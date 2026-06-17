"""RED tests for the §8/§9 worker job/report contracts — slice 0.5b.

Freezes the job-file/result-file envelopes crossing the sidecar↔worker boundary: the Blender mesh
worker (BlenderJob → BlenderReport + GateMetrics + the GEOM-bytes scratch-ref) and the Sims export
worker (ExportJob → ExportJobReport, the disambiguated §9 report). Safety rule 3 (sidecar = sole
writer): every artifact field is a scratch-path *ref*, never inline bytes / a canonical-tree write.
ErrorEnvelope (0.2) carries failures. The bpy mesh logic + @s4tk packaging are worker impls
(Phase 1/2), NOT here.
"""

import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

import pytest
from pydantic import ValidationError

import aisims_contracts.workers as workers_mod
from aisims_contracts.domain import ExportReport as DomainExportReport
from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from aisims_contracts.workers import (
    BBox,
    BlenderJob,
    BlenderJobStatus,
    BlenderReport,
    ExportJob,
    ExportJobReport,
    ExportJobStatus,
    GateMetrics,
    workers_schema,
)

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "workers.schema.json"


def _bbox() -> BBox:
    return BBox(minCorner=(0.0, 0.0, 0.0), maxCorner=(1.0, 2.0, 3.0))


def _gate_metrics() -> GateMetrics:
    return GateMetrics(normals=True, uv=True, lods=4, polyByTile={"lod0": 1800}, meshgroups=2)


def _blender_report() -> BlenderReport:
    return BlenderReport(
        geomBytesRef="scratch/geom/abc.bin",
        previewRef="scratch/preview/abc.png",
        gateMetrics=_gate_metrics(),
        status=BlenderJobStatus.SUCCEEDED,
    )


def _export_report() -> ExportJobReport:
    return ExportJobReport(
        packagePath="scratch/pkg/abc.package",
        includedItems=["i1", "i2"],
        resourceManifest=["OBJD", "COBJ", "GEOM"],
        status=ExportJobStatus.SUCCEEDED,
    )


def _error() -> ErrorEnvelope:
    return ErrorEnvelope(
        code=ErrorCode.GEOM_EXPORT_FAILED,
        category=ErrorCategory.GEOMETRY,
        retryable=False,
        creatorMessage="x",
        maintainerDetail="y",
    )


def test_blender_job_report_models() -> None:  # spec(§8)
    """BlenderJob/BlenderReport field sets exact; geom/preview are str refs (rule 3); round-trip."""
    assert set(BlenderJob.model_fields) == {"meshPath", "params", "donorBBox", "jobId"}
    assert set(BlenderReport.model_fields) == {
        "geomBytesRef",
        "previewRef",
        "gateMetrics",
        "status",
        "error",
    }
    # rule 3: outputs are scratch-path str refs (optional — absent on failure), never bytes.
    assert BlenderReport.model_fields["geomBytesRef"].annotation == (str | None)
    assert BlenderReport.model_fields["previewRef"].annotation == (str | None)
    job = BlenderJob(
        meshPath="scratch/mesh/x.glb", params={"smooth": True}, donorBBox=_bbox(), jobId="b1"
    )
    assert BlenderJob.model_validate_json(job.model_dump_json()) == job
    report = _blender_report()
    assert BlenderReport.model_validate_json(report.model_dump_json()) == report
    with pytest.raises(ValidationError):
        BlenderJob.model_validate({**job.model_dump(mode="json"), "bogus": 1})


def test_gate_metrics_model() -> None:  # spec(§8)
    """GateMetrics{normals,uv,lods,polyByTile,meshgroups} — pass/fail flags + counts; strict."""
    assert set(GateMetrics.model_fields) == {"normals", "uv", "lods", "polyByTile", "meshgroups"}
    assert GateMetrics.model_fields["normals"].annotation is bool
    assert GateMetrics.model_fields["uv"].annotation is bool
    assert GateMetrics.model_fields["lods"].annotation is int
    assert GateMetrics.model_fields["meshgroups"].annotation is int
    assert GateMetrics.model_fields["polyByTile"].annotation == dict[str, int]
    gm = _gate_metrics()
    assert GateMetrics.model_validate_json(gm.model_dump_json()) == gm
    with pytest.raises(ValidationError):
        GateMetrics.model_validate({**gm.model_dump(), "bogus": 1})


def test_bbox_model() -> None:  # spec(§8)
    """BBox is two 3-float corners (cardinality-pinned), the donor rescale target; round-trip."""
    bb = _bbox()
    assert BBox.model_validate_json(bb.model_dump_json()) == bb
    with pytest.raises(ValidationError):  # exactly 3 floats per corner
        BBox(minCorner=(0.0, 0.0), maxCorner=(1.0, 1.0, 1.0))


def test_export_job_model() -> None:  # spec(§9)
    """ExportJob field set exact; geomBytesRef is the §8 ref threaded through; round-trip."""
    assert set(ExportJob.model_fields) == {
        "donorRef",
        "geomBytesRef",
        "textures",
        "tuningEdits",
        "targetTGIKeys",
        "jobId",
    }
    assert ExportJob.model_fields["geomBytesRef"].annotation is str  # the §8↔§9 GEOM-bytes ref
    job = ExportJob(
        donorRef="donor/123",
        geomBytesRef="scratch/geom/abc.bin",
        textures=["scratch/tex/d.dst"],
        tuningEdits={"price": 50},
        targetTGIKeys=["0x1_0x2_0x3"],
        jobId="e1",
    )
    assert ExportJob.model_validate_json(job.model_dump_json()) == job
    with pytest.raises(ValidationError):
        ExportJob.model_validate({**job.model_dump(mode="json"), "bogus": 1})


def test_export_worker_report_disambiguated() -> None:  # spec(§9)
    """Q1 collision guard: the §9 worker report is ExportJobReport — a DISTINCT symbol + field set
    from the §12 domain ExportReport (0.4a, frozen). The shared name was the collision; the worker
    one is renamed (Lesson 5: never re-freeze the landed domain contract)."""
    # Distinct symbols with distinct names — the worker report took the disambiguated name.
    assert ExportJobReport.__name__ == "ExportJobReport"
    assert DomainExportReport.__name__ == "ExportReport"
    assert set(ExportJobReport.model_fields) == {
        "packagePath",
        "includedItems",
        "resourceManifest",
        "status",
        "error",
    }
    assert set(ExportJobReport.model_fields) != set(DomainExportReport.model_fields)
    # packagePath is a scratch-path ref (rule 3), optional — absent on a total failure.
    assert ExportJobReport.model_fields["packagePath"].annotation == (str | None)
    report = _export_report()
    assert ExportJobReport.model_validate_json(report.model_dump_json()) == report
    with pytest.raises(ValidationError):
        ExportJobReport.model_validate({**report.model_dump(mode="json"), "bogus": 1})


def test_report_status_output_consistency() -> None:  # spec(§8)/spec(§9)
    """status↔outputs consistency (safety rule 6 / within-model invariant, à la Inv7): an
    inconsistent worker report does NOT validate — a malformed output never slips the boundary.

    BlenderReport: succeeded ⟹ geomBytesRef + gateMetrics present AND error is None; failed ⟹ error
    present. ExportJobReport: succeeded ⟹ packagePath present AND error None; partial ⟹ packagePath
    present (error optional — it describes the per-item failure); failed ⟹ error present. previewRef
    stays optional even on success.
    """
    # BlenderReport — valid combinations construct fine.
    _blender_report()  # succeeded: geom + gateMetrics present, error None
    BlenderReport(status=BlenderJobStatus.FAILED, error=_error())  # failed: error present
    # succeeded but missing geomBytesRef (the geomBytesRef-is-None branch of the `or`) → reject.
    with pytest.raises(ValidationError):
        BlenderReport(status=BlenderJobStatus.SUCCEEDED, gateMetrics=_gate_metrics())
    # succeeded but missing gateMetrics (the gateMetrics-is-None branch of the `or`) → reject.
    with pytest.raises(ValidationError):
        BlenderReport(status=BlenderJobStatus.SUCCEEDED, geomBytesRef="scratch/g.bin")
    # succeeded but the present ref is blank (min_length=1, rule 6) → reject.
    with pytest.raises(ValidationError):
        BlenderReport(
            status=BlenderJobStatus.SUCCEEDED, geomBytesRef="", gateMetrics=_gate_metrics()
        )
    # succeeded but error set → reject (no error on a successful run).
    with pytest.raises(ValidationError):
        BlenderReport(
            status=BlenderJobStatus.SUCCEEDED,
            geomBytesRef="scratch/g.bin",
            gateMetrics=_gate_metrics(),
            error=_error(),
        )
    # failed but no error → reject.
    with pytest.raises(ValidationError):
        BlenderReport(status=BlenderJobStatus.FAILED)

    # ExportJobReport — valid combinations.
    _export_report()  # succeeded: packagePath present
    ExportJobReport(
        status=ExportJobStatus.PARTIAL, packagePath="scratch/p.package", includedItems=["i1"]
    )
    ExportJobReport(status=ExportJobStatus.FAILED, error=_error())
    # intentional asymmetry vs BlenderReport: a partial result MAY carry an error (the per-item
    # partial failure) — so success/partial + error is VALID (error-None is not enforced here).
    ExportJobReport(
        status=ExportJobStatus.PARTIAL,
        packagePath="scratch/p.package",
        includedItems=["i1"],
        error=_error(),
    )
    # succeeded/partial but no packagePath → reject.
    with pytest.raises(ValidationError):
        ExportJobReport(status=ExportJobStatus.SUCCEEDED, includedItems=["i1"])
    with pytest.raises(ValidationError):
        ExportJobReport(status=ExportJobStatus.PARTIAL, includedItems=["i1"])
    # succeeded but the present packagePath is blank (min_length=1, rule 6) → reject.
    with pytest.raises(ValidationError):
        ExportJobReport(status=ExportJobStatus.SUCCEEDED, packagePath="")
    # full success must NOT carry an error (flag-3 ruling: symmetry with BlenderReport) → reject.
    with pytest.raises(ValidationError):
        ExportJobReport(
            status=ExportJobStatus.SUCCEEDED, packagePath="scratch/p.package", error=_error()
        )
    # failed but no error → reject.
    with pytest.raises(ValidationError):
        ExportJobReport(status=ExportJobStatus.FAILED)


def test_worker_status_members() -> None:  # spec(§9)
    """Worker-local status enums (== membership); ExportJobStatus carries §9 partial success."""
    assert {m.value for m in BlenderJobStatus} == {"succeeded", "failed"}
    assert {m.value for m in ExportJobStatus} == {"succeeded", "partial", "failed"}


def test_worker_failure_uses_error_envelope() -> None:  # spec(§17)
    """A failed worker report carries the 0.2 ErrorEnvelope, not a bespoke error."""
    assert BlenderReport.model_fields["error"].annotation == (ErrorEnvelope | None)
    assert ExportJobReport.model_fields["error"].annotation == (ErrorEnvelope | None)
    env = _error()
    report = BlenderReport(status=BlenderJobStatus.FAILED, error=env)  # outputs absent on failure
    assert report.geomBytesRef is None
    assert report.error == env
    assert BlenderReport.model_validate_json(report.model_dump_json()) == report


def test_workers_import_direction(intra_imports: Callable[[ModuleType], set[str]]) -> None:
    """workers.py imports `error` only — its own §2.5 seam (acyclic DAG); spec(§8)/spec(§9).

    NOT ipc/domain/responses/providers — a worker contract carries refs + ErrorEnvelope, nothing
    from the other seams (uses the shared intra_imports conftest fixture from 0.5a).
    """
    imports = intra_imports(workers_mod)
    assert imports == {"error"}, imports
    assert imports.isdisjoint({"ipc", "domain", "responses", "providers"}), imports


def test_workers_schema_snapshot() -> None:  # spec(§8)/spec(§9)
    """§2.5-seam guard: the worker value-model schema == the checked-in snapshot (drift = failure).

    Regenerate deliberately (never a blind regen) and review the diff:
        uv run python -c "import json; from aisims_contracts.workers import workers_schema; \
            json.dump(workers_schema(), open('tests/__snapshots__/workers.schema.json','w'), \
            indent=2, sort_keys=True)"
    """
    # Pin the value-model set independently of the snapshot (catches a silent model drop pre-regen).
    assert set(workers_schema()) == {
        "BBox",
        "GateMetrics",
        "BlenderJob",
        "BlenderReport",
        "ExportJob",
        "ExportJobReport",
    }
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert workers_schema() == expected
