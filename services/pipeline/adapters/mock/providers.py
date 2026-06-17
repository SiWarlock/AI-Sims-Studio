"""§7 mock provider adapters — Image3D / ImageGen / LLM (PIPE-002, no lock-in).

Each mock structurally conforms to the frozen §7 Protocol (imported, never redefined). All
"randomness" (latencyMs, fetched bytes) is a pure function of ``(seed, call-sequence)`` via a
per-mock ``random.Random(seed)``; timestamps are a fixed epoch + deterministic offset — NO
wall-clock — so a seeded run reproduces byte-for-byte (REQ-T-101). Failures are injected via a
``FailurePlan``: async providers surface them on ``PollResult`` (FAILED / EXPIRED); the sync
``LLMProvider`` calls RAISE ``ProviderError`` (no contract error field). Artifacts are written ONLY
under the sidecar-provided scratch dir (rule 3 / fp-4).
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from types import UnionType
from typing import Any, Union, get_args, get_origin

from aisims_contracts.error import ErrorCode
from aisims_contracts.providers import PollResult, PollStatus, ProviderJobRef, ProviderUsage
from pydantic import BaseModel

from .failure import FailurePlan, MockOp, ProviderError, envelope_for

# Fixed base instant for deterministic submittedAt (never wall-clock); Tripo 24h URL expiry.
_EPOCH = datetime(2026, 1, 1, tzinfo=UTC)
_EXPIRY = timedelta(hours=24)
_MIN_LATENCY_MS = 50
_MAX_LATENCY_MS = 5000


class _BaseAsyncProvider:
    """Shared async submit/poll/fetch lifecycle for the image providers (§7 reconcile spine)."""

    kind: str = "mock-async"

    def __init__(
        self,
        *,
        seed: int = 0,
        scratch_dir: Path,
        succeed_after_polls: int = 3,
        failure_plan: FailurePlan | None = None,
    ) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        self._scratch_dir = scratch_dir
        self._succeed_after_polls = succeed_after_polls
        self._plan = failure_plan or FailurePlan()
        self._submit_count = 0
        self._poll_counts: dict[str, int] = {}

    def _new_ref(self, model: str) -> ProviderJobRef:
        self._submit_count += 1
        submitted = _EPOCH + timedelta(seconds=self._submit_count)
        job_id = f"{self.kind}-{self._seed}-{self._submit_count}"
        self._poll_counts[job_id] = 0
        return ProviderJobRef(
            provider=self.kind,
            model=model,
            jobId=job_id,
            submittedAt=submitted,
            expiresAt=submitted + _EXPIRY,
        )

    def poll(self, ref: ProviderJobRef) -> PollResult:
        count = self._poll_counts.get(ref.jobId, 0) + 1
        self._poll_counts[ref.jobId] = count
        usage = ProviderUsage(latencyMs=self._rng.randint(_MIN_LATENCY_MS, _MAX_LATENCY_MS))

        injected = self._plan.match(MockOp.POLL, count)
        if injected is not None:
            status = (
                PollStatus.EXPIRED if injected is ErrorCode.ARTIFACT_EXPIRED else PollStatus.FAILED
            )
            return PollResult(status=status, usage=usage, error=envelope_for(injected))

        n = self._succeed_after_polls
        if count >= n:
            urls = [f"https://mock.local/{ref.jobId}/out.bin"]
            return PollResult(status=PollStatus.SUCCEEDED, progress=1.0, urls=urls, usage=usage)

        # poll #1 → SUBMITTED, intermediate polls → RUNNING, poll #n → SUCCEEDED. With
        # succeed_after_polls <= 2 there is no intermediate poll, so RUNNING is simply not emitted.
        status = PollStatus.SUBMITTED if count == 1 else PollStatus.RUNNING
        progress = (count - 1) / max(n - 1, 1)
        return PollResult(status=status, progress=progress, usage=usage)

    def fetch(self, urls: list[str]) -> list[str]:
        self._scratch_dir.mkdir(parents=True, exist_ok=True)
        scratch_root = self._scratch_dir.resolve()
        paths: list[str] = []
        for index, url in enumerate(urls):
            # derive a SAFE basename: strip any path components so a provider-supplied url can't
            # write outside the scratch dir (rule 3 / fp-4 — matters when Phase-3 real adapters
            # reuse this fetch shape against externally-returned urls).
            name = Path(url.rsplit("/", 1)[-1]).name
            if name in ("", ".", ".."):
                name = f"artifact-{index}.bin"
            dest = self._scratch_dir / name
            if not dest.resolve().is_relative_to(scratch_root):  # defense in depth
                raise ValueError(f"fetch target escapes the scratch dir: {dest}")
            dest.write_bytes(f"mock-artifact:{url}".encode())
            paths.append(str(dest))
        return paths


class MockImage3DProvider(_BaseAsyncProvider):
    kind = "mock-image3d"

    def submit(self, image: bytes, params: dict[str, Any]) -> ProviderJobRef:
        return self._new_ref(str(params.get("model", "mock-3d")))


class MockImageGenProvider(_BaseAsyncProvider):
    kind = "mock-imagegen"

    def submit(self, prompt: str, params: dict[str, Any]) -> ProviderJobRef:
        return self._new_ref(str(params.get("model", "mock-imagegen")))


class MockLLMProvider:
    """Synchronous mock LLM (§7): deterministic ``complete``; ``structured`` builds a minimal valid
    instance of the caller's schema. Injected failure RAISES ``ProviderError`` (no error field)."""

    def __init__(self, *, seed: int = 0, failure_plan: FailurePlan | None = None) -> None:
        self._seed = seed
        self._rng = random.Random(seed)
        self._plan = failure_plan or FailurePlan()
        self._complete_count = 0
        self._structured_count = 0

    def complete(self, prompt: str, params: dict[str, Any]) -> str:
        self._complete_count += 1
        injected = self._plan.match(MockOp.COMPLETE, self._complete_count)
        if injected is not None:
            raise ProviderError(envelope_for(injected))
        return f"mock-completion[{self._seed}:{self._complete_count}] {prompt[:32]}"

    def structured[T: BaseModel](self, prompt: str, schema: type[T], params: dict[str, Any]) -> T:
        self._structured_count += 1
        injected = self._plan.match(MockOp.STRUCTURED, self._structured_count)
        if injected is not None:
            raise ProviderError(envelope_for(injected))
        return _build_minimal(schema, self._rng)


def _build_minimal[M: BaseModel](schema: type[M], rng: random.Random) -> M:
    """Deterministically synthesize a minimal VALID instance of ``schema``: defaulted fields keep
    their default; required fields are filled by type. Assumes acyclic schemas (the frozen §-seam
    contracts are) — a self-referential required field would recurse unbounded."""
    values: dict[str, Any] = {}
    for name, field in schema.model_fields.items():
        if field.is_required():
            values[name] = _value_for(field.annotation, rng)
    return schema(**values)


def _value_for(annotation: Any, rng: random.Random) -> Any:
    """A deterministic placeholder value for a pydantic field annotation (bounded type support).

    Supported: str/int/float/bool, list/dict (empty), Optional/Union (first non-None member),
    nested BaseModel (recursed), Enum (first member). Anything else (Literal, tuple, TypedDict,
    constrained/exotic annotations) raises NotImplementedError — a clear "extend me here" signal,
    never a silently-wrong value. Extend as Phase-2 plan schemas require it.
    """
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:  # Optional[X] / X | None → first non-None member
        non_none = [arg for arg in get_args(annotation) if arg is not type(None)]
        return _value_for(non_none[0], rng) if non_none else None
    if origin is list:
        return []
    if origin is dict:
        return {}
    if annotation is str:
        return "mock"
    if annotation is bool:
        return True
    if annotation is int:
        return rng.randint(0, 1000)
    if annotation is float:
        return float(rng.randint(0, 1000))
    if isinstance(annotation, type):
        if issubclass(annotation, BaseModel):
            return _build_minimal(annotation, rng)
        if issubclass(annotation, Enum):
            return next(iter(annotation))
    raise NotImplementedError(f"mock structured cannot synthesize a value for {annotation!r}")
