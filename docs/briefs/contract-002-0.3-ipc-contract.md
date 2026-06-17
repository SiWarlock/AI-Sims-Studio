# /tdd brief — ipc_contract

## Feature
Define the frozen **IPC contract** (§4) — the typed REST + SSE boundary between the Electron UI and the FastAPI sidecar — as Pydantic v2 models in `packages/contracts/src/aisims_contracts/ipc.py`, guarded by a **§2.5-seam schema-snapshot test**. Covers: the SSE event taxonomy (8 typed events, discriminated union), the REST command request models + a per-endpoint `ErrorEnvelope` error-code map, the `/health` response carrying `contractVersion`, and the per-launch loopback-token + idempotency-key wire conventions. Defines the SHAPES only — the FastAPI routes / SSE stream / token middleware are Phase 2.

## Use case + traceability
- **Task ID:** 0.3
- **Architecture sections it implements:** `ARCHITECTURE.md §4` (IPC contract — REST commands, SSE taxonomy, token, `contractVersion`, idempotency, py↔ts sync), §16 (loopback-token trust boundary), §17 (`ErrorEnvelope` error codes per endpoint + the SSE `error` event), §6 (`/health` from the supervisor), §12 (the domain entities REST responses + `step-state`/`validation` events reference — 0.4 coupling).
- **Related context:** Phase 0, contract track. **0.2 (ErrorEnvelope) landed** (C2 `c93215b`) — the SSE `error` event + REST error codes import it from `aisims_contracts.error`. **0.4 (domain types) is a sibling slice not yet landed**; 0.3's REST response bodies + a couple of SSE event payloads reference domain entities (Project / PipelineRun / Step / ValidationResult) that 0.4 defines — see **Step-2.5 Q1 (the load-bearing coupling call)**. TS client codegen is **deferred to 0.6** (as ErrorEnvelope's TS was). Package is `aisims_contracts` (src-layout); `extra="forbid"` + camelCase wire form per the 0.2 precedent.

## Acceptance criteria

**SSE event taxonomy (§4)**
- [ ] 8 typed SSE event payload models — `progress`, `step-state`, `log`, `validation`, `cost`, `gate-needed`, `done`, `error` — combined into a **discriminated union** keyed on an `event` `Literal` tag.
- [ ] The `error` event embeds **`ErrorEnvelope`** imported from `aisims_contracts.error` (never a hand-rolled duplicate — root `CLAUDE.md` forbidden pattern).
- [ ] Resumable stream: each event carries an `id` (the `Last-Event-ID` resume cursor, §4) — type per Q4.
- [ ] Domain-referencing fields (`step-state` → Step status; `validation` → a ValidationResult summary) handled per Q1.

**REST command surface (§4)**
- [ ] A request model for each of the **14 endpoints**: `POST /projects`, `GET /projects`, `POST /projects/{id}/runs` (start|resume), `POST /runs/{id}/gate` (approve|reject|edit), `POST /items/{id}/regenerate` (concept|mesh|cleanup), `POST /items/{id}/include`, `POST /items/{id}/functional`, `POST /projects/{id}/validate`, `POST /projects/{id}/export`, `POST /projects/{id}/test-install`, `POST /steps/{id}/rerun`, `DELETE /jobs/{id}` (cancel), `GET/PUT /settings`, `POST /settings/providers/{p}/test`. Multi-mode commands (runs, gate, regenerate) are discriminated unions.
- [ ] Every **mutating** command carries an **idempotency key** (R9) — representation per Q3.
- [ ] **Per-endpoint error-code map:** an explicit checked-in mapping (endpoint → the `ErrorCode` subset it may return, §17), every referenced code ∈ the §17 `ErrorCode` enum (no stray codes).
- [ ] REST response bodies returning domain entities → handled per Q1 (forward-ref to 0.4).

**Health + versioning + token (§4 / §16)**
- [ ] `HealthResponse` model carrying `contractVersion` (the value returned at `/health`).
- [ ] `contractVersion` constant + negotiation semantics documented (UI presents its supported version; mismatch → defined behavior — enforced Phase 2).
- [ ] The per-launch loopback **token** wire convention modeled (header representation + the reject-on-missing rule documented; enforcement is Phase 2, §16).

**Freeze + tests**
- [ ] **Schema-snapshot test** (§2.5-seam): the IPC surface (`model_json_schema()` of the event union + request models + `HealthResponse` + the error-code map) field-names + enums + discriminators == a checked-in `ipc.schema.json`, tagged **`spec(§4)`**. A drift is the failure.
- [ ] Discriminated-union round-trip: each SSE event + each multi-mode request serializes/deserializes by its tag.
- [ ] Boundary rejection: unknown `event` tag / unknown command discriminator / extra field → `ValidationError` (`extra="forbid"`).
- [ ] `/preflight` clean.

## Wiring / entry point (Step 7.5)
IPC contract types are frozen contract models. Runtime wiring (FastAPI routes accepting/emitting them, the SSE stream, the token middleware) lands in **Phase 2 (sidecar)**; the TS client in **0.6** + **Phase 7 (UI)**. For THIS slice the reachability surface is the **schema-snapshot test** + the models being importable from `aisims_contracts.ipc`. Runtime wiring: `none — wiring lands in Phase 2 (sidecar) + 0.6 (TS client codegen) + Phase 7 (UI)`.

## Files expected to touch
**New:** `packages/contracts/src/aisims_contracts/ipc.py` (the IPC models), `packages/contracts/tests/test_ipc.py` (RED tests), `packages/contracts/tests/__snapshots__/ipc.schema.json` (the committed snapshot). The package `__init__.py` may add an IPC export.
**Modified:** none. (The IPC cross-doc row + Appendix-A confirm are orchestrator territory — flag at Step 9; do not edit `ARCHITECTURE.md`/`CLAUDE.md`/`IMPLEMENTATION_PLAN.md`.)
If implementation needs files beyond this list, **flag at Step 2.5** before GREEN.

## RED test outline (Step 2)
1. **`test_sse_event_union_members`** — the discriminated union covers exactly the 8 `event` tags; each tag resolves to its model.
2. **`test_sse_error_event_embeds_errorenvelope`** — the `error` event payload IS `ErrorEnvelope` (imported from `aisims_contracts.error`, not duplicated).
3. **`test_rest_request_models_present`** — a request model exists for each of the 14 endpoints; the multi-mode commands (runs start|resume, gate approve|reject|edit, regenerate concept|mesh|cleanup) validate by discriminator.
4. **`test_idempotency_key_on_mutating_commands`** — every mutating command carries the idempotency-key representation (per Q3); read-only commands (GET /projects, GET /settings, /health) do not require it.
5. **`test_endpoint_error_code_map`** — the endpoint→`ErrorCode`-subset map covers all 14 endpoints; every code ∈ the §17 `ErrorCode` enum (assert ⊆, no stray codes).
6. **`test_health_response_contract_version`** — `HealthResponse` carries `contractVersion` == the module constant.
7. **`test_boundary_rejection`** — unknown event tag / unknown command discriminator / extra field → `ValidationError`.
8. **`test_ipc_schema_snapshot`** *(the §2.5-seam guard)* — `model_json_schema()` of the IPC surface (normalized) == checked-in `ipc.schema.json`. **Tag `spec(§4)`** so `spec-lint tests 0` finds it.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **NEW models:** the SSE event union + 14 request models + `HealthResponse` + the endpoint→ErrorCode map. All §2.5-seam (shared **A↔B** per the Appendix-A IPC row).
- **Orchestrator doc rows to write (Step-9 routing):** add the **IPC** row to `packages/contracts/CLAUDE.md` cross-doc table with `pin: tests/test_ipc.py::test_ipc_schema_snapshot`; confirm the `ARCHITECTURE.md` Appendix-A IPC row (§4) field list == the shipped surface (endpoint table; event types; `contractVersion`; idempotencyKey; token).
- **§2.5-seam touched?** YES — the IPC schema is shared A↔B. The `spec(§4)` schema-snapshot test (RED #8) is mandatory this cycle.

## Things to flag at Step 2.5
1. **0.3↔0.4 domain coupling (LOAD-BEARING — surface, don't silently default).** REST response bodies + the `step-state`/`validation` SSE events reference domain entities (Project, PipelineRun, Step, ValidationResult) defined in **0.4 (not yet landed)**.
   - **(A, my default) — define the domain-independent IPC protocol now** (event union, request commands, `/health`, token, idempotency, error-code map) + model domain-entity payloads as **forward references** (`from __future__ import annotations` + `model_rebuild()` wired when 0.4 lands). The 0.3 snapshot covers the protocol shapes; the domain-coupled response payloads' snapshot finalizes in 0.4. Keeps the tracker order; no duplicate types.
   - **(B)** define minimal domain stubs in 0.3, replaced in 0.4 — risks duplicate-type drift; discouraged.
   - **(C)** swap 0.4 before 0.3 — contradicts the tracker + the lead's dispatch; raise as a sequencing **finding** only if (A) proves unworkable.
   Surface your read at Step-2.5; I confirm (escalate to the lead if it reshapes the contract surface materially).
2. **Token + idempotency-key representation.** The loopback token is a per-request auth **header** (not a body field); the idempotency key is a per-mutating-command header/field. My default: **typed header-convention constants + an `IpcRequestHeaders` model** (`token`, `idempotencyKey`) documenting the wire contract; enforcement is Phase 2. (Confirm vs a request-envelope wrapper or per-command fields.)
3. **Snapshot granularity.** One combined `ipc.schema.json` vs per-model snapshots. My default: **one combined, normalized snapshot** (the IPC contract is one §2.5 seam → one diff-reviewable artifact).
4. **SSE `id` / resume-cursor type.** My default: **`str`** (SSE `id` is text on the wire; an opaque monotonic string is most flexible for `Last-Event-ID`).
5. **`contractVersion` type + value.** My default: **a semver-ish string constant** (e.g. `"1.0"`); `/health` returns it; mismatch handling documented, enforced Phase 2. Confirm the initial value/format.
6. **Discriminated-union mechanism.** My default: **Pydantic `Field(discriminator=...)` tagged unions** (tag = a `Literal` field) for the SSE events + the multi-mode commands.

## Dependencies + sequencing
- **Depends on:** 0.2 (ErrorEnvelope — landed). **Soft-coupled to:** 0.4 (domain types — see Q1).
- **Blocks:** 0.5 (provider/worker contracts), 0.6 (codegen consumes `ipc.schema.json` → TS client — deferred there, not here), Phase 2 (sidecar implements the routes), Phase 7 (UI client).

## Estimated commit count
**2–3.** Suggested split (bisectable; none touches a safety invariant — the token here is the SHAPE, not the §16 enforcement):
1. `feat(contracts): IPC SSE event taxonomy + /health + contractVersion` (the event union + HealthResponse).
2. `feat(contracts): IPC REST command models + per-endpoint error-code map + token/idempotency wire conventions` (+ the `spec(§4)` schema-snapshot).
If the token modeling drifts toward **enforcement** (rejecting requests), STOP — that's Phase-2 safety surface, flag it.

## Lessons-logged candidates anticipated
- Convention — "§2.5-seam discriminated-union contracts snapshot the full union AND assert exact tag membership (`==`)."
- Convention — "the IPC error surface is an explicit endpoint→ErrorCode map asserted ⊆ the §17 enum (no stray codes)."
- Future TODO — 0.6 codegen consumes `ipc.schema.json` → TS client (carry-forward).

## How to invoke
1. Read end-to-end — do **not** skip the Step-2.5 questions, especially **Q1 (the 0.3↔0.4 coupling)**.
2. `/tdd ipc_contract` (continuing session — you're mid-session; no `/session-start`).
3. Step 0/1 — confirm the restatement + file list.
4. Step 2.5 — send the test-design write-up + answers to Q1–Q6. **Q1 is load-bearing: surface your read, take no silent default.** Wait for `APPROVED.`/`TWEAK:`/`ADD:` before GREEN.
5. Step 9 — surface the IPC cross-doc row + the resolved 0.4-coupling approach + lessons.
