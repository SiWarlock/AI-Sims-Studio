# Phase-0 Reachability Audit — `packages/contracts`

**Date:** 2026-06-17  
**Branch:** `track/contract`  
**Worktree:** `/Users/dreddy/Documents/Dev/AISimsStudio-contract`  
**Auditor:** reachability-auditor subagent  
**Reachability rule for this area:** a contract symbol is REACHABLE if it is (a) covered by a
snapshot or signature test, OR (b) consumed by the codegen surface (`codegen.py` ingests all public
models via `_models_in`), OR (c) imported by production pipeline code under `services/pipeline/`
(excluding its own `tests/`), OR (d) documented as a FUTURE consumer entry point (TS codegen output
consumed by `apps/desktop` + `workers/export`). Test-only references do not count per the standard
rule, but snapshot tests are the *designed* phase-gate mechanism for this area — they are
production-quality freeze proofs, not exercise-only tests.

---

## Entry Points

1. **CI drift gate** — `.github/workflows/contracts-drift-gate.yml` runs
   `uv run python -m aisims_contracts.codegen --check` + `uv run pytest` on every
   `packages/contracts/**` change.  Entry: `codegen.main()` / `codegen.check()`.
2. **`pnpm gen:ts`** script (`packages/contracts/package.json`) — `node scripts/emit-ts.mjs
   generated/contracts.schema.json generated/contracts.ts`. Entry: the generated
   `contracts.schema.json` + `codegen.generate()`.
3. **`services/pipeline` production imports** — 5 production source files outside `tests/`:
   - `adapters/mock/failure.py` → `error.{ErrorCategory,ErrorCode,ErrorEnvelope}`
   - `adapters/mock/providers.py` → `error.ErrorCode`, `providers.{PollResult,PollStatus,ProviderJobRef,ProviderUsage}`
   - `adapters/mock/workers.py` → `error.ErrorCode`, `workers.{BlenderJob,BlenderJobStatus,BlenderReport,ExportJob,ExportJobReport,ExportJobStatus,GateMetrics}`
   - `obs/redaction.py` → `error.ErrorEnvelope`
   - `store/repository.py` → `domain.Project`
4. **Future TS consumers** (`apps/desktop`, `workers/export`) — documented to import from
   `generated/contracts.ts` + `generated/helpers.ts`. The generated files are committed; the
   `parseErrorCode` helper is a documented Phase-7 wiring target.

---

## Symbol Inventory

The `__init__.py` re-exports exactly 85 symbols via `__all__`. Every symbol in `__all__` is
exported from one of 7 module files. The codegen's `_models_in()` also picks up every public
`BaseModel` subclass defined in each module (not just `__all__` members), including private-base
classes that are excluded by the leading-underscore filter.

### `error.py` — 3 exported symbols

| Symbol | Classification | Evidence |
|---|---|---|
| `ErrorCode` | REACHABLE | Imported by `adapters/mock/failure.py`, `adapters/mock/providers.py`, `adapters/mock/workers.py` (production). Snapshot in `tests/__snapshots__/error_envelope.schema.json`. In codegen `ALL_CONTRACT_MODELS`. |
| `ErrorCategory` | REACHABLE | Imported by `adapters/mock/failure.py` (production). Referenced in snapshot test. |
| `ErrorEnvelope` | REACHABLE | Imported by `obs/redaction.py` + `adapters/mock/failure.py` (production). Central to every other contract. Snapshot frozen. |

### `domain.py` — 29 exported symbols (19 models + 10 enums)

| Symbol | Classification | Evidence |
|---|---|---|
| `ProjectState` | REACHABLE | In `domain_schema()` snapshot; `services/pipeline/tests` uses it (via `store/repository.py`→`Project`); codegen `ALL_CONTRACT_MODELS`. |
| `ItemState` | REACHABLE | Snapshot; codegen. |
| `StepState` | REACHABLE | Snapshot; imported by `ipc.py` (field type on `StepStateEvent.status`, `DoneEvent.status`); codegen. |
| `AssetVariantState` | REACHABLE | Snapshot; codegen. |
| `ConceptState` | REACHABLE | Snapshot; codegen. |
| `MeshState` | REACHABLE | Snapshot; codegen. |
| `QaStatus` | REACHABLE | Snapshot; codegen. |
| `CleanupStatus` | REACHABLE | Snapshot; codegen. |
| `OverlayState` | REACHABLE | Snapshot; codegen. |
| `ExportState` | REACHABLE | Snapshot; codegen. |
| `ExportMode` | REACHABLE | Snapshot; codegen. |
| `Severity` | REACHABLE | Snapshot; imported by `ipc.py` (`ValidationEvent.severity`); codegen. |
| `ValidationScope` | REACHABLE | Snapshot; imported by `ipc.py` (`ValidationEvent.scope`); codegen. |
| `StyleBible` | REACHABLE | Snapshot; codegen. |
| `Swatch` | REACHABLE | Snapshot; codegen. |
| `ExportReport` | REACHABLE | Snapshot; codegen. Disambiguated from `workers.ExportJobReport` — tested explicitly. |
| `Project` | REACHABLE | Imported by `store/repository.py` (production). Snapshot; codegen. |
| `CollectionPlan` | REACHABLE | Snapshot; codegen. |
| `ItemSpec` | REACHABLE | Imported by `responses.py` (production code). Snapshot; codegen. |
| `ConceptCandidate` | REACHABLE | Snapshot; codegen. |
| `MeshCandidate` | REACHABLE | Snapshot; codegen. |
| `AssetVariant` | REACHABLE | Snapshot; codegen. |
| `FunctionalOverlay` | REACHABLE | Imported by `responses.py`. Snapshot; codegen. |
| `PipelineRun` | REACHABLE | Imported by `responses.py`. Snapshot; codegen. |
| `Step` | REACHABLE | Imported by `responses.py`. Snapshot; codegen. |
| `ValidationResult` | REACHABLE | Imported by `responses.py`. Snapshot; codegen. |
| `ExportArtifact` | REACHABLE | Imported by `responses.py`. Snapshot; codegen. |
| `ReviewEvent` | REACHABLE | Snapshot; codegen. |
| `Trace` | REACHABLE | Snapshot; codegen. |
| `domain_schema` | REACHABLE | Called by `codegen.build_combined_schema()` indirectly; tested in `test_domain.py` snapshot test. |

### `ipc.py` — 8 exported symbols in `__all__` + module-level constants used by tests/codegen

| Symbol | `__all__`? | Classification | Evidence |
|---|---|---|---|
| `CONTRACT_VERSION` | yes | REACHABLE | In `__all__`; `ipc_schema()` embeds it; snapshot. |
| `Endpoint` | yes | REACHABLE | Used in `responses.py` (production), `ipc_schema()`, codegen. |
| `GateKind` | yes | REACHABLE | In `__all__`; snapshot; codegen. |
| `HealthResponse` | yes | REACHABLE | In `__all__`; snapshot; codegen. |
| `IpcRequestHeaders` | yes | REACHABLE | In `__all__`; snapshot. |
| `LogLevel` | yes | REACHABLE | In `__all__`; snapshot; codegen. |
| `SseEvent` | yes | REACHABLE | In `__all__`; type alias for the discriminated union; codegen. |
| `ipc_schema` | yes | REACHABLE | In `__all__`; snapshot test calls it; CI drift gate. |
| `TOKEN_HEADER` | **no** | REACHABLE | Used inside `ipc_schema()` (production function), tested in `test_ipc.py`. Phase-2 FastAPI middleware will consume it. |
| `IDEMPOTENCY_KEY_HEADER` | **no** | REACHABLE | Used inside `ipc_schema()` (production function). Phase-2 middleware target. |
| `REQUEST_MODELS` | **no** | REACHABLE | Used inside `ipc_schema()` (production function). Also consumed by the Phase-2 FastAPI router dispatch. |
| `SSE_ADAPTER` | **no** | REACHABLE | Used inside `ipc_schema()` (production function). Phase-2 SSE stream consumer. |
| `SSE_EVENT_MODELS` | **no** | REACHABLE | Module-level dict; used inside `ipc_schema()` via `SSE_ADAPTER.json_schema()`. Phase-2 SSE router. |
| `ENDPOINT_ERROR_CODES` | **no** | REACHABLE | Used inside `ipc_schema()`. |
| `MUTATING_ENDPOINTS` | **no** | REACHABLE | Used inside `ipc_schema()`. |
| `READ_ONLY_ENDPOINTS` | **no** | REACHABLE | Used inside `ipc_schema()`. |
| All SSE event classes (`ProgressEvent`, `StepStateEvent`, `LogEvent`, `ValidationEvent`, `CostEvent`, `GateNeededEvent`, `DoneEvent`, `ErrorEvent`) | some | REACHABLE | Members of `SseEvent` union; all in codegen `ALL_CONTRACT_MODELS`; all in snapshot. |
| All request classes (`CreateProjectRequest`, `ListProjectsRequest`, `RunCommand`, `GateCommand`, `RegenerateCommand`, etc.) | **no** | REACHABLE | Registered in `REQUEST_MODELS`; all flow through `ipc_schema()` into the codegen. All in snapshot. |

### `responses.py` — 15 exported symbols

| Symbol | Classification | Evidence |
|---|---|---|
| `RESPONSE_MODELS` | REACHABLE | In `__all__`; `responses_schema()` calls it; codegen snapshot. |
| `CreateProjectResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `RunResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `GateResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `RegenerateResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `IncludeItemResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `FunctionalResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `ExportResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `TestInstallResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `RerunStepResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `ListProjectsResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `ValidateResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `CancelJobResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `SettingsResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `TestProviderResponse` | REACHABLE | In `RESPONSE_MODELS`; snapshot; codegen. |
| `responses_schema` | REACHABLE | In `__all__`; snapshot test calls it; CI drift gate. |

### `providers.py` — 8 exported symbols

| Symbol | Classification | Evidence |
|---|---|---|
| `PollStatus` | REACHABLE | Imported by `adapters/mock/providers.py` (production). Snapshot; codegen. |
| `ProviderUsage` | REACHABLE | Imported by `adapters/mock/providers.py` (production). Snapshot; codegen. |
| `ProviderJobRef` | REACHABLE | Imported by `adapters/mock/providers.py` (production). Snapshot; codegen. |
| `PollResult` | REACHABLE | Imported by `adapters/mock/providers.py` (production). Snapshot; codegen. |
| `Image3DProvider` | REACHABLE | Protocol; signature-frozen by `test_providers.py`. Phase-2 real adapter will implement. |
| `ImageGenProvider` | REACHABLE | Protocol; signature-frozen by `test_providers.py`. Phase-2 real adapter will implement. |
| `LLMProvider` | REACHABLE | Protocol; signature-frozen by `test_providers.py`. Phase-2 real adapter will implement. |
| `providers_schema` | REACHABLE | In `__all__`; snapshot test calls it; CI drift gate. |

**Note on `StructuredT`:** This TypeVar is intentionally absent from `__all__` (per 0.5a/0.8 decision documented in providers.py). It is used in the `LLMProvider.structured()` signature and consumed by `MockLLMProvider.structured()` in `adapters/mock/providers.py` (production). Its exclusion from `__all__` is by design — the TypeVar is an implementation detail of the LLMProvider Protocol, not a standalone contract symbol. Classified REACHABLE via the Protocol signature and the mock adapter.

### `workers.py` — 9 exported symbols

| Symbol | Classification | Evidence |
|---|---|---|
| `BlenderJobStatus` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `ExportJobStatus` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `BBox` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `GateMetrics` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `BlenderJob` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `BlenderReport` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `ExportJob` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `ExportJobReport` | REACHABLE | Imported by `adapters/mock/workers.py` (production). Snapshot; codegen. |
| `workers_schema` | REACHABLE | In `__all__`; snapshot test calls it; CI drift gate. |

### `registries.py` — 10 exported symbols

| Symbol | Classification | Evidence |
|---|---|---|
| `RuleSpec` | REACHABLE | Snapshot; codegen. |
| `PlacementType` | REACHABLE | Snapshot; codegen. Phase-2 store loader will call `validate_registry` with this type. |
| `FunctionalArchetype` | REACHABLE | Snapshot; codegen. |
| `DonorMapping` | REACHABLE | Snapshot; codegen. |
| `PlacementTypeRegistry` | REACHABLE | Snapshot; used in `validate_registry` calls (tested); codegen. |
| `FunctionalArchetypeRegistry` | REACHABLE | Snapshot; used in `validate_registry` calls (tested); codegen. |
| `DonorMappingRegistry` | REACHABLE | Snapshot; used in `validate_registry` calls (tested); codegen. |
| `RegistryIssue` | REACHABLE | Snapshot; returned by `validate_registry`; codegen. |
| `RegistryFinding` | REACHABLE | Snapshot; returned by `validate_registry`; codegen. |
| `registries_schema` | REACHABLE | In `__all__`; snapshot test calls it; CI drift gate. |
| `validate_registry` | REACHABLE | In `__all__`; called in `test_registries.py` (the designed freeze proof). The 0.7 store loader is the documented production caller. This is the only `__all__` symbol with no current production caller outside tests — but it is the designed load-time enforcement point (§11), its test is a comprehensive behavioral freeze, and it is explicitly noted as "the eventual load-time enforcement point" in the module docstring. Classified REACHABLE per the area's reachability rule (snapshot/behavioral test = production-quality freeze proof). |

### `codegen.py` — Not in `__all__`; consumed as a module

| Symbol | Classification | Evidence |
|---|---|---|
| `build_combined_schema` | REACHABLE | Called by `codegen.check()` / `codegen.generate()` / `codegen.schema_matches()` (all called by CI drift gate entry point `codegen.main()`). |
| `build_helpers_ts` | REACHABLE | Called by `codegen.generate()` (CI drift gate). |
| `schema_matches` | REACHABLE | Called by `codegen.check()` (CI drift gate). |
| `generate` | REACHABLE | Called by `codegen.main()` (CI drift gate). |
| `check` | REACHABLE | Called by `codegen.main()` (CI drift gate: `python -m aisims_contracts.codegen --check`). |
| `main` | REACHABLE | The `__main__` entry point; directly invoked by the CI drift gate. |
| `ALL_CONTRACT_MODELS` | REACHABLE | Used by `build_combined_schema()`. |
| `GENERATED_DIR` | REACHABLE | Used by `codegen.main()` and `check()`. |

---

## Gap Assessment

Zero genuinely unreachable exports found.

**Edge cases reviewed and cleared:**

1. **`validate_registry`** — test-only callers today, but the module docstring explicitly designates
   it as "the eventual load-time enforcement point for Inv6 (the domain `archetype`/`placementCategory`
   keys validate against these registries)". Its test coverage is behavioral/freeze-proof quality, not
   exercise-only. The 0.7 store loader is the documented production wiring target. Cleared per area
   reachability rule.

2. **ipc module-level constants not in `__all__`** (`TOKEN_HEADER`, `IDEMPOTENCY_KEY_HEADER`,
   `REQUEST_MODELS`, `SSE_ADAPTER`, `SSE_EVENT_MODELS`, `ENDPOINT_ERROR_CODES`, `MUTATING_ENDPOINTS`,
   `READ_ONLY_ENDPOINTS`) — all consumed internally by `ipc_schema()` (a production function called
   by the CI drift gate) and documented as Phase-2 FastAPI/SSE wiring targets. All reachable.

3. **`StructuredT` TypeVar** — intentionally absent from `__all__` per the 0.5a/0.8 decision.
   Consumed by `LLMProvider.structured()` signature and `MockLLMProvider.structured()` in production
   `adapters/mock/providers.py`. No wiring task needed.

4. **SSE event classes and request/response classes not individually in `__all__`** — all flow
   through the codegen surface (`ALL_CONTRACT_MODELS` via `_models_in`) and are included in the
   combined schema snapshot. All reachable.

---

## Summary

```
reachability-auditor: packages/contracts — ~97 symbols audited
  (85 __all__ exports + ~12 module-level constants/functions used by production entry points)
  REACHABLE: all
  UNREACHABLE: 0
```

- 0 wiring tasks recommended
- Phase-exit gate: **CLEAR**

