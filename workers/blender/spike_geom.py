"""S1a spike — the §8/§9 Blender-CLI GEOM orchestration harness (headless-testable core).

Builds the production ``blender --background --factory-startup --python`` invocation, runs it via an
*injected* :class:`Runner` seam (the real subprocess stays out of the test path until env-ready),
assembles a contract-valid :class:`~aisims_contracts.workers.BlenderReport` from the worker's
result-file, and applies the §8 / §17 hang-watchdog (wall-clock deadline → kill + retry-once →
structured :class:`~aisims_contracts.error.ErrorEnvelope`). Reuses the frozen ``aisims_contracts``
worker models unchanged (safety rule 6: status↔outputs consistency is enforced by their
``model_validator``).

**Scratch-only (safety rule 3).** Every path this harness touches (job-file, result-file, GEOM
bytes) is under the sidecar-provided scratch dir; a ``geomBytesRef`` escaping scratch is refused and
its bytes are never read. This worker writes neither Postgres nor the canonical tree (rule 3).

**Env-ready (NOT this slice).** The real ``blender --background`` GEOM emission + the in-game
verdict run once Blender 5.1.x lands; :class:`_SubprocessRunner` + :func:`_run_cli` are the entry
point the env-ready probe invokes. Headless tests inject fake runners instead.
"""

from __future__ import annotations

import json
import subprocess
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from aisims_contracts.workers import BlenderJob, BlenderJobStatus, BlenderReport, GateMetrics
from pydantic import ValidationError

from geom.structural import validate_geom_structure

_DEFAULT_DEADLINE_S: float = 600.0
# The env-ready bpy script `blender --background` runs (lands with Blender 5.1.x provisioning).
_DEFAULT_SCRIPT = "cli/geom_export.py"
_MAX_RETRIES = 1
# Reject a worker-controlled GEOM file larger than this before reading it into memory (the §8 fast
# check only needs the header + declared body; an oversized .geom is a malformed-worker signal, not
# a valid mesh). Guards the harness against an OOM from an untrusted in-scratch file.
_MAX_GEOM_BYTES = 256 * 1024 * 1024


@dataclass(frozen=True, slots=True)
class RunResult:
    """A single Runner invocation outcome. ``timed_out`` is the §17 watchdog signal (the deadline
    was hit and the process tree killed); ``returncode`` is the process exit status otherwise."""

    timed_out: bool
    returncode: int


class Runner(Protocol):
    """The subprocess seam. Production wraps ``blender --background`` (env-ready); tests inject
    fakes. The implementation owns the wall-clock kill; the harness owns the retry policy."""

    def run(self, cmd: list[str], deadline_s: float) -> RunResult: ...


def build_blender_command(script: str, jobfile: str) -> list[str]:
    """The §8 production invocation: ``--factory-startup`` isolation + the job-file after ``--``."""
    return ["blender", "--background", "--factory-startup", "--python", script, "--", jobfile]


def run_geom_spike(
    job: BlenderJob,
    runner: Runner,
    scratch_dir: Path,
    deadline_s: float = _DEFAULT_DEADLINE_S,
    *,
    script: str = _DEFAULT_SCRIPT,
    max_retries: int = _MAX_RETRIES,
) -> BlenderReport:
    """Run the GEOM spike: serialize the job into scratch, invoke the runner under the §17 watchdog
    (kill + retry-once on a deadline breach), validate the emitted GEOM, and assemble a
    contract-valid BlenderReport. Never raises on a worker fault — it becomes
    ``BlenderReport(status=failed, error=<ErrorEnvelope>)``."""
    scratch_dir.mkdir(parents=True, exist_ok=True)
    jobfile = scratch_dir / f"{job.jobId}.job.json"
    jobfile.write_text(job.model_dump_json())
    cmd = build_blender_command(script, str(jobfile))

    timed_out = True
    for _ in range(max_retries + 1):
        outcome = runner.run(cmd, deadline_s)
        if not outcome.timed_out:
            timed_out = False
            break
    if timed_out:
        return _failed(
            f"blender GEOM job exceeded the {deadline_s}s wall-clock deadline; killed and "
            f"retried {max_retries}x (§17 watchdog)",
            creator="The mesh export timed out.",
        )

    return _assemble_report(job, scratch_dir)


def _assemble_report(job: BlenderJob, scratch_dir: Path) -> BlenderReport:
    """Read the worker's result-file from scratch and map it onto a contract-valid BlenderReport,
    gating on the §8 structural GEOM check before declaring success."""
    result_file = scratch_dir / f"{job.jobId}.result.json"
    if not result_file.exists():
        return _failed("worker produced no result-file")
    try:
        raw = json.loads(result_file.read_text())
    except (ValueError, OSError) as exc:
        return _failed(f"unreadable result-file: {exc!r}")
    if not isinstance(raw, dict):
        return _failed("result-file is not a JSON object")

    status = raw.get("status")
    if status == BlenderJobStatus.FAILED.value:
        return _worker_failure(raw)
    if status != BlenderJobStatus.SUCCEEDED.value:
        return _failed(f"unknown worker status {status!r}")

    geom_ref = raw.get("geomBytesRef")
    if not isinstance(geom_ref, str) or not geom_ref:
        return _failed("succeeded result-file missing geomBytesRef")
    resolved = _resolve_within_scratch(scratch_dir, geom_ref)
    if resolved is None or not resolved.exists():
        return _failed(f"geomBytesRef escapes scratch or is missing: {geom_ref}")
    geom_size = resolved.stat().st_size
    if geom_size > _MAX_GEOM_BYTES:
        return _failed(f"emitted GEOM exceeds the {_MAX_GEOM_BYTES}-byte cap: {geom_size}")
    struct_res = validate_geom_structure(resolved.read_bytes())
    if not struct_res.ok:
        kinds = ", ".join(issue.kind for issue in struct_res.issues)
        return _failed(f"emitted GEOM failed the §8 structural check: {kinds}")

    gate_raw = raw.get("gateMetrics")
    if not isinstance(gate_raw, dict):
        return _failed("succeeded result-file missing gateMetrics")
    try:
        gate = GateMetrics.model_validate(gate_raw)
    except ValidationError as exc:
        return _failed(f"invalid gateMetrics: {exc}")

    # Persist the canonical, scratch-vetted path (not the raw worker string) so a downstream §9
    # consumer re-resolves to the same vetted target (rule 3). previewRef is non-core: route it
    # through the same scratch guard and drop it to None on escape rather than failing the report.
    preview = raw.get("previewRef")
    preview_ref = None
    if isinstance(preview, str) and preview:
        preview_resolved = _resolve_within_scratch(scratch_dir, preview)
        preview_ref = str(preview_resolved) if preview_resolved is not None else None
    return BlenderReport(
        status=BlenderJobStatus.SUCCEEDED,
        geomBytesRef=str(resolved),
        gateMetrics=gate,
        previewRef=preview_ref,
    )


def _worker_failure(raw: dict[str, Any]) -> BlenderReport:
    """Map a ``status=failed`` result-file onto a BlenderReport, preferring the worker's own
    ErrorEnvelope and synthesizing one if it's absent or malformed."""
    err_raw = raw.get("error")
    if isinstance(err_raw, dict):
        try:
            return BlenderReport(
                status=BlenderJobStatus.FAILED, error=ErrorEnvelope.model_validate(err_raw)
            )
        except ValidationError:
            pass
    return _failed("worker reported failure without a valid ErrorEnvelope")


def _failed(
    detail: str,
    *,
    creator: str = "The mesh export failed.",
    code: ErrorCode = ErrorCode.GEOM_EXPORT_FAILED,
    category: ErrorCategory = ErrorCategory.GEOMETRY,
    retryable: bool = False,
) -> BlenderReport:
    """Build a failed BlenderReport. ``GEOM_EXPORT_FAILED`` is the coarse per-stage code for every
    GEOM-stage fault (timeout / worker-failure / invalid-GEOM); the specific cause rides in
    ``maintainerDetail`` (the redaction-egress surface, §16)."""
    return BlenderReport(
        status=BlenderJobStatus.FAILED,
        error=ErrorEnvelope(
            code=code,
            category=category,
            retryable=retryable,
            creatorMessage=creator,
            maintainerDetail=detail,
        ),
    )


def _resolve_within_scratch(scratch_dir: Path, ref: str) -> Path | None:
    """Resolve ``ref`` and confirm it lies inside ``scratch_dir`` (safety rule 3 scratch-only).
    Returns the resolved path, or ``None`` if it escapes scratch or can't be resolved."""
    try:
        resolved = Path(ref).resolve()
        resolved.relative_to(scratch_dir.resolve())
    except (ValueError, OSError):
        return None
    return resolved


class _SubprocessRunner:  # pragma: no cover - exercised only at env-ready (real Blender)
    """Production runner — wraps the ``blender --background`` subprocess with the §17 wall-clock
    watchdog. Its actual Blender invocation runs only at env-ready (Blender 5.1.x); full
    process-tree kill is an env-ready hardening detail. Headless tests inject fakes instead."""

    def run(self, cmd: list[str], deadline_s: float) -> RunResult:
        try:
            proc = subprocess.run(cmd, timeout=deadline_s, check=False)
        except subprocess.TimeoutExpired:
            return RunResult(timed_out=True, returncode=-1)
        return RunResult(timed_out=False, returncode=proc.returncode)


def _run_cli(argv: Sequence[str]) -> int:  # pragma: no cover - env-ready probe entry point
    """Env-ready probe entry: read a job-file path → run the spike → write the result/report file.
    This is what the S1a env-ready real-Blender probe and S1c's test-install consume."""
    if len(argv) < 2:
        return 2
    jobfile = Path(argv[1])
    scratch = jobfile.parent
    job = BlenderJob.model_validate_json(jobfile.read_text())
    report = run_geom_spike(job, _SubprocessRunner(), scratch)
    (scratch / f"{job.jobId}.report.json").write_text(report.model_dump_json())
    return 0 if report.status is BlenderJobStatus.SUCCEEDED else 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_run_cli(sys.argv))
