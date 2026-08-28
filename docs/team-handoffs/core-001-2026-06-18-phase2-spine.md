# Handoff — core track, Phase-2 round 1 (2.1–2.4): pipeline spine

**Date:** 2026-06-18 · **Track:** core · **Orchestrator:** core-pipeline-orchestrator · **Branch:** track/core
**Round:** Phase-2 spine, slices 2.1–2.4 (mocks). Closed out at the user's direction (clean 4-slice stopping point); 2.5/2.6/2.7 resume fresh next round.

> **Routing note (multi-track).** Sections **A** (IMPLEMENTATION_PLAN.md delta) + **B** (ARCHITECTURE.md arch-notes) are **shared-root-doc edits → the INTEGRATION checkout** (the lead's root tree), NOT track/core. The lead applies them there. Section **C** is the **track-local** round commit (LESSONS/CLAUDE index/briefs/this handoff/session doc) on track/core. No shared-root file is edited in the worktree.

---

## Round summary

6 commits on `track/core` off base `bd4d4c4` (Phase-0 seal):

| Slice | Commit(s) | What |
|---|---|---|
| 2.1 LangGraph StateGraph + checkpointer | `69a405b` (Inv5 gate guard) · `a742045` (StateGraph + typed State) · `b1cabd2` (checkpointer + resume + DSN-redaction caplog pin) | typed `PipelineState` (by-id), 5 ordered `interrupt()` gates, PG-primary/SQLite-fallback checkpointer, resume-across-restart. **[SAFETY rule-6 / Inv5] landed (own commit + pin).** |
| 2.2 Two-phase cloud node | `0bc96c2` | `@task` idempotent submit persists `ProviderJobRef` before side effect → poll/reconcile node; R9 no-double-submit; injected provider; `durability='sync'` at invoke; bounded poll watchdog. |
| 2.3 Bounded-parallel scheduler | `a1e6d9e` | two `ResourceKind` semaphore caps (cloud / Blender), block-and-queue, per-item failure isolation (catch `Exception`), one-active-project reject guard. REQ-NF-101. |
| 2.4 Startup reconciler + stale-lock recovery | `2165c56` | §6 decision-table (`{RE_POLL,RESUME,RE_FETCH,REGENERATE}`), re-fetch→regenerate escalation, per-ref isolation, dead-PID lock reclaim on reopen. REQ-NF-102. |

Suite at 2.4: **99 passed / 1 skipped** (env-gated PG); `mypy --strict` 59 files; ruff+format clean. Reviewers ran every slice (security-reviewer on the invariant slices; both clean). Not pushed (push at the round seal if a remote is configured for track/core).

---

## A. INTEGRATION-CHECKOUT DELTA — `IMPLEMENTATION_PLAN.md` (lead applies to root tree)

### A1. Tick completed work (Phase 2 section)
- **2.1** — tick the two behavior bullets (one node/subgraph per stage + checkpointer w/ ownership partition & SQLite-saver parity; approval gates = `interrupt()`/`Command(resume)`). ✅ landed.
- **2.2** — tick (`@task` idempotent submit → persist `ProviderJobRef` before side effect → poll/reconcile). ✅
- **2.3** — tick (bounded-parallel, two separate caps, one active project, block-and-queue, per-item isolation). ✅
- **2.4** — tick (decision-table; single-writer lock PID+heartbeat reclaimable on reopen). ✅
- **Acceptance criteria (2):** tick the **`[SAFETY-RULE-6 · Inv5]` ordered-gates** bullet (landed 2.1 `69a405b`, pinned by `test_gates_ordered`/`test_gates_graph`). **Leave UNticked:** `[SAFETY-RULE-1 · Inv1]` exportability gate (→ new **2.6**) and the "full mock collection runs… kill→reconcile→resume" end-to-end (→ new **2.7**).

### A2. Add two tasks to Phase 2 (after 2.5)
```markdown
### 2.6 — [SAFETY-RULE-1 · Inv1 · PINNED · NON-DROPPABLE · D16] Full exportability gate
- [ ] The Phase-2 engine validator completes the 3-condition gate: an item is exportable **only if** `included ∧ has a state=selected AssetVariant ∧ no blocking validation` (Inv1) — pinned by a test asserting all three conditions gate export (own commit, mirroring how Inv5 landed in 2.1).
- [ ] Files: NEW `services/pipeline/engine/exportability.py` (or the export-stage validator seam)
- [ ] Cross-doc invariant: none (consumes 0.4a `AssetVariant`/`AssetVariantState`/`ItemSpec`; State-internal)
- [ ] Depends on: 2.1 (export gate node), 0.4a
- [ ] Implements: SAFETY-RULE-1 / Inv1

### 2.7 — Run-start integration + reconcile-resume contract test
- [ ] End-to-end boot wiring: supervisor → reconciler → scheduler → `build_graph` resume; registry-selected providers via the 2.2 `providers=` seam (Lesson 13); per-item State keying (`itemId:stage`); a `StepRepository` for the transactional "step FAILED" write + the regenerate re-enqueue; `TaskGroup`/explicit sibling-cancel for cancellable real work (2.3-b); the queryable app-repo `ProviderJobRef` persistence (2.2-d).
- [ ] **The reconcile-resume contract test:** a full mock collection runs on the graph; kill mid-run → reopen → reconcile + resume from the last completed step with **no lost accepted assets and no double-submit**; gates pause/resume across process exit.
- [ ] Files: NEW `services/pipeline/engine/runner.py` (boot/run-start) + a `StepRepository` in `store/`
- [ ] Cross-doc invariant: none
- [ ] Depends on: 2.2, 2.3, 2.4, 2.5
```

### A3. "Currently in progress" (replace)
> **Phase 2 — core track — round 1 SEALED (2.1–2.4) on `track/core`.** The resumable pipeline spine is up on mocks: typed `PipelineState` (by-id) + 5 ordered `interrupt()` gates (Inv5 PINNED, own commit) + PG/SQLite checkpointer w/ resume-across-restart (2.1); two-phase `@task` cloud node w/ R9 no-double-submit (2.2); bounded-parallel scheduler, two `ResourceKind` caps (2.3); startup reconciler decision-table + dead-PID lock reclaim (2.4). 99 tests. **Remaining Phase 2:** 2.5 (error taxonomy/watchdog/bounded-repair/cancel) → **2.6 Inv1 exportability gate** (PINNED, own commit+pin) → **2.7 run-start integration + the kill→reconcile→resume contract test** (the Phase-2 acceptance demo). **Next session target: 2.5.** Inv5 ✅ landed; **Inv1 remains the open PINNED safety item (2.6).**

### A4. Log entry (append)
```markdown
### 2026-06-18 — Phase 2 core round 1 (2.1–2.4): pipeline spine on track/core
- **Landed:** 2.1 (`69a405b` Inv5 gate guard, own commit+pin · `a742045` StateGraph+State · `b1cabd2` checkpointer+resume+DSN-redaction pin) · 2.2 (`0bc96c2` two-phase cloud node, R9) · 2.3 (`a1e6d9e` bounded-parallel scheduler, REQ-NF-101) · 2.4 (`2165c56` startup reconciler + dead-PID lock reclaim, REQ-NF-102). 99 passed/1 skipped; mypy --strict 59 files.
- **Decisions:** durability is a langgraph-1.2.5 **runtime** invoke arg (not compile) → build_graph compiles checkpointer-only (Lesson 11). R9 scopes to no-double-**submit**; mid-poll re-fetch is the reconciler's job. one-active-project = in-memory reject guard, distinct from the 0.9 on-disk lock. Reconciler poll-raise → conservative human-gated REGENERATE (transient→RE_POLL reclassification deferred to 2.5).
- **Restructure (user-approved):** ADD 2.6 (Inv1 full-exportability-gate, own commit+pin — the second PINNED D16 item, no home in the original 2.1–2.5) + 2.7 (run-start integration + the kill→reconcile→resume contract test — the Phase-2 acceptance demo, not an explicit 2.X task). Surfaced by the orchestrator as a Finding; user approved both as required/non-droppable.
- **Lessons banked:** `services/pipeline` §9–§16 (graph State by-id+contract-enums · checkpointer PG/SQLite-fallback · langgraph add_node mypy overload · two-phase cloud node/R9 · injected provider · ResourceKind caps · asyncio catch-Exception-not-BaseException · reconciler decision-table).
- **Carry-forward triage:** the run-start-integration items folded INTO 2.7; transient-poll→RE_POLL folded INTO 2.5; the PollFetchProvider hoist-to-shared-engine-module + the Inv1 validator → 2.6/2.7. (see Section D.)
- **Round seal:** 2.1–2.4 sealed on `track/core`; closed out at a clean 4-slice boundary (orchestrator surfaced the Phase-2-completeness Finding + the context fork; user chose close-out-now). Phase 2 resumes fresh (2.5→2.6→2.7).
- **Reference:** implementer session doc `docs/sessions/core-001-…-phase2-spine.md`; briefs `docs/briefs/core-00{1,2,3,4}-*.md`; this handoff.
```

---

## B. INTEGRATION-CHECKOUT DELTA — `ARCHITECTURE.md` arch-notes (lead applies; atomic prose, no contract change)

**§5 (Pipeline orchestration) — append a "Phase-2 spine (2.1/2.2 skeleton)" note:**
> The graph-runtime `PipelineState` (in `services/pipeline/graph/state.py`) references §12 entities **by id** and imports their enums from `aisims_contracts` (never redefines them): `{projectId, runId, itemStates: dict[str,ItemState], providerJobRefs, gateCursor: GateKind|None, artifactRefs, pollErrors}`. The 5 ordered approval gates are `interrupt()`/`Command(resume)` with a `GateKind`-keyed ordered-gate guard (`graph/gates.py`) as the **Inv5 enforcement point** (rejects an out-of-order/unknown-gate resume). Cloud stages are **two-phase**: a `@task` submit node (result-checkpointed) persists the `ProviderJobRef` into State **before any side effect**, then a `<stage>_poll` reconcile node (R9 no-double-submit on replay). **`durability='sync'` is a runtime `invoke`/`stream` arg in langgraph 1.2.5 — NOT a `compile()` kwarg** — so `build_graph` compiles checkpointer-only; the 'sync' convention is applied by the run-start caller. Checkpointer factory = `langgraph-checkpoint-postgres` primary with a separate-module SQLite-saver fallback (ADR-002), SQLite = deterministic unit path, PG = env-gated `AISIMS_TEST_DATABASE_URL`.

**§6 (Job/run engine + supervisor) — append a "Phase-2 scheduler + reconciler (2.3/2.4)" note:**
> The **scheduler** (`engine/scheduler.py`, distinct from the graph) bounds item work by two independent `ResourceKind`-tagged `asyncio.Semaphore` caps (cloud-submit / local-Blender), block-and-queue on `acquire`, per-item failure isolation via a `dict[str,UnitResult]` map (catch `Exception`, **not** `BaseException` — cancellation propagates), and a one-active-project **reject** guard (`ProjectBusyError`, released in `finally`) — an in-memory guard **distinct** from the 0.9 on-disk `SingleWriterLock`. The **startup reconciler** (`engine/reconciler.py`) is a pure decision-table `decide(poll_status, artifact_present) → {RE_POLL, RESUME, RE_FETCH, REGENERATE}` with the re-fetch→regenerate escalation (re-fetch fails / no urls) and a conservative human-gated REGENERATE on a poll-raise; FS/provider deps injected; decision-only (returns outcomes; the transactional "step FAILED" write + regenerate re-enqueue are the run-start integration). `reclaim_stale_lock` reuses the 0.9 **dead-PID-only** reclaim on reopen (a LIVE owner is never reclaimed; atomic-acquire + fencing stay the Phase-2+ upgrade).

---

## C. TRACK-LOCAL round commit (`track/core`)

Orchestrator round terminal commit (after the implementer's `/session-end` session-doc commit), `git add` exactly:
- `services/pipeline/LESSONS.md` (lessons **#9–#16**)
- `services/pipeline/CLAUDE.md` (index rows #9–16, a §12 lookup row, the lesson-11 private-import forbidden-pattern)
- `docs/briefs/core-00{1,2,3,4}-*.md` (the 4 slice briefs)
- `docs/team-handoffs/core-001-2026-06-18-phase2-spine.md` (this file)
Commit msg: `docs(core): Phase-2 round 1 seal (2.1–2.4) — lessons #9–16 + briefs + handoff`. Push to `origin/track/core` if a remote is configured.

---

## D. Carry-forward triage (for the next round's briefs)

- **2.5 (error taxonomy):** transient-poll-error → RE_POLL reclassification (vs the 2.4 conservative REGENERATE fallback); §17 classification of the scheduler's isolated per-item failures + the reconciler's poll-raises; the full wall-clock+heartbeat cloud-poll watchdog (the 2.2 `max_polls` is the pre-2.5 stopgap); bounded LLM repair (max-K); cancel semantics.
- **2.6 (Inv1):** the 3-condition exportability validator + its pinning test (own commit).
- **2.7 (run-start integration):** supervisor→reconciler→scheduler→`build_graph` resume; the `StepRepository` (transactional step-FAILED write + regenerate re-enqueue); queryable app-repo `ProviderJobRef` persistence (2.2-d); `TaskGroup`/sibling-cancel for cancellable real work (2.3-b); per-item State keying; the kill→reconcile→resume contract test.
- **Cleanup:** hoist ONE poll+fetch Protocol into a shared `engine` module (`graph/cloud_node` + `engine/reconciler` both import it; graph→engine is the allowed direction) — removes the 2-copy dup.
- **Phase-3 carry:** real-adapter mid-flight idempotency key (crash during the external submit); fetch() URL scheme/host validation (§16 provider-output validation; the mock fetch already scratch-guards basenames).
- **Phase-8 carry:** real LangSmith tracing config; bound the export tracing queue (0.9 unbounded fail-open).
