"""The job/run engine's bounded-parallel scheduler (task 2.3, §6, REQ-NF-101).

Distinct from the LangGraph graph: this is the engine primitive that schedules a project's
item-work **bounded-parallel** by two INDEPENDENT per-``ResourceKind`` caps — a *cloud-submit*
cap and a *local-Blender-subprocess* cap (different hot paths; human-set config knobs) — under
**one active project**, **block-and-queue on saturation** (an ``asyncio.Semaphore`` acquire
naturally queues the surplus), with **per-item failure isolation** (each unit's outcome is
captured in a result map; one failure never aborts its siblings).

Scope: 2.3 is the standalone primitive over a caller-supplied async ``work_fn``. The run-start
integration (the scheduler driving ``build_graph`` per item with registry-selected providers —
Lesson 13) is 2.4-adjacent; ``WorkUnit.run`` is exactly where that per-item graph invocation
will plug in. The one-active-project guard here is an in-memory scheduler guard — DISTINCT from
the 0.9 process-level on-disk ``SingleWriterLock`` (``engine/lock.py``); they are not conflated.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

type WorkFn[T] = Callable[[], Awaitable[T]]


class ResourceKind(StrEnum):
    """The hot path a unit of work contends on — each has its own concurrency cap (§6)."""

    CLOUD_SUBMIT = "cloud_submit"
    LOCAL_BLENDER = "local_blender"


class SchedulerConfig(BaseModel):
    """Human-set concurrency knobs (§6/§21): one cap per ResourceKind, each ≥ 1."""

    model_config = ConfigDict(extra="forbid")

    cloud_submit_cap: int = Field(default=4, ge=1)
    local_blender_cap: int = Field(default=2, ge=1)


class ProjectBusyError(RuntimeError):
    """Raised when a run is started while another project's run is already active (§6)."""


@dataclass(frozen=True)
class WorkUnit[T]:
    """One schedulable unit: a stable ``key`` (item/step id), the ResourceKind whose cap governs
    it, and an async ``run`` thunk (the caller's work — e.g. drive the item through the graph)."""

    key: str
    kind: ResourceKind
    run: WorkFn[T]


@dataclass(frozen=True)
class UnitResult[T]:
    """A unit's captured outcome: its value, or the Exception it raised (per-item isolation)."""

    key: str
    value: T | None = None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class Scheduler:
    """Runs a project's items bounded-parallel under two caps + a one-active-project guard.

    Single-event-loop-scoped: the per-cap ``asyncio.Semaphore``s bind to the loop of first use,
    so construct (and run) a ``Scheduler`` under the one event loop that drives it.
    """

    def __init__(self, config: SchedulerConfig | None = None) -> None:
        self._config = config or SchedulerConfig()
        self._caps: dict[ResourceKind, asyncio.Semaphore] = {
            ResourceKind.CLOUD_SUBMIT: asyncio.Semaphore(self._config.cloud_submit_cap),
            ResourceKind.LOCAL_BLENDER: asyncio.Semaphore(self._config.local_blender_cap),
        }
        self._active_project: str | None = None

    async def _run_unit[T](self, unit: WorkUnit[T]) -> UnitResult[T]:
        # The per-kind semaphore bounds peak concurrency and block-and-queues the surplus.
        async with self._caps[unit.kind]:
            try:
                value = await unit.run()
            except Exception as exc:
                # Per-item isolation: capture and continue — siblings are unaffected. Catch
                # Exception (NOT BaseException): CancelledError / KeyboardInterrupt propagate.
                return UnitResult(key=unit.key, error=exc)
            return UnitResult(key=unit.key, value=value)

    async def run_project[T](
        self, project_id: str, units: Sequence[WorkUnit[T]]
    ) -> dict[str, UnitResult[T]]:
        """Run ``units`` bounded-parallel for ``project_id``; return each unit's outcome by key.

        Rejects a second concurrent run with ``ProjectBusyError`` (one active project, §6). The
        active-project guard is released in ``finally`` so a raising/cancelled run never wedges
        the scheduler. A unit raising a plain ``Exception`` is isolated (captured per-item); a
        ``BaseException`` (e.g. cancellation) propagates and aborts the batch.

        Keys must be unique within a batch (the result map is keyed by ``WorkUnit.key``).
        NOTE: per the ``asyncio.gather`` contract, a unit raising a BaseException propagates but
        leaves sibling coroutines running detached; that is harmless for the 2.3 mock work_fn, but
        the 2.4 run-start wiring (real Blender/cloud work in ``WorkUnit.run``) should wrap the batch
        in a TaskGroup / explicitly cancel siblings so orphaned real work can't linger.
        """
        keys = [unit.key for unit in units]
        if len(set(keys)) != len(keys):
            raise ValueError(
                f"duplicate WorkUnit keys in the batch for {project_id!r}: "
                f"the result map is keyed by WorkUnit.key, so duplicates would lose units"
            )
        if self._active_project is not None:
            raise ProjectBusyError(
                f"project {self._active_project!r} is active; {project_id!r} rejected "
                f"(one active project, §6)"
            )
        self._active_project = project_id
        try:
            results = await asyncio.gather(*(self._run_unit(unit) for unit in units))
        finally:
            self._active_project = None
        return {result.key: result for result in results}
