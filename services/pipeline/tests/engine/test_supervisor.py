"""RED — §6 supervisor (spawn/health/restart-backoff/teardown) + single-writer lock.

Driven against trivial stand-in subprocesses (per Q4) — NOT real Postgres/Blender/@s4tk. The lock
carries owner-PID + heartbeat (clock + pid-aliveness injected for determinism, per Q5).
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

SLEEP_CHILD = [sys.executable, "-c", "import time; time.sleep(30)"]
CRASH_CHILD = [sys.executable, "-c", "import sys; sys.exit(1)"]


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def test_supervisor_spawns_and_health_polls() -> None:
    """spec(§6) — spawn a stand-in child; health reports up while it runs, down after teardown."""
    from engine.supervisor import Supervisor

    sup = Supervisor(spawn_cmd=SLEEP_CHILD)
    sup.start()
    try:
        assert sup.is_healthy()
    finally:
        sup.teardown()
    assert not sup.is_healthy()


def test_supervisor_restart_with_backoff() -> None:
    """spec(§6) — a crashing child is restarted with capped deterministic backoff, then gives up."""
    from engine.supervisor import Supervisor, backoff_delays

    slept: list[float] = []
    sup = Supervisor(
        spawn_cmd=CRASH_CHILD,
        max_restarts=3,
        backoff_base=0.01,
        backoff_cap=0.05,
        sleep=slept.append,
    )
    outcome = sup.run_with_restarts()
    sup.teardown()

    assert outcome.gave_up is True
    assert outcome.restarts == 3
    assert slept == backoff_delays(3, base=0.01, cap=0.05)
    # capped, monotonic non-decreasing
    assert slept == sorted(slept) and max(slept) <= 0.05


def test_supervisor_gives_up_immediately_with_zero_restarts() -> None:
    """spec(§6) — max_restarts=0 ⟹ one start then immediate give-up; no backoff indexing."""
    from engine.supervisor import Supervisor

    slept: list[float] = []
    sup = Supervisor(spawn_cmd=CRASH_CHILD, max_restarts=0, sleep=slept.append)
    outcome = sup.run_with_restarts()
    sup.teardown()

    assert outcome.restarts == 0 and outcome.gave_up is True
    assert slept == []


def test_supervisor_process_tree_teardown(tmp_path: Path) -> None:
    """spec(§6) — teardown kills the child AND its grandchild (process-tree); no orphan process."""
    from engine.supervisor import Supervisor

    pidfile = tmp_path / "grandchild.pid"
    parent_cmd = [
        sys.executable,
        "-c",
        (
            "import subprocess, sys, time\n"
            "gc = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(30)'])\n"
            f"open({str(pidfile)!r}, 'w').write(str(gc.pid))\n"
            "time.sleep(30)\n"
        ),
    ]
    sup = Supervisor(spawn_cmd=parent_cmd)
    sup.start()
    try:
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            if pidfile.exists() and pidfile.read_text().strip():
                break
            time.sleep(0.05)
        assert pidfile.exists() and pidfile.read_text().strip(), "grandchild pidfile not written"
        grandchild_pid = int(pidfile.read_text().strip())
        child_pid = sup.child_pid()
        assert _alive(child_pid) and _alive(grandchild_pid)
    finally:
        sup.teardown()

    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline and (_alive(child_pid) or _alive(grandchild_pid)):
        time.sleep(0.05)
    assert not _alive(child_pid), "child orphaned after teardown"
    assert not _alive(grandchild_pid), "grandchild orphaned after teardown"


def test_single_writer_lock_acquire_and_contend(tmp_path: Path) -> None:
    """spec(§6) — the first acquire wins; a second acquire fails while a LIVE owner holds it."""
    from engine.lock import SingleWriterLock

    lock_path = tmp_path / "project.lock"
    now = [1000.0]
    holder = SingleWriterLock(
        lock_path, pid=111, ttl=30.0, clock=lambda: now[0], pid_alive=lambda p: True
    )
    assert holder.acquire() is True

    contender = SingleWriterLock(
        lock_path, pid=222, ttl=30.0, clock=lambda: now[0], pid_alive=lambda p: True
    )
    assert contender.acquire() is False  # owner 111 is alive + heartbeat fresh


def test_single_writer_lock_stale_reclaim(tmp_path: Path) -> None:
    """spec(§6) — a DEAD owner's lock is reclaimable on reopen (canonical stale case; the reclaim
    gate is the dead PID ALONE — the expired heartbeat here is incidental, not required)."""
    from engine.lock import SingleWriterLock

    lock_path = tmp_path / "project.lock"
    now = [1000.0]
    dead_owner = SingleWriterLock(
        lock_path, pid=999, ttl=30.0, clock=lambda: now[0], pid_alive=lambda p: True
    )
    assert dead_owner.acquire() is True  # 999 takes it at t=1000

    now[0] = 1100.0  # +100s: heartbeat now stale (> ttl)
    reclaimer = SingleWriterLock(
        lock_path, pid=222, ttl=30.0, clock=lambda: now[0], pid_alive=lambda p: p != 999
    )
    assert reclaimer.acquire() is True  # owner 999 DEAD → reclaimed (heartbeat also expired)


def test_single_writer_lock_live_owner_with_stale_heartbeat_not_reclaimed(tmp_path: Path) -> None:
    """spec(§6) — a LIVE owner holds even with a STALE heartbeat: Phase 0 has no fencing token, so a
    pid_alive owner is never reclaimed (a GC/swap stall must not yield two live writers)."""
    from engine.lock import SingleWriterLock

    lock_path = tmp_path / "project.lock"
    now = [1000.0]
    owner = SingleWriterLock(
        lock_path, pid=111, ttl=30.0, clock=lambda: now[0], pid_alive=lambda p: True
    )
    assert owner.acquire() is True  # heartbeat stamped at t=1000

    now[0] = 1100.0  # +100s: heartbeat is stale (> ttl) — but the owner PID is still alive
    contender = SingleWriterLock(
        lock_path, pid=222, ttl=30.0, clock=lambda: now[0], pid_alive=lambda p: True
    )
    assert contender.acquire() is False  # live owner holds DESPITE the stale heartbeat
