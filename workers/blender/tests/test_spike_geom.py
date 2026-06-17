"""RED tests for the §8/§9 Blender-CLI orchestration harness (S1a) — `spike_geom.py`.

§8: production GEOM path is the ``blender --background --factory-startup --python`` CLI subprocess;
the ``BlenderJob`` → ``BlenderReport`` job-file/result-file envelope; the §17 hang-watchdog
(wall-clock deadline → kill + retry-once → structured error). The real subprocess is kept out of the
test path behind an injected ``Runner`` seam; tests inject fakes (success / failure / timeout).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from aisims_contracts.error import ErrorCode
from aisims_contracts.workers import BBox, BlenderJob, BlenderJobStatus

from spike_geom import RunResult, build_blender_command, run_geom_spike

_GATE = {
    "normals": True,
    "uv": True,
    "lods": 4,
    "polyByTile": {"LOD0": 1800},
    "meshgroups": 1,
}


def _job(tmp_path: Path, job_id: str = "job-1") -> BlenderJob:
    return BlenderJob(
        meshPath=str(tmp_path / "mesh.obj"),
        params={},
        donorBBox=BBox(minCorner=(0.0, 0.0, 0.0), maxCorner=(1.0, 1.0, 1.0)),
        jobId=job_id,
    )


def _write_result(scratch: Path, job_id: str, payload: dict[str, object]) -> None:
    (scratch / f"{job_id}.result.json").write_text(json.dumps(payload))


class _SuccessRunner:
    """Writes a success result-file (+ the GEOM bytes) under scratch, like the real worker would."""

    def __init__(self, scratch: Path, job_id: str, geom_bytes: bytes) -> None:
        self._scratch = scratch
        self._job_id = job_id
        self._geom = geom_bytes
        self.calls = 0

    def run(self, cmd: list[str], deadline_s: float) -> RunResult:
        self.calls += 1
        geom_path = self._scratch / f"{self._job_id}.geom"
        geom_path.write_bytes(self._geom)
        _write_result(
            self._scratch,
            self._job_id,
            {
                "status": "succeeded",
                "geomBytesRef": str(geom_path),
                "gateMetrics": _GATE,
                "previewRef": None,
            },
        )
        return RunResult(timed_out=False, returncode=0)


class _FailureRunner:
    def __init__(self, scratch: Path, job_id: str) -> None:
        self._scratch = scratch
        self._job_id = job_id
        self.calls = 0

    def run(self, cmd: list[str], deadline_s: float) -> RunResult:
        self.calls += 1
        _write_result(
            self._scratch,
            self._job_id,
            {
                "status": "failed",
                "error": {
                    "code": "GEOM_EXPORT_FAILED",
                    "category": "geometry",
                    "retryable": False,
                    "creatorMessage": "Blender could not export the mesh.",
                    "maintainerDetail": "bpy GEOM exporter raised on the donor topology",
                },
            },
        )
        return RunResult(timed_out=False, returncode=1)


class _TimeoutRunner:
    """Always reports a watchdog kill (never writes a result-file)."""

    def __init__(self) -> None:
        self.calls = 0

    def run(self, cmd: list[str], deadline_s: float) -> RunResult:
        self.calls += 1
        return RunResult(timed_out=True, returncode=-1)


def test_build_blender_command_shape() -> None:
    # spec(§8): the production path is `blender --background --factory-startup --python <script>`,
    # with the job-file passed after the `--` separator.
    cmd = build_blender_command("cli/geom_export.py", "scratch/job-1.job.json")
    assert cmd[:5] == [
        "blender",
        "--background",
        "--factory-startup",
        "--python",
        "cli/geom_export.py",
    ]
    assert "--" in cmd
    assert cmd[cmd.index("--") + 1] == "scratch/job-1.job.json"


def test_run_geom_spike_success_assembles_valid_report(tmp_path: Path) -> None:
    # spec(§8): success → a contract-valid BlenderReport (rule 6: succeeded ⟹ geomBytesRef +
    # gateMetrics present, error None), geomBytesRef inside the provided scratch dir.
    from tests.fixtures import make_geom_bytes

    job = _job(tmp_path)
    runner = _SuccessRunner(tmp_path, job.jobId, make_geom_bytes())
    report = run_geom_spike(job, runner, tmp_path, deadline_s=5.0)

    assert report.status is BlenderJobStatus.SUCCEEDED
    assert report.error is None
    assert report.gateMetrics is not None
    assert report.geomBytesRef is not None
    # The report carries the canonical, scratch-vetted path (not the raw worker string), so a
    # downstream §9 consumer re-resolves to the same target inside scratch (rule 3).
    assert Path(report.geomBytesRef).is_relative_to(tmp_path.resolve())
    assert Path(report.geomBytesRef) == (tmp_path / f"{job.jobId}.geom").resolve()


def test_run_geom_spike_failed_runner_yields_failed_report(tmp_path: Path) -> None:
    # spec(§8): a worker failure → BlenderReport(status=failed, error=<ErrorEnvelope>), no
    # geomBytesRef.
    job = _job(tmp_path)
    report = run_geom_spike(job, _FailureRunner(tmp_path, job.jobId), tmp_path, deadline_s=5.0)

    assert report.status is BlenderJobStatus.FAILED
    assert report.error is not None
    assert report.geomBytesRef is None


def test_run_geom_spike_watchdog_retries_once_then_fails(tmp_path: Path) -> None:
    # spec(§8): §17 hang-watchdog — a deadline breach is killed + retried exactly once; a second
    # breach returns failed + structured ErrorEnvelope, never a raise / half-result.
    job = _job(tmp_path)
    runner = _TimeoutRunner()
    report = run_geom_spike(job, runner, tmp_path, deadline_s=0.01)

    assert runner.calls == 2
    assert report.status is BlenderJobStatus.FAILED
    assert report.error is not None
    assert report.geomBytesRef is None
    # maintainerDetail distinguishes a wall-clock deadline breach from a malformed-mesh failure
    # (same coarse code GEOM_EXPORT_FAILED; nuance rides in maintainerDetail, per orch note 1).
    assert "deadline" in report.error.maintainerDetail.lower()


@pytest.mark.parametrize(("valid_geom", "expected"), [(True, "succeeded"), (False, "failed")])
def test_run_geom_spike_validates_emitted_geom(
    tmp_path: Path, valid_geom: bool, expected: str
) -> None:
    # spec(§8): the GEOM stage gates before packaging — a structurally invalid emitted GEOM
    # downgrades the report to failed; a valid one stays succeeded.
    from tests.fixtures import make_geom_bytes

    job = _job(tmp_path)
    geom_bytes = make_geom_bytes() if valid_geom else make_geom_bytes(magic=b"NOPE")
    report = run_geom_spike(
        job, _SuccessRunner(tmp_path, job.jobId, geom_bytes), tmp_path, deadline_s=5.0
    )

    assert report.status.value == expected


def test_run_geom_spike_rejects_geomref_outside_scratch(tmp_path: Path) -> None:
    # spec(§8) / safety rule 3: a geomBytesRef escaping the provided scratch dir is refused (the
    # worker writes ONLY under sidecar scratch) → failed, the out-of-scratch bytes are never read.
    job = _job(tmp_path)
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    outside = tmp_path / "outside.geom"

    from tests.fixtures import make_geom_bytes

    outside.write_bytes(make_geom_bytes())

    class _EscapeRunner:
        calls = 0

        def run(self, cmd: list[str], deadline_s: float) -> RunResult:
            self.calls += 1
            _write_result(
                scratch,
                job.jobId,
                {"status": "succeeded", "geomBytesRef": str(outside), "gateMetrics": _GATE},
            )
            return RunResult(timed_out=False, returncode=0)

    report = run_geom_spike(job, _EscapeRunner(), scratch, deadline_s=5.0)
    assert report.status is BlenderJobStatus.FAILED
    assert report.error is not None


def test_run_geom_spike_failed_without_error_synthesizes_envelope(tmp_path: Path) -> None:
    # spec(§8) / rule 6: a status=failed result-file with no valid ErrorEnvelope still degrades to a
    # failed report with a synthesized envelope — never a raise, never a succeeded report.
    job = _job(tmp_path)

    class _BadFailureRunner:
        def run(self, cmd: list[str], deadline_s: float) -> RunResult:
            _write_result(tmp_path, job.jobId, {"status": "failed"})  # no `error` key
            return RunResult(timed_out=False, returncode=1)

    report = run_geom_spike(job, _BadFailureRunner(), tmp_path, deadline_s=5.0)
    assert report.status is BlenderJobStatus.FAILED
    assert report.error is not None
    assert report.error.code is ErrorCode.GEOM_EXPORT_FAILED


def test_run_geom_spike_rejects_oversized_geom(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # spec(§8) / rule 6: a worker-controlled GEOM above the size cap is refused BEFORE it's read
    # into memory (OOM guard) → failed, not succeeded.
    monkeypatch.setattr("spike_geom._MAX_GEOM_BYTES", 8)
    from tests.fixtures import make_geom_bytes

    job = _job(tmp_path)
    runner = _SuccessRunner(tmp_path, job.jobId, make_geom_bytes())  # 44 bytes > 8-byte cap
    report = run_geom_spike(job, runner, tmp_path, deadline_s=5.0)

    assert report.status is BlenderJobStatus.FAILED
    assert report.error is not None
    assert "cap" in report.error.maintainerDetail.lower()
