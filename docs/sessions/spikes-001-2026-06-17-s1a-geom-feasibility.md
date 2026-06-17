# spikes-001 — S1 GEOM/DBPF feasibility: the S1a harness + env-ready verdict

- **Date:** 2026-06-17
- **Phase:** 1 (Feasibility spikes) · Track: **spikes** · Area: `workers/blender`
- **Predecessor:** `docs/sessions/contract-004-2026-06-17-services-pipeline-phase0-tail.md` (Phase-0 SEAL — the contract freeze that unblocked the 6-track fork; cross-track fork point)
- **Successor:** _(TBD — S1b `workers/export` clone-a-donor, blocked on Sims 4 install + donor)_
- **Tasks:** 1.1 (S1a) · **Briefs:** `docs/briefs/spikes-001-1.1-s1a-geom-harness.md` (@7955314e), `docs/briefs/spikes-002-1.1-s1a-env-ready-geom-probe.md` (@03944dfb)
- **Commits:** `0d6215f` (S1a headless harness) · `aa6ce58` (env-ready hardening + real-format validator) · `0b0b6c9` (custom headless bpy GEOM writer)

---

## 🎯 S1a-probe VERDICT — PASS (GEOM-emission feasibility)

**The #1 project risk's primary GEOM path is GREEN at the structural bar.**

Headless **Blender 5.1.2** (build `ec6e62d40fa9`, built 2026-05-19, bundled Python **3.13.9** — exactly
the pinned 5.1.2 / Py3.13) on **Apple Silicon** **emits structurally-valid Sims-4 GEOM bytes** via a
**custom minimal GEOM writer** (`bpy` + `struct`) — the first of the three §20 fallbacks (custom GEOM
writer / pinned-old-Blender / Windows-VM), now **proven** so the other two are not needed for emission.

- **End-to-end, real path:** real `_SubprocessRunner` → `blender --background --factory-startup --python
  blender_scripts/geom_export.py -- <jobfile>` → **412-byte v0x05 GEOM** (8 verts / 12 tris / uv_0) →
  `validate_real_geom` `ok=True` → contract-valid `succeeded` `BlenderReport`.
- **Method source:** SimsWiki **`0x015A1849`** (the GEOM RCOL chunk spec) — the format authority;
  **Context7 has no @s4tk/GEOM coverage** (reconfirmed). The custom writer + the real-format validator
  both follow this spec; the writer was NOT hand-rolled from memory.
- **PASS bar (this probe):** parses as real GEOM (magic/version) + non-empty vertex/face/meshgroup counts
  + a UV vertex-format element. The captured first emission is pinned as `tests/fixtures/cube_v0x05.geom`
  and a test asserts the same validator accepts it — proving the validator on **real Blender output**, not
  just a hand-built fixture.

**RESIDUAL (explicitly NOT this probe — no FAIL, no fallback triggered):**
- **In-game placeability = S1c** — blocked on a real Sims 4 install (HITL test-install). The structural
  PASS does NOT assert the object places in Build/Buy.
- **Full @s4tk round-trip validation = S1b** — the rigorous format bar (DBPF clone-a-donor); @s4tk is
  `workers/export`, not yet installed.
- **Machine-specific:** the `/Applications/Blender.app/...` executable fallback is a spike convenience
  (env `AISIMS_BLENDER_BIN` overrides; Phase-4 replaces with real config).

---

## Why this session existed

Phase-0 sealed the frozen contracts and unblocked the 6-track fork. The spikes track owns S1 — **the
project gate** (ARCHITECTURE §20/§22 open question 1: *no verified headless-Mac GEOM path*). This session
proved S1's headless-Mac GEOM feasibility in two slices: first the deterministic **harness** around the
Blender CLI subprocess (env-deferred), then — once Blender 5.1.2 was provisioned — the **env-ready probe**
that drives a real emission and renders the verdict.

## What was built

### Files created
- `workers/blender/spike_geom.py` — the §8/§9 Blender-CLI orchestration harness: `build_blender_command`,
  `run_geom_spike` (injected `Runner` Protocol, §17 hang-watchdog kill→retry-once, contract-valid
  `BlenderReport` assembly), the scratch-only guard, the `validator` seam, `run_geom_spike_from_jobfile`
  (fail-closed inbound job-file), the real `_SubprocessRunner` (process-tree kill), `_resolve_blender_exe`,
  `__main__`.
- `workers/blender/geom/structural.py` — the §8 **placeholder** structural-GEOM validator (spike container;
  fail-soft, never raises). The synthetic-fixture parser.
- `workers/blender/geom/real_geom.py` — the **real** Sims-4 GEOM (0x015A1849) structural validator
  (`validate_real_geom`, bounds-checked `_Reader`; magic/version/counts/UV; never raises). The env-ready
  swap of the placeholder parser.
- `workers/blender/blender_scripts/geom_export.py` — the **exploratory** bpy custom GEOM writer (runs under
  Blender's bundled Python; cube → v0x05 GEOM bytes + result-file). mypy-excluded (bpy unresolvable in the
  worker uv env); ruff-linted.
- `workers/blender/tests/` — `test_geom_structural.py`, `test_spike_geom.py`, `test_real_geom.py`,
  `test_env_ready_probe.py`, `fixtures/__init__.py` (synthetic + real GEOM fixture builders),
  `fixtures/cube_v0x05.geom` (captured real Blender GEOM).

### Files modified
- `workers/blender/pyproject.toml` — added `aisims-contracts` workspace dep + the strict-typing file set
  (`geom`, `spike_geom.py`, `tests`) + the `blender_scripts/` mypy exclude (bpy-only dir).

## Decisions made
- **GEOM-emission method = custom minimal writer (Q1).** Most controllable headless, no GUI-addon
  dependency, and it IS a named §20 fallback — proving it is the spike's value. Sourced from SimsWiki
  0x015A1849. (Alternatives: a Blender addon headless — itself unverified; @s4tk handoff — S1b territory.)
- **Validator = sibling `geom/real_geom.py` + captured-fixture pin (Q2).** Keeps the placeholder parser
  intact; minimal real-format check; full @s4tk round-trip deferred to S1b.
- **Runner seam = injected `Runner` Protocol.** The real subprocess stays out of the test path; the
  production `_SubprocessRunner` does a process-**group** kill (`start_new_session` + `os.killpg`) for the
  §17 watchdog.
- **Configurable Blender executable (`_resolve_blender_exe`).** `blender` is not on PATH on this Mac;
  precedence env `AISIMS_BLENDER_BIN` > `.app` fallback > `"blender"` (the fallback never masks an explicit
  override). Implementer catch from the cleared-blocker recon.
- **bpy script home = `blender_scripts/`.** A bpy-only dir → a clean dir-scoped mypy exclude (+ an inline
  per-file opt-out), no worker-env code to accidentally drop from strict. (Resolved after a cli/↔blender_scripts
  bounce; final = `blender_scripts/`.)
- **Safety hardening folded in-slice** (from review): canonical scratch-resolved `geomBytesRef`, 256 MiB
  GEOM read cap, `previewRef` scratch-guarding, non-allocating `_Reader.skip`, eager count caps, the bpy
  uint16-index guard → clean failed result-file.

## Decisions explicitly NOT made (deferred)
- **In-game placeability verdict (S1c)** — needs Sims 4; this probe's bar is structural only.
- **Full @s4tk round-trip validation (S1b)** — needs @s4tk (`workers/export`, not installed).
- **MTNF (embedded-material) skip interpretation** — `validate_real_geom` skips `r.skip(r.u32())` as
  payload-only; UNTESTED vs a real donor GEOM with a material (the cube has none). Resolve against the spec
  at S1b.
- **Detached-grandchild watchdog** — `killpg` reaps the process group; a fully-detached (new-session)
  Blender grandchild would escape. Env-ready/Phase-4 hardening.
- **Production sidecar→worker dispatch** — Phase 4 (the engine dispatching `BlenderJob`s on the real
  pipeline). Not this slice.

## TDD compliance — CLEAN
- Every deterministic change was **RED-first** (confirmed failing for the right reason before GREEN) across
  both slices: the placeholder + real-format validators, the watchdog/report-assembly harness, the
  fail-closed job-file path, the process-tree kill, the configurable-exe precedence.
- The **GEOM emission itself** (the bpy `blender --background` call) is the **hybrid-spike run-and-observe**
  arm — per the project TDD posture, the deterministic harness *around* a non-deterministic/integration call
  is `/tdd`, the call itself is the spike. Its first valid output became the pinned fixture, and the
  validator is test-pinned against that **real** Blender output. No TDD violations.

## Reachability
- `validate_geom_structure` / `validate_real_geom` ← `_assemble_report` ← `run_geom_spike` ←
  `run_geom_spike_from_jobfile` ← `_run_cli` / `__main__` (the env-ready probe entry, real
  `_SubprocessRunner`). **Confirmed empirically** — the end-to-end probe produced the `succeeded` report via
  the real runner, not a test fake.
- `build_blender_command` ← `run_geom_spike`. `_resolve_blender_exe` ← `run_geom_spike`.
- **No tested-but-unwired gaps.** Production pipeline dispatch is a documented **Phase-4** entry (not this
  slice).

## Open follow-ups
**Step-9 categorized (routed hot by the orchestrator → integration-doc-edits ledger / IMPLEMENTATION_PLAN
carry-forwards):**
- **Future TODO (S1b):** resolve the MTNF payload-vs-self-inclusive interpretation vs a real donor GEOM;
  full @s4tk round-trip validation.
- **Future TODO (S1c):** in-game placeability verdict (HITL test-install; needs Sims 4).
- **Future TODO (env-ready/Phase-4):** detached-grandchild process-tree kill; replace the machine-specific
  `.app` executable fallback with real config.
- **Architecture-doc note (→ integration-doc-edits ledger, NOT a live ARCHITECTURE.md edit):** §8
  GEOM-emission method = custom headless writer (proven on Blender 5.1/Apple Silicon); the real
  structural-check set (magic/version/counts/UV/bounds); the SPIKE-vs-real GEOM distinction.
- **Lesson candidates (orchestrator banks):** (a) spike/worker harnesses inject the subprocess runner behind
  a `Protocol` so the deterministic core is fully testable headless; (b) headless Sims-4 GEOM emission via a
  custom bpy `struct` writer works on Blender 5.1 — TDD the harness/validator, run-and-observe the emission.
- **Security Finding (spikes-001, escalated to lead):** the §8↔§9 GEOM-bytes TOCTOU / downstream
  containment re-check — latent today (no §9 consumer), homed at the **Phase-5** export consumer.

## How to use what was built
- **Re-run the probe:** `blender --background --factory-startup --python blender_scripts/geom_export.py --
  <jobfile>` (or drive it through `run_geom_spike_from_jobfile` with `_SubprocessRunner`); set
  `AISIMS_BLENDER_BIN` to point at a specific Blender.
- **Validate emitted bytes:** `geom.real_geom.validate_real_geom(data) -> GeomStructResult`.
- The captured fixture `tests/fixtures/cube_v0x05.geom` is the pinned real-GEOM reference for the validator.
