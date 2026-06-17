# /tdd brief — ipc_completion

## Feature
Complete the frozen IPC contract (D15): add the **REST response bodies** for the 14 §4 endpoints in a NEW
`responses.py` (embedding the now-landed 0.4a domain entities), **tighten 0.3's 4 loose SSE `str` fields to
their domain enums** (the mandatory, snapshot-affecting D15 tightening), keep **`GateKind` single-homed**
(import, never redefine), and **re-freeze `ipc.schema.json`** + add a `responses` §2.5-seam snapshot.

## Use case + traceability
- **Task ID:** 0.4b
- **Architecture sections it implements:** `ARCHITECTURE.md §4` (the IPC response bodies + the SSE-field
  tightening complete the frozen REST+SSE contract), §12 (the embedded domain entities — `domain.py`, landed
  0.4a), §17 (`ValidationResult.severity`/`Severity` ⊃ the IPC `ValidationEvent.severity`).
- **Related context:** 0.4a landed (`4a69df5`) — `domain.py` exports all 16 entities + the 13 state enums
  incl. `StepState`/`Severity`/`ValidationScope`; `GateKind` is single-defined in `ipc.py` (`e7b628a`, 0.3).
  0.3 deliberately froze `ipc.py` **domain-independent** (SSE events reference domain by `str` + protocol
  enums; response bodies deferred here). This slice reverses that **only for the 4 marked SSE fields** (each
  carries an inline "MANDATORY-tightened in 0.4b" comment) + adds the response surface. Conventions from
  0.2/0.3/0.4a hold: `aisims_contracts` package, `extra="forbid"`, camelCase wire fields, `StrEnum` for closed
  sets, one `spec(§X)` schema-snapshot per §2.5 seam (a drift IS the failure — never a blind regen).

## Acceptance criteria (what "done" means)

**A. REST response bodies (§4 / DATA_MODEL.md "Core Entities") → NEW `responses.py`**
- [ ] A **response model per the 14 §4 endpoints** (named, parallel to the `REQUEST_MODELS` structure in
  `ipc.py`), each embedding the correct domain entity. Default mapping (confirm/adjust at Q2):
  | Endpoint | Default response | Embeds |
  |---|---|---|
  | CREATE_PROJECT | `CreateProjectResponse` | `Project` |
  | LIST_PROJECTS | `ListProjectsResponse` | `items: list[Project]` + `total`/`limit`/`offset` (Q6) |
  | START_OR_RESUME_RUN | `RunResponse` | `PipelineRun` |
  | GATE | `GateResponse` | `PipelineRun` (advanced run state) — Q2 |
  | REGENERATE | `RegenerateResponse` | `PipelineRun` (async job started; the candidate streams via SSE) — Q2 |
  | INCLUDE_ITEM | `IncludeItemResponse` | `ItemSpec` |
  | FUNCTIONAL | `FunctionalResponse` | `FunctionalOverlay` |
  | VALIDATE | `ValidateResponse` | `results: list[ValidationResult]` |
  | EXPORT | `ExportResponse` | `ExportArtifact` (embeds `ExportReport`) — Q2 |
  | TEST_INSTALL | `TestInstallResponse` | `PipelineRun` (async) — Q2 |
  | RERUN_STEP | `RerunStepResponse` | `Step` — Q2 |
  | CANCEL_JOB | `CancelJobResponse` | protocol ack `{jobId, cancelled}` (no domain entity) |
  | SETTINGS | `SettingsResponse` | protocol settings view (`simsModsPath`, `telemetryEnabled`, …; no domain entity) |
  | TEST_PROVIDER | `TestProviderResponse` | protocol result `{ok, latencyMs?, error: ErrorEnvelope?}` (no domain entity) |
- [ ] `responses.py` imports BOTH `aisims_contracts.ipc` + `aisims_contracts.domain` and keeps the
  acyclic import direction (`error ← domain`; `error,domain ← ipc`; `ipc,domain ← responses`). It does **not**
  reach back into `ipc.py` to mutate request shapes.
- [ ] A `RESPONSE_MODELS: dict[Endpoint, TypeAdapter[...]]` registry (parallel to `REQUEST_MODELS`) covering all
  14 endpoints, + a `responses_schema()` producer for the snapshot.

**B. [D15 · MANDATORY · PINNED] str→domain-enum tighten 0.3's SSE fields (snapshot-affecting, deliberate)**
- [ ] `StepStateEvent.status`: `str` → `StepState` (import from `aisims_contracts.domain`).
- [ ] `DoneEvent.status`: `str` → the **run-terminal subset** `{succeeded, failed, cancelled}` (Q3 — type
  shape).
- [ ] `ValidationEvent.severity`: `str` → `Severity`.
- [ ] `ValidationEvent.scope`: `str` → `ValidationScope`.
- [ ] **No loose `str` domain field survives** the SSE union. Each tightened field rejects an out-of-enum value
  (`extra="forbid"` already holds; enum membership now pins the value).
- [ ] **Re-freeze `ipc.schema.json`** — the diff shows ONLY these 4 fields changing from `str` to the enum (the
  reviewable-diff discipline; everything else byte-identical).

**C. `GateKind` single-definition guard (Inv5 surface — no behavior)**
- [ ] `GateKind` stays **single-homed** (currently `ipc.py`); 0.4b adds **no duplicate** of it in `domain.py`
  or `responses.py`. A test pins exactly-one definition / single import home. (No domain gate model exists yet
  to import it — see Q5 for the Phase-2 DAG note; do NOT introduce one here.)

**D. Freeze + preflight**
- [ ] **Schema-snapshot test** for the response surface, tagged `spec(§4)` (Q4: own `responses.schema.json` vs
  fold into the ipc snapshot — default: own). The re-frozen `ipc.schema.json` reflects the 4 tightened fields.
- [ ] Response-model JSON round-trip + boundary rejection (`extra="forbid"`); the SSE-tighten rejection tests
  (B); the `GateKind` single-home test (C).
- [ ] `/preflight` clean (`ruff` + `mypy --strict` + `pytest`).

## Wiring / entry point (Step 7.5)
`none — wiring lands in Phase 2 + 0.6.` These are frozen contract **shapes**: the FastAPI routes that *return*
these response bodies + emit the tightened SSE events are Phase 2 (sidecar); the TS client that consumes them is
0.6 codegen. Reachability surface this slice = the `spec(§4)` schema-snapshot(s) + importability from
`aisims_contracts.responses` (+ the tightened `aisims_contracts.ipc`). No tested-but-unwired gap — snapshot +
importability ARE the intended contract surface (consistent with 0.2/0.3/0.4a).

## Files expected to touch
**New:**
- `packages/contracts/src/aisims_contracts/responses.py` — the 14 REST response models + `RESPONSE_MODELS` + `responses_schema()`.
- `packages/contracts/tests/test_responses.py` — A/D tests.
- `packages/contracts/tests/__snapshots__/responses.schema.json` — the `spec(§4)` response snapshot (Q4).

**Modified:**
- `packages/contracts/src/aisims_contracts/ipc.py` — tighten the 4 SSE fields to domain enums (adds a
  `from aisims_contracts.domain import StepState, Severity, ValidationScope` import); `DoneEvent.status` per Q3.
- `packages/contracts/tests/test_ipc.py` — assert the tightened field types + rejection; update the snapshot test.
- `packages/contracts/tests/__snapshots__/ipc.schema.json` — **re-frozen** (only the 4 fields change).
- `packages/contracts/src/aisims_contracts/__init__.py` — re-export the new response models + `RESPONSE_MODELS`.

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `tests/test_responses.py` (+ additions to `tests/test_ipc.py`)
1. **`test_response_models_present`** — `RESPONSE_MODELS` has an entry for all 14 `Endpoint` members; each
   response model exists.
   - Asserts: `set(RESPONSE_MODELS) == set(Endpoint)`; each embeds the documented domain entity (per the A table).
   - Why: §4 "each REST command: … success response"; completes the deferred 0.3 surface (D15).
2. **`test_sse_fields_tightened`** *(in `test_ipc.py`)* — the 4 fields are now domain enums, not `str`.
   - Asserts: `StepStateEvent.status` accepts a `StepState` + rejects `"bogus"`; `ValidationEvent.severity` is
     `Severity`; `.scope` is `ValidationScope`; `DoneEvent.status` accepts `succeeded/failed/cancelled`.
   - Why: D15 mandatory tightening; root `CLAUDE.md` "deterministic validation"; Lesson 5 (str-now + pinned tighten).
3. **`test_done_status_terminal_subset`** *(in `test_ipc.py`)* — `DoneEvent.status` rejects non-terminal run
   states (`"running"`, `"pending"`, `"waiting-for-user"`).
   - Asserts: only `{succeeded, failed, cancelled}` validate; others raise.
   - Why: §6/§12 PipelineRun terminal subset; `done` is a run-terminal event.
4. **`test_gatekind_single_definition`** — `GateKind` is importable from exactly one home (`ipc`); no duplicate
   symbol in `domain`/`responses`.
   - Asserts: `aisims_contracts.domain` + `aisims_contracts.responses` do not define a `GateKind`.
   - Why: Lesson 5 (one home per shared enum; import never redefine); no duplicate §2.5-seam enum.
5. **`test_responses_round_trip` + `test_responses_boundary_rejection`** — JSON round-trip equality; `extra="forbid"`
   rejects an unknown field on a response model.
   - Why: 0.2/0.3/0.4a boundary-strictness convention (Lesson 3).
6. **`test_responses_schema_snapshot`** *(§2.5-seam guard, `spec(§4)`)* — `responses.schema.json` matches the
   checked-in snapshot; **and** the re-frozen `ipc.schema.json` reflects the 4 tightened fields.
   - Why: Lesson 1 (every §2.5-seam ships a `spec(§X)` snapshot same cycle; a drift IS the failure).

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** IPC SSE union **CHANGED** (4 fields `str`→domain enum); NEW `responses.py` module
  (14 response models) joins the §4 IPC seam. `ipc.py` now imports 3 `domain` enums → it is **no longer fully
  "domain-independent"** (the 0.3-era property the cross-doc IPC row records).
- **Orchestrator doc rows to write hot (Step 9 routing):** update the **IPC row** in
  `packages/contracts/CLAUDE.md` cross-doc table (note the tightened SSE fields + the new `responses.py` +
  drop the "domain-independent" phrasing for the SSE surface) + the matching `ARCHITECTURE.md §4`/Appendix-A
  note; add `pin: tests/test_responses.py::test_responses_schema_snapshot` for the response seam.
- **§2.5-seam (shared-contract) model touched?** **YES** — the `ipc.schema.json` re-freeze + the new
  `responses.schema.json`. Both snapshot tests are mandatory **this cycle** (RED #6).

## Things to flag at Step 2.5
0. **(SIZE/SEQUENCING) commit split.** This is one logical unit (IPC completion). My default: ONE slice, up to
   2 commits — C1 `feat(contracts): IPC REST response bodies (responses.py) + spec(§4) snapshot`; C2
   `feat(contracts): tighten SSE fields to domain enums + GateKind guard + ipc re-freeze (D15)`. No safety
   invariant is implemented here (Inv5 enforcement is Phase-2), so no mandatory own-commit. Surface if you'd
   bundle to 1 or need a different split for bisectability.
1. **Response-model shape — named wrapper per endpoint vs bare domain entity vs generic envelope.** My default:
   **a named response model per endpoint** that embeds the domain entity (symmetry with `REQUEST_MODELS`; lets
   each endpoint's response grow additively without disturbing the embedded domain type — matches the user's
   extensible-over-minimal posture). Alternatives: return the domain entity directly (less boilerplate, but no
   per-endpoint evolution seam); a generic `CommandResponse[T]` (pydantic-generic JSON-schema is messier to
   snapshot). Surface your read.
2. **Endpoint→entity mapping (the A table).** Confirm the defaults; the genuinely ambiguous ones: **EXPORT**
   (`ExportArtifact` handle vs the async `PipelineRun` — default `ExportArtifact`, embeds `ExportReport`);
   **REGENERATE / TEST_INSTALL** (async → `PipelineRun`, the artifact streams via SSE — default `PipelineRun`);
   **RERUN_STEP** (`Step` vs `PipelineRun` — default `Step`); **GATE** (`PipelineRun` advanced vs a decision ack
   — default `PipelineRun`). Pin each to §4/DATA_MODEL and surface disagreements.
3. **`DoneEvent.status` terminal-subset type.** My default: **`Literal[StepState.SUCCEEDED, StepState.FAILED,
   StepState.CANCELLED]`** — a type-level subset the snapshot/codegen advertises to TS consumers, with **no
   duplicate enum** (honors Lesson 5). Fallback if pydantic emits an ugly JSON-schema for a Literal-of-enum-
   members (verify): keep `status: StepState` + a `field_validator` restricting to the 3 terminal members
   (runtime-pinned, but the subset isn't visible in the schema). Do **not** mint a separate `RunTerminalStatus`
   `StrEnum` (duplicate values with `StepState` = the smell Lesson 5 warns against). Surface what pydantic emits.
4. **Response snapshot placement.** My default: **own `responses.schema.json` tagged `spec(§4)`** — keeps the
   `ipc.schema.json` re-freeze diff showing ONLY the 4 tightened fields (reviewable-diff discipline) and matches
   the one-module-one-snapshot pattern (error/ipc/domain). Alternative: fold response models into `ipc_schema()`.
   Confirm.
5. **`GateKind` home + the Phase-2 import-DAG note (flag, do NOT resolve here).** 0.4b keeps `GateKind` in
   `ipc.py` and only guards single-definition. Heads-up for the carry-forward: once `ipc.py` imports `domain`
   enums (this slice) **and** a future Phase-2 domain *gate model* needs `GateKind`, importing it from `ipc`
   would create an `ipc ↔ domain` **cycle**. Resolution options when that lands (Phase-2, not now): move
   `GateKind` into `domain.py` (the gate sequence is also an Inv5 domain concept) or a neutral shared-enums
   module both import. Don't pre-solve in 0.4b — just don't add a domain gate model. Confirm you're leaving it.
6. **`LIST_PROJECTS` pagination shape.** My default: `ListProjectsResponse{items: list[Project], total: int,
   limit: int|None, offset: int|None}` (mirrors `ListProjectsRequest`'s limit/offset). Alternative: a bare
   `list[Project]`. Confirm.

## Dependencies + sequencing
- **Depends on:** 0.4a (domain entities + `StepState`/`Severity`/`ValidationScope` enums — landed `4a69df5`);
  0.3 (the IPC surface being completed/tightened — landed `e7b628a`).
- **Blocks:** 0.5 (provider/worker/registry contracts), 0.6 (codegen consumes the re-frozen `ipc.schema.json` +
  the new `responses.schema.json` → TS), 0.7 (store persists the embedded entities), Phase 2 (the engine emits
  the tightened SSE events + the routes return these bodies).

## Estimated commit count
**1–2** (per Q0). Default: C1 response bodies + `spec(§4)` snapshot; C2 the D15 SSE tightening + `GateKind`
guard + `ipc.schema.json` re-freeze. The snapshot re-freeze pairs naturally with the field change (one
bisectable unit). Collapse to 1 if the implementer judges the whole thing reviewable in one sitting.

## Lessons-logged candidates anticipated
- **Convention candidate** — a freeze-before-dependency seam ships `str` first, then a **mandatory pinned
  tighten** once the dependency lands (the 0.3→0.4b SSE pattern; extends Lesson 5).
- **Architecture-doc note candidate** — `ipc.py` graduates from "domain-independent" to "imports the 3 SSE
  domain enums"; record the response-body surface (§4 / Appendix-A) consumers (0.6 codegen) will depend on.
- **Future TODO — carry-forward** — the `GateKind` import-DAG decision (Q5) surfaces when a Phase-2 domain gate
  model lands; record `last-consumer-slice: Phase-2 (gate model)`.

## How to invoke
1. **Fresh implementer session → run `/session-start` once** (orient on the tracker + this area's `CLAUDE.md`),
   then read this brief + `docs/planning/DATA_MODEL.md` (the §4 endpoint table + entity fields) end-to-end.
2. **`/tdd ipc_completion`**.
3. **Step 2.5** — answer Q0–Q6 (Q1 + Q3 are the load-bearing shape calls); surface your reads. Wait for
   `APPROVED.` before GREEN.
4. **Step 9** — surface the IPC cross-doc row update + the new `responses` seam row + the re-freeze + lessons.
