"""The frozen ``ErrorEnvelope`` contract (ARCHITECTURE §17, Appendix A).

``ErrorEnvelope`` is the 6th frozen shared contract — carried in the SSE ``error`` event,
``Step.error``, and ``ValidationResult``, and emitted by every stage (mock + real). It is a
§2.5-seam model: its JSON-Schema is frozen by a snapshot test before tracks fork, and the
pydantic model is the single source of truth for the §4 py↔ts codegen.
"""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class ErrorCode(StrEnum):
    """Closed, stable per-stage error code set (§17).

    Within-version PRODUCER contract: the sidecar emits only these codes; an out-of-enum
    value is rejected at the boundary (deterministic validation, safety rule 6).

    CONSUMERS (the 0.6 TS codegen type + engine/UI switch logic) MUST treat any unrecognized
    code as ``SYSTEM`` for forward compatibility, so a future additive split is non-breaking;
    that tolerance is tested where consumers live, not here.

    ``PROVIDER_AUTH_QUOTA`` groups auth (401) and quota/billing (402); the 401-vs-402
    distinction is preserved in ``ErrorEnvelope.maintainerDetail`` at emit time.
    """

    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_RATE_LIMIT = "PROVIDER_RATE_LIMIT"
    PROVIDER_AUTH_QUOTA = "PROVIDER_AUTH_QUOTA"
    PROVIDER_OUTAGE = "PROVIDER_OUTAGE"
    ARTIFACT_EXPIRED = "ARTIFACT_EXPIRED"
    MALFORMED_OUTPUT = "MALFORMED_OUTPUT"
    MESH_QA_FAILED = "MESH_QA_FAILED"
    GEOM_EXPORT_FAILED = "GEOM_EXPORT_FAILED"
    DBPF_WRITE_FAILED = "DBPF_WRITE_FAILED"
    TEST_INSTALL_FAILED = "TEST_INSTALL_FAILED"
    DISK_FULL = "DISK_FULL"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    SYSTEM = "SYSTEM"


class ErrorCategory(StrEnum):
    """Closed coarse error-category set (§17) — the routing/telemetry grouping for a code."""

    # Names are UPPER, values are the lowercase wire tokens; StrEnum makes the value the
    # canonical string — consumers compare/serialize via the value (str(member)), never .name.
    PROVIDER = "provider"
    NETWORK = "network"
    VALIDATION = "validation"
    GEOMETRY = "geometry"
    PACKAGING = "packaging"
    BUDGET = "budget"
    SYSTEM = "system"


class ErrorEnvelope(BaseModel):
    """Frozen error contract (§17, §4): SSE ``error``, ``Step.error``, ``ValidationResult``.

    Field names are camelCase to match the JSON/TS wire form (§4) — no alias indirection.
    ``extra="forbid"`` rejects unknown fields at the boundary (frozen §2.5-seam, safety rule 6).
    """

    model_config = ConfigDict(extra="forbid")

    # code and category are independent producer-asserted axes (no fixed code->category map):
    # the emitter sets both; consumers treat an unknown code as SYSTEM (forward-compat).
    code: ErrorCode
    category: ErrorCategory
    retryable: bool
    creatorMessage: str
    # maintainerDetail is a redaction-egress surface (safety rule 5): it rides in the SSE
    # error event / Step.error / ValidationResult — scrub secrets at the §16/§14 egress;
    # never emit raw provider error bodies or auth material into it.
    maintainerDetail: str
    traceRef: str | None = None
    suggestedAction: str | None = None
