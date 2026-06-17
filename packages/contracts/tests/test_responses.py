"""RED tests for the IPC REST response bodies (§4) — slice 0.4b.

Completes the frozen IPC contract: a named response model per the 14 §4 endpoints, each
embedding the now-landed 0.4a domain entity (Project / PipelineRun / ItemSpec / …), a
``RESPONSE_MODELS`` registry parallel to ``ipc.REQUEST_MODELS``, and a ``responses_schema()``
producer guarded by a ``spec(§4)`` schema snapshot. Also pins ``GateKind`` single-definition
(no duplicate §2.5-seam enum in domain/responses). SHAPES only — the FastAPI routes that
return these bodies are Phase 2; the TS client that consumes them is 0.6.
"""

import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
from pydantic import BaseModel, ValidationError

import aisims_contracts.domain as domain_mod
import aisims_contracts.error as error_mod
import aisims_contracts.ipc as ipc_mod
import aisims_contracts.responses as responses_mod
from aisims_contracts.domain import (
    ExportArtifact,
    FunctionalOverlay,
    ItemSpec,
    PipelineRun,
    Project,
    ProjectState,
    Step,
    StepState,
    ValidationResult,
)
from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from aisims_contracts.ipc import Endpoint, GateKind
from aisims_contracts.responses import (
    RESPONSE_MODELS,
    CancelJobResponse,
    CreateProjectResponse,
    ExportResponse,
    FunctionalResponse,
    GateResponse,
    IncludeItemResponse,
    ListProjectsResponse,
    RegenerateResponse,
    RerunStepResponse,
    RunResponse,
    SettingsResponse,
    ValidateResponse,
    responses_schema,
)

# TestInstallResponse / TestProviderResponse are referenced inline via ``responses_mod`` (NOT bound
# as module-level names) so pytest doesn't try to collect these ``Test*``-named contract models as
# test classes (a bare-name import — or even an alias — would re-trigger the collection warning).

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "responses.schema.json"

# Each endpoint that returns a single embedded domain entity → (response model, field, entity type).
SINGLE_ENTITY_EMBEDS: dict[Endpoint, tuple[type[BaseModel], str, type]] = {
    Endpoint.CREATE_PROJECT: (CreateProjectResponse, "project", Project),
    Endpoint.START_OR_RESUME_RUN: (RunResponse, "run", PipelineRun),
    Endpoint.GATE: (GateResponse, "run", PipelineRun),
    Endpoint.REGENERATE: (RegenerateResponse, "run", PipelineRun),
    Endpoint.INCLUDE_ITEM: (IncludeItemResponse, "item", ItemSpec),
    Endpoint.FUNCTIONAL: (FunctionalResponse, "overlay", FunctionalOverlay),
    Endpoint.EXPORT: (ExportResponse, "artifact", ExportArtifact),
    Endpoint.TEST_INSTALL: (responses_mod.TestInstallResponse, "run", PipelineRun),
    Endpoint.RERUN_STEP: (RerunStepResponse, "step", Step),
}


def _project() -> Project:
    return Project(
        id="p1",
        name="My Kitchen",
        prompt="a cozy retro kitchen",
        desiredItemCount=8,
        status=ProjectState.PLANNED,
    )


def _run() -> PipelineRun:
    return PipelineRun(id="run1", projectId="p1", runType="full", status=StepState.RUNNING)


def _error() -> ErrorEnvelope:
    return ErrorEnvelope(
        code=ErrorCode.SYSTEM,
        category=ErrorCategory.SYSTEM,
        retryable=False,
        creatorMessage="x",
        maintainerDetail="y",
    )


def test_response_models_present() -> None:  # spec(§4)
    """RESPONSE_MODELS covers 14 endpoints; each single-entity body embeds its A-table entity."""
    assert set(RESPONSE_MODELS) == set(Endpoint)
    assert len(Endpoint) == 14
    # Single-entity endpoints embed exactly the documented domain entity (the A table).
    for _ep, (model, field, entity) in SINGLE_ENTITY_EMBEDS.items():
        assert field in model.model_fields, f"{model.__name__}.{field}"
        assert model.model_fields[field].annotation is entity, model.__name__
    # Collection endpoints embed a list of the entity (+ pagination on LIST_PROJECTS, Q6).
    assert ListProjectsResponse.model_fields["items"].annotation == list[Project]
    for f in ("total", "limit", "offset"):
        assert f in ListProjectsResponse.model_fields
    assert ValidateResponse.model_fields["results"].annotation == list[ValidationResult]
    # Protocol-ack endpoints carry no domain entity (just the wire ack / settings view).
    assert set(CancelJobResponse.model_fields) == {"jobId", "cancelled"}
    assert set(SettingsResponse.model_fields) == {"simsModsPath", "telemetryEnabled"}
    assert responses_mod.TestProviderResponse.model_fields["error"].annotation == (
        ErrorEnvelope | None
    )


def test_responses_round_trip() -> None:  # spec(§4)
    """JSON round-trip preserves equality through each RESPONSE_MODELS TypeAdapter (§4/§13).

    Covers a representative spread of embedded-entity shapes: a single persisted entity (Project),
    a paginated collection (list[Project]), a PipelineRun-embedding body, and the ErrorEnvelope-
    bearing protocol-ack body — so a TypeAdapter/embed mismatch on any variant is caught.
    """
    resp = CreateProjectResponse(project=_project())
    adapter = RESPONSE_MODELS[Endpoint.CREATE_PROJECT]
    assert adapter.validate_json(adapter.dump_json(resp)) == resp
    listed = ListProjectsResponse(items=[_project()], total=1, limit=10, offset=0)
    list_adapter = RESPONSE_MODELS[Endpoint.LIST_PROJECTS]
    assert list_adapter.validate_json(list_adapter.dump_json(listed)) == listed
    run_resp = RunResponse(run=_run())
    run_adapter = RESPONSE_MODELS[Endpoint.START_OR_RESUME_RUN]
    assert run_adapter.validate_json(run_adapter.dump_json(run_resp)) == run_resp
    prov = responses_mod.TestProviderResponse(ok=False, latencyMs=42, error=_error())
    prov_adapter = RESPONSE_MODELS[Endpoint.TEST_PROVIDER]
    assert prov_adapter.validate_json(prov_adapter.dump_json(prov)) == prov


def test_responses_boundary_rejection() -> None:  # spec(§4)
    """extra='forbid' rejects an unknown field on a response body (Lesson 3 strictness).

    Includes the two ``Test*``-named models (referenced via ``responses_mod``) — they're the
    easiest to silently lose ``_Response`` inheritance on, so each gets a rejection assertion.
    """
    with pytest.raises(ValidationError):
        CancelJobResponse.model_validate({"jobId": "j1", "cancelled": True, "bogus": "boom"})
    with pytest.raises(ValidationError):
        CreateProjectResponse.model_validate({"project": _project().model_dump(), "stray": 1})
    with pytest.raises(ValidationError):
        responses_mod.TestInstallResponse.model_validate({"run": _run().model_dump(), "bogus": 1})
    with pytest.raises(ValidationError):
        responses_mod.TestProviderResponse.model_validate({"ok": True, "bogus": 1})


def test_gatekind_single_definition() -> None:  # spec(§4)
    """GateKind is single-homed in ipc (Lesson 5): no duplicate definition in domain/responses."""
    assert GateKind.__module__ == "aisims_contracts.ipc"
    # Absent, or (if re-exported) the SAME object — never a redefinition with separate identity.
    for mod in (domain_mod, responses_mod):
        sym = getattr(mod, "GateKind", None)
        assert sym is None or sym is GateKind, mod.__name__


def test_import_direction(intra_imports: Callable[[ModuleType], set[str]]) -> None:  # spec(§4)
    """Pin the acyclic intra-package import DAG: error ← domain ← ipc ← responses.

    mypy does NOT enforce import acyclicity — a cycle would only surface as an ImportError at
    collection. This makes the rule an explicit, pinned spec and pre-positions the Phase-2
    GateKind cycle guard (Q5 carry-forward): now that ipc imports domain (0.4b), a future domain
    gate model importing GateKind from ipc would create an ipc↔domain cycle. (Helper in conftest.)
    """
    error_imports = intra_imports(error_mod)
    domain_imports = intra_imports(domain_mod)
    ipc_imports = intra_imports(ipc_mod)
    responses_imports = intra_imports(responses_mod)

    # Forbidden upward edges are ABSENT (the orchestrator's ADD spec):
    assert error_imports.isdisjoint({"domain", "ipc", "responses"}), error_imports
    assert domain_imports.isdisjoint({"ipc", "responses"}), domain_imports
    assert "responses" not in ipc_imports, ipc_imports
    # Allowed downward edges are PRESENT (the DAG is real, not vacuously satisfied):
    assert "domain" in ipc_imports, ipc_imports  # the 0.4b tightening import
    assert {"ipc", "domain"} <= responses_imports, responses_imports


def test_responses_schema_snapshot() -> None:  # spec(§4)
    """§2.5-seam guard: the response surface == the checked-in snapshot (a drift is the failure).

    Regenerate deliberately (never a blind regen) and review the diff:
        uv run python -c "import json; from aisims_contracts.responses import responses_schema; \
            json.dump(responses_schema(), open('tests/__snapshots__/responses.schema.json','w'), \
            indent=2, sort_keys=True)"
    """
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert responses_schema() == expected
