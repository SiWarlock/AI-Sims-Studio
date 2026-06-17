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
