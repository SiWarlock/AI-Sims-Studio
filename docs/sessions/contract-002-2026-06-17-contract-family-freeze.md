# Session contract-002 — §2.5 contract family freeze (0.4b · 0.5a · 0.5b · 0.5c)

- **Date:** 2026-06-17
- **Phase / track:** Phase 0 (Foundations & frozen contracts) · track `contract` · area `packages/contracts`
- **Predecessor:** [contract-001](contract-001-2026-06-17-phase-0-frozen-contracts.md) — scaffold + ErrorEnvelope/IPC/domain (0.1–0.4a)
- **Successor:** [contract-003](contract-003-2026-06-17-codegen-drift-gate.md) — py→ts codegen + CI drift gate (0.6)

## Why this session existed
Complete the §2.5 frozen-contract family on top of contract-001's error/ipc/domain: finish the IPC
contract (0.4b), then freeze the three remaining §2.5 seams — provider adapters (0.5a §7), worker
job/report envelopes (0.5b §8/§9), and the registries + load-time validator (0.5c §11). Landing
0.5c freezes the whole family so other tracks can fork off stable contracts before 0.6 codegen.

## What was built

### Files created
- **`src/aisims_contracts/responses.py` (0.4b):** the 14 §4 REST response models (each embedding its
  0.4a domain entity) + `RESPONSE_MODELS` registry + `responses_schema()`.
- **`src/aisims_contracts/providers.py` (0.5a):** 3 model-agnostic `Protocol` interfaces
  (`Image3DProvider`/`ImageGenProvider`/`LLMProvider`) + value models (`ProviderJobRef`,
  `PollResult`, `ProviderUsage`, `PollStatus`) + `providers_schema()`.
- **`src/aisims_contracts/workers.py` (0.5b):** `BlenderJob`→`BlenderReport` (+ `GateMetrics`, `BBox`),
  `ExportJob`→`ExportJobReport`, worker status enums, the status↔outputs `model_validator`, `workers_schema()`.
- **`src/aisims_contracts/registries.py` (0.5c):** 3 open-registry entry models + flexible `RuleSpec` +
  3 versioned collection wrappers (`_RegistryFile` base, `@abstractmethod entry_keys()`) + `RegistryIssue`/
  `RegistryFinding` + the pure `validate_registry` load-time validator + `registries_schema()`.
- **`tests/conftest.py` (0.5a):** the shared `intra_imports` fixture (hoisted from test_responses.py).
- **Tests + snapshots:** `tests/test_{responses,providers,workers,registries}.py` +
  `tests/__snapshots__/{responses,providers,workers,registries}.schema.json`; additions to `tests/test_ipc.py`.

### Files modified
- **`src/aisims_contracts/ipc.py` (0.4b):** tightened the 4 domain-typed SSE fields `str`→domain enums
  (`StepStateEvent.status`→`StepState`; `DoneEvent.status`→`Literal[SUCCEEDED,FAILED,CANCELLED]`;
  `ValidationEvent.severity`→`Severity`; `.scope`→`ValidationScope`); now imports the 3 domain enums.
- **`tests/__snapshots__/ipc.schema.json` (0.4b):** re-frozen (the 4 retypes + the 3 enum `$defs`).
- **`tests/test_responses.py` (0.5a):** swapped its local `_intra_imports` for the conftest fixture.
- **`src/aisims_contracts/__init__.py`:** re-exports for every new contract (4 slices).

### Commits (mine, on `track/contract`)
`35f1a2e` feat(contracts) IPC SSE tighten [0.4b C1] · `7d701a6` feat(contracts) IPC response bodies [0.4b C2] ·
`de7caee` feat(contracts) provider adapters [0.5a] · `ccce712` feat(contracts) worker contracts [0.5b] ·
`818024d` feat(contracts) registry contracts [0.5c]. 62 tests green; mypy --strict + ruff + ruff format clean.

## Decisions made
- **0.4b (D15):** REST response bodies = a named model per endpoint embedding the domain entity
  (REQUEST_MODELS symmetry); `DoneEvent.status` = `Literal[StepState members]` (clean enum schema, no
  duplicate enum). **Commit order swapped** to C1=tighten/C2=responses — C1=responses would have left
  `test_import_direction` red (it asserts `domain ∈ ipc imports`, true only post-tighten). `ipc.py`
  graduates from "domain-independent" to importing the 3 SSE enums (acyclic `ipc → domain`).
- **0.5a (§7):** `Protocol` (structural; `@runtime_checkable` omitted, YAGNI). `submit` first-arg
  diverges by provider — `Image3D.submit(image: bytes)` vs `ImageGen.submit(prompt: str)` (ImageGen is
  text-to-image); the signature test freezes the param names. LLM `complete/structured` return raw
  (`str`/`StructuredT`); latency/cost recorded at the node onto domain `Step`, not a contract wrapper.
  `params: dict[str,Any]` = the open §7 seam (Inv6 analogue). Protocols frozen by a **signature test**
  (no JSON schema); value models by the snapshot. `ProviderUsage.latencyMs/costCents` got `ge=0` (review).
- **0.5b (§8/§9):** §9 worker report renamed `ExportReport`→**`ExportJobReport`** (the §12 domain
  `ExportReport` owns the name — never re-freeze the landed contract). All artifact fields are
  scratch-path `str` refs (`min_length=1`), never inline bytes (rule 3). A `model_validator` pins
  status↔outputs consistency (rule 6): Blender succeeded⟹geom+gateMetrics+error-None / failed⟹error;
  Export succeeded⟹packagePath+error-None / partial⟹packagePath (error optional) / failed⟹error.
  Worker-local status enums (not domain `ExportState`).
- **0.5c (§11):** entry envelopes frozen + flexible `RuleSpec{kind,params}` (the rule grammar is
  S3-pinned — not over-specified). Per-registry `{registryVersion:int, entries}` wrappers. Pure
  `validate_registry(raw, type)` = structural + version + id/key uniqueness ONLY → `RegistryFinding`
  (granular `issue` + §17 `ErrorEnvelope`). `eligibilityRules` (not `eligibilityPredicate`).
- **Cross-slice:** the `intra_imports` AST helper hoisted to `tests/conftest.py` (0.5a) so 0.5b/0.5c
  reuse it via a fixture instead of copying.

## Decisions explicitly NOT made (deferred)
- **Inv1 (full exportability gate) + Inv5 (ordered gates)** → Phase-2 engine validator (D16 pins).
- **Q5 GateKind import-DAG (Phase-2):** now that `ipc → domain`, a future Phase-2 domain *gate model*
  importing `GateKind` from `ipc` would cycle → move `GateKind` to `domain`/a neutral shared-enums
  module THEN. `test_import_direction` guards the DAG so the cycle would be caught.
- **`StructuredT` package-level export** → decided at 0.8 (adapters implementing the Protocol don't need it).
- **`min_length=1` on registry `id`/`key`/`name`** + **BBox `minCorner≤maxCorner`** + **N=3 duplicate
  test** → deferred (the orchestrator folded the empty-string-key guard into its snapshot-hardening
  carry-forward; BBox inversion is worker-impl/geometric).
- **TS/Node codegen** for all contracts → 0.6.

## TDD compliance
Clean. All four slices followed RED → Step-2.5 pause (orchestrator review; 0.5b drew a TWEAK adding the
status↔outputs validator, 0.5c an ADD for the `RegistryIssue` membership test) → GREEN → reviewers →
Step-9 → commit. No violations. No implementation-before-test.

## Reachability
All frozen-contract surfaces, **not runtime-wired by design** — importability from `aisims_contracts.*`
+ the `spec()`-tagged schema snapshots, plus (0.5a) the interface-signature freeze test and (0.5c) the
pure `validate_registry` (unit-reachable, verified end-to-end from the package root). Runtime callers
land later: Phase-2 routes/engine/cloud-nodes, the 0.7 store loader (registries + persisted entities),
0.6 TS/Node codegen, 0.8 mock adapters. No tested-but-unwired gaps.

## Cross-doc invariant audit
Multi-track memory check: every model field change was flagged at Step 9 and the orchestrator confirmed
receipt + is hot-routing — IPC SSE union CHANGED + new `responses.py` (0.4b); new `providers.py` (0.5a);
new `workers.py` + the §9/Appendix-A `ExportReport`→`ExportJobReport` rename (0.5b); new `registries.py`
+ the §11/Appendix-A `eligibilityPredicate`→`eligibilityRules` reconcile (0.5c). The cross-doc rows +
arch edits ride the orchestrator's `/orchestrate-end` round commit (working tree shows `CLAUDE.md`/
`LESSONS.md`/`ARCHITECTURE.md` modified = its territory). No undocumented drift.

## Open follow-ups
- **0.6 codegen** consumes `{error,ipc,responses,domain,providers,workers,registries}.schema.json` → TS
  (UI) + Node (@s4tk export worker) with a CI drift gate. Note the per-model `$defs` dedup (`ExportReport`
  appears standalone + inlined under `ExportArtifact`; `ExportJobReport` is distinct — no collision).
- **Phase-2 pins (D16):** Inv1 + Inv5 in the engine validator; the GateKind import-DAG move when a domain
  gate model lands; the engine maps worker status enums onto domain `ExportState` + records LLM
  latency/cost onto `Step`.
- **0.7 store loader** is `validate_registry`'s production caller (Inv6 load-time enforcement point).
- **0.8** decides `StructuredT` export; mock adapters implement the §7 Protocols.
- **Snapshot-hardening carry-forward (orchestrator-held):** `min_length=1` on ref/key fields across
  providers/domain/registries; the value-model-set assertion pattern (in 0.5b/0.5c).
- **Lessons (orchestrator banks at close-out):** str-now→pinned-tighten (0.3→0.4b); Protocol-freeze-via-
  signature-test + open-`params` Inv6 analogue (0.5a); `Test*`/pytest-collection gotcha; cross-seam
  name-collision (rename the later seam) + worker-report safety shaping (refs + the consistency validator,
  rules 3/6) (0.5b); registry envelope-frozen/grammar-flexible + a contract package shipping a pure
  validator function (0.5c).

## How to use what was built
`from aisims_contracts import …` for any frozen contract (all re-exported via `__init__`). To evolve a
seam: edit the pydantic model, then deliberately regenerate its `*.schema.json` snapshot (review the
diff — a drift is the failure, never a blind regen). `validate_registry(raw_config, PlacementTypeRegistry)`
returns `[]` for a valid registry config or a list of `RegistryFinding`s.
