"""The §8/§9 worker job/report contracts — slice 0.5b.

The job-file/result-file envelopes crossing the sidecar↔worker boundary: the Blender mesh worker
(BlenderJob → BlenderReport + GateMetrics + the GEOM-bytes scratch-ref) and the Sims export worker
(ExportJob → ExportJobReport — the §9 worker report, renamed to disambiguate from the §12 domain
``ExportReport`` it would otherwise collide with).

Safety rule 3 (sidecar = SOLE writer): every artifact field is a path/ref into sidecar-provided
scratch (``geomBytesRef`` / ``previewRef`` / ``packagePath``), never inline bytes and never a write
into Postgres or the canonical artifact tree. Safety rule 6 (deterministic validation of worker
output before any state write): a ``model_validator`` pins status↔outputs consistency so a malformed
report (e.g. ``succeeded`` with no GEOM) can't cross the boundary. ``ErrorEnvelope`` (0.2) carries
failures.

SHAPES only — the bpy mesh/GEOM logic, the @s4tk packaging, and the atomic-write/DBPF-round-trip/
test-install flow (safety rule 4) are the worker impls (Phase 1 spikes + Phase 2), NOT here. Import
direction: ``workers`` imports ``error`` only — its own §2.5 seam, sibling of domain/providers (all
import ``error``); it does NOT import ipc/domain/responses/providers. Conventions follow 0.2–0.5a:
``extra="forbid"``, camelCase fields, ``StrEnum`` for closed sets, one combined ``spec(§8/§9)``
schema-snapshot over the value models.
"""

from enum import StrEnum
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from aisims_contracts.error import ErrorEnvelope


class _Worker(BaseModel):
    """Base for every worker value model: strict boundary (extra='forbid'), camelCase (§4)."""

    model_config = ConfigDict(extra="forbid")


class BlenderJobStatus(StrEnum):
    """Terminal status of a Blender mesh job (§8). The §17 hang-watchdog kill→retry is impl; the
    terminal status is what the report carries."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ExportJobStatus(StrEnum):
    """Terminal status of a Sims export job (§9). ``partial`` = some per-item packages complete-and-
    valid while others failed (never a half-written file). Distinct from the domain ``ExportState``
    (the node's rollup on ``ExportArtifact``); the node MAPS this onto that."""

    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class BBox(_Worker):
    """An axis-aligned bounding box (donor rescale target, §8) — two cardinality-pinned corners."""

    minCorner: tuple[float, float, float]
    maxCorner: tuple[float, float, float]


class GateMetrics(_Worker):
    """The §8 game-ready gate metrics: pass/fail flags + counts. ``normals`` (recalc/transfer — S4S
    drops normals), ``uv`` (uv_0 + uv_1 present), ``lods`` (LOD + shadow-LOD count), ``polyByTile``
    (per-tile poly budget, ~2000 tris/tile LOD0), ``meshgroups`` (meshgroup-count match)."""

    normals: bool
    uv: bool
    lods: int
    polyByTile: dict[str, int]
    meshgroups: int


class BlenderJob(_Worker):
    """Inputs the sidecar hands the Blender CLI subprocess (§8). ``meshPath`` is a scratch-path ref;
    ``params`` is the open, job-specific knob bag (the adapter/worker interprets it)."""

    # min_length=1 (0.5b): meshPath/jobId are real scratch-path / id refs, never blank (rule 3/6).
    meshPath: str = Field(min_length=1)
    params: dict[str, Any]
    donorBBox: BBox
    jobId: str = Field(min_length=1)


class BlenderReport(_Worker):
    """The Blender worker result (§8). Outputs are scratch-path refs, absent on a failed run; a
    ``model_validator`` pins status↔outputs consistency (safety rule 6). ``previewRef`` stays
    optional even on success (nice-to-have, not a core output)."""

    # min_length=1: a present ref is a real scratch path, never blank (rule 6).
    geomBytesRef: str | None = Field(default=None, min_length=1)
    previewRef: str | None = Field(default=None, min_length=1)
    gateMetrics: GateMetrics | None = None
    status: BlenderJobStatus
    error: ErrorEnvelope | None = None

    @model_validator(mode="after")
    def _check_status_outputs(self) -> Self:
        if self.status is BlenderJobStatus.SUCCEEDED:
            if self.geomBytesRef is None or self.gateMetrics is None:
                raise ValueError("succeeded BlenderReport requires geomBytesRef + gateMetrics")
            if self.error is not None:
                raise ValueError("succeeded BlenderReport must not carry an error")
        elif self.status is BlenderJobStatus.FAILED and self.error is None:
            raise ValueError("failed BlenderReport requires an error")
        return self


class ExportJob(_Worker):
    """Inputs the sidecar hands the @s4tk export worker (§9). ``geomBytesRef`` is the §8 output
    threaded through (the §8↔§9 GEOM-bytes flow); ``textures`` are scratch refs; ``tuningEdits`` is
    the open OBJD-tuning edit bag; ``targetTGIKeys`` are the target resource keys."""

    # min_length=1 (0.5b): donorRef/geomBytesRef/jobId are real refs/ids, never blank (rule 3/6).
    donorRef: str = Field(min_length=1)
    geomBytesRef: str = Field(min_length=1)
    textures: list[str] = Field(default_factory=list)
    tuningEdits: dict[str, Any] = Field(default_factory=dict)
    targetTGIKeys: list[str] = Field(default_factory=list)
    jobId: str = Field(min_length=1)


class ExportJobReport(_Worker):
    """The §9 export-worker result — renamed from the arch's ``ExportReport`` to disambiguate from
    the §12 domain ``ExportReport`` (0.4a, frozen; different concern: human-readable summary).
    ``packagePath`` is a scratch-path ref, absent on a total failure; a ``model_validator`` pins
    status↔outputs consistency (safety rule 6): ``succeeded`` ⟹ packagePath present AND error None;
    ``partial`` ⟹ packagePath present (a partial result MAY carry an ``error`` describing the
    per-item failure); ``failed`` ⟹ error present."""

    # min_length=1: a present packagePath is a real scratch path, never blank (rule 6).
    packagePath: str | None = Field(default=None, min_length=1)
    includedItems: list[str] = Field(default_factory=list)
    resourceManifest: list[str] = Field(default_factory=list)
    status: ExportJobStatus
    error: ErrorEnvelope | None = None

    @model_validator(mode="after")
    def _check_status_outputs(self) -> Self:
        if self.status in (ExportJobStatus.SUCCEEDED, ExportJobStatus.PARTIAL):
            if self.packagePath is None:
                raise ValueError(f"{self.status.value} ExportJobReport requires a packagePath")
            # A full success carries no error (partial MAY — it describes the per-item failure).
            if self.status is ExportJobStatus.SUCCEEDED and self.error is not None:
                raise ValueError("succeeded ExportJobReport must not carry an error")
        elif self.status is ExportJobStatus.FAILED and self.error is None:
            raise ValueError("failed ExportJobReport requires an error")
        return self


# The frozen worker value-model surface, in stable definition order, for the §2.5-seam snapshot.
_VALUE_MODELS: dict[str, type[BaseModel]] = {
    "BBox": BBox,
    "GateMetrics": GateMetrics,
    "BlenderJob": BlenderJob,
    "BlenderReport": BlenderReport,
    "ExportJob": ExportJob,
    "ExportJobReport": ExportJobReport,
}


def workers_schema() -> dict[str, Any]:
    """The combined §8/§9 worker value-model surface for the §2.5-seam snapshot — each model's
    JSON-Schema (the status enums + embedded GateMetrics/BBox ride in each model's ``$defs``)."""
    return {name: model.model_json_schema() for name, model in _VALUE_MODELS.items()}
