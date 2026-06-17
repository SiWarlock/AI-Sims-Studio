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

### "Currently in progress" — replace with
> **Phase 1 spikes — S1a GEOM-emission feasibility PASS (`1b28e0d`).** The #1-risk primary GEOM path is proven headless on Apple Silicon (custom bpy writer, Blender 5.1.2). Spikes track is **warm-idle / parked**, fully Sims-4-blocked: S1b clone-a-donor + S1c in-game verdict need the user's Sims 4 install + a donor `.package`; S2 image-to-3D needs cloud keys; S3 needs S1. `track/spikes` sealed + pushed. Resume = donor-scan + S1b on Sims 4 landing.

### Carry-forward triage (Step 5.5, this round)
4 items, all **SPREAD/KEEP** with last-consumer markers (§8↔§9 TOCTOU → Phase 5; env-ready hardening residual + cross-runtime provisioning → Phase 4; real-GEOM validation depth → S1b). 0 deleted / 0 inlined / 0 deferred. Under the ~7 cap. (Inlining to phase tasks happens at the integration merge when these reach their consuming phase.)

---

## `ARCHITECTURE.md`

### §8 (annotation — updated by the S1a env-ready PASS)
Annotate §8's GEOM path with the S1a result: **the GEOM-emission method = a custom headless `bpy` `struct` writer, PROVEN on Blender 5.1.2 / Apple Silicon** (the first of the three §20 fallbacks; format from SimsWiki `0x015A1849`). The **real structural-check set** now exists (`validate_real_geom`: magic / version 0x05·0x0C / vertex-face-meshgroup counts / UV / declared-body bounds) alongside the spikes-001 **placeholder** parser — keep the SPIKE-vs-real distinction explicit. **Scope:** S1a proves GEOM-emission feasibility ONLY; in-game placeability (S1c, Sims 4) + full @s4tk round-trip (S1b) are NOT proven by it. The §8 "immediate structural validation" check list MAY now firm into that named real set; the **§8↔§9 containment-on-handoff** requirement remains the Phase-5 pinned task above. (origin: 1.1/S1a + S1a env-ready probe.)

---

**Provenance:** D27 (user, 2026-06-17 — defer-but-pin); S1a headless harness `0d6215f`; S1a env-ready GEOM probe spikes-002 (🎯 GEOM-emission PASS; commit hashes at round close). Banked in-area (not here): `workers/blender` Lessons §1 (runner-injection seam) + §2 (headless GEOM emission).
