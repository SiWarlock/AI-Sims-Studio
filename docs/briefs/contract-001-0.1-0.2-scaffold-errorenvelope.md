# /tdd brief — monorepo_scaffold_and_error_envelope

## Feature
Stand up the §2.5 monorepo scaffold + pinned strict-typing toolchain (task 0.1), then define the frozen **`ErrorEnvelope`** contract (§17) as the first Pydantic→JSON-Schema shared model, guarded by a **schema-snapshot test** (task 0.2, the §2.5-seam requirement).

## Use case + traceability
- **Task ID:** 0.1, 0.2
- **Architecture sections it implements:** `ARCHITECTURE.md §2.5` (subsystem boundaries → directory layout + the frozen-contract seam), §17 (ErrorEnvelope taxonomy), §4 (pydantic→JSON-Schema→TS sync seam the package layout must support), §12 (domain/contract inventory + `schemaVersion` convention).
- **Related context:** Greenfield Phase 0, contract track (serial bottleneck — lands first; downstream tracks fork from `track/contract`). Area dirs already exist with `CLAUDE.md`+`LESSONS.md` only — this slice adds the toolchain manifests + the first contract. `ErrorEnvelope` already has an Appendix-A row (`ARCHITECTURE.md` line ~402) + a tracker enum list (0.2). Stale commit `45065ff` is a SUPERSEDED architecture (Tauri/React18/Py3.12) — ignore it; author fresh against Electron/React19/Vite/Py3.13.

## Acceptance criteria (what "done" means)

**0.1 — scaffold + toolchain**
- [ ] Root monorepo workspace config exists: pnpm workspace (`apps/desktop`, `workers/export`) + uv workspace (`packages/contracts`, `services/pipeline`, `workers/blender`, `evals`) + version pins (`.tool-versions` / `.python-version` + `.nvmrc`): Python 3.13, Node 22 LTS.
- [ ] Each code area has a manifest skeleton (`pyproject.toml` / `package.json`) wired for strict typing + lint: Python → ruff + `mypy --strict` + pytest; TS → `tsc --noEmit` strict + ESLint + Vitest. Each area's empty package **lints + type-checks + collects tests clean**.
- [ ] `services/pipeline/{graph,adapters,engine,registries,store,obs}/` package dirs exist (importable empty packages).
- [ ] Blender 5.1 detect note + Postgres+pgvector bundle-plan note recorded (manifest dependency placeholder + one-line plan comment) — not bundled here (deployment/packaging is Phase 10).
- [ ] `/preflight` (or per-area lint+type+test) clean on the empty scaffold.

**0.2 — ErrorEnvelope**
- [ ] `ErrorEnvelope` Pydantic v2 model with exactly the Appendix-A field set: `code, category, retryable, creatorMessage, maintainerDetail, traceRef, suggestedAction`.
- [ ] `code` is a closed enum = the §17 set (PROVIDER_TIMEOUT, PROVIDER_RATE_LIMIT, PROVIDER_AUTH_QUOTA, PROVIDER_OUTAGE, ARTIFACT_EXPIRED, MALFORMED_OUTPUT, MESH_QA_FAILED, GEOM_EXPORT_FAILED, DBPF_WRITE_FAILED, TEST_INSTALL_FAILED, DISK_FULL, VALIDATION_FAILED, SYSTEM).
- [ ] `category` is a closed enum = {provider, network, validation, geometry, packaging, budget, system} (§17).
- [ ] `retryable: bool`; required vs optional fields pinned (see Step-2.5 Q4).
- [ ] Pydantic rejects an out-of-enum `code` / `category` at the boundary.
- [ ] JSON round-trip (`model_dump_json` → `model_validate_json`) preserves equality.
- [ ] **Schema-snapshot test** (§2.5-seam): `ErrorEnvelope.model_json_schema()` field-name set + enum members == a checked-in snapshot, tagged `spec(§17)`. A drifted snapshot is the failure.
- [ ] All unit tests in `packages/contracts/tests/test_error.py` pass.
- [ ] `/preflight` clean.
- [ ] Cross-doc invariant: `ErrorEnvelope` row flagged at Step 9 for the orchestrator to write into `packages/contracts/CLAUDE.md` cross-doc table (Appendix-A row already exists).

## Wiring / entry point (Step 7.5)
`ErrorEnvelope` is a frozen contract type — its runtime emit sites (SSE `error` event + `Step.error` + `ValidationResult`, §4/§17) land in **0.3 (IPC)** and **Phase 2 (engine)**. For THIS slice the reachability surface is the **schema-snapshot test** (the contract's guard) + the model being importable from the `contracts` package. The 0.1 scaffold's entry point is the toolchain itself (preflight lint/type/test runs against every area's manifest). Runtime wiring: `none — wiring lands in 0.3 + 2.x`.

## Files expected to touch
**New (0.1):**
- `pnpm-workspace.yaml`, root `package.json`, root `pyproject.toml` (uv workspace), `.tool-versions` (+ `.nvmrc` / `.python-version`), `.npmrc` (as needed) — root workspace + pins.
- `packages/contracts/pyproject.toml` + `packages/contracts/src/<pkg>/__init__.py` + `packages/contracts/tests/__init__.py` — the contract package (this slice's home).
- `services/pipeline/pyproject.toml` + `services/pipeline/{graph,adapters,engine,registries,store,obs}/__init__.py` — sidecar skeleton.
- `workers/blender/pyproject.toml`, `evals/pyproject.toml` — uv area skeletons.
- `workers/export/package.json`, `apps/desktop/package.json` — pnpm area skeletons (strict TS config: `tsconfig.json`, `eslint.config.js`, `vitest.config.ts` as minimal as each needs to lint/type/test clean empty).

**New (0.2):**
- `packages/contracts/src/<pkg>/error.py` — the `ErrorEnvelope` model + the two enums.
- `packages/contracts/tests/test_error.py` — the RED tests.
- `packages/contracts/tests/__snapshots__/error_envelope.schema.json` — the committed JSON-Schema snapshot.

**Modified:** none. (`packages/contracts/CLAUDE.md` cross-doc row + `ARCHITECTURE.md` are orchestrator territory — flag at Step 9, do not edit.)

If implementation needs files beyond this list (e.g. a shared `tsconfig.base.json`), **flag at Step 2.5** before GREEN.

## RED test outline (Step 2)
Tests in `packages/contracts/tests/test_error.py` (0.1 has no behavioral RED — its gate is preflight cleanliness on the empty scaffold):

1. **`test_error_envelope_field_set`** — model fields == exactly {code, category, retryable, creatorMessage, maintainerDetail, traceRef, suggestedAction}.
   - Asserts: `set(ErrorEnvelope.model_fields) == {…}`; required/optional split per Q4.
   - Why: Appendix-A `ErrorEnvelope` row + §17.
2. **`test_error_code_enum_members`** — `code` enum value-set == the §17 closed set (exact membership, no extras/omissions).
   - Asserts: `{e.value for e in ErrorCode} == {…13 codes…}`.
   - Why: §17 stable per-stage enum.
3. **`test_error_category_enum_members`** — `category` enum == {provider, network, validation, geometry, packaging, budget, system}.
   - Asserts: closed-set equality.
   - Why: §17 category set.
4. **`test_error_envelope_rejects_unknown_code`** — constructing with an out-of-enum `code` (and `category`) raises `ValidationError`.
   - Asserts: Pydantic boundary rejection.
   - Why: §17 closed enum + deterministic boundary validation (root `CLAUDE.md` safety rule 6).
5. **`test_error_envelope_round_trip`** — `model_validate_json(model_dump_json(x)) == x` for a fully-populated and a minimal (optionals omitted) instance.
   - Asserts: serialization stability across the IPC/SSE boundary.
   - Why: §4 frozen py↔ts guarantee (JSON is the wire form).
6. **`test_error_envelope_schema_snapshot`** *(the §2.5-seam guard)* — `ErrorEnvelope.model_json_schema()` (normalized) == checked-in `error_envelope.schema.json`. **Tag the test `spec(§17)`** so `spec-lint tests 0` finds it.
   - Asserts: field-name set + enum members frozen against the snapshot.
   - Why: §2.5 shared-contract freeze; ARCHITECTURE Appendix-A "freeze before tracks fork."

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** NEW model `ErrorEnvelope` (+ `ErrorCode`, `ErrorCategory` enums).
- **Orchestrator doc rows to write hot (Step 9 routing):** add the `ErrorEnvelope` row to `packages/contracts/CLAUDE.md` cross-doc invariants table with `pin: tests/test_error.py::test_error_envelope_schema_snapshot`. `ARCHITECTURE.md` Appendix-A row already exists (~line 402) — orchestrator confirms its field list matches the shipped model; if Q1/Q4 change a field/enum name, that's an atomic Appendix-A + §17 edit same round.
- **§2.5-seam (shared-contract) model touched?** YES — `ErrorEnvelope` is shared across ALL tracks. The schema-snapshot test (RED #6, tagged `spec(§17)`) is mandatory in this cycle.

## Things to flag at Step 2.5
1. **`PROVIDER_AUTH/QUOTA` enum spelling.** §17 writes the slash-form (and elsewhere "401/402"). Enum can't hold a slash. Split into `PROVIDER_AUTH` + `PROVIDER_QUOTA`, or one `PROVIDER_AUTH_QUOTA`? My default vote: **single `PROVIDER_AUTH_QUOTA`** — matches §17's grouping ("terminal-config" class). If you prefer the 401/402 split, that's an Appendix-A/§17 wording reconcile (orchestrator writes). Contract-surface call — surface it.
2. **Does `ErrorEnvelope` carry `schemaVersion`?** §4 says "all *persisted* entities carry `schemaVersion`"; ErrorEnvelope is transient (embedded in SSE `error`/`Step.error`/`ValidationResult`), and neither §17 nor Appendix-A lists the field. My default vote: **no `schemaVersion` on ErrorEnvelope** — it rides inside versioned envelopes (SSE negotiates `contractVersion` §4; Step/ValidationResult persist with their own version).
3. **Package name + layout.** A top-level `contracts` package risks import collisions. My default vote: **`src/aisims_contracts/` package (`from aisims_contracts.error import ErrorEnvelope`), `src`-layout, hatchling/uv build**. Confirm before GREEN — every later contract (0.3/0.4/0.5) imports from here, so the package name is load-bearing.
4. **Field optionality.** My default vote: **required = {code, category, retryable, creatorMessage, maintainerDetail}; optional (`None` default) = {traceRef, suggestedAction}** — a trace may not exist at error time; a suggested action may be absent.
5. **Scaffold depth (0.1).** Full per-area app bootstrap, or skeleton manifests that lint/type/test clean empty? My default vote: **skeleton manifests only** — deep per-area bootstrap (Electron/Vite/React19 in `apps/desktop`, @s4tk in `workers/export`, the `bpy` harness in `workers/blender`) is each downstream track's first-phase work. 0.1 gives every area a compiling/linting empty skeleton so tracks fork clean. Come-back guidance: each track's Phase-N.1 fleshes its area. (Scope-shaping — confirm.)
6. **Snapshot mechanism.** syrupy (used in `evals/`) vs a plain checked-in `.json` + assert. My default vote: **plain checked-in `error_envelope.schema.json` + normalized compare** — language-agnostic, diff-reviewable, no extra dep in the contracts package.

## Dependencies + sequencing
- **Depends on:** none (greenfield). **Blocked by:** the spec-lint Task-ID fix (Finding raised separately — the mandatory pre-dispatch gate can't PASS on numeric task IDs until it lands).
- **Blocks:** 0.3 (IPC — carries `ErrorEnvelope` in SSE `error`/error codes), 0.4 (domain — `ValidationResult.error`), 0.5 (provider/worker reports), 0.6 (codegen consumes the snapshot to emit TS — TS generation for `ErrorEnvelope` is **deferred to 0.6**, not this slice), and Phase 2 (`Step.error`). Every Phase-0 contract + every track depends on the scaffold.

## Estimated commit count
**2.** Distinct logical units, different commit types — keep them as two commits inside this one bundled round:
1. `chore(scaffold): monorepo layout + pinned strict-typing toolchain` (0.1).
2. `feat(contracts): frozen ErrorEnvelope contract + schema-snapshot` (0.2).
Not bundled into one commit (scaffold is large + non-TDD; ErrorEnvelope is the TDD'd contract — bisectability wants them split). Neither touches a safety invariant, so no further atomization needed.

## Lessons-logged candidates anticipated
- **Convention candidate** — "Every §2.5-seam contract ships with a `spec(§X)`-tagged schema-snapshot test in the same `/tdd` cycle; a drifted snapshot is the failure, never a silent regen."
- **Convention candidate** — "Closed enums (`ErrorCode`/`ErrorCategory`) assert exact membership (`==`, not `⊆`) so adding/removing a code is a visible test change."
- **Architecture-doc note candidate** — record the resolved `PROVIDER_AUTH/QUOTA` spelling + the "ErrorEnvelope carries no `schemaVersion`" decision into §17/Appendix-A if Q1/Q2 deviate from the doc's current wording.
- **Future TODO — operational** — TS/Node codegen for `ErrorEnvelope` (consumes this snapshot) is 0.6; carry-forward so 0.6's brief folds it in.

## How to invoke
1. Read this brief end-to-end (don't skip Step-2.5 questions).
2. Run `/session-start` first (first slice of the session), then `/tdd monorepo_scaffold_and_error_envelope`.
3. Step 0 (Restate) — confirm the restatement matches the Feature line + the 0.1/0.2 split.
4. Step 1 — confirm the file list.
5. Step 2.5 — send the test-design write-up + answers to Q1–Q6 (or take defaults); wait for `APPROVED.`/`TWEAK:`/`ADD:` before GREEN.
6. Step 9 — surface the `ErrorEnvelope` cross-doc row + anything beyond the anticipated lessons.

## Addendum — 0.1 scope addition (orchestrator, lead-authorized D7/D8, 2026-06-17)
Resolves the commit-msg hook blocker (stale cross-machine pre-commit residue: `.git/hooks/commit-msg` hardcodes `/Users/nozzins/...` python, no `.pre-commit-config.yaml`, fails every commit) **in-scope as proper toolchain setup — NOT a hook bypass**:

- [ ] Add repo-root `.pre-commit-config.yaml`: ruff (lint) + mypy (types) + a conventional-commits **commit-msg** check. Add `pre-commit` to the uv toolchain (dev dep / tool).
- [ ] Run `uv run pre-commit install --hook-type pre-commit --hook-type commit-msg` to **REGENERATE** valid hooks for THIS machine — replaces the broken residue + unblocks all commits on `track/contract`. Must run **before the first Step-10 commit** (else it fails closed).
- [ ] Add `gitleaks` to the toolchain so `secrets-guard.sh`'s staged-secret scan becomes **blocking** (non-urgent — may trail).
- **Fallback B (harness-classifier caveat):** if `pre-commit install` is DENIED by the Code auto-mode classifier (git-hook write), **STOP** — do not force (no `--no-verify`, no `core.hooksPath`, no hand-editing the hook; all defeat the guardrail + get denied). Flag the orchestrator → deferred user-authorization item. Continue ALL 0.1/0.2 dev (scaffold + ErrorEnvelope + snapshot → green → preflight) regardless; queue commits in order, batch-land once cleared.
