# /tdd brief — s1b_donor_scan

## Feature
The **donor-scan gate** of spike S1b (clone-a-donor): auto-detect the Sims 4 install + its FullBuild
donor packages (EA-App macOS), open a FullBuild donor `.package` **READ-ONLY** via `@s4tk`, and
resolve + report a candidate Build/Buy donor object's required resource set
(OBJD / COBJ / MODL / MLOD / GEOM / FTPT / RIG / _IMG·DST). **De-risks "can `@s4tk` read the EA-App-macOS
donors on this Mac"** before the clone (spikes-004) swaps S1a's GEOM into one. **Hybrid spike:** the
auto-detect path-resolution + resource-set-resolution logic is TDD'd; the actual `@s4tk` parse of a real
~1 GB FullBuild package + donor selection is exploratory run-and-observe.

## Use case + traceability
- **Task ID:** 1.1
- **Architecture sections it implements:** `ARCHITECTURE.md §9` (Sims export — `@s4tk`
  clone-an-EA-donor: open donor read-only, the required resource set), `§10` (Donor Library —
  scan/index the user's Sims 4 install), `§20` (S1 feasibility go/no-go gate), `§22` (open question 6 —
  `@s4tk`/GEOM provenance).
- **Related context:** S1a sealed (`c35913b` on origin/track/spikes) — the GEOM bytes the clone will swap
  are `workers/blender/tests/fixtures/cube_v0x05.geom`. This slice begins the carry-forward
  "full `@s4tk` round-trip validation (last-consumer S1b)" — the donor *read* here, the round-trip
  *write* in spikes-004. Frozen contracts: `ExportJob`/`ExportJobReport` (`aisims_contracts.workers`,
  §9) + the DonorMapping entry schema (0.5c, §11).

### Orchestrator-verified facts (do NOT re-derive — record in the report)
- **Sims 4 install:** `/Applications/EA Games/The Sims 4.app` (EA-App macOS).
- **FullBuild donor packages (the donor source — Build/Buy catalog):**
  `…/The Sims 4.app/Contents/Data/Client/ClientFullBuild{0-8}.package` (~1 GB each) +
  `…/Contents/Data/Simulation/SimulationFullBuild0.package`.
- **Auto-detect's verified default target:** `/Applications/EA Games/The Sims 4.app/Contents/Data/{Client,Simulation}/*FullBuild*.package`.

## Acceptance criteria (what "done" means)
- [ ] **Auto-detect** resolves the Sims 4 install + its FullBuild packages by probing the EA-App-macOS
      default (the verified path above) + an env override `AISIMS_SIMS4_PATH`. If NOT found → returns a
      **structured `not-found`** result (does NOT guess or hardcode a wrong path) so the orchestrator can
      flag it to the lead → user.
- [ ] `@s4tk` added as a `workers/export` dependency (vendor-pinned, §22 Q6).
- [ ] A FullBuild donor `.package` is opened **READ-ONLY** (safety rule 4 — the game's packages are
      never modified; donor bytes immutable). The worker writes only to scratch.
- [ ] A **candidate Build/Buy donor object** is resolved + reported: its OBJD + the linked required
      resource set (OBJD/COBJ/MODL/MLOD/GEOM/FTPT/RIG/_IMG·DST), and the OBJD tuning instance resolves.
- [ ] **Written donor-scan report** (rolls into the eventual S1b verdict; + a scratch JSON the clone
      consumes): install path, packages found, the candidate donor object (TGI keys) + its resource
      manifest, and the **`@s4tk`-reads-EA-macOS-donors** confirmation. FAIL (no install / `@s4tk` can't
      parse the package) → flag + Finding.
- [ ] Deterministic tests green; `/preflight` clean (`tsc --noEmit` + eslint + vitest).

## Wiring / entry point (Step 7.5)
A `workers/export` spike scan entry — `src/donor/scan.ts` exposing the auto-detect + read + resolve,
called from the spike entry `src/spike_clone.ts` (scan stage now; clone stage lands in spikes-004).
Production Donor-Library scan/index into Postgres (§10) is **not** this slice:
`none — production donor-library wiring lands in Phase 5`. Confirm the scan is reached from the spike
entry, not just tests.

## Files expected to touch
**New:**
- `workers/export/src/donor/scan.ts` — auto-detect (install + FullBuild packages), `@s4tk` open
  read-only, candidate-object + required-resource-set resolution.
- `workers/export/src/spike_clone.ts` — the spike entry (scan stage; clone stage = spikes-004).
- `workers/export/test/donor/scan.test.ts` — deterministic tests.
- a small donor-resource fixture for the resource-set-resolution test (a minimal parsed-object shape —
  NOT a real 1 GB package).

**Modified:**
- `workers/export/package.json` — add the pinned `@s4tk` dependency.

If implementation needs files beyond this list, **flag at Step 2.5** before going deep.

## RED test outline (Step 2) — the DETERMINISTIC surface (the real-package parse is exploratory, below)
Tests in `workers/export/test/donor/scan.test.ts`:

1. **`auto_detect_resolves_ea_app_macos_default`** — given the EA-App-macOS layout (mocked fs), returns
   the install root + the FullBuild package list.
   - Why: §10 scan; the verified default path.
2. **`auto_detect_env_override_wins`** — `AISIMS_SIMS4_PATH` set → that path takes precedence.
   - Why: §10 config override (a non-default install).
3. **`auto_detect_not_found_returns_structured_result`** — no install anywhere → a structured
   `not-found` (NOT a guess, NOT a throw).
   - Why: lead's directive — flag, don't guess.
4. **`resolve_required_resource_set`** — given a parsed donor object (fixture), resolves the required
   set (OBJD/COBJ/MODL/MLOD/GEOM/FTPT/RIG/_IMG·DST) + reports any missing.
   - Why: §9 required-resource assertion (the clone needs the full set).
5. **`candidate_donor_ref_conforms`** — the scan emits a `donorRef` shape the clone (`ExportJob.donorRef`)
   consumes.
   - Why: §9 §8↔§9 handoff continuity.

**Exploratory arm (NOT unit-tested — run-and-observe, captured in the report):** `@s4tk` opening a real
`ClientFullBuild*.package` read-only + finding a suitable candidate donor object. The "does `@s4tk` read
the EA-macOS donors" question is answered by running it, not a pre-written unit test (project TDD posture:
the deterministic wrapper is `/tdd`; the external-tool call is the spike).

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — frozen `ExportJob`/`ExportJobReport` + DonorMapping reused unchanged.
- **Orchestrator doc rows to write hot (Step 9):** none expected to the `workers/export/CLAUDE.md`
  cross-doc table. Likely a **lesson** (does `@s4tk` read EA-macOS donors) + a §9/§10 **arch note** →
  route to the **integration-doc-edits ledger** (not a live `ARCHITECTURE.md` edit).
- **Shared-contract (Appendix-A seam) model touched?** No — no schema-snapshot needed.

## Things to flag at Step 2.5
1. **Candidate donor object selection.** Which Build/Buy object to clone for the spike? My default vote:
   **a simple decorative object** (single GEOM/MLOD, no slots/FTPT complexity) for first signal — explore
   the FullBuild index for a candidate; record its TGI keys. A complex/functional object adds risk;
   keep the spike's donor simple (functional behavior is S3, not S1b).
2. **`@s4tk` API surface.** **Pull `@s4tk` docs via Context7 / the `@s4tk` docs site** for the
   Package/resource-read API (don't hand-roll DBPF parsing). My default vote: `@s4tk/models` `Package`
   read APIs (read-only `Package.from(...)` + the resource index/extraction), pinned version; never a
   write path on the donor.
3. **Report destination.** My default vote: the donor-scan result **rolls into the eventual S1b verdict**
   (`docs/sessions`, like S1a) + a **scratch JSON** the clone (spikes-004) consumes for the candidate +
   manifest.
4. **Auto-detect scope.** My default vote: **EA-App macOS** (the verified install) + the env override —
   do NOT over-engineer Steam/cross-launcher for the spike; flag if the user's install differs.

## Dependencies + sequencing
- **Depends on:** 0.5b (`ExportJob`/`ExportJobReport`, sealed) + Sims 4 installed (**VERIFIED**
  `/Applications/EA Games/The Sims 4.app`).
- **Blocks:** **spikes-004 (S1b-clone)** — the GEOM-swap + DBPF round-trip + atomic write (safety rule 4)
  needs this scan's candidate donor + its resource manifest. (S1c in-game test-install is the user's
  hands-on step after the clone produces a validated `.package`.)

## Estimated commit count
**2–3.** (1) auto-detect + the pinned `@s4tk` dep + the read-only donor open; (2) required-resource-set
resolution + the candidate-donor report. **No safety-invariant pin in THIS slice** — the donor is
read-only (enforced by using `@s4tk` read APIs + the forbidden-grep), and the atomic-write / half-package
safety path is spikes-004's (its own security-reviewed commit). The scan only READS donors + writes scratch.

## Lessons-logged candidates anticipated
- **Convention candidate** — whether/how `@s4tk` reads EA-App-macOS FullBuild donors headless (the
  finding) + the read-only-donor access pattern.
- **Architecture-doc note candidate** — §10 donor-source path for EA-App macOS (the verified install +
  FullBuild layout) → integration-doc-edits ledger.
- **Future TODO** — the full `@s4tk` round-trip validation completes in spikes-004 (the clone write).

## How to invoke
1. **Read this brief end-to-end** — note the hybrid split (auto-detect/resource-resolution = TDD; the
   real-package `@s4tk` parse = exploratory) + the 4 Step-2.5 questions.
2. **Run `/session-start`** first — this is your first `workers/export` (TS) slice (you were in
   `workers/blender` for S1a; new area). Then `/tdd s1b_donor_scan`.
3. **Step 2.5** — send the test-design write-up + your candidate-donor pick (Q1) + the `@s4tk` API you
   researched (Q2). A **Step-7.5 early ping is invited** if `@s4tk` can't parse the EA-macOS packages —
   that's a Finding (the donor source isn't readable on Mac), surface it before going deep.
4. **Step 9** — categorized flags + the scan report; route §9/§10 arch notes to the ledger.
