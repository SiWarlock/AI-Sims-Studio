"""§6 single-writer lock — one active project, owner-PID + heartbeat, dead-owner reclaim.

An on-disk lock carrying ``owner_pid`` + ``heartbeat`` + ``ttl``. **Phase-0 reclaim policy:** a LIVE
owner PID ALWAYS holds — a stale heartbeat alone is NOT grounds to reclaim, since the skeleton has
no fencing token and a GC/swap/debugger stall could starve a live owner's heartbeat (reclaiming it
would risk two live writers against one store). Only a DEAD owner PID is reclaimable. The heartbeat
is retained in metadata for PID-reuse disambiguation + the Phase-2 hung-owner+fencing story.
Complements 0.7's ``open_store`` version-stamp/compat-check (it does not duplicate that logic).
"""

from __future__ import annotations

import os
import time
from collections.abc import Callable
from pathlib import Path

from pydantic import BaseModel, ConfigDict


def _default_pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists but not signalable by us
    return True


class LockMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_pid: int
    heartbeat: float
    ttl: float


class SingleWriterLock:
    def __init__(
        self,
        lock_path: Path,
        *,
        pid: int | None = None,
        ttl: float = 30.0,
        clock: Callable[[], float] = time.time,
        pid_alive: Callable[[int], bool] = _default_pid_alive,
    ) -> None:
        self._path = lock_path
        self._pid = pid if pid is not None else os.getpid()
        self._ttl = ttl
        self._clock = clock
        self._pid_alive = pid_alive

    def _read(self) -> LockMetadata | None:
        if not self._path.exists():
            return None
        return LockMetadata.model_validate_json(self._path.read_text())

    def _write(self) -> None:
        meta = LockMetadata(owner_pid=self._pid, heartbeat=self._clock(), ttl=self._ttl)
        self._path.write_text(meta.model_dump_json())

    def acquire(self) -> bool:
        """Acquire (or reclaim a DEAD owner's lock). Returns False while a LIVE owner holds it.

        Phase-0 limitation: this read-then-write is NOT atomic against a concurrent first-acquire /
        reclaim (no OS-level atomic-create / fencing token yet — that lands with the Phase-2 fencing
        story). The single-operator Phase-0 posture makes the race non-impacting; the live-owner
        guard below still prevents two LIVE writers.
        """
        existing = self._read()
        if existing is not None and self._pid_alive(existing.owner_pid):
            return False
        self._write()
        return True

    def release(self) -> None:
        existing = self._read()
        if existing is not None and existing.owner_pid == self._pid:
            self._path.unlink(
                missing_ok=True
            )  # idempotent: a concurrent reclaim may have removed it
