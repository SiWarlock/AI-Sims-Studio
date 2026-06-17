# LESSONS.md — AI Sims Creator (the Blender mesh/GEOM worker (bpy))

> Full prose for every lesson logged during work in `workers/blender/`. The compact index lives in `workers/blender/CLAUDE.md` "Lessons logged" table.
>
> **Lesson numbers are stable IDs.** New lessons get the next sequential number. Numbers may be referenced from code comments, commit messages, and cross-references between lessons. **Don't reorder; don't reuse a deleted number's slot.**
>
> **Lessons start at §1.** Each code area has its own lesson sequence — lessons don't carry across code areas.

---

## Lesson format

```markdown
## <a id="N"></a>N. <Short topic> — <one-line rule>

**Date:** YYYY-MM-DD.
**Source slice:** <slice-id or commit hash>.

<2-5 paragraphs explaining: what was discovered, why it matters, how to
apply the rule, what edge cases are still open. Cite file:line references
where applicable.>

**Rule:** <one-sentence summary, same as the heading subtitle>.
```

---

<a id="1"></a>
## 1. Inject the subprocess runner behind a Protocol — keep real `subprocess` out of the test path

**Date:** 2026-06-17.
**Source slice:** 1.1 / S1a (`workers/blender/spike_geom.py`).

The Blender worker's production path is a `blender --background --factory-startup --python` CLI
subprocess (§8). A subprocess call is the one thing you cannot exercise deterministically in a
headless unit test — it needs the real binary, it's slow, and (for Blender) it may not even be
installed yet. The S1a harness keeps the subprocess as the *only* env-gated surface by injecting it
behind a tiny seam: a `Runner` `Protocol` (`run(cmd: list[str], deadline_s: float) -> RunResult`)
passed into `run_geom_spike`. The production `_SubprocessRunner` wraps `subprocess.run(timeout=)`;
tests pass fakes (success / worker-failure / timeout). Everything *around* the call — command
construction, the §8 hang-watchdog (deadline → kill → retry-once → structured `ErrorEnvelope`), the
contract-valid `BlenderReport` assembly, the structural-GEOM gate — is then 100% testable now, with
zero Blender installed.

Why it matters here: S1 is the project's #1-risk go/no-go gate, and the env (Blender 5.1, a Sims 4
donor) was being provisioned in parallel. The seam let the entire deterministic harness land + go
green headless on day one, leaving only the real `blender --background` GEOM emission + the
in-game verdict as the env-ready follow-up. Without the seam, the whole slice would have blocked on
infra it didn't actually need to *build*.

Apply it whenever a worker shells out: the subprocess (or any external-process / network call) goes
behind an injected `Protocol`, and the deterministic control-flow that wraps it is tested against
fakes. The real impl's process-tree-kill / timeout-hardening is the env-ready concern, not a reason
to leave the control-flow untested. (Same principle the project applies to provider adapters — the
non-deterministic call sits behind a seam; the harness around it is `/tdd`.)

**Rule:** Spike/worker harnesses inject the subprocess runner behind a `Protocol` so the
deterministic core (command-build, watchdog, report-assembly) is fully testable headless; the real
`subprocess` is the only env-gated part. **Enforcement:** `pin: workers/blender/tests/test_spike_geom.py` (fake-runner injection exercises the seam; not mechanically grep-enforceable).

<a id="2"></a>
## 2. Headless Sims-4 GEOM emission works via a custom bpy `struct` writer on Blender 5.1 / Apple Silicon

**Date:** 2026-06-17.
**Source slice:** 1.1 / S1a env-ready probe (`blender_scripts/geom_export.py`, GEOM v0x05).

The project's #1 risk was: *can headless Blender on Apple Silicon emit placeable Sims-4 GEOM at all?*
S1a's env-ready probe answered the **emission-feasibility** half: **yes** — a custom minimal GEOM
writer (raw `struct` packing of GEOM v0x05 from `bpy` mesh data: positions/normals/uv_0 + triangulated
faces) run under `blender --background --factory-startup --python` produces structurally-valid GEOM
bytes that a real-format parser accepts (a 412-byte cube). The custom-writer is **the first of the
three §20 fallbacks** — proving it headless is the spike's value; it needs no GUI addon (S4S is a
Windows GUI tool), so it sidesteps the addon-headless unknown entirely. Format sourced from **SimsWiki
`0x015A1849`** (the GEOM RCOL chunk) — Context7 has **no** @s4tk/GEOM coverage, so don't hand-roll the
format from memory; cite the source you used.

The structural shape that worked, recorded so a future slice doesn't re-derive it: magic→version
(0x05/0x0C)→tgiOffset/Size→embeddedID(+MTNF if ≠0)→mergeGroup/sortOrder→numVerts→vertex-format
declaration {dataType/subType/bytesPerElement, UV = dataType 3}→vertexData→
itemCount/bytesPerFacePoint/numFacePoints+indices→(v0x05) skinControllerIndex→boneCount→TGI list.

How to test a thing whose whole point is "does this external tool work": **TDD the deterministic
wrapper, run-and-observe the call.** The validator, the runner hardening, the report assembly are
test-first; the actual `blender --background` emission is an integration run, and its **first valid
output is captured as the pinned fixture** — so a later test asserts the same validator accepts real
Blender output (proving the validator on the real artifact, not just a hand-built one). The
chicken/egg (no real GEOM fixture until the probe emits one) is resolved by capture-then-pin.

**Scope honesty:** this is GEOM-emission feasibility only. **In-game placeability (S1c, needs Sims 4)
and full @s4tk round-trip validation (S1b) are NOT proven by S1a** — the structural bar (parses +
non-empty counts + UV) is necessary, not sufficient, for "places in Build/Buy." Keep that distinction
in any go/no-go claim.

**Rule:** Prove a feasibility unknown with the cheapest controllable path (custom headless writer >
GUI-addon-headless); TDD the deterministic wrapper + capture-then-pin the first real output as the
fixture; never overclaim a structural PASS as an end-to-end PASS. **Enforcement:** `pin: workers/blender/tests/test_real_geom.py` + `tests/fixtures/cube_v0x05.geom` (captured-real-output confirmation; the emission itself is run-and-observe, not mechanically enforceable).
