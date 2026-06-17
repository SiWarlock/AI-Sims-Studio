# Session contract-004 — services/pipeline Phase-0 infra tail (0.7 · 0.8 · 0.9)

- **Date:** 2026-06-17
- **Phase:** 0 (Foundations) — the `services/pipeline`-area tail; **completes Phase 0 (0.1–0.9)**
- **Track:** contract · **Area:** services/pipeline · **Branch:** track/contract
- **Predecessor:** [contract-003-2026-06-17-codegen-drift-gate.md](contract-003-2026-06-17-codegen-drift-gate.md)
- **Successor:** _(TBD — Phase-0 exit / Phase 2 once tracks fork)_

## Why this session existed

The contract track's first six slices (0.1–0.6) froze the §2.5 contract family + codegen in
`packages/contracts`. This session implemented the **`services/pipeline` infra tail** — the three
remaining Phase-0 slices that stand up the sidecar's deterministic skeletons + safety invariants
the pipeline core (Phase 2) and evals (Phase 8) build on. The orchestrator cycled
(contracts-area → pipeline-area) mid-session; the implementer persisted across all three slices.

## What was built

### 0.7 — Postgres store skeleton + Alembic + versioning (§13) — commits `379df6f`, `c500df9`, `19b1edb`
**Files created:**
- `store/db.py` — SQLAlchemy 2.0 `DeclarativeBase` + portable `json_doc()` (JSONB on PG, JSON on SQLite via `with_variant`).
- `store/models.py` — hybrid ORM rows (key cols + JSONB entity doc): `ProjectRow`/`PipelineRunRow`/`StepRow`/`SchemaMetaRow`.
- `store/repository.py` — `Repository[T]` base + `ProjectRepository` (the sole writer, rule 3).
- `store/versioning.py` — `VersionStamp`, `check_compat` (REFUSE on schema/registry mismatch), `IncompatibleStoreError`.
- `store/artifacts.py` — `commit_artifact` (write→fsync→commit-row ordering) + `canonical_path_for` (path-traversal-guarded).
- `store/migrations/runner.py` + `migrations/env.py` + `migrations/versions/0001_baseline.py` + `alembic.ini` — async Alembic baseline.
- `tests/store/*` (conftest + 5 test files).

**Files modified:** `pyproject.toml` (added sqlalchemy[asyncio]/alembic/asyncpg/aiosqlite/pydantic + a now-redundant `follow_untyped_imports` override — see follow-ups).

### 0.8 — Mock-adapter framework + failure injection (§7/§8/§9/§17) — commits `986d975`, `e2b73b6`
**Files created:**
- `adapters/mock/failure.py` — `FailurePlan`/`FailureRule`/`MockOp`, `envelope_for` (valid `ErrorEnvelope` for all 13 `ErrorCode`s), `ProviderError` (sync error channel).
- `adapters/mock/providers.py` — mock `Image3DProvider`/`ImageGenProvider`/`LLMProvider` (seeded determinism, no wall-clock, scratch-guarded `fetch`, type-driven `structured`).
- `adapters/mock/workers.py` — mock Blender/export executors (success/partial/injected-FAILED through the frozen `model_validator`s).
- `adapters/mock/__init__.py` — re-exports + a thin name→constructor factory seam (`MOCK_PROVIDERS`/`MOCK_WORKERS`; no self-registration).
- `tests/adapters/*` (3 test files).

### 0.9 — Supervisor + obs/tracing + redaction (§6/§14/§16/§17) — commits `704ef57`, `e8fe397` (SAFETY), `07dbd9f`
**Files created:**
- `engine/supervisor.py` — free-port pick, spawn, health-poll, restart-with-backoff, process-tree teardown (`start_new_session`+`killpg`).
- `engine/lock.py` — single-writer lock (owner-PID + heartbeat; **reclaim only on DEAD PID**; idempotent release).
- `obs/secrets.py` — `SecretsAccessor` protocol + `InMemorySecretsAccessor` (values never leak into repr/str).
- `obs/redaction.py` — **[rule-5 PINNED]** redactor: scrubs both `ErrorEnvelope` free-text fields (+ `suggestedAction`), value + pattern, **fail-closed**, recursive `redact_span`.
- `obs/tracing.py` — fail-open tracing seam (background queue + per-export timeout, drop-on-timeout, trace-loss counter, redact-before-export).
- `tests/engine/*` + `tests/obs/*` (3 test files).

## Decisions made
- **Hybrid persistence** (key cols relational + full pydantic entity as JSONB carrying `schemaVersion`) — cheap schema evolution vs full-relational churn (0.7).
- **Test-DB strategy** — deterministic unit layer on `sqlite+aiosqlite` (CI-green, no Docker; JSONB→JSON variant); PG integration env-gated behind `AISIMS_TEST_DATABASE_URL` (0.7).
- **Seeded determinism, no wall-clock** — every mock "random" output is a pure fn of `(seed, call-seq)`; fixed epoch for timestamps (0.8).
- **Sync error channel** — `LLMProvider.complete/structured` raise a pipeline-local `ProviderError(envelope)` (the contract has no sync error field) (0.8).
- **Lock reclaim = dead-PID only** (orchestrator TWEAK) — a live owner always holds in Phase 0 (no fencing token; a GC/swap stall must not yield two writers); heartbeat rides as metadata for Phase-2 fencing (0.9).
- **Fail-OPEN tracing vs fail-CLOSED redaction** — opposite postures, both mandatory: a trace may drop to never block a run; a secret never leaks (0.9).
- **Redaction guarantee = accessor registration**; the pattern set is best-effort defense-in-depth (0.9).

## Decisions explicitly NOT made (deferred)
- Real Postgres/Blender/@s4tk supervision + app boot → Phase 2; real LangSmith config → Phase 8; real OS-keychain accessor → Phase 7.
- Migrate-runner beyond the baseline + pre-migration on-disk-stamp compat check → Phase-2 runner.
- Registry SELECTION/self-registration of mocks + LangGraph node instrumentation → Phase 2.
- Queue/in-flight-thread bounding (drop-on-full) → Phase 8; lock atomic-acquire + fencing token → Phase 2.

## TDD compliance
**Clean — no violations.** All three slices ran strict RED → Step-2.5 (orchestrator-reviewed) → GREEN. Step-8 reviewer findings (path-traversal guard, `env.py` models import, engine-disposal, recursive `redact_span`, etc.) were folded within the GREEN/refactor loop with a covering test added for each new behavior. The rule-5 redaction pin (0.9b) is its own commit; security-reviewer ran and was **CLEAR**.

## Reachability
All Phase-0 **skeletons — NOT wired to a live run by design** (each `/tdd` Step 7.5 confirmed this). Reachable from the test suite. The redactor IS wired into the tracing exporter (0.9c). Future production entry points (→ Future TODOs):
- store `open_store`/compat-check ← supervisor/startup (0.9) + LangGraph nodes (Phase 2).
- mock providers/workers ← Phase-2 registry/factory selection + Phase-8 eval harness.
- supervisor ← app startup (Phase 2/7); tracing seam ← LangGraph nodes (Phase 2, real LangSmith Phase 8); redactor ← SSE error-event emit (Phase 2/7).

## Open follow-ups
Step-9 items were routed **hot** to the orchestrator during the session (its `/orchestrate-end` is the verify pass) — §13/§7/§8/§9/§17/§6/§14/§16 arch notes + area `CLAUDE.md` lookup rows + lessons (hybrid persistence; write-then-commit-row; seeded determinism; sync-vs-async error channel; fail-open-vs-fail-closed; secrets-accessor chokepoint; process-tree teardown). Still-open:
- **`follow_untyped_imports` override (pyproject.toml)** now redundant after D24 (`14ec0ce` shipped contracts `py.typed`) → orchestrator removes at `/orchestrate-end`.
- **0.5a `StructuredT`-export carry-forward CLOSED** (mock `structured` uses its own PEP-695 TypeVar) → orchestrator deletes the carry-forward.
- **Future TODOs (belongs-to-phase):** PG-integration-in-CI (D20/Ph0-exit); pre-migration on-disk stamp + `enforce_compat` hardening (Ph2); artifact streaming `read_bytes`→`copyfileobj` (Ph2); `ProviderError`→neutral `adapters/errors.py` (Ph3); `MockOp` FETCH-time injection (Ph2); unbounded-queue + in-flight-thread bound (Ph8); lock atomic-acquire + fencing token (Ph2); `traceRef` redaction-check when populated (Ph2); pattern-set is best-effort, accessor-registration is the guarantee (Ph7 keychain discipline).

## Notes
- Orchestrator handoff mid-session (contracts-orch → pipeline-orch) verified via team-registry + task system + lead confirmation before acting.
- Two shared-worktree git races with concurrent orchestrator commits were handled cleanly (0.8 C1 re-commit + the minimal→full `__init__` hold-aside).
