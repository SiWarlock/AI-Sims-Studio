"""The IPC REST response bodies (§4) — slice 0.4b, completing the frozen IPC contract.

One named response model per the 14 §4 endpoints, each embedding the landed 0.4a domain entity
(``Project`` / ``PipelineRun`` / ``ItemSpec`` / …) so each endpoint's success response can evolve
additively without disturbing the embedded domain type (symmetry with ``ipc.REQUEST_MODELS``). A
``RESPONSE_MODELS`` registry + ``responses_schema()`` producer back the ``spec(§4)`` snapshot.

SHAPES only: the FastAPI routes that *return* these bodies are Phase 2 (sidecar); the TS client
that consumes them is 0.6. Import direction (acyclic, §2.5): ``responses → {ipc, domain}`` and
``ipc/domain → error`` — this module never reaches back into ``ipc`` to mutate request shapes.
Conventions follow 0.2/0.3/0.4a: ``extra="forbid"``, camelCase wire fields, no alias indirection.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, TypeAdapter

from aisims_contracts.domain import (
    ExportArtifact,
    FunctionalOverlay,
    ItemSpec,
    PipelineRun,
    Project,
    Step,
    ValidationResult,
)
from aisims_contracts.error import ErrorEnvelope
from aisims_contracts.ipc import Endpoint


class _Response(BaseModel):
    """Base for every REST response body: strict boundary (extra='forbid'), camelCase (§4)."""

    model_config = ConfigDict(extra="forbid")


# --- single-entity responses (embed exactly one domain entity per the §4 / A-table mapping) ---
class CreateProjectResponse(_Response):
    project: Project


class RunResponse(_Response):
    """START_OR_RESUME_RUN — returns the run that was started/resumed; candidates stream via SSE."""

    run: PipelineRun


class GateResponse(_Response):
    """GATE — returns the advanced run state after the gate decision is applied."""

    run: PipelineRun


class RegenerateResponse(_Response):
    """REGENERATE — async job started; the regenerated candidate streams via SSE."""

    run: PipelineRun


class IncludeItemResponse(_Response):
    item: ItemSpec


class FunctionalResponse(_Response):
    overlay: FunctionalOverlay


class ExportResponse(_Response):
    """EXPORT — the export artifact handle (embeds the ExportReport summary)."""

    artifact: ExportArtifact


class TestInstallResponse(_Response):
    """TEST_INSTALL — async run; the install result streams via SSE."""

    run: PipelineRun


class RerunStepResponse(_Response):
    step: Step


# --- collection responses ---
class ListProjectsResponse(_Response):
    """LIST_PROJECTS — the page of projects + pagination echo (mirrors ListProjectsRequest)."""

    items: list[Project]
    total: int
    limit: int | None = None
    offset: int | None = None


class ValidateResponse(_Response):
    results: list[ValidationResult]


# --- protocol-ack responses (no domain entity) ---
class CancelJobResponse(_Response):
    jobId: str
    cancelled: bool


class SettingsResponse(_Response):
    """GET/PUT /settings — the protocol settings view. Secrets NEVER ride here (safety rule 5)."""

    telemetryEnabled: bool
    simsModsPath: str | None = None


class TestProviderResponse(_Response):
    """TEST_PROVIDER — connectivity probe; ``error`` carries the 0.2 ErrorEnvelope on failure."""

    ok: bool
    latencyMs: int | None = None
    error: ErrorEnvelope | None = None


# The endpoint → response-model registry, parallel to ipc.REQUEST_MODELS (all 14 endpoints).
RESPONSE_MODELS: dict[Endpoint, TypeAdapter[Any]] = {
    Endpoint.CREATE_PROJECT: TypeAdapter(CreateProjectResponse),
    Endpoint.LIST_PROJECTS: TypeAdapter(ListProjectsResponse),
    Endpoint.START_OR_RESUME_RUN: TypeAdapter(RunResponse),
    Endpoint.GATE: TypeAdapter(GateResponse),
    Endpoint.REGENERATE: TypeAdapter(RegenerateResponse),
    Endpoint.INCLUDE_ITEM: TypeAdapter(IncludeItemResponse),
    Endpoint.FUNCTIONAL: TypeAdapter(FunctionalResponse),
    Endpoint.VALIDATE: TypeAdapter(ValidateResponse),
    Endpoint.EXPORT: TypeAdapter(ExportResponse),
    Endpoint.TEST_INSTALL: TypeAdapter(TestInstallResponse),
    Endpoint.RERUN_STEP: TypeAdapter(RerunStepResponse),
    Endpoint.CANCEL_JOB: TypeAdapter(CancelJobResponse),
    Endpoint.SETTINGS: TypeAdapter(SettingsResponse),
    Endpoint.TEST_PROVIDER: TypeAdapter(TestProviderResponse),
}


def responses_schema() -> dict[str, Any]:
    """The §2.5-seam snapshot for the REST response surface: each endpoint → its response model's
    JSON-Schema (embedded domain entities + their state enums ride in each model's ``$defs``)."""
    return {ep.value: RESPONSE_MODELS[ep].json_schema() for ep in Endpoint}
