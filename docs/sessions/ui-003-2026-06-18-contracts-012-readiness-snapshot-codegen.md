# Session ui-003 — contracts-012: additive GET /readiness + 0.5b snapshot-hardening + codegen IPC-catalog

- **Date:** 2026-06-18
- **Phase:** Post-Phase-0 contracts micro-slice (plan task 0.10 — waived task-ID, added to `main` at integration per the batch-at-integration doc-edit policy)
- **Track / branch:** `ui` / `track/contract-readiness` (worktree `AISimsStudio-contract-readiness`, forked off frozen `track/contract`)
- **Predecessor:** `docs/sessions/contract-004-2026-06-17-services-pipeline-phase0-tail.md`
- **Successor:** _(none yet)_

## Why this session existed

The user chose **F1=B** — re-open the frozen §4 IPC contract **additively** — to give Phase-7 Onboarding a real system-readiness surface, with the lead driving a batched contracts micro-slice on a dedicated branch that then propagates to the `ui` track. Phase 0's contract team had wound down, so `ui-contracts-implementer` was stood up to execute one batched, ADDITIVE-only `packages/contracts` micro-slice.

## What was built

Three independent, additive contract-package items (3-commit bundle).

### Files created
- `packages/contracts/generated/ipc-catalog.ts` — the §4 IPC endpoint/protocol catalog emitted to deterministic TS (endpoint `METHOD path` values, mutating/read-only partition, header names, contractVersion) so a later UI slice imports it instead of the hand-authored, drift-guarded `endpoints.ts` (ledger T3).
- `docs/briefs/contract-012-readiness-snapshot-codegen-batch.md` — the orchestrator-authored brief, placed into this worktree so it rides the slice commits (committed `8eb1d2a`).
- `docs/sessions/ui-003-2026-06-18-contracts-012-readiness-snapshot-codegen.md` — this doc (renumbered ui-001→ui-003 at the track/contract-readiness→track/ui merge; ui-001=detection-vertical, ui-002=impl cycle-1).

### Files modified
- `src/aisims_contracts/ipc.py` — `Endpoint.READINESS = "GET /readiness"`; `ReadyState`/`ReadinessSubsystem` StrEnums; `ReadinessRequest` (no-body); wired `REQUEST_MODELS` / `READ_ONLY_ENDPOINTS` / `ENDPOINT_ERROR_CODES = {SYSTEM}`; docstrings 14→15.
- `src/aisims_contracts/responses.py` — `ReadinessCheck`/`ReadinessReport` models; `RESPONSE_MODELS[READINESS]`; docstring 14→15.
- `src/aisims_contracts/__init__.py` — export `ReadyState`, `ReadinessSubsystem`, `ReadinessCheck`, `ReadinessReport` (for the Phase-2 sidecar route).
- `src/aisims_contracts/providers.py` — `min_length=1` on `ProviderJobRef.{provider,model,jobId}`.
- `src/aisims_contracts/workers.py` — `min_length=1` on `BlenderJob.{meshPath,jobId}`, `ExportJob.{donorRef,geomBytesRef,jobId}` (output refs were already pinned).
- `src/aisims_contracts/registries.py` — `min_length=1` on `PlacementType/FunctionalArchetype.{id,donorRef}`, `DonorMapping.{key,donorObjectKey}`, `RuleSpec.kind`.
- `src/aisims_contracts/codegen.py` — `build_ipc_catalog_ts()` (pure-Python emitter, no node); wired into `generate()` + the `check()` drift loop.
- `tests/test_{ipc,responses,providers,workers,registries,codegen}.py` — 10 new tests + count `14→15` (×2) + providers `set(models)==expected` assertion + nested-`ReadinessCheck` extra-forbid assertion.
- `tests/__snapshots__/{ipc,responses,providers,workers,registries}.schema.json` — re-frozen (error + domain **untouched** = byte-identical).
- `generated/{contracts.schema.json,contracts.ts}` — regenerated (readiness types + minLength descriptions). `helpers.ts` unchanged.

### Commits (on `track/contract-readiness`)
- `8eb1d2a` docs(briefs): brief placement
- `8872baf` (a) feat(contracts): additive GET /readiness IPC surface (§4, 0.10a)
- `4e48233` (b) feat(contracts): min_length=1 + exact-model-set assertion (§7/§8/§11, 0.10b)
- `c4107c2` (c) feat(contracts): codegen emits the IPC protocol catalog (§4, 0.10c)

## Decisions made
- **Additive-only proof scoping (load-bearing).** The brief's RED#3 wording "every non-IPC/response snapshot byte-identical" over-reached because item (b) intentionally re-freezes providers/workers/registries in the same slice. Scoped the proof to (i) error+domain byte-identity (held by their unchanged snapshot tests) + (ii) a structural "readiness is the only addition" test on ipc/responses. **No git-baseline read** (CI-fragile). Orchestrator-approved.
- **min_length field scope** = the scalar path/ref/key fields only; **kept** `RuleSpec.kind`; **excluded** `name` (display, not a key), `RegistryFinding.entryKey` (validator output, not an ingest boundary), and list-ELEMENT constraints. Orchestrator-approved (flag 4).
- **Readiness enums** = `StrEnum` (consistent with LogLevel/GateKind); **subsystem set** = §18's 5 prerequisites (postgres/blender/sims_install/mods_path/providers), verified by the orchestrator against §18.
- **Catalog** = single `generated/ipc-catalog.ts` of typed consts via a pure-Python emitter (no JSON-Schema round-trip); `new Set<Endpoint>([...])` so the future UI `tsc --noEmit` is satisfied.
- **3-commit split with regen-between-commits** so each commit's drift gate is independently green (verified: a=75, b=78, c=80 passed).

## Decisions explicitly NOT made
- **`ReadinessReport.checks` min_length** — left **permissive** (no `min_length`): an early probe legitimately has 0 checks; the Phase-7 UI gate reads empty-checks as "not yet determined." Orchestrator-confirmed.
- **List-element key-emptiness hardening** (textures/targetTGIKeys/requiredResources/tuningKeys/preserveKeys/PollResult.urls) — deferred as a future 0.5b-style tightening (out of this slice's scalar scope).

## TDD compliance
**Clean.** Every code change had its test written first and confirmed RED for the right reason (import/attribute/assertion mismatch) before GREEN, RED→2.5→GREEN per feature in commit order. The Step-2.5 design write-up was reviewed + `APPROVED.` by the orchestrator before any implementation.

## Reachability (Step 7.5)
Contracts are definition + codegen surfaces (no runtime entry point in this area).
- `build_ipc_catalog_ts()` → `generate()` → reachable from the codegen CLI (`python -m aisims_contracts.codegen`) + the `--check` CI drift gate.
- Readiness models/endpoint → enter via the `ipc_schema()` / `responses_schema()` §2.5 snapshot producers + the codegen aggregation (`ALL_CONTRACT_MODELS` → `contracts.ts`) + `__init__` exports.
- `min_length` constraints → enforced at model validation (every boundary), surfaced via the seam schema producers.
- **Documented-downstream consumers (not unreachable-by-mistake):** Phase-2 sidecar `GET /readiness` route; Phase-7 UI readiness-gate + `endpoints.ts`→generated-catalog swap.

## Open follow-ups
Step-9 items were routed hot by the orchestrator to its integration ledger (do not re-route):
- **Cross-doc invariant (integration-owned):** `ARCHITECTURE.md §4` / Appendix-A gain the readiness surface (additive) + the emitted IPC catalog; the §7/§8/§11 `min_length` tightening (snapshot-affecting). Lead applies at the `track/contract-readiness → track/ui` merge / `main` integration.
- **Convention candidate:** "a post-seal additive contract surface ships with an additive-only proof (error/domain byte-identical + a structural 'only the addition' test) so cross-track consumers are provably unaffected."
- **Future TODO (belongs-to-a-phase):** (1) list-element key-emptiness hardening; (2) runtime consumers — Phase-2 sidecar route + Phase-7 UI gate + `endpoints.ts`→catalog swap.
- **Consumer rebase note:** item (b) moves the §7/§8/§11 snapshots — core/providers/mesh-export rebase + re-verify at the merge (an empty path/ref/key was already invalid → correctness tightening, not a break of valid usage).

## How to use what was built
- Regenerate the TS surface (incl. the catalog): `cd packages/contracts && uv run python -m aisims_contracts.codegen`; drift gate: `… codegen --check`.
- Construct a readiness response: `from aisims_contracts import ReadinessReport, ReadinessCheck, ReadyState, ReadinessSubsystem`.
- The UI imports endpoint/protocol constants from `generated/ipc-catalog.ts` (after the lead propagates the generated TS to `track/ui`).
