"""RED tests for the S1a env-ready hardening — fail-closed job-file + process-tree kill.

Folds the spikes-001 carry-forwards: (a) the `_run_cli`/`__main__` probe entry must FAIL-CLOSED on a
malformed/missing inbound job-file (structured failure, never a raise — rule 6 inbound validation);
(b) `_SubprocessRunner` must kill the process TREE on a deadline breach (Blender spawns
grandchildren), not just the direct child.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from aisims_contracts.workers import BlenderJobStatus

from spike_geom import (
    RunResult,
    _resolve_blender_exe,
    _SubprocessRunner,
    build_blender_command,
    run_geom_spike_from_jobfile,
)

_APP_BIN = "/Applications/Blender.app/Contents/MacOS/Blender"


class _NeverRunner:
    """A runner that must never be reached when the inbound job-file is invalid."""

    def __init__(self) -> None:
        self.calls = 0

    def run(self, cmd: list[str], deadline_s: float) -> RunResult:
        self.calls += 1
        return RunResult(timed_out=False, returncode=0)


def test_build_blender_command_uses_configured_executable() -> None:
    # spec(§8): `blender` is not on PATH; build_blender_command must emit the configured exe as
    # argv[0], with the default staying "blender" (the implementer's PATH catch).
    assert build_blender_command("blender_scripts/geom_export.py", "j.json")[0] == "blender"
    configured = build_blender_command(
        "blender_scripts/geom_export.py", "j.json", blender_exe=_APP_BIN
    )
    assert configured[0] == _APP_BIN
    assert configured[1:4] == ["--background", "--factory-startup", "--python"]


def test_resolve_blender_exe_precedence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # spec(§8): explicit env AISIMS_BLENDER_BIN beats the .app fallback beats "blender"; the
    # fallback (machine-specific, a spike convenience) must never mask an explicit override.
    existing = tmp_path / "Blender"
    existing.write_text("")
    missing = tmp_path / "nope"

    monkeypatch.setenv("AISIMS_BLENDER_BIN", "/custom/blender")
    assert _resolve_blender_exe(existing) == "/custom/blender"  # 1. env wins, even over a real .app

    monkeypatch.delenv("AISIMS_BLENDER_BIN", raising=False)
    assert _resolve_blender_exe(existing) == str(existing)  # 2. no env → .app fallback if present
    assert _resolve_blender_exe(missing) == "blender"  # 3. no env, no .app → "blender"


def test_run_cli_fail_closed_on_missing_jobfile(tmp_path: Path) -> None:
    # spec(§8) / rule 6: a missing job-file → a failed BlenderReport, never a raise; the subprocess
    # spawn is never reached.
    runner = _NeverRunner()
    report = run_geom_spike_from_jobfile(tmp_path / "nope.json", runner, tmp_path)
    assert report.status is BlenderJobStatus.FAILED
    assert report.error is not None
    assert runner.calls == 0


def test_run_cli_fail_closed_on_malformed_jobfile(tmp_path: Path) -> None:
    # spec(§8) / rule 6: a job-file that isn't valid JSON / fails BlenderJob validation → failed, no
    # raise, no subprocess spawn.
    runner = _NeverRunner()
    bad = tmp_path / "bad.json"
    bad.write_text("{ not valid json")
    report = run_geom_spike_from_jobfile(bad, runner, tmp_path)
    assert report.status is BlenderJobStatus.FAILED
    assert report.error is not None
    assert runner.calls == 0


def test_subprocess_runner_tree_kill_on_deadline(tmp_path: Path) -> None:
    # spec(§8) / §17: on a deadline breach the process TREE is killed — a grandchild that outlives
    # the direct child is also reaped, not just the direct child. RED until _SubprocessRunner uses a
    # process-group kill (the spikes-001 carry-forward).
    started = tmp_path / "child_started"
    grandchild_alive = tmp_path / "grandchild_alive"
    # Timing: deadline 0.5s → kill fires with a ~2.5s margin before the grandchild's 3s sleep
    # would write its marker (robust to slow signal delivery); we then wait past 3s and assert the
    # marker is absent (i.e. the grandchild was killed mid-sleep, not just slow).
    child_src = (
        "import subprocess, sys, time\n"
        "open(sys.argv[1], 'w').close()\n"
        "gc = 'import sys, time; time.sleep(3.0); open(sys.argv[1], \"w\").close()'\n"
        "subprocess.Popen([sys.executable, '-c', gc, sys.argv[2]])\n"
        "time.sleep(30)\n"
    )
    cmd = [sys.executable, "-c", child_src, str(started), str(grandchild_alive)]

    result = _SubprocessRunner().run(cmd, deadline_s=0.5)

    assert result.timed_out is True
    assert started.exists()  # the child really ran
    time.sleep(4.0)  # wait past the grandchild's 3s sleep
    assert not grandchild_alive.exists()  # tree-killed: the grandchild never wrote its marker
