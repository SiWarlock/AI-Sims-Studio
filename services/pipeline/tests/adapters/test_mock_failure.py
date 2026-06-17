"""RED — §17 deterministic failure injection (REQ-T-101).

The injector emits a valid ErrorEnvelope for EVERY ErrorCode (all 13) with a sensible
category/retryable; the sync LLM calls surface failure by RAISING (no contract error channel);
the same seed + same call sequence reproduces byte-identically; and injected envelopes are
egress-realistic (both free-text fields populated; one carries a secret-looking token) so the
0.9 redaction chokepoint has a real surface to scrub.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from aisims_contracts.providers import PollResult, PollStatus, ProviderJobRef
from pydantic import BaseModel


class _DemoPlan(BaseModel):
    title: str
    count: int


@pytest.mark.parametrize("code", list(ErrorCode))
def test_failure_injection_covers_all_error_codes(code: ErrorCode) -> None:
    """spec(§17) — the injector emits a valid ErrorEnvelope for each of the 13 codes."""
    from adapters.mock.failure import envelope_for

    env = envelope_for(code)
    assert isinstance(env, ErrorEnvelope)
    assert env.code is code
    assert isinstance(env.category, ErrorCategory)
    assert isinstance(env.retryable, bool)
    assert env.creatorMessage and env.maintainerDetail


def test_error_classification_transient_vs_terminal() -> None:
    """spec(§17) — AUTH_QUOTA is terminal (not retryable); transient codes are retryable."""
    from adapters.mock.failure import envelope_for

    assert envelope_for(ErrorCode.PROVIDER_AUTH_QUOTA).retryable is False
    for transient in (
        ErrorCode.PROVIDER_TIMEOUT,
        ErrorCode.PROVIDER_RATE_LIMIT,
        ErrorCode.PROVIDER_OUTAGE,
    ):
        assert envelope_for(transient).retryable is True


def test_injected_envelope_is_egress_realistic() -> None:
    """spec(§17) — every envelope fills both free-text fields; AUTH_QUOTA carries a secret-looking
    token in maintainerDetail (the 0.9 redaction-pin / eval egress surface, D)."""
    from adapters.mock.failure import envelope_for

    for code in ErrorCode:
        env = envelope_for(code)
        assert env.creatorMessage.strip()
        assert env.maintainerDetail.strip()

    auth_detail = envelope_for(ErrorCode.PROVIDER_AUTH_QUOTA).maintainerDetail
    assert re.search(r"(sk-|AKIA|Bearer\s)\S+", auth_detail), "no secret-looking token to redact"


def test_llm_sync_failure_raises_envelope() -> None:
    """spec(§17) — sync LLM calls have no error field, so injected failure RAISES (Q5 channel)."""
    from adapters.mock.failure import FailurePlan, FailureRule, MockOp, ProviderError
    from adapters.mock.providers import MockLLMProvider

    complete_plan = FailurePlan(
        rules=[FailureRule(operation=MockOp.COMPLETE, at_call=1, code=ErrorCode.PROVIDER_TIMEOUT)]
    )
    with pytest.raises(ProviderError) as ei:
        MockLLMProvider(seed=1, failure_plan=complete_plan).complete("x", {})
    assert ei.value.envelope.code is ErrorCode.PROVIDER_TIMEOUT

    structured_plan = FailurePlan(
        rules=[FailureRule(operation=MockOp.STRUCTURED, at_call=1, code=ErrorCode.MALFORMED_OUTPUT)]
    )
    with pytest.raises(ProviderError) as ei2:
        MockLLMProvider(seed=1, failure_plan=structured_plan).structured("x", _DemoPlan, {})
    assert ei2.value.envelope.code is ErrorCode.MALFORMED_OUTPUT


def test_mock_determinism_same_seed(tmp_path: Path) -> None:
    """spec(REQ-T-101) — same seed + same call sequence ⟹ byte-identical outputs, incl. the
    injected failure (refs, latencies, envelope all reproduce)."""
    from adapters.mock.failure import FailurePlan, FailureRule, MockOp
    from adapters.mock.providers import MockImage3DProvider, MockLLMProvider

    plan = FailurePlan(
        rules=[FailureRule(operation=MockOp.POLL, at_call=2, code=ErrorCode.PROVIDER_OUTAGE)]
    )

    def run_once(name: str) -> tuple[ProviderJobRef, PollResult, PollResult]:
        mock = MockImage3DProvider(
            seed=42, scratch_dir=tmp_path / name, succeed_after_polls=4, failure_plan=plan
        )
        ref = mock.submit(b"img", {})
        first = mock.poll(ref)
        second = mock.poll(ref)  # injected OUTAGE at poll #2
        return ref, first, second

    a_ref, a1, a2 = run_once("a")
    b_ref, b1, b2 = run_once("b")
    assert a_ref == b_ref  # ProviderJobRef (jobId/submittedAt/expiresAt) reproduces
    assert a1 == b1  # poll #1 reproduces (status/progress/usage)
    assert a2 == b2  # injected-failure poll reproduces (status/envelope/latency)
    assert a2.status is PollStatus.FAILED
    assert a2.error is not None and a2.error.code is ErrorCode.PROVIDER_OUTAGE

    # the sync structured() path reproduces too (REQ-T-101 covers every "random" output)
    s1 = MockLLMProvider(seed=7).structured("x", _DemoPlan, {})
    s2 = MockLLMProvider(seed=7).structured("x", _DemoPlan, {})
    assert s1 == s2
