"""The two-phase cloud-node pattern (task 2.2, §5).

A cloud stage runs in two checkpointed phases:

1. **submit node** — a ``@task``-wrapped idempotent submit whose ``ProviderJobRef`` result
   is checkpointed, then written into ``PipelineState.providerJobRefs`` BEFORE any poll
   side-effect (so the reconcile-spine handle survives a checkpoint). On replay a completed
   submit is replayed from the @task cache, never re-run — no double-submit (R9).
2. **poll/reconcile node** — reads the persisted ref, polls the provider to a terminal
   ``PollStatus`` (bounded by a ``max_polls`` watchdog), then on ``succeeded`` fetches outputs
   into ``artifactRefs``, or on ``failed``/``expired`` surfaces the §17 ``ErrorEnvelope``
   UNCHANGED into ``pollErrors`` (never re-rolled). The reconcile DECISION (re-submit /
   regenerate) is 2.4.

The provider is INJECTED (rule 2 — no hard-coded provider; registry-based selection is 2.3).
``durability="sync"`` is applied by the run-time caller (Lesson 11), not at compile.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any, Protocol

from aisims_contracts import (
    ErrorCategory,
    ErrorCode,
    ErrorEnvelope,
    GateKind,
    PollResult,
    PollStatus,
    ProviderJobRef,
)
from langgraph.func import task

from graph.state import PipelineState

NodeUpdate = dict[str, Any]
SubmitFn = Callable[[PipelineState], ProviderJobRef]

_PENDING = (PollStatus.SUBMITTED, PollStatus.RUNNING)
# Pre-2.5 stopgap for the §17 cloud-poll watchdog (the full wall-clock + structured-envelope
# watchdog is 2.5): bound the poll loop so a never-terminal provider cannot hang the run.
_DEFAULT_MAX_POLLS = 100


class PollWatchdogError(RuntimeError):
    """Raised when a poll loop exhausts its ``max_polls`` budget without a terminal status.

    The pre-2.5 stopgap for the §17 cloud-poll watchdog (full wall-clock + structured-envelope
    handling lands with the 2.5 error taxonomy).
    """


class PollFetchProvider(Protocol):
    """The poll/fetch half of a provider — uniform across Image3D/ImageGen (§7).

    The *job* is async (submitted→running→succeeded); the *calls* are synchronous per the
    frozen §7 contract. (A future async adapter would make these ``async def`` + ``await``.)
    """

    def poll(self, ref: ProviderJobRef) -> PollResult: ...

    def fetch(self, urls: list[str]) -> list[str]: ...


@dataclass(frozen=True)
class CloudStageSpec:
    """The injected provider seam for one cloud stage (rule 2 — no hard-coded provider).

    submit: the stage-specific submit (closes over the provider + payload derivation — Image3D
        takes ``bytes``, ImageGen takes a ``str`` prompt; this callable hides that difference).
    provider: the uniform poll/fetch source.
    max_polls: the watchdog budget for the poll loop.
    """

    submit: SubmitFn
    provider: PollFetchProvider
    max_polls: int = _DEFAULT_MAX_POLLS


ProviderBundle = Mapping[GateKind, CloudStageSpec]


def cloud_step_key(state: PipelineState, gate: GateKind) -> str:
    """The providerJobRefs / artifactRefs / pollErrors key for ``gate`` in this run.

    2.2 is collection-level (one job per cloud stage per run) → the stage name. Per-item keying
    (``itemId:stage``) arrives with bounded-parallel item iteration (2.3).
    """
    return gate.value


def _system_envelope(status: PollStatus) -> ErrorEnvelope:
    """The §17 floor for a terminal-failure poll that omits an envelope (a provider breach).

    NOT a re-roll of an existing envelope (there is none) — it records an otherwise-lost
    terminal failure so it can never be silently dropped.
    """
    return ErrorEnvelope(
        code=ErrorCode.SYSTEM,
        category=ErrorCategory.SYSTEM,
        retryable=False,
        creatorMessage="Something went wrong on our side.",
        maintainerDetail=f"Provider reported terminal {status.value} without an envelope (§17).",
    )


def make_submit_node(gate: GateKind, spec: CloudStageSpec) -> Callable[[PipelineState], NodeUpdate]:
    """Phase 1: the ``@task`` idempotent submit; persists the ``ProviderJobRef`` into State."""

    # The result is checkpointed → a completed submit is replayed, never re-run (R9). Two cloud
    # stages share the inner name "_submit" but never share a cache key — langgraph differentiates
    # @task calls by graph position, so concept's and mesh's submits stay distinct (verified).
    @task
    def _submit(state: PipelineState) -> ProviderJobRef:
        return spec.submit(state)

    def submit_node(state: PipelineState) -> NodeUpdate:
        key = cloud_step_key(state, gate)
        if key in state.providerJobRefs:
            return {}  # idempotent guard — already submitted (a second R9 layer)
        ref = _submit(state).result()
        return {"providerJobRefs": {**state.providerJobRefs, key: ref}}

    return submit_node


def make_poll_node(gate: GateKind, spec: CloudStageSpec) -> Callable[[PipelineState], NodeUpdate]:
    """Phase 2: poll the persisted ref to terminal; fetch on success / surface error on failure."""

    def poll_node(state: PipelineState) -> NodeUpdate:
        key = cloud_step_key(state, gate)
        ref = state.providerJobRefs[key]
        # Poll at most max_polls times (the §17 watchdog stopgap — exact bound, 0 ⇒ no polls).
        result: PollResult | None = None
        for _ in range(spec.max_polls):
            result = spec.provider.poll(ref)
            if result.status not in _PENDING:
                break
        if result is None or result.status in _PENDING:
            raise PollWatchdogError(
                f"cloud poll for {key!r} exhausted its budget "
                f"({spec.max_polls} polls) without reaching a terminal status"
            )
        if result.status is PollStatus.SUCCEEDED:
            paths = spec.provider.fetch(result.urls or [])
            return {"artifactRefs": {**state.artifactRefs, key: paths}}
        # FAILED / EXPIRED → surface the provider's §17 envelope UNCHANGED (never re-rolled);
        # fall back to a SYSTEM envelope only if a provider breaches §17 by omitting one.
        envelope = result.error if result.error is not None else _system_envelope(result.status)
        return {"pollErrors": {**state.pollErrors, key: envelope}}

    return poll_node
