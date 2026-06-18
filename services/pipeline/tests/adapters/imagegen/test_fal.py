"""RED — C1: the real fal (FLUX) ImageGenProvider backend behind the frozen §7 seam.

A second bakeoff backend (EVAL-002) exercising the established foundation (LESSONS 9/10/11) across a
DIFFERENT wire shape: fal's queue API completes in two GETs (status → COMPLETED, then the result
response). Behavioral + client-agnostic; cassette content authored at GREEN to the verified shape.
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aisims_contracts.error import ErrorCode, ErrorEnvelope
from aisims_contracts.providers import ImageGenProvider, PollStatus, ProviderJobRef

from obs.secrets import InMemorySecretsAccessor, SecretsAccessor

from .conftest import CASSETTE_DIR, SpyAccessor

Cassette = Callable[[str], AbstractContextManager[None]]

_EXPECTED_CASSETTES = {
    "fal_submit",
    "fal_poll",
    "fal_poll_failed",
    "fal_submit_401",
    "fal_fetch",
    "fal_fetch_wrongmagic",
    "fal_poll_result_error",
}


def _public_resolver(_host: str) -> list[str]:
    """Map any host → a public test IP so the §16 SSRF floor passes without real DNS."""
    return ["93.184.216.34"]


def _provider(scratch: Path, secrets: SecretsAccessor | None = None) -> ImageGenProvider:
    from adapters.imagegen.fal import FalImageGenProvider

    return FalImageGenProvider(
        secrets=secrets or InMemorySecretsAccessor({"FAL_KEY": "fal-test-PLACEHOLDER"}),
        scratch_dir=scratch,
        resolver=_public_resolver,
    )


def _ref(request_id: str) -> ProviderJobRef:
    return ProviderJobRef(
        provider="fal",
        model="fal-ai/flux-pro/v1.1",
        jobId=request_id,
        submittedAt=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_fal_conforms_to_imagegenprovider_protocol(tmp_path: Path) -> None:
    """spec(§7) — the fal backend structurally satisfies the frozen ImageGenProvider Protocol."""
    from adapters.imagegen.fal import FalImageGenProvider

    provider: ImageGenProvider = FalImageGenProvider(
        secrets=InMemorySecretsAccessor({"FAL_KEY": "x"}), scratch_dir=tmp_path
    )
    assert callable(provider.submit)
    assert callable(provider.poll)
    assert callable(provider.fetch)


def test_fal_submit_returns_jobref(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§7) — submit() puts the prompt in the request body (asserted on the pure builder) and
    returns a well-formed ProviderJobRef (jobId = fal request_id)."""
    from adapters.imagegen.fal import build_submit_body

    body = build_submit_body("a red armchair", {"seed": 7})
    assert body["prompt"] == "a red armchair"
    assert body["seed"] == 7

    provider = _provider(tmp_path)
    with imagegen_cassette("fal_submit"):
        ref = provider.submit("a red armchair", {"seed": 7})
    assert isinstance(ref, ProviderJobRef)
    assert ref.jobId and ref.provider == "fal" and ref.model


def test_fal_poll_pending_then_succeeded(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§7) — poll walks IN_PROGRESS (progress) → COMPLETED (the two-GET completion: status then
    result) with urls + usage.latencyMs + costCents (the fal FLUX model is priced)."""
    provider = _provider(tmp_path)
    with imagegen_cassette("fal_poll"):
        first = provider.poll(_ref("req-1"))
        second = provider.poll(_ref("req-1"))

    assert first.status in (PollStatus.SUBMITTED, PollStatus.RUNNING)
    assert first.progress is not None
    assert second.status is PollStatus.SUCCEEDED
    assert second.urls
    assert second.usage is not None
    assert second.usage.latencyMs >= 0
    assert second.usage.costCents is not None and second.usage.costCents >= 0


def test_fal_poll_job_failure_rides_pollresult_error(
    imagegen_cassette: Cassette, tmp_path: Path
) -> None:
    """spec(§17) — a fal job failure (error/error_type) rides PollResult(FAILED, error); poll does
    NOT raise (async channel — lesson 10)."""
    provider = _provider(tmp_path)
    with imagegen_cassette("fal_poll_failed"):
        result = provider.poll(_ref("req-fail"))  # must not raise

    assert result.status is PollStatus.FAILED
    assert isinstance(result.error, ErrorEnvelope)


def test_fal_poll_result_fetch_failure_rides_error(
    imagegen_cassette: Cassette, tmp_path: Path
) -> None:
    """spec(§17) — fal's TWO-GET completion: if the result GET fails AFTER status=COMPLETED, that
    rides PollResult.error too (poll never raises) and is RETRYABLE (the job is done → Phase-2 can
    re-fetch the result)."""
    provider = _provider(tmp_path)
    with imagegen_cassette("fal_poll_result_error"):
        result = provider.poll(_ref("req-resulterr"))  # must not raise

    assert result.status is PollStatus.FAILED
    assert isinstance(result.error, ErrorEnvelope)
    assert result.error.retryable is True


def test_fal_submit_http_failure_raises(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§17) — submit has no result error field → RAISES ProviderError on a 401
    (PROVIDER_AUTH_QUOTA)."""
    from adapters.errors import ProviderError

    provider = _provider(tmp_path)
    with imagegen_cassette("fal_submit_401"), pytest.raises(ProviderError) as exc:
        provider.submit("x", {"seed": 1})
    assert exc.value.envelope.code is ErrorCode.PROVIDER_AUTH_QUOTA


def test_fal_fetch_scratch_guarded_and_validated(
    imagegen_cassette: Cassette, tmp_path: Path
) -> None:
    """spec(§16) — fetch REUSES the hardened path (scratch-guarded + content-validated): a valid
    image writes under scratch; a wrong-magic body raises ProviderError(MALFORMED_OUTPUT)."""
    from adapters.errors import ProviderError

    provider = _provider(tmp_path)
    with imagegen_cassette("fal_fetch"):
        paths = provider.fetch(["https://v3.fal.media/files/out/concept.png"])
    assert len(paths) == 1
    assert tmp_path.resolve() in Path(paths[0]).resolve().parents

    with imagegen_cassette("fal_fetch_wrongmagic"), pytest.raises(ProviderError) as exc:
        provider.fetch(["https://v3.fal.media/files/out/notimage.png"])
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT


def test_fal_key_via_accessor_not_persisted(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """safety rule 5 — key pulled via SecretsAccessor.get at call time; never stashed/in repr."""
    secret_value = "fal-SUPER-SECRET-key-9z"
    spy = SpyAccessor({"FAL_KEY": secret_value})
    provider = _provider(tmp_path, secrets=spy)

    assert spy.get_calls == []
    with imagegen_cassette("fal_submit"):
        provider.submit("a red armchair", {"seed": 7})

    assert "FAL_KEY" in spy.get_calls
    assert secret_value not in repr(provider)
    assert secret_value not in str(provider)
    str_attrs = [v for v in vars(provider).values() if isinstance(v, str)]
    assert not any(secret_value in attr for attr in str_attrs)


def test_fal_cassettes_have_no_authorization_header() -> None:
    """safety rule 5 — every fal cassette is scrubbed (no auth header / key bytes)."""
    cassettes = sorted(CASSETTE_DIR.glob("fal_*.yaml"))
    present = {c.stem for c in cassettes}
    assert _EXPECTED_CASSETTES <= present, f"missing cassettes: {_EXPECTED_CASSETTES - present}"
    for cassette in cassettes:
        text = cassette.read_text().lower()
        assert "authorization" not in text, f"{cassette.name} leaks an Authorization header"
        assert "x-api-key" not in text, f"{cassette.name} leaks an x-api-key header"
        assert "key fal-" not in text, f"{cassette.name} leaks a fal key"


def test_fal_in_factory_seam() -> None:
    """fp-2 — IMAGEGEN_PROVIDERS['fal'] resolves the class; nothing self-registers on import."""
    from adapters.imagegen import IMAGEGEN_PROVIDERS
    from adapters.imagegen.fal import FalImageGenProvider

    assert IMAGEGEN_PROVIDERS["fal"] is FalImageGenProvider
    assert all(isinstance(ctor, type) for ctor in IMAGEGEN_PROVIDERS.values())


@pytest.mark.skipif(
    os.environ.get("AISIMS_IMAGEGEN_LIVE") != "1", reason="set AISIMS_IMAGEGEN_LIVE=1 (+ FAL_KEY)"
)
def test_fal_live_smoke(tmp_path: Path) -> None:
    """One real submit→poll→fetch against fal — proves the real queue path end to end."""
    from adapters.imagegen import IMAGEGEN_PROVIDERS

    key = os.environ.get("FAL_KEY")
    if not key:
        pytest.skip("FAL_KEY not set")

    provider = IMAGEGEN_PROVIDERS["fal"](
        secrets=InMemorySecretsAccessor({"FAL_KEY": key}), scratch_dir=tmp_path
    )
    ref = provider.submit("a single red ceramic mug, plain background", {"seed": 7})
    result = provider.poll(ref)
    for _ in range(30):
        if result.status in (PollStatus.SUCCEEDED, PollStatus.FAILED, PollStatus.EXPIRED):
            break
        time.sleep(2)
        result = provider.poll(ref)

    assert result.status is PollStatus.SUCCEEDED
    assert result.urls
    paths = provider.fetch(result.urls)
    assert paths and Path(paths[0]).is_file()
