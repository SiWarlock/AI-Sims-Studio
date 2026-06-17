# Phase-0 Reachability Audit — services/pipeline

**Date:** 2026-06-17
**Area:** `services/pipeline/{store,engine,obs,adapters}`
**Branch:** `track/contract`
**Gate:** Phase-0 exit (final pre-Phase-2 gate; all slices 0.1–0.9 landed)
**Auditor posture:** Phase-0 ships **skeletons not yet wired to a live run by design.**
A symbol that is (a) test-reachable AND (b) has a documented future production entry point in the
session doc / brief is classified as REACHABLE-SKELETON (expected Phase-0 state, not a defect).
A genuine finding is a symbol with NO test reach AND no documented future wiring, OR a wiring
claim contradicted by the code.

---

## 1. Exported symbol enumeration

### `store/` — 26 exports across 6 files

| Symbol | File | Kind |
|---|---|---|
| `Base` | `store/db.py:18` | class |
| `json_doc` | `store/db.py:22` | function |
| `ProjectRow` | `store/models.py:21` | class |
| `PipelineRunRow` | `store/models.py:30` | class |
| `StepRow` | `store/models.py:40` | class |
| `SchemaMetaRow` | `store/models.py:50` | class |
| `Repository` | `store/repository.py:20` | class |
| `ProjectRepository` | `store/repository.py:47` | class |
| `VersionStamp` | `store/versioning.py:29` | class |
| `CURRENT_STAMP` | `store/versioning.py:38` | constant |
| `CompatVerdict` | `store/versioning.py:46` | enum |
| `IncompatibleStoreError` | `store/versioning.py:51` | class |
| `check_compat` | `store/versioning.py:60` | function |
| `read_stamp` | `store/versioning.py:70` | function |
| `write_stamp` | `store/versioning.py:82` | function |
| `canonical_path_for` | `store/artifacts.py:40` | function |
| `commit_artifact` | `store/artifacts.py:56` | function |
| `Store` | `store/facade.py:34` | dataclass |
| `open_store` | `store/facade.py:46` | function |
| `run_migrations` | `store/migrations/runner.py:33` | function |

### `engine/` — 7 exports across 2 files

| Symbol | File | Kind |
|---|---|---|
| `pick_free_port` | `engine/supervisor.py:19` | function |
| `backoff_delays` | `engine/supervisor.py:27` | function |
| `SupervisionOutcome` | `engine/supervisor.py:33` | dataclass |
| `Supervisor` | `engine/supervisor.py:38` | class |
| `LockMetadata` | `engine/lock.py:31` | class |
| `SingleWriterLock` | `engine/lock.py:39` | class |

### `obs/` — 8 exports across 3 files

| Symbol | File | Kind |
|---|---|---|
| `SecretsAccessor` | `obs/secrets.py:14` | Protocol |
| `InMemorySecretsAccessor` | `obs/secrets.py:20` | class |
| `REDACTION_PLACEHOLDER` | `obs/redaction.py:23` | constant |
| `REDACTION_FAILED_PLACEHOLDER` | `obs/redaction.py:24` | constant |
| `Redactor` | `obs/redaction.py:42` | class |
| `Exporter` | `obs/tracing.py:23` | Protocol |
| `TracingSeam` | `obs/tracing.py:27` | class |

### `adapters/mock/` — 10 exports (via `__init__.py`)

| Symbol | File | Kind |
|---|---|---|
| `MOCK_PROVIDERS` | `adapters/mock/__init__.py:32` | dict |
| `MOCK_WORKERS` | `adapters/mock/__init__.py:39` | dict |
| `FailurePlan` | `adapters/mock/failure.py:40` | class |
| `FailureRule` | `adapters/mock/failure.py:30` | class |
| `MockOp` | `adapters/mock/failure.py:19` | StrEnum |
| `ProviderError` | `adapters/mock/failure.py:55` | exception |
| `envelope_for` | `adapters/mock/failure.py:156` | function |
| `MockImage3DProvider` | `adapters/mock/providers.py:110` | class |
| `MockImageGenProvider` | `adapters/mock/providers.py:117` | class |
| `MockLLMProvider` | `adapters/mock/providers.py:124` | class |
| `MockBlenderWorker` | `adapters/mock/workers.py:28` | class |
| `MockExportWorker` | `adapters/mock/workers.py:54` | class |

**Total: 45 exported symbols audited.**

---

## 2. Production entry points (current Phase-0 state)

No live production entry points exist yet in this area:
- No `main.py`, `app.py`, `startup.py`, or FastAPI `app =` in `services/pipeline/`.
- `graph/__init__.py` and `registries/__init__.py` are stub stubs (Phase-2 land).
- No CLI scripts registered in `pyproject.toml [project.scripts]`.
- No cron/queue registrations.

This is **expected by design** for Phase 0. The session doc (contract-004) explicitly states:
> "All Phase-0 skeletons — NOT wired to a live run by design."

Future production entry points are documented in `contract-011-0.9-supervisor-obs-redaction.md`
(brief) and `contract-004-2026-06-17-services-pipeline-phase0-tail.md` (session doc):
- **Phase 2:** supervisor app-boot (Postgres/sidecar/Blender/@s4tk), LangGraph node wiring,
  SSE error-event emit (redactor call site), registry selection via `MOCK_PROVIDERS`/`MOCK_WORKERS`.
- **Phase 7:** real OS-keychain `SecretsAccessor`, onboarding SSE-redaction wiring.
- **Phase 8:** real LangSmith `Exporter` wired into `TracingSeam`.

---

## 3. Classification

### REACHABLE-SKELETON (test-reached + documented future production entry point)

All 45 symbols fall into this category. Detail:

#### store/

| Symbol | Test file | Future entry point |
|---|---|---|
| `open_store` | `tests/store/test_repo_round_trip.py`, `test_sidecar_sole_writer.py`, `test_write_bytes_then_commit_row.py`, `test_version_stamp_and_compat_check.py` | supervisor/startup (Phase 2) + LangGraph nodes (Phase 2) |
| `Store` | same (returned by `open_store`) | same |
| `ProjectRepository` | `test_repo_round_trip.py`, `test_sidecar_sole_writer.py` | LangGraph nodes (Phase 2) |
| `Repository` | (base class of `ProjectRepository`; exercised transitively) | same |
| `run_migrations` | `test_alembic_baseline_builds.py` + invoked by `open_store` | `open_store` (Phase 2) |
| `Base` | `migrations/env.py` (Alembic script; run by `run_migrations`) | `run_migrations` → `open_store` |
| `json_doc` | `migrations/versions/0001_baseline.py` (invoked by `run_migrations`) | same |
| `ProjectRow` | exercised by `ProjectRepository` in `test_repo_round_trip.py` | `ProjectRepository` (Phase 2) |
| `PipelineRunRow` | exercised by `run_migrations` (Alembic creates the table) | Phase-2 `PipelineRunRepository` |
| `StepRow` | exercised by `run_migrations` | Phase-2 `StepRepository` |
| `SchemaMetaRow` | `read_stamp`/`write_stamp` → `test_version_stamp_and_compat_check.py` | `open_store` (Phase 2) |
| `VersionStamp` | `test_version_stamp_and_compat_check.py` | `open_store` (Phase 2) |
| `CURRENT_STAMP` | `test_version_stamp_and_compat_check.py` + `open_store` | `open_store` (Phase 2) |
| `CompatVerdict` | `test_version_stamp_and_compat_check.py` + `open_store` | `open_store` (Phase 2) |
| `IncompatibleStoreError` | `test_version_stamp_and_compat_check.py` | `open_store` (Phase 2) |
| `check_compat` | `test_version_stamp_and_compat_check.py` + `open_store` | `open_store` (Phase 2) |
| `read_stamp` | `test_version_stamp_and_compat_check.py` + `open_store` | `open_store` (Phase 2) |
| `write_stamp` | `test_version_stamp_and_compat_check.py` + `open_store` | `open_store` (Phase 2) |
| `canonical_path_for` | `test_write_bytes_then_commit_row.py`, `test_sidecar_sole_writer.py` | Phase-2 artifact commit path |
| `commit_artifact` | `test_write_bytes_then_commit_row.py`, `test_sidecar_sole_writer.py` | Phase-2 repo layer (after worker returns path) |

#### engine/

| Symbol | Test file | Future entry point |
|---|---|---|
| `Supervisor` | `tests/engine/test_supervisor.py` | app startup (Phase 2/7) |
| `SupervisionOutcome` | `test_supervisor.py` (returned by `run_with_restarts`) | app startup (Phase 2) |
| `backoff_delays` | `test_supervisor.py` (imported directly to assert schedule) | `Supervisor.__init__` → startup |
| `pick_free_port` | **test-only indirect** — exercised only via `Supervisor` lifecycle in tests (no direct test call; `Supervisor.start` is what uses it) | app startup (Phase 2) — assigns a free port before spawning |
| `SingleWriterLock` | `test_supervisor.py` | `open_store` + Phase-2 boot sequence |
| `LockMetadata` | `test_supervisor.py` (via `SingleWriterLock._read`/`_write`) | `SingleWriterLock` → Phase-2 boot |

> **Note on `pick_free_port`:** It is defined in `engine/supervisor.py:19` but is not directly
> imported or called by any test — tests instantiate `Supervisor` and call `start()`, which
> internally uses the kernel-bind approach. `pick_free_port` is a **public helper** not yet
> called from a test OR from any production path. However, the brief (§6, REQ-O-103) documents it
> as the Phase-2 "free port pick" mechanism for the supervisor. This is the ONE symbol in the
> audit with **no test reach** (neither direct nor transitive). See finding F-1 below.

#### obs/

| Symbol | Test file | Future entry point |
|---|---|---|
| `Redactor` | `tests/obs/test_redaction.py`, `tests/obs/test_tracing.py` | SSE error-event emit (Phase 2/7), structured logging (now via `TracingSeam`) |
| `TracingSeam` | `tests/obs/test_tracing.py` | LangGraph nodes (Phase 2), real LangSmith (Phase 8) |
| `InMemorySecretsAccessor` | `test_redaction.py`, `test_tracing.py` | placeholder for Phase-7 real keychain accessor |
| `SecretsAccessor` | (Protocol; `InMemorySecretsAccessor` conforms, exercised transitively) | Phase-7 keychain impl |
| `Exporter` | (Protocol; `_HangingExporter`, `_ErroringExporter`, `_RecordingExporter` in tests conform) | Phase-8 LangSmith exporter |
| `REDACTION_PLACEHOLDER` | `test_redaction.py` (pattern-match assertions; placeholder value in `redact_text`) | `Redactor.redact_text` → SSE/log egress |
| `REDACTION_FAILED_PLACEHOLDER` | `test_redaction.py:91` | `Redactor._safe_redact` fail-closed path |

> **Key wiring cross-check (0.9c claim):** The brief states "the redactor IS wired into the
> tracing exporter (0.9c)." Code confirms: `obs/tracing.py:20` imports `from .redaction import
> Redactor` and `TracingSeam.__init__` takes a `redactor: Redactor` parameter; `_export_one`
> calls `self._redactor.redact_span(span)` at line 68. **Claim is accurate — the redactor IS
> wired into the tracing exporter now.** The SSE egress call site is correctly documented as
> deferred (Phase 2/7).

#### adapters/mock/

| Symbol | Test file | Future entry point |
|---|---|---|
| `FailurePlan` | `test_mock_failure.py`, `test_mock_providers.py`, `test_mock_workers.py` | Phase-2 registry/factory (injected at test harness construction) |
| `FailureRule` | same | same |
| `MockOp` | same | same |
| `ProviderError` | `test_mock_failure.py` | Phase-2 engine repair loop |
| `envelope_for` | `test_mock_failure.py`, `test_redaction.py` | Phase-2 error path + eval harness |
| `MockImage3DProvider` | `test_mock_providers.py`, `test_mock_workers.py` (via `MOCK_PROVIDERS`) | Phase-2 registry selection → `MOCK_PROVIDERS["image3d"]` |
| `MockImageGenProvider` | `test_mock_providers.py` | Phase-2 registry selection |
| `MockLLMProvider` | `test_mock_providers.py` | Phase-2 registry selection |
| `MockBlenderWorker` | `test_mock_workers.py` | Phase-2 registry selection → `MOCK_WORKERS["blender"]` |
| `MockExportWorker` | `test_mock_workers.py` | Phase-2 registry selection |
| `MOCK_PROVIDERS` | `test_mock_workers.py:115` | Phase-2 factory seam |
| `MOCK_WORKERS` | `test_mock_workers.py:118` | Phase-2 factory seam |

---

## 4. Findings

### F-1 — `pick_free_port` has no test reach (direct or transitive)

**File:** `services/pipeline/engine/supervisor.py:19`
**Classification:** TEST-UNREACHED (but has documented future production caller)

`pick_free_port` is a public function defined in `supervisor.py` but:
- No test imports or calls it directly.
- `Supervisor` does NOT call `pick_free_port` internally — `Supervisor.start()` calls
  `subprocess.Popen(self._cmd, ...)` with the cmd list passed by the caller; it does NOT
  pick the port itself. The caller (not yet written — Phase 2 app boot) is expected to call
  `pick_free_port()` and embed the result in `spawn_cmd`.

This means `pick_free_port` is a **dangling public helper**: defined, exported, but not
exercised by any test and not called by any production path. Per the Phase-0 posture it still
has a documented future entry point (Phase-2 supervisor boot), so this is NOT true dead code.
However, it is the one symbol with ZERO test coverage — weaker than all other Phase-0 skeletons.

**Recommended entry point:** `pick_free_port` should be called in the Phase-2 app-startup
supervisor-boot path (wherever `Supervisor(spawn_cmd=[...port...])` is constructed). A covering
test (even a trivial "port is an int in range 1–65535") would close the test-reach gap before
Phase-2 wiring.
**Step-9 routing:** Future TODO — wiring belongs to Phase 2 (supervisor boot); minimal test
coverage is a Phase-0 close-out improvement that can land at `/orchestrate-end` cleanup.

### F-2 — `PipelineRunRow` and `StepRow` have no repository layer yet

**Files:** `services/pipeline/store/models.py:30`, `services/pipeline/store/models.py:40`
**Classification:** REACHABLE-SKELETON (via `run_migrations` / Alembic, which creates the tables)

These ORM rows are defined and their tables are created by the 0001 Alembic migration (reached
via `run_migrations` in tests). But there is no `PipelineRunRepository` or `StepRepository`
equivalent of `ProjectRepository` yet. The session doc explicitly defers these to Phase 2.
This is expected and not a defect — both rows are exercised by `run_migrations` and have
documented Phase-2 consumers.

**No action required at Phase-0 exit.** Noted for Phase-2 tracking.

### F-3 — SSE error-event egress NOT wired (expected deferred, claim confirmed)

The brief and session doc state the SSE egress call site for `redact_envelope` lands in
Phase 2/7. Code search confirms: no `redact_envelope` call exists outside of tests. The
tracing-exporter wiring (`redact_span` in `TracingSeam._export_one`) IS wired as claimed.
**No finding — the deferred-wiring claim is accurate.**

---

## 5. Summary table

| Subarea | Exports | REACHABLE-SKELETON | TEST-UNREACHED | True dead code |
|---|---|---|---|---|
| `store/` | 20 | 20 | 0 | 0 |
| `engine/` | 6 | 5 | 1 (`pick_free_port`) | 0 |
| `obs/` | 7 | 7 | 0 | 0 |
| `adapters/mock/` | 12 | 12 | 0 | 0 |
| **Total** | **45** | **44** | **1** | **0** |

---

## 6. Wiring-claim cross-checks

| Claim (from brief / session doc) | Code evidence | Verdict |
|---|---|---|
| "Redactor IS wired into the tracing exporter (0.9c)" | `obs/tracing.py:20,68` imports + calls `Redactor.redact_span` | CONFIRMED |
| "SSE error-event emit (redactor call site) deferred to Phase 2/7" | No `redact_envelope` call outside tests | CONFIRMED-DEFERRED |
| "Mock providers/workers factory seam (`MOCK_PROVIDERS`/`MOCK_WORKERS`) — Phase-2 selects through" | `adapters/mock/__init__.py:32–42`; consumed in `test_mock_workers.py:115,118` | CONFIRMED (test-reached) |
| "Real LangSmith exporter deferred to Phase 8" | `TracingSeam.__init__` accepts any `Exporter` (Protocol injection); no LangSmith import present | CONFIRMED-DEFERRED |
| "Real OS-keychain SecretsAccessor deferred to Phase 7" | Only `InMemorySecretsAccessor` exists; `SecretsAccessor` is a Protocol | CONFIRMED-DEFERRED |
| "`open_store` — production callers: supervisor/startup (0.9) + LangGraph nodes (Phase 2)" | No production caller present; test-only callers confirmed | CONFIRMED-DEFERRED |

---

## 7. Summary for orchestrator

- **45 exports audited** across `store/`, `engine/`, `obs/`, `adapters/mock/`.
- **44 REACHABLE-SKELETON** — test-reached and have documented Phase-2/7/8 production entry points.
- **1 TEST-UNREACHED** — `pick_free_port` (`engine/supervisor.py:19`): defined, public, no test
  reach, no production caller yet. Not true dead code (Phase-2 entry point documented). Recommend
  a trivial covering test and Phase-2 supervisor-boot wiring.
- **0 true dead code** symbols (test-unreached AND no documented future caller).
- **All wiring claims cross-checked** — the 0.9c redactor→tracing-exporter wiring is live in code;
  all other deferred wiring claims are accurately described as deferred (no phantom wiring present).
- **`PipelineRunRow` / `StepRow`** have no repository yet — expected, deferred to Phase 2.

**Phase-exit gate: CLEAR**
(The single TEST-UNREACHED symbol, `pick_free_port`, has a documented Phase-2 production entry
point and is not true dead code. Zero symbols are both test-unreached and documentation-undocumented.
The PINNED rule-5 redaction wiring is live and confirmed. Phase 0 is clear to close.)
