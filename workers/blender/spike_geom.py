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
import os
import signal
import subprocess
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from aisims_contracts.workers import BlenderJob, BlenderJobStatus, BlenderReport, GateMetrics
from pydantic import ValidationError

from geom.real_geom import validate_real_geom
from geom.structural import GeomStructResult, validate_geom_structure

# The structural-GEOM validator seam: the spike default is the placeholder parser; the env-ready
# path (real Blender output) injects the real-format `validate_real_geom`.
GeomValidator = Callable[[bytes], GeomStructResult]

_DEFAULT_DEADLINE_S: float = 600.0
# The bpy GEOM-emission script `blender --background` runs. Lives in `blender_scripts/` (the bpy-
# runtime-script home) — it runs under Blender's bundled Python, not the worker uv env, so it is NOT
# part of the worker import graph (and is mypy-excluded).
_DEFAULT_SCRIPT = "blender_scripts/geom_export.py"
_MAX_RETRIES = 1
# `blender` is not on PATH on this Apple-Silicon Mac; the app-bundle binary is the fallback.
# SPIKE convenience only — machine-specific; Phase-4 productionization replaces it with real config.
_MAC_APP_BIN: Final = Path("/Applications/Blender.app/Contents/MacOS/Blender")
_BLENDER_BIN_ENV: Final = "AISIMS_BLENDER_BIN"
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


def build_blender_command(script: str, jobfile: str, *, blender_exe: str = "blender") -> list[str]:
    """The §8 production invocation: the (configurable) Blender executable + ``--factory-startup``
    isolation + the job-file after ``--``. ``blender_exe`` defaults to ``"blender"``; the real
    runner overrides it — see :func:`_resolve_blender_exe`."""
    return [blender_exe, "--background", "--factory-startup", "--python", script, "--", jobfile]


def _resolve_blender_exe(app_fallback: Path = _MAC_APP_BIN) -> str:
    """Resolve the Blender executable with explicit precedence: the ``AISIMS_BLENDER_BIN`` env var
    wins over the app-bundle fallback wins over a bare ``"blender"`` on PATH. The fallback never
    masks an explicit override (so a misconfigured machine fails loudly, not silently wrong)."""
    env = os.environ.get(_BLENDER_BIN_ENV)
    if env:
        return env
    if app_fallback.exists():
        return str(app_fallback)
    return "blender"


def run_geom_spike(
    job: BlenderJob,
    runner: Runner,
    scratch_dir: Path,
    deadline_s: float = _DEFAULT_DEADLINE_S,
    *,
    script: str = _DEFAULT_SCRIPT,
    max_retries: int = _MAX_RETRIES,
    validator: GeomValidator = validate_geom_structure,
) -> BlenderReport:
    """Run the GEOM spike: serialize the job into scratch, invoke the runner under the §17 watchdog
    (kill + retry-once on a deadline breach), validate the emitted GEOM, and assemble a
    contract-valid BlenderReport. Never raises on a worker fault — it becomes
    ``BlenderReport(status=failed, error=<ErrorEnvelope>)``."""
    scratch_dir.mkdir(parents=True, exist_ok=True)
    jobfile = scratch_dir / f"{job.jobId}.job.json"
    jobfile.write_text(job.model_dump_json())
    cmd = build_blender_command(script, str(jobfile), blender_exe=_resolve_blender_exe())

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

    return _assemble_report(job, scratch_dir, validator)


def _assemble_report(job: BlenderJob, scratch_dir: Path, validator: GeomValidator) -> BlenderReport:
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
    struct_res = validator(resolved.read_bytes())
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


class _SubprocessRunner:
    """Production runner — runs the (resolved) ``blender --background`` subprocess and enforces the
    §17 wall-clock watchdog with a process-**tree** kill: ``start_new_session=True`` makes the child
    lead a fresh process group, so on a deadline breach one ``killpg`` reaps Blender + any
    grandchildren it spawned (not just the direct child). Tests drive it with non-Blender commands;
    the real Blender invocation is the env-ready probe path."""

    def run(self, cmd: list[str], deadline_s: float) -> RunResult:
        proc = subprocess.Popen(cmd, start_new_session=True)
        try:
            proc.wait(timeout=deadline_s)
        except subprocess.TimeoutExpired:
            self._kill_tree(proc)
            return RunResult(timed_out=True, returncode=-1)
        return RunResult(timed_out=False, returncode=proc.returncode)

    @staticmethod
    def _kill_tree(proc: subprocess.Popen[bytes]) -> None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            proc.kill()  # fall back to a direct-child kill if the group is already gone
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            pass


def run_geom_spike_from_jobfile(
    jobfile: Path,
    runner: Runner,
    scratch_dir: Path | None = None,
    deadline_s: float = _DEFAULT_DEADLINE_S,
) -> BlenderReport:
    """Read + validate an inbound job-file, then run the spike — **fail-closed**: a missing /
    unreadable / malformed job-file (bad JSON or failing ``BlenderJob`` validation) returns a failed
    ``BlenderReport`` and never spawns a subprocess (rule-6 inbound validation before any state
    change). ``scratch_dir`` defaults to the job-file's parent dir."""
    scratch = scratch_dir if scratch_dir is not None else jobfile.parent
    try:
        job = BlenderJob.model_validate_json(jobfile.read_text())
    except (OSError, ValueError, ValidationError) as exc:
        return _failed(
            f"unreadable / malformed inbound job-file {jobfile}: {exc!r}",
            creator="The mesh export job could not be read.",
        )
    # The env-ready entry runs real Blender → validate emitted bytes with the REAL-format parser.
    return run_geom_spike(job, runner, scratch, deadline_s, validator=validate_real_geom)


def _run_cli(argv: Sequence[str]) -> int:  # pragma: no cover - env-ready probe entry point
    """Env-ready probe entry: read a job-file path → run the spike (fail-closed) → write the report.
    This is what the S1a env-ready real-Blender probe and S1c's test-install consume."""
    if len(argv) < 2:
        return 2
    jobfile = Path(argv[1])
    report = run_geom_spike_from_jobfile(jobfile, _SubprocessRunner(), jobfile.parent)
    (jobfile.parent / f"{jobfile.stem}.report.json").write_text(report.model_dump_json())
    return 0 if report.status is BlenderJobStatus.SUCCEEDED else 1


if __name__ == "__main__":  # pragma: no cover
    import sys

    raise SystemExit(_run_cli(sys.argv))
