"""RED tests for the frozen IPC contract (§4, §16, §17).

The typed REST + SSE boundary between the Electron UI and the FastAPI sidecar — SHAPES only
(routes / SSE stream / token middleware are Phase 2). Freezes the 8-event SSE discriminated
union (the ``error`` event embeds the 0.2 ``ErrorEnvelope``), the 14 REST request models, the
per-endpoint ``ErrorCode`` map (⊆ §17), ``HealthResponse(contractVersion)``, the token +
idempotency-key header conventions, and the §2.5-seam combined schema snapshot.
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

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
    Endpoint,
    ErrorEvent,
    GateKind,
    HealthResponse,
    IpcRequestHeaders,
    LogLevel,
    ProgressEvent,
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
    """A request model exists for each of the 14 endpoints (the multi-mode ones are unions)."""
    assert set(REQUEST_MODELS) == set(Endpoint)
    assert len(Endpoint) == 14


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
