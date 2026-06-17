"""§17 deterministic failure-injection core for the mock adapters (REQ-T-101).

A typed ``FailurePlan`` (a list of ``FailureRule``s keyed by operation + 1-based call index) tells
a mock to fail deterministically; ``envelope_for`` builds a valid ``ErrorEnvelope`` for any of the
13 ``ErrorCode``s with a sensible category + retryable classification (transient ⟹ retryable;
``PROVIDER_AUTH_QUOTA`` terminal). ``ProviderError`` is the pipeline-local sync error channel
(the §7 ``LLMProvider`` calls have no error field, so they raise) — Phase-3 real adapters may hoist
it to a neutral ``adapters/errors.py``.
"""

from __future__ import annotations

from enum import StrEnum

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from pydantic import BaseModel, ConfigDict, Field


class MockOp(StrEnum):
    """The mock operations a failure can be injected at. SUBMIT/FETCH are omitted: neither has a
    contract error channel, so a submit-class failure surfaces at the first POLL instead."""

    POLL = "poll"
    COMPLETE = "complete"
    STRUCTURED = "structured"
    BLENDER_RUN = "blender_run"
    EXPORT_RUN = "export_run"


class FailureRule(BaseModel):
    """Fail ``operation`` on its ``at_call``-th invocation (1-based) with ``code``."""

    model_config = ConfigDict(extra="forbid")

    operation: MockOp
    code: ErrorCode
    at_call: int = Field(default=1, ge=1)


class FailurePlan(BaseModel):
    """A deterministic, declarative set of failure rules handed to a mock at construction."""

    model_config = ConfigDict(extra="forbid")

    rules: list[FailureRule] = Field(default_factory=list)

    def match(self, operation: MockOp, call_index: int) -> ErrorCode | None:
        """The injected code for ``operation`` at ``call_index`` (1-based), or None."""
        for rule in self.rules:
            if rule.operation is operation and rule.at_call == call_index:
                return rule.code
        return None


class ProviderError(Exception):
    """The sync provider error channel (§17 / 0.8-Q5): wraps an ``ErrorEnvelope``.

    Pipeline-local — the contract defines the error *data* (``ErrorEnvelope``); the sync-call error
    *channel* is a sidecar concern. Raised by ``LLMProvider.complete``/``structured`` on failure.
    """

    def __init__(self, envelope: ErrorEnvelope) -> None:
        super().__init__(f"{envelope.code}: {envelope.creatorMessage}")
        self.envelope = envelope


# Per-code taxonomy: (category, retryable, creatorMessage, maintainerDetail). Covers every
# ErrorCode (all 13) — the parametrized test iterates list(ErrorCode) and asserts each is present.
# PROVIDER_AUTH_QUOTA.maintainerDetail seeds a secret-looking token on purpose: it is the realistic
# egress surface the 0.9 redaction chokepoint (PINNED rule-5 item) must scrub.
_TAXONOMY: dict[ErrorCode, tuple[ErrorCategory, bool, str, str]] = {
    ErrorCode.PROVIDER_TIMEOUT: (
        ErrorCategory.NETWORK,
        True,
        "The provider took too long to respond — retrying may help.",
        "Provider request exceeded the wall-clock timeout (transient).",
    ),
    ErrorCode.PROVIDER_RATE_LIMIT: (
        ErrorCategory.PROVIDER,
        True,
        "The provider is busy right now — we'll retry shortly.",
        "HTTP 429 rate-limited; honor Retry-After before resubmitting.",
    ),
    ErrorCode.PROVIDER_AUTH_QUOTA: (
        ErrorCategory.PROVIDER,
        False,
        "Your provider account couldn't be used — check your key and billing in Settings.",
        # the bearer token below is a SYNTHETIC fixture (not a real key) — the deliberate rule-5
        # egress surface the 0.9 redaction chokepoint must scrub (see module docstring).
        "Provider rejected credentials (401); Authorization: Bearer sk-live-9f8e7d6c5b4a3210 "
        "was refused — verify the key in Settings.",
    ),
    ErrorCode.PROVIDER_OUTAGE: (
        ErrorCategory.PROVIDER,
        True,
        "The provider is temporarily unavailable — retrying may help.",
        "Provider returned 5xx / service outage (transient).",
    ),
    ErrorCode.ARTIFACT_EXPIRED: (
        ErrorCategory.PROVIDER,
        False,
        "A generated file expired before we could download it — regenerate to continue.",
        "Signed artifact URL past expiresAt (Tripo 24h race); re-fetch unavailable, regenerate.",
    ),
    ErrorCode.MALFORMED_OUTPUT: (
        ErrorCategory.VALIDATION,
        True,
        "The AI returned something we couldn't read — we'll try again.",
        "Model output failed pydantic validation; the bounded repair loop may recover.",
    ),
    ErrorCode.MESH_QA_FAILED: (
        ErrorCategory.GEOMETRY,
        True,
        "The 3D mesh didn't pass quality checks — we'll attempt a repair.",
        "Mesh QA gate failed (non-manifold / normals / poly budget); repairable.",
    ),
    ErrorCode.GEOM_EXPORT_FAILED: (
        ErrorCategory.GEOMETRY,
        False,
        "We couldn't turn this mesh into a game-ready object.",
        "GEOM export failed (LOD / meshgroup / uv); not retryable without new geometry.",
    ),
    ErrorCode.DBPF_WRITE_FAILED: (
        ErrorCategory.PACKAGING,
        False,
        "We couldn't build the Sims package file.",
        "DBPF write / round-trip validate failed; package not produced.",
    ),
    ErrorCode.TEST_INSTALL_FAILED: (
        ErrorCategory.PACKAGING,
        False,
        "The package couldn't be test-installed into your game.",
        "Test-install verification failed (Mods path / permission / placeability).",
    ),
    ErrorCode.DISK_FULL: (
        ErrorCategory.SYSTEM,
        False,
        "Your disk is full — free some space and try again.",
        "No space left on device while writing scratch / artifact bytes.",
    ),
    ErrorCode.VALIDATION_FAILED: (
        ErrorCategory.VALIDATION,
        False,
        "Something didn't pass our safety and validation checks.",
        "Deterministic validation gate rejected the output before a state write (rule 6).",
    ),
    ErrorCode.SYSTEM: (
        ErrorCategory.SYSTEM,
        False,
        "Something went wrong on our side.",
        "Unclassified internal error; see the trace for the stack.",
    ),
}


def envelope_for(code: ErrorCode) -> ErrorEnvelope:
    """Build a valid, egress-realistic ``ErrorEnvelope`` for ``code`` (§17 taxonomy)."""
    category, retryable, creator_message, maintainer_detail = _TAXONOMY[code]
    return ErrorEnvelope(
        code=code,
        category=category,
        retryable=retryable,
        creatorMessage=creator_message,
        maintainerDetail=maintainer_detail,
    )
