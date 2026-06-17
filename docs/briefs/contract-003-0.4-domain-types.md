# /tdd brief — domain_types

## Feature
Define the **domain model** (§12, Appendix A) as Pydantic v2 models in `packages/contracts/src/aisims_contracts/domain.py` — the 15 Appendix-A entities + their **state-machine enums** + the **invariants encoded as types where structurally possible** — guarded by a **§2.5-seam schema-snapshot test**. Then **complete the IPC contract** per D15: the deferred REST response bodies, the mandatory str→domain-enum tightening of 0.3's SSE fields, and the `GateKind` import. The canonical field-level domain artifact is **`docs/planning/DATA_MODEL.md`** (read it — the brief points at it rather than re-listing every field).

## Use case + traceability
- **Task ID:** 0.4
- **Architecture sections it implements:** `ARCHITECTURE.md §12` (domain model, state machines, invariants — canonical detail in `docs/planning/DATA_MODEL.md`), §4 (the IPC response bodies + tightening complete the IPC contract), §13 (Postgres-authoritative; `schemaVersion` on persisted entities), §11 (open registries — `archetype`/`placementCategory` are registry keys, NOT enums), §17 (`ValidationResult.severity` ⊃ the IPC `ValidationEvent.severity`).
- **Related context:** Phase 0, contract track. 0.1/0.2/0.3 landed (`143381a`/`c93215b`/`e7b628a`). This is the biggest contract slice — see **Step-2.5 Q0 (sequencing/size)**. TS codegen for all of it is **deferred to 0.6**. Conventions from 0.2/0.3 hold: `aisims_contracts` package, `extra="forbid"`, camelCase wire form, `StrEnum` for closed sets, schema-snapshot freeze.

## Acceptance criteria

**A. Domain entity models (§12 / DATA_MODEL.md "Core Entities")**
- [ ] Pydantic models for the 15 entities: `Project`, `CollectionPlan`, `StyleBible`, `ItemSpec`, `ConceptCandidate`, `MeshCandidate`, `AssetVariant`, `Swatch`, `FunctionalOverlay`, `PipelineRun`, `Step`, `ValidationResult`, `ExportArtifact`, `ReviewEvent`, `Trace` — fields per DATA_MODEL.md + Appendix-A. (`ExportReport` if cleanly separable — confirm at 2.5.)
- [ ] **Every persisted entity carries `schemaVersion`** (§13) — type per Q4.
- [ ] **Open-registry keys stay `str`, NOT enums** (Invariant 6, §11): `ItemSpec.archetype`, `ItemSpec.placementCategory`, `FunctionalOverlay.archetype` are registry keys (like 0.3's `FunctionalRequest.archetype`). Do NOT make them closed enums.

**B. State-machine enums (§12 / DATA_MODEL.md "State Machines")**
- [ ] Closed `StrEnum`s for each state machine: `ItemState` (13 base + audit-added: skipped/unsupported/cancelled/test-installed/in-game-verified/in-game-failed), `StepState` (8), `ProjectState`, `AssetVariantState` (candidate/selected/locked/superseded), `ConceptState`, `MeshState`, `OverlayState` (draft/validated/approved/invalid), `ExportState`. Exact membership pinned (==).
- [ ] The contract defines **states (membership)**, not transitions — the transition edges are Phase-2 engine logic. (Confirm Q2.)

**C. Invariants as types where structurally expressible (DATA_MODEL.md "Invariants")**
- [ ] Encode what the type system can hold (e.g. `AssetVariant` ref required on an export-ready item; `FunctionalOverlay.sourceItemId` = same ItemSpec identity, Invariant 2; ≥1 `Swatch` on an exportable variant, Invariant 7). Cross-entity/runtime invariants (exportable = included ∧ selected variant ∧ no blockers, Invariant 1; ordered gates, Invariant 5) are **documented + validator-shaped**, enforcement in Phase-2 — do NOT over-encode. (Confirm depth at Q3.)

**D. Complete the IPC contract (D15 — depends on the new domain enums)**
- [ ] **IPC REST response bodies** for the 14 §4 endpoints (embed the domain entities). Placement per Q5.
- [ ] **str→domain-enum tighten** 0.3's SSE fields (snapshot-affecting, deliberate): `StepStateEvent.status` → `StepState`; `DoneEvent.status` → the PipelineRun terminal subset; `ValidationEvent.severity` → `ValidationResult.severity` enum; `ValidationEvent.scope` → the scope enum. Regenerate `ipc.schema.json`.
- [ ] `GateKind` **imported** from `aisims_contracts.ipc` where the domain gate model needs it — NOT redefined (no duplicate §2.5-seam enum).

**E. Freeze + preflight**
- [ ] **Schema-snapshot test** (§2.5-seam): `domain.schema.json` over the domain surface, tagged `spec(§12)`. A drift is the failure. The IPC snapshot re-freezes with the tightened fields.
- [ ] State-enum membership tests (exact ==), schemaVersion-present test, the structural-invariant tests, JSON round-trip, boundary rejection (`extra="forbid"`).
- [ ] `/preflight` clean.

## Wiring / entry point (Step 7.5)
Domain types are frozen contract models; their runtime use (the store repo layer writing/reading them, the engine driving the state machines) lands in **Phase 2 + 0.7 (store)**. Reachability surface this slice = the schema-snapshot tests + importability from `aisims_contracts.domain`. Runtime wiring: `none — wiring lands in 0.7 (store) + Phase 2 (engine) + 0.6 (TS codegen)`.

## Files expected to touch
**New:** `packages/contracts/src/aisims_contracts/domain.py`, `packages/contracts/tests/test_domain.py`, `packages/contracts/tests/__snapshots__/domain.schema.json`.
**Modified (by the implementer, its slice files):** `ipc.py` (response bodies + str→enum tighten + GateKind import), `test_ipc.py` + `ipc.schema.json` (re-frozen), `__init__.py` (domain exports). REST responses may live in `ipc.py` or a new `responses.py` — Q5.
**Modified (orchestrator territory — flag at Step 9, do not edit):** `ARCHITECTURE.md`/`CLAUDE.md`/`IMPLEMENTATION_PLAN.md`.

## RED test outline (Step 2)
1. `test_domain_models_present` — the 15 entities exist + carry `schemaVersion`.
2. `test_state_enum_membership` — each state `StrEnum`'s members == the DATA_MODEL set (exact ==, esp. Item-13 + audit-added, Step-8).
3. `test_open_registry_keys_are_str` — `ItemSpec.archetype`/`placementCategory` + `FunctionalOverlay.archetype` are `str`, not enums (Invariant 6 guard).
4. `test_structural_invariants` — the type-expressible invariants (overlay same-identity ref; export-ready requires a selected variant ref; ≥1 swatch) hold + reject violations.
5. `test_ipc_responses_present` — a response model per the 14 endpoints; embeds the right domain entity.
6. `test_ipc_sse_fields_tightened` — `StepStateEvent.status`/`DoneEvent.status`/`ValidationEvent.severity`+`scope` are now the domain enums (not str); `GateKind` is imported (single definition).
7. `test_domain_round_trip` + `test_boundary_rejection` (`extra="forbid"`).
8. `test_domain_schema_snapshot` *(§2.5-seam guard)* — `domain.schema.json`, tagged `spec(§12)`; and the re-frozen `ipc.schema.json` reflects the tightened fields.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **NEW models:** 15 domain entities + the state enums (all §2.5-seam, shared A↔B). **CHANGED:** the IPC contract (response bodies added; SSE str fields tightened to domain enums — a deliberate snapshot change).
- **Orchestrator doc rows (Step 9):** add the **domain** row + the state-enum set to `packages/contracts/CLAUDE.md` cross-doc table with `pin: tests/test_domain.py::test_domain_schema_snapshot`; update the **IPC** row to note the response bodies + tightened fields; confirm/extend the Appendix-A §12 rows == shipped models.
- **§2.5-seam touched?** YES — domain models + the IPC re-freeze. Both schema-snapshots mandatory this cycle.

## Things to flag at Step 2.5
0. **(SIZE/SEQUENCING — load-bearing) 0.4 is the biggest slice.** Propose a GREEN sequence + commit split: (A, my default) ONE slice, multi-commit — C1 entity models + state enums; C2 invariants-as-types; C3 the IPC completion (responses + tighten + GateKind). If you judge it too large to review/freeze cleanly as one, say so and I'll split into 0.4a (domain) + 0.4b (IPC completion) with the lead — surface your read.
1. **State machines = states only, not transitions** (transitions are Phase-2 engine). Confirm.
2. **Invariants-as-types depth** — which invariants become types (structural) vs documented+validator (cross-entity/runtime)? My default: structural ones as types (Inv 2, 7, the export-ready variant ref); Inv 1/5 (exportable predicate, ordered gates) documented + validator-shaped, enforced Phase-2. Don't over-encode. Surface your line.
3. **`schemaVersion` type/default** — `int` (e.g. `1`) vs str. My default: `schemaVersion: int = 1` per model.
4. **IPC response-body placement** — in `ipc.py`, or a new `responses.py` (responses embed domain → a module that imports both ipc + domain)? My default: a new `responses.py` (clean: it depends on both ipc + domain; keeps ipc.py domain-independent as 0.3 froze it). Confirm.
5. **str→enum tighten exact mappings** — confirm `DoneEvent.status` maps to which subset (PipelineRun terminal: succeeded/failed/cancelled?) and `ValidationEvent.scope` → the `ValidationResult.scope` enum {project,item,mesh,overlay,export}.
6. **Registries out of 0.4** — `PlacementType`/`FunctionalArchetype`/`DonorMapping` are **0.5** (registry contracts), NOT 0.4; `archetype`/`placementCategory` are registry-key `str`s here. Confirm.

## Dependencies + sequencing
- **Depends on:** 0.1; 0.2 (ValidationResult/Step reference ErrorEnvelope via `error?`); 0.3 (the IPC completion tightens 0.3's SSE fields + imports `GateKind`).
- **Blocks:** 0.5 (provider/worker/registry contracts reference domain), 0.6 (codegen consumes both snapshots → TS), 0.7 (store persists these), Phase 2 (engine).

## Estimated commit count
**2–3** (per Q0). Suggested: `feat(contracts): domain entity models + state machines (§12)`; `feat(contracts): invariants-as-types + domain snapshot`; `feat(contracts): complete IPC contract — REST responses + SSE field tightening + GateKind (D15)`. The domain snapshot + the IPC re-freeze may force a particular grouping (cite the bisectability argument like 0.3 if so).

## Lessons-logged candidates anticipated
- Convention — open-registry keys are `str` (registry-validated), never closed enums, even when a finite set is "known today" (Invariant 6).
- Convention — the contract encodes state-machine STATES (membership-pinned), not transitions (engine territory).
- Carry-forward — 0.6 codegen consumes `domain.schema.json` + the re-frozen `ipc.schema.json` → TS.

## How to invoke
1. Read this brief + **`docs/planning/DATA_MODEL.md`** (the canonical field/state/invariant detail) end-to-end.
2. `/tdd domain_types` (continuing session; no `/session-start`).
3. Step 2.5 — answer **Q0 (size/sequencing)** + Q1–Q6; surface your reads (Q0 + Q2 are load-bearing). Wait for `APPROVED.` before GREEN.
4. Step 9 — surface the domain + IPC cross-doc rows + the re-freeze + lessons.
