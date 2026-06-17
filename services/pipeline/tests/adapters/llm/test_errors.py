"""RED — C1: the neutral ``adapters/errors.py`` foundation (§17 classification + the hoist).

Pure-deterministic, no live calls. Covers the brief acceptance bullets for the shared error
module: the HTTP-status→``ErrorCode`` classifier, the §17 retryable/category posture of the built
``ErrorEnvelope``, and the ``ProviderError`` hoist (mock surface stays intact).
"""

from __future__ import annotations

import pytest
from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (None, ErrorCode.PROVIDER_TIMEOUT),  # timeout / connect error → no HTTP response
        (429, ErrorCode.PROVIDER_RATE_LIMIT),
        (401, ErrorCode.PROVIDER_AUTH_QUOTA),
        (402, ErrorCode.PROVIDER_AUTH_QUOTA),
        (500, ErrorCode.PROVIDER_OUTAGE),
        (503, ErrorCode.PROVIDER_OUTAGE),
        (400, ErrorCode.SYSTEM),
        (404, ErrorCode.SYSTEM),
        (418, ErrorCode.SYSTEM),
    ],
)
def test_classify_http_status_to_error_code(status: int | None, expected: ErrorCode) -> None:
    """spec(§17) — provider HTTP failures map to the closed ErrorCode set: timeout/connect→TIMEOUT,
    429→RATE_LIMIT, 401/402→AUTH_QUOTA, 5xx/503→OUTAGE, anything else→SYSTEM."""
    from adapters.errors import classify

    assert classify(status) is expected


def test_auth_quota_not_retryable_transient_retryable() -> None:
    """spec(§17) — the built envelope carries the terminal-vs-transient posture: AUTH_QUOTA is a
    terminal-config failure (NOT retryable); timeout/rate-limit/outage are transient (retryable).
    Category routing: AUTH_QUOTA→provider, timeout→network."""
    from adapters.errors import build_envelope

    auth = build_envelope(ErrorCode.PROVIDER_AUTH_QUOTA)
    assert auth.retryable is False
    assert auth.category is ErrorCategory.PROVIDER

    for code in (
        ErrorCode.PROVIDER_TIMEOUT,
        ErrorCode.PROVIDER_RATE_LIMIT,
        ErrorCode.PROVIDER_OUTAGE,
    ):
        assert build_envelope(code).retryable is True

    assert build_envelope(ErrorCode.PROVIDER_TIMEOUT).category is ErrorCategory.NETWORK
    # MALFORMED_OUTPUT is retryable (the bounded repair loop is Phase-2) and a validation failure.
    malformed = build_envelope(ErrorCode.MALFORMED_OUTPUT)
    assert malformed.retryable is True
    assert malformed.category is ErrorCategory.VALIDATION


def test_build_envelope_unclassified_code_degrades_to_system() -> None:
    """A code outside the provider-classification set (e.g. a downstream stage code) must NOT
    KeyError at an egress boundary — it degrades to a conservative SYSTEM/non-retryable envelope
    that still carries the real code."""
    from adapters.errors import build_envelope

    envelope = build_envelope(ErrorCode.DISK_FULL)
    assert envelope.code is ErrorCode.DISK_FULL  # the real code is preserved
    assert envelope.category is ErrorCategory.SYSTEM
    assert envelope.retryable is False


def test_build_envelope_validation_failed_classified() -> None:
    """VALIDATION_FAILED is a known §17 code (the 3.2 silhouette gate is its first emitter): it
    classifies to VALIDATION / not-retryable — NOT the SYSTEM-degrade fallback."""
    from adapters.errors import build_envelope

    envelope = build_envelope(ErrorCode.VALIDATION_FAILED)
    assert envelope.code is ErrorCode.VALIDATION_FAILED
    assert envelope.category is ErrorCategory.VALIDATION
    assert envelope.retryable is False


def test_provider_error_carries_envelope() -> None:
    """The hoist (carry-forward 0.8/0.9): ProviderError lives in adapters.errors and is the SAME
    class re-exported from adapters.mock — so the mock surface (and its tests) stay intact, and a
    Phase-2 engine path can catch it without importing a mock module."""
    from adapters.errors import ProviderError
    from adapters.mock import ProviderError as MockProviderError

    assert ProviderError is MockProviderError  # re-export, not a copy

    envelope = ErrorEnvelope(
        code=ErrorCode.PROVIDER_RATE_LIMIT,
        category=ErrorCategory.PROVIDER,
        retryable=True,
        creatorMessage="busy",
        maintainerDetail="429",
    )
    err = ProviderError(envelope)
    assert err.envelope is envelope
    assert isinstance(err, Exception)
