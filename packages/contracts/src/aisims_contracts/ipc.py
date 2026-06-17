"""The frozen IPC contract (§4, §16, §17) — the typed REST + SSE boundary between the Electron
UI and the FastAPI sidecar.

SHAPES only: the FastAPI routes, the SSE stream, and the loopback-token / idempotency
middleware are Phase 2 (sidecar); the TS client is 0.6. Per Step-2.5 Q1 (0.3↔0.4 coupling,
option A-refined), this is the domain-INDEPENDENT protocol surface — SSE events reference
domain objects by ``str`` IDs + protocol-level status/severity strings; REST response bodies
that return domain entities (Project / PipelineRun / Step / ValidationResult) are defined in
0.4. Conventions follow 0.2: the ``aisims_contracts`` package, ``extra="forbid"``, and
camelCase wire field names (no alias indirection, §4).
"""

from enum import StrEnum
from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from aisims_contracts.error import ErrorCode, ErrorEnvelope

# --- versioning + wire conventions (§4, §16) ---
# contractVersion is returned at /health and negotiated by the UI; a mismatch is handled in
# Phase 2 (the shape is frozen here, the enforcement is not).
CONTRACT_VERSION = "1.0"
# Per-launch loopback token (§16): the sidecar mints it, hands it to the renderer over the
# trusted parent->child channel, and every request must present it (reject otherwise, Phase 2).
TOKEN_HEADER = "X-AISims-Token"
# Idempotency key on mutating commands (R9); the conventional Stripe-style header name.
IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"


class _Wire(BaseModel):
    """Base for every IPC wire model: strict boundary (extra='forbid'), camelCase fields (§4)."""

    model_config = ConfigDict(extra="forbid")


# --- closed PROTOCOL enums (Q1 guardrail 1): a wire-level severity/lifecycle that is NOT a 0.4
# domain-entity field is a real enum here NOW, never a str placeholder. ---
class LogLevel(StrEnum):
    """Wire-level log severity for the SSE ``log`` event (protocol concept, not a 0.4 enum)."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class GateKind(StrEnum):
    """The 5 ordered approval gates (plan→concept→mesh→overlay→export; safety rule 6).

    A protocol/workflow concept (which gate the run is paused at) — defined here, not a 0.4
    domain-entity field.
    """

    PLAN = "plan"
    CONCEPT = "concept"
    MESH = "mesh"
    OVERLAY = "overlay"
    EXPORT = "export"


# ===========================================================================================
# SSE event taxonomy (§4) — a discriminated union keyed on the ``event`` Literal tag. Each event
# carries ``id`` (the resume cursor, Q4=str). Per the Q1 guardrail, status/severity fields are
# classified: PROTOCOL concepts (log level, gate kind) are enums here; DOMAIN fields that ARE a
# 0.4 enum (Step status, run status, ValidationResult scope/severity) stay str + a MANDATORY
# pinned 0.4 tightening. Domain objects are referenced by str IDs, never embedded entities.
# ===========================================================================================
class _SseEventBase(_Wire):
    """Common SSE envelope: the resume cursor shared by every event."""

    id: str


class ProgressEvent(_SseEventBase):
    event: Literal["progress"] = "progress"
    runId: str
    # [0,1] is a structural numeric invariant of a progress fraction (safety rule 6).
    fraction: float = Field(ge=0.0, le=1.0)
    message: str | None = None


class StepStateEvent(_SseEventBase):
    event: Literal["step-state"] = "step-state"
    runId: str
    stepId: str
    # DOMAIN field (the §12/§6 Step 8-state lifecycle) → str here, MANDATORY-tightened to the
    # Step-status enum in 0.4 (pinned carry-forward); no loose domain str survives the merge.
    status: str


class LogEvent(_SseEventBase):
    event: Literal["log"] = "log"
    level: LogLevel
    message: str
    stepId: str | None = None


class ValidationEvent(_SseEventBase):
    event: Literal["validation"] = "validation"
    # DOMAIN fields (§12 ValidationResult.scope/.severity) → str here, MANDATORY-tightened to the
    # domain enums in 0.4 (pinned carry-forward); the full ValidationResult entity lands in 0.4.
    scope: str
    severity: str
    message: str
    itemId: str | None = None


class CostEvent(_SseEventBase):
    event: Literal["cost"] = "cost"
    runId: str
    amountCents: int
    currency: str = "USD"


class GateNeededEvent(_SseEventBase):
    event: Literal["gate-needed"] = "gate-needed"
    runId: str
    # PROTOCOL concept (which ordered approval gate the run is paused at) → a real enum here NOW.
    gate: GateKind
    itemId: str | None = None


class DoneEvent(_SseEventBase):
    event: Literal["done"] = "done"
    runId: str
    # DOMAIN field (the §12/§6 PipelineRun terminal status) → str here, MANDATORY-tightened to the
    # run-status enum in 0.4 (pinned carry-forward).
    status: str


class ErrorEvent(_SseEventBase):
    event: Literal["error"] = "error"
    # The 6th frozen contract, imported from 0.2 — never a hand-rolled duplicate (§17).
    error: ErrorEnvelope
    runId: str | None = None
    stepId: str | None = None


SseEvent = Annotated[
    ProgressEvent
    | StepStateEvent
    | LogEvent
    | ValidationEvent
    | CostEvent
    | GateNeededEvent
    | DoneEvent
    | ErrorEvent,
    Field(discriminator="event"),
]
SSE_ADAPTER: TypeAdapter[SseEvent] = TypeAdapter(SseEvent)

SSE_EVENT_MODELS: dict[str, type[_SseEventBase]] = {
    "progress": ProgressEvent,
    "step-state": StepStateEvent,
    "log": LogEvent,
    "validation": ValidationEvent,
    "cost": CostEvent,
    "gate-needed": GateNeededEvent,
    "done": DoneEvent,
    "error": ErrorEvent,
}


# ===========================================================================================
# REST command surface (§4) — one request model per endpoint; multi-mode commands are
# discriminated unions. Request bodies only (Q1: response bodies returning domain entities
# land in 0.4). The loopback token + idempotency key travel as headers (see IpcRequestHeaders).
# ===========================================================================================
class Endpoint(StrEnum):
    """The 14 REST endpoints (§4). Value = ``METHOD path`` (GET/PUT /settings is one endpoint)."""

    CREATE_PROJECT = "POST /projects"
    LIST_PROJECTS = "GET /projects"
    START_OR_RESUME_RUN = "POST /projects/{id}/runs"
    GATE = "POST /runs/{id}/gate"
    REGENERATE = "POST /items/{id}/regenerate"
    INCLUDE_ITEM = "POST /items/{id}/include"
    FUNCTIONAL = "POST /items/{id}/functional"
    VALIDATE = "POST /projects/{id}/validate"
    EXPORT = "POST /projects/{id}/export"
    TEST_INSTALL = "POST /projects/{id}/test-install"
    RERUN_STEP = "POST /steps/{id}/rerun"
    CANCEL_JOB = "DELETE /jobs/{id}"
    SETTINGS = "GET/PUT /settings"
    TEST_PROVIDER = "POST /settings/providers/{p}/test"


class CreateProjectRequest(_Wire):
    name: str
    prompt: str | None = None


class ListProjectsRequest(_Wire):
    # GET /projects — these map to query parameters at the FastAPI layer (Phase 2), not a body.
    limit: int | None = None
    offset: int | None = None


class StartRunRequest(_Wire):
    action: Literal["start"] = "start"


class ResumeRunRequest(_Wire):
    action: Literal["resume"] = "resume"
    fromStepId: str | None = None


RunCommand = Annotated[StartRunRequest | ResumeRunRequest, Field(discriminator="action")]


class GateApproveRequest(_Wire):
    decision: Literal["approve"] = "approve"


class GateRejectRequest(_Wire):
    decision: Literal["reject"] = "reject"
    reason: str | None = None


class GateEditRequest(_Wire):
    # The edited gate content is domain-shaped (the plan being edited) → lands in 0.4; 0.3 freezes
    # only the protocol envelope + the optional free-text note.
    decision: Literal["edit"] = "edit"
    note: str | None = None


GateCommand = Annotated[
    GateApproveRequest | GateRejectRequest | GateEditRequest,
    Field(discriminator="decision"),
]


class RegenConceptRequest(_Wire):
    target: Literal["concept"] = "concept"


class RegenMeshRequest(_Wire):
    target: Literal["mesh"] = "mesh"


class RegenCleanupRequest(_Wire):
    target: Literal["cleanup"] = "cleanup"


RegenerateCommand = Annotated[
    RegenConceptRequest | RegenMeshRequest | RegenCleanupRequest,
    Field(discriminator="target"),
]


class IncludeItemRequest(_Wire):
    included: bool


class FunctionalRequest(_Wire):
    # archetype = a FunctionalArchetype registry key (str protocol-level; the registry is §11).
    archetype: str
    enabled: bool = True


class ValidateRequest(_Wire):
    scope: str | None = None


class ExportRequest(_Wire):
    itemIds: list[str] | None = None


class TestInstallRequest(_Wire):
    pass


class RerunStepRequest(_Wire):
    force: bool = False


class CancelJobRequest(_Wire):
    pass


class UpdateSettingsRequest(_Wire):
    # Minimal protocol-level settings (the full onboarding/Settings surface is §18). Secrets
    # (provider/LLM keys) NEVER ride here — they go to the OS keychain (safety rule 5).
    simsModsPath: str | None = None
    telemetryEnabled: bool | None = None


class TestProviderRequest(_Wire):
    # The provider id is the {p} path param; the key is already in the keychain (never in the body).
    model: str | None = None


REQUEST_MODELS: dict[Endpoint, TypeAdapter[Any]] = {
    Endpoint.CREATE_PROJECT: TypeAdapter(CreateProjectRequest),
    Endpoint.LIST_PROJECTS: TypeAdapter(ListProjectsRequest),
    Endpoint.START_OR_RESUME_RUN: TypeAdapter(RunCommand),
    Endpoint.GATE: TypeAdapter(GateCommand),
    Endpoint.REGENERATE: TypeAdapter(RegenerateCommand),
    Endpoint.INCLUDE_ITEM: TypeAdapter(IncludeItemRequest),
    Endpoint.FUNCTIONAL: TypeAdapter(FunctionalRequest),
    Endpoint.VALIDATE: TypeAdapter(ValidateRequest),
    Endpoint.EXPORT: TypeAdapter(ExportRequest),
    Endpoint.TEST_INSTALL: TypeAdapter(TestInstallRequest),
    Endpoint.RERUN_STEP: TypeAdapter(RerunStepRequest),
    Endpoint.CANCEL_JOB: TypeAdapter(CancelJobRequest),
    Endpoint.SETTINGS: TypeAdapter(UpdateSettingsRequest),
    Endpoint.TEST_PROVIDER: TypeAdapter(TestProviderRequest),
}

# Idempotency is required iff the endpoint mutates (R9). LIST_PROJECTS is the only pure read;
# /health is separate (not a command). SETTINGS is one endpoint (GET/PUT) classified mutating —
# its GET simply omits the optional key (the GET/PUT response split is a 0.4 concern).
READ_ONLY_ENDPOINTS: frozenset[Endpoint] = frozenset({Endpoint.LIST_PROJECTS})
MUTATING_ENDPOINTS: frozenset[Endpoint] = frozenset(set(Endpoint) - READ_ONLY_ENDPOINTS)


# ===========================================================================================
# Per-endpoint ErrorCode map (§17) — the ErrorCode subset each endpoint may return. Every code
# is a member of the §17 ErrorCode enum (the test asserts ⊆; no stray codes).
# ===========================================================================================
ENDPOINT_ERROR_CODES: dict[Endpoint, frozenset[ErrorCode]] = {
    Endpoint.CREATE_PROJECT: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.LIST_PROJECTS: frozenset({ErrorCode.SYSTEM}),
    Endpoint.START_OR_RESUME_RUN: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.GATE: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.REGENERATE: frozenset(
        {
            ErrorCode.PROVIDER_TIMEOUT,
            ErrorCode.PROVIDER_RATE_LIMIT,
            ErrorCode.PROVIDER_AUTH_QUOTA,
            ErrorCode.PROVIDER_OUTAGE,
            ErrorCode.ARTIFACT_EXPIRED,
            ErrorCode.MALFORMED_OUTPUT,
            ErrorCode.MESH_QA_FAILED,
            ErrorCode.VALIDATION_FAILED,
            ErrorCode.SYSTEM,
        }
    ),
    Endpoint.INCLUDE_ITEM: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.FUNCTIONAL: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.VALIDATE: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.EXPORT: frozenset(
        {
            ErrorCode.GEOM_EXPORT_FAILED,
            ErrorCode.DBPF_WRITE_FAILED,
            ErrorCode.DISK_FULL,
            ErrorCode.VALIDATION_FAILED,
            ErrorCode.SYSTEM,
        }
    ),
    Endpoint.TEST_INSTALL: frozenset(
        {ErrorCode.TEST_INSTALL_FAILED, ErrorCode.DISK_FULL, ErrorCode.SYSTEM}
    ),
    Endpoint.RERUN_STEP: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.CANCEL_JOB: frozenset({ErrorCode.SYSTEM}),
    Endpoint.SETTINGS: frozenset({ErrorCode.VALIDATION_FAILED, ErrorCode.SYSTEM}),
    Endpoint.TEST_PROVIDER: frozenset(
        {
            ErrorCode.PROVIDER_TIMEOUT,
            ErrorCode.PROVIDER_RATE_LIMIT,
            ErrorCode.PROVIDER_AUTH_QUOTA,
            ErrorCode.PROVIDER_OUTAGE,
            ErrorCode.SYSTEM,
        }
    ),
}


class IpcRequestHeaders(_Wire):
    """Per-request wire headers (§4/§16): ``token`` on every request, ``idempotencyKey`` on
    mutating commands (the header names are TOKEN_HEADER / IDEMPOTENCY_KEY_HEADER)."""

    token: str
    idempotencyKey: str | None = None


class HealthResponse(_Wire):
    """GET /health response (§4/§6) — carries the negotiated contractVersion."""

    contractVersion: str
    status: Literal["ok"] = "ok"


def ipc_schema() -> dict[str, Any]:
    """The combined IPC contract surface for the §2.5-seam snapshot: the SSE event union, every
    REST request model, HealthResponse, the request-headers convention, and the endpoint→ErrorCode
    map (codes sorted for a deterministic, diff-reviewable artifact)."""
    return {
        "contractVersion": CONTRACT_VERSION,
        "headers": {"token": TOKEN_HEADER, "idempotencyKey": IDEMPOTENCY_KEY_HEADER},
        "sseEvent": SSE_ADAPTER.json_schema(),
        "requestModels": {ep.value: REQUEST_MODELS[ep].json_schema() for ep in Endpoint},
        "requestHeaders": IpcRequestHeaders.model_json_schema(),
        "health": HealthResponse.model_json_schema(),
        "endpointErrorCodes": {
            ep.value: sorted(code.value for code in ENDPOINT_ERROR_CODES[ep]) for ep in Endpoint
        },
        "mutatingEndpoints": sorted(ep.value for ep in MUTATING_ENDPOINTS),
        "readOnlyEndpoints": sorted(ep.value for ep in READ_ONLY_ENDPOINTS),
    }
