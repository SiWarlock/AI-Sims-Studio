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
