"""RED — §8/§9 mock worker executors + the sole-writer conformance (rule 3 / fp-4).

Mock Blender (BlenderJob→BlenderReport) + export (ExportJob→ExportJobReport) executors build
reports THROUGH the frozen models, so the status↔outputs model_validator (rule 6) holds. They
write artifacts ONLY under their sidecar-provided scratch dir (rule 3 conformance — the
enforcement pin is 0.7's test_sidecar_sole_writer).
"""

from __future__ import annotations

from pathlib import Path

from aisims_contracts.error import ErrorCode
from aisims_contracts.workers import (
    BBox,
    BlenderJob,
    BlenderJobStatus,
    ExportJob,
    ExportJobStatus,
)


def _blender_job() -> BlenderJob:
    return BlenderJob(
        meshPath="scratch/in.obj",
        params={},
        donorBBox=BBox(minCorner=(0.0, 0.0, 0.0), maxCorner=(1.0, 1.0, 1.0)),
        jobId="blender-1",
    )


def _export_job() -> ExportJob:
    return ExportJob(donorRef="donor-1", geomBytesRef="scratch/geom.bin", jobId="export-1")


def test_mock_blender_worker_success_report(tmp_path: Path) -> None:
    """spec(§8) — a Blender success report carries geomBytesRef + gateMetrics and no error."""
    from adapters.mock.workers import MockBlenderWorker

    report = MockBlenderWorker(seed=1, scratch_dir=tmp_path).run(_blender_job())
    assert report.status is BlenderJobStatus.SUCCEEDED
    assert report.geomBytesRef is not None
    assert report.gateMetrics is not None
    assert report.error is None


def test_mock_export_worker_success_and_partial(tmp_path: Path) -> None:
    """spec(§9) — export success ⟹ packagePath/no error; partial ⟹ packagePath + per-item error."""
    from adapters.mock.workers import MockExportWorker

    ok = MockExportWorker(seed=1, scratch_dir=tmp_path).run(_export_job())
    assert ok.status is ExportJobStatus.SUCCEEDED
    assert ok.packagePath is not None and ok.error is None

    partial = MockExportWorker(seed=1, scratch_dir=tmp_path, partial=True).run(_export_job())
    assert partial.status is ExportJobStatus.PARTIAL
    assert partial.packagePath is not None
    assert partial.error is not None  # the per-item failure description


def test_mock_writes_only_to_scratch(tmp_path: Path) -> None:
    """spec(rule 3 / fp-4) — mocks write artifacts ONLY under the sidecar-provided scratch dir;
    the canonical artifact tree (here a sibling stand-in) is never touched."""
    from adapters.mock.providers import MockImage3DProvider
    from adapters.mock.workers import MockBlenderWorker, MockExportWorker

    scratch = tmp_path / "scratch"
    scratch.mkdir()
    canonical = tmp_path / "canonical"  # stand-in for the sidecar-only canonical tree
    canonical.mkdir()

    img = MockImage3DProvider(seed=1, scratch_dir=scratch, succeed_after_polls=2)
    ref = img.submit(b"x", {})
    res = img.poll(ref)
    res = img.poll(ref)  # SUCCEEDED → urls
    assert res.urls
    img.fetch(res.urls)
    MockBlenderWorker(seed=1, scratch_dir=scratch).run(_blender_job())
    MockExportWorker(seed=1, scratch_dir=scratch).run(_export_job())

    assert list(scratch.rglob("*")), "the mocks should have written into scratch"
    assert not list(canonical.rglob("*")), "mocks must not write outside their scratch dir"


def test_mock_worker_failure_injection(tmp_path: Path) -> None:
    """spec(§8/§9, §17) — a worker FailureRule yields a FAILED report carrying the injected
    envelope and NO outputs, valid under the status↔outputs validator (failed ⟹ error required)."""
    from adapters.mock.failure import FailurePlan, FailureRule, MockOp
    from adapters.mock.workers import MockBlenderWorker, MockExportWorker

    blender_plan = FailurePlan(
        rules=[FailureRule(operation=MockOp.BLENDER_RUN, at_call=1, code=ErrorCode.MESH_QA_FAILED)]
    )
    b = MockBlenderWorker(seed=1, scratch_dir=tmp_path, failure_plan=blender_plan).run(
        _blender_job()
    )
    assert b.status is BlenderJobStatus.FAILED
    assert b.error is not None and b.error.code is ErrorCode.MESH_QA_FAILED
    assert b.geomBytesRef is None and b.gateMetrics is None

    export_plan = FailurePlan(
        rules=[
            FailureRule(operation=MockOp.EXPORT_RUN, at_call=1, code=ErrorCode.DBPF_WRITE_FAILED)
        ]
    )
    e = MockExportWorker(seed=1, scratch_dir=tmp_path, failure_plan=export_plan).run(_export_job())
    assert e.status is ExportJobStatus.FAILED
    assert e.error is not None and e.error.code is ErrorCode.DBPF_WRITE_FAILED
    assert e.packagePath is None


def test_mock_factory_seam_resolves_by_name(tmp_path: Path) -> None:
    """spec(§7, fp-2) — the package exposes a thin name→constructor seam Phase-2 selects through;
    no concrete mock is hard-wired and nothing self-registers on import."""
    from adapters.mock import MOCK_PROVIDERS, MOCK_WORKERS, MockExportWorker, MockImage3DProvider

    assert MOCK_PROVIDERS["image3d"] is MockImage3DProvider
    assert MOCK_WORKERS["export"] is MockExportWorker

    provider = MOCK_PROVIDERS["image3d"](seed=1, scratch_dir=tmp_path)
    assert provider.submit(b"x", {}).jobId  # constructible + usable through the seam
