# /tdd brief — registry_contracts

## Feature
Freeze the **§11 registry entry-schema contracts** in a NEW `registries.py`: the three open-registry entry models
(`PlacementType` / `FunctionalArchetype` / `DonorMapping`) + their rule sub-grammar representation + a per-registry
`registryVersion` + a **load-time validator** (structural validity + version + id/key uniqueness). Guarded by a
§2.5-seam schema-snapshot. The registry *content* (seeded entries) and the full rule semantics are NOT here.

## Use case + traceability
- **Task ID:** 0.5c (decomposed from 0.5; last of the 0.5 split — siblings 0.5a `de7caee`, 0.5b `ccce712` landed)
- **Architecture sections it implements:** `ARCHITECTURE.md §11` (registries — open, data-driven, version-controlled
  config = source of truth; loaded+validated into Postgres as a read cache; each carries `registryVersion`; entry JSON
  + rule sub-grammars; ADR-010 "add an entry = config + donor + test"), §13 (loaded into the §13 store — but the
  *loading* is 0.7/runtime, here only the schema + the pure validator), §17 (`ErrorEnvelope` for validation findings),
  §12 (Inv6 tie-in — the domain `archetype`/`placementCategory` `str` keys validate against THESE registries).
- **Related context:** Phase 0, contract track. Conventions from 0.2–0.5b: `aisims_contracts`, `extra="forbid"`,
  camelCase, `StrEnum` for closed sets, one `spec(§X)` snapshot per seam, the acyclic intra-package DAG (extend
  `test_import_direction` to `registries.py` via the `intra_imports` conftest fixture). **The rule sub-grammars
  (tuning-graft, eligibility) are pinned by spike S3 (Phase 1) — one archetype proves the schema.** So 0.5c freezes
  the entry ENVELOPES + a flexible rule representation; it must NOT over-specify the grammar ahead of S3.

## Acceptance criteria (what "done" means)

**A. Registry entry models (§11 / DATA_MODEL.md "Registry entries")**
- [ ] `PlacementType{id, name, donorRef, footprintRules}`; `FunctionalArchetype{id, name, donorRef, tuningGraftRules,
  eligibilityRules, validationRules}`; `DonorMapping{key, donorObjectKey, requiredResources, tuningKeys, preserveKeys}`.
  `extra="forbid"`, camelCase. (Note the §11-vs-DATA_MODEL naming: §11 says `eligibilityPredicate`, DATA_MODEL says
  `eligibilityRules` — reconcile at Q4.)
- [ ] **Rule sub-grammars represented but NOT over-specified** (Q1): `footprintRules`/`tuningGraftRules`/`eligibilityRules`/
  `validationRules` modeled as a flexible-but-structured representation (S3 pins the full grammar in Phase 1). The
  registry stays an **open registry** (Inv6) — adding an entry is config+donor+test, never an engine/enum change.

**B. Registry collection + version (§11/§13)**
- [ ] Each registry is a versioned collection: `registryVersion` (Q3 — per-registry-file wrapper vs per-entry) so the
  §13 store can stamp + compat-check it. Per the version-stamp convention (forbidden-pattern 4: never drop `registryVersion`).

**C. Load-time validator (§11 — the first 0.5x slice with real logic)**
- [ ] A pure `validate_registry(...)` that checks **structural validity + `registryVersion` present + id/key uniqueness**
  within a registry. Returns findings (Q5 — `ErrorEnvelope`-based vs a registry-local result). Deterministic + test-first.
- [ ] **Scope boundary (Q2):** the load-time validator does NOT do donor resolution (the Donor-Library subsystem +
  catalog are Phase-1/runtime) or rule-semantics evaluation (S3 + the engine) — only structural/version/uniqueness.

**D. Freeze + preflight**
- [ ] **Schema-snapshot test** over the entry models + the collection wrapper, tagged `spec(§11)` → `registries.schema.json`.
- [ ] Validator tests (good registry passes; missing `registryVersion` / duplicate id / malformed entry each rejected with
  the right finding); JSON round-trip + boundary rejection (`extra="forbid"`); `test_registries_import_direction`
  (registries imports only what Q5 settles — ideally just `error`). `/preflight` clean.

## Wiring / entry point (Step 7.5)
`none — wiring lands in 0.7 (the store loads + caches validated registries into Postgres) + Phase-1 S3 (seeds + pins
the rule grammar) + Phase-2 (the engine evaluates eligibility/validation rules) + 0.6 (codegen).` The load-time
validator is a **pure function** here (no I/O); its production caller is the 0.7 store loader. Reachability surface =
the `spec(§11)` snapshot + importability from `aisims_contracts.registries` (+ the validator is unit-reachable). Frozen-
contract + pure-validator surface, not runtime-wired.

## Files expected to touch
**New:**
- `packages/contracts/src/aisims_contracts/registries.py` — the 3 entry models + the rule-grammar representation + the
  collection/`registryVersion` wrapper + `validate_registry`.
- `packages/contracts/tests/test_registries.py` — A–D tests (reuse the `intra_imports` conftest fixture).
- `packages/contracts/tests/__snapshots__/registries.schema.json` — the `spec(§11)` snapshot.

**Modified:**
- `packages/contracts/src/aisims_contracts/__init__.py` — re-export the registry models + `validate_registry`.

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `tests/test_registries.py`
1. **`test_registry_entry_models`** — the 3 entry models + field sets exact; `extra="forbid"`; round-trip. Why: §11 entries.
2. **`test_open_registry_not_enum`** — entry `id`/`key`/`name` are `str` (open registry, Inv6) — NOT closed enums. Why: §11/Inv6.
3. **`test_rule_subgrammar_representation`** — the rule fields exist in the flexible representation chosen at Q1 (not over-specified). Why: §11 S3-deferred grammar.
4. **`test_registry_version_present`** — the collection carries `registryVersion` (per Q3); a registry missing it is rejected. Why: §11/§13 + forbidden-pattern 4.
5. **`test_validate_registry_ok`** — a well-formed registry passes. Why: §11 load-time validation.
6. **`test_validate_registry_rejects`** — missing `registryVersion` / duplicate id-or-key / malformed entry each produce the right finding. Why: §11 structural validation.
7. **`test_validate_registry_scope_boundary`** — the validator does NOT attempt donor resolution / rule-semantics (e.g. an unresolved `donorRef` is NOT a load-time failure here). Why: Q2 boundary (donor-resolution/S3 are later).
8. **`test_registries_import_direction`** — `registries.py` imports only `error` (Q5) — disjoint {ipc,domain,responses,providers,workers}. Why: Lesson 5/7.
9. **`test_registries_schema_snapshot`** *(§2.5-seam, `spec(§11)`)*. Why: Lesson 1.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** NEW `registries.py` (§11 seam). Appendix-A already lists PlacementType/FunctionalArchetype/
  DonorMapping (§11, C/D↔registries) — confirm == shipped; reconcile the `eligibilityPredicate`/`eligibilityRules`
  naming (Q4) in §11 + Appendix-A if needed.
- **Orchestrator doc rows to write hot (Step 9):** add the **registries** row to `CLAUDE.md` cross-doc table
  (`pin: tests/test_registries.py::test_registries_schema_snapshot`); the §11/Appendix-A naming reconcile.
- **§2.5-seam touched?** **YES** (`registries.py`, C/D↔registries). Snapshot mandatory this cycle.
- **Inv6 link:** this is the registry the domain `archetype`/`placementCategory` `str` keys (0.4a) validate against —
  note the cross-model relationship (the validator is the eventual enforcement point for Inv6 at load time).

## Things to flag at Step 2.5
0. **(SIZE) commit count.** `registries.py` = entry schemas (frozen shapes) + the load-time validator (real logic).
   My default: **1 commit** (one seam-family) — but the validator is the first 0.5x logic, so if you'd rather split
   C1 schemas + snapshot / C2 validator for bisectability, surface it. No safety invariant is *implemented* (the
   validator is structural; Inv6 enforcement at load is its eventual job but the registry data isn't here).
1. **(LOAD-BEARING) Rule sub-grammar depth — how much to freeze before S3.** §11 says S3 (Phase 1) pins the tuning-graft +
   eligibility sub-grammars. My default: freeze the **entry envelopes** + represent each rule list as a flexible
   structured type (e.g. `list[RuleSpec]` where `RuleSpec` is a thin `{kind: str, params: dict[str,Any]}`, OR
   `list[dict[str,Any]]`) — enough to round-trip + snapshot, NOT a full typed grammar that would pre-empt S3. Closing the
   grammar now (before S3 proves it) is the same regression as closing an open registry. Surface your read — this is the
   load-bearing call.
2. **(LOAD-BEARING) Load-time validator scope + return.** My default: checks **structural validity + `registryVersion`
   present + id/key uniqueness** only; NOT donor resolution (Donor-Library subsystem / Phase-1) or rule-semantics (S3/engine). Returns a list
   of findings. Q5 settles the finding TYPE.
3. **`registryVersion` placement.** My default: a **per-registry collection wrapper** `{registryVersion: int, entries:
   list[Entry]}` (one version per registry file, matching "each [registry] carries a registryVersion") — not per-entry.
   Confirm `int` (like `schemaVersion`) vs `str`.
4. **`eligibilityRules` vs `eligibilityPredicate` naming.** §11 prose says `eligibilityPredicate`; DATA_MODEL.md +
   §11's own entry list say `eligibilityRules`. My default: **`eligibilityRules`** (plural, matches DATA_MODEL +
   the validationRules/tuningGraftRules list-shape) and I reconcile §11's prose `eligibilityPredicate` → `eligibilityRules`
   in the arch (atomic with the round). Confirm.
5. **`registries.py` import direction + validator-finding type.** My default: registries imports **only `error`** — the
   validator returns findings built on `ErrorEnvelope` (0.2) or a small registry-local `RegistryError` (NOT the domain
   `ValidationResult`, which would couple registries→domain and break the clean seam). Confirm — this keeps the import
   DAG `error ← registries`.
6. **Out of scope (confirm):** the seeded registry **content/data** (the actual PlacementType/Archetype/DonorMapping
   entries — Phase-1 S3 seeds one, later phases more); loading into **Postgres** (0.7 store); **donor resolution** +
   the Donor-Library catalog (Phase-1/runtime); rule-semantics **evaluation** (S3 + Phase-2 engine).

## Dependencies + sequencing
- **Depends on:** 0.2 (`ErrorEnvelope` for findings), 0.4 (the domain `archetype`/`placementCategory` keys these
  registries back — Inv6). Independent of 0.3/0.5a/0.5b (sibling seams).
- **Blocks:** 0.6 (codegen → TS), 0.7 (the store loads + caches validated registries), Phase-1 S3 (seeds + pins the rule
  grammar against this schema), Phase-2 (the engine evaluates the rules).

## Estimated commit count
**1** (per Q0). `registries.py` (entry schemas + collection/version + the load-time validator) + the `spec(§11)`
snapshot is one bisectable seam-family. Split to 2 (schemas / validator) only if you judge the validator separately
cherry-pickable.

## Lessons-logged candidates anticipated
- **Convention candidate** — a registry contract freezes the entry *envelope* + an open rule representation; the rule
  *grammar* that a spike (S3) will pin stays flexible (`{kind, params}` / `dict`) so freezing doesn't pre-empt the spike —
  the registry-seam analogue of the open-`params`/open-key rule (Lessons 2/7).
- **Architecture-doc note candidate** — reconcile §11 `eligibilityPredicate` → `eligibilityRules`; record that
  `validate_registry` is the load-time enforcement point for Inv6 (the domain keys validate against these registries).
- **Convention candidate** — a contract package can ship a pure *validator function* (not just frozen models) when the
  validation is deterministic + structural; it's TDD'd like any logic (good/bad fixtures), distinct from the snapshot freeze.

## How to invoke
1. Read this brief + `ARCHITECTURE.md §11` (+ DATA_MODEL.md "Registry entries") end-to-end.
2. **`/tdd registry_contracts`** (continuing session; no `/session-start`).
3. **Step 2.5** — answer Q0–Q6 (Q1 grammar-depth + Q2 validator-scope are the load-bearing calls); coverage map. Wait
   for `APPROVED.` before GREEN.
4. **Step 9** — surface the registries cross-doc row + the §11/Appendix-A naming reconcile + lessons.
