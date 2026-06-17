"""Neutral, mock-free home for the sync provider error channel + §17 classification.

``ProviderError`` is hoisted here from ``adapters/mock/failure.py`` (carry-forward 0.8/0.9) so a
Phase-2 engine path can catch it without importing a mock module; ``mock/failure.py`` now
re-imports it. ``classify`` maps a provider HTTP status (or ``None`` for a timeout/connect error,
which has no response) to the closed §17 ``ErrorCode`` set; ``build_envelope`` stamps the §17
category + the transient-vs-terminal ``retryable`` posture (auth/quota terminal, the rest
transient). Real adapters RAISE ``ProviderError`` on a sync failure — the frozen §7 ``LLMProvider``
seam has no result error field (Lesson 5).

``maintainerDetail`` is a redaction-egress surface (safety rule 5): callers pass a BOUNDED provider
status/reason (e.g. ``"HTTP 429 from api.anthropic.com"``), NEVER a raw response body or the prompt
echo — the prompt isn't a registered secret, so don't lean on the 0.9 redactor to scrub it.
"""

from __future__ import annotations

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope


class ProviderError(Exception):
    """The sync provider error channel (§17): wraps an ``ErrorEnvelope``.

    Pipeline-local — the contract defines the error *data* (``ErrorEnvelope``); the sync-call error
    *channel* is a sidecar concern. Raised by ``LLMProvider.complete``/``structured`` on failure.
    """

    def __init__(self, envelope: ErrorEnvelope) -> None:
        super().__init__(f"{envelope.code}: {envelope.creatorMessage}")
        self.envelope = envelope


def classify(status: int | None) -> ErrorCode:
    """Map a provider HTTP ``status`` to the closed §17 ``ErrorCode`` set.

    ``None`` means a timeout / connection error (no HTTP response). 429 → rate-limit; 401/402 →
    auth-or-quota; any 5xx (incl. 503) → outage; anything else → the catch-all ``SYSTEM``.
    """
    if status is None:
        return ErrorCode.PROVIDER_TIMEOUT
    if status == 429:
        return ErrorCode.PROVIDER_RATE_LIMIT
    if status in (401, 402):
        return ErrorCode.PROVIDER_AUTH_QUOTA
    if status >= 500:
        return ErrorCode.PROVIDER_OUTAGE
    # other 4xx (and any 3xx that leaks through with redirects disabled) → the catch-all.
    return ErrorCode.SYSTEM


# code → (category, retryable, creatorMessage). The codes the real adapters emit; the §17
# transient-vs-terminal posture is the contract (auth/quota = terminal-config, NOT retryable; the
# rest transient). Distinct from the mock's _TAXONOMY (which carries canned per-code fixtures) —
# this is the §17 fact, independent of the mock.
_CLASSIFICATION: dict[ErrorCode, tuple[ErrorCategory, bool, str]] = {
    ErrorCode.PROVIDER_TIMEOUT: (
        ErrorCategory.NETWORK,
        True,
        "The provider took too long to respond — retrying may help.",
    ),
    ErrorCode.PROVIDER_RATE_LIMIT: (
        ErrorCategory.PROVIDER,
        True,
        "The provider is busy right now — we'll retry shortly.",
    ),
    ErrorCode.PROVIDER_AUTH_QUOTA: (
        ErrorCategory.PROVIDER,
        False,
        "Your provider account couldn't be used — check your key and billing in Settings.",
    ),
    ErrorCode.PROVIDER_OUTAGE: (
        ErrorCategory.PROVIDER,
        True,
        "The provider is temporarily unavailable — retrying may help.",
    ),
    ErrorCode.MALFORMED_OUTPUT: (
        ErrorCategory.VALIDATION,
        True,
        "The AI returned something we couldn't read — we'll try again.",
    ),
    # A deterministic validation gate rejected the output (§17 / rule 6) — e.g. the 3.2 silhouette
    # gate when no concept candidate passes. Terminal (the caller decides regenerate-vs-fail).
    ErrorCode.VALIDATION_FAILED: (
        ErrorCategory.VALIDATION,
        False,
        "Something didn't pass our safety and validation checks.",
    ),
    ErrorCode.SYSTEM: (
        ErrorCategory.SYSTEM,
        False,
        "Something went wrong on our side.",
    ),
}


def build_envelope(code: ErrorCode, *, maintainer_detail: str | None = None) -> ErrorEnvelope:
    """Build an ``ErrorEnvelope`` for ``code`` with its §17 category + transient/terminal posture.

    ``maintainer_detail`` MUST be a bounded provider status/reason (safety rule 5) — never a raw
    response body / prompt echo. When omitted, a generic ``"<code> (<category>)"`` is used.

    This builder's first-class domain is the provider-classified codes in ``_CLASSIFICATION``; a
    code outside it (e.g. a downstream stage code) degrades to a conservative SYSTEM/non-retryable
    envelope that still carries the real ``code`` — never a ``KeyError`` at an egress boundary.
    """
    category, retryable, creator_message = _CLASSIFICATION.get(
        code, _CLASSIFICATION[ErrorCode.SYSTEM]
    )
    return ErrorEnvelope(
        code=code,
        category=category,
        retryable=retryable,
        creatorMessage=creator_message,
        maintainerDetail=maintainer_detail or f"{code.value} ({category.value})",
    )
