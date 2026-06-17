"""§6 supervisor (REQ-O-103) — free-port pick, spawn, health-poll, restart-with-backoff, teardown.

Phase-0 skeleton: drives a child subprocess (a trivial stand-in in tests, real
Postgres/sidecar/Blender/@s4tk in Phase 2). Children are spawned in a NEW SESSION so the whole
process tree (child + grandchildren) is torn down via the process group — no orphan processes/ports.
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass


def pick_free_port() -> int:
    """Bind an ephemeral port and return it (the kernel picks a free one)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port: int = sock.getsockname()[1]
    return port


def backoff_delays(max_attempts: int, *, base: float, cap: float) -> list[float]:
    """Capped exponential backoff schedule: ``min(cap, base * 2**i)`` for each attempt."""
    return [min(cap, base * (2**i)) for i in range(max_attempts)]


@dataclass
class SupervisionOutcome:
    restarts: int
    gave_up: bool


class Supervisor:
    def __init__(
        self,
        *,
        spawn_cmd: Sequence[str],
        health_check: Callable[[], bool] | None = None,
        max_restarts: int = 3,
        backoff_base: float = 0.1,
        backoff_cap: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._cmd = list(spawn_cmd)
        self._health_check = health_check
        self._max_restarts = max_restarts
        self._delays = backoff_delays(max_restarts, base=backoff_base, cap=backoff_cap)
        self._sleep = sleep
        self._proc: subprocess.Popen[bytes] | None = None

    def start(self) -> None:
        # Precondition: no live child (run_with_restarts waits before each restart). Calling start()
        # while a child is running would orphan it — not guarded in Phase 0.
        self._proc = subprocess.Popen(self._cmd, start_new_session=True)

    def child_pid(self) -> int:
        if self._proc is None:
            raise RuntimeError("supervisor not started")
        return self._proc.pid

    def is_healthy(self) -> bool:
        if self._proc is None or self._proc.poll() is not None:
            return False
        return self._health_check() if self._health_check is not None else True

    def run_with_restarts(self) -> SupervisionOutcome:
        """Watch the child; restart with capped backoff up to ``max_restarts``, then give up."""
        if self._proc is None:
            self.start()
        restarts = 0
        while True:
            assert self._proc is not None
            self._proc.wait()
            if restarts >= self._max_restarts:
                return SupervisionOutcome(restarts=restarts, gave_up=True)
            self._sleep(self._delays[restarts])
            restarts += 1
            self.start()

    def teardown(self) -> None:
        """Kill the child's whole process group (child + grandchildren); no orphans."""
        if self._proc is None:
            return
        try:
            os.killpg(os.getpgid(self._proc.pid), signal.SIGKILL)
        except ProcessLookupError:
            pass  # already gone
        self._proc.wait()
        self._proc = None
