# spikes-002 — S1b donor-scan: @s4tk reads the EA-macOS donors

- **Date:** 2026-06-17
- **Phase:** 1 (Feasibility spikes) · Track: **spikes** · Area: `workers/export`
- **Predecessor:** `docs/sessions/spikes-001-2026-06-17-s1a-geom-feasibility.md`
- **Successor:** _(TBD — spikes-004 S1b-clone: GEOM swap + atomic DBPF write, fresh implementer)_
- **Task:** 1.1 (S1b donor-scan) · **Brief:** `docs/briefs/spikes-003-1.1-s1b-donor-scan.md` (@9cbb16db)
- **Commit:** `35ee2e3` (S1b donor-scan)

---

## ✅ S1b donor-scan DE-RISK — PASS

**"Can `@s4tk` read the EA-App-macOS donors on this Mac?" = YES.**

`@s4tk` opens the real Sims-4 FullBuild donor packages **READ-ONLY** and resolves a candidate Build/Buy
object. Verdict feeds the eventual S1b result (the clone, spikes-004, completes it).

- **Install:** `/Applications/EA Games/The Sims 4.app` — 10 FullBuild donors
  (`Contents/Data/Client/ClientFullBuild{0-8}.package` ~1 GB each + `Simulation/SimulationFullBuild0.package`).
- **Read:** `ClientFullBuild0.package` (719 MB) opened read-only via the **buffer path**
  (`Package.extractResourcesAsync(buffer, {resourceFilter, limit})`) — `readFile` 275 ms +
  OBJD-filtered extract ~3 ms; 256 OBJDs surfaced.
- **Candidate** `0xC0DB5AE7:0x00000000:0x031A` — **resolvedByScan** `[OBJD, MODL, FTPT, RIG, IMG]`
  + tuning resolves; **deferredToClone** `[COBJ, MLOD, GEOM]` = NOT-RESOLVED-BY-SCAN (the clone follows
  the OBJD→MODL→MLOD→GEOM chain + COBJ, possibly cross-package) — **NOT absent from the donor**.
- A scratch JSON (the candidate + manifest) is emitted for the clone to consume.

**Finding (→ lead + integration ledger):** `@s4tk`'s memory-bounded MMAP path (`streamResources` +
`@s4tk/plugin-bufferfromfile`) needs a native `.node` that won't build on this macOS setup (custom
Makefile/`step` build, not node-gyp). Pivoted to the **buffer path** (orchestrator-approved); the MMAP
memory optimization is **Phase-5** (matters under concurrency with N×~719 MB buffers).

---

## Why this session existed

Phase-1 S1 has two make-or-break unknowns; S1a proved the headless-Mac GEOM emission path (spikes-001).
This session (a fresh `workers/export` TS area, re-engaged after the user's Sims 4 install was verified)
proved the second: that `@s4tk` can read the EA-App-macOS donor packages — the prerequisite for the
clone (spikes-004) that swaps S1a's GEOM into a donor.

## What was built

### Files created
- `workers/export/src/donor/scan.ts` — the donor-scan module: `detectSims4Install` (auto-detect behind
  an injected `FsProbe` seam; `AISIMS_SIMS4_PATH` override → EA-App-macOS default → structured
  `not-found`), `realFsProbe`, `resolveRequiredResources`, `toDonorCandidate`, `REQUIRED_RESOURCES`, and
  the exploratory `scanDonorObjects` (`@s4tk` read-only buffer read → OBJD → `ParsedDonorObject`).
- `workers/export/src/spike_clone.ts` — the spike entry: `runDonorScan` (detect → scan → resolve →
  report; never throws) + `main()` (writes a randomized-`0o600` scratch JSON). Clone stage = spikes-004.
- `workers/export/test/donor/scan.test.ts` — 5 deterministic tests (auto-detect ×3 via a fake `FsProbe`;
  resource-resolution; donorRef/manifest conformance to the FROZEN generated `ExportJob`/`ExportJobReport`).

### Files modified
- `workers/export/package.json` — added `@s4tk/models@0.6.14` (runtime, pinned) + `tsx` (devDep, runs
  the spike entry). `pnpm-lock.yaml` updated.

## Decisions made
- **`@s4tk` read = buffer path (`extractResourcesAsync`), pivoted from the approved MMAP
  `streamResources`** — the MMAP plugin's native build is broken on this setup; `extractResources` with
  filter+limit decodes only the matched OBJDs (light, unlike `Package.from`), confirmed fast (275 ms read
  + 3 ms extract). MMAP → Phase-5.
- **Candidate = simple decorative object** (Q1) — sorted tuning-resolved, then fewest slots, then most
  resources resolved.
- **Auto-detect scope = EA-App macOS + `AISIMS_SIMS4_PATH`** (Q4) — no Steam/cross-launcher for the spike;
  structured `not-found` (never guesses) so the orchestrator can flag an absent install.
- **fs behind an injected `FsProbe` seam** — auto-detect is unit-testable without a real install
  (reuses the S1a Runner-seam pattern / `workers/blender` Lesson §1).
- **Contracts-import = relative type-only import** of the generated `ExportJob`/`ExportJobReport` (no
  hand-roll). First TS consumer of the generated contracts.
- **Review hardening folded in-slice:** `tuningId===0n` sentinel → null; sort criterion mirrored to the
  resolve rule; `fileURLToPath` main-guard; `main()` `.catch()`; randomized `mkdtempSync` scratch + `0o600`;
  donor read size-cap (4 GB); 32-bit key masking.

## Decisions explicitly NOT made (deferred)
- **The clone (spikes-004 / S1b-clone)** — resolve `[COBJ, MLOD, GEOM]` via the OBJD→MODL→MLOD→GEOM chain
  + COBJ (possibly cross-package), swap S1a's GEOM, atomic DBPF write (safety rule 4), its own security
  pass. NOT this slice.
- **MMAP memory-bounded read** (`streamResources` + `@s4tk/plugin-bufferfromfile` native build) — Phase-5.
- **Production contracts-import mechanism** (tsconfig path alias vs a published `@aisims/contracts` pkg) —
  a cross-area Phase-5/7 Option A/B/C call (workers/export + apps/desktop both consume the generated TS).
- **Production Donor-Library scan/index into the store (§10)** — Phase 5.

## TDD compliance — CLEAN
- The deterministic surface (auto-detect, resource-resolution, donorRef-conformance) was **RED-first**
  (confirmed failing on the missing module before GREEN).
- `scanDonorObjects` (the `@s4tk` real-package read) is the **hybrid-spike run-and-observe** arm — per
  the project TDD posture, the deterministic wrapper is `/tdd`, the external-tool call is the spike. No
  TDD violations.

## Reachability
- `detectSims4Install` / `resolveRequiredResources` / `toDonorCandidate` / `scanDonorObjects` ←
  `runDonorScan` ← `main()` (the spike entry). Confirmed by the end-to-end run (real `@s4tk` read →
  candidate report). No tested-but-unwired gaps. Production Donor-Library wiring = **Phase 5**.

## Open follow-ups
**Step-9 categorized (routed hot by the orchestrator → ledger / banked lesson):**
- **Finding / arch note (→ integration ledger + lead):** the MMAP-native-build issue + the buffer-path
  pivot; MMAP = Phase-5 memory optimization.
- **Future TODO (spikes-004):** the clone — `[COBJ, MLOD, GEOM]` chain resolution + GEOM swap + atomic
  write (rule 4) + its security pass. The OBJD→MODL link is resolved here (handoff start; scratch JSON).
- **Future TODO (Phase-5 hardening):** decompression-bomb / per-resource memory ceiling + worker
  isolation for the production donor-index; the MMAP native-build setup.
- **Cross-area arch note (→ ledger):** the contracts-import mechanism decision (Phase-5/7).
- **Lesson (orchestrator banks as `workers/export` §1):** `@s4tk` reads EA-macOS FullBuild donors via the
  buffer path (`extractResourcesAsync` filter+limit); the read-only-donor access pattern; the
  MMAP-native-build gotcha.

**No cross-doc invariant change** — frozen `ExportJob`/`ExportJobReport` reused unchanged.

## How to use what was built
- **Run the scan:** `pnpm exec tsx src/spike_clone.ts` (set `AISIMS_SIMS4_PATH` to override the install);
  writes `donor-scan.json` to a randomized scratch dir.
- **Programmatic:** `runDonorScan()` → `DonorScanReport`; `detectSims4Install()` / `scanDonorObjects(pkg)`
  / `resolveRequiredResources(obj)` for the pieces. The clone (spikes-004) consumes the scratch JSON's
  candidate + manifest.
