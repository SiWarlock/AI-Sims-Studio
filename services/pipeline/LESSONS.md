# LESSONS.md — AI Sims Creator (the Python pipeline sidecar)

> Full prose for every lesson logged during work in `services/pipeline/`. The compact index lives in `services/pipeline/CLAUDE.md` "Lessons logged" table.
>
> **Lesson numbers are stable IDs.** New lessons get the next sequential number. Numbers may be referenced from code comments, commit messages, and cross-references between lessons. **Don't reorder; don't reuse a deleted number's slot.**
>
> **Lessons start at §1.** Each code area has its own lesson sequence — lessons don't carry across code areas.

---

## Lesson format

```markdown
## <a id="N"></a>N. <Short topic> — <one-line rule>

**Date:** YYYY-MM-DD.
**Source slice:** <slice-id or commit hash>.

<2-5 paragraphs explaining: what was discovered, why it matters, how to
apply the rule, what edge cases are still open. Cite file:line references
where applicable.>

**Rule:** <one-sentence summary, same as the heading subtitle>.
```

---

## <a id="1"></a>1. Store persistence — HYBRID rows (key columns + the versioned entity as JSONB), not full-relational

**Date:** 2026-06-17. **Source slice:** 0.7 (`store/`, §13).

The §13 store persists the frozen domain entities (`aisims_contracts.domain`, 0.4a). Rather than mapping every field to a column (full-relational — which churns the schema + forces a migration on every model change), use a **hybrid** row: a few **key columns** the store queries/indexes on (`id` PK, `status`, `projectId`, `schema_version`) + the **full pydantic entity as a JSONB column** carrying its `schemaVersion`. The JSONB is cheap to evolve under `schemaVersion` (the entity shape changes without DDL; the migration runner reads the stamp). Portability to the deterministic test layer is `JSONB().with_variant(JSON, "sqlite")` — the SAME SQLAlchemy models run on Postgres (prod) and sqlite (unit tests). The repository layer (`Repository[T]` base + per-aggregate concretes) is the SOLE writer (rule 3).

**Rule:** persist domain entities as hybrid rows — key/indexed columns + the versioned entity as JSONB (`with_variant` for the sqlite test layer); avoid full-relational mapping that churns the schema on every model change.
**Enforce:** `pin: tests/store/test_project_repo_round_trip.py`.

## <a id="2"></a>2. Artifact durability — write bytes → fsync(file+dir) → THEN commit the row; the mover holds no DB handle (rules 3/4)

**Date:** 2026-06-17. **Source slice:** 0.7 (`store/artifacts.py`, §13).

An artifact (mesh/image/package bytes) and its DB row must be written in an order that survives a crash: move the bytes into the canonical layout, **`fsync` the file AND its directory**, and only THEN run the repo-owned `commit_row`. A crash at any point leaves an **orphan file** (reclaimable later), **never a dangling row** referencing missing bytes. The helper `commit_artifact(scratch_path, canonical_path, commit_row)` takes a commit CALLBACK, **not a db/session/store handle** — so the artifact mover structurally cannot write the DB itself; the row lands only through the repo (rule 3, sidecar = sole writer). The canonical-path builder sanitizes id segments (`is_relative_to` guard) so an unsanitized id can't escape the canonical tree (rule 4).

**Rule:** write-bytes → `fsync(file+dir)` → repo-owned commit-row (crash ⇒ orphan, never a dangling row); the artifact mover takes a commit callback, never a DB handle (structural sole-writer guard); sanitize canonical path segments.
**Enforce:** `pin: tests/store/test_write_bytes_then_commit_row.py` + `tests/store/test_sidecar_sole_writer.py`.

## <a id="3"></a>3. Store test-DB — sqlite+aiosqlite deterministic unit layer + an env-gated PG integration test

**Date:** 2026-06-17. **Source slice:** 0.7 (`tests/store/`, §13).

The production store is Postgres, but a per-test PG server makes the unit gate slow + Docker-dependent. Split it: a **deterministic unit layer on `sqlite+aiosqlite`** (no server, CI-green; the hybrid models run there via the `JSONB→JSON` `with_variant`), plus a **real-PG integration round-trip gated behind `AISIMS_TEST_DATABASE_URL`** (skipped when unset). The Alembic baseline is tested on sqlite (DDL is portable enough for the skeleton). Caveat: PG-specific behavior (JSONB operators, pgvector) is NOT exercised by the default gate — the gated PG test must run in CI (a PG service) before the store carries real Phase-2 load (tracked: the deferred holistic-CI, D20).

**Rule:** test the store on a sqlite+aiosqlite unit layer for a fast deterministic gate (hybrid models via `with_variant`) + an env-gated real-PG integration test; ensure the PG test runs in CI before production load (PG-specifics aren't covered by sqlite).
**Enforce:** `pin: tests/store/conftest.py` (the sqlite fixture) · `accepted: PG-in-CI tracked as a holistic-CI carry-forward (D20)`.

## <a id="4"></a>4. Seeded deterministic mocks — every "random" output + timestamp is a pure fn of (seed, call-seq); no wall-clock

**Date:** 2026-06-17. **Source slice:** 0.8 (`adapters/mock/`, §7/§17).

The mock adapters (provider + worker) must reproduce **byte-for-byte** across runs so Phase-2 pipeline tests and Phase-8 evals are deterministic. Achieve it with an explicit `seed: int` per mock driving a per-instance `random.Random(seed)`; every "random" output (`latencyMs`, chosen `urls`, `jobId` suffix, failure timing) is a pure function of `(seed, call-sequence)`. **No wall-clock** anywhere: timestamps come from a fixed epoch constant + a deterministic offset (`submittedAt`), and `expiresAt = submittedAt + 24h`. A same-seed test runs a mock twice (including an injected failure at a fixed poll index) and asserts equality of the full result objects (`ProviderJobRef` + each `PollResult`'s status/progress/usage/envelope) — the property a resume/reconcile test relies on. The async lifecycle (`SUBMITTED→RUNNING→SUCCEEDED` at `succeed_after_polls=3`) keeps both non-terminal states poll-observable.

**Rule:** seed every mock; all "randomness" + timestamps derive from `(seed, call-seq)` + a fixed epoch — never bare `random` or wall-clock — so Phase-2/eval runs reproduce byte-for-byte.
**Enforce:** `pin: tests/adapters/test_mock_failure.py::test_mock_determinism_same_seed`.

## <a id="5"></a>5. Provider error-channel asymmetry — async carries the failure in the result; sync RAISES

**Date:** 2026-06-17. **Source slice:** 0.8 (`adapters/mock/failure.py`, §7/§17).

The §7 provider contracts split on how a failure travels, and the mock framework must honor both channels. **Async** ops carry the error in a result: a failed `Image3DProvider`/`ImageGenProvider` job surfaces via `PollResult(status=FAILED|EXPIRED, error=ErrorEnvelope)`, and the workers via `BlenderReport`/`ExportJobReport(status=FAILED, error=…)` (the rule-6 `model_validator` enforces *failed ⟹ error present*). But **`LLMProvider.complete/structured` are synchronous and return `str`/`StructuredT` — there is no error field** — so a failure must be **raised**: a pipeline-local `ProviderError(Exception)` carrying `.envelope: ErrorEnvelope`. Do not bolt an error-return onto the sync calls (that diverges from the frozen contract). Open follow-up: when a Phase-2 engine path needs to `catch` `ProviderError`, hoist it from `adapters/mock/failure.py` to a neutral `adapters/errors.py` so the engine never imports a mock module (carry-forward).

**Rule:** async provider/worker failures ride the result (`PollResult.error` / report `error`, rule-6 validator); the synchronous `LLMProvider` calls have no error field, so they RAISE a `ProviderError(envelope)` — keep the channel split, don't fake a return.
**Enforce:** `pin: tests/adapters/test_mock_failure.py::test_llm_sync_failure_raises_envelope`.

## <a id="6"></a>6. Fail-OPEN tracing vs fail-CLOSED redaction — opposite postures, both rule-5 mandatory

**Date:** 2026-06-17. **Source slice:** 0.9 (`obs/tracing.py`, `obs/redaction.py`, §14/§16).

Two egress concerns in the obs layer take **opposite** failure postures, and conflating them is a bug. **Tracing is fail-OPEN** (rule 5 / R-): observability must NEVER stall or fail a generation run, so a slow / hanging / offline exporter ⟹ drop the trace + bump a loss counter; `emit` never blocks or raises into the caller (background queue + a fresh-daemon-thread-with-`join(timeout)`; unbounded queue in Phase 0). **Redaction is fail-CLOSED** (rule 5): a secret must NEVER leak, so if the redactor can't run, the field becomes a placeholder — a raw free-text field is never egressed. Mnemonic: *a trace may be lost to protect the run; a secret is never leaked to protect the user.* Don't let either borrow the other's posture (a fail-open redactor would leak; a fail-closed tracer would block a run).

**Rule:** tracing fails OPEN (drop + count, never block/raise); redaction fails CLOSED (placeholder, never egress raw) — opposite postures, both rule-5 mandatory.
**Enforce:** `pin: tests/obs/test_tracing.py::test_tracing_fail_open_on_hang` + `tests/obs/test_redaction.py::test_redaction_fail_closed`.

## <a id="7"></a>7. Secrets-accessor chokepoint — accessor-registration is the GUARANTEE; the pattern set is best-effort

**Date:** 2026-06-17. **Source slice:** 0.9 (`obs/secrets.py`, `obs/redaction.py`, §16).

Secrets flow through a **single accessor** (`SecretsAccessor.get` + `active_values`): keys are pulled at use and never persisted into LangGraph State, logs, or traces (the accessor's own `repr`/`str` are redacted so an accidental f-string can't leak one). The redactor scrubs every egress against the accessor's `active_values` (substring match, every occurrence) **plus** a best-effort secret/PII **pattern** set (key shapes). The load-bearing distinction: **the GUARANTEE that a secret is scrubbed comes from it being REGISTERED with the accessor** — the pattern set is only a defense-in-depth net for unregistered tokens (e.g. a raw provider error body), NOT the guarantee. This makes Phase-7 keychain discipline (every secret registered with the accessor) a *correctness* requirement, not hygiene. Redaction also recurses into nested span structures so no nested value bypasses the chokepoint.

**Rule:** route every secret through the single accessor (never into State/logs/traces; redacted `repr`/`str`); the redactor scrubs accessor `active_values` as the GUARANTEE + a best-effort pattern net — so every secret MUST be accessor-registered (Phase-7 discipline).
**Enforce:** `pin: tests/obs/test_redaction.py::test_secrets_accessor_never_persists` + `tests/obs/test_redaction.py::test_redaction_scrubs_both_errorenvelope_fields`.

## <a id="8"></a>8. Single-writer lock — a LIVE owner always holds; reclaim only a DEAD PID (no fencing yet)

**Date:** 2026-06-17. **Source slice:** 0.9 (`engine/lock.py`, §6).

The single-writer lock guards one active sidecar against a corrupting double-writer. On a single machine PID-liveness is reliably detectable, so the safe Phase-0 rule is: **a live owner PID ALWAYS holds; reclaim is gated on the owner PID being DEAD — full stop.** The heartbeat/ttl are recorded in the lock metadata but are **NOT** consulted by the reclaim gate. The tempting broader rule "reclaim on a stale heartbeat even if the PID is alive" is **unsafe without a fencing token**: a GC pause / OS swap / debugger stall can starve a heartbeat on a live, genuinely-same owner, and reclaiming its lock would put two live writers on one store. Atomic-acquire (close the acquire TOCTOU) + a fencing token (so a woken stale owner's writes are rejected) are the Phase-2 upgrade that *then* makes heartbeat-based reclaim of a hung-but-alive owner safe.

**Rule:** the single-writer lock holds for any LIVE owner PID; reclaim ONLY a dead PID (heartbeat is metadata, not a reclaim trigger) until Phase-2 adds atomic-acquire + a fencing token.
**Enforce:** `pin: tests/engine/test_supervisor.py::test_single_writer_lock_live_owner_with_stale_heartbeat_not_reclaimed`.

## <a id="9"></a>9. Graph `State` references domain by id + imports contract enums — never redefine a §12 type in `graph/`

**Date:** 2026-06-17. **Source slice:** 2.1 (`graph/state.py`, §5/§12).

The LangGraph `PipelineState` is a **graph-runtime** model, not a domain entity: it references the §12 entities **by id** and **imports** its enums (`GateKind`, `ItemState`, `StepState`) from `aisims_contracts` — it must NEVER redefine one locally in `graph/`. The landed shape is deliberately lean and references-only — `{projectId, runId, itemStates: dict[str, ItemState], providerJobRefs, gateCursor: GateKind | None}` at 2.1, growing to add `artifactRefs` + `pollErrors` (fetched scratch paths + §17 envelopes, both by step key) at 2.2 — every field an id, status enum, path, or contract-imported envelope, never an embedded entity body. This holds because of the §5 **ownership partition**: the checkpointer is authoritative for graph-execution **position only**, while the app repository (0.7 `PipelineRunRow`/`StepRow`) owns the entity rows — so State carries ids + status, not embedded bodies. Redefining a domain enum in `graph/` forks the frozen contract (the forbidden duplicate-contract pattern) and lets State + the store silently disagree. Note the import direction: a `services/pipeline` **consumer** importing `GateKind` from the `aisims_contracts` package namespace creates **no** `ipc↔domain` contracts-internal cycle, so the GateKind `ipc.py→domain.py` relocation carry-forward does **not** fire here (it fires only if a model *inside* `contracts/domain.py` needs `GateKind`).

**Rule:** graph `State` references domain entities by id and imports their enums from `aisims_contracts`; never redefine a §12 entity/enum in `graph/` (checkpoint = graph-position-authoritative only; the repo owns entity rows).
**Enforce:** `pin: tests/graph/test_state.py::test_pipeline_state_imports_contract_enums` + `::test_pipeline_state_references_entities_by_id`.

## <a id="10"></a>10. Checkpointer = PG primary + separate-module SQLite-saver fallback; SQLite=unit, PG=env-gated

**Date:** 2026-06-17. **Source slice:** 2.1 (`graph/checkpointer.py`, §5/ADR-002).

`make_checkpointer` selects `langgraph-checkpoint-postgres` as the primary saver and falls back to the **SQLite saver in a separate module** when PG is unavailable (ADR-002, the build-start verification of open-Q #4), logging only a **credential-free DSN label** — never the raw DSN/password (rule-5; `_safe_dsn`, and the rule-5 grep can't catch a raw-DSN exception, so it's pinned by a caplog test). The SQLite saver is the deterministic **unit** path (Docker-free, CI-green); the PG path is **env-gated behind `AISIMS_TEST_DATABASE_URL`** and skips cleanly when unset — mirroring the 0.7 store test-DB strategy. PG↔SQLite **parity** (same interrupt→resume run → identical final State) is asserted so the fallback is behavior-equivalent, not a degraded mode.

**Rule:** checkpointer = PG primary + separate-module SQLite-saver fallback (ADR-002); SQLite = deterministic unit path, PG = env-gated `AISIMS_TEST_DATABASE_URL`; log only a credential-free DSN label (rule-5).
**Enforce:** `pin: tests/graph/test_checkpointer.py::test_make_checkpointer_prefers_pg_falls_back_to_sqlite` + `::test_make_checkpointer_fallback_log_redacts_dsn` (rule-5 regression).

## <a id="11"></a>11. langgraph `add_node` under `mypy --strict` — localized `type: ignore[call-overload]`, never import private `StateNode`

**Date:** 2026-06-17. **Source slice:** 2.1 (`graph/build.py`, §5).

`StateGraph.add_node` with a Protocol-typed (or otherwise non-inferrable) node action can't have its `NodeInputT` inferred by `mypy --strict`, producing a `call-overload` error. The correct fix is a **localized `# type: ignore[call-overload]`** at the single `add_node` call site — **NOT** importing the private `langgraph.graph._node.StateNode` to satisfy the overload (a private symbol that can break on any langgraph minor bump). Keep the ignore narrow (the specific error code, one call site); annotate `build_graph`'s return as the public `CompiledStateGraph[...]`, not `Any`. Verified against **langgraph 1.2.5**: in this version `durability` is a **runtime** `invoke`/`stream` arg, **not** a `compile()` kwarg — so `build_graph` compiles checkpointer-only and the `'sync'` durability convention is documented for the 2.3 caller.

**Rule:** under `mypy --strict`, a Protocol-typed langgraph `add_node` needs a localized `# type: ignore[call-overload]` — never import the private `langgraph.graph._node.StateNode`; type the return as the public `CompiledStateGraph`.
**Enforce:** `pattern: from langgraph\.graph\._node import` (private-symbol import ban — added to the forbidden-patterns block); the localized ignore itself is `accepted: not mechanically pinnable beyond the import ban`.

## <a id="12"></a>12. Two-phase cloud node — `@task` idempotent submit persists the ref before any side effect; never re-submit on resume (R9)

**Date:** 2026-06-17. **Source slice:** 2.2 (`graph/cloud_node.py`, §5/§17).

A cloud stage (one that calls an async provider) runs as **two LangGraph nodes**: a `<stage>` **submit node** that wraps `provider.submit` in a langgraph `@task` (functional API) — so the submit's RESULT (the `ProviderJobRef`) is **checkpointed** — and persists that ref into `PipelineState.providerJobRefs` **before** the poll phase; then a `<stage>_poll` **reconcile node** that reads the persisted ref, polls to a terminal `PollStatus`, and `fetch()`es outputs on success (into `artifactRefs`) or surfaces the §17 envelope **unchanged** on failure (into `pollErrors`). This is the **R9** guarantee (no double-billing under replay): on resume langgraph returns the **cached** @task result instead of re-running submit, so `provider.submit` is called **exactly once** (spy-proven across a SQLite-file restart) — two layers back it, the @task result-cache AND the State-persisted ref. `durability='sync'` **at invoke** (langgraph 1.2.5 runtime arg, Lesson 11) makes the checkpoint synchronous so a crash can't lose the ref. **Scope boundary:** R9 covers no-double-**submit** only — a mid-poll resume re-polls/re-fetches (a real provider re-downloads, the Tripo 24h race), which is the **2.4 reconciler's** decision-table territory (§6), not an R9 violation. **Mechanism note (for 2.3):** langgraph differentiates **same-named `@task` closures by graph position**, so `concept`'s and `mesh`'s submit tasks don't collide in the cache — a bare `@task` is safe across stages (no per-stage name mangling).

**Rule:** cloud stages are two-phase — a `@task` idempotent submit (result-checkpointed) persists the `ProviderJobRef` into State before any side effect; the poll node reads the persisted ref; never re-submit on resume (R9 = no-double-submit; mid-poll re-fetch is 2.4's reconcile).
**Enforce:** `pin: tests/graph/test_cloud_node.py::test_no_double_submit_on_resume`.

## <a id="13"></a>13. Cloud nodes take an INJECTED provider — registry selection is the scheduler's job; never hard-code in `graph/`

**Date:** 2026-06-17. **Source slice:** 2.2 (`graph/cloud_node.py`, `graph/build.py`, §5).

A cloud node receives its provider by **injection** — `build_graph(checkpointer, *, providers: ProviderBundle | None)` where `ProviderBundle = Mapping[GateKind, CloudStageSpec]` — and `graph/` imports **no adapter module** (the provider Protocol types come from `aisims_contracts`). This keeps **rule 2** (no provider lock-in; the bakeoff intact) **structural**: the graph never names a concrete provider. `providers=None` leaves the 2.1 no-op topology untouched (prior tests stay green). The registry-based provider **selection** (config → registry → concrete adapter) is the **scheduler's job (2.3)**, not the graph's — the graph is provider-agnostic by construction. Tests inject a mock/spy provider; production injection wires at 2.3.

**Rule:** cloud nodes take an injected Protocol-typed provider via `build_graph(providers=…)`; `graph/` imports no adapter — registry selection is the scheduler's job (2.3). Never hard-code a provider in `graph/`.
**Enforce:** `pin: tests/graph/test_cloud_node.py::test_cloud_node_uses_injected_provider` + the existing rule-2 provider-lock-in forbidden-pattern grep.

## <a id="14"></a>14. Bounded-parallel engine — a `ResourceKind`-tagged cap per hot path; block-and-queue, never unbounded fan-out

**Date:** 2026-06-17. **Source slice:** 2.3 (`engine/scheduler.py`, §6).

The job/run engine bounds item work by a **`ResourceKind`-tagged cap**: cloud-submit and local-Blender-subprocess are **separate** `asyncio.Semaphore`s (REQ-NF-101) — different hot paths (network vs subprocess), so saturating one must not throttle the other (proven by a mixed batch reaching 2+2 = 4 concurrent > either single cap). Concurrency is bounded by **semaphore `acquire`** (block-and-queue on saturation — the (cap+1)th unit WAITS, never errors, never exceeds the cap), never an unbounded `gather` fan-out. Caps are human-set config knobs (`SchedulerConfig`, `ge=1`). A `WorkUnit{key, kind, run: () -> Awaitable}` tags each unit's resource kind; `run_project` returns a `dict[key, UnitResult]`. The scheduler is **distinct from the graph** (§6) — a reusable primitive over an injected async `work_fn`; the graph-driving is the caller's job (2.4 run-start integration, `WorkUnit.run` is the plug-in point). **One-active-project** is an in-memory **REJECT** guard (`ProjectBusyError`, released in `finally`) — distinct from the 0.9 on-disk single-writer lock (process-level); don't conflate.

**Rule:** bound item work by a `ResourceKind`-tagged cap (cloud-submit vs local-Blender = SEPARATE semaphores); block-and-queue via `acquire`, never an unbounded fan-out; caps are config knobs (≥1).
**Enforce:** `pin: tests/engine/test_scheduler.py::test_two_caps_are_independent` + `::test_block_and_queue_on_saturation`.

## <a id="15"></a>15. asyncio per-item failure isolation — catch `Exception`, NEVER `BaseException` (cancellation must propagate)

**Date:** 2026-06-17. **Source slice:** 2.3 (`engine/scheduler.py`, §6).

When isolating per-item failures across a concurrent batch (so one unit's error doesn't abort its siblings), capture each unit's outcome in a result map and catch **`Exception`** — **never** `BaseException`, a bare `except:`, or `gather(return_exceptions=True)` (which captures `BaseException` too). `asyncio.CancelledError` and `KeyboardInterrupt` are `BaseException`, not `Exception`: swallowing them breaks cooperative cancellation (the §17 cancel path, 2.5) and clean shutdown. So: per-unit `try: await run() except Exception as e: capture`; `UnitResult.error: Exception | None`. Any guard/lock the batch holds is released in a **`finally`** so a raised-or-cancelled run still clears it (no permanent wedge). **Open caveat (2.4):** plain `gather` leaves in-flight siblings **detached** when the batch is cancelled — once `run` holds real Blender-subprocess/cloud work (costly to orphan), the run-start wiring must wrap the batch in a `TaskGroup` / explicitly cancel siblings; mock work is harmless to orphan.

**Rule:** async per-item failure isolation catches `Exception`, never `BaseException`/bare-`except`/`gather(return_exceptions=True)` — cancellation + interrupt must propagate; release held guards in `finally`.
**Enforce:** `pin: tests/engine/test_scheduler.py::test_external_cancel_releases_guard` (real `task.cancel()` path) + the synthetic-raise isolation test.

## <a id="16"></a>16. Startup reconciler — a pure decision-table over `(poll_status, artifact_present)`; inject the FS/provider deps

**Date:** 2026-06-17. **Source slice:** 2.4 (`engine/reconciler.py`, §6).

The startup reconciler is a **pure decision-table**: `decide(poll_status, artifact_present) -> {RE_POLL, RESUME, RE_FETCH, REGENERATE}` (§6 R-e) — pollable→re-poll, succeeded+present→resume, succeeded+missing→re-fetch, expired/failed→regenerate. The driver escalates a `RE_FETCH` whose re-`fetch()` fails (or a succeeded job with no urls) to **REGENERATE** ("re-fetch then regenerate"), and a poll that **raises** → REGENERATE (the conservative human-gated "offer regenerate"; the transient-vs-terminal reclassification → RE_POLL is the §17 taxonomy's job, 2.5). Keep it **deterministic** by **injecting** the side-effecting deps — the provider (poll+fetch) and an `artifact_exists(ref) -> bool` predicate — so the table is unit-testable with no real FS/network. Per-ref **failure isolation** catches `Exception` (not `BaseException`, Lesson 15) so one ref's poll-raise doesn't abort the batch. The reconciler is **decision-only** (returns the outcome map); the transactional "step FAILED" write + the regenerate re-enqueue are the boot wiring. Stale-lock recovery **reuses** the 0.9 dead-PID-only reclaim (Lesson 8) — a LIVE owner is never reclaimed.

**Rule:** the startup reconciler is a pure `(poll_status, artifact_present) -> action` decision-table with INJECTED FS/provider deps; decision-only (returns outcomes, no writes); per-ref isolation catches `Exception`; reuse the dead-PID-only lock reclaim.
**Enforce:** `pin: tests/engine/test_reconciler.py::test_decide_*` + `::test_reconcile_refetch_then_regenerate_on_expired_urls`.
