# Session contract-003 — py→ts codegen + CI drift gate (0.6)

- **Date:** 2026-06-17
- **Phase / track:** Phase 0 (Foundations & frozen contracts) · track `contract` · area `packages/contracts`
- **Predecessor:** [contract-002](contract-002-2026-06-17-contract-family-freeze.md) — §2.5 contract family freeze (0.4b–0.5c)
- **Successor:** TBD — a **fresh `services/pipeline`-area implementer** (area transition + context cycle) picks up **0.7** (Postgres store skeleton + Alembic). NOT a `packages/contracts` continuation — the §2.5 contract family + its codegen are complete; Phase 0's remaining slices (0.7–0.9) are sidecar/store work.

## Why this session existed
Make the frozen §2.5 contracts **consumable** as TypeScript and **guard them**: stand up the
pydantic→JSON-Schema→TS codegen (§4) + a CI drift gate so a model change without a regen fails CI.
This is the first non-frozen-contract slice — tooling on top of the now-complete contract family.

## What was built

### Files created
- **`src/aisims_contracts/codegen.py`** — aggregates all 7 contracts' public models (per-module
  introspection) via `models_json_schema` → one deduped combined `$defs`; normalizes field schemas
  (strips titles; collapses `$ref`+`default`); `build_helpers_ts()` emits the `parseErrorCode→SYSTEM`
  tolerance helper; `schema_matches()` = pure-Python schema gate; `check()` + `main(--check)` = the
  full drift gate; `generate()` writes the tree.
- **`scripts/emit-ts.mjs`** — the Node `json-schema-to-typescript` emitter glue (carrier-root → TS).
- **`package.json`** + **`pnpm-lock.yaml`** — pins `json-schema-to-typescript` **15.0.4** (standalone,
  `pnpm install --ignore-workspace`; `packages/contracts` is a uv area, not a pnpm member).
- **`generated/{contracts.schema.json, contracts.ts, helpers.ts}`** — committed codegen output (the
  gate's diff target; never hand-edited — forbidden-pattern 2).
- **`tests/test_codegen.py`** — 8 tests (5 pure-Python core: combined-schema coverage, determinism,
  title-strip, schema-drift passes-clean/fails-on-drift; 3 node-coupled `skipif`: TS emit, drift-TS,
  ErrorCode tolerance).
- **`.github/workflows/contracts-drift-gate.yml`** — the repo's first CI workflow (minimal drift-gate job).

### Files modified
- none (codegen is a `python -m` tooling module — not re-exported via `__init__`; no contract model changed).

### Commits (mine, on `track/contract`)
`033e25f` feat(contracts) codegen pipeline [0.6 C1] · `ee51b24` ci(contracts) drift-gate workflow [0.6 C2].
70 tests green (node-coupled ran, not skipped); mypy --strict + ruff + ruff format clean; `--check` exit 0.

## Decisions made
- **Q1 toolchain (Context7-verified):** Python `models_json_schema` → combined `$defs` →
  `json-schema-to-typescript` (npm) → `generated/contracts.ts`. Rejected a pure-Python emitter (would
  reinvent the discriminated-union/`$ref`/Literal-subset handling and risk subtle bugs). Determinism via
  a fixed `bannerComment` (no timestamp) + sorted keys.
- **Q3 two-level gate:** the **pure-Python schema gate** (`schema_matches`) is the primary, always-runnable
  cross-track enforcement (fully pytest-tested); the node TS gate is secondary. `--check` wraps both.
- **Q5/Q6 carry-forwards DONE:** ErrorCode tolerance = an emitted `parseErrorCode→SYSTEM` helper (strict
  producer / tolerant consumer); field titles stripped codegen-side (no snapshot re-freeze).
- **Emitter quirk fixed:** defaulted-enum fields emit `{"$ref", "default"}`, which made
  json-schema-to-typescript mint duplicate `Foo1` types → the codegen drops the `default` sibling
  (reviewer tightened this to drop ONLY `default`, preserving any meaningful sibling).
- **Reviewer hardening:** pinned the emitter **exact** (`15.0.4`) to kill the Prettier-version drift class;
  guarded `main(--check)` against a missing node (clean message, no stack trace); added a CI step
  asserting the emitter is installed so node tests can't silently skip.
- **Commit split:** C1 = codegen pipeline + generated + tests; C2 = the CI workflow (the `--check` gate
  logic lives in codegen.py/C1; C2 is pure CI wiring).

## Decisions explicitly NOT made (deferred)
- **Snapshot-hardening back-port** (carry-forward C: `min_length=1` on providers/domain/registries ref/key
  fields + value-model-set assertions) → stays its own slice (it re-freezes 3 frozen snapshots; bundling
  into a tooling slice would muddy bisectability). Orchestrator holds + re-triages.
- **ErrorCode-tolerance UI wiring** (Zod boundary) → Phase 7 (the carry-forward's other last-consumer).
  0.6 ships only the `parseErrorCode` primitive.
- **Holistic per-area CI** (lint/type/test jobs for all 6 areas) → Phase-0-exit carry-forward (D20). 0.6
  ships only the minimal §4 drift-gate job.
- **A behavioral (runtime) TS test** for `parseErrorCode` → a contracts vitest / Phase-7 concern; 0.6
  pins the emitted helper's logic structurally in pytest.

## TDD compliance
Clean. 0.6 followed RED (Python-core tests) → Step-2.5 toolchain ruling → GREEN (+ node-coupled tests)
→ reviewer → Step-9 → 2-commit Step-10. The node-coupled tests were written after the Q1 ruling (the
toolchain they exercise was the load-bearing decision), but before their implementation. No violations.

## Reachability
Build-time tooling — **not runtime-wired by design.** `python -m aisims_contracts.codegen` runs the full
chain (verified end-to-end); `--check` exits 0 clean / non-zero on drift (verified); `generated/` is
importable by the consuming tracks (`apps/desktop`, `workers/export`) — they wire it. The CI workflow runs
the gate. No tested-but-unwired gaps (the codegen + gate ARE the surface).

## Cross-doc invariant audit
Multi-track memory check: **no contract model field changed** (0.6 is tooling; titles handled codegen-side,
so no snapshot re-freeze). The codegen-toolchain **arch-note** (§4 + the area `CLAUDE.md` lookup-table row +
the fp-2 generated-artifact rule) was flagged at Step 9; the orchestrator hot-routes it on `/orchestrate-end`.
No undocumented drift.

## Open follow-ups
- **Arch/doc (orchestrator hot-routes):** the §4 codegen-toolchain note + the `generated/` consumer path +
  the standalone `package.json` / `pnpm install --ignore-workspace` tooling note; Lessons 12 (deterministic
  codegen — fixed banner/sorted/no-timestamps or the gate false-positives) & 13 (strict-producer/tolerant-
  consumer for a forward-compatible enum).
- **Carry-forwards:** snapshot-hardening back-port (its own slice); ErrorCode-tolerance UI wiring (Phase 7);
  holistic per-area CI (Phase-0-exit).
- **⚠ Two `/preflight` Findings surfaced (tooling, lead-owned):** (1) the per-area `uv sync` prunes the shared
  workspace `dev` group → run from the workspace root (`--all-packages`); **fixed `93b9a3e`**. (2) the
  contracts-mode build step is `python -m contracts.codegen` (wrong module — should be
  `aisims_contracts.codegen`) AND regenerates instead of `--check` (a preflight verifies, never mutates);
  the orchestrator is fixing it under the D19 tooling precedent.

## How to use what was built
- Regenerate: `uv run python -m aisims_contracts.codegen` (writes `generated/`). Needs node + the emitter
  (`pnpm install --ignore-workspace` in `packages/contracts`).
- Check drift: `uv run python -m aisims_contracts.codegen --check` (exit non-zero on drift). CI runs this.
- A model change flows: edit the pydantic model → regenerate → commit `generated/`. Never hand-edit
  `generated/*` (the gate fails on it). Consumers `import` from `generated/contracts.ts` + `helpers.ts`.
