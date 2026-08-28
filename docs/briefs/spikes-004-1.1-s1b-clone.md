# /tdd brief — s1b_clone

## Feature
The **clone** stage of spike S1b — the safety-critical half: take the donor-scan's candidate, resolve
the deferred `[COBJ, MLOD, GEOM]` chain (OBJD→MODL→MLOD→GEOM + COBJ, possibly cross-package), **swap in
S1a's emitted GEOM**, preserve OBJD→tuning / FTPT / RIG / SLOT, re-serialize the DBPF via `@s4tk`, and
**atomically write a round-trip-validated `.package`** (safety rule 4) to a sidecar scratch dir — the
artifact the user installs for the **S1c in-game test-install**. This closes the @s4tk clone-a-donor
half of S1. **Hybrid spike:** the clone mechanics + the atomic-write safety sequence + round-trip
validation are DETERMINISTIC (TDD'd, the atomic-write path test-pinned as its own safety commit); the
real cloned `.package` from the live candidate donor is exploratory run-and-observe → the verdict.

## Use case + traceability
- **Task ID:** 1.1
- **Architecture sections it implements:** `ARCHITECTURE.md §9` (Sims export — clone-an-EA-donor: swap
  GEOM + textures + thumbnail + COBJ, preserve OBJD→tuning/FTPT/RIG/SLOT, re-serialize; the required
  resource set; **atomic write = temp→fsync→DBPF round-trip validate→atomic rename, donors read-only,
  never a half-package in Mods — safety rule 4 / Invariant 4**), `§10` (Donor Library — the donor chain),
  `§20` (S1 feasibility go/no-go), `§22` (open question 6 — `@s4tk`/GEOM provenance).
- **Related context:** S1b donor-scan sealed (`35ee2e3`, round `b8bca40`) — consume its
  `DonorCandidate{donorRef: "<packagePath>#<objectKey>"}` + `resourceManifest`; the candidate is
  `0xC0DB5AE7:0x00000000:0x031A` with `[COBJ,MLOD,GEOM]` deferred-to-clone. S1a's emitted GEOM is
  `workers/blender/tests/fixtures/cube_v0x05.geom` (the bytes to swap in — proves the S1a→S1b chain).
  Frozen contracts: `ExportJob`/`ExportJobReport` (`aisims_contracts.workers`, §9). **Consumes the
  carry-forward "real-GEOM @s4tk round-trip validation (last-consumer S1b)".**

## Acceptance criteria (what "done" means)
- [ ] **Chain resolution:** resolve the candidate's deferred `[COBJ, MLOD, GEOM]` via OBJD→MODL→MLOD→GEOM
      + the COBJ — across the FullBuild set if the chain refs leave the candidate's package (Step-2.5 Q2).
- [ ] **Clone:** swap S1a's GEOM bytes into the donor's GEOM resource; swap thumbnail + COBJ; **preserve
      OBJD→tuning, FTPT, RIG, SLOT** unchanged. The donor is opened **READ-ONLY** (rule 4 — game packages
      never modified).
- [ ] **Re-serialize** the cloned DBPF via `@s4tk` (the full required resource set: OBJD/COBJ/MODL/MLOD/
      GEOM/FTPT/RIG/_IMG·DST).
- [ ] **🔒 Atomic validated write (safety rule 4) — its OWN commit, security-reviewed:** write to a temp
      path → `fsync` (file + dir) → **DBPF round-trip + structural validate** (re-open via `@s4tk`: the
      required resource set is present, the swapped GEOM is present, the OBJD tuning instance resolves) →
      **atomic rename** into the scratch output dir. **On validation failure: NO rename, NO partial file**
      (the temp is discarded). **Never** write into a live Sims Mods folder; the worker writes **scratch
      only** (rule 3).
- [ ] Returns a contract-valid `ExportJobReport` (`succeeded` ⟹ `packagePath` in scratch + `error` None;
      `failed` ⟹ `error` + no package; rule-6 status↔outputs).
- [ ] **Written S1b-clone verdict** (`docs/sessions`): the candidate cloned, the resolved chain, the
      round-trip-validation result, the **scratch `.package` path** + an explicit **"READY for the user's
      S1c in-game test-install"** flag (with the install instruction). FAIL → flag + Finding.
- [ ] Deterministic tests green (the atomic-write safety sequence + clone mechanics + round-trip);
      `/preflight` clean (`tsc --noEmit` + eslint + vitest).

## Wiring / entry point (Step 7.5)
The clone stage of `workers/export/src/spike_clone.ts` (a `runClone`/clone entry consuming the scan's
`DonorCandidate`) — the spike entry the user/orchestrator runs to produce the `.package`. Production
sidecar→export-worker dispatch (§9) is **not** this slice: `none — production wiring lands in Phase 5`.
Confirm the clone is reached from the spike entry, not just tests.

## Files expected to touch
**New:**
- `workers/export/src/donor/resolveChain.ts` — resolve the deferred `[COBJ,MLOD,GEOM]` chain (cross-package).
- `workers/export/src/clone/clone.ts` — swap GEOM/thumbnail/COBJ, preserve OBJD/FTPT/RIG/SLOT.
- `workers/export/src/serialize/serialize.ts` — re-serialize the cloned DBPF via `@s4tk`.
- `workers/export/src/validate/roundTrip.ts` — DBPF round-trip + structural validation.
- `workers/export/src/write/atomicWrite.ts` — **🔒 the safety-rule-4 atomic write** (temp→fsync→validate→rename).
- tests per module, incl. `test/write/atomicWrite.test.ts` (the safety pins).
- a GEOM fixture reference for the swap (S1a's `cube_v0x05.geom`; Step-2.5 Q1).

**Modified:**
- `workers/export/src/spike_clone.ts` — add the clone stage (consume the scan's candidate → clone → write).

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2)
**🔒 Safety — `test/write/atomicWrite.test.ts` (the rule-4 pins; their own commit):**
1. **`atomic_write_sequence_temp_fsync_validate_rename`** — writes to a temp path, fsyncs (file+dir),
   validates, then renames; the final file appears only after a passing validate.
   - Why: §9 atomic export ordering (rule 4).
2. **`atomic_write_validation_failure_no_partial`** — a round-trip-validate failure → **no output file,
   no rename** (temp discarded); returns `failed`.
   - Why: rule 4 "never a half-written file" — the load-bearing safety pin.
3. **`atomic_write_never_touches_mods_or_donor`** — the write targets only the given scratch dir; the
   donor path is never opened for write; no path under a Mods folder is written.
   - Why: rule 4 donors read-only + rule 3 scratch-only.

**Clone / chain / round-trip (deterministic, against a fixture donor):**
4. **`resolve_chain_obute_modl_mlod_geom`** — given a fixture donor graph, resolves OBJD→MODL→MLOD→GEOM
   + COBJ; cross-package ref resolves against the package set.
5. **`clone_swaps_geom_preserves_obj_ftpt_rig_slot`** — after clone, the GEOM bytes == the swapped-in
   GEOM; OBJD/FTPT/RIG/SLOT are byte-identical to the donor's.
6. **`roundtrip_validate_asserts_required_set_and_tuning`** — re-open the serialized package: required
   resource set present, swapped GEOM present, OBJD tuning instance resolves; a missing-resource package
   fails validation.
7. **`clone_report_contract_valid`** — `succeeded` ⟹ `packagePath` in scratch + no error; `failed` ⟹
   error + no package (rule-6 status↔outputs).

**Exploratory arm (run-and-observe → verdict):** the real clone of the live candidate donor
(`0xC0DB5AE7…031A`) producing a round-trip-valid `.package` in scratch. The "does clone-a-donor produce
a valid installable package" question is answered by running it; the in-game placeability is **S1c**
(the user's hands), NOT this slice.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — frozen `ExportJob`/`ExportJobReport` reused unchanged.
- **Orchestrator doc rows to write hot (Step 9):** none to the `workers/export/CLAUDE.md` cross-doc
  table. Likely a **lesson** (the @s4tk clone/re-serialize mechanics + the atomic-write pattern) + a §9
  **arch note** → route to the **integration-doc-edits ledger** (not a live `ARCHITECTURE.md` edit).
- **Shared-contract (Appendix-A seam) model touched?** No — no schema-snapshot needed.

## Things to flag at Step 2.5
1. **GEOM source for the swap.** My default vote: **reference S1a's `cube_v0x05.geom`** (the proven-emitted
   GEOM — proves the end-to-end S1a→S1b chain; a cube where the donor object was). Cross-area: read the
   `workers/blender` fixture, or copy it into `workers/export/test/fixtures/` (a copy is cleaner for the
   area boundary). Flag your pick.
2. **Cross-package chain resolution.** The candidate's MLOD/GEOM may live in a different FullBuild than its
   OBJD. My default vote: resolve in the candidate's package first; if a ref leaves it, resolve across the
   FullBuild set (the scan lists all 10). **If cross-package proves deep for the spike, re-scan for an
   in-package candidate** (a simpler donor whose whole chain is co-located) — surface via Step-7.5, don't
   grind.
3. **`fsync` granularity.** My default vote: `fsync(tempFile)` **and** `fsync(dir)` before the rename
   (durable rename) — mirrors the 0.7 store's write-bytes→fsync(file+dir)→commit pattern.
4. **Round-trip validation depth.** My default vote: re-open via `@s4tk` + assert {required resource set
   present, swapped GEOM present, OBJD tuning resolves}. In-game placeability is **S1c** (user), explicitly
   NOT this validation's bar.

## Dependencies + sequencing
- **Depends on:** S1b donor-scan (`35ee2e3`, sealed) — the candidate + `scanDonorObjects`/`resolveRequiredResources`
  API; S1a's GEOM (`cube_v0x05.geom`); 0.5b `ExportJob`/`ExportJobReport`.
- **Blocks:** **S1c** (the user's in-game test-install of the produced `.package` — the final S1 placeability
  verdict). On a PASS here + a PASS at S1c, the full S1 go/no-go is met → 1.1 tickable.

## Estimated commit count
**2–3, with the atomic write as its OWN commit (safety-critical — never bundled).**
(1) chain resolution + clone + re-serialize + round-trip validation (deterministic). (2) **🔒 the
safety-rule-4 atomic validated write** — its own commit, security-reviewed (the temp→fsync→validate→
rename sequence + the no-partial-on-failure + the donor-read-only/no-Mods pins). The verdict is a separate
`docs(sessions)` commit. Do NOT bundle the safety write with the clone mechanics.

## Lessons-logged candidates anticipated
- **Convention candidate** — the `@s4tk` clone + re-serialize mechanics (swap-resource + preserve-set) +
  the atomic-validated-write sequence (temp→fsync→round-trip→rename; no-partial-on-failure).
- **Architecture-doc note candidate** — the §9 clone resource-swap/preserve set + the round-trip-validation
  check set → integration-doc-edits ledger.
- **Future TODO** — the production atomic-export hardening (the §8↔§9 `geomBytesRef` containment, already a
  Phase-5 PINNED ledger task) + per-item partial-success packaging (§9) for multi-item exports (Phase 5).

## How to invoke
1. **Read this brief end-to-end** — this is the **safety-critical** slice; note the rule-4 atomic-write
   pins (their own commit) + the 4 Step-2.5 questions.
2. You're a fresh session — run `/session-start` first (you're oriented on `track/spikes @ b8bca40`), then
   `/tdd s1b_clone`.
3. **Step 2.5** — send the test-design write-up (esp. the atomic-write safety pins) + your answers to Q1–Q4.
   A **Step-7.5 early-ping is invited** if the cross-package chain resolution (Q2) proves deep — re-scan for
   an in-package candidate rather than grind.
4. **Step 9** — categorized flags + the verdict (the scratch `.package` path + the **S1c-ready** flag I
   relay to the lead → user); route §9 arch notes to the ledger.
