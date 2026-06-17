# USER_FLOWS — AI Sims Creator

> arch-draft (Brain 1) rough draft. Phase-4 artifact. Covers creator workflows A–F (PRD §11) + inferred
> system/admin flows G–K. Confirmed cross-cutting behavior: **bounded-parallel** item execution (configurable
> cap, one active project), **reconcile-and-resume** crash recovery, **soft-budget** cost warnings,
> **scoped per-item/per-stage** repair. Every in-scope PRD requirement maps to a flow (coverage table at end).

**Cross-cutting invariants (apply to all generation flows):**
- Every step emits a **trace** (OBS-001) and updates **step state** (pending/running/succeeded/failed/
  skipped/waiting-for-user/retrying/cancelled).
- Every artifact records **lineage** to its inputs (OBS-003).
- Failure of one item never corrupts the project or other items (PIPE-004 / FR-3D-006).
- Accepted assets are never overwritten without confirmation (NFR §22.6).
- Human review gates: plan, concept, mesh, overlay, export (PIPE-005).

---

## Flow A — Create a New Collection
- **Actor:** Creator. **Trigger:** clicks New Project. **Preconditions:** app running; (optional) provider keys set.
- **Steps:** name → collection prompt → optional required items / style notes / item count / output mode
  (decor | functional | mixed) / generation mode (fast | balanced | quality) → submit → system runs
  **Collection Planner + Style Bible Generator** → user reviews/edits plan (add/remove/rename/edit/confirm
  archetype/lock required) → **approve plan** (gate 1).
- **System responsibilities:** validate required fields; persist project + settings; generate schema-valid
  plan incl. required items, archetype assignment, functional-candidate marking; produce coherent style bible;
  flag unsupported items (convert-with-confirmation or mark-unsupported).
- **Success:** approved Collection Plan v1 persisted. **Failures:** LLM error/timeout → retry/edit-prompt;
  schema-invalid plan → repair/regenerate; unsupported items → surfaced with creator-friendly reason.
- **Data touched:** Project (C), CollectionPlan (C), StyleBible (C), ItemSpec[] (C), PipelineRun+trace (C).
- **Lifecycle:** project planned; items → `planned`.

## Flow B — Generate Concepts
- **Actor:** Creator (+ Concept Prompt/Image workers). **Trigger:** plan approved / per-item regenerate.
- **Steps:** per item spec → generate concept prompt → generate N concept candidates (N from generation
  mode) → user reviews candidates (approve / select-preferred / regenerate / edit-prompt / reject-with-reason
  / skip) → **approve concept** (gate 2) → approved concept becomes image-to-3D input.
- **System responsibilities:** preserve every concept artifact + prompt + provider; optionally score
  image-to-3D readiness (EVAL-002 criteria); capture approve/reject as preference events (OBS-004).
- **Success:** ≥1 approved concept per included item. **Failures:** image-gen error → retry/regenerate;
  low-readiness concept → warn but allow; budget threshold reached → soft warning before more candidates.
- **Data touched:** ConceptCandidate[] (C/U), preference events (C), trace (C). **Lifecycle:** item →
  concept-generating → concept-review-needed → (approved) mesh-pending.

## Flow C — Generate 3D Assets
- **Actor:** Creator (+ 3D Router, Mesh QA, Blender Cleanup, Swatch workers). **Trigger:** concept approved /
  per-item regenerate mesh / rerun cleanup.
- **Steps:** approved concept → 3D Router calls one/more image-to-3D adapters (cloud-first; local fallback) →
  store mesh candidate(s) → **Mesh QA** (import, nonzero/plausible dims, face budget, normals, material/UV
  presence, no extreme spikes) → passing candidates → **Blender cleanup** (import, fix orientation, normalize
  scale, set origin/pivot, apply transforms, repair/preserve materials, reduce geometry where feasible,
  **generate game-ready GEOM + LODs + footprint/rig**, render preview, export normalized intermediate) →
  preview shown → user accepts / regenerates / reruns cleanup.
- **System responsibilities:** store all mesh metadata (FR-3D-004) + QA score + cleanup status + preview path;
  structured failure on any stage (FR-3D-006 / FR-BLEND-005); never block other items; honor concurrency cap.
- **Success:** ≥1 preview-ready mesh variant per included item meeting QA. **Failures:** adapter error/timeout →
  retry/alt-adapter/regenerate; QA reject → regenerate or exclude; Blender crash → structured error + retry
  just this stage; non-game-ready geometry → flag for manual fallback (`open question`/risk).
- **Data touched:** MeshCandidate[] (C/U), normalized intermediate + preview (C), AssetVariant (C/U), trace (C).
- **Lifecycle:** mesh-pending → mesh-generating → mesh-QA-pending → blender-cleanup-pending → preview-ready.

## Flow D — Curate the Collection
- **Actor:** Creator. **Trigger:** items have previews. **Steps:** Collection Board (grid, thumbs, status,
  badges) → open Item Detail → edit metadata (name/desc/tags/price/notes/swatch labels) → choose swatch/variant
  → include/exclude → mark eligible items for functional upgrade → add new item / filter by status.
- **System responsibilities:** persist edits; recompute item validation; keep include/exclude explicit; expose
  generation history.
- **Success:** curated set with clear include/exclude + selected variants. **Failures:** edit conflict with
  in-flight regen → guard against overwriting accepted assets. **Data touched:** ItemSpec (U), AssetVariant (U),
  metadata (U). **Lifecycle:** item → needs-review ↔ export-ready / excluded.

## Flow E — Make an Item Functional
- **Actor:** Creator (+ Functional Overlay Planner). **Trigger:** clicks Make Functional on an eligible item.
- **Steps:** show source asset → show **eligible** functional archetypes only (from the extensible archetype registry; seeds: audio/light/mirror/moodlet) →
  choose archetype → configure simple behavior options → generate overlay (clone EA **donor tuning**) →
  behavior summary → **validate compatibility** (source asset ↔ overlay) → **approve overlay** (gate 4) →
  choose export mode (decor-only | functional-only | both).
- **System responsibilities:** overlay is an **extension of the same item identity** (not a duplicate); store
  overlay schema + user config + validation state + export mode; only show supported archetypes.
- **Success:** valid overlay attached; item exportable as chosen mode with real in-game behavior. **Failures:**
  incompatible source/overlay → actionable blocker; tuning-clone failure → structured error + retry.
- **Data touched:** FunctionalOverlay (C/U), ValidationResult (C), trace (C). **Lifecycle:** item gains
  functional state; export mode set.

## Flow F — Validate and Export (+ Test-Install)
- **Actor:** Creator (+ Validation + Package/Export workers). **Trigger:** opens Validation Center / Export Center.
- **Steps:** run project validation → show blockers/warnings/passes (project/item/mesh/overlay/export scopes) →
  fix/regenerate/exclude/retry → Export Center summary → choose output path → **approve export** (gate 5) →
  build DBPF `.package`(s) via clone-and-replace → write export report + logs → show success / success-with-
  warnings / partial / failed / cancelled → **optional test-install to configured Sims 4 Mods folder** →
  manual in-game placeability/behavior check (anchor slice).
- **System responsibilities:** block export on critical failures (FR-VAL-004); produce real installable
  artifacts for **all** included items; reproducible-from-state where feasible; export report (§24.2).
- **Success:** installable package(s) + report; anchor items verified placeable/behaving in-game. **Failures:**
  validation blockers → not exportable until resolved; build error → structured failure + partial report;
  test-install/path error → surfaced, export artifact still retained.
- **Data touched:** ValidationResult[] (C), ExportArtifact (C), export report + logs (C). **Lifecycle:** project
  → validating → exported.

---

## System Flow G — Pipeline Run Execution (job engine)
- **Actor:** job/run engine + workers. **Trigger:** any generation request. **Behavior:** represent work as a
  **graph run** with step-level state; schedule items **bounded-parallel** (configurable cap, default ~2–4),
  **one active project**; stream progress to Generation Workspace; enforce tool-call boundaries; emit traces +
  cost/latency. **Recovery:** durable step state so a single failed step doesn't sink the run.

## System Flow H — Scoped Repair Loop
- **Trigger:** retry of a single stage for a single item (regenerate concept / regenerate mesh / rerun cleanup /
  retry overlay / exclude-and-continue). **Behavior:** rerun only the failed stage; preserve upstream accepted
  artifacts + lineage; new attempt is a new candidate (history retained).

## System Flow I — Crash / Abandonment Recovery
- **Trigger:** app reopen after close/crash with runs in progress. **Behavior:** detect interrupted runs;
  **reconcile in-flight cloud jobs by re-polling provider job IDs** where the provider supports it; reattach
  completed results, mark unrecoverable steps for retry; offer **resume from last completed step**; never lose
  accepted assets. `production-hardening`.

## System Flow J — External Dependency Failure
- **Trigger:** cloud provider outage / rate-limit / timeout, or Blender crash. **Behavior:** structured error
  with actionable message; retry-with-backoff; offer alternate adapter where configured; isolate to the
  affected item; preserve partial state + trace. Soft-budget warnings surface here too.

## Admin Flow K — Maintainer / Dev Panel
- **Actor:** Maintainer (Advanced mode). **Behavior:** view pipeline runs/traces/job history/tool calls/
  artifact paths/validation logs/eval results/adapter config; rerun a step or full pipeline; export logs; open
  artifact path; switch mock↔real adapter; view raw project state.

---

## Requirement → Flow Coverage (stop-condition check)
| PRD area | Flow(s) | Notes |
|---|---|---|
| Project mgmt (FR-PROJ) | A, K | persistence, reopen, settings |
| Prompt/Planning (FR-PLAN) | A | plan + style bible + approval |
| Concept (FR-CONCEPT) | B | candidates, approval, scoring |
| Image-to-3D (FR-3D) | C, G | adapters, multi-candidate, QA, failure isolation |
| Blender (FR-BLEND) | C, J | cleanup, preview, **game-ready GEOM/LOD**, structured errors |
| Curation (FR-CURATE) | D | board, detail, regen, include/exclude, metadata |
| Functional (FR-FUNC) | E | overlay-as-extension, eligibility, validation, export mode |
| Validation (FR-VAL) | F | multi-scope, block-on-critical |
| Export (FR-EXPORT) | F | real DBPF for all items, report, test-install |
| Dev/Advanced (FR-DEV) | K | runs, logs, artifacts, traces, reruns, adapter config |
| Observability (OBS) | all (cross-cutting) | trace, lineage, review events |
| Resumability/recovery (PIPE-004) | G, H, I | step state, scoped repair, reconcile-resume |
| Human gates (PIPE-005) | A,B,C,E,F | 5 approval gates |

**Unmapped / flagged:** in-game *behavior fidelity* for all 4 functional archetypes (Flow E) and *game-ready
geometry feasibility* (Flow C) are the two flows whose success depends on unresolved spikes — tracked in
`RISKS.md`, sequenced behind early spikes.
