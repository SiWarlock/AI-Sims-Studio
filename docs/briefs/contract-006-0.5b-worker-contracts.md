# /tdd brief — worker_contracts

## Feature
Freeze the **§8/§9 worker job/report contracts** in a NEW `workers.py`: the Blender mesh worker envelope
(`BlenderJob` → `BlenderReport` + the **GEOM-bytes** payload) and the Sims export worker envelope (`ExportJob` →
its report) — guarded by a §2.5-seam schema-snapshot. These are the **job-file/result-file envelopes** crossing
the sidecar↔worker boundary; the actual bpy mesh logic + @s4tk packaging are the worker impls (Phase 1/2), NOT here.

## Use case + traceability
- **Task ID:** 0.5b (decomposed from 0.5; sibling of 0.5a landed `de7caee`)
- **Architecture sections it implements:** `ARCHITECTURE.md §8` (Blender subsystem — `BlenderJob`/`BlenderReport`
  + GEOM-bytes), §9 (Sims export subsystem — `ExportJob` + report), §13 (artifact ordering — workers return
  **scratch-path refs**, the sidecar is sole writer), §17 (`ErrorEnvelope` on a failed report).
- **Related context:** Phase 0, contract track. Conventions from 0.2–0.5a: `aisims_contracts`, `extra="forbid"`,
  camelCase, `StrEnum` for closed sets, one `spec(§X)` snapshot per seam, the acyclic intra-package import DAG
  (extend `test_import_direction` to `workers.py`). **Safety rule 3 (sidecar = sole writer):** worker reports
  return **paths/refs into sidecar-provided scratch**, never bytes written into Postgres or the canonical tree —
  the contract must shape this (`geomBytesRef`/`packagePath` are refs, not inline payloads / not canonical-tree writes).

## Acceptance criteria (what "done" means)

**A. Blender worker envelope (§8)**
- [ ] `BlenderJob{meshPath, params, donorBBox, jobId}` (the inputs the sidecar hands the Blender CLI subprocess).
- [ ] `BlenderReport{geomBytesRef, previewRef, gateMetrics, status, error?}` — `geomBytesRef`/`previewRef` are
  **scratch-path refs** (safety rule 3), NOT inline bytes (Q2). `error` is `ErrorEnvelope|None` (§17).
- [ ] `gateMetrics` — the §8 game-ready gate metrics `{normals, uv, lods, polyByTile, meshgroups}` as a typed
  value model (shapes per Q3).

**B. Export worker envelope (§9)**
- [ ] `ExportJob{donorRef, geomBytesRef, textures, tuningEdits, targetTGIKeys, jobId}` (the export worker inputs;
  `geomBytesRef` is the §8 output threaded through — the GEOM-bytes flow §8↔§9).
- [ ] The export **worker report** `{packagePath, includedItems, resourceManifest, status, error?}` —
  `packagePath` a scratch-path ref (safety rule 3). **⚠ NAME COLLISION (Q1, load-bearing):** §9's report is
  *also* called `ExportReport` in the arch, but the §12 domain `ExportReport` (0.4a — `projectName/timestamp/
  included/excluded/functional/validationSummary/warnings/artifactPaths/runRef`) already owns that name. They are
  **different shapes for different concerns** (worker result vs human-readable summary). Disambiguate — do NOT
  reuse/duplicate the name.
- [ ] **Partial success** (§9): the report can express per-item completeness (status per Q4) — "each package
  individually complete-and-valid, never a half-file."

**C. Freeze + preflight**
- [ ] **Schema-snapshot test** over the worker value models, tagged `spec(§8)`+`spec(§9)` (or one combined
  `workers.schema.json` — Q5) → a drift IS the failure (Lesson 1).
- [ ] Status-enum membership tests (==); JSON round-trip + boundary rejection (`extra="forbid"`); the failure-path
  `ErrorEnvelope` test; `test_workers_import_direction` (workers imports `error` only — NOT ipc/domain/responses/
  providers; uses the shared `intra_imports` conftest fixture from 0.5a). `/preflight` clean.

## Wiring / entry point (Step 7.5)
`none — wiring lands in Phase 1 (spikes drive the workers) + Phase 2 (the engine submits these jobs + consumes the
reports) + 0.6 (TS/Node codegen — the @s4tk export worker is Node, consumes the generated types).` Reachability
surface = the `spec(§8/§9)` snapshot + importability from `aisims_contracts.workers`. Frozen-contract surface,
not runtime-wired (consistent with 0.2–0.5a).

## Files expected to touch
**New:**
- `packages/contracts/src/aisims_contracts/workers.py` — `BlenderJob`/`BlenderReport`/`gateMetrics`, `ExportJob`/
  the disambiguated export-worker report, the worker status enum(s).
- `packages/contracts/tests/test_workers.py` — A/B/C tests (reuse the `intra_imports` conftest fixture).
- `packages/contracts/tests/__snapshots__/workers.schema.json` — the `spec(§8/§9)` snapshot (Q5).

**Modified:**
- `packages/contracts/src/aisims_contracts/__init__.py` — re-export the worker contracts.

**Orchestrator territory (flag at Step 9 — I edit):** if Q1 disambiguates the worker report's name, I update
**§9 + Appendix-A** (which currently both say `ExportReport`) to the new name, atomic with the round.

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `tests/test_workers.py`
1. **`test_blender_job_report_models`** — `BlenderJob`/`BlenderReport` field sets exact; `geomBytesRef`/`previewRef`
   are str refs; round-trip; `extra="forbid"`. Why: §8 envelope + safety rule 3.
2. **`test_gate_metrics_model`** — `gateMetrics{normals,uv,lods,polyByTile,meshgroups}` typed per Q3. Why: §8 game-ready gate.
3. **`test_export_job_model`** — `ExportJob{donorRef,geomBytesRef,textures,tuningEdits,targetTGIKeys,jobId}`; round-trip. Why: §9.
4. **`test_export_worker_report_disambiguated`** — the §9 worker report exists under its **disambiguated name** and
   is NOT the §12 domain `ExportReport` (assert distinct symbols + distinct field sets). Why: Q1 collision guard / Lesson 5.
5. **`test_worker_status_members`** — worker status enum(s) membership == the Q4 set (incl. partial-success). Why: §9 partial success.
6. **`test_worker_failure_uses_error_envelope`** — a failed report carries `ErrorEnvelope`. Why: §17.
7. **`test_workers_import_direction`** — `workers.py` imports `error` only (uses the `intra_imports` fixture). Why: Lesson 5/7.
8. **`test_workers_schema_snapshot`** *(§2.5-seam, `spec(§8/§9)`)*. Why: Lesson 1.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** NEW `workers.py` (§8 + §9 seams). Appendix-A already lists `BlenderJob`/`BlenderReport`
  (§8, C↔D/B↔D) + `ExportJob`/`ExportReport` (§9, B↔C) — confirm == shipped; **the §9 + Appendix-A `ExportReport`
  name updates to the disambiguated worker-report name (Q1).**
- **Orchestrator doc rows to write hot (Step 9):** add the **workers** row to `CLAUDE.md` cross-doc table with
  `pin: tests/test_workers.py::test_workers_schema_snapshot`; do the §9/Appendix-A name disambiguation.
- **§2.5-seam touched?** **YES** (`workers.py`, C↔D/B↔C/B↔D). Snapshot mandatory this cycle.
- **Safety note:** the worker-return-path shape encodes **safety rule 3** (sidecar sole writer) — the security-reviewer
  should run at Step 8 (invariant policy), and the report fields stay refs (no inline canonical-tree write).

## Things to flag at Step 2.5
0. **(SIZE) commit count.** §8 + §9 are two envelopes sharing the worker-contract pattern + the GEOM-bytes flow.
   My default: **1 commit** (`workers.py` is one seam-family). Split to 2 (blender / export) only if you judge them
   separately bisectable. No safety invariant is *implemented* here (the contract shapes rule 3 but enforcement is
   the worker impl), so no mandatory own-commit.
1. **(LOAD-BEARING) `ExportReport` name collision.** The §9 worker report collides with the §12 domain `ExportReport`
   (0.4a, frozen). My default: **rename the worker one → `ExportJobReport`** (parallels the `…Job`→`…JobReport`
   pairing; leaves the frozen domain `ExportReport` untouched; I update §9 + Appendix-A to match). Alternatives:
   `WorkerExportReport`, `PackageReport`. Do NOT touch the domain `ExportReport` (re-freezing the domain snapshot is
   churn we avoid). Surface your read — this names a frozen §2.5 contract.
2. **(LOAD-BEARING — safety rule 3) GEOM-bytes transfer = scratch-path ref, not inline bytes.** My default:
   `geomBytesRef: str` (a path into sidecar-provided scratch the Blender worker wrote; the export worker reads it).
   Workers write ONLY to scratch + return paths (root `CLAUDE.md` rule 3); the contract must not invite a worker to
   embed bytes destined for the canonical tree. Confirm `geomBytesRef`/`previewRef`/`packagePath` are all refs.
3. **`gateMetrics` field types.** My default: `GateMetrics{normals: bool, uv: bool, lods: int, polyByTile: dict[str,int]
   (or list), meshgroups: int}` — pass/fail flags + counts; `polyByTile` keyed by LOD/tile. Surface the precise shapes
   (the §8 game-ready gate: normals recalc, uv_0+uv_1, 3–4 LOD+shadow, ~2000 tris/tile LOD0, meshgroup-count match).
4. **Worker status enum(s).** My default: worker-local minimal enums — `BlenderJobStatus{succeeded, failed}` (+ the
   §17 hang-watchdog kill→retry is impl, the terminal status is what's reported) and `ExportJobStatus{succeeded,
   partial, failed}` (§9 partial success). Do NOT reuse the domain `ExportState` (0.4a, the `ExportArtifact.buildStatus`
   — that's the node's rollup, a different concern) — the node MAPS the worker status onto it. Keeps `workers.py`
   importing only `error` (acyclic). Confirm vs reusing a domain enum.
5. **Snapshot file split.** My default: one combined **`workers.schema.json`** tagged `spec(§8)`+`spec(§9)` (both
   envelopes are the worker-contract seam). Alternative: separate `blender.schema.json` + `export.schema.json`.
   Confirm.
6. **Out of scope (confirm):** the bpy mesh/GEOM logic + the @s4tk packaging + atomic-write/DBPF-round-trip/test-install
   (safety rule 4) are **worker impls** (Phase 1 spikes + Phase 2), NOT contract shape; donor `.package` read-only +
   the donor-resolve flow are the Donor-Library subsystem / worker-impl.

## Dependencies + sequencing
- **Depends on:** 0.2 (`ErrorEnvelope`), 0.4 (the domain `ExportReport`/`ExportArtifact` the disambiguation must not
  collide with). Independent of 0.3/0.5a/0.5c (sibling seams).
- **Blocks:** 0.6 (codegen → TS for UI + **Node for the @s4tk export worker**), Phase 1 (S1 Blender spike + GEOM/DBPF
  spike drive these), Phase 2 (the engine submits jobs).

## Estimated commit count
**1** (per Q0). `workers.py` (both envelopes) + the `spec(§8/§9)` snapshot is one bisectable seam-family. Split to 2
only if the implementer judges blender/export separately cherry-pickable.

## Lessons-logged candidates anticipated
- **Convention candidate** — disambiguating a name collision across two §2.5 seams (the §9 worker report vs the §12
  domain `ExportReport`): rename the *later/less-frozen* one, never re-freeze the landed contract.
- **Architecture-doc note candidate** — §9/Appendix-A `ExportReport` → the disambiguated worker-report name; record
  the worker-return-path (safety rule 3) shape that consumers (Phase-2 engine, @s4tk worker) depend on.
- **Convention candidate** — worker reports carry scratch-path **refs**, never inline bytes / canonical-tree writes
  (safety rule 3 shaped at the contract).

## How to invoke
1. Read this brief + `ARCHITECTURE.md §8` + §9 (+ §13 artifact ordering) end-to-end.
2. **`/tdd worker_contracts`** (continuing session; no `/session-start`).
3. **Step 2.5** — answer Q0–Q6 (Q1 name-collision + Q2 GEOM-ref are the load-bearing calls); coverage map. Wait for
   `APPROVED.` before GREEN.
4. **Step 9** — surface the workers cross-doc row + the §9/Appendix-A `ExportReport` disambiguation + lessons.
