# PRD → REQ Coverage — AI Sims Creator

> Persisted by arch-finalize (dimension 1). 140 PRD items walked. Uncovered + citation problems are the human-gate list.

## Coverage table

| PRD item | Covering REQ / status |
|---|---|
| §8.1 #1 Desktop project system | FR-PROJ-001/002/003 + REQ-D-101 (PRESEARCH P6) — Electron desktop, app-managed local Postgres + on-disk artifacts (ARCH §4,§7; ADR-09) |
| §8.1 #2 New collection wizard | UI-002 + AC-002 (covered ARCH §11; USER_FLOWS Flow A) |
| §8.1 #3 Prompt-to-collection planning | FR-PLAN-001/002 + AC-003 (ARCH §6.7 Collection Planner; Flow A) |
| §8.1 #4 Collection plan review and editing | FR-PLAN-005 + UI-003 + AC-004 (Flow A) |
| §8.1 #5 Concept image generation and review | FR-CONCEPT-001..004 + UI-005 + AC-005/006 (ARCH §6.4 ImageGenProvider; Flow B) |
| §8.1 #6 Image-to-3D model adapter layer | FR-3D-001/003 + ADR-003 Image3DProvider (ARCH §6.4) |
| §8.1 #7 Candidate mesh generation | FR-3D-002 + AC-007 (Flow C; MeshCandidate entity) |
| §8.1 #8 Blender automation strategy w/ Python+MCP+hybrid spike support | PARTIAL — FR-BLEND-001/002 + BLEND-001..005 adopted, but ADR-006 EXCLUDES MCP entirely ("MCP excluded") — see citationProblems; spike now Python-vs-bpy only, not the PRD-mandated 3-way (Python/MCP/hybrid) |
| §8.1 #9 Mesh QA and preview rendering | FR-3D-005 + FR-BLEND-003 + EVAL-005 (Flow C) |
| §8.1 #10 Collection board | FR-CURATE-001 + UI-006 + AC-010 (Flow D) |
| §8.1 #11 Item detail screen | UI-007 + FR-CURATE-002 (Flow D) |
| §8.1 #12 Per-item regeneration and curation | FR-CURATE-003 + ORCH-005 + AC-011 (System Flow H scoped repair) |
| §8.1 #13 Supported functional overlay wizard | FR-FUNC-001 + UI-008 + AC-013 / REQ-F-102 (Flow E; ADR-010) |
| §8.1 #14 Validation center | FR-VAL-001/002 + UI-009 + AC-014 (Flow F) |
| §8.1 #15 Export center | FR-EXPORT-001 + UI-010 + AC-015 / REQ-F-101 (Flow F; ADR-005) |
| §8.1 #16 Advanced developer panel | FR-DEV-001..006 + UI-011 + AC-016 (Admin Flow K) |
| §8.1 #17 Observability for generation runs | OBS-001..005 + ADR-07 LangSmith (ARCH §9,§12) |
| §8.1 #18 Eval harnesses | EVAL-001..009 + ADR-08 + AC-017 (ARCH §14) |
| §8.1 #19 Mock pipeline adapters for parallel UI build | PIPE-002 / REQ-T-101 + AC-018 (ARCH §4A Track A; ADR-01) |
| §8.2 should #1 Multiple concept candidates per item | FR-CONCEPT-002 + REQ-NF-103 gen-mode→candidate-count (PRESEARCH P4; Flow B) |
| §8.2 should #2 Multiple mesh candidates per item | FR-3D-003 + DATA_MODEL MeshCandidate 1-N (ConceptCandidate 1-N MeshCandidate) |
| §8.2 should #3 Collection-level style lock | FR-PLAN-004 StyleBible (DATA_MODEL StyleBible; PRESEARCH P1 style-lock) |
| §8.2 should #4 Test install to configured local target folder | FR-EXPORT-006 ELEVATED to REQ-O-101 must-ship (ADR-05; Flow F) |
| §8.2 should #5 Human preference capture on approve/reject | OBS-004 + EVAL-009 + ReviewEvent entity (DATA_MODEL) |
| §8.2 should #6 Basic rebuild from saved project state | REQ-NF-102 reconcile-and-resume + NFR §22.2 (System Flow I); export reproducible-from-state (Flow F) |
| §8.2 should #7 Export report w/ items, warnings, artifacts | FR-EXPORT-004 + §24.2 + ExportReport entity |
| §8.3 nice-to-have #1-8 (richer behaviors, more archetypes, CAS, animation, script mods, in-game smoke test, marketplace, collaboration) | out-of-scope(post-MVP per §8.3; ARCH §1a/§18 Non-Goals; novel scripted gameplay = feasibility wall; CAS/anim/marketplace/collab explicitly deferred) |
| §9.1 7 decorative Build/Buy categories (clutter/tabletop/shelf/electronics/light/mirror/wall) | REQ-F-106 open PlacementType registry SUPERSEDES the fixed 7 (ADR-010; DATA_MODEL PlacementType) — see notes: decorative breadth made open, 7 named categories not individually enumerated as donor mappings |
| §9.2 4 functional archetypes (audio/light/mirror/moodlet) + optional computer-prop | REQ-F-102 extensible FunctionalArchetype registry, seeds audio/light/mirror/moodlet (ADR-010; DATA_MODEL FunctionalArchetype). Computer-prop = optional, registry-addable |
| §10.1 Decorative playable asset (6 reqs: artifact/metadata/category/preview/in-package/placeable) | REQ-F-101 real-placeable DBPF for all items + §23.3 item validation + test-install gate (ADR-05; Flow F) |
| §10.2 Functional playable asset (6 reqs incl. compatibility, paired/variant export) | FR-FUNC-003/004/006 + REQ-F-102/103 tuning-clone + §23.4 overlay validation (Flow E; FunctionalOverlay entity) |
| §10.3 Unsupported generation handling (convert-to-nearest OR mark-unsupported w/ reason) | PARTIAL — captured in PRESEARCH P1 hidden-mechanics + Flow A ("flag unsupported items"), but NO PRD-native REQ id and not in ARCH §6 modules or DATA_MODEL invariants — see uncovered (open-registry reframe weakens but does not delete this requirement) |
| §12 UI-001 Project Dashboard | UI-001 (ARCH §11; Flow A/K) |
| §12 UI-002 New Collection Wizard | UI-002 (ARCH §11; Flow A) |
| §12 UI-003 Collection Plan Review | UI-003 (ARCH §11; Flow A) |
| §12 UI-004 Generation Workspace (13 statuses, queue, retry) | UI-004 + ORCH-002 (ARCH §11; System Flow G; 13-state item machine DATA_MODEL) |
| §12 UI-005 Concept Review Screen | UI-005 (ARCH §11; Flow B) |
| §12 UI-006 Collection Board | UI-006 (ARCH §11; Flow D) |
| §12 UI-007 Item Detail Screen | UI-007 (ARCH §11; Flow D) |
| §12 UI-008 Functional Upgrade Wizard | UI-008 (ARCH §11; Flow E) |
| §12 UI-009 Validation Center | UI-009 (ARCH §11; Flow F) |
| §12 UI-010 Export Center | UI-010 (ARCH §11; Flow F) |
| §12 UI-011 Advanced / Developer Panel | UI-011 + FR-DEV-* (ARCH §11; Admin Flow K) |
| §13 PIPE-001 Stable pipeline interface (13 min ops) | REQ-I-101 versioned IPC contract (ARCH §6.1; ADR-01) |
| §13 PIPE-002 Mock adapter requirement | REQ-T-101 (ARCH §6.4; ADR-01) |
| §13 PIPE-003 Real adapter requirement | PIPE-003 + provider interfaces (ARCH §6.4; ADR-03/04/14) |
| §13 PIPE-004 Resumable jobs (step-level state) | REQ-NF-102 + ADR-02 (ARCH §6.2/§6.3; System Flow I) |
| §13 PIPE-005 Human review gates (5: plan/concept/3D/overlay/export) | PIPE-005 + interrupt()/Command(resume) (ARCH §8; ADR-02; invariant 5) |
| §14.3 Image-to-3D adapter layer, pluggable, swappable | FR-3D-001/003 + ADR-03 (ARCH §6.4/§9) |
| §14.4 3D generation metadata (10 stored fields) | FR-3D-004 + MeshCandidate entity fields (DATA_MODEL) |
| §14.5 Candidate mesh handling (accept/reject/cleanup/repair/replace) | FR-CURATE-006 + MeshCandidate state machine (DATA_MODEL) |
| §14.6 Mesh imperfection handling (orientation/scale/UVs/etc.) | REQ-F-105 game-ready geometry + FR-BLEND-001 (ADR-06 game-ready gate; Flow C) |
| §15 BLEND-001 Blender automation strategy spike (5 test assets) | PARTIAL — adopted as spike S1, but ADR-06 reframes to Python-vs-bpy (MCP excluded) — see citationProblems |
| §15 BLEND-002 Tasks to evaluate (11 ops) | FR-BLEND-001 + EVAL-004 (ARCH §6.5 Blender worker; Flow C) |
| §15 BLEND-003 Evaluation criteria (10) | EVAL-004 + RISKS (ARCH §14) |
| §15 BLEND-004 Decision rule: do NOT reject MCP prematurely | VIOLATED — ADR-06 excludes MCP as a stage executor up-front ("MCP excluded","MCP can't be a reproducible stage executor") — see citationProblems |
| §15 BLEND-005 Likely hybrid pattern (deterministic + agentic repair) | PARTIAL — ADR-06 keeps "hybrid" label + MCP as manual-rescue-only, but drops agentic repair as a pipeline stage — see notes |
| §16 ORCH-001 Graph-structured pipeline | ORCH-001 + ADR-02 LangGraph StateGraph (ARCH §6.3) |
| §16 ORCH-002 Step-level state (8 states) | ORCH-002 + 8-state run/step machine (DATA_MODEL; ARCH §6.2) |
| §16 ORCH-003 Agent/worker roles (15 listed) | ORCH-003 — LLM workers in ARCH §6.7 (Planner/StyleBible/ConceptPrompt/ArchetypeMapper/OverlayPlanner/Repair) + workers §6.5 — see notes: 6 of 15 named explicitly, others implied (StyleBibleGenerator, Texture/Swatch worker, HumanReviewGate, ProductOrchestrator) — partial enumeration |
| §16 ORCH-004 Tool call boundaries (no unstructured state writes) | ORCH-004 + invariant 10 (DATA_MODEL; ARCH §6.2 enforces tool-call boundaries) |
| §16 ORCH-005 Repair loops (5 scoped examples) | ORCH-005 + System Flow H scoped repair |
| §16 ORCH-006 User interruptions (pause/cancel/skip) | ORCH-006 + cancel via DELETE/jobs (ARCH §6.1/§11) — see notes: cancel+skip covered; explicit PAUSE not named anywhere |
| §17 MCP-001 Internal pipeline tools exposable | PARTIAL — registries/providers structured as interfaces (ARCH §6) but MCP-tool-exposure not addressed; not contradicted — see notes (MCP-001 says "should be structured so could be exposed", satisfied implicitly by clean interfaces) |
| §17 MCP-002 Blender MCP spike (test if MCP improves cleanup) | NOT DONE — ADR-06 excludes MCP without the PRD-mandated spike test; only "manual rescue tool" mention — see citationProblems |
| §17 MCP-003 Production guardrail (MCP output passes deterministic validation) | MCP-003 + invariant 10 (DATA_MODEL; ARCH §15 trust boundary d) |
| §18 OBS-001 Trace every run (15 fields) | OBS-001 + Trace entity (DATA_MODEL; ARCH §9 LangSmith) |
| §18 OBS-002 Observability platform | ADR-07 LangSmith + REQ-O-102 fail-open (ARCH §9/§12) |
| §18 OBS-003 Artifact lineage | OBS-003 + invariant 3 (DATA_MODEL; ARCH §5) |
| §18 OBS-004 User review events | OBS-004 + ReviewEvent entity |
| §18 OBS-005 Developer visibility in Advanced Panel | OBS-005 + UI-011 (Admin Flow K) |
| §19 EVAL-001 Prompt-to-Plan harness (5 test cases) | EVAL-001 (ARCH §14; ADR-08) |
| §19 EVAL-002 Concept image harness | EVAL-002 + concept bakeoff (ADR-04; ARCH §14) |
| §19 EVAL-003 Image-to-3D bakeoff harness | EVAL-003 + evaluate_comparative (ADR-03/08; ARCH §14) |
| §19 EVAL-004 Blender automation harness | EVAL-004 (ARCH §14; ADR-06) — note: now compares Python-vs-bpy not Python/MCP/hybrid |
| §19 EVAL-005 Mesh QA harness | EVAL-005 + metric component layer trimesh/Open3D (ADR-08; ARCH §14) |
| §19 EVAL-006 Sims archetype mapping harness (golden mappings) | EVAL-006 (ARCH §14) — note: golden mappings assume fixed archetypes; reconcile w/ open registry |
| §19 EVAL-007 Functional overlay harness | EVAL-007 (ARCH §14) |
| §19 EVAL-008 Export harness | EVAL-008 + DBPF round-trip (ARCH §14) |
| §19 EVAL-009 Human preference harness | EVAL-009 + annotation queues + ReviewEvent (ADR-08) |
| §20.1 Project entity | DATA_MODEL Project entity |
| §20.2 Collection Plan entity | DATA_MODEL CollectionPlan |
| §20.3 Style Bible entity | DATA_MODEL StyleBible |
| §20.4 Item Spec entity | DATA_MODEL ItemSpec |
| §20.5 Concept Candidate entity | DATA_MODEL ConceptCandidate |
| §20.6 Mesh Candidate entity | DATA_MODEL MeshCandidate |
| §20.7 Asset Variant entity | DATA_MODEL AssetVariant |
| §20.8 Functional Overlay entity | DATA_MODEL FunctionalOverlay |
| §20.9 Pipeline Run entity | DATA_MODEL PipelineRun + Step |
| §20.10 Validation Result entity | DATA_MODEL ValidationResult |
| §20.11 Export Artifact entity | DATA_MODEL ExportArtifact + ExportReport |
| §21.1 FR-PROJ-001..005 Project management | FR-PROJ-001..005 (ARCH §4,§7; Flow A/K) — FR-PROJ-005 settings (gen-mode/output-folder/advanced) covered |
| §21.2 FR-PLAN-001..006 Prompt and planning | FR-PLAN-001..006 (Flow A; ARCH §6.7) |
| §21.3 FR-CONCEPT-001..005 Concept generation | FR-CONCEPT-001..005 (Flow B; ARCH §6.4) — FR-CONCEPT-005 readiness score = silhouette-quality gate ADR-04 |
| §21.4 FR-3D-001..006 Image-to-3D | FR-3D-001..006 (Flow C; ADR-03) — FR-3D-006 failure-no-corruption = invariant 8 |
| §21.5 FR-BLEND-001..005 Blender cleanup/preview | FR-BLEND-001/003/004/005 covered; FR-BLEND-002 (spike Python/MCP/hybrid) PARTIAL — MCP dropped (ADR-06) — see citationProblems |
| §21.6 FR-CURATE-001..006 Collection curation | FR-CURATE-001..006 (Flow D) |
| §21.7 FR-FUNC-001..006 Functional overlays | FR-FUNC-001..006 (Flow E; REQ-F-102/103) |
| §21.8 FR-VAL-001..005 Validation | FR-VAL-001..005 (Flow F; §23 multi-scope) |
| §21.9 FR-EXPORT-001..006 Export | FR-EXPORT-001..006 (Flow F; REQ-F-101; REQ-O-101) |
| §21.10 FR-DEV-001..006 Advanced/developer features | FR-DEV-001..006 (Admin Flow K; UI-011) |
| §22.1 NFR Usability (creator-mode simplicity, hide advanced, progress, actionable failures) | Creator-vs-Advanced gate (ARCH §11) + structured error taxonomy (Phase8 scope inference) — note: "structured error taxonomy + actionable messages" is a scope-inference, no PRD-native NFR id |
| §22.2 NFR Reliability (item failure isolation, frequent save, scoped regen, validate-before-export, mock/real same shape) | invariants 1/4/8 + REQ-NF-102 + REQ-T-101 (DATA_MODEL; ARCH §6.2) |
| §22.3 NFR Extensibility (archetypes/overlays/models/Blender-strategies/evals addable) | REQ-F-106 open registries + ADR-03/04/06/08 adapter layers (ARCH §6.6) |
| §22.4 NFR Observability | OBS-001..005 (ARCH §9) |
| §22.5 NFR Performance (UI responsive, stage progress, cancellable, iterative concepts, no UI freeze) | PRESEARCH P6 NFR budgets (no SLO; responsive-UI/progress/cancel binding) + REQ-NF-101 (ARCH §11) |
| §22.6 NFR Local-First Project Safety (predictable location, organized artifacts, no overwrite accepted, backup-by-copy) | REQ-D-101 on-disk layout + invariant 4 + backup=copy+pg_dump (ADR-09; ARCH §7) |
| §23.1 Concept validation checks | FR-VAL-002 + Flow F (ValidationResult scope=item; §23.1) |
| §23.2 Mesh validation checks (7) | FR-VAL-002 + EVAL-005 mesh QA + ValidationResult scope=mesh |
| §23.3 Item validation checks | FR-VAL-002 + invariant 1 (DATA_MODEL) |
| §23.4 Functional overlay validation checks | FR-FUNC-004 + ValidationResult scope=overlay (Flow E) |
| §23.5 Project export validation checks (6) | FR-VAL-001/004 + invariant 1 + ValidationResult scope=export (Flow F) |
| §24.1 Export modes (full/selected/decor-only/functional/report) | FR-FUNC-006 + FR-EXPORT-* + FunctionalOverlay.exportMode (decor/functional/both) |
| §24.2 Export report (9 fields) | FR-EXPORT-004 + ExportReport entity (all 9 fields) |
| §24.3 Export completion states (5: success/warn/partial/failed/cancelled) | FR-EXPORT-005 + ExportArtifact state machine (DATA_MODEL) |
| §26.1 AC-001 create project | AC-001 (Flow A) |
| §26.1 AC-002 enter Y2K anchor prompt | AC-002 (Flow A; anchor scenario) |
| §26.1 AC-003 structured plan incl. required items | AC-003 + FR-PLAN-003 (Flow A) |
| §26.1 AC-004 edit and approve plan | AC-004 (Flow A gate 1) |
| §26.1 AC-005 generate concept images | AC-005 (Flow B) |
| §26.1 AC-006 approve/regenerate concepts | AC-006 (Flow B gate 2) |
| §26.1 AC-007 generate candidate 3D meshes | AC-007 (Flow C) |
| §26.1 AC-008 run Blender automation | AC-008 (Flow C; ADR-06) |
| §26.1 AC-009 generate preview renders | AC-009 + FR-BLEND-003 (Flow C) |
| §26.1 AC-010 review in Collection Board | AC-010 (Flow D) |
| §26.1 AC-011 regenerate one item w/o restarting project | AC-011 + ORCH-005 (System Flow H) |
| §26.1 AC-012 include/exclude items | AC-012 + FR-CURATE-004 (Flow D) |
| §26.1 AC-013 upgrade ≥1 eligible item to functional | AC-013 ELEVATED by REQ-F-102 (Flow E) |
| §26.1 AC-014 validate before export | AC-014 + FR-VAL-001 (Flow F) |
| §26.1 AC-015 export installable Sims 4 content | AC-015 ELEVATED by REQ-F-101 real-placeable (Flow F; ADR-05) |
| §26.1 AC-016 Advanced Panel shows logs/traces/artifacts | AC-016 + FR-DEV-002/003/004 (Admin Flow K) |
| §26.1 AC-017 ≥1 eval harness runs on anchor prompt | AC-017 + EVAL-001 (ARCH §14) |
| §26.1 AC-018 mock+real adapters behind stable interfaces | AC-018 + REQ-T-101 + PIPE-003 (ARCH §6.4) |
| §26.2 Vertical slice AC (CD-player path, 10 checks) | PRESEARCH P0/P1 CD-player vertical slice + ARCH §1/§16 anchor demo (covered as named slice) |
| §26.3 UI AC (6: all screens, connected, mock states, prompt-to-export, advanced optional, real-pipeline-connectable) | UI screens UI-001..011 + AC-018 + Track A mock-first (ARCH §4A/§11) — note: "mock data covers success/warning/FAILURE states" maps to PIPE-002 realistic failure states |
| §27 Coding agent guardrails (18, incl. no-single-chat, adapters, graph state, failure-states-first) | ADR-12 production-grade + ARCH §1a/§4A/§18 — note: guardrails are constraints not features; #12 "failure states before happy paths" = production posture, no explicit REQ id |
| §28 Risks and mitigations (6) | RISKS.md + ARCH §15 (R1-R7) — note: PRD §28 risks reframed/expanded in RISKS.md |
| §29 Open Questions (15) | PRESEARCH P9 OQ1-OQ11 + DECISIONS ADRs resolve most; OQ11 explicit deferral |
| §6.1 Anchor demo (Y2K set, 13 system steps incl. specific items) | Anchor scenario (ARCH §1/§16; PRESEARCH P0/P1; primary acceptance) |
| §22.5 Jobs cancellable/skippable | ORCH-006 + cancel (ARCH §6.1) — note: skip covered Flow B; pause not explicitly designed |

## UNCOVERED (PRD musts with no REQ + not explicitly out-of-scope)

- §10.3 Unsupported-generation handling (convert-to-nearest-supported WITH user confirmation, OR mark-unsupported with creator-friendly reason): appears only as a one-line PRESEARCH P1 hidden-mechanic and a passing Flow A clause; it has NO PRD-native REQ id adopted, NO module in ARCH §6, and NO DATA_MODEL invariant. Under the open-registry reframe (ADR-010 'decorative generation open for any prop') the 'convert/mark-unsupported' path is left ambiguous — what now counts as 'unsupported' for a placement type or functional archetype with no donor is undefined. This is a PRD must ('the system must either...') with no concrete home.
- §9.2 optional Computer-prop archetype: PRD lists it as an explicit (optional) functional archetype with a feasibility caveat. PRESEARCH/ADR-010 fold it into 'registry-addable' but no row/seed/spike commits to it; acceptable as optional but the architecture never states whether it is seeded or deferred — leaves it unresolved rather than explicitly out-of-scope.
- ORCH-003 worker-role completeness: PRD names 15 specific worker roles. ARCH §6.5/§6.7 explicitly names only ~8 (Collection Planner, Style Bible, Concept-Prompt, Concept-Image, 3D Router, Mesh QA, Blender Cleanup, Archetype Mapper, Overlay Planner, Export Builder, Validation, Repair). MISSING by name: Product Orchestrator (#1), Texture/Swatch Worker (#9 — partially implied by 'Swatch worker' in DATA_MODEL but not in ARCH §6.7 LLM-worker list), and the Human Review Gate as a first-class role (#15, implied by gates but not listed as a worker). Not fatal (the job engine + gates subsume them) but the explicit ORCH-003 enumeration is not fully satisfied.

## Citation problems (explicit REQs lacking a valid PRD citation / divergences)

- BLEND-001 / BLEND-004 / FR-BLEND-002 / MCP-002 mandate a 3-WAY Blender spike (deterministic Python vs MCP/agentic vs hybrid) and EXPLICITLY forbid rejecting MCP prematurely ('The product must not reject MCP-driven Blender control prematurely' §15.4; 'The team must test whether Blender MCP... improves mesh cleanup' §17.2). ADR-006 contradicts these: it states 'MCP excluded' and 'MCP can't be a reproducible stage executor', demoting MCP to a manual-rescue-only tool WITHOUT running the PRD-mandated comparative spike. The architecture cites BLEND-001/EVAL-004 as covered but the spike scope has silently narrowed to Python-vs-bpy. This is a real divergence from an explicit PRD requirement that should be surfaced to the human as a scope change, not buried in an ADR.
- PRESEARCH §Phase6 claims 'every in-scope requirement maps to a flow' (USER_FLOWS coverage table) and 'arch-finalize will persist the full PRD→REQ coverage table' — but neither PRESEARCH nor ARCHITECTURE_DRAFT actually contains a per-ID PRD→REQ coverage table; coverage is asserted at the category level (FR-PROJ, FR-PLAN, ...) only. Several PRD-native IDs (e.g. §10.3 unsupported-handling, the optional computer-prop archetype) thus have an ASSERTED-but-unverified citation. The finalize step (this audit) is where those gaps surface; until ARCHITECTURE.md carries the explicit table, the 'fully covered' claim in PRESEARCH P6 / USER_FLOWS is overstated.
- EVAL-006 (Sims archetype mapping harness) cites fixed 'golden mappings' (CD player→electronics prop; lava lamp→light-like; etc.) but ADR-010 replaces fixed archetypes with open registries. The harness's golden-mapping pass criteria (§19.6) and EVAL-006's citation are not reconciled with the registry reframe — the architecture adopts EVAL-006 verbatim while changing the model it evaluates, leaving the eval's reference set undefined.