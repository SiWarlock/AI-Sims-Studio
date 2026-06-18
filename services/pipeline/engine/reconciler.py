"""The startup reconciler (task 2.4, §6/§5, REQ-NF-102).

On sidecar reopen, for each persisted in-flight ``ProviderJobRef`` poll the provider and route
via the §6 decision-table (R-e):

- ``submitted``/``running`` → **RE_POLL** (job still alive)
- ``succeeded`` ∧ artifact present → **RESUME** (continue from here)
- ``succeeded`` ∧ artifact missing → **RE_FETCH** (re-download; escalate to REGENERATE if the
  re-fetch fails — expired urls)
- ``failed``/``expired``/GC'd → **REGENERATE** (step failed + OFFER regenerate — human-gated)

Per-ref failure isolation: one ref's poll raising is captured (catch ``Exception``, NOT
``BaseException`` — Lesson 15) and routed to REGENERATE (unknown state → offer regenerate), never
aborting the others. Plus stale-lock recovery: reclaim a DEAD-owner-PID single-writer lock on
reopen (wires the 0.9 ``SingleWriterLock`` dead-PID-only rule — no new fencing).

Scope: 2.4 proves the decision-table + the reclaim deterministically over an injected provider +
an injected ``artifact_exists`` predicate. The live boot wiring (supervisor → reconcile → resume
via the scheduler, the transactional "step FAILED" write, the regenerate re-enqueue) is the
run-start integration. ``reconcile`` is SYNC (the §7 Protocol is sync); the async boot wraps it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from aisims_contracts import PollResult, PollStatus, ProviderJobRef

from engine.lock import SingleWriterLock


class ReconcileAction(StrEnum):
    """The §6 startup-reconcile decision-table outcomes (R-e)."""

    RE_POLL = "re_poll"  # job still alive (submitted/running) → keep polling
    RESUME = "resume"  # succeeded + artifact present → continue from here (no-op)
    RE_FETCH = "re_fetch"  # succeeded + artifact missing → re-download the outputs
    REGENERATE = "regenerate"  # failed/expired/GC'd or re-fetch-failed → offer regenerate


class PollFetchProvider(Protocol):
    """The poll/fetch half of an async provider (§7) — a narrowed structural interface for
    injection (interface-segregation, not a wire-contract dup). Calls are synchronous per §7."""

    def poll(self, ref: ProviderJobRef) -> PollResult: ...

    def fetch(self, urls: list[str]) -> list[str]: ...


# A presence predicate keyed by the ref (the caller closes over State.artifactRefs → path).
ArtifactExists = Callable[[ProviderJobRef], bool]


@dataclass(frozen=True)
class ReconcileOutcome:
    """A ref's resolution: the routed action, the re-fetched paths (on a successful RE_FETCH),
    and any captured exception (isolation). ``ok`` means no exception occurred during reconcile."""

    jobId: str
    action: ReconcileAction
    fetched_paths: list[str] | None = None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


def decide(poll_status: PollStatus, *, artifact_present: bool) -> ReconcileAction:
    """The pure §6 startup-reconcile decision-table (R-e)."""
    if poll_status in (PollStatus.SUBMITTED, PollStatus.RUNNING):
        return ReconcileAction.RE_POLL
    if poll_status is PollStatus.SUCCEEDED:
        return ReconcileAction.RESUME if artifact_present else ReconcileAction.RE_FETCH
    # FAILED / EXPIRED — and GC'd, which surfaces as EXPIRED or an injected poll failure.
    return ReconcileAction.REGENERATE


class Reconciler:
    """Resolves each persisted ProviderJobRef on reopen via the §6 decision-table."""

    def reconcile(
        self,
        refs: Sequence[ProviderJobRef],
        provider: PollFetchProvider,
        artifact_exists: ArtifactExists,
    ) -> dict[str, ReconcileOutcome]:
        """Poll + route each ref; return the per-ref resolution by jobId (per-ref isolation)."""
        return {ref.jobId: self._reconcile_one(ref, provider, artifact_exists) for ref in refs}

    def _reconcile_one(
        self,
        ref: ProviderJobRef,
        provider: PollFetchProvider,
        artifact_exists: ArtifactExists,
    ) -> ReconcileOutcome:
        try:
            result = provider.poll(ref)
        except Exception as exc:
            # Per-ref isolation (Lesson 15 — catch Exception, NOT BaseException). An unrecoverable
            # poll → REGENERATE (offer regenerate); 2.5's §17 taxonomy may reclassify transient.
            return ReconcileOutcome(jobId=ref.jobId, action=ReconcileAction.REGENERATE, error=exc)
        # Presence only matters for SUCCEEDED — avoid a spurious FS check on a still-pollable ref.
        present = result.status is PollStatus.SUCCEEDED and artifact_exists(ref)
        action = decide(result.status, artifact_present=present)
        if action is ReconcileAction.RE_FETCH:
            urls = result.urls or []
            if not urls:
                # Succeeded but nothing to re-fetch from → cannot recover → offer regenerate.
                return ReconcileOutcome(jobId=ref.jobId, action=ReconcileAction.REGENERATE)
            try:
                paths = provider.fetch(urls)
            except Exception as exc:
                # "re-fetch then regenerate": the re-download failed (expired urls) → escalate,
                # capturing the error so the outcome is not-ok (distinguishable from a clean route).
                return ReconcileOutcome(
                    jobId=ref.jobId, action=ReconcileAction.REGENERATE, error=exc
                )
            # The artifact is re-fetched — carry the paths so the boot wiring can resume from them.
            return ReconcileOutcome(
                jobId=ref.jobId, action=ReconcileAction.RE_FETCH, fetched_paths=paths
            )
        return ReconcileOutcome(jobId=ref.jobId, action=action)


def reclaim_stale_lock(lock: SingleWriterLock) -> bool:
    """On reopen, reclaim the single-writer lock if its owner PID is DEAD (0.9 dead-PID-only rule).

    Returns True if acquired (the lock was free or reclaimed from a dead owner); False while a LIVE
    owner holds it. This NAMES the reopen call site; the dead-vs-live decision is the 0.9
    SingleWriterLock's. No atomic-acquire / fencing token — that's the Phase-2+ upgrade (Lesson 8).
    """
    return lock.acquire()
