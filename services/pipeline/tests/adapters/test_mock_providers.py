"""RED — §7 mock providers: Protocol conformance, async lifecycle, expiry, sync LLM.

The mocks structurally conform to the frozen §7 Protocols (Image3DProvider / ImageGenProvider /
LLMProvider) — they import the Protocols, never redefine them (forbidden-pattern 2, no lock-in).
"""

from __future__ import annotations

from pathlib import Path

from aisims_contracts.error import ErrorCode
from aisims_contracts.providers import (
    Image3DProvider,
    ImageGenProvider,
    LLMProvider,
    PollResult,
    PollStatus,
)
from pydantic import BaseModel


class _DemoPlan(BaseModel):
    title: str
    count: int
    note: str = "default-note"


def test_mock_providers_conform_to_protocols(tmp_path: Path) -> None:
    """spec(§7) — each mock structurally satisfies its provider Protocol (mypy-checked binding)."""
    from adapters.mock.providers import (
        MockImage3DProvider,
        MockImageGenProvider,
        MockLLMProvider,
    )

    img3d: Image3DProvider = MockImage3DProvider(seed=1, scratch_dir=tmp_path)
    imggen: ImageGenProvider = MockImageGenProvider(seed=1, scratch_dir=tmp_path)
    llm: LLMProvider = MockLLMProvider(seed=1)

    # the typed bindings above ARE the static conformance assertion under mypy --strict; below we
    # also INVOKE each seam method THROUGH the Protocol-typed binding (runtime behavioral
    # conformance — stronger than a mere callable() attribute check).
    assert isinstance(img3d.poll(img3d.submit(b"x", {})), PollResult)
    assert isinstance(imggen.poll(imggen.submit("a prompt", {})), PollResult)
    assert isinstance(llm.complete("hi", {}), str)
    assert isinstance(llm.structured("plan", _DemoPlan, {}), _DemoPlan)


def test_mock_provider_async_lifecycle(tmp_path: Path) -> None:
    """spec(§7) — submit→ref; polls walk SUBMITTED→RUNNING→SUCCEEDED, progress∈[0,1] rising,
    usage.latencyMs always set, expiresAt present (the reconcile-spine)."""
    from adapters.mock.providers import MockImage3DProvider

    mock = MockImage3DProvider(seed=7, scratch_dir=tmp_path, succeed_after_polls=3)
    ref = mock.submit(b"concept-image-bytes", {"model": "hunyuan3d"})
    assert ref.expiresAt is not None and ref.expiresAt > ref.submittedAt

    r1 = mock.poll(ref)
    r2 = mock.poll(ref)
    r3 = mock.poll(ref)
    assert [r1.status, r2.status, r3.status] == [
        PollStatus.SUBMITTED,
        PollStatus.RUNNING,
        PollStatus.SUCCEEDED,
    ]
    assert r1.progress is not None and r2.progress is not None and r3.progress is not None
    assert 0.0 <= r1.progress <= r2.progress <= r3.progress == 1.0  # progress rises to 1.0
    for r in (r1, r2, r3):
        assert r.usage is not None and r.usage.latencyMs >= 0
    assert r3.urls and r3.error is None

    paths = mock.fetch(r3.urls)
    assert paths and all(Path(p).exists() for p in paths)


def test_mock_provider_expired_race(tmp_path: Path) -> None:
    """spec(§7) — an expiring mock polls EXPIRED with an ARTIFACT_EXPIRED envelope (Tripo 24h)."""
    from adapters.mock.failure import FailurePlan, FailureRule, MockOp
    from adapters.mock.providers import MockImage3DProvider

    plan = FailurePlan(
        rules=[FailureRule(operation=MockOp.POLL, at_call=1, code=ErrorCode.ARTIFACT_EXPIRED)]
    )
    mock = MockImage3DProvider(seed=1, scratch_dir=tmp_path, failure_plan=plan)
    res = mock.poll(mock.submit(b"x", {}))
    assert res.status is PollStatus.EXPIRED
    assert res.error is not None and res.error.code is ErrorCode.ARTIFACT_EXPIRED


def test_mock_llm_complete_and_structured(tmp_path: Path) -> None:
    """spec(§7) — complete→deterministic str; structured→a valid instance of the caller's schema."""
    from adapters.mock.providers import MockLLMProvider

    llm = MockLLMProvider(seed=2)
    text = llm.complete("describe a Y2K lamp", {})
    assert isinstance(text, str) and text

    out = llm.structured("plan the item", _DemoPlan, {})
    assert isinstance(out, _DemoPlan)
    assert isinstance(out.title, str) and isinstance(out.count, int)
