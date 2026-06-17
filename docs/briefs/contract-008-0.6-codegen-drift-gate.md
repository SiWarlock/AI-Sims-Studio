# /tdd brief — codegen_drift_gate

## Feature
Stand up the **py→ts codegen + CI drift gate** (§4): pydantic models are the single source → JSON Schema (the
existing `*_schema()` producers / checked-in snapshots) → generated **TypeScript** types consumed by the UI
(`apps/desktop`) and the Node `@s4tk` worker (`workers/export`); a **CI gate fails on drift** (generated output
out of sync with the pydantic source). This is the first non-frozen-contract slice — tooling, not a §2.5 model.

## Use case + traceability
- **Task ID:** 0.6
- **Architecture sections it implements:** `ARCHITECTURE.md §4` ("py↔ts sync (frozen guarantee): pydantic models
  are the single source → JSON Schema → generated TS (UI) + Node (worker) types; CI drift gate fails on divergence").
- **Related context:** Phase 0, contract track. **All 7 §2.5 contracts are frozen** (error/ipc/responses/domain/
  providers/workers/registries), each with a `spec(§X)` snapshot + a `*_schema()` producer — those are this slice's
  inputs. Conventions: forbidden-pattern 2 (NEVER hand-edit generated TS/JSON artifacts — they're codegen output,
  gated by the drift check). The **consuming** side (importing the generated types in `apps/desktop`/`workers/export`)
  is those tracks' concern, NOT here — 0.6 produces the types + the gate.

## Acceptance criteria (what "done" means)

**A. Codegen pipeline (§4)**
- [ ] A codegen entry (`python -m aisims_contracts.codegen` per the area `CLAUDE.md`, + whatever Node step the TS
  emitter needs — Q1) that takes the pydantic-sourced JSON Schema for **every** frozen contract (error/ipc/responses/
  domain/providers/workers/registries) and emits **TypeScript** types to a generated output tree (Q4).
- [ ] **Single source = pydantic.** The codegen derives the JSON Schema from the pydantic models (the `*_schema()`
  producers), NOT from a hand-maintained schema (Q2) — so a model change flows through to TS.
- [ ] The generated TS covers all frozen contracts; a consumer (`apps/desktop` / `workers/export`) can import them
  (importability is the surface — actual consumption is those tracks).

**B. CI drift gate (§4)**
- [ ] A **`--check` mode** (regenerate to a temp + diff against the committed generated output; exit non-zero on any
  difference) so a model change without a regen **fails the gate** (Q3). Plus a CI workflow step that runs it.
- [ ] The gate is deterministic + reproducible (stable ordering, no timestamps in the output) so a clean tree always
  passes and a real drift always fails.

**C. Carry-forward folded in (origin 0.2/0.5b — last-consumer 0.6)**
- [ ] **ErrorCode consumer-tolerance** (carry-forward, origin 0.2/D10b): the generated TS for `ErrorCode` (+ its
  consumers) must **degrade gracefully on an unrecognized code → `SYSTEM`**, so a future additive enum split is
  non-breaking. The producer stays a strict closed enum; tolerance lives in the generated/consumer TS (Q5).
- [ ] **JSON-Schema field titles** (carry-forward, origin 0.2): generated consumer types should read well — either
  add `Field(title=…)` to the models (re-freezes those snapshots) OR handle titles in the codegen (Q6). My default:
  handle in codegen (avoid re-freezing 7 snapshots).
- [ ] **Snapshot-hardening back-port** (carry-forward, origin 0.5b — optional, can ride this slice): `min_length=1`
  on path/ref `str` fields (providers `urls`/refs + domain path fields + registry `id`/`key`/`name`) + the explicit
  value-model-SET assertion in the providers/domain snapshot tests. Fold in if cheap; else leave in carry-forward.

**D. Tests + preflight**
- [ ] Deterministic tests: codegen produces the expected TS for a representative contract (snapshot the generated TS);
  the `--check` gate passes on a clean tree and **fails on an injected model/TS drift**; the ErrorCode-tolerance
  behavior is pinned. `/preflight` clean (note the workspace-root `uv sync` Finding — see "Wiring/notes").

## Wiring / entry point (Step 7.5)
`none at runtime — this is build-time tooling.` The codegen entry is `python -m aisims_contracts.codegen` (+ the Q1
Node step); the drift gate runs in CI (the workflow) + locally via `--check`. The generated TS is **imported by**
`apps/desktop` + `workers/export` (those tracks wire it). Reachability surface = the codegen runs end-to-end (schemas
→ TS), the `--check` gate exits correctly on clean/drift, and the generated output is importable. NOTE: `/preflight`'s
per-area `uv sync` prunes the shared workspace `dev` group — run `uv sync` from the **workspace root** (Finding flagged
to the lead this round).

## Files expected to touch
**New:**
- `packages/contracts/src/aisims_contracts/codegen.py` — the codegen entry (schemas → TS; + the Node emitter glue, Q1).
- Node codegen glue (Q1) — e.g. `packages/contracts/package.json` + a TS-emit script if `json-schema-to-typescript`
  (npm) is the emitter, OR a pure-Python emitter — surface at Q1.
- `packages/contracts/generated/**` (Q4) — the generated TS output tree (codegen output; never hand-edited, fp-2).
- `packages/contracts/tests/test_codegen.py` — A/B/D tests (codegen output snapshot + the drift-gate behavior).
- A CI workflow step (`.github/workflows/…` or the project's CI location) running the `--check` gate.

**Modified:**
- `packages/contracts/pyproject.toml` / `package.json` — the codegen dep(s) + script entry.
- (Q6) the contract models if `Field(title=)` is chosen over codegen-side title handling — would re-freeze those snapshots.

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `tests/test_codegen.py`
1. **`test_codegen_emits_ts_for_all_contracts`** — running codegen produces TS for every frozen contract; the output
   matches a committed snapshot of the generated TS. Why: §4 single-source→TS.
2. **`test_drift_gate_passes_clean`** — `--check` on the committed tree exits 0. Why: §4 gate (no false positives).
3. **`test_drift_gate_fails_on_drift`** — inject a model/schema change (or mutate the committed TS) → `--check` exits
   non-zero. Why: §4 gate catches divergence (the load-bearing behavior).
4. **`test_errorcode_tolerance`** — the generated `ErrorCode` consumer maps an unknown code → `SYSTEM` (not a parse
   error). Why: carry-forward 0.2/D10b (forward-compat).
5. **`test_codegen_deterministic`** — two runs produce byte-identical output (stable ordering, no timestamps). Why:
   the gate must be reproducible.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none (tooling) — UNLESS Q6 picks `Field(title=)`, which adds a (cosmetic) field attr to
  the contract models + re-freezes their snapshots → flag as a cross-doc/snapshot change.
- **Orchestrator doc rows to write hot (Step 9):** the `packages/contracts/CLAUDE.md` lookup-table row "py↔ts sync
  (… codegen + CI drift gate) → §4" already exists — confirm it points right; add a forbidden-pattern note if the
  generated-output path differs from the assumed `generated/`. No new §2.5 model row (tooling).
- **§2.5-seam touched?** No new model — but the codegen is the mechanism that makes the frozen contracts *consumable*,
  so the drift gate is effectively the cross-track enforcement that the TS == the pydantic source.

## Things to flag at Step 2.5
0. **(SIZE) commit count.** My default: **1–2** — C1 the codegen pipeline + generated output + its tests; C2 the
   `--check` drift gate + the CI workflow. Surface your split (the gate is the load-bearing half).
1. **(LOAD-BEARING) Codegen toolchain + the py/npm boundary.** The schemas come from Python (`*_schema()`); TS
   emission is typically an **npm** tool. My default: `python -m aisims_contracts.codegen` writes the JSON Schemas,
   then a Node step runs **`json-schema-to-typescript`** (mature npm) to emit TS — chained by a script; the drift gate
   wraps the whole chain. Alternatives: a pure-Python TS emitter (avoids npm but reinvents a mature tool), `pydantic2ts`,
   or `quicktype`. **Verify the current `json-schema-to-typescript` API via Context7** before committing. Surface your
   read — this shapes the whole slice.
2. **Single source — regenerate schema from pydantic at codegen time, or read the checked-in `*.schema.json` snapshots?**
   My default: regenerate from the `*_schema()` producers (pydantic-sourced, always current); the checked-in snapshots
   stay the freeze guard (a separate test). Confirm — reading the snapshots instead would make the codegen lag a
   model change until a re-freeze.
3. **Drift-gate mechanism.** My default: `codegen --check` regenerates to a temp + diffs against the committed
   `generated/` tree, exits non-zero on any diff; CI runs it. Alternative: `git diff --exit-code` after a regen.
   Confirm + how the CI step is wired.
4. **Generated-output location.** My default: `packages/contracts/generated/` (per the area `CLAUDE.md` module-layout —
   "generated/ is OUTPUT of codegen, imported BY other areas"). Confirm the path the UI + worker will import from
   (workspace-relative).
5. **ErrorCode tolerance shape (carry-forward).** My default: emit `ErrorCode` as a TS union of the known literals
   **plus** a consumer helper / `parseErrorCode(x): ErrorCode` that returns `SYSTEM` on an unknown — strict producer,
   tolerant consumer. Confirm the exact TS shape (a branded type? a `| string` fallback? a parse helper?).
6. **Field titles — codegen-side vs `Field(title=)`.** My default: handle titles in the codegen (avoid re-freezing 7
   snapshots for cosmetic JSDoc). Confirm — `Field(title=)` is cleaner long-term but churns every snapshot now.

## Dependencies + sequencing
- **Depends on:** 0.2 + 0.3 + 0.4 + 0.5 (all the frozen contracts + their `*_schema()` producers — ALL LANDED).
- **Blocks:** the TS-consuming tracks (`apps/desktop` UI, `workers/export`) — **codegen gates their fork** (per D18,
  they fork after this track's Phase 0 + integration merge); Phase 2 (typed IPC client).

## Estimated commit count
**1–2** (per Q0). C1 codegen pipeline + generated output + tests; C2 the `--check` drift gate + CI workflow. The gate
is the load-bearing half — keep it cleanly bisectable.

## Lessons-logged candidates anticipated
- **Convention candidate** — generated artifacts are NEVER hand-edited (fp-2); the drift gate is the enforcement, and
  it must be deterministic (stable ordering, no timestamps) or it false-positives.
- **Architecture-doc note candidate** — record the codegen toolchain (the py→JSON→TS chain + the chosen emitter) +
  the generated-output path that consumers import, in §4 / the area `CLAUDE.md` lookup table.
- **Convention candidate** — strict producer + tolerant consumer for a forward-compatible enum (ErrorCode → SYSTEM
  fallback in the generated TS), so an additive enum split is non-breaking.

## How to invoke
1. Read this brief + `ARCHITECTURE.md §4` end-to-end; **Context7 the `json-schema-to-typescript` (or chosen emitter)
   current API** before Step 2.5.
2. **`/tdd codegen_drift_gate`** (continuing session; no `/session-start`).
3. **Step 2.5** — answer Q0–Q6 (Q1 toolchain + Q3 drift-gate are the load-bearing calls); coverage map. Wait for
   `APPROVED.` before GREEN.
4. **Step 9** — surface the codegen toolchain arch-note + the lookup-table confirm + lessons (+ the carry-forward
   resolutions: ErrorCode tolerance, field titles, snapshot-hardening).
