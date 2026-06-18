# /tdd brief — contracts_readiness_snapshot_codegen_batch

> **CROSS-TRACK ARTIFACT.** Authored by `ui-desktop-orchestrator` for a `ui-contracts-implementer` executing in
> the **contract worktree on `track/contract`** (the §4/§2.5 contracts are owned there, not the ui worktree). This
> file is staged in the ui worktree for the lead to relay/place into the contract worktree's `docs/briefs/` as
> the next `contract-NNN`. **Mechanics pending lead confirmation** (see "Coordination" below): the target worktree
> path/branch, brief placement, and a numbered plan task (proposed **0.10**) on `track/contract`'s
> `IMPLEMENTATION_PLAN.md` so `spec-lint` passes. Treat `packages/contracts` as the area; Python 3.13 / uv / pytest
> / `mypy --strict`.

## Feature
A batched, post-Phase-0 `packages/contracts` micro-slice with three independent contract-package items:
**(a)** an **additive** `GET /readiness` IPC surface (the F1=B readiness contract the UI's system-readiness gate
consumes); **(b)** the pending **0.5b snapshot-hardening back-port** (`min_length=1` on contract path/ref/key
string fields + an explicit value-model-SET assertion in the snapshot tests); **(c)** the **codegen-emits-IPC-
catalog** extension (the UI's endpoint catalog — paths, mutating-set, header names, `contractVersion` — emitted to
generated TS so a later UI slice imports it instead of the drift-guarded hand-authored `endpoints.ts`).

## Use case + traceability
- **Task ID:** 0.10 *(proposed — must be added to `track/contract`'s `IMPLEMENTATION_PLAN.md` before dispatch;
  see Coordination)*
- **Architecture sections it implements:** `ARCHITECTURE.md §4` (IPC contract — readiness is **additive**; the
  codegen-catalog is the §4 py↔ts sync surface), `§7`/`§8`/`§11` (the provider/worker/registry contract string
  fields the 0.5b hardening tightens). **Widens phase scope because** Phase 0's `Spec anchors:` line is `§2.5`
  (the union of per-seam snapshots) and this post-seal micro-slice cites the individual seam sections it
  re-freezes; all three items are §2.5-seam-snapshot-covered work.
- **Related context:**
  - **F1=B (user, 2026-06-17):** the readiness surface re-opens §4 **additively** — existing models untouched, so
    core/providers/mesh-export consumers are unaffected; re-froze + codegen'd + propagated by the lead to `track/ui`.
  - **Carry-forward (0.5b):** `min_length=1` on contracts path/ref/key `str` fields + `set(models)==expected` in
    the snapshot tests; re-freezes 3 snapshots → this was flagged as its own contracts micro-slice.
  - **Carry-forward (ledger T3, origin 7.1):** the 0.6 codegen emits model/enum *types* only — not the IPC
    endpoint catalog — so the UI hand-authored `apps/desktop/src/ipc/endpoints.ts` (drift-guarded against
    `ipc.schema.json`). Emitting the catalog lets the UI import it; the UI drift-guard then points at the generated
    artifact.
  - **Frozen-contract discipline:** `packages/contracts` is the §2.5 source of truth; every model change re-freezes
    its `spec(§X)` schema-snapshot. The additive readiness surface MUST NOT alter any existing model's shape.

## Acceptance criteria (what "done" means)
### (a) Additive `GET /readiness`
- [ ] New `Endpoint.READINESS = "GET /readiness"`, classified **read-only** (added to `READ_ONLY_ENDPOINTS`),
      `ENDPOINT_ERROR_CODES[READINESS] = {SYSTEM}`, registered in `REQUEST_MODELS` (no-body request) + the response map.
- [ ] New models: `ReadyState(StrEnum: ready|degraded|blocked)`, `ReadinessSubsystem(StrEnum: postgres|blender|
      sims_install|mods_path|providers)`, `ReadinessCheck{subsystem, status: ReadyState, detail?: str, remediation?: str}`,
      `ReadinessReport{overall: ReadyState, checks: list[ReadinessCheck]}` — `extra="forbid"`, camelCase wire fields.
- [ ] **Additive-only proof:** every pre-existing model's JSON-Schema is byte-identical to its current snapshot
      (no existing `spec(§X)` snapshot changes except the IPC/response ones that gain the new readiness entries).
- [ ] `ipc.schema.json` + `responses.schema.json` re-frozen with the readiness additions; codegen → `generated/
      contracts.ts` gains `ReadinessReport`/`ReadinessCheck`/`ReadyState`/`ReadinessSubsystem`; `--check` clean.
### (b) 0.5b snapshot-hardening
- [ ] `min_length=1` on the contract path/ref/key `str` fields (providers/workers/registries scratch-path / ref /
      key fields — the ones a 0-length value would be invalid for); an empty string is rejected at the boundary.
- [ ] The snapshot tests assert the **exact model set** (`set(models) == EXPECTED`), not just per-model shape.
- [ ] The 3 affected `spec(§7/§8/§11)` snapshots re-frozen to reflect the `minLength` additions.
### (c) codegen IPC-catalog
- [ ] The codegen emits the IPC protocol catalog (endpoint `METHOD path` values, `MUTATING_ENDPOINTS` /
      `READ_ONLY_ENDPOINTS` sets, `TOKEN_HEADER`/`IDEMPOTENCY_KEY_HEADER`, `CONTRACT_VERSION`) to a generated TS
      artifact (e.g. `generated/ipc-catalog.ts`), deterministic (sorted, fixed banner), `--check`-guarded.
- [ ] A test asserts the emitted catalog equals the `ipc.py` source-of-truth values (the same surface the UI
      `endpoints.ts` drift-guard pins against `ipc.schema.json`).
- [ ] `/preflight` clean (ruff + `mypy --strict` + pytest + the codegen `--check`).

## Wiring / entry point (Step 7.5)
Contracts are **definition + codegen** surfaces, not runtime entry points. The readiness models enter via
`ipc_schema()`/`responses_schema()` (the §2.5 snapshot producers) + the codegen aggregation; the catalog enters
via the codegen emitter. **Consumer wiring is downstream:** the sidecar's `GET /readiness` route is Phase-2
(core track); the UI readiness-gate slice + the `endpoints.ts`→generated-catalog swap resume on `track/ui` after
the lead propagates the new generated TS. `none — runtime wiring lands in the consumer tracks (Phase-2 sidecar route + the ui readiness/endpoints slices)`.

## Files expected to touch
**Modified:**
- `packages/contracts/src/aisims_contracts/ipc.py` — `Endpoint.READINESS`, the readiness enums, the endpoint maps.
- `packages/contracts/src/aisims_contracts/responses.py` — `ReadinessCheck`/`ReadinessReport` + `RESPONSE_MODELS` entry.
- `packages/contracts/src/aisims_contracts/{providers,workers,registries}.py` — `min_length=1` on the path/ref/key fields.
- `packages/contracts/src/aisims_contracts/codegen.py` (+ the `emit-ts.mjs` toolchain) — emit the IPC catalog.
- `packages/contracts/tests/test_{ipc,responses,providers,workers,registries,codegen}.py` — new/updated assertions.
- `packages/contracts/tests/__snapshots__/{ipc,responses,providers,workers,registries}.schema.json` — re-frozen.
- `packages/contracts/generated/{contracts.ts, ipc-catalog.ts}` — regenerated.

**New:** the readiness models live in the existing modules (no new source file); `generated/ipc-catalog.ts` is new.

## RED test outline (Step 2)
1. **`test_readiness_report_roundtrips`** — `ReadinessReport`/`ReadinessCheck` validate; `extra="forbid"`; enum fields reject out-of-set. Why: §4 additive surface.
2. **`test_readiness_endpoint_registered_readonly`** — `READINESS ∈ READ_ONLY_ENDPOINTS`, in the maps, `{SYSTEM}` error. Why: §4.
3. **`test_existing_snapshots_unchanged_except_readiness`** — every non-IPC/response snapshot is byte-identical; IPC/response snapshots change only by the readiness additions. Why: **additive-only** guarantee (consumers unaffected).
4. **`test_contract_string_fields_reject_empty`** — the hardened path/ref/key fields reject `""`. Why: 0.5b.
5. **`test_snapshot_asserts_exact_model_set`** — `set(models) == EXPECTED` for each hardened seam. Why: 0.5b (drift can't add/drop a model silently).
6. **`test_codegen_emits_ipc_catalog`** — the emitted catalog == the `ipc.py` source values (paths/sets/headers/version); deterministic; `--check` clean. Why: T3.
7. **`test_generated_ts_has_readiness_types`** — `generated/contracts.ts` contains `ReadinessReport`/`ReadinessCheck`/`ReadyState`/`ReadinessSubsystem`. Why: §4 propagation.

## Cross-doc invariant impact (orchestrator/lead writes the docs)
- **Model field changes:** **adds** the readiness models (new §2.5-seam surface on §4) + `min_length` on existing
  string fields (tightening, snapshot-affecting). The `ARCHITECTURE.md §4` Appendix-A / contract rows gain the
  readiness surface — an **integration-owned root-doc edit** (route to the integration ledger, not the worktree copy).
- **§2.5-seam touched?** YES — IPC/responses (readiness) + providers/workers/registries (`min_length`). RED 1–5 are
  the schema-snapshot tests; re-freeze in-slice.

## Things to flag at Step 2.5
1. **Readiness enums — `StrEnum` vs open `str`.** **Default: `StrEnum`** (consistent with `LogLevel`/`GateKind`;
   grows additively like `ErrorCode`, with the UI tolerant-consumer pattern if needed). Subsystems can extend later.
2. **`ReadinessSubsystem` initial set.** `{postgres, blender, sims_install, mods_path, providers}` per §18's
   prerequisites. **Default: that set** — confirm against §18; additive thereafter.
3. **Catalog artifact shape.** A generated TS module exporting typed constants (endpoint paths, the two sets,
   header names, version). **Default: a single `generated/ipc-catalog.ts`** mirroring `ipc.py`'s catalog, deterministic.
4. **`min_length` field scope.** Apply only to fields where a 0-length value is semantically invalid (scratch
   paths, refs, registry keys) — **not** every `str`. **Default: the path/ref/key fields named in the 0.5b carry-forward.**

## Dependencies + sequencing
- **Depends on:** Phase 0 sealed contracts (all landed on `track/contract`). No upstream live task.
- **Blocks:** the **ui readiness-gate slice** (needs the propagated readiness TS) + the **ui `endpoints.ts`→
  generated-catalog swap**. The Phase-2 sidecar `GET /readiness` route (core track).

## Estimated commit count
**3** (bundled; each an independent contract concern, each green in order):
1. **Additive `GET /readiness`** (models + maps + snapshots + codegen) — the §4 surface.
2. **0.5b snapshot-hardening** (`min_length` + set-assertion + 3 re-frozen snapshots).
3. **codegen IPC-catalog** (emitter + `generated/ipc-catalog.ts` + `--check` test).

Each touches `packages/contracts` only; (1) and (2) re-freeze snapshots (review the diffed JSON carefully). No
safety **invariant** in the root-CLAUDE sense (these are contract-shape changes), but the additive-only proof
(RED #3) is the load-bearing guarantee — keep it green.

## Lessons-logged candidates anticipated
- **Convention candidate** — "A post-seal additive contract surface ships with an **additive-only proof** (every
  pre-existing snapshot byte-identical) so consumers across tracks are provably unaffected."
- **Architecture-doc note** — §4 gains the readiness surface + the emitted IPC catalog (integration-owned edit).

## Coordination (lead — mechanics I need before dispatch)
1. **Target worktree + branch** for the `ui-contracts-implementer` (expected `../AISimsStudio-contract` on
   `track/contract`) — confirm on spawn.
2. **Brief placement** — relay/copy this file into that worktree's `docs/briefs/` as the next `contract-NNN`
   (contract-012 by my count); I won't write into another track's worktree.
3. **Plan task 0.10** — add a numbered task entry on `track/contract`'s `IMPLEMENTATION_PLAN.md` (so `spec-lint
   brief` passes its task-ID + phase-anchor checks); I'll spec-lint in that worktree context once it exists.
4. On green: you coordinate the `track/contract → track/ui` pull so the new generated TS reaches me and the ui
   readiness-gate slice resumes.
