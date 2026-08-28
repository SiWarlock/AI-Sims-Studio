# Integration-doc-edits ledger — spikes track

> **Apply target:** `main` (integration checkout), by the integration owner, **at the spikes→integration merge** — NOT live, NEVER in a worktree copy.
>
> **Policy (user, 2026-06-17):** cross-track edits to `IMPLEMENTATION_PLAN.md` / `ARCHITECTURE.md` are accumulated here, not applied live; the integration owner applies the whole block to `main` at merge (race-free batching across the parallel tracks). This file is orchestrator-owned, rides `/orchestrate-end` commits on `track/spikes`, and is handed to the integration owner at merge. Append across slices; never edit the worktree's own copies of the shared root docs.

---

## `IMPLEMENTATION_PLAN.md`

### Phase 5 — Acceptance (NEW pinned task to add)
- [ ] `[SAFETY-RULE-3 · PINNED · NON-DROPPABLE · D27]` **§8↔§9 `geomBytesRef` containment re-check at re-open.** Pinned by a test: a `geomBytesRef` symlink swapped between validate-time and the downstream re-open is **rejected** and its bytes are never read. Full fix = a symlink-free / content-addressed GEOM handoff, OR `O_NOFOLLOW` + a downstream containment re-check. (origin: 2026-06-17 · 1.1/S1a; security-reviewer rated [critical] in the abstract; **latent** until the §9 export consumer exists. Mirrors the Inv1/Inv5→Phase-2 pin posture, D16.)

### Carry-forward to upcoming briefs (adds)
- **(origin: 2026-06-17 · 1.1/S1a) §8↔§9 `geomBytesRef` TOCTOU** — pointer to the Phase-5 PINNED task above. **Last-consumer: Phase 5** (mesh-export track).
- **(origin: 2026-06-17 · 1.1/S1a env-ready probe — LANDED, residual → Phase 4) S1a env-ready hardening** — fail-closed job-file + process-group tree-kill (`Popen`+`start_new_session`+`os.killpg`) + configurable `_resolve_blender_exe` ALL landed in the env-ready probe. **RESIDUAL:** a fully *detached* (new-session) Blender grandchild still escapes `killpg` (the probe pins the same-group case); the `/Applications/Blender.app/...` exe fallback is machine-specific (env `AISIMS_BLENDER_BIN` overrides; Phase-4 replaces with real config). **Last-consumer: Phase 4.**
- **(origin: 2026-06-17 · 1.1/S1a env-ready probe) real-GEOM validation depth** — `validate_real_geom`'s MTNF-skip path (`embedded_id ≠ 0`, payload-only `r.skip(r.u32())`) is **untested vs a real donor GEOM with a material** (the spike cube has none); resolve against the format spec when @s4tk + donors land. Full @s4tk round-trip validation (the rigorous bar beyond structural) is **S1b**. **Last-consumer: S1b.**
- **(origin: 2026-06-17 · 1.1/S1a) cross-runtime contract provisioning** — `aisims_contracts` on Blender's bundled-Python `sys.path` at deploy (imported under the worker `uv` env now; Blender's bundled 3.13 differs). **Last-consumer: env-ready deploy / Phase 4.**
- **(origin: 2026-06-17 · 1.1/S1b donor-scan) TS contracts-import mechanism** — the generated TS contracts (`packages/contracts/generated`) need a PRODUCTION import mechanism for the TS consumers (`workers/export`, `apps/desktop`): a **tsconfig path alias** vs a **published `@aisims/contracts` workspace package**. S1b donor-scan used a **non-locking relative type-only import** (spike-local; imports the generated source-of-truth, not a hand-roll). **Decide deliberately — Option A/B/C, a dev-facing import convention — at the first production TS consumer.** **Last-consumer: Phase 5 / Phase 7.**
- **(origin: 2026-06-17 · 1.1/S1b donor-scan) `@s4tk` memory-bounded donor read (MMAP)** — the spike reads donors via the **buffer path** (`extractResourcesAsync(buffer, {filter, limit})`: a transient ~719 MB `readFile` buffer, freed; ~275 ms read + ~3 ms filtered-OBJD decode — decodes only matched resources, not a full `Package.from`). The memory-bounded **MMAP path** (`streamResources` + `@s4tk/plugin-bufferfromfile`) needs a native `.node` that **does NOT build on this macOS setup** (custom Makefile/`step` build, not node-gyp). For production (concurrent reads of 1 GB+ donors → N transient 719 MB buffers), switch to the MMAP path + resolve its native build. **Last-consumer: Phase 5 (production donor library).**
- **(origin: 2026-06-17 · 1.1/S1b donor-scan) Phase-5 donor-index hardening** — the spike has a 4 GB donor-read size-cap; production needs a **decompression-bomb / per-resource memory ceiling** + **worker isolation** for the donor-index pass (large untrusted-ish binary parsing). **Last-consumer: Phase 5 (production donor library).**
- **(origin: 2026-06-17 · 1.1/S1b-clone) precise MODL→MLOD→GEOM ref-walk** — the spike **type-collects** `[COBJ,MLOD,GEOM]` across the package set (works exactly for a single-object candidate) because `@s4tk` models MODL/MLOD as `RawResource` (no typed binary ref-walk). Production needs the precise OBJD→MODL→MLOD→GEOM binary reference walk so a multi-object package resolves the *exact* chain (no over-collection). **Last-consumer: Phase 5.**
- **(origin: 2026-06-17 · 1.1/S1b-clone) production re-keying clone (vs override)** — the spike produces an **OVERRIDE clone** (same donor TGI keys, GEOM swapped → the donor object renders as the new mesh in Build/Buy; a valid placeability proof). Production needs a **re-keyed fresh non-colliding object**: new GUIDs/TGI + MODL/MLOD ref-rewrite + COBJ/thumbnail swap (a *new* catalog object, not an override of a real EA object). **Last-consumer: Phase 5.**
- **(origin: 2026-06-17 · 1.1/S1b-clone, Step-8 reviews) S1b-clone Phase-5 hardening** — (a) atomic-write **final-path clobber-confirm** (SEC#2 — refuse/confirm before overwriting an existing output `.package`); (b) **Windows path-sep** robustness in the Mods-path guard (cross-platform deferred, §20); (c) per-item **partial-success packaging** (§9 — multi-item exports: each package individually complete-and-valid). **Last-consumer: Phase 5.**

### Task 1.1 — stays **UNTICKED**
S1a **headless harness** (`0d6215f`) + the S1a **env-ready GEOM probe** (`aa6ce58` validator+hardening, `0b0b6c9` bpy writer; verdict `1b28e0d`) have landed — **🎯 GEOM-emission feasibility = PASS** (custom headless `bpy` writer, Blender 5.1.2 / Apple Silicon, structural bar). **Remaining (keep 1.1 open):** S1b clone-a-donor (Sims 4 + donor), S1c in-game test-install verdict (Sims 4), S2, S3. The full S1 go/no-go (**places in Build/Buy via test-install**) is NOT yet met — structural-emission PASS is necessary, not sufficient.

### Log entry to append (orchestrator framing)
```markdown
### 2026-06-17 — Phase 1 spikes round 1 (S1a): headless-Mac GEOM feasibility — 🎯 PASS

- **Landed (track/spikes):** S1a in 3 commits — `0d6215f` (headless harness: injected-Runner seam, §17 watchdog, contract-valid BlenderReport, scratch-only guard) · `aa6ce58` (env-ready hardening: real `_SubprocessRunner` process-tree kill, fail-closed job-file, configurable `_resolve_blender_exe`; real-format GEOM validator + captured fixture) · `0b0b6c9` (custom bpy GEOM `struct` writer). Verdict `1b28e0d`. 44 tests, mypy --strict (12 files), security no critical/high (rules 3+6 pinned).
- **🎯 S1a VERDICT = PASS (GEOM-emission feasibility):** headless Blender 5.1.2 / Py3.13.9 on Apple Silicon emits structurally-valid Sims-4 GEOM via a custom writer (§20 fallback #1; SimsWiki 0x015A1849). This retires the make-or-break half of the project's #1 risk (§20/§22 open-Q1).
- **Scope (NOT a full S1 go):** structural-emission PASS only. The full S1 ("places in Build/Buy via test-install") still needs S1c (in-game, Sims-4-blocked) + S1b (@s4tk round-trip, Sims-4-blocked). 1.1 stays UNTICKED.
- **Decisions:** D27 (user — defer-but-pin the §8↔§9 geomBytesRef TOCTOU to a Phase-5 PINNED·NON-DROPPABLE task). Integration-doc-edit policy (user): plan/ARCH edits accumulate in this ledger, applied at the spikes→integration merge.
- **Unblocked / blocked:** mesh-export track (4/5/6) can now plan against a proven primary GEOM path. Spikes track parks: S1b/S1c blocked on Sims 4 install + donor; S2 blocked on cloud keys; S3 blocked on S1.
- **Lessons:** workers/blender §1 (runner-injection seam) + §2 (headless GEOM emission via custom bpy writer).
- **Next session target:** S1b clone-a-donor (donor-scan + @s4tk round-trip) the moment Sims 4 + a donor land.
- **Reference:** implementer session/verdict doc `spikes-001-2026-06-17-s1a-geom-feasibility.md`.
```
```markdown
### 2026-06-17 — Phase 1 spikes round 2 (S1b donor-scan): @s4tk reads EA-macOS donors — ✅ PASS

- **Landed (track/spikes):** S1b donor-scan `35ee2e3` (`workers/export` — first slice in the area). Auto-detect Sims 4 install + FullBuild donors (EA-App macOS); @s4tk open a donor READ-ONLY via the buffer path (`extractResourcesAsync` filter+limit — decodes only matched OBJDs, not a full `Package.from`); candidate `0xC0DB5AE7…031A` resolved; scratch JSON emitted for the clone. 5 tests; tsc + eslint + forbidden-grep clean; security no critical/high (rules 3+4). Session doc `a748190`.
- **✅ DE-RISK PASS:** @s4tk reads the EA-macOS FullBuild donors — retires the SECOND make-or-break unknown of S1 (round 1 retired the first, headless GEOM). Candidate resolved `[OBJD,MODL,FTPT,RIG,IMG]`+tuning; `[COBJ,MLOD,GEOM]` deferred to the clone (the OBJD→MODL→MLOD→GEOM chain, NOT absent).
- **Finding (resolved → Phase-5):** @s4tk's memory-bounded MMAP read needs a native plugin that won't build on this macOS setup → buffer-path pivot (approved). MMAP = Phase-5 memory optimization.
- **Team:** implementer **CYCLE (impl-only)** at this clean scan/clone boundary — impl hit WARN (70%); the clone (spikes-004) is big + safety-invariant (rule 4 atomic export) and can't cycle mid-slice, so a fresh impl takes it with full headroom. Orchestrator persists (49%).
- **Lessons:** workers/export §1 (@s4tk reads macOS donors via the buffer path; read-only donors; the MMAP-native-build gotcha).
- **Next session target:** spikes-004 S1b-clone — resolve `[COBJ,MLOD,GEOM]` + the GEOM swap + **atomic export** (rule 4) → the validated `.package` for the user's **S1c in-game test-install**. Dispatched to the fresh impl on the lead's ready-signal.
- **Reference:** implementer session doc `spikes-002-2026-06-17-s1b-donor-scan.md`.
```

### "Currently in progress" — replace with
> **Phase 1 spikes — S1b donor-scan = ✅ de-risk PASS (`35ee2e3`).** Both S1 make-or-break unknowns now proven: headless-Mac GEOM emission (round 1, `1b28e0d`) + @s4tk-reads-EA-macOS-donors (round 2). **Next: spikes-004 S1b-clone** — resolve the GEOM chain + GEOM swap + **atomic export** (rule 4) → the validated `.package` for the user's **S1c in-game test-install**. Spikes track is **mid-cycle** (impl-only — a fresh `spikes-meshexport-implementer` takes the clone with full headroom; orchestrator persists). S1c = user's hands; S2 parked on cloud keys; S3 needs S1. `track/spikes` sealed through the S1b-scan round + pushed.

### Carry-forward triage (Step 5.5, S1b-scan round)
**7 items: 1 KEEP + 6 SPREAD.** KEEP: real-GEOM validation depth (MTNF + @s4tk round-trip) → **spikes-004 clone** (the immediately-next spikes brief; I fold it in). SPREAD (cross-phase integration handoffs, last-consumer markers — inlined to phase tasks at the integration merge, NOT spikes-next-brief items): §8↔§9 TOCTOU → Phase 5; env-ready hardening residual + cross-runtime provisioning → Phase 4; TS contracts-import → Phase 5/7; MMAP donor read + donor-index hardening → Phase 5. 0 deleted / 0 deferred. At the ~7 cap but all carry consumers (none >3 slices stale-without-consumer); the spikes working set is just the 1 KEEP — the 6 are integration-merge concerns. No force-resolve needed.

---

## `ARCHITECTURE.md`

### §8 (annotation — updated by the S1a env-ready PASS)
Annotate §8's GEOM path with the S1a result: **the GEOM-emission method = a custom headless `bpy` `struct` writer, PROVEN on Blender 5.1.2 / Apple Silicon** (the first of the three §20 fallbacks; format from SimsWiki `0x015A1849`). The **real structural-check set** now exists (`validate_real_geom`: magic / version 0x05·0x0C / vertex-face-meshgroup counts / UV / declared-body bounds) alongside the spikes-001 **placeholder** parser — keep the SPIKE-vs-real distinction explicit. **Scope:** S1a proves GEOM-emission feasibility ONLY; in-game placeability (S1c, Sims 4) + full @s4tk round-trip (S1b) are NOT proven by it. The §8 "immediate structural validation" check list MAY now firm into that named real set; the **§8↔§9 containment-on-handoff** requirement remains the Phase-5 pinned task above. (origin: 1.1/S1a + S1a env-ready probe.)

### §9 (annotation — S1b-clone mechanics proven)
Annotate §9's clone-a-donor with the S1b result: the **clone resource-swap/preserve set** = swap GEOM under the donor's GEOM key (as `RawResource`) + `Resource.clone()` the preserve-set (OBJD/FTPT/RIG/SLOT) + never mutate the donor (read-only); the **round-trip-validation check set** = re-open the written package and assert {required resource set present / swapped-GEOM bytes survived serialize / OBJD tuning resolves}; the **atomic-write sequence** = temp→fsync(file+dir)→validate-on-disk-bytes→atomic-rename, no-partial/never-throw, scratch-only (rule 4). **Scope:** the spike produces an **OVERRIDE clone** (donor TGI preserved) as the placeability proof; **isolating one object's exact GEOM from a multi-object FullBuild needs the MLOD→GEOM RCOL ref-walk** (the live-artifact blocker — @s4tk models MODL/MLOD as opaque `RawResource`). (origin: 1.1/S1b-clone.)

---

**Provenance:** D27 (user, 2026-06-17 — defer-but-pin); S1a headless harness `0d6215f`; S1a env-ready GEOM probe spikes-002 (🎯 GEOM-emission PASS; commit hashes at round close). Banked in-area (not here): `workers/blender` Lessons §1 (runner-injection seam) + §2 (headless GEOM emission).
