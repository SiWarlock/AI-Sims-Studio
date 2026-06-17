"""RED — §14 fail-open tracing seam.

The seam exports via a background queue with a short per-export timeout: a slow / hanging /
erroring / offline exporter NEVER stalls or raises into the calling path (fail-open, rule 5). Every
drop bumps a trace-loss counter. Egress passes through the §16 redaction chokepoint first.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any


def _wait_until(predicate: Callable[[], bool], timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.02)
    return predicate()


class _HangingExporter:
    def __init__(self) -> None:
        self._never = threading.Event()  # never set → export blocks forever

    def export(self, span: dict[str, Any]) -> None:
        self._never.wait()


class _ErroringExporter:
    def export(self, span: dict[str, Any]) -> None:
        raise RuntimeError("exporter offline")


class _RecordingExporter:
    def __init__(self) -> None:
        self.received: list[dict[str, Any]] = []

    def export(self, span: dict[str, Any]) -> None:
        self.received.append(span)


def _redactor() -> Any:
    from obs.redaction import Redactor
    from obs.secrets import InMemorySecretsAccessor

    return Redactor(InMemorySecretsAccessor({"k": "sk-live-TRACESECRET"}))


def test_tracing_fail_open_on_hang() -> None:
    """spec(§14 / rule 5) — a hanging exporter never blocks/raises into the caller; the trace is
    dropped within the timeout."""
    from obs.tracing import TracingSeam

    seam = TracingSeam(_HangingExporter(), redactor=_redactor(), export_timeout=0.05)
    try:
        seam.emit({"name": "node", "data": "x"})  # returns immediately, never raises
        assert _wait_until(lambda: seam.trace_loss_count >= 1)
    finally:
        seam.close()


def test_tracing_drop_counter_increments() -> None:
    """spec(§14) — every dropped export bumps the trace-loss counter."""
    from obs.tracing import TracingSeam

    seam = TracingSeam(_ErroringExporter(), redactor=_redactor(), export_timeout=0.05)
    try:
        for i in range(3):
            seam.emit({"name": f"node-{i}"})
        assert _wait_until(lambda: seam.trace_loss_count >= 3)
    finally:
        seam.close()


def test_tracing_exports_redacted_span_on_success() -> None:
    """spec(§14/§16) — a working exporter receives the span (no drop), redacted at egress."""
    from obs.tracing import TracingSeam

    exporter = _RecordingExporter()
    seam = TracingSeam(exporter, redactor=_redactor(), export_timeout=1.0)
    try:
        seam.emit({"name": "node", "detail": "token sk-live-TRACESECRET in the span"})
        assert _wait_until(lambda: len(exporter.received) == 1)
        assert seam.trace_loss_count == 0
        assert "sk-live-TRACESECRET" not in str(exporter.received[0])  # redacted at egress
    finally:
        seam.close()
