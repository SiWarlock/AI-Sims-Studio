# /tdd brief — s1a_geom_spike_harness

## Feature
The headless-testable core of spike **S1** (the GEOM/DBPF placeability gate — the project's #1 risk):
a **structural-GEOM validator** (§8's "immediate structural validation — fast GEOM check before
packaging") plus a **§8/§9 contract-conformant Blender-CLI orchestration harness** (build the
`blender --background` invocation, run via an *injected* runner, assemble a contract-valid
`BlenderReport`, apply the §8 hang-watchdog control flow). All of it is deterministic and runs
**headless now**; the real `blender --background` GEOM probe + the in-game verdict are **deferred to
env-ready** (Blender 5.1.x is being provisioned in parallel; a real Sims 4 install + donor land later).

## Use case + traceability
- **Task ID:** 1.1
- **Architecture sections it implements:** `ARCHITECTURE.md §8` (mesh/Blender subsystem — game-ready
  gate, GEOM-as-a-distinct-stage with immediate structural validation, the hang-watchdog, the
  `BlenderJob`→`BlenderReport` job-file/result-file envelope), `§20` (S1 is a *feasibility go/no-go
  gate*, not a scope reducer; the three unverified fallbacks), `§22` (open question 1 — no verified
  headless-Mac GEOM path; open question 6 — @s4tk/GEOM provenance, relevant to the §8↔§9 handoff).
- **Related context:** the frozen worker contracts in `packages/contracts`
  (`aisims_contracts.workers`: `BlenderJob` / `BlenderReport` / `GateMetrics` / `BBox`, 0.5b
  `ccce712`, signature-frozen, `model_validator` pins status↔outputs per safety rule 6). `§9`'s
  `ExportJob.geomBytesRef` is the downstream consumer of this slice's GEOM bytes — the **§8↔§9
  GEOM-bytes flow** — so the validator's notion of "structurally valid GEOM" is what S1b
  (`workers/export` clone-a-donor) will ingest. Re-scoped S1 acceptance (user call, 2026-06-17):
  the deterministic scaffolding is built + tested NOW; the actual go/no-go **verdict is deferred to
  env-ready, not a forced pass**.

## Acceptance criteria (what "done" means)
- [ ] `validate_geom_structure(data: bytes) -> GeomStructResult` returns `ok=False` with a structured
      issue for empty / truncated / bad-magic input — and **never raises** on malformed bytes
      (fail-at-GEOM-not-at-install: a fast structural reject, not an exception).
- [ ] For a valid minimal GEOM fixture, `validate_geom_structure` returns `ok=True` plus extracted
      counts (vertices > 0, faces/indices > 0, meshgroups ≥ 1) and UV-set presence flags.
- [ ] `build_blender_command(job: BlenderJob, script: str, jobfile: str) -> list[str]` produces an
      invocation beginning `blender --background --factory-startup --python <script>` and passes the
      job-file path after the `--` separator (assert flag presence + the `--factory-startup` isolation
      flag + arg-after-`--`).
- [ ] `run_geom_spike(job, runner, deadline_s)` with a **fake runner** that writes a success
      result-file returns a **contract-valid `BlenderReport`** (`status=succeeded` ⟹ `geomBytesRef`
      present + `gateMetrics` present + `error is None`; the frozen `model_validator` accepts it), and
      the `geomBytesRef` points inside the provided scratch dir.
- [ ] **Hang-watchdog (§8):** a runner that exceeds `deadline_s` is killed and retried **exactly once**;
      a second deadline breach returns `BlenderReport(status=failed, error=<ErrorEnvelope>)` — never a
      raise, never a half-result.
- [ ] The worker writes **only** under the sidecar-provided scratch dir and returns refs — no Postgres
      / canonical-artifact-tree access (the `forbidden-patterns` rule-2 grep stays clean).
- [ ] All unit tests in `workers/blender/tests/test_geom_structural.py` and
      `.../test_spike_geom.py` pass; `/preflight` clean (ruff + `mypy --strict` + pytest).
- [ ] **Env-ready follow-up (NOT done in this slice — recorded, not forced):** the real
      `blender --background` GEOM emission + the structural-validity verdict on actual Blender output
      run when Blender 5.1.x lands; tracked as the S1a env-ready probe.

## Wiring / entry point (Step 7.5)
`workers/blender/spike_geom.py` exposes the spike's callable entry point (`run_geom_spike`, plus a
thin `__main__` that reads a job-file path → runs → writes the result-file) — this is what the
**S1a env-ready probe** invokes once Blender lands, and what S1c's test-install consumes. Production
sidecar→worker wiring (the engine dispatching `BlenderJob`s on the real pipeline) is **not** this
slice: `none — production wiring lands in Phase 4`. The slice is reachable now via its own
`run_geom_spike` entry point + its tests; confirm the entry point is real, not test-only.

## Files expected to touch
**New:**
- `workers/blender/geom/__init__.py`
- `workers/blender/geom/structural.py` — the structural-GEOM validator + `GeomStructResult`
  (real, reusable Phase-4 infra — the §8 "fast GEOM check").
- `workers/blender/spike_geom.py` — the orchestration harness: `build_blender_command`,
  `run_geom_spike` (injected `Runner` seam, result-file parse, contract-valid `BlenderReport`
  assembly, §8 hang-watchdog), `__main__` entry point.
- `workers/blender/io/__init__.py` + `workers/blender/io/scratch.py` *(if needed)* — scratch-dir
  read/write helpers (sidecar-provided scratch only; never the canonical tree).
- `workers/blender/tests/test_geom_structural.py`
- `workers/blender/tests/test_spike_geom.py`
- `workers/blender/tests/fixtures/` — the minimal GEOM fixture (synthetic-now / real-donor at
  env-ready — see Step-2.5 Q1).

**Modified:**
- `workers/blender/pyproject.toml` — add the `aisims_contracts` workspace dependency (the harness
  imports the frozen `BlenderJob`/`BlenderReport`/`GateMetrics`/`BBox`). Flag if the workspace wiring
  needs a root change (Step 7.5).

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2)
Tests in `workers/blender/tests/test_geom_structural.py`:

1. **`test_validate_geom_rejects_empty`** — empty bytes → `ok=False`, a `parse`/`truncated` issue.
   - Asserts: `validate_geom_structure(b"").ok is False` and an issue is present; no exception.
   - Why: §8 "fail at GEOM, not at install" — the fast check rejects soft.
2. **`test_validate_geom_rejects_bad_magic`** — wrong leading magic → `ok=False`, a `magic` issue.
   - Asserts: a non-GEOM byte blob is rejected with a structured `magic`/`version` issue.
   - Why: §8 structural validation is a real gate, not a pass-through.
3. **`test_validate_geom_rejects_truncated`** — valid magic but a body cut short → `ok=False`.
   - Asserts: truncation past the header → structured issue, no raise.
   - Why: §8 fast-reject of malformed GEOM.
4. **`test_validate_geom_accepts_minimal_fixture`** — the minimal valid GEOM fixture → `ok=True`.
   - Asserts: `ok is True`; extracted `vertices > 0`, `faces > 0`, `meshgroups >= 1`; UV flags set.
   - Why: §8 — a structurally valid GEOM yields the counts the game-ready gate / §9 packager need.
5. **`test_validate_geom_never_raises_on_fuzz`** — a handful of random/garbage blobs → all return a
   `GeomStructResult`, none raise.
   - Asserts: every input yields a result object; never an exception.
   - Why: §8 fail-soft (a malformed mesh must surface as a GEOM-stage failure, not a crash).

Tests in `workers/blender/tests/test_spike_geom.py`:

6. **`test_build_blender_command_shape`** — the CLI invocation is correctly formed.
   - Asserts: starts `blender --background --factory-startup --python <script>`; job-file passed after `--`.
   - Why: §8 production path is the `blender --background --factory-startup --python` CLI subprocess.
7. **`test_run_geom_spike_success_assembles_valid_report`** — fake runner writes a success result-file.
   - Asserts: returns `BlenderReport(status=succeeded)` with `geomBytesRef` (inside scratch) +
     `gateMetrics`, `error is None`; the frozen `model_validator` accepts it.
   - Why: §8 `BlenderJob`→`BlenderReport` envelope conformance (safety rule 6).
8. **`test_run_geom_spike_failed_runner_yields_failed_report`** — runner reports a worker failure.
   - Asserts: `BlenderReport(status=failed, error=<ErrorEnvelope>)`; no `geomBytesRef`.
   - Why: §8 + rule-6 status↔outputs (failed ⟹ error present).
9. **`test_run_geom_spike_watchdog_retries_once_then_fails`** — runner times out twice.
   - Asserts: runner invoked exactly twice (kill→retry-once); final report `status=failed` with a
     structured `ErrorEnvelope`; never raises.
   - Why: §8 hang-watchdog (wall-clock deadline → kill+retry-once → structured error).
10. **`test_run_geom_spike_validates_emitted_geom`** — success result-file carries the minimal fixture
    bytes → the harness runs `validate_geom_structure` on them before reporting success.
    - Asserts: a structurally *invalid* emitted GEOM downgrades the report to `failed` (the GEOM stage
      gates before packaging, §8); a valid one stays `succeeded`.
    - Why: §8 "GEOM export = a distinct stage with immediate structural validation."

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none. The harness **reuses** the frozen `BlenderJob`/`BlenderReport`/
  `GateMetrics`/`BBox` contracts unchanged — no new shared-contract model, no field add/remove/rename.
- **Orchestrator doc rows to write hot (Step 9 routing):** none expected. The `workers/blender/CLAUDE.md`
  cross-doc table already carries the `BlenderJob`/`BlenderReport` §8 row. `GeomStructResult` is an
  area-internal type (not a §8/§9 seam model), so it stays out of the cross-doc table. If the slice
  surfaces a new behavior worth pinning in §8 (e.g. the concrete structural-check set), flag it as an
  **Architecture-doc note** at Step 9 — do not edit `ARCHITECTURE.md` here.
- **Shared-contract (Appendix-A seam) model touched?** No — no Appendix-A model's invariant changes, so
  no new schema-snapshot test is required (the existing `spec(§8)` worker snapshot already guards the
  contracts this slice consumes).

## Things to flag at Step 2.5
1. **Minimal structural-GEOM check set + fixture sourcing.** What does the spike's "fast GEOM check"
   actually assert, and where does the test fixture come from before a real Sims 4 donor exists? Options:
   (a) magic+version+non-empty vertex/face/meshgroup counts + UV-set flags, with a **synthetic minimal
   GEOM fixture** hand-built from the GEOM/RCOL format spec; (b) defer the positive-path assertion until
   a real donor-extracted GEOM lands. My default vote: **(a)** — a minimal-but-real structural subset +
   a small synthetic fixture now, swapped for a real-donor-extracted fixture at env-ready. Keeps the
   validator genuinely test-first today; the fixture swap is a one-line follow-up. (GEOM is a
   Sims-4-specific binary format — pull the structure from an @s4tk / sims4toolkit GEOM reference, not
   from memory.)
2. **Contract import under the worker env vs Blender's bundled Python.** The harness imports
   `aisims_contracts` for real conformance — fine under the worker's `uv` env (where pytest runs), but
   under `blender --background` the script runs on Blender's bundled Python with a different sys.path.
   My default vote: **import `aisims_contracts` now** (real conformance under the worker env); treat the
   Blender-bundled-Python provisioning as a **deploy concern deferred to env-ready** and surface it as a
   carry-forward at Step 9. Don't hand-roll a duplicate of the contract to dodge the import (forbidden).
3. **Runner-injection seam shape.** How is the real subprocess kept out of the test path? My default
   vote: a `Runner` **Protocol** (`run(cmd: list[str], deadline_s: float) -> RunResult`) injected into
   `run_geom_spike`; the production impl wraps `subprocess.run` (its wiring deferred to env-ready),
   tests pass fakes (success / failure / timeout). Matches the project's adapter-seam posture.
4. **Watchdog retry policy.** §8 says "kill+retry-once." My default vote: **exactly one** retry on a
   deadline breach; the second breach → `failed` + structured `ErrorEnvelope`. No exponential backoff,
   no unbounded retry (a spike harness must terminate deterministically).

## Dependencies + sequencing
- **Depends on:** 0.5b frozen worker contracts (`ccce712`, LANDED) — `BlenderJob`/`BlenderReport`/
  `GateMetrics`/`BBox`. No other prior slice.
- **Blocks:** S1b (`workers/export` `spike_clone` clone-a-donor — consumes the validated GEOM-bytes
  notion via the §8↔§9 handoff) and the **S1a env-ready real-Blender probe** (runs the same harness
  against a live `blender --background` once Blender 5.1.x is installed).

## Estimated commit count
**2 (bundle-eligible).** (1) the structural-GEOM validator (`geom/structural.py` + its tests);
(2) the contract-conformant orchestration harness + watchdog (`spike_geom.py` + its tests). Same area,
shared spike context, **no safety-invariant pin is being added** (the sole-writer/scratch-only rule is
enforced by the existing `forbidden-patterns` grep, not a new pin in this slice) — so the two may land
as one bundled commit if the total stays small and bisectable; split the validator out first if it
grows. Neither commit may bundle a real-Blender integration run (that's the env-ready follow-up).

## Lessons-logged candidates anticipated
- **Convention candidate** — "spike/worker harnesses inject the subprocess runner behind a `Protocol`
  so the deterministic logic (command-build, hang-watchdog, report-assembly) is fully testable headless;
  the real `subprocess` stays out of the test path until env-ready."
- **Architecture-doc note candidate** — the concrete structural-GEOM check set may firm up §8's
  "immediate structural validation" from prose into a named check list (magic/version/counts/UV).
- **Future TODO — operational** — (a) cross-runtime contract provisioning: `aisims_contracts` on
  Blender's bundled-Python sys.path at deploy; (b) the S1a env-ready real-Blender probe + the S1c
  in-game test-install verdict (HITL, user-run).

## How to invoke
1. **Read this brief end-to-end** — especially "Things to flag at Step 2.5" (4 design questions with
   default votes; take defaults or ping back).
2. **Run `/tdd s1a_geom_spike_harness`** in the implementer session.
3. **Step 0 (Restate)** — confirm the restatement matches the Feature line (note the env-ready deferral:
   real Blender run is NOT in this slice).
4. **Step 1 (Identify files)** — confirm against "Files expected to touch."
5. **Step 2.5** — send the test-design write-up (one `Asserts: <invariant> (§anchor)` line per test +
   the per-acceptance-bullet coverage map) and the 4 design-question answers; wait for `APPROVED.`.
6. **Step 9 (summarize)** — surface the cross-runtime-contract-provisioning carry-forward + anything
   beyond the anticipated lessons-logged candidates.
