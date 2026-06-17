"""§8/§9 mock worker executors — Blender (mesh/GEOM) + export (DBPF).

Each executor builds its report THROUGH the frozen model (BlenderReport / ExportJobReport), so the
status↔outputs ``model_validator`` (rule 6) is what enforces consistency — a malformed
status/outputs combo can't be produced. Outputs are scratch-path refs the mock writes under the
sidecar-provided scratch dir ONLY (rule 3 / fp-4); failures are injected via a ``FailurePlan``.
"""

from __future__ import annotations

import random
from pathlib import Path

from aisims_contracts.error import ErrorCode
from aisims_contracts.workers import (
    BlenderJob,
    BlenderJobStatus,
    BlenderReport,
    ExportJob,
    ExportJobReport,
    ExportJobStatus,
    GateMetrics,
)

from .failure import FailurePlan, MockOp, envelope_for


class MockBlenderWorker:
    """Mock §8 Blender executor: BlenderJob → BlenderReport."""

    def __init__(
        self, *, seed: int = 0, scratch_dir: Path, failure_plan: FailurePlan | None = None
    ) -> None:
        self._rng = random.Random(seed)
        self._scratch_dir = scratch_dir
        self._plan = failure_plan or FailurePlan()
        self._run_count = 0

    def run(self, job: BlenderJob) -> BlenderReport:
        self._run_count += 1
        injected = self._plan.match(MockOp.BLENDER_RUN, self._run_count)
        if injected is not None:
            return BlenderReport(status=BlenderJobStatus.FAILED, error=envelope_for(injected))

        self._scratch_dir.mkdir(parents=True, exist_ok=True)
        geom = self._scratch_dir / f"{job.jobId}.geom"
        geom.write_bytes(b"mock-geom-bytes")
        metrics = GateMetrics(normals=True, uv=True, lods=2, polyByTile={"0": 1800}, meshgroups=1)
        return BlenderReport(
            status=BlenderJobStatus.SUCCEEDED, geomBytesRef=str(geom), gateMetrics=metrics
        )


class MockExportWorker:
    """Mock §9 export executor: ExportJob → ExportJobReport (success / partial / failed)."""

    def __init__(
        self,
        *,
        seed: int = 0,
        scratch_dir: Path,
        failure_plan: FailurePlan | None = None,
        partial: bool = False,
    ) -> None:
        self._rng = random.Random(seed)
        self._scratch_dir = scratch_dir
        self._plan = failure_plan or FailurePlan()
        self._partial = partial
        self._run_count = 0

    def run(self, job: ExportJob) -> ExportJobReport:
        self._run_count += 1
        injected = self._plan.match(MockOp.EXPORT_RUN, self._run_count)
        if injected is not None:
            return ExportJobReport(status=ExportJobStatus.FAILED, error=envelope_for(injected))

        self._scratch_dir.mkdir(parents=True, exist_ok=True)
        package = self._scratch_dir / f"{job.jobId}.package"
        package.write_bytes(b"mock-dbpf-bytes")
        if self._partial:
            return ExportJobReport(
                status=ExportJobStatus.PARTIAL,
                packagePath=str(package),
                includedItems=[job.jobId],
                error=envelope_for(ErrorCode.GEOM_EXPORT_FAILED),
            )
        return ExportJobReport(
            status=ExportJobStatus.SUCCEEDED, packagePath=str(package), includedItems=[job.jobId]
        )
