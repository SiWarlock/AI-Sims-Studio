"""Startup reconciler pins (task 2.4, §6/§5, REQ-NF-102).

The reconciler is a pure decision-table over each persisted ProviderJobRef on reopen
(submitted/running→re-poll, succeeded+present→resume, succeeded+missing→re-fetch,
failed/expired→regenerate), plus a driver that escalates re-fetch→regenerate when the
re-fetch fails (expired urls), isolates per-ref poll failures (catch Exception, Lesson 15),
and wires the 0.9 SingleWriterLock dead-PID-only reclaim on reopen. On mock providers.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from aisims_contracts import PollResult, PollStatus, ProviderJobRef

from engine.lock import SingleWriterLock
from engine.reconciler import (
    ReconcileAction,
    Reconciler,
    decide,
    reclaim_stale_lock,
)


def _ref(job_id: str) -> ProviderJobRef:
    return ProviderJobRef(
        provider="mock", model="m", jobId=job_id, submittedAt=datetime(2026, 1, 1, tzinfo=UTC)
    )


def _poll(status: PollStatus, urls: list[str] | None = None) -> PollResult:
    return PollResult(status=status, urls=urls)


class _StubProvider:
    """Maps jobId → a canned PollResult (or an Exception to raise); fetch optionally fails."""

    def __init__(
        self, results: dict[str, PollResult | Exception], *, fetch_raises: bool = False
    ) -> None:
        self._results = results
        self._fetch_raises = fetch_raises
        self.fetch_calls = 0

    def poll(self, ref: ProviderJobRef) -> PollResult:
        outcome = self._results[ref.jobId]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    def fetch(self, urls: list[str]) -> list[str]:
        self.fetch_calls += 1
        if self._fetch_raises:
            raise RuntimeError("artifact urls expired")
        return [f"/scratch/artifact-{i}.bin" for i in range(len(urls))]


# --- the pure §6 decision-table (tests 1-4) ---


def test_decide_pollable_re_polls() -> None:
    """Asserts a still-pollable job → RE_POLL. spec(§6)"""
    assert decide(PollStatus.SUBMITTED, artifact_present=False) is ReconcileAction.RE_POLL
    assert decide(PollStatus.RUNNING, artifact_present=True) is ReconcileAction.RE_POLL


def test_decide_succeeded_artifact_present_resumes() -> None:
    """Asserts succeeded + artifact present → RESUME (continue). spec(§6)"""
    assert decide(PollStatus.SUCCEEDED, artifact_present=True) is ReconcileAction.RESUME


def test_decide_succeeded_artifact_missing_refetches() -> None:
    """Asserts succeeded + artifact missing → RE_FETCH. spec(§6)"""
    assert decide(PollStatus.SUCCEEDED, artifact_present=False) is ReconcileAction.RE_FETCH


def test_decide_expired_or_failed_regenerates() -> None:
    """Asserts expired / failed (incl. GC'd) → REGENERATE. spec(§6)"""
    assert decide(PollStatus.EXPIRED, artifact_present=True) is ReconcileAction.REGENERATE
    assert decide(PollStatus.FAILED, artifact_present=False) is ReconcileAction.REGENERATE


# --- the reconcile driver (tests 5-6) ---


def test_reconcile_refetch_then_regenerate_on_expired_urls() -> None:
    """Asserts a succeeded-but-missing ref whose re-fetch fails escalates to REGENERATE. spec(§6)"""
    provider = _StubProvider({"j1": _poll(PollStatus.SUCCEEDED, urls=["u"])}, fetch_raises=True)
    outcomes = Reconciler().reconcile([_ref("j1")], provider, artifact_exists=lambda _r: False)
    assert outcomes["j1"].action is ReconcileAction.REGENERATE
    assert provider.fetch_calls == 1  # the re-fetch was attempted before escalating
    assert not outcomes["j1"].ok  # the fetch error is captured (distinguishable from a clean route)
    assert isinstance(outcomes["j1"].error, RuntimeError)


def test_reconcile_refetch_success_carries_paths() -> None:
    """Asserts a succeeded-but-missing ref re-fetches and carries its paths (RE_FETCH). spec(§6)"""
    provider = _StubProvider({"j1": _poll(PollStatus.SUCCEEDED, urls=["u1", "u2"])})
    outcomes = Reconciler().reconcile([_ref("j1")], provider, artifact_exists=lambda _r: False)
    assert outcomes["j1"].action is ReconcileAction.RE_FETCH
    assert outcomes["j1"].ok
    assert outcomes["j1"].fetched_paths is not None
    assert len(outcomes["j1"].fetched_paths) == 2
    assert provider.fetch_calls == 1


def test_reconcile_succeeded_no_urls_regenerates() -> None:
    """Asserts a succeeded-but-missing ref with no urls → REGENERATE (no phantom fetch). spec(§6)"""
    provider = _StubProvider({"j1": _poll(PollStatus.SUCCEEDED, urls=None)})
    outcomes = Reconciler().reconcile([_ref("j1")], provider, artifact_exists=lambda _r: False)
    assert outcomes["j1"].action is ReconcileAction.REGENERATE
    assert provider.fetch_calls == 0  # nothing to fetch → never attempted (no phantom success)


def test_reconcile_per_ref_isolation() -> None:
    """Asserts one ref's poll raising does not abort the others; its error is captured. spec(§6)"""
    refs = [_ref("ok"), _ref("boom"), _ref("alive")]
    provider = _StubProvider(
        {
            "ok": _poll(PollStatus.SUCCEEDED, urls=["u"]),
            "boom": RuntimeError("poll exploded"),
            "alive": _poll(PollStatus.RUNNING),
        }
    )
    present = {"ok"}
    outcomes = Reconciler().reconcile(refs, provider, artifact_exists=lambda r: r.jobId in present)
    assert outcomes["ok"].action is ReconcileAction.RESUME
    assert outcomes["ok"].ok
    assert outcomes["alive"].action is ReconcileAction.RE_POLL
    assert outcomes["alive"].ok
    assert not outcomes["boom"].ok
    assert isinstance(outcomes["boom"].error, RuntimeError)
    assert outcomes["boom"].action is ReconcileAction.REGENERATE  # unrecoverable → offer regenerate


# --- stale-lock recovery on reopen (test 7) ---


def test_stale_lock_dead_pid_reclaimed_on_reopen(tmp_path: Path) -> None:
    """Asserts a lock held by a DEAD owner PID is reclaimed on reopen. spec(§6)"""
    lock_path = tmp_path / "writer.lock"
    assert SingleWriterLock(lock_path, pid=111).acquire()  # prior owner holds it
    reopen = SingleWriterLock(lock_path, pid=222, pid_alive=lambda p: p != 111)  # 111 is dead
    assert reclaim_stale_lock(reopen) is True


def test_live_lock_not_reclaimed(tmp_path: Path) -> None:
    """Asserts a lock held by a LIVE owner PID is NOT reclaimed (dead-PID-only rule). spec(§6)"""
    lock_path = tmp_path / "writer.lock"
    assert SingleWriterLock(lock_path, pid=111).acquire()
    reopen = SingleWriterLock(lock_path, pid=222, pid_alive=lambda _p: True)  # 111 is alive
    assert reclaim_stale_lock(reopen) is False
