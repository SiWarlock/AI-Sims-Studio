"""Bounded-parallel scheduler pins (task 2.3, §6, REQ-NF-101).

The job/run engine schedules item-work bounded by two INDEPENDENT per-ResourceKind caps
(cloud-submit + local-Blender), under one active project, block-and-queue on saturation,
with per-item failure isolation. asyncio model; no pytest-asyncio (each test drives its own
loop via asyncio.run). The concurrency probe is deterministic — it spins the loop until the
cap saturates rather than sleeping a fixed interval.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

import pytest
from pydantic import ValidationError

from engine.scheduler import (
    ProjectBusyError,
    ResourceKind,
    Scheduler,
    SchedulerConfig,
    WorkUnit,
)

CLOUD = ResourceKind.CLOUD_SUBMIT
BLENDER = ResourceKind.LOCAL_BLENDER


class _Probe:
    """Tracks per-kind in-flight + peak concurrency; gates each unit on a release Event."""

    def __init__(self) -> None:
        self.active: dict[ResourceKind, int] = dict.fromkeys(ResourceKind, 0)
        self.peak: dict[ResourceKind, int] = dict.fromkeys(ResourceKind, 0)
        self.started: dict[ResourceKind, int] = dict.fromkeys(ResourceKind, 0)
        self.release = asyncio.Event()

    def work(self, kind: ResourceKind) -> Callable[[], Awaitable[str]]:
        async def _run() -> str:
            self.started[kind] += 1
            self.active[kind] += 1
            self.peak[kind] = max(self.peak[kind], self.active[kind])
            await self.release.wait()
            self.active[kind] -= 1
            return kind.value

        return _run


async def _wait_until(predicate: Callable[[], bool]) -> None:
    """Spin the event loop until `predicate` holds (deterministic; bounded against a hang)."""
    for _ in range(100_000):
        if predicate():
            return
        await asyncio.sleep(0)
    raise AssertionError("predicate never satisfied — scheduler did not reach the expected state")


def _units(probe: _Probe, kind: ResourceKind, n: int) -> list[WorkUnit[str]]:
    return [WorkUnit(key=f"{kind.value}-{i}", kind=kind, run=probe.work(kind)) for i in range(n)]


def test_cloud_cap_bounds_peak_concurrency() -> None:
    """Asserts CLOUD_SUBMIT peak concurrency never exceeds cloud_submit_cap. spec(§6)"""

    async def inner() -> None:
        probe = _Probe()
        sched = Scheduler(SchedulerConfig(cloud_submit_cap=3, local_blender_cap=2))
        task = asyncio.create_task(sched.run_project("p", _units(probe, CLOUD, 7)))
        await _wait_until(lambda: probe.active[CLOUD] == 3)
        assert probe.peak[CLOUD] == 3  # saturated at the cap, never above
        probe.release.set()
        results = await task
        assert len(results) == 7
        assert all(r.ok for r in results.values())

    asyncio.run(inner())


def test_blender_cap_bounds_peak_concurrency() -> None:
    """Asserts LOCAL_BLENDER peak concurrency never exceeds local_blender_cap. spec(§6)"""

    async def inner() -> None:
        probe = _Probe()
        sched = Scheduler(SchedulerConfig(cloud_submit_cap=4, local_blender_cap=2))
        task = asyncio.create_task(sched.run_project("p", _units(probe, BLENDER, 6)))
        await _wait_until(lambda: probe.active[BLENDER] == 2)
        assert probe.peak[BLENDER] == 2
        probe.release.set()
        results = await task
        assert len(results) == 6
        assert all(r.ok for r in results.values())

    asyncio.run(inner())


def test_two_caps_are_independent() -> None:
    """Asserts cloud + blender each reach their own cap concurrently (separate paths). spec(§6)"""

    async def inner() -> None:
        probe = _Probe()
        sched = Scheduler(SchedulerConfig(cloud_submit_cap=2, local_blender_cap=2))
        units = _units(probe, CLOUD, 3) + _units(probe, BLENDER, 3)
        task = asyncio.create_task(sched.run_project("p", units))
        # Both kinds saturate at the SAME time — cloud saturation did not consume blender slots.
        await _wait_until(lambda: probe.active[CLOUD] == 2 and probe.active[BLENDER] == 2)
        assert probe.peak[CLOUD] == 2
        assert probe.peak[BLENDER] == 2
        probe.release.set()
        results = await task
        assert len(results) == 6
        assert all(r.ok for r in results.values())

    asyncio.run(inner())


def test_block_and_queue_on_saturation() -> None:
    """Asserts the (cap+1)th unit waits for a free slot, never exceeds the cap. spec(§6)"""

    async def inner() -> None:
        probe = _Probe()
        sched = Scheduler(SchedulerConfig(cloud_submit_cap=2, local_blender_cap=2))
        task = asyncio.create_task(sched.run_project("p", _units(probe, CLOUD, 3)))
        await _wait_until(lambda: probe.active[CLOUD] == 2)
        # The 3rd unit is blocked on the semaphore — it has NOT started.
        assert probe.started[CLOUD] == 2
        assert probe.active[CLOUD] == 2  # cap never exceeded
        probe.release.set()
        results = await task
        assert probe.started[CLOUD] == 3  # the queued unit started only after a slot freed
        assert len(results) == 3
        assert all(r.ok for r in results.values())

    asyncio.run(inner())


def test_per_item_failure_isolation() -> None:
    """Asserts one unit raising does not abort siblings; the failure is captured. spec(§6)"""

    async def inner() -> None:
        async def good() -> str:
            return "ok"

        async def boom() -> str:
            raise ValueError("unit blew up")

        sched = Scheduler(SchedulerConfig(cloud_submit_cap=4, local_blender_cap=2))
        units: list[WorkUnit[str]] = [
            WorkUnit(key="g1", kind=CLOUD, run=good),
            WorkUnit(key="bad", kind=CLOUD, run=boom),
            WorkUnit(key="g2", kind=CLOUD, run=good),
            WorkUnit(key="g3", kind=CLOUD, run=good),
        ]
        results = await sched.run_project("p", units)
        assert not results["bad"].ok
        assert isinstance(results["bad"].error, ValueError)
        assert all(results[k].ok for k in ("g1", "g2", "g3"))
        assert results["g1"].value == "ok"

    asyncio.run(inner())


def test_one_active_project_guard() -> None:
    """Asserts a second run while one is active is rejected (one active project). spec(§6)"""

    async def inner() -> None:
        probe = _Probe()
        sched = Scheduler()
        task_a = asyncio.create_task(sched.run_project("A", _units(probe, CLOUD, 1)))
        await _wait_until(lambda: probe.active[CLOUD] == 1)  # project A is active
        with pytest.raises(ProjectBusyError, match=r"project 'A' is active"):
            await sched.run_project("B", _units(probe, CLOUD, 1))
        probe.release.set()
        await task_a

    asyncio.run(inner())


def test_external_cancel_releases_guard() -> None:
    """Asserts an externally-cancelled run releases the guard so a fresh run starts. spec(§6)"""

    async def inner() -> None:
        async def good() -> str:
            return "ok"

        probe = _Probe()
        sched = Scheduler()
        task = asyncio.create_task(sched.run_project("A", _units(probe, CLOUD, 1)))
        await _wait_until(lambda: probe.active[CLOUD] == 1)  # A is mid-flight
        task.cancel()  # the realistic cancel path: caller cancels the run task
        with pytest.raises(asyncio.CancelledError):
            await task
        # The finally released the guard → a fresh run starts cleanly (no wedge).
        results = await sched.run_project("B", [WorkUnit(key="b", kind=CLOUD, run=good)])
        assert results["b"].value == "ok"

    asyncio.run(inner())


def test_duplicate_keys_rejected() -> None:
    """Asserts a batch with duplicate WorkUnit keys is rejected (no silent result loss). spec(§6)"""

    async def inner() -> None:
        async def good() -> str:
            return "ok"

        sched = Scheduler()
        dupe = [
            WorkUnit(key="x", kind=CLOUD, run=good),
            WorkUnit(key="x", kind=CLOUD, run=good),
        ]
        with pytest.raises(ValueError, match="duplicate WorkUnit keys"):
            await sched.run_project("p", dupe)

    asyncio.run(inner())


def test_cancellation_propagates_not_captured() -> None:
    """Asserts CancelledError propagates (not captured) and the guard is released. spec(§6)"""

    async def inner() -> None:
        async def cancel_me() -> str:
            raise asyncio.CancelledError

        async def good() -> str:
            return "ok"

        sched = Scheduler(SchedulerConfig(cloud_submit_cap=4, local_blender_cap=2))
        units: list[WorkUnit[str]] = [
            WorkUnit(key="c", kind=CLOUD, run=cancel_me),
            WorkUnit(key="g", kind=CLOUD, run=good),
        ]
        # CancelledError is BaseException, not Exception → it is NOT captured into a UnitResult;
        # it propagates and aborts the batch (the §17 cancel path, never swallowed).
        with pytest.raises(asyncio.CancelledError):
            await sched.run_project("p", units)
        # The active-project guard was released in `finally` despite the cancellation — a fresh
        # run starts cleanly (the scheduler did not wedge).
        results = await sched.run_project("p2", [WorkUnit(key="g2", kind=CLOUD, run=good)])
        assert results["g2"].value == "ok"

    asyncio.run(inner())


def test_scheduler_config_validates_caps() -> None:
    """Asserts SchedulerConfig rejects a cap < 1 and ships human-set defaults. spec(§6)"""
    with pytest.raises(ValidationError):
        SchedulerConfig(cloud_submit_cap=0)
    with pytest.raises(ValidationError):
        SchedulerConfig(local_blender_cap=0)
    cfg = SchedulerConfig()
    assert cfg.cloud_submit_cap >= 1
    assert cfg.local_blender_cap >= 1
