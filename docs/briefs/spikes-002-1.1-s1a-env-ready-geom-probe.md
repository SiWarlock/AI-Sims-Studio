# /tdd brief — s1a_env_ready_geom_probe

## Feature
The env-ready arm of spike **S1a** (the #1-risk go/no-go): drive a **real** `blender --background`
GEOM emission through the already-landed S1a harness on Apple Silicon, structurally validate the
**real** emitted bytes (not the placeholder spike-GEOM container), and emit a written **S1a-probe
verdict**. This is a **hybrid spike**: the GEOM-emission *method* is a genuine exploratory unknown
(research-driven); the harness wiring, the real-format structural check, and the env-ready hardening
are deterministic and TDD'd. **In-game placeability stays out of scope — that is S1c, blocked on the
pending Sims 4 install.** This probe's question is narrower: *can headless Blender 5.1 on Apple Silicon
emit structurally-valid Sims-4 GEOM bytes, and by what method?*

## Use case + traceability
- **Task ID:** 1.1
- **Architecture sections it implements:** `ARCHITECTURE.md §8` (the GEOM-export stage + immediate
  structural validation; the `blender --background --factory-startup --python` CLI-subprocess production
  path; the `BlenderJob`→`BlenderReport` envelope), `§20` (S1 is a feasibility go/no-go gate; the three
  unverified fallbacks — custom GEOM writer / pinned-old-Blender microservice / Windows-helper VM),
  `§22` (open question 1 — no verified headless-Mac GEOM path; open question 6 — @s4tk/GEOM provenance,
  the format authority for validation).
- **Related context:** spikes-001 (the S1a headless harness — `spike_geom.py` + `geom/structural.py`,
  **landed `0d6215f`**); `workers/blender` LESSONS.md #1 (the injected-`Runner` seam — this slice swaps the
  fake runner for the real `_SubprocessRunner`). Reuses the frozen `aisims_contracts` worker models
  unchanged. Folds the S1a env-ready hardening carry-forwards (fail-closed job-file; process-tree kill)
  recorded at the spikes-001 close-out.

### Orchestrator-verified facts (do NOT re-derive — confirm + record in the verdict)
- Installed Blender = **5.1.2** (build 2026-05-19), bundled **Python 3.13.9** — **exactly the pinned
  5.1.2 / Py3.13**. Version check **PASSES**, no version Finding.
- Headless launch verified: `blender --background --factory-startup --python-expr "import bpy; ..."`
  returns `bpy 5.1.2`, `py 3.13.9`, `bpy.data.meshes` available — **headless + bpy work on this Apple
  Silicon Mac.** So the unknown is **GEOM emission**, not whether Blender runs headless.

## Acceptance criteria (what "done" means)
- [ ] Re-assert `blender --version` == `5.1.2` / bundled Py3.13 at run time; **record the exact build
      string in the verdict** (env provenance).
- [ ] **Configurable Blender executable path** — `build_blender_command` must NOT hardcode `"blender"`
      as argv[0]: `blender` is **not on `PATH`** here (binary at
      `/Applications/Blender.app/Contents/MacOS/Blender`), so a hardcoded `"blender"` makes the real
      `_SubprocessRunner` raise `FileNotFoundError`. Make it configurable (default `"blender"`,
      overridable via param/env to the `.app` binary path). **This is the first sub-task** (implementer's
      catch).
- [ ] A Blender-side GEOM-emission script (`blender_scripts/geom_export.py`, matching the harness
      `_DEFAULT_SCRIPT`) runs **headless** (driven by the real `_SubprocessRunner` wired into
      `run_geom_spike`, replacing the fake) and writes GEOM bytes for a **trivial test mesh** into the
      provided scratch dir. **No real donor is needed for this probe** — use a synthetic `donorBBox` +
      trivial mesh for first signal (the real donor `.package` is S1b/S1c's input, not this GEOM-bytes
      probe's; it stays correctly Sims-4-blocked).
- [ ] The emitted bytes pass a **real Sims-4 GEOM** structural check (parses as GEOM/RCOL; non-empty
      vertex/face/meshgroup counts; UV present) — via the method chosen at Step 2.5 (NOT the spikes-001
      placeholder container).
- [ ] `run_geom_spike` against the real runner returns a **contract-valid `BlenderReport`**
      (`succeeded` ⟹ real `geomBytesRef` in scratch + `gateMetrics`; or `failed` + `ErrorEnvelope` on a
      genuine emission failure — the watchdog/retry path still holds).
- [ ] **Env-ready hardening folded in:** `_run_cli`/`__main__` **fail-closed** on a malformed/missing
      inbound job-file (returns a structured failure, does not raise) — with a test; `_SubprocessRunner`
      process-**tree** kill on a deadline breach (Blender grandchildren) — with a test if expressible
      headless, else documented as exercised by the real run.
- [ ] **Written S1a-probe verdict** in `docs/sessions/spikes-NNN-…`: PASS/FAIL, the **GEOM-emission
      method** used (+ why), the structural-validity result, the exact Blender build, the headless-Apple-
      Silicon confirmation, and the explicit **residual** (in-game placeability = S1c, pending Sims 4).
      **FAIL ⟹ the chosen fallback (pinned-old-Blender / Windows-VM) is named + escalated as a Finding.**
- [ ] Deterministic tests green; `/preflight` clean (ruff + `mypy --strict` + pytest).

## Wiring / entry point (Step 7.5)
`workers/blender/spike_geom.py` `run_geom_spike` / `__main__` — now driving the **real**
`_SubprocessRunner` (the env-ready probe entry the verdict is generated from). Production sidecar→worker
dispatch remains `none — production wiring lands in Phase 4`. Confirm the real runner is invoked on the
probe path, not just in a test.

## Files expected to touch
**New:**
- `workers/blender/blender_scripts/geom_export.py` — the Blender-side (`bpy`) GEOM-emission script the
  CLI subprocess runs (matches the harness `_DEFAULT_SCRIPT`; bpy-only dir, mypy-excluded). **Exploratory** —
  may be rewritten once the method is proven.
- A captured real-GEOM **fixture** (the probe's first valid output, pinned for the structural test) under
  `workers/blender/tests/fixtures/` — bootstrapped from the first successful emission (chicken/egg: no
  real GEOM fixture exists until the probe produces one).
- Tests for the deterministic surface (fail-closed job-file; tree-kill; real-format structural check).

**Modified:**
- `workers/blender/spike_geom.py` — wire the real `_SubprocessRunner`; **configurable Blender
  executable path** in `build_blender_command` (default `"blender"`, overridable to the `.app` binary —
  not on `PATH`); fail-closed job-file handling.
- `workers/blender/geom/structural.py` — add a **real-Sims-4-GEOM** structural mode (or a sibling
  validator), distinct from the spikes-001 placeholder parser (Step-2.5 question on shape).
- `workers/blender/pyproject.toml` — only if a GEOM-format dependency is added (flag at Step 2.5).

If implementation needs files beyond this list, **flag at Step 2.5** before going deep.

## RED test outline (Step 2) — the DETERMINISTIC surface (the GEOM-emission arm is exploratory, below)
Tests in `workers/blender/tests/`:

1. **`test_run_cli_fail_closed_on_missing_jobfile`** — `_run_cli`/`__main__` given a missing job-file
   path returns a structured failure (or a `failed` `BlenderReport`), **does not raise**.
   - Why: §8 fail-soft; the spikes-001 carry-forward hardening.
2. **`test_run_cli_fail_closed_on_malformed_jobfile`** — a job-file that isn't valid JSON / fails
   `BlenderJob` validation → structured failure, no raise.
   - Why: deterministic boundary validation before any subprocess spawn.
3. **`test_subprocess_runner_tree_kill_on_deadline`** *(if expressible headless — e.g. a fake child that
   spawns a grandchild that outlives a `subprocess.run(timeout=)`)* — on a deadline breach the process
   **tree** is killed, not just the direct child.
   - Why: spikes-001 carry-forward (Blender spawns grandchildren); else document as covered by the real run.
4. **`test_real_geom_structural_accepts_captured_fixture`** — the captured real-GEOM fixture →
   `ok=True` with non-empty vertex/face/meshgroup counts + UV flags.
   - Why: §8 real-format structural validation (the env-ready swap of the spikes-001 placeholder parser).
5. **`test_real_geom_structural_rejects_placeholder_and_garbage`** — the spikes-001 placeholder container
   and random bytes are **rejected** by the real-format check.
   - Why: the real parser must not accept the placeholder (proves it's really parsing EA GEOM).
6. **`test_build_blender_command_uses_configured_executable`** — `build_blender_command` with a
   configured exe path emits that path as argv[0]; the default stays `"blender"`.
   - Why: `blender` is not on `PATH`; the real runner must reach the `.app` binary (implementer's catch).

**Exploratory arm (NOT unit-tested — run-and-observe, captured in the verdict):** the headless
`blender --background` GEOM emission itself. Its first valid output **becomes** fixture (4). The
"does Blender emit valid GEOM" question is answered by running the real probe + structural check, not by
a pre-written unit test (per the project TDD posture: the deterministic harness around a
non-deterministic/integration call is `/tdd`; the call itself is the spike).

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — frozen `BlenderJob`/`BlenderReport`/`GateMetrics`/`BBox`/`ErrorEnvelope`
  reused unchanged.
- **Orchestrator doc rows to write hot (Step 9 routing):** none to the `workers/blender/CLAUDE.md`
  cross-doc table (the §8 row stands). Likely Step-9 outputs: an **Architecture-doc note** firming §8's
  GEOM-emission method + the real structural-check set (route to the **integration-doc-edits ledger**,
  not a live `ARCHITECTURE.md` edit — per the user's accumulate-at-merge policy); a **lesson** on the
  headless GEOM-emission method; and the **verdict** (a `docs/sessions/` doc).
- **Shared-contract (Appendix-A seam) model touched?** No — no schema-snapshot needed.

## Things to flag at Step 2.5 (and a Step-7.5 early check-in is invited)
1. **GEOM-emission method — the central unknown.** Options: (a) a **custom minimal GEOM writer**
   (write the GEOM/RCOL bytes directly from `bpy` mesh data — most controllable headless, is a named
   §20 fallback, no GUI-plugin dependency); (b) drive an **existing Blender Sims-4 GEOM addon** headless
   (lower implementation effort *if* it runs on Blender 5.1 headless — itself unverified); (c) emit an
   intermediate and hand GEOM-writing to **@s4tk** (cross-area, S1b territory). My default vote:
   **(a) a custom minimal writer for a trivial mesh, for first signal** — then **report viability at
   Step 2.5 (or a Step-7.5 early ping) BEFORE deep implementation**, since the GEOM/RCOL format is deep.
   Research the format from the **@s4tk / sims4toolkit source** (Context7 has no @s4tk/GEOM coverage —
   confirmed in spikes-001; don't hand-roll from memory — cite the source you used in the verdict).
2. **Real-GEOM validation method.** (a) a **hand-rolled real-format structural parser** in Python
   (minimal: GEOM/RCOL magic + version + counts + UV); (b) **@s4tk round-trip** (most rigorous, but
   @s4tk is `workers/export` + not yet installed → cross-area); (c) bootstrap the structural assertions
   from the probe's **first captured output**. My default vote: **(a) + (c)** — a minimal real-format
   check, pinned against the first captured GEOM; defer full @s4tk round-trip validation to **S1b**
   (where @s4tk lands). Flag if you'd rather pull @s4tk in now.
3. **Test mesh.** Trivial primitive (cube/quad) vs a representative Sims prop. My default vote:
   **trivial cube** — first signal only; a real prop needs S2's image-to-3D output anyway.
4. **"Structurally valid" bar for a PASS-first-signal.** My default vote: parses as GEOM/RCOL +
   non-empty vertex/face/meshgroup + UV present is **enough for this probe's PASS** — in-game
   placeability is the S1c gate (Sims 4), explicitly NOT this probe's bar. Confirm.

## Dependencies + sequencing
- **Depends on:** spikes-001 (S1a harness, `0d6215f`, landed) + Blender 5.1.2 installed (**verified**).
- **Blocks / informs:** S1c (in-game placeability verdict — needs Sims 4) and S1b (clone-a-donor — the
  GEOM bytes this probe emits are what @s4tk will swap into a donor).

## Estimated commit count
**2–3.** A spike, but the deterministic surface is real: (1) env-ready hardening (fail-closed job-file +
tree-kill) — its own commit; (2) the real-format structural validator + captured fixture; (3) the real
runner wiring + the Blender-side emission script (the exploratory arm — may be marked spike/throwaway if
a method swap is needed). Do NOT bundle the hardening with the exploratory emission. The **verdict** is a
separate `docs(sessions)` commit at `/session-end`. Each is small + bisectable.

## Lessons-logged candidates anticipated
- **Convention candidate** — the viable headless Sims-4 GEOM-emission method on Blender 5.1 / Apple
  Silicon (what worked, what didn't — custom writer vs addon).
- **Architecture-doc note candidate** — firm §8's GEOM-emission path + the real structural-check set
  (→ integration-doc-edits ledger, applied at merge).
- **Future TODO — operational** — the in-game placeability verdict (S1c) + full @s4tk round-trip
  validation (S1b) once Sims 4 + @s4tk land.

## How to invoke
1. **Read this brief end-to-end** — note the hybrid split (deterministic harness/validator/hardening =
   TDD; GEOM emission = exploratory run-and-observe) and the 4 Step-2.5 questions.
2. **This is a new area-session continuation** in `workers/blender` (same area as spikes-001) — you're
   oriented; jump to `/tdd s1a_env_ready_geom_probe`. (Run `/session-start` only if this is a fresh
   session.)
3. **Step 2.5** — send the test-design write-up (deterministic tests) + your **GEOM-emission method**
   pick (Q1) with the research you based it on. A **Step-7.5 early ping is explicitly invited** if the
   method proves deep — don't burn the whole slice before surfacing a method that isn't working.
4. **Step 9** — categorized flags + the verdict draft; route the §8 arch note to the ledger.
