"""RED — C1: the real WaveSpeed FLUX.2 [pro] ImageGenProvider behind the frozen §7 seam.

Behavioral, client-agnostic: each test pins a contract (conformance / submit shape / async poll
lifecycle / the three-way error channel / scratch-guarded fetch / secrets-at-call-time / scrubbed
cassettes / factory seam). Cassette content is authored at GREEN to match the verified wire shape.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager
from datetime import UTC, datetime
from pathlib import Path

import pytest
from aisims_contracts.error import ErrorCode, ErrorEnvelope
from aisims_contracts.providers import ImageGenProvider, PollStatus, ProviderJobRef

from adapters.validation import DEFAULT_MAX_CANDIDATES, DEFAULT_MAX_IMAGE_BYTES
from obs.secrets import InMemorySecretsAccessor, SecretsAccessor

from .conftest import CASSETTE_DIR, SpyAccessor

Cassette = Callable[[str], AbstractContextManager[None]]

_EXPECTED_CASSETTES = {
    "wavespeed_submit",
    "wavespeed_poll",
    "wavespeed_poll_failed",
    "wavespeed_submit_401",
    "wavespeed_fetch",
    "wavespeed_fetch_error",
    "wavespeed_fetch_wrongmagic",
    "wavespeed_poll_unknown",
}


def _public_resolver(_host: str) -> list[str]:
    """Map any host → a public test IP so the §16 SSRF guard passes WITHOUT real DNS (the resolver
    is injected per the Q2 condition — we do NOT couple the test to a production allowed_hosts)."""
    return ["93.184.216.34"]


def _provider(
    scratch: Path,
    secrets: SecretsAccessor | None = None,
    *,
    max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
    max_candidates: int = DEFAULT_MAX_CANDIDATES,
) -> ImageGenProvider:
    from adapters.imagegen import WaveSpeedImageGenProvider

    # default model = the real WaveSpeed FLUX.2 [pro] path (matches the cassette endpoints).
    # inject the resolver (public IP) so the always-on private-IP SSRF floor passes without DNS.
    return WaveSpeedImageGenProvider(
        secrets=secrets or InMemorySecretsAccessor({"WAVESPEED_API_KEY": "sk-ws-test-PLACEHOLDER"}),
        scratch_dir=scratch,
        resolver=_public_resolver,
        max_bytes=max_bytes,
        max_candidates=max_candidates,
    )


def _ref(job_id: str) -> ProviderJobRef:
    return ProviderJobRef(
        provider="wavespeed",
        model="flux-2-pro",
        jobId=job_id,
        submittedAt=datetime(2026, 1, 1, tzinfo=UTC),
    )


def test_conforms_to_imagegenprovider_protocol(tmp_path: Path) -> None:
    """spec(§7) — the real adapter structurally satisfies the frozen ImageGenProvider Protocol
    (the typed binding IS the mypy --strict conformance assertion; parity with the mock)."""
    from adapters.imagegen import WaveSpeedImageGenProvider

    provider: ImageGenProvider = WaveSpeedImageGenProvider(
        secrets=InMemorySecretsAccessor({"WAVESPEED_API_KEY": "x"}),
        scratch_dir=tmp_path,
    )
    assert callable(provider.submit)
    assert callable(provider.poll)
    assert callable(provider.fetch)


def test_submit_returns_jobref_with_seed_and_transparent_bg(
    imagegen_cassette: Cassette, tmp_path: Path
) -> None:
    """spec(§7) — submit() puts transparent_bg + the pinned seed in the request body (asserted on
    the pure builder; vcr matches method+uri not body) + returns a well-formed ProviderJobRef."""
    from adapters.imagegen.wavespeed import build_submit_body

    body = build_submit_body("a red armchair", {"seed": 12345, "transparent_bg": True})
    assert body["seed"] == 12345
    assert body["transparent_bg"] is True

    provider = _provider(tmp_path)
    with imagegen_cassette("wavespeed_submit"):
        ref = provider.submit("a red armchair", {"seed": 12345, "transparent_bg": True})

    assert isinstance(ref, ProviderJobRef)
    assert ref.jobId
    assert ref.provider and ref.model


def test_poll_pending_then_succeeded(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§7) — poll walks pending (SUBMITTED/RUNNING + progress) → SUCCEEDED with urls +
    usage.latencyMs set."""
    provider = _provider(tmp_path)
    with imagegen_cassette("wavespeed_poll"):
        first = provider.poll(_ref("job-123"))
        second = provider.poll(_ref("job-123"))

    assert first.status in (PollStatus.SUBMITTED, PollStatus.RUNNING)
    assert first.progress is not None
    assert second.status is PollStatus.SUCCEEDED
    assert second.urls
    assert second.usage is not None and second.usage.latencyMs >= 0


def test_poll_job_failure_rides_pollresult_error(
    imagegen_cassette: Cassette, tmp_path: Path
) -> None:
    """spec(§17) — async channel (lesson 5): a job failure / poll-HTTP failure rides
    PollResult(FAILED|EXPIRED, error=ErrorEnvelope) — poll does NOT raise."""
    provider = _provider(tmp_path)
    with imagegen_cassette("wavespeed_poll_failed"):
        result = provider.poll(_ref("job-fail"))  # must not raise

    assert result.status in (PollStatus.FAILED, PollStatus.EXPIRED)
    assert isinstance(result.error, ErrorEnvelope)
    assert result.error.code is ErrorCode.PROVIDER_OUTAGE  # job-failure classification


def test_poll_unknown_status_maps_to_running(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """An unrecognized WaveSpeed status (not completed/failed/created/processing) is treated as
    still-pending (RUNNING) — pins the deliberate fallback. The Phase-2 poll loop's max-attempts cap
    bounds the unlikely 'new terminal status' case (Step-9 flag)."""
    provider = _provider(tmp_path)
    with imagegen_cassette("wavespeed_poll_unknown"):
        result = provider.poll(_ref("job-unknown"))  # must not raise
    assert result.status is PollStatus.RUNNING


def test_poll_missing_key_rides_pollresult_error(tmp_path: Path) -> None:
    """spec(§17) — poll NEVER raises: even a missing key (raised by the call-time key-pull, which is
    INSIDE poll's guard) rides PollResult.error rather than escaping."""
    provider = _provider(tmp_path, secrets=InMemorySecretsAccessor({}))  # no key configured
    result = provider.poll(_ref("job-x"))  # must not raise
    assert result.status is PollStatus.FAILED
    assert result.error is not None and result.error.code is ErrorCode.PROVIDER_AUTH_QUOTA


def test_usage_parsing_is_defensive() -> None:
    """poll never raises, so usage parsing must degrade (not blow up) on a bad/negative/absent
    inference — a valid one yields ProviderUsage; anything else yields None."""
    from adapters.imagegen.wavespeed import _usage

    assert _usage({"timings": {"inference": 2500}}) is not None
    assert _usage({"timings": {"inference": "N/A"}}) is None
    assert _usage({"timings": {"inference": -5}}) is None
    assert _usage({}) is None


def test_submit_http_failure_raises(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§17) — submit has no result error field, so an HTTP failure RAISES ProviderError
    (no ref to return); 401 → PROVIDER_AUTH_QUOTA."""
    provider = _provider(tmp_path)
    from adapters.errors import ProviderError

    with imagegen_cassette("wavespeed_submit_401"), pytest.raises(ProviderError) as exc:
        provider.submit("x", {"seed": 1})
    assert exc.value.envelope.code is ErrorCode.PROVIDER_AUTH_QUOTA


def test_fetch_http_failure_raises(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§17) — fetch returns paths (no error field), so a download HTTP failure RAISES
    ProviderError."""
    provider = _provider(tmp_path)
    from adapters.errors import ProviderError

    with imagegen_cassette("wavespeed_fetch_error"), pytest.raises(ProviderError):
        provider.fetch(["https://cdn.wavespeed.ai/out/missing.png"])


def test_fetch_writes_scratch_guarded(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§16/rule3) — fetch writes only under the sidecar scratch dir with a sanitized basename;
    a basename that would escape scratch is rejected (the shared scratch guard, mock-analogue)."""
    provider = _provider(tmp_path)
    with imagegen_cassette("wavespeed_fetch"):
        paths = provider.fetch(["https://cdn.wavespeed.ai/out/concept.png"])

    assert len(paths) == 1
    written = Path(paths[0]).resolve()
    assert tmp_path.resolve() in written.parents  # under scratch
    assert written.read_bytes()  # non-empty

    # the shared scratch guard sanitizes an adversarial basename to stay under scratch (no network)
    from adapters.imagegen._base import safe_scratch_path

    guarded = safe_scratch_path(tmp_path, "https://x/../../../etc/passwd", index=0)
    assert tmp_path.resolve() in guarded.resolve().parents


def test_fetch_rejects_oversized(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§16) — a download exceeding the adapter's max_bytes raises ProviderError (wired through
    get_bytes' streaming cap). Reuses the happy cassette body with a tiny cap."""
    from adapters.errors import ProviderError

    provider = _provider(tmp_path, max_bytes=16)
    with imagegen_cassette("wavespeed_fetch"), pytest.raises(ProviderError) as exc:
        provider.fetch(["https://cdn.wavespeed.ai/out/concept.png"])
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT


def test_fetch_rejects_wrong_magic(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """spec(§16) — a downloaded body that isn't an allowed image kind (an HTML error page) →
    ProviderError(MALFORMED_OUTPUT), wired through validate_content."""
    from adapters.errors import ProviderError

    provider = _provider(tmp_path)
    with imagegen_cassette("wavespeed_fetch_wrongmagic"), pytest.raises(ProviderError) as exc:
        provider.fetch(["https://cdn.wavespeed.ai/out/notimage.png"])
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT


def test_fetch_rejects_too_many_candidates(tmp_path: Path) -> None:
    """spec(§16) — more than max_candidates urls is rejected BEFORE any download (no cassette)."""
    from adapters.errors import ProviderError

    provider = _provider(tmp_path, max_candidates=2)
    with pytest.raises(ProviderError) as exc:
        provider.fetch([f"https://cdn.wavespeed.ai/out/{i}.png" for i in range(5)])
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED


def test_key_via_accessor_not_persisted(imagegen_cassette: Cassette, tmp_path: Path) -> None:
    """safety rule 5 — the key is pulled via SecretsAccessor.get(name) at call time, never at
    construction, never stashed as a raw attribute, never in repr/str."""
    secret_value = "sk-ws-SUPER-SECRET-xyz789"
    spy = SpyAccessor({"WAVESPEED_API_KEY": secret_value})
    provider = _provider(tmp_path, secrets=spy)

    assert spy.get_calls == []  # nothing pulled at construction

    with imagegen_cassette("wavespeed_submit"):
        provider.submit("a red armchair", {"seed": 12345, "transparent_bg": True})

    assert "WAVESPEED_API_KEY" in spy.get_calls
    assert secret_value not in repr(provider)
    assert secret_value not in str(provider)
    # substring check (not element-equality) — the raw key must not hide inside any str attribute
    str_attrs = [v for v in vars(provider).values() if isinstance(v, str)]
    assert not any(secret_value in attr for attr in str_attrs)


def test_cassettes_have_no_authorization_header() -> None:
    """safety rule 5 — every committed cassette is scrubbed: no auth header / live key bytes."""
    cassettes = sorted(CASSETTE_DIR.glob("*.yaml"))
    present = {c.stem for c in cassettes}
    assert _EXPECTED_CASSETTES <= present, f"missing cassettes: {_EXPECTED_CASSETTES - present}"

    for cassette in cassettes:
        text = cassette.read_text().lower()
        assert "authorization" not in text, f"{cassette.name} leaks an Authorization header"
        assert "x-api-key" not in text, f"{cassette.name} leaks an x-api-key header"
        assert "bearer sk-" not in text, f"{cassette.name} leaks a bearer key"


def test_factory_seam_no_self_registration() -> None:
    """fp-2 — the imagegen adapter resolves through a static name→constructor map; nothing
    self-registers/self-instantiates on import, and it does not bleed into the other seams."""
    from adapters.imagegen import IMAGEGEN_PROVIDERS, WaveSpeedImageGenProvider
    from adapters.llm import LLM_PROVIDERS
    from adapters.mock import MOCK_PROVIDERS

    assert set(IMAGEGEN_PROVIDERS) == {"wavespeed"}
    assert IMAGEGEN_PROVIDERS["wavespeed"] is WaveSpeedImageGenProvider
    assert all(isinstance(ctor, type) for ctor in IMAGEGEN_PROVIDERS.values())
    assert "wavespeed" not in MOCK_PROVIDERS
    assert "wavespeed" not in LLM_PROVIDERS
