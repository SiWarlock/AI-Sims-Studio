# /tdd brief — store_skeleton

## Feature
Stand up the **§13 Postgres store skeleton**: the sidecar **repository layer** (the SOLE writer of Postgres +
the canonical artifact tree — safety rule 3), an **Alembic baseline**, the **data-dir version stamp + startup
compat check** (`schemaVersion`/`registryVersion`), and the **write-bytes-then-commit-row** artifact-ordering
helper. Phase-0 skeleton — the store scaffold + its invariants, NOT the full per-entity persistence or business logic.

## Use case + traceability
- **Task ID:** 0.7  *(first `services/pipeline`-area slice — area switch from `packages/contracts`)*
- **Architecture sections it implements:** `ARCHITECTURE.md §13` (data store & artifacts — Postgres + Alembic;
  artifacts = files on disk, canonical layout, **write-bytes-then-commit-row**; the **sidecar repo layer is the
  only writer**; migration & versioning — `schemaVersion`/`registryVersion` stamps + a migration runner on
  project-open), §6 (the engine repo layer commits the row after a worker returns a path — sole-writer boundary),
  §12 (the frozen domain entities, 0.4a, are what the store persists).
- **Related context:** Phase 0, contract track (this track owns all of Phase 0; 0.1–0.6 were `packages/contracts`,
  0.7–0.9 are `services/pipeline`). The 7 §2.5 contracts are FROZEN + on origin (`18195d6`) — the store imports the
  domain entities from `aisims_contracts.domain`, never redefines them. Area conventions (`services/pipeline/CLAUDE.md`):
  `mypy --strict`, Pydantic v2, **forbidden-pattern 4** (a worker must NEVER write Postgres/the canonical tree — the
  repo layer commits the row after the worker returns a path; `pin: tests/store/test_sidecar_sole_writer.py`),
  forbidden-pattern 5 (secrets only in the OS keychain, never DB/logs/traces).

## Acceptance criteria (what "done" means)

**A. Repository layer (§13 — sidecar = sole writer, rule 3)**
- [ ] A `services/pipeline/store/` repository layer that reads/writes the frozen domain entities (0.4a) to Postgres —
  the **only** writer of Postgres + the canonical artifact tree. Pattern + scope per Q2 (skeleton = the base + ≥1
  concrete repo, e.g. `Project`).
- [ ] DB access + the persistence model per Q1 (ORM + relational-vs-JSONB). The entity carries `schemaVersion` (0.4a).

**B. Alembic baseline (§13)**
- [ ] An Alembic baseline migration creating the skeleton tables (Q3) + the `schema_meta`/version-stamp table. `alembic
  upgrade head` on an empty DB produces the schema; `migrations/` wired.

**C. Versioning — data-dir stamp + startup compat check (§13, R-i)**
- [ ] A version stamp (`schemaVersion` + `registryVersion` + app/data-dir version) persisted (Q5) + a **startup
  compat check** on open that compares the stamped version against current and surfaces an incompat (migrate or
  refuse) — never silently open an incompatible store. (Forbidden-pattern: never DROP a version stamp.)

**D. Write-bytes-then-commit-row ordering (§13)**
- [ ] A helper enforcing the artifact-write ordering: write bytes → `fsync` → **then** commit the DB row referencing
  the path, so a crash leaves an **orphan file, never a dangling ref** (Q6). Canonical layout by project/item/candidate.

**E. [SAFETY — rule 3] Sole-writer invariant**
- [ ] **`pin: tests/store/test_sidecar_sole_writer.py`** — the repo layer is the sole writer of Postgres + the
  canonical tree; workers write only sidecar-provided scratch + return paths (the engine repo commits the row). This
  is a **safety-invariant pin → its OWN commit** (never bundled); security-reviewer runs at Step 8.

**F. Tests + preflight**
- [ ] Deterministic tests: a repo round-trip (write entity → read back == ); `alembic upgrade head` builds the schema;
  the compat check accepts a matching stamp + refuses/flags a mismatch; the write-ordering helper commits the row only
  after the bytes are durable (+ leaves an orphan, not a dangling ref, on a simulated mid-write crash); the sole-writer
  pin (E). `/preflight` clean (**`uv sync --all-packages`** from workspace root — D19).

## Wiring / entry point (Step 7.5)
`none wired to a live run yet — Phase-0 skeleton.` The repo layer's production callers are the LangGraph nodes
(Phase 2) + the supervisor/startup (0.9 + Phase 2 runs the compat check on project-open). Reachability surface this
slice = the repo round-trips against a test Postgres, `alembic upgrade head` builds the schema, the compat-check +
write-ordering helpers are unit-reachable. (If a real Postgres isn't available in the test env, use a containerized/
ephemeral PG or the project's test-DB fixture — flag the approach at Q7.)

## Files expected to touch
**New:**
- `services/pipeline/store/*` — the repository layer (DB engine/session, base + concrete repos), the version-stamp +
  compat-check, the write-ordering helper.
- `services/pipeline/migrations/*` (Alembic env + the baseline revision) + `alembic.ini` (or pyproject config).
- `services/pipeline/tests/store/*` — incl. `test_sidecar_sole_writer.py` (E).
**Modified:**
- `services/pipeline/pyproject.toml` — add SQLAlchemy/Alembic/the PG driver (+ a test-DB dep, Q7).

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `services/pipeline/tests/store/`
1. **`test_repo_round_trip`** — write a domain entity (e.g. `Project`) via the repo, read it back == (incl. `schemaVersion`). Why: §13 repo layer.
2. **`test_alembic_baseline_builds`** — `alembic upgrade head` on an empty DB creates the skeleton schema + `schema_meta`. Why: §13 Alembic.
3. **`test_version_stamp_and_compat_check`** — a matching stamp opens; a mismatched `schemaVersion`/`registryVersion` is refused/flagged. Why: §13 R-i.
4. **`test_write_bytes_then_commit_row`** — the helper commits the row only after bytes are fsynced; a simulated mid-write crash leaves an orphan file, NOT a dangling row. Why: §13 ordering.
5. **`test_sidecar_sole_writer`** *(SAFETY, rule 3)* — the repo layer is the sole writer; a worker-style path doesn't write Postgres/the canonical tree. Why: rule 3 / forbidden-pattern 4.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none to the frozen contracts (the store CONSUMES `aisims_contracts.domain`, never redefines).
  The persistence model (Q1) is a `services/pipeline` concern, not a §2.5 seam.
- **Orchestrator doc rows to write hot (Step 9):** add a `services/pipeline/CLAUDE.md` lookup-table row (store → §13);
  any new store-area lesson (e.g. the persistence-model choice, the write-ordering pattern).
- **§2.5-seam touched?** No (the store is an area-internal layer). The **rule-3 sole-writer** is a safety invariant —
  its pin (E) is mandatory + gets its own commit.

## Things to flag at Step 2.5
0. **(SIZE — load-bearing) split.** This is large for one slice. My default: **split 0.7a/0.7b/0.7c** — 0.7a
   (DB engine + persistence model + the repo-layer skeleton + Alembic baseline), 0.7b (versioning: stamp + startup
   compat check), 0.7c (write-bytes-then-commit-row + the **sole-writer safety pin** as its own commit). 0.7a first
   (the persistence model gates everything). Confirm or propose your split.
1. **(LOAD-BEARING) Persistence model + DB access.** My default: **SQLAlchemy 2.0 (async) + Alembic** with a **hybrid**
   row — key columns (`id`, `projectId`, `status`, `schemaVersion`) relational/indexed + the full pydantic entity as a
   **JSONB** column (the JSONB carries the versioned model; cheap to evolve under `schemaVersion`). Alternatives: full
   relational mapping (a column per field — heavy, churns on every model change) or raw `asyncpg` (no Alembic pairing).
   This is the foundational call — surface your read (and verify the SQLAlchemy 2.0 async + Alembic API via Context7).
2. **Repo-layer pattern.** My default: a typed base `Repository[T]` (get/put/list by id) + ≥1 concrete repo (`Project`)
   for the skeleton; the rest land as their entities are needed (Phase 2). The repo layer is the SOLE writer (rule 3).
   Confirm.
3. **Alembic baseline scope.** My default: the skeleton tables only (`project`, `pipeline_run`, `step`, + `schema_meta`)
   — establish the pattern, not all 16 entities. Confirm which tables seed the baseline.
4. **Version stamp location + compat policy.** My default: a `schema_meta` table (`schemaVersion`, `registryVersion`,
   appVersion, dataDirVersion) + an on-disk stamp for the data dir; the startup check **refuses** to open on a
   major-mismatch (migrate path is the runner, deferred) and logs a minor one. Confirm the refuse-vs-migrate policy.
5. **Write-ordering helper shape.** My default: `commit_artifact(scratch_path, canonical_path, row, repo)` → move/write
   bytes into the canonical layout → `fsync` → commit the row; on failure, the bytes orphan (a sweeper reclaims them
   later, deferred). Confirm.
6. **Out of scope (confirm):** the LangGraph checkpointer (the Phase-2 orchestration layer — though it shares the DB); full per-entity
   repos for all 16 entities (land as Phase-2 needs them); the actual migration RUNNER logic beyond the baseline +
   compat check (Phase 2); business logic / state-machine transitions (Phase 2).
7. **Test-DB approach.** How does the test suite get a Postgres (containerized/ephemeral PG, a session-scoped fixture,
   or SQLite-for-unit + PG-for-integration)? Surface your read — it shapes the test wiring + the CI job.

## Dependencies + sequencing
- **Depends on:** 0.4 (the domain entities the store persists — frozen, on origin). Independent of 0.5/0.6 (the store
  doesn't consume providers/workers/registries or the codegen).
- **Blocks:** Phase 2 (the engine's repo writes + the checkpointer share this DB), 0.9 (the supervisor runs the
  compat check on startup).

## Estimated commit count
**2–4** (per Q0 — I lean split). At minimum the **sole-writer safety pin (E) is its OWN commit** (never bundled).
Suggested if split: 0.7a (persistence + repo + Alembic), 0.7b (versioning), 0.7c (write-ordering + sole-writer pin).

## Lessons-logged candidates anticipated
- **Convention candidate** — the persistence model (hybrid relational + JSONB-carrying-the-versioned-entity) + why
  (cheap schema evolution under `schemaVersion` vs full relational churn).
- **Convention candidate** — write-bytes-then-commit-row: a crash must leave an orphan file, never a dangling row;
  the helper enforces the ordering.
- **Architecture-doc note candidate** — record the store's persistence model + the sole-writer enforcement point
  (the repo layer; `test_sidecar_sole_writer`) in §13 / the area `CLAUDE.md`.

## How to invoke
1. **Fresh `services/pipeline` implementer — run `/session-start`** (orient on `services/pipeline/CLAUDE.md` + LESSONS +
   the area stack), then read this brief + `ARCHITECTURE.md §13` (+ §6 sole-writer boundary). **Context7** the
   SQLAlchemy 2.0 (async) + Alembic API before Step 2.5.
2. **`/tdd store_skeleton`**.
3. **Step 2.5** — answer Q0–Q7 (Q0 split + Q1 persistence model are load-bearing; Q4/E is the safety pin); coverage
   map. Wait for `APPROVED.` before GREEN.
4. **Step 9** — surface the store lookup-table row + the persistence-model lesson + the sole-writer pin.
