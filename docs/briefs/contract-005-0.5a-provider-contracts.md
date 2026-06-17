# /tdd brief — provider_contracts

## Feature
Freeze the **§7 provider-adapter contracts** in a NEW `providers.py`: the three model-agnostic provider
**interfaces** (`Image3DProvider` / `ImageGenProvider` / `LLMProvider`) + the **value models** they exchange
(`ProviderJobRef`, a poll-result model, a `PollStatus` enum, and the cost+latency carrier) — guarded by a
§2.5-seam schema-snapshot over the value models plus an interface-signature test over the three Protocols.
Concrete mock/real adapters are NOT in this slice (0.8 / Phase-2).

## Use case + traceability
- **Task ID:** 0.5a (decomposed from 0.5 per the tracker sizing split — confirm at Q0)
- **Architecture sections it implements:** `ARCHITECTURE.md §7` (provider adapters — the three interfaces +
  `ProviderJobRef` + `PollStatus` + cost/latency), §21 (cost/latency recording + price-table fallback), §16
  (provider-output validation — **named, out-of-scope here**: it's adapter-impl logic, not contract shape).
- **Related context:** Phase 0, contract track. 0.1–0.4b landed (`…`/`35f1a2e`/`7d701a6`). This is the first of
  the 0.5 split (0.5a providers / 0.5b workers / 0.5c registries). Conventions from 0.2/0.3/0.4: `aisims_contracts`
  package, `extra="forbid"` on wire models, camelCase fields, `StrEnum` for closed sets, one `spec(§X)`
  schema-snapshot per §2.5 seam. **ProviderConfig/Secret are OUT** (the Settings/onboarding surface; secrets live in the OS
  keychain, safety rule 5) — exactly as 0.4a excluded them from the domain.

## Acceptance criteria (what "done" means)

**A. Provider interfaces (§7) — model-agnostic, impl-free**
- [ ] `Image3DProvider` + `ImageGenProvider`: `submit(image, params) -> ProviderJobRef`; `poll(ref) -> PollResult`;
  `fetch(urls) -> <local artifact refs>`. `LLMProvider`: `complete(...)` + `structured(...)`. Defined as the
  interface seam (Protocol vs ABC — Q1); NO concrete provider (fal/WaveSpeed/Claude) here — those are 0.8/Phase-2.
- [ ] The interfaces are model-agnostic (bakeoff, no model lock-in): model-specific params are a flexible type
  (Q4), not a per-model closed schema.

**B. Value models (§7) — the wire/State-persisted data the interfaces exchange**
- [ ] `ProviderJobRef{provider, model, jobId, submittedAt, expiresAt?}` (§7 — persisted in graph State + Postgres;
  the reconcile spine). `extra="forbid"`, camelCase.
- [ ] A **poll-result** model `{status: PollStatus, progress?, urls?}` (§7).
- [ ] `PollStatus` `StrEnum` — membership ==-pinned (Q2). Must cover the **Tripo 24h URL-expiry** path (§7).
- [ ] A **cost+latency** carrier on provider results: `latencyMs` (MUST be recorded for every cloud op) +
  `costCents` (SHOULD; nullable with the §21 price-table-estimate fallback semantics documented). Placement per Q3.
- [ ] `ErrorEnvelope` (0.2) is the failure carrier on a failed poll/result — imported, never re-rolled (§17).

**C. Freeze + preflight**
- [ ] **Schema-snapshot test** over the *value models* (`ProviderJobRef`, poll-result, `PollStatus`, cost/latency),
  tagged `spec(§7)` → `providers.schema.json`. (Protocols aren't JSON-serializable — they're frozen by B-below.)
- [ ] **Interface-signature test** — the three Protocols expose exactly the expected method set with the expected
  signatures (via `inspect`/`typing.get_type_hints`), so a signature drift on a frozen seam fails a test (Q5).
- [ ] `PollStatus` membership test (exact ==); JSON round-trip + boundary rejection (`extra="forbid"`) on the value
  models; the import-direction guard extends to `providers.py` (it imports `error`; it does NOT import ipc/domain/
  responses — providers is its own §2.5 seam). `/preflight` clean.

## Wiring / entry point (Step 7.5)
`none — wiring lands in 0.8 (mock adapters) + Phase-2 (real adapters + the LangGraph cloud nodes that submit/poll/
fetch and persist ProviderJobRef) + 0.6 (TS codegen of the value models).` Reachability surface this slice = the
`spec(§7)` schema-snapshot + the interface-signature test + importability from `aisims_contracts.providers`.
Frozen-contract surface, not runtime-wired — consistent with 0.2/0.3/0.4.

## Files expected to touch
**New:**
- `packages/contracts/src/aisims_contracts/providers.py` — the 3 interfaces + the value models + `PollStatus`.
- `packages/contracts/tests/test_providers.py` — A/B/C tests.
- `packages/contracts/tests/__snapshots__/providers.schema.json` — the `spec(§7)` value-model snapshot.

**Modified:**
- `packages/contracts/src/aisims_contracts/__init__.py` — re-export the provider interfaces + value models.

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `tests/test_providers.py`
1. **`test_provider_interfaces_present`** — the 3 interfaces exist with their method sets (`submit/poll/fetch`;
   `complete/structured`).
   - Asserts: methods exist with the expected names; signature shape per Q1/Q5.
   - Why: §7 three-interface seam.
2. **`test_provider_job_ref_model`** — `ProviderJobRef` has exactly `{provider,model,jobId,submittedAt,expiresAt?}`;
   `extra="forbid"` rejects unknowns; round-trips.
   - Why: §7 reconcile-spine value model.
3. **`test_poll_status_members`** — `PollStatus` membership == the Q2 set (exact); covers the expiry path.
   - Why: §7 `status ∈ PollStatus` + Tripo expiry.
4. **`test_cost_latency_carrier`** — the result carries `latencyMs` (required) + `costCents` (nullable); placement per Q3.
   - Why: §7/§21 cost+latency recording.
5. **`test_provider_failure_uses_error_envelope`** — a failed poll/result carries `ErrorEnvelope`, not a bespoke error.
   - Why: §17 single error contract.
6. **`test_providers_import_direction`** — `providers.py` imports `error` only (not ipc/domain/responses); extends
   the 0.4b acyclic-DAG guard to the new module.
   - Why: Lesson 5/6 (one-home enums; acyclic intra-package DAG).
7. **`test_providers_schema_snapshot`** *(§2.5-seam guard, `spec(§7)`)* + **`test_provider_interface_signatures`**
   (the Protocol signature freeze).
   - Why: Lesson 1 (every §2.5-seam ships a `spec(§X)` snapshot same cycle).

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** NEW `providers.py` (§7 seam) — `ProviderJobRef` / poll-result / `PollStatus` / cost-latency
  + the 3 interfaces. Appendix-A already lists `ProviderJobRef` + the three interfaces (rows present); confirm == shipped.
- **Orchestrator doc rows to write hot (Step 9):** add the **providers** row to `packages/contracts/CLAUDE.md`
  cross-doc table with `pin: tests/test_providers.py::test_providers_schema_snapshot`; confirm/extend the §7 + Appendix-A rows.
- **§2.5-seam (shared-contract) model touched?** **YES** (`providers.py`, B↔E per Appendix-A). Snapshot mandatory this cycle.

## Things to flag at Step 2.5
0. **(SIZE/SEQUENCING) Confirm the 0.5 split.** I decomposed 0.5 → 0.5a (providers) / 0.5b (workers §8/§9) /
   0.5c (registries §11) — 3 distinct §2.5 seams, each its own snapshot + different design questions (workers carry
   an `ExportReport` name collision; registries carry a validator). My default: **this split, providers first**
   (fewest deps, no collisions). Push back if you'd bundle. Within 0.5a my default is **1 commit** (interfaces +
   value models + snapshot are one seam).
1. **Interface seam — `typing.Protocol` vs `abc.ABC`.** My default: **`Protocol`** (structural — mock + real
   adapters satisfy it without inheriting; matches the adapter-behind-registry seam; `@runtime_checkable` if a
   runtime isinstance is ever needed). Alternative: ABC (nominal, abstractmethod-enforced). Surface your read —
   this shapes how 0.8 mocks + Phase-2 reals declare conformance.
2. **`PollStatus` membership.** My default (ground against §7): `{submitted, running, succeeded, failed, expired}`
   — `expired` covers the Tripo 24h URL-expiry race explicitly. Confirm/adjust (e.g. add `queued`?).
3. **cost+latency placement.** My default: a small `ProviderUsage{latencyMs:int, costCents:int|None}` value object
   embedded on the poll-result (and reusable by 0.5b worker reports later). Alternative: flat fields on the result.
   Confirm.
4. **Model-specific `params` type.** My default: `params: dict[str, Any]` (model-agnostic, bakeoff — the adapter
   validates per-model at impl time, §16). Alternative: a typed base + per-provider extension. Confirm we keep it
   open (closing it would foreclose the no-model-lock-in posture, like Inv6 for registries).
5. **Snapshot scope.** My default: the `spec(§7)` snapshot covers the **pydantic value models only**
   (`ProviderJobRef`/poll-result/`PollStatus`/usage); the Protocol interfaces are frozen by the **signature test**
   (they have no JSON schema). Confirm — and that the signature test is the right "freeze" for the interface half.
6. **Out of scope (confirm):** provider-output validation (§16 max-bytes/magic-byte/path-sanitize) = adapter-impl
   logic (0.8/Phase-2), not contract shape; `ProviderConfig`/`Secret` = the Settings/onboarding surface + OS keychain (safety rule 5),
   never a contract field here.

## Dependencies + sequencing
- **Depends on:** 0.2 (ErrorEnvelope — the failure carrier). (Independent of 0.3/0.4 — providers is its own seam.)
- **Blocks:** 0.5b/0.5c (sibling seams, independent but share the round), 0.6 (codegen → TS), 0.8 (mock adapters
  implement these interfaces), Phase-2 (real adapters + the cloud nodes).

## Estimated commit count
**1** (per Q0). Interfaces + value models + the `spec(§7)` snapshot are one logical seam; bisectability stays
meaningful as a single unit. Split to 2 only if the interface-signature test + value-model snapshot want separate
commits for review.

## Lessons-logged candidates anticipated
- **Convention candidate** — freezing an **interface** seam (Protocol) in a §2.5 snapshot world: value models get the
  JSON-schema snapshot; the interface gets a signature-freeze test (no JSON schema for a Protocol).
- **Architecture-doc note candidate** — confirm §7/Appendix-A `ProviderJobRef` + interface rows == shipped shapes.
- **Convention candidate** — `params: dict[str,Any]` is the model-agnostic seam (bakeoff), the provider-impl
  validates per-model — the §7 analogue of Inv6's open-registry-key rule.

## How to invoke
1. Read this brief + `ARCHITECTURE.md §7` (+ §21 cost/latency) end-to-end.
2. **`/tdd provider_contracts`** (continuing session; no `/session-start`).
3. **Step 2.5** — answer Q0–Q6 (Q1 interface-seam + Q5 snapshot-scope are the load-bearing calls); surface your
   reads with the coverage map. Wait for `APPROVED.` before GREEN.
4. **Step 9** — surface the providers cross-doc row + the §7/Appendix-A confirm + lessons.
