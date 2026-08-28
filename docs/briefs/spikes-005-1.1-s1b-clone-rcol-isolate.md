# /tdd brief — s1b_clone_rcol_isolate

## Feature
The live-artifact arm of S1b-clone (user-greenlit **Option A**): a **bounded RCOL chunk-header TGI-ref
read** to isolate the candidate object's exact GEOM from a multi-object FullBuild, then drive it through
the already-proven clone → atomic-write → DBPF round-trip path to produce a real single-object
**OVERRIDE `.package`** — the installable artifact for the user's **S1c in-game Build/Buy test**. This
completes S1's actual PASS criterion (places in Build/Buy).

## Use case + traceability
- **Task ID:** 1.1 (continues task #6 / S1b-clone — the held live arm)
- **Architecture sections it implements:** `ARCHITECTURE.md §9` (clone-a-donor — the exact GEOM the swap
  needs), `§10` (Donor Library — the donor chain), `§20` (S1 go/no-go), `§22` (open Q6 — `@s4tk`/GEOM).
- **Related context:** the S1b-clone deterministic mechanics + atomic write are LANDED (`0584704`
  atomicWrite, `460af26` mechanics). The Step-7.5 finding: type-collection over-collects across a
  FullBuild because `@s4tk` decodes MODL/MLOD as opaque `RawResource`. Candidate `0xC0DB5AE7…031A` in
  `ClientFullBuild0.package`. S1a's GEOM = `cube_v0x05.geom` (the swap-in bytes).

## ⚠️ SCOPE BOUNDARY (user/lead-set — keep it a SPIKE, NOT Phase-5)
**Read the candidate's TGI ref table out of the RCOL chunk headers ONLY** — just enough to isolate the
ONE object's GEOM (resolve MODL→MLOD→GEOM via the chunk-header TGI refs). **DO NOT** build the full
precise ref-walk, mesh decode/re-encode, or production mesh pipeline — those stay **Phase-5**
(carry-forward in the ledger). If the bounded chunk-header read proves insufficient to isolate the GEOM,
**Step-7.5 ping me** — do NOT expand into the mesh pipeline to force it.

## Acceptance criteria (what "done" means)
- [ ] A **bounded RCOL chunk-header parse** (`isolateGeom` / a focused module) reads the candidate's
      MODL→MLOD→GEOM **TGI refs from the RCOL chunk headers** and returns the candidate's exact GEOM
      `ResourceKey` (one object, not the whole-catalog over-collection).
- [ ] The live single-object path uses the isolated GEOM (replaces the type-collection over-collect for
      the real candidate) → clone (swap S1a's GEOM, preserve OBJD/FTPT/RIG/SLOT, donor read-only) →
      atomic write → DBPF round-trip + structural validate (the proven path, unchanged).
- [ ] **A real single-object OVERRIDE `.package` is produced** in scratch and passes the round-trip
      validation (required resource set / swapped GEOM present / OBJD tuning resolves).
- [ ] **Written S1 verdict** (`docs/sessions`): the scratch `.package` path, the **install steps** for
      the user, an explicit **override note** ("REPLACES donor object `0xC0DB5AE7…031A` in Build/Buy;
      remove the package after testing"), and the **S1c-READY** flag. On a PASS at the user's in-game
      test, S1's full PASS criterion is met.
- [ ] Deterministic tests for the RCOL chunk-header parse green; `/preflight` clean (tsc + eslint + vitest).

## Wiring / entry point (Step 7.5)
`isolateGeom` wired into `runCloneFrom`'s live single-object path (`spike_clone.ts`) — reached from the
spike entry. Production donor-library/export wiring stays `none — lands in Phase 5`.

## Files expected to touch
**New:**
- `workers/export/src/donor/isolateGeom.ts` — the bounded RCOL chunk-header TGI-ref read.
- `workers/export/test/donor/isolateGeom.test.ts` — the parse tests (against an RCOL-chunk-header fixture).
- an RCOL chunk-header fixture (a minimal MODL/MLOD chunk-header byte structure with TGI refs).

**Modified:**
- `workers/export/src/spike_clone.ts` — use `isolateGeom` on the live single-object path (the
  type-collection fallback stays for the single-object-fixture case).

If implementation needs files beyond this list (esp. anything toward the mesh pipeline) — **STOP and
Step-7.5 ping** per the scope boundary.

## RED test outline (Step 2)
Tests in `workers/export/test/donor/isolateGeom.test.ts`:

1. **`isolate_geom_reads_chunk_header_tgi_refs`** — given an RCOL chunk-header fixture (MODL→MLOD→GEOM
   TGI refs), returns the GEOM `ResourceKey`.
   - Why: §9 — the exact-GEOM isolation the swap needs.
2. **`isolate_geom_single_geom_not_overcollected`** — a fixture with multiple GEOMs → returns only the
   candidate's chain GEOM (the over-collection fix).
   - Why: the Step-7.5 root cause — one object, not the catalog.
3. **`isolate_geom_unresolvable_returns_structured_not_throw`** — a chunk header without a resolvable
   GEOM ref → a structured `unresolved` result (fail loud but not a crash; don't clone geometry-less).
   - Why: spike safety — never build a wrong artifact.

**Exploratory arm (run-and-observe → verdict):** isolate the LIVE candidate's GEOM from
`ClientFullBuild0.package` → produce the real override `.package`. The "does the bounded read isolate the
one object" question is answered by running it; in-game placeability is **S1c** (the user).

## Cross-doc invariant impact
- **Model field changes:** none (frozen contracts reused).
- **Orchestrator doc rows (Step 9):** a §9/§10 **arch note** (the bounded RCOL chunk-header read) +
  possibly a **lesson** → integration-doc-edits ledger. No cross-doc table change.
- **Shared-contract model touched?** No.

## Things to flag at Step 2.5
1. **RCOL chunk-header format source.** Pull the RCOL chunk-header / TGI-ref-table layout from
   **sims4toolkit / SimsWiki RCOL** (not from memory — cite it). My default vote: parse only the chunk
   header's external-TGI-ref table (the public-resource references), enough to walk MODL→MLOD→GEOM by
   key; stop there.
2. **Bounded-parse scope confirmation.** Confirm the parse stays at the chunk-header TGI-ref table — NO
   mesh-data decode. If the GEOM ref isn't in the chunk-header table (needs deeper RCOL-internal
   parsing), **Step-7.5 ping** rather than expand scope.
3. **Fixture.** A minimal hand-built RCOL chunk-header byte structure with TGI refs (synthetic, like the
   S1a GEOM fixture) — the live FullBuild proves the positive path at run.

## Dependencies + sequencing
- **Depends on:** the landed S1b-clone mechanics (`0584704`/`460af26`); the donor-scan candidate; S1a's GEOM.
- **Blocks:** **S1c** — the user's in-game test of the produced `.package` (the final S1 placeability verdict).

## Estimated commit count
**1–2:** (1) `isolateGeom` (the bounded RCOL parse + tests); (2) the live-path wiring (if it warrants a
separate commit). The verdict is a separate `docs(sessions)` commit. No safety-invariant pin here (the
atomic-write safety landed in `0584704`); donor stays read-only.

## Lessons-logged candidates anticipated
- **Convention candidate** — the bounded RCOL chunk-header TGI-ref read to isolate one object's GEOM from
  a multi-object FullBuild (the spike-scoped alternative to the full Phase-5 ref-walk).
- **Architecture-doc note** — §9/§10 the donor GEOM-isolation method → ledger.

## How to invoke
1. **Read this brief end-to-end** — especially the ⚠️ SCOPE BOUNDARY (this is the line that keeps the
   spike from ballooning into the Phase-5 mesh pipeline).
2. You're mid-session (task #6) — jump to `/tdd s1b_clone_rcol_isolate`.
3. **Step 2.5** — the RCOL-parse tests + your chunk-header format source (Q1). **Step-7.5 ping** if the
   bounded chunk-header read can't isolate the GEOM — don't expand scope to force it.
4. **Step 9** — flags + the verdict (the `.package` path + install steps + override note + S1c-READY).
   I relay the S1c handoff to the lead → user.
