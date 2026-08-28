# Session core-001 — Phase 2 pipeline spine (2.1–2.4)

- **Date:** 2026-06-18
- **Track:** core · **Phase:** 2 (Pipeline core — graph · engine · reconciler)
- **Predecessor session:** [contract-004](contract-004-2026-06-17-services-pipeline-phase0-tail.md) (Phase-0 `services/pipeline` tail — the fork point)
- **Successor session:** _TBD_ (next core round — 2.5 error taxonomy + new 2.6 Inv1 gate + 2.7 run-start integration)
- **Branch:** `track/core` (not pushed — orchestrator pushes at `/orchestrate-end`)

## Why this session existed

Phase 0 sealed the frozen contracts; the core track forked off `origin/track/contract` to build the **resumable pipeline spine on mocks** (the §5/§6 orchestration core — graph, engine, reconciler — provably resumable without cloud). This session landed the first four Phase-2 tasks (2.1–2.4); the round was closed at the user's direction with 2.5 held for next round.

## What was built

### Files created
- `graph/gates.py` — `GATE_ORDER` + `assert_gate_order`/`next_gate`/`GateOrderError`: the **Inv5** ordered-gate guard (SAFETY rule-6).
- `graph/state.py` — `PipelineState` (Pydantic v2): the by-id checkpoint State (`projectId`, `runId`, `itemStates`, `providerJobRefs`, `artifactRefs`, `pollErrors`, `gateCursor`); imports the §12 enums, never redefines them.
- `graph/build.py` — `build_graph(checkpointer, *, providers=None, on_stage=None)`: the StateGraph topology (5 stages × interrupt gates, two-phase cloud stages when a provider is injected), `# type: ignore[call-overload]` on `add_node` (Lesson 11).
- `graph/checkpointer.py` — `make_checkpointer(...)`: PG-primary / SQLite-saver fallback (ADR-002), credential-free DSN logging (`_safe_dsn`, rule-5).
- `graph/cloud_node.py` — the two-phase cloud node (`CloudStageSpec`, `make_submit_node`/`make_poll_node`, `PollWatchdogError`): `@task` idempotent submit → State-persisted ref → poll/reconcile (R9).
- `engine/scheduler.py` — `Scheduler`/`SchedulerConfig`/`ResourceKind`/`WorkUnit`/`UnitResult`/`ProjectBusyError`: bounded-parallel, two `ResourceKind`-tagged semaphore caps, one-active-project reject guard.
- `engine/reconciler.py` — `Reconciler`/`ReconcileAction`/`ReconcileOutcome`/`decide`/`reclaim_stale_lock`: the §6 startup-reconcile decision-table + dead-PID lock reclaim.
- Tests (NEW): `tests/graph/{__init__,conftest,test_state,test_build,test_checkpointer,test_resume,test_gates_ordered,test_gates_graph,test_cloud_node}.py`; `tests/engine/{test_scheduler,test_reconciler}.py`.

### Files modified
- `graph/__init__.py` — export the graph seam (`build_graph`, `PipelineState`, `make_checkpointer`, gates, `CloudStageSpec`, `ProviderBundle`, `PollWatchdogError`).
- `engine/__init__.py` — export the scheduler + reconciler seam.
- `pyproject.toml` + `uv.lock` — add `langgraph` 1.2.5 + `langgraph-checkpoint-postgres`/`-sqlite` 3.1.0 (2.1/2.2).

### Commits (6, on `track/core`)
- 2.1 `69a405b` (Inv5 gate guard) · `a742045` (StateGraph + State) · `b1cabd2` (checkpointer + resume)
- 2.2 `0bc96c2` (two-phase cloud node, R9)
- 2.3 `a1e6d9e` (bounded-parallel scheduler)
- 2.4 `2165c56` (startup reconciler + dead-PID lock reclaim)

## Decisions made
- **langgraph 1.2.5** — API verified via Context7 + throwaway probes; **`durability` is a runtime `invoke`/`stream` arg, not `compile()`** (Lesson 11). Checkpointer = PG-primary / separate-module SQLite-saver fallback; SQLite is the deterministic unit path, PG env-gated behind `AISIMS_TEST_DATABASE_URL`.
- **Inv5 ordered-gate guard lands as its own first commit** (bisectable safety pin), ahead of `build.py` which imports it.
- **Two-phase cloud node = two nodes** (`<stage>` submit `@task` → `<stage>_poll`) so the `ProviderJobRef` is in State **before** the poll (acceptance #2); R9 proven by a closure-`@task` cache + a State-guard (spy shows `submit`==1 across a SQLite restart). langgraph differentiates same-named `@task` closures by graph position (probe-verified) → no cache collision.
- **Provider injection** via `build_graph(providers=ProviderBundle|None)`; `None` leaves the 2.1 no-op topology untouched (rule 2 — no hard-coded provider; registry selection is the scheduler's job).
- **Scheduler** = asyncio, two independent `asyncio.Semaphore` caps; one-active-project = **reject** (`ProjectBusyError`, released in `finally`); per-item isolation catches `Exception` **not** `BaseException` (cancellation propagates — Lesson 15).
- **Reconciler** = a pure `decide()` table + a driver with injected provider + `artifact_exists` predicate; **sync** (the §7 Protocol is sync). Lock reclaim reuses the **unchanged** 0.9 `SingleWriterLock` dead-PID-only `acquire`.
- **`PipelineState.artifactRefs`/`pollErrors`** added in 2.2 are **State-internal** (checkpoint fields), NOT a `packages/contracts` change.
- Typing: a localized `# type: ignore[call-overload]` for langgraph `add_node` (Lesson 11) rather than importing the private `langgraph.graph._node.StateNode`; PEP 695 generics for the scheduler.

## Decisions explicitly NOT made (deferred)
- **Live run-start integration** (run-start IPC → scheduler → `build_graph` per item; supervisor boot → reconciler → resume) → **2.7** (new task). Everything this session is reachable from the suite + exported, but not yet wired to a production entry point.
- **Inv1 full exportability gate** → **2.6** (new task, own commit + pin).
- **§17 error-taxonomy classification** of the per-item / per-ref failures the scheduler + reconciler isolate → **2.5**; incl. transient-poll-error → RE_POLL reclassification (the conservative REGENERATE fallback is correct for 2.4).
- **`TaskGroup` / explicit sibling-cancel** for real cancellable work in `WorkUnit.run` (the asyncio.gather-orphans-siblings nuance) → **2.7** run-start wiring.
- **Hoist the poll+fetch Protocol** (duplicated in `graph/cloud_node` + `engine/reconciler`) into a shared `engine` module → orchestrator-tracked dedup.
- **Real-adapter mid-flight idempotency key** + **`fetch` URL scheme/host validation** (§16) → **Phase 3**.
- **Queryable app-repo `ProviderJobRef` persistence** (a store column for the reconciler) + the transactional "step FAILED" write (`StepRepository`) + regenerate re-enqueue → run-start integration (**2.7**).
- **Per-item State keying** (`itemId:stage`) for the State maps → future item-iteration slice.
- **Full §17 cloud-poll watchdog** (wall-clock + structured envelope) → 2.5 (the `max_polls` bound is the pre-2.5 stopgap).

## TDD compliance
**CLEAN — no violations.** All four tasks ran strict `/tdd`: tests written first, RED confirmed for the right reason (ModuleNotFoundError / import), Step-2.5 test-design approved by the orchestrator before GREEN, then minimal implementation. Both Step-8 reviewers (security + code-quality) ran every slice; all HIGH/MED findings were folded in-slice (notably the 2.2 RULE-5 DSN-log redaction + unknown-gate `GateOrderError`, and the 2.4 RE_FETCH `fetched_paths`/no-urls/`.ok` cluster).

## Reachability
Every feature is **exported from its package `__init__` and reachable from the test suite**:
- 2.1: `graph/__init__:build_graph`, `PipelineState`, `make_checkpointer` (+ gates).
- 2.2: `graph/cloud_node` factories via `build_graph(providers=)`; `test_build_wires_cloud_stages_only_when_injected` pins the wiring seam.
- 2.3: `engine/__init__:Scheduler` (+ config/result types).
- 2.4: `engine/__init__:Reconciler`/`decide`/`reclaim_stale_lock`.

**Tested-but-not-live-wired gap (documented, not silent):** the production entry path (run-start IPC handler → scheduler → `build_graph`; supervisor boot → reconciler → resume) is **not yet wired** — it is the explicit **2.7 run-start integration** task, including the kill→reopen→reconcile-resume Phase-2 contract test.

## Open follow-ups
Step-9 items were routed **hot** to the orchestrator each slice (its `/orchestrate-end` is the verify pass): arch notes (§5 two-phase node + State shape + durability-at-invoke; §6 scheduler + reconciler decision-table + scheduler-vs-lock distinction), LESSONS #9–16, the area `CLAUDE.md` index/lookup/forbidden-pattern rows. Still-open (all owned beyond this round):
- **Cross-doc invariant: NONE** this session (the invariants table is empty; `PipelineState` is engine-internal — confirmed multi-track memory-check: every State change was flagged at Step 9 as State-internal/not-a-contract).
- **Future TODOs (belongs-to-phase):** run-start integration (**2.7**) — scheduler→`build_graph` per item, registry-selected providers, `TaskGroup`/sibling-cancel, queryable app-repo ref persistence, `StepRepository` "step FAILED" write, regenerate re-enqueue; **2.6** Inv1 exportability gate; **2.5** §17 taxonomy (+ transient-poll→RE_POLL, full watchdog); **Phase 3** real-adapter idempotency key + `fetch` URL validation; orchestrator-tracked poll+fetch Protocol hoist.

## How to use what was built
- `build_graph(make_checkpointer(...), providers={GateKind.CONCEPT: CloudStageSpec(submit=…, provider=…)})` → a resumable graph; invoke with `durability="sync"`; gates pause via `interrupt()`, resume via `Command(resume=…)`.
- `Scheduler(SchedulerConfig(cloud_submit_cap=…, local_blender_cap=…)).run_project(project_id, units)` → bounded-parallel `dict[key, UnitResult]`.
- `Reconciler().reconcile(refs, provider, artifact_exists)` on reopen → `dict[jobId, ReconcileOutcome]`; `reclaim_stale_lock(lock)` to reclaim a dead-owner lock.
