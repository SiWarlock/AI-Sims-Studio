"""RED tests for the frozen IPC contract (§4, §16, §17).

The typed REST + SSE boundary between the Electron UI and the FastAPI sidecar — SHAPES only
(routes / SSE stream / token middleware are Phase 2). Freezes the 8-event SSE discriminated
union (the ``error`` event embeds the 0.2 ``ErrorEnvelope``), the 14 REST request models, the
per-endpoint ``ErrorCode`` map (⊆ §17), ``HealthResponse(contractVersion)``, the token +
idempotency-key header conventions, and the §2.5-seam combined schema snapshot.
"""

import json
from pathlib import Path
from typing import get_args

import pytest
from pydantic import ValidationError

from aisims_contracts.domain import Severity, StepState, ValidationScope
from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from aisims_contracts.ipc import (
    CONTRACT_VERSION,
    ENDPOINT_ERROR_CODES,
    IDEMPOTENCY_KEY_HEADER,
    MUTATING_ENDPOINTS,
    READ_ONLY_ENDPOINTS,
    REQUEST_MODELS,
    SSE_ADAPTER,
    SSE_EVENT_MODELS,
    TOKEN_HEADER,
    DoneEvent,
    Endpoint,
    ErrorEvent,
    GateKind,
    HealthResponse,
    IpcRequestHeaders,
    LogLevel,
    ProgressEvent,
    ReadinessSubsystem,
    ReadyState,
    StepStateEvent,
    ValidationEvent,
    ipc_schema,
)

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "ipc.schema.json"

EXPECTED_EVENT_TAGS = {
    "progress",
    "step-state",
    "log",
    "validation",
    "cost",
    "gate-needed",
    "done",
    "error",
}

VALID_ENVELOPE = {
    "code": "SYSTEM",
    "category": "system",
    "retryable": False,
    "creatorMessage": "x",
    "maintainerDetail": "y",
}


def test_sse_event_union_members() -> None:  # spec(§4)
    """The SSE discriminated union covers exactly the 8 event tags; each tag → its model."""
    assert set(SSE_EVENT_MODELS) == EXPECTED_EVENT_TAGS
    for tag, model in SSE_EVENT_MODELS.items():
        assert model.model_fields["event"].default == tag


def test_protocol_enums_membership() -> None:  # spec(§4)
    """Protocol-level closed enums (Q1 guardrail 1) assert exact membership."""
    assert {member.value for member in LogLevel} == {"debug", "info", "warning", "error"}
    assert {member.value for member in GateKind} == {"plan", "concept", "mesh", "overlay", "export"}


def test_sse_error_event_embeds_errorenvelope() -> None:  # spec(§17)
    """The ``error`` event payload IS ErrorEnvelope (imported from 0.2, never duplicated)."""
    assert ErrorEvent.model_fields["error"].annotation is ErrorEnvelope
    assert SSE_EVENT_MODELS["error"] is ErrorEvent
    env = ErrorEnvelope(
        code=ErrorCode.SYSTEM,
        category=ErrorCategory.SYSTEM,
        retryable=False,
        creatorMessage="x",
        maintainerDetail="y",
    )
    event = ErrorEvent(id="42", error=env)
    back = SSE_ADAPTER.validate_json(SSE_ADAPTER.dump_json(event))
    assert isinstance(back, ErrorEvent)
    assert back.error == env


def test_rest_request_models_present() -> None:  # spec(§4)
    """A request model exists for each of the 15 endpoints (the multi-mode ones are unions)."""
    assert set(REQUEST_MODELS) == set(Endpoint)
    assert len(Endpoint) == 15


def test_idempotency_key_on_mutating_commands() -> None:  # spec(§4)
    """Idempotency travels as a header; required iff the endpoint mutates (GETs omit it)."""
    assert IDEMPOTENCY_KEY_HEADER
    assert TOKEN_HEADER
    assert "idempotencyKey" in IpcRequestHeaders.model_fields
    assert "token" in IpcRequestHeaders.model_fields
    # Mutating + read-only partition the 14 endpoints with no overlap.
    assert MUTATING_ENDPOINTS | READ_ONLY_ENDPOINTS == set(Endpoint)
    assert MUTATING_ENDPOINTS.isdisjoint(READ_ONLY_ENDPOINTS)
    assert Endpoint.LIST_PROJECTS in READ_ONLY_ENDPOINTS
    assert Endpoint.CREATE_PROJECT in MUTATING_ENDPOINTS


def test_endpoint_error_code_map() -> None:  # spec(§17)
    """The endpoint→ErrorCode map covers all 14 endpoints; codes ⊆ the §17 enum (no strays)."""
    assert set(ENDPOINT_ERROR_CODES) == set(Endpoint)
    all_codes = {code for codes in ENDPOINT_ERROR_CODES.values() for code in codes}
    assert all_codes <= set(ErrorCode)


def test_health_response_contract_version() -> None:  # spec(§4)
    """HealthResponse carries contractVersion == the module constant (pinned to "1.0")."""
    assert CONTRACT_VERSION == "1.0"
    health = HealthResponse(contractVersion=CONTRACT_VERSION)
    assert health.contractVersion == CONTRACT_VERSION


def test_boundary_rejection() -> None:  # spec(§4)
    """Unknown event tag / unknown command discriminator / extra field → ValidationError."""
    with pytest.raises(ValidationError):
        SSE_ADAPTER.validate_python({"event": "not-a-real-event", "id": "1"})
    with pytest.raises(ValidationError):
        SSE_ADAPTER.validate_python(
            {"event": "error", "id": "1", "error": VALID_ENVELOPE, "bogus": "boom"}
        )
    runs = REQUEST_MODELS[Endpoint.START_OR_RESUME_RUN]
    with pytest.raises(ValidationError):
        runs.validate_python({"action": "not-a-mode"})


def test_progress_fraction_bounded() -> None:  # spec(§4)
    """ProgressEvent.fraction is a structural [0,1] invariant (safety rule 6)."""
    ProgressEvent(id="1", runId="r", fraction=0.5)
    for bad in (-0.1, 1.1):
        with pytest.raises(ValidationError):
            ProgressEvent(id="1", runId="r", fraction=bad)


def test_sse_fields_tightened() -> None:  # spec(§4)
    """[D15] The 4 loose SSE str fields are now their domain enums; out-of-enum values reject.

    Lesson 5: a freeze-before-dependency seam ships str first, then a mandatory pinned tighten
    once the dependency (0.4a domain enums) lands. No loose domain str survives the SSE union.
    """
    assert StepStateEvent.model_fields["status"].annotation is StepState
    assert ValidationEvent.model_fields["severity"].annotation is Severity
    assert ValidationEvent.model_fields["scope"].annotation is ValidationScope
    # DoneEvent.status is the 4th tightened field — a Literal subset; pin its exact members.
    assert get_args(DoneEvent.model_fields["status"].annotation) == (
        StepState.SUCCEEDED,
        StepState.FAILED,
        StepState.CANCELLED,
    )
    # Accept a valid enum value; reject an out-of-enum one (membership now pins the value).
    StepStateEvent(id="1", runId="r", stepId="s", status=StepState.RUNNING)
    with pytest.raises(ValidationError):
        StepStateEvent(id="1", runId="r", stepId="s", status="bogus")
    ValidationEvent(id="1", scope=ValidationScope.MESH, severity=Severity.ERROR, message="m")
    with pytest.raises(ValidationError):
        ValidationEvent(id="1", scope="nope", severity=Severity.ERROR, message="m")
    with pytest.raises(ValidationError):
        ValidationEvent(id="1", scope=ValidationScope.MESH, severity="nope", message="m")


def test_done_status_terminal_subset() -> None:  # spec(§4)
    """DoneEvent.status is the run-terminal subset {succeeded, failed, cancelled}; others reject.

    The ``done`` event is run-terminal (§6/§12 PipelineRun) — non-terminal run states must not
    validate, and no separate RunTerminalStatus enum is minted (Lesson 5, subset via Literal).
    """
    for ok in (StepState.SUCCEEDED, StepState.FAILED, StepState.CANCELLED):
        DoneEvent(id="1", runId="r", status=ok)
    for bad in ("running", "pending", "waiting-for-user", "retrying", "skipped"):
        with pytest.raises(ValidationError):
            DoneEvent(id="1", runId="r", status=bad)
    # A non-terminal StepState *member* (not just its raw string) is also rejected.
    with pytest.raises(ValidationError):
        DoneEvent(id="1", runId="r", status=StepState.RUNNING)


def test_ipc_schema_snapshot() -> None:  # spec(§4)
    """§2.5-seam guard: the combined IPC schema == the checked-in snapshot (drift = failure).

    A drift is a REAL failure, never a blind regen. To intentionally evolve the contract,
    regenerate deliberately and review the diff:
        uv run python -c "import json; from aisims_contracts.ipc import ipc_schema; \
            json.dump(ipc_schema(), open('tests/__snapshots__/ipc.schema.json','w'), \
            indent=2, sort_keys=True)"
    """
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert ipc_schema() == expected


# ===========================================================================================
# Additive GET /readiness (contracts-012, item a) — the §4 readiness surface the UI onboarding
# gate consumes. ADDITIVE-ONLY: it adds a new endpoint + new enums/models without perturbing any
# pre-existing model, so the live §4 consumers (core / providers / mesh-export) are unaffected.
# ===========================================================================================
# The 14 endpoints frozen at the §4 seal — the additive-only baseline: the readiness slice may
# ADD "GET /readiness" but must not perturb any of these (consumers-unaffected guarantee).
PRE_READINESS_ENDPOINTS = {
    "POST /projects",
    "GET /projects",
    "POST /projects/{id}/runs",
    "POST /runs/{id}/gate",
    "POST /items/{id}/regenerate",
    "POST /items/{id}/include",
    "POST /items/{id}/functional",
    "POST /projects/{id}/validate",
    "POST /projects/{id}/export",
    "POST /projects/{id}/test-install",
    "POST /steps/{id}/rerun",
    "DELETE /jobs/{id}",
    "GET/PUT /settings",
    "POST /settings/providers/{p}/test",
}


def test_readiness_enums_membership() -> None:  # spec(§4)
    """The two readiness StrEnums freeze their member sets (protocol enums like LogLevel/GateKind;
    grow additively like ErrorCode, with the UI tolerant-consumer pattern if needed)."""
    assert {member.value for member in ReadyState} == {"ready", "degraded", "blocked"}
    assert {member.value for member in ReadinessSubsystem} == {
        "postgres",
        "blender",
        "sims_install",
        "mods_path",
        "providers",
    }


def test_readiness_endpoint_registered_readonly() -> None:  # spec(§4)
    """GET /readiness is an additive, read-only endpoint wired into every per-endpoint map; its
    only ErrorCode is {SYSTEM}; the request body is empty (a GET, no body/query params)."""
    assert Endpoint.READINESS.value == "GET /readiness"
    assert Endpoint.READINESS in READ_ONLY_ENDPOINTS
    assert Endpoint.READINESS in REQUEST_MODELS
    assert ENDPOINT_ERROR_CODES[Endpoint.READINESS] == frozenset({ErrorCode.SYSTEM})
    # the maps stay total over the endpoint set; the read/mutate partition still holds.
    assert set(REQUEST_MODELS) == set(Endpoint)
    assert set(ENDPOINT_ERROR_CODES) == set(Endpoint)
    assert MUTATING_ENDPOINTS | READ_ONLY_ENDPOINTS == set(Endpoint)
    assert MUTATING_ENDPOINTS.isdisjoint(READ_ONLY_ENDPOINTS)
    assert Endpoint.READINESS not in MUTATING_ENDPOINTS


def test_existing_snapshots_unchanged_except_readiness() -> None:  # spec(§4)
    """Additive-only proof (IPC side): readiness ADDS keys without perturbing any pre-existing
    endpoint, the read/mutate partition, or the SSE stream — so the live §4 consumers
    (core / providers / mesh-export) are provably unaffected. The error/domain seams' byte-identity
    is held by their own (unchanged) snapshot tests; providers/workers/registries change only by the
    0.5b minLength tightening (item b), proven by their re-frozen snapshots + set-assertions."""
    assert len(PRE_READINESS_ENDPOINTS) == 14
    schema = ipc_schema()
    # readiness is the ONLY new key across every per-endpoint map.
    assert set(schema["requestModels"]) == PRE_READINESS_ENDPOINTS | {"GET /readiness"}
    assert set(schema["endpointErrorCodes"]) == PRE_READINESS_ENDPOINTS | {"GET /readiness"}
    # readiness joins the read-only set; the prior read-only membership (GET /projects) is intact.
    assert set(schema["readOnlyEndpoints"]) == {"GET /projects", "GET /readiness"}
    # readiness is REST-only: it mints NO SSE event, so the streamed union is byte-stable.
    assert set(SSE_EVENT_MODELS) == EXPECTED_EVENT_TAGS
    # the protocol constants the UI negotiates against are unchanged by the addition.
    assert schema["contractVersion"] == "1.0"
    assert schema["headers"] == {"token": TOKEN_HEADER, "idempotencyKey": IDEMPOTENCY_KEY_HEADER}
