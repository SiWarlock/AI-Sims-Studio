"""§14 fail-open tracing seam.

A thin, backend-portable (Phoenix/Langfuse/LangSmith) tracing seam. ``emit`` enqueues onto an
unbounded background queue and returns immediately — it NEVER blocks or raises into the calling
path. A worker drains the queue and exports each span through the §16 redaction chokepoint, running
each export in a fresh daemon thread with a short timeout: a slow / hanging / erroring / offline
exporter is **dropped** (fail-open, rule 5) and the trace-loss counter is bumped — a generation run
is never stalled or failed by tracing.

Phase-0: the exporter is injected (no-op/mock); real LangSmith config is Phase-8. Bounding the queue
+ the in-flight export threads (sustained-hang accumulation) is a Phase-8 hardening.
"""

from __future__ import annotations

import queue
import threading
from typing import Any, Protocol

from .redaction import Redactor


class Exporter(Protocol):
    def export(self, span: dict[str, Any]) -> None: ...


class TracingSeam:
    def __init__(
        self,
        exporter: Exporter,
        *,
        redactor: Redactor,
        export_timeout: float = 0.1,
    ) -> None:
        self._exporter = exporter
        self._redactor = redactor
        self._timeout = export_timeout
        self._queue: queue.Queue[dict[str, Any]] = queue.Queue()  # unbounded (Phase 0)
        self._loss = 0
        self._loss_lock = threading.Lock()
        self._stop = threading.Event()
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()

    def emit(self, span: dict[str, Any]) -> None:
        """Enqueue a span. Non-blocking + non-raising: a hung exporter never stalls the caller."""
        self._queue.put_nowait(span)

    @property
    def trace_loss_count(self) -> int:
        with self._loss_lock:
            return self._loss

    def _bump_loss(self) -> None:
        with self._loss_lock:
            self._loss += 1

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                span = self._queue.get(timeout=0.05)
            except queue.Empty:
                continue
            self._export_one(span)
            self._queue.task_done()

    def _export_one(self, span: dict[str, Any]) -> None:
        redacted = self._redactor.redact_span(span)  # §16 egress redaction
        done = threading.Event()
        errored: list[bool] = []

        def _do() -> None:
            try:
                self._exporter.export(redacted)
            except Exception:
                errored.append(True)
            finally:
                done.set()

        threading.Thread(target=_do, daemon=True).start()
        if not done.wait(self._timeout) or errored:
            self._bump_loss()  # timed out (hang) OR exporter errored → fail-open drop

    def close(self, timeout: float = 2.0) -> None:
        # spans still queued at close are dropped silently (NOT counted) — fail-open by design.
        self._stop.set()
        self._worker.join(timeout)
