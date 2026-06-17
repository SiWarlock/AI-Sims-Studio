# AI Sims Creator - Product Requirements Document (PRD) v2

**Document date:** June 16, 2026  
**Document type:** Product Requirements Document  
**Status:** Draft v2 for product review and implementation planning  
**Primary audience:** Product owner, coding agent, engineering agent, UI implementer, pipeline implementer, technical maintainer  
**Project codename:** AI Sims Creator

---

## 1. Executive Summary

AI Sims Creator is a desktop AI studio for creating Sims 4 Build/Buy custom content collections. The MVP must let a non-technical or semi-technical Sims creator describe a collection in natural language, generate a coherent set of supported 3D object assets, review concept images and 3D previews, refine or regenerate individual items, optionally convert selected supported items into simple functional objects, validate the project, and export installable Sims 4 content.

The core MVP journey is:

1. User creates a project.
2. User enters a collection prompt.
3. The system creates a structured collection plan.
4. The system generates concept images for each item.
5. Approved concepts are converted into candidate 3D meshes through pluggable image-to-3D model adapters.
6. Candidate meshes are cleaned, normalized, preview-rendered, and validated through a Blender automation layer.
7. Assets are mapped to supported Sims 4 Build/Buy object archetypes.
8. Selected eligible assets can receive functional overlays.
9. The project is validated.
10. The system exports installable Sims 4 content.

The MVP includes both the full creator-facing app UI and the backend generation pipeline. The UI may be developed in parallel against mocked pipeline interfaces, but the product MVP is not complete until at least one real vertical slice works end to end.

The product must not be implemented as a generic chatbot or a fully unconstrained AI agent. It must be a structured, observable, graph-orchestrated creation system with clear product states, repeatable jobs, model/tool adapters, validation gates, human review gates, and eval harnesses.

---

## 2. Product Definition

### 2.1 One-Sentence Product Definition

AI Sims Creator is a desktop application that allows a Sims creator to prompt, generate, curate, functionally enhance, validate, and export Sims 4 Build/Buy custom content collections using AI-assisted asset generation and Sims-specific build pipelines.

### 2.2 Product Category

AI-assisted Sims 4 custom content creation studio.

### 2.3 Product Form Factor

The MVP should be a desktop-first application with local project storage and a local or locally-controlled pipeline runner.

A web UI may be used for development or prototyping if it accelerates iteration, but the product should be designed around desktop creator workflows because the application must interact with local assets, local 3D tooling, local previews, local project files, and eventually a Sims 4 test installation or Mods folder.

### 2.4 Primary Product Promise

A creator should be able to type a collection idea such as:

> Create a Y2K bedroom clutter collection with a CD player, lava lamp, old translucent laptop, funky mirror, chrome picture frames, stickered magazines, makeup clutter, and translucent plastic storage.

The product should transform that prompt into a reviewable, generated, Sims-ready Build/Buy collection within supported archetypes.

### 2.5 MVP Positioning

The MVP is not a planning assistant. It must generate real supported assets and move them toward playable in-game output.

The MVP is also not an unrestricted mod generator. It should support constrained Build/Buy object categories and a small number of functional archetypes.

---

## 3. Product Goals

### 3.1 Primary Goals

1. Let a non-technical Sims expert create custom content through a guided creative workflow.
2. Generate themed Build/Buy object collections from natural language prompts.
3. Use concept images as the bridge between text prompts and 3D generation.
4. Convert concept images into candidate 3D meshes using pluggable image-to-3D models.
5. Normalize, clean, preview, and validate generated 3D assets through Blender automation.
6. Allow per-item review, regeneration, and curation.
7. Allow selected eligible generated assets to become simple functional objects.
8. Export installable Sims 4 custom content for supported categories.
9. Provide observability, traces, logs, and eval harnesses so the pipeline can be improved over time.
10. Let the UI and pipeline be built in parallel through stable contracts and mock adapters.

### 3.2 Secondary Goals

1. Support future expansion into additional object archetypes.
2. Support future deeper functional gameplay objects.
3. Support future CAS-related pipelines, but not in MVP.
4. Support future animation experimentation, but not as an MVP requirement.
5. Support a technical maintainer with logs, traces, artifact paths, and rerun controls.

---

## 4. Non-Goals

The MVP must not attempt to support everything. The following are out of scope for MVP:

1. Full CAS clothing, hair, makeup, or accessories.
2. Fully custom Sim animation generation.
3. Arbitrary gameplay mod generation.
4. Complex script-heavy game systems.
5. Full autonomous publishing workflows.
6. Marketplace-style storefront features.
7. Collaboration, team roles, or multi-user review.
8. Guaranteed generation of any object from any prompt.
9. Fully autonomous Blender editing with no validation or review.
10. Replacing all manual creator judgment.

The MVP must stay focused on prompt-driven Build/Buy collection generation with limited functional upgrades.

---

## 5. Target Users

### 5.1 Primary User: Sims Creator

The primary user is a Sims 4 expert who has strong creative direction and understands the kind of content she wants in the game, but does not want to manually operate a complex modding, package, Blender, or tuning toolchain.

Characteristics:

- Understands Sims 4 aesthetics, gameplay, Build/Buy categories, and creator culture.
- Can describe desired collections and objects clearly.
- Wants to create content quickly and iteratively.
- May understand Sims terms but should not need to understand package internals.
- Needs visual review, regeneration, and refinement controls.

### 5.2 Secondary User: Technical Maintainer

The secondary user is the person building, maintaining, and debugging the tool.

Characteristics:

- Comfortable with coding agents, logs, traces, pipelines, and model adapters.
- Needs access to developer panels, pipeline run details, artifact paths, job retries, eval results, and configuration.
- Can run spike tests, switch providers, and inspect pipeline failures.

### 5.3 Coding Agent as an Implementation User

A coding agent will use this PRD to build the product. Therefore, this document includes explicit requirements, feature boundaries, statuses, acceptance criteria, and implementation guardrails.

The coding agent should treat this PRD as the product behavior contract. The future Technical Architecture Document may refine exact technologies, schemas, and service boundaries.

---

## 6. Core MVP Scenario

### 6.1 Anchor Demo

The MVP must be built around the following anchor scenario:

A user opens the app and creates a new project:

> Y2K Bedroom Clutter Set. Include a CD player, lava lamp, retro translucent laptop, funky mirror, stickered magazines, makeup clutter, chrome photo frame, and translucent acrylic organizer. Use hot pink, silver chrome, lime accents, glossy plastic, and playful teen bedroom energy.

The system must:

1. Generate a structured collection plan.
2. Include the required items.
3. Mark supported functional candidates.
4. Generate concept images for each item.
5. Let the user approve or regenerate concepts.
6. Generate candidate 3D assets from approved concepts.
7. Clean and normalize generated assets.
8. Render item previews.
9. Show the collection in a visual board.
10. Let the user refine, regenerate, include, or exclude individual items.
11. Let the user make the CD player functional as an audio-style object, or make the lava lamp functional as a light-style object, or make the mirror functional as a mirror-style object.
12. Validate the project.
13. Export installable Sims 4 content.

### 6.2 MVP Success Statement

The MVP succeeds when this anchor scenario works end to end for at least one full collection and at least one functional upgrade.

---

## 7. Product Principles

1. **Generate real assets, not just plans.** The product must produce actual candidate 3D objects and exportable content.
2. **Use AI in bounded stages.** AI should plan, generate, evaluate, and repair within controlled interfaces.
3. **Prefer graph orchestration over uncontrolled agents.** The system should be stateful, inspectable, and resumable.
4. **Review before expensive stages.** The user should be able to approve concept images before mesh generation.
5. **One asset, multiple outputs.** A decor asset and functional asset should share a common identity.
6. **MVP supports constrained archetypes.** Do not imply universal content generation.
7. **UI and pipeline should be decoupled.** The app UI can be built with mocked pipeline data, then connected to real adapters.
8. **Observe everything.** Every major generation, validation, and export step should be traceable.
9. **Evaluate continuously.** The product should include harnesses for agent, image, mesh, Blender, functional, and export quality.
10. **Make the creator experience simple.** Hide technical complexity unless advanced mode is enabled.

---

## 8. MVP Scope Summary

### 8.1 Must-Have MVP Features

1. Desktop project system.
2. New collection wizard.
3. Prompt-to-collection planning.
4. Collection plan review and editing.
5. Concept image generation and review.
6. Image-to-3D model adapter layer.
7. Candidate mesh generation.
8. Blender automation strategy with spike support for deterministic Python, MCP-driven Blender control, and hybrid workflows.
9. Mesh QA and preview rendering.
10. Collection board.
11. Item detail screen.
12. Per-item regeneration and curation.
13. Supported functional overlay wizard.
14. Validation center.
15. Export center.
16. Advanced developer panel.
17. Observability for generation runs.
18. Eval harnesses.
19. Mock pipeline adapters so UI can be built in parallel.

### 8.2 Should-Have MVP Features

1. Multiple concept candidates per item.
2. Multiple mesh candidates per item where supported.
3. Collection-level style lock.
4. Test install to a configured local target folder.
5. Human preference capture on approve/reject decisions.
6. Basic rebuild from saved project state.
7. Export report with included items, warnings, and artifacts.

### 8.3 Nice-to-Have / Post-MVP Features

1. Richer functional behaviors.
2. More object archetypes.
3. CAS asset generation.
4. Animation spike.
5. Script mod generation.
6. Automated in-game smoke testing.
7. Template marketplace or asset library.
8. Team/project collaboration.

---

## 9. Supported MVP Content Types

### 9.1 Decorative Build/Buy Object Categories

The MVP must focus on supported Build/Buy decorative categories.

Required supported categories:

1. Small clutter object.
2. Tabletop decor.
3. Shelf decor.
4. Simple electronics prop.
5. Simple light-like decor object.
6. Simple mirror-like decor object.
7. Small wall or standing decor object.

### 9.2 Functional Archetypes

The MVP must support a limited set of functional overlays. These are not arbitrary gameplay mods. They are constrained upgrade patterns for selected eligible assets.

Required MVP functional archetypes:

1. **Audio device archetype**
   - Example: generated CD player.
   - Basic product behavior: object becomes an audio-style interactive object.

2. **Light / on-off archetype**
   - Example: generated lava lamp.
   - Basic product behavior: object has an on/off or active/inactive state and visual light-style behavior if supported by the implementation.

3. **Mirror archetype**
   - Example: generated funky mirror.
   - Basic product behavior: object maps to a mirror-like interaction pattern where feasible.

4. **Moodlet / vibe emitter archetype**
   - Example: cute clutter item that gives an environment or emotional vibe.
   - Basic product behavior: item receives a simple supported effect overlay.

Optional MVP functional archetype:

5. **Computer-like prop archetype**
   - Example: retro translucent laptop.
   - This should remain optional unless the pipeline proves it can support it without destabilizing MVP scope.

---

## 10. Definition of Playable In-Game

For MVP, "playable in-game" means the generated output is intended to be installed into The Sims 4 and used through supported Build/Buy behavior.

### 10.1 Decorative Playable Asset

A decorative playable asset must:

1. Have an exportable asset artifact.
2. Have Sims-facing metadata.
3. Belong to a supported object category.
4. Have at least one visual preview.
5. Be included in package/export output.
6. Be intended to appear as a placeable Build/Buy asset after installation.

### 10.2 Functional Playable Asset

A functional playable asset must:

1. Satisfy decorative asset requirements.
2. Have a valid functional overlay schema.
3. Belong to a supported functional archetype.
4. Pass compatibility checks between source asset and functional overlay.
5. Export as either a functional variant or a paired decor/functional output.
6. Present behavior matching the selected functional archetype at a basic usable level.

### 10.3 Unsupported Generation

If a user asks for unsupported content, the system must either:

1. Convert the request into the nearest supported decorative archetype, with user confirmation; or
2. Mark the item as unsupported for MVP and explain why in creator-friendly language.

---

## 11. End-to-End User Workflow

### 11.1 Workflow A: Create a New Collection

1. User opens the app.
2. User clicks **New Project**.
3. User enters project name.
4. User enters collection prompt.
5. User optionally lists required items.
6. User optionally enters style notes.
7. User selects desired item count.
8. User submits the prompt.
9. System generates a collection plan.
10. User reviews, edits, and approves the plan.

### 11.2 Workflow B: Generate Concepts

1. System generates concept image prompts for each approved item spec.
2. System generates one or more concept images per item.
3. User reviews concept candidates.
4. User approves a candidate, regenerates candidates, edits the item prompt, or skips an item.
5. Approved concepts become inputs to image-to-3D generation.

### 11.3 Workflow C: Generate 3D Assets

1. Approved concept is passed to one or more image-to-3D model adapters.
2. System stores generated candidate mesh artifacts.
3. System runs initial mesh QA.
4. System sends passing candidates to Blender automation.
5. Blender automation normalizes, cleans, and renders previews.
6. System shows generated 3D preview in the item detail screen.
7. User accepts, regenerates, or reruns cleanup.

### 11.4 Workflow D: Curate the Collection

1. User views all generated items in Collection Board.
2. User opens any item to review details.
3. User edits metadata.
4. User chooses swatches or variants.
5. User includes or excludes items from export.
6. User marks eligible items for functional upgrade.

### 11.5 Workflow E: Make an Item Functional

1. User selects an eligible generated item.
2. User clicks **Make Functional**.
3. System shows supported functional archetypes for that item.
4. User chooses an archetype.
5. User configures simple behavior options.
6. System generates a functional overlay.
7. System validates the overlay against the source asset.
8. User chooses export mode: decor-only, functional-only, or both.

### 11.6 Workflow F: Validate and Export

1. User opens Validation Center.
2. System runs project validation.
3. System shows blockers, warnings, and passing checks.
4. User fixes, regenerates, excludes, or proceeds as allowed.
5. User opens Export Center.
6. User reviews export summary.
7. User starts export.
8. System builds output artifacts.
9. System shows success, partial success, or failure.
10. System stores export report and logs.

---

## 12. Application UI Requirements

The MVP includes the full app UI. The UI may initially use mocked data, but screens and flows should be implemented against stable pipeline-facing contracts.

### 12.1 UI-001: Project Dashboard

Purpose: Manage projects.

Required capabilities:

1. Create new project.
2. Open existing project.
3. Show recent projects.
4. Show project name, last modified date, and status.
5. Show whether a project has generated assets or export artifacts.
6. Provide access to settings and advanced mode.

### 12.2 UI-002: New Collection Wizard

Purpose: Capture creative intent.

Required fields:

1. Project name.
2. Collection prompt.
3. Required item list.
4. Desired item count.
5. Optional style notes.
6. Optional output mode:
   - Decorative collection.
   - Functional-enabled collection.
   - Mixed collection.
7. Optional generation mode:
   - Fast draft.
   - Balanced.
   - Quality.

Required behavior:

1. Validate required fields.
2. Allow user to proceed to plan generation.
3. Save prompt and settings in project state.

### 12.3 UI-003: Collection Plan Review

Purpose: Let the user approve and edit what will be generated.

Required display per item:

1. Item name.
2. Item description.
3. Object archetype.
4. Functional eligibility.
5. Placement category.
6. Style/material notes.
7. Status.

Required actions:

1. Add item.
2. Remove item.
3. Rename item.
4. Edit item description.
5. Change or confirm archetype.
6. Lock required item.
7. Approve plan.
8. Regenerate plan.

### 12.4 UI-004: Generation Workspace

Purpose: Show the full generation pipeline status.

Required sections:

1. Collection-level progress.
2. Item-level progress.
3. Pipeline stage statuses.
4. Current active job.
5. Queue of pending jobs.
6. Warnings and failures.
7. Retry controls.

Required statuses:

1. Planned.
2. Concept pending.
3. Concept generating.
4. Concept review needed.
5. Mesh pending.
6. Mesh generating.
7. Mesh QA pending.
8. Blender cleanup pending.
9. Preview ready.
10. Needs review.
11. Export ready.
12. Failed.
13. Excluded.

### 12.5 UI-005: Concept Review Screen

Purpose: Review concept images before 3D generation.

Required display:

1. Item spec summary.
2. Concept candidates.
3. Concept prompt.
4. Quality/readiness score if available.
5. User notes.

Required actions:

1. Approve concept.
2. Regenerate concept.
3. Edit concept prompt.
4. Select preferred candidate.
5. Reject candidate with reason.
6. Skip item.

### 12.6 UI-006: Collection Board

Purpose: Main visual board for the generated collection.

Required display:

1. Item grid.
2. Preview thumbnail.
3. Item name.
4. Category/archetype.
5. Status.
6. Functional eligibility badge.
7. Warning/error badge.
8. Include/exclude toggle.

Required actions:

1. Open item detail.
2. Regenerate item.
3. Rerun cleanup.
4. Include/exclude from export.
5. Make functional if eligible.
6. Add new item.
7. Filter by status.

### 12.7 UI-007: Item Detail Screen

Purpose: Inspect and refine a single item.

Required display:

1. 3D preview render.
2. Concept image.
3. Item spec.
4. Mesh candidate status.
5. Swatches or variants.
6. Metadata fields.
7. Functional eligibility.
8. Validation results for this item.
9. Generation history.

Required editable fields:

1. Display name.
2. Description.
3. Tags.
4. Price suggestion.
5. User notes.
6. Swatch labels if supported.

Required actions:

1. Regenerate concept.
2. Regenerate mesh.
3. Rerun Blender cleanup.
4. Select candidate variant.
5. Edit metadata.
6. Make functional.
7. Include/exclude from export.

### 12.8 UI-008: Functional Upgrade Wizard

Purpose: Upgrade supported assets into functional objects.

Required steps:

1. Show selected source asset.
2. Show eligible functional archetypes.
3. Let user choose one archetype.
4. Show simple behavior configuration options.
5. Generate functional overlay.
6. Show functional behavior summary.
7. Validate compatibility.
8. Confirm export mode.

Required output:

1. Functional overlay record.
2. Updated item status.
3. Validation state.
4. Export mode setting.

### 12.9 UI-009: Validation Center

Purpose: Show export readiness.

Required display:

1. Project-level validation status.
2. Item-level validation status.
3. Blocking errors.
4. Warnings.
5. Informational notes.
6. Recommended repair or retry actions.

Required actions:

1. Run validation.
2. Retry failed step.
3. Exclude item.
4. Open item detail.
5. Proceed to export if no blockers.

### 12.10 UI-010: Export Center

Purpose: Build final output.

Required display:

1. Export summary.
2. Included items.
3. Functional items.
4. Warnings.
5. Output path.
6. Build status.
7. Export artifact list.

Required actions:

1. Choose output path.
2. Build export.
3. Open output folder.
4. View export report.
5. Optional test install to configured folder.

### 12.11 UI-011: Advanced / Developer Panel

Purpose: Debug and improve the pipeline.

Required display:

1. Pipeline graph runs.
2. Trace IDs.
3. Job history.
4. Tool/model calls.
5. Artifact paths.
6. Validation logs.
7. Eval results.
8. Adapter configuration.

Required actions:

1. Rerun step.
2. Rerun full pipeline.
3. Export logs.
4. Open artifact path.
5. Switch mock/real adapter if configured.
6. View raw project state.

---

## 13. Pipeline Product Requirements

### 13.1 PIPE-001: Stable Pipeline Interface

The UI must communicate with the generation pipeline through stable contracts. This allows UI development to proceed against mock implementations while real pipeline workers are developed in parallel.

Minimum pipeline operations:

1. Create project.
2. Generate collection plan.
3. Generate concept candidates.
4. Approve concept.
5. Generate mesh candidates.
6. Run mesh QA.
7. Run Blender cleanup.
8. Generate preview render.
9. Generate swatches or variants.
10. Attach functional overlay.
11. Run validation.
12. Build export.
13. Fetch logs/traces.

### 13.2 PIPE-002: Mock Adapter Requirement

Every major pipeline operation must support a mock adapter for UI development and automated testing.

Mock adapters must produce realistic statuses, artifacts, warnings, and failure states.

### 13.3 PIPE-003: Real Adapter Requirement

Each mock adapter should have a corresponding real adapter or planned real adapter.

The application must not hard-code fake-only behavior into core product state.

### 13.4 PIPE-004: Resumable Jobs

Long-running jobs must be represented as resumable pipeline runs with step-level state.

A project should not lose all progress if one item fails.

### 13.5 PIPE-005: Human Review Gates

The pipeline must support human approval gates, especially:

1. Collection plan approval.
2. Concept image approval.
3. 3D asset candidate approval.
4. Functional overlay approval.
5. Export approval.

---

## 14. 3D Asset Generation Strategy

### 14.1 Strategic Direction

The primary MVP strategy for 3D object generation is:

**Prompt -> structured item spec -> concept image -> image-to-3D mesh candidate -> Blender cleanup -> preview render -> Sims archetype mapping -> validation -> export.**

This is a core PRD requirement.

The product should not attempt to directly generate final Sims-ready assets from text alone.

### 14.2 Why Concept Images Are Required

Concept images provide:

1. Better user review before expensive 3D generation.
2. More controllable inputs for image-to-3D models.
3. A visible creative checkpoint.
4. Better artifact history and human preference data.
5. A fallback asset for documentation, thumbnails, or regeneration.

### 14.3 Image-to-3D Model Adapter Layer

The system must support a pluggable image-to-3D adapter layer.

The PRD does not mandate one model. The model landscape is moving quickly, and the product must be able to evaluate and swap models.

Candidate models/tools for spike testing may include:

1. Stable Fast 3D / SF3D.
2. SPAR3D.
3. TripoSR.
4. TripoSG.
5. TRELLIS or TRELLIS.2.
6. Hunyuan3D 2.x.
7. Other emerging image-to-3D tools.

### 14.4 3D Generation Requirements

For each mesh generation attempt, the system must store:

1. Source item spec.
2. Source concept image.
3. Model adapter name.
4. Adapter configuration.
5. Generated mesh artifact path.
6. Generated texture/material artifact paths where available.
7. Runtime status.
8. Error information if failed.
9. Mesh QA score or result.
10. Preview render path if produced.

### 14.5 Candidate Mesh Handling

The system should support multiple mesh candidates per item.

A mesh candidate may be:

1. Accepted.
2. Rejected by system QA.
3. Rejected by user.
4. Sent for cleanup.
5. Sent for repair.
6. Replaced by regenerated output.

### 14.6 Mesh Output Expectations

The MVP should expect generated meshes to be imperfect. The system must treat generated meshes as candidates requiring cleanup and validation, not final production assets.

The pipeline must assume that generated meshes may have:

1. Incorrect orientation.
2. Incorrect scale.
3. High polygon count.
4. Bad or missing UVs.
5. Broken material links.
6. Geometry artifacts.
7. Poor backside details.
8. Non-game-ready topology.
9. Bad object origin/pivot.
10. Visual mismatch with intended item.

---

## 15. Blender Automation and MCP Spike Requirements

### 15.1 Strategic Direction

The product must include a Blender automation layer, but the implementation strategy is not predetermined.

The team must spike-test:

1. Deterministic Blender Python scripts.
2. Blender MCP / agent-driven Blender control.
3. Hybrid workflows that combine deterministic scripts with agentic cleanup or repair.
4. Manual fallback hooks for difficult cases if needed.

### 15.2 BLEND-001: Blender Automation Strategy Spike

The MVP planning phase must include a spike comparing Blender automation approaches on the same asset set.

Required spike test assets:

1. Y2K CD player.
2. Lava lamp.
3. Funky mirror.
4. Retro translucent laptop/computer prop.
5. Simple clutter item.

### 15.3 BLEND-002: Tasks to Evaluate

Each Blender strategy must be evaluated against these tasks:

1. Import generated mesh.
2. Inspect mesh dimensions.
3. Fix orientation.
4. Normalize scale.
5. Set origin/pivot.
6. Apply transforms.
7. Preserve or repair materials.
8. Reduce excessive geometry where feasible.
9. Generate preview render.
10. Export normalized intermediate file.
11. Report failure in a structured way.

### 15.4 BLEND-003: Evaluation Criteria

Each approach must be evaluated on:

1. Reliability.
2. Visual quality improvement.
3. Repeatability.
4. Debuggability.
5. Speed.
6. Cost.
7. Recoverability.
8. Ease of integration.
9. Effect on user-facing previews.
10. Suitability for batch collection generation.

### 15.5 BLEND-004: Decision Rule

The product must not reject MCP-driven Blender control prematurely.

If Blender MCP or another agentic Blender approach outperforms deterministic Python for cleanup, repair, or creative mesh fixes, the implementation should support it.

If deterministic Python outperforms agentic control for repeatability, it should be used for those tasks.

A hybrid strategy is explicitly allowed and likely preferred.

### 15.6 BLEND-005: Likely Hybrid Pattern

A likely hybrid pattern is:

1. Deterministic script imports asset, sets scene, normalizes scale, applies transforms, renders preview, and exports.
2. Agentic Blender tool handles judgment-heavy repair or creative cleanup when deterministic scripts fail.
3. Deterministic validator checks final output.
4. Repair loop retries only the failed stage.

The final TAD should choose the concrete implementation after spike results.

---

## 16. Agentic Orchestration Requirements

### 16.1 Orchestration Strategy

The product should use a graph-based orchestration framework or equivalent. LangGraph is a strong candidate, but the PRD does not mandate a final framework.

The required capability is not specifically "LangGraph"; the required capability is:

1. Stateful multi-step workflows.
2. Conditional routing.
3. Human review gates.
4. Retry and repair loops.
5. Durable run state.
6. Step-level observability.
7. Tool/model adapter calls.
8. Ability to run mocked and real steps.

### 16.2 ORCH-001: Graph-Structured Pipeline

The pipeline must be represented as a graph or graph-equivalent workflow, not as one opaque blocking process.

### 16.3 ORCH-002: Step-Level State

Each stage must produce step-level state, including:

1. Pending.
2. Running.
3. Succeeded.
4. Failed.
5. Skipped.
6. Waiting for user.
7. Retrying.
8. Cancelled.

### 16.4 ORCH-003: Agent/Worker Roles

The system should define specialized agents/workers rather than one general agent doing everything.

Required or planned worker roles:

1. Product Orchestrator.
2. Collection Planner.
3. Style Bible Generator.
4. Concept Prompt Generator.
5. Concept Image Generator.
6. 3D Model Router.
7. Mesh QA Worker.
8. Blender Cleanup Worker.
9. Texture/Swatch Worker.
10. Sims Archetype Mapper.
11. Functional Overlay Planner.
12. Package/Export Builder.
13. Validation Worker.
14. Repair Agent.
15. Human Review Gate.

### 16.5 ORCH-004: Tool Call Boundaries

Agents must call tools through explicit interfaces.

Agents must not write unstructured project state directly without validation.

### 16.6 ORCH-005: Repair Loops

The system must support targeted repair loops.

Examples:

1. Regenerate only concept for one item.
2. Regenerate only mesh for one item.
3. Rerun Blender cleanup for one item.
4. Retry functional overlay generation.
5. Exclude one failed item and continue export.

### 16.7 ORCH-006: User Interruptions

The user must be able to pause, cancel, or skip long-running item generation where feasible.

---

## 17. MCP Strategy Requirements

### 17.1 MCP Role

MCP should be considered an integration strategy for agents and tools, especially for development and optional advanced automation.

The product may expose its own pipeline tools through MCP-like interfaces or use existing MCP servers where useful.

### 17.2 MCP-001: Internal Pipeline Tools

The product should be structured so internal pipeline capabilities could be exposed as tools, such as:

1. Create collection plan.
2. Generate concept image.
3. Run image-to-3D model.
4. Score mesh candidate.
5. Normalize mesh in Blender.
6. Generate swatches.
7. Attach functional overlay.
8. Run validation.
9. Build export.
10. Install test build.

### 17.3 MCP-002: Blender MCP Spike

The team must test whether Blender MCP or equivalent agentic Blender control improves mesh cleanup, repair, or creative editing.

### 17.4 MCP-003: Production Guardrail

MCP-driven actions must still pass deterministic validation before being accepted into the project state.

---

## 18. Observability Requirements

Observability is an MVP requirement because the product combines LLMs, image generation, 3D generation, Blender automation, validation, and export.

### 18.1 OBS-001: Trace Every Pipeline Run

Every pipeline run must create a trace or trace-equivalent record.

Required trace fields:

1. Project ID.
2. Item ID if item-specific.
3. User prompt.
4. Collection plan version.
5. Item spec version.
6. Agent/worker name.
7. Model/tool used.
8. Tool inputs.
9. Tool outputs or artifact references.
10. Start/end time.
11. Status.
12. Error details.
13. Cost/latency where available.
14. Validation results.
15. User approval/rejection events.

### 18.2 OBS-002: Observability Platform

The system should integrate with an observability platform suitable for AI workflows.

Candidate platforms include:

1. Langfuse.
2. Arize Phoenix.
3. LangSmith.
4. OpenAI Agents SDK tracing if that stack is used.
5. Custom OpenTelemetry-compatible tracing if preferred.

The PRD does not mandate the final observability tool, but it does mandate traceability.

### 18.3 OBS-003: Artifact Lineage

Every generated artifact must be traceable to its upstream inputs.

Examples:

1. Mesh generated from concept image.
2. Concept image generated from item prompt.
3. Item prompt generated from collection plan.
4. Functional overlay generated from source asset and user configuration.
5. Export artifact generated from selected item versions.

### 18.4 OBS-004: User Review Events

User approvals, rejections, regeneration choices, and notes must be captured as product data.

These events are valuable for quality improvement and future personalization.

### 18.5 OBS-005: Developer Visibility

The Advanced Panel must expose key observability data without requiring manual database inspection.

---

## 19. Evals and Test Harness Requirements

The MVP must include evaluation harnesses from the start. These harnesses are necessary because the pipeline will be multimodal, probabilistic, and agentic.

### 19.1 EVAL-001: Prompt-to-Plan Harness

Purpose: Verify that collection prompts become valid structured plans.

Required test cases:

1. Y2K bedroom clutter collection.
2. Coquette vanity clutter collection.
3. Witchy apothecary shelf clutter collection.
4. Retro diner decor collection.
5. Space-age plastic bedroom decor collection.

Pass criteria:

1. Output matches schema.
2. Required user items are included.
3. Unsupported items are flagged.
4. Object archetypes are assigned.
5. Functional candidates are correctly marked.
6. Style bible is coherent.

### 19.2 EVAL-002: Concept Image Harness

Purpose: Verify that concept images are suitable for image-to-3D conversion.

Pass criteria:

1. Object is isolated.
2. Silhouette is clear.
3. Background is minimal.
4. Perspective is usable.
5. Item matches spec.
6. Style matches collection.
7. Image is not too cluttered for 3D reconstruction.

### 19.3 EVAL-003: Image-to-3D Model Bakeoff Harness

Purpose: Compare candidate image-to-3D models.

For each test asset and model, record:

1. Model name.
2. Input concept image.
3. Generation time.
4. Hardware or provider used.
5. Output file type.
6. Vertex count.
7. Face count.
8. Texture/UV presence.
9. Material presence.
10. Blender import success.
11. Preview render success.
12. Mesh QA score.
13. Human quality score.
14. Sims-readiness score.

### 19.4 EVAL-004: Blender Automation Harness

Purpose: Compare deterministic Python, MCP agentic control, and hybrid cleanup.

Pass criteria:

1. Import succeeds.
2. Orientation corrected.
3. Scale normalized.
4. Origin/pivot set.
5. Materials preserved or repaired.
6. Preview render generated.
7. Exported intermediate file created.
8. Failures are structured and understandable.

### 19.5 EVAL-005: Mesh QA Harness

Purpose: Reject obviously unusable assets.

Checks:

1. Mesh imports.
2. Mesh has nonzero dimensions.
3. Bounding box is plausible.
4. Face count is within archetype budget or flagged.
5. No extreme spikes detected.
6. Normals are valid or repairable.
7. Materials/textures exist or are flagged.
8. Preview render completes.

### 19.6 EVAL-006: Sims Archetype Mapping Harness

Purpose: Verify generated objects map to supported archetypes.

Golden mappings:

1. CD player -> small electronics prop; functional candidate: audio.
2. Lava lamp -> light-like decor; functional candidate: light.
3. Funky mirror -> mirror-like decor; functional candidate: mirror.
4. Magazine stack -> small clutter; no functional candidate.
5. Acrylic organizer -> tabletop decor; possible moodlet/vibe candidate only.

### 19.7 EVAL-007: Functional Overlay Harness

Purpose: Verify the functional overlay pipeline.

Golden cases:

1. CD player -> audio device overlay.
2. Lava lamp -> light/on-off overlay.
3. Funky mirror -> mirror overlay.
4. Cute decor -> moodlet/vibe overlay.

Pass criteria:

1. Overlay schema valid.
2. Source asset compatible.
3. User behavior choices saved.
4. Functional summary generated.
5. Validation passes or returns actionable blockers.

### 19.8 EVAL-008: Export Harness

Purpose: Verify final output generation.

Pass criteria:

1. Export folder created.
2. Export artifact exists.
3. Export report exists.
4. Included item count matches user selection.
5. Functional items are listed.
6. Warnings are preserved.
7. Build is reproducible from saved state where feasible.

### 19.9 EVAL-009: Human Preference Harness

Purpose: Capture domain-expert review decisions.

For each approval/rejection, store:

1. Project ID.
2. Item ID.
3. Candidate ID.
4. Artifact type.
5. User decision.
6. Rejection reason if rejected.
7. User notes.
8. Timestamp.

---

## 20. Product Data Model Requirements

This section defines product-level entities. Exact schemas belong in the TAD, but implementation should preserve these concepts.

### 20.1 Project

Represents a user-created content project.

Minimum fields:

1. Project ID.
2. Name.
3. Prompt.
4. Style notes.
5. Desired item count.
6. Current status.
7. Created/updated timestamps.
8. Collection plan reference.
9. Export settings.
10. Pipeline run references.

### 20.2 Collection Plan

Represents the structured plan generated from the prompt.

Minimum fields:

1. Plan ID.
2. Project ID.
3. Style bible.
4. Item specs.
5. Version.
6. Approval status.

### 20.3 Style Bible

Represents collection-level style consistency.

Minimum fields:

1. Theme summary.
2. Color palette.
3. Materials.
4. Shape language.
5. Era references.
6. Thumbnail/render style.
7. Negative style constraints.

### 20.4 Item Spec

Represents a planned object.

Minimum fields:

1. Item ID.
2. Display name.
3. Description.
4. Required/optional flag.
5. Object archetype.
6. Placement category.
7. Functional eligibility.
8. Concept prompt.
9. Mesh generation prompt/context.
10. Swatch plan.
11. Status.

### 20.5 Concept Candidate

Represents a generated concept image.

Minimum fields:

1. Candidate ID.
2. Item ID.
3. Prompt.
4. Image artifact path.
5. Model/provider.
6. Status.
7. User decision.
8. Readiness score if available.

### 20.6 Mesh Candidate

Represents a generated 3D asset candidate.

Minimum fields:

1. Candidate ID.
2. Item ID.
3. Source concept ID.
4. Model adapter.
5. Mesh artifact path.
6. Texture/material artifact paths.
7. QA status.
8. Cleanup status.
9. Preview render path.
10. User decision.

### 20.7 Asset Variant

Represents an accepted or reviewable item variant.

Minimum fields:

1. Variant ID.
2. Item ID.
3. Concept candidate reference.
4. Mesh candidate reference.
5. Swatch references.
6. Preview references.
7. Export readiness.

### 20.8 Functional Overlay

Represents optional behavior layered onto an asset.

Minimum fields:

1. Overlay ID.
2. Source item ID.
3. Source variant ID.
4. Functional archetype.
5. User configuration.
6. Behavior summary.
7. Validation status.
8. Export mode.

### 20.9 Pipeline Run

Represents a graph/workflow run.

Minimum fields:

1. Run ID.
2. Project ID.
3. Item ID if applicable.
4. Run type.
5. Status.
6. Steps.
7. Trace reference.
8. Start/end time.

### 20.10 Validation Result

Represents validation output.

Minimum fields:

1. Result ID.
2. Scope: project, item, mesh, overlay, export.
3. Severity: error, warning, info, pass.
4. Message.
5. Suggested action.
6. Related artifact or item.

### 20.11 Export Artifact

Represents final generated output.

Minimum fields:

1. Export ID.
2. Project ID.
3. Output path.
4. Included items.
5. Functional overlays included.
6. Build status.
7. Export report path.
8. Timestamp.

---

## 21. Functional Requirements

### 21.1 Project Management

**FR-PROJ-001:** The system must allow users to create a new project.  
**FR-PROJ-002:** The system must persist projects locally.  
**FR-PROJ-003:** The system must allow users to reopen projects.  
**FR-PROJ-004:** The system must store project status and generation history.  
**FR-PROJ-005:** The system should support project-level settings for generation mode, output folder, and advanced mode.

### 21.2 Prompt and Planning

**FR-PLAN-001:** The system must accept a natural language collection prompt.  
**FR-PLAN-002:** The system must generate a structured collection plan.  
**FR-PLAN-003:** The system must include required user-specified items where feasible.  
**FR-PLAN-004:** The system must produce a collection-level style bible.  
**FR-PLAN-005:** The user must be able to edit and approve the plan.  
**FR-PLAN-006:** The system must mark functional candidates based on supported archetypes.

### 21.3 Concept Generation

**FR-CONCEPT-001:** The system must generate concept image prompts from item specs.  
**FR-CONCEPT-002:** The system must generate one or more concept images per item.  
**FR-CONCEPT-003:** The user must be able to approve, reject, or regenerate concepts.  
**FR-CONCEPT-004:** The system must preserve concept image artifacts and prompts.  
**FR-CONCEPT-005:** The system should score concept images for image-to-3D readiness.

### 21.4 Image-to-3D Generation

**FR-3D-001:** The system must support image-to-3D model adapters.  
**FR-3D-002:** The system must generate candidate mesh artifacts from approved concept images.  
**FR-3D-003:** The system must support multiple model candidates or providers.  
**FR-3D-004:** The system must store mesh artifacts and metadata.  
**FR-3D-005:** The system must run initial mesh QA after generation.  
**FR-3D-006:** The system must handle failed mesh generation without corrupting project state.

### 21.5 Blender Cleanup and Preview

**FR-BLEND-001:** The system must support Blender-based cleanup or normalization.  
**FR-BLEND-002:** The system must spike-test deterministic Python, MCP, and hybrid approaches.  
**FR-BLEND-003:** The system must generate preview renders.  
**FR-BLEND-004:** The system must store normalized intermediate files.  
**FR-BLEND-005:** The system must report cleanup failures with structured errors.

### 21.6 Collection Curation

**FR-CURATE-001:** The system must show a visual collection board.  
**FR-CURATE-002:** The user must be able to open item details.  
**FR-CURATE-003:** The user must be able to regenerate individual items.  
**FR-CURATE-004:** The user must be able to include or exclude items from export.  
**FR-CURATE-005:** The user must be able to edit item metadata.  
**FR-CURATE-006:** The system should allow candidate selection when multiple variants exist.

### 21.7 Functional Overlays

**FR-FUNC-001:** The system must allow eligible assets to be upgraded through the Functional Upgrade Wizard.  
**FR-FUNC-002:** The system must only show supported functional archetypes.  
**FR-FUNC-003:** The system must store functional overlays as extensions of source assets.  
**FR-FUNC-004:** The system must validate compatibility between source asset and overlay.  
**FR-FUNC-005:** The user must be able to review a behavior summary before export.  
**FR-FUNC-006:** The system should support decor-only, functional-only, or both export modes.

### 21.8 Validation

**FR-VAL-001:** The system must run project-level validation before export.  
**FR-VAL-002:** The system must run item-level validation.  
**FR-VAL-003:** The system must separate errors, warnings, and info messages.  
**FR-VAL-004:** The system must block export when critical requirements fail.  
**FR-VAL-005:** The system must suggest repair, retry, exclusion, or manual review actions where possible.

### 21.9 Export

**FR-EXPORT-001:** The system must provide an export flow.  
**FR-EXPORT-002:** The system must show an export summary before building.  
**FR-EXPORT-003:** The system must generate export artifacts for supported content.  
**FR-EXPORT-004:** The system must create an export report.  
**FR-EXPORT-005:** The system must show success, partial success, or failure.  
**FR-EXPORT-006:** The system should support optional test install to a configured folder.

### 21.10 Advanced / Developer Features

**FR-DEV-001:** The system must expose pipeline runs.  
**FR-DEV-002:** The system must expose logs.  
**FR-DEV-003:** The system must expose artifact paths.  
**FR-DEV-004:** The system must expose trace references.  
**FR-DEV-005:** The system should allow rerunning individual failed steps.  
**FR-DEV-006:** The system should allow mock vs real adapter configuration.

---

## 22. Non-Functional Requirements

### 22.1 Usability

1. The default UX must be usable by a non-technical Sims creator.
2. Technical terminology must be minimized in creator mode.
3. Advanced logs and technical controls must be hidden unless advanced mode is enabled.
4. Long-running jobs must show progress.
5. Failure messages must be actionable.

### 22.2 Reliability

1. Failed generation for one item must not destroy the entire project.
2. The product must save intermediate state frequently.
3. Regeneration must be scoped where possible.
4. Validation must run before export.
5. Mock and real adapters must return consistent state shapes.

### 22.3 Extensibility

1. New object archetypes must be addable later.
2. New functional overlays must be addable later.
3. New image-to-3D models must be addable through adapters.
4. New Blender automation strategies must be addable.
5. New eval harnesses must be addable.

### 22.4 Observability

1. Pipeline runs must be traceable.
2. Agent/tool/model calls must be logged.
3. Artifact lineage must be inspectable.
4. User review decisions must be recorded.
5. Evals must be runnable repeatedly.

### 22.5 Performance

The MVP does not need real-time generation for all stages. However:

1. The app UI must remain responsive during long jobs.
2. Users must see stage progress.
3. Jobs should be cancellable or skippable where feasible.
4. Concept generation should feel iterative.
5. Mesh generation may be slower but must not freeze the UI.

### 22.6 Local-First Project Safety

1. Project files must be stored in a predictable location.
2. Artifacts must be organized by project and item.
3. Failed jobs must not overwrite accepted assets without confirmation.
4. The system should support project backup by copying the project folder.

---

## 23. Validation Requirements

Validation must exist at multiple levels.

### 23.1 Concept Validation

Checks:

1. Concept image exists.
2. Concept is associated with item spec.
3. Concept was approved or is auto-approved by a selected mode.
4. Concept is suitable for image-to-3D generation or warning is shown.

### 23.2 Mesh Validation

Checks:

1. Mesh artifact exists.
2. Mesh imports into Blender.
3. Mesh has nonzero dimensions.
4. Mesh has plausible dimensions for object archetype.
5. Mesh has acceptable or flagged face count.
6. Mesh has preview render.
7. Mesh has material/texture status.

### 23.3 Item Validation

Checks:

1. Item has approved or selected asset variant.
2. Metadata exists.
3. Object archetype is supported.
4. Export inclusion state is clear.
5. Warnings are attached to item.

### 23.4 Functional Overlay Validation

Checks:

1. Source asset exists.
2. Functional archetype is supported.
3. Source asset is eligible.
4. Behavior config is complete.
5. Export mode is set.
6. Overlay is compatible with asset status.

### 23.5 Project Export Validation

Checks:

1. At least one item included.
2. All included items have selected variants.
3. No included item has blocking errors.
4. Export output path is valid.
5. Functional overlays pass validation.
6. Export report can be written.

---

## 24. Export Requirements

### 24.1 Export Modes

The product should support:

1. Full collection export.
2. Selected item export.
3. Decor-only export.
4. Functional variants export where supported.
5. Export report generation.

### 24.2 Export Report

The export report must include:

1. Project name.
2. Export timestamp.
3. Included items.
4. Excluded items.
5. Functional items.
6. Validation summary.
7. Warnings.
8. Export artifact paths.
9. Pipeline run reference.

### 24.3 Export Completion States

The export flow must report:

1. Success.
2. Success with warnings.
3. Partial success.
4. Failed with blockers.
5. Cancelled.

---

## 25. Parallel Implementation Plan

The product should be built through parallel UI and pipeline tracks.

### 25.1 Track A: Full UI with Mocked Pipeline

Build first or in parallel:

1. Project Dashboard.
2. New Collection Wizard.
3. Collection Plan Review.
4. Generation Workspace.
5. Concept Review.
6. Collection Board.
7. Item Detail.
8. Functional Upgrade Wizard.
9. Validation Center.
10. Export Center.
11. Advanced Panel.

Use mock data for:

1. Y2K collection plan.
2. Concept images.
3. 3D previews.
4. Mesh statuses.
5. Validation errors/warnings.
6. Export result.

### 25.2 Track B: Pipeline Vertical Slice

Build a real pipeline for one asset first:

**Y2K CD player -> concept image -> image-to-3D -> Blender cleanup strategy spike -> preview render -> mesh QA report -> export scaffold.**

Then repeat for:

1. Lava lamp.
2. Funky mirror.
3. Retro laptop/computer prop.
4. Small clutter item.

### 25.3 Track C: Connect UI to Pipeline

Replace mocks with real implementations in order:

1. Collection planner.
2. Concept generation.
3. Concept approval state.
4. Image-to-3D generation.
5. Blender cleanup.
6. Preview rendering.
7. Mesh QA.
8. Functional overlay.
9. Validation.
10. Export.

### 25.4 Track D: Harden and Evaluate

Add:

1. Evals.
2. Observability dashboards.
3. Retry/recoverability.
4. Better error states.
5. Human preference capture.
6. Regression test datasets.

---

## 26. MVP Acceptance Criteria

### 26.1 Product-Level Acceptance Criteria

**AC-001:** User can create a new project.  
**AC-002:** User can enter the Y2K anchor prompt.  
**AC-003:** System generates a structured collection plan including required items.  
**AC-004:** User can edit and approve the collection plan.  
**AC-005:** System generates concept images for planned items.  
**AC-006:** User can approve or regenerate concept images.  
**AC-007:** System generates candidate 3D meshes from approved concepts.  
**AC-008:** System runs Blender automation on candidate meshes.  
**AC-009:** System generates preview renders for generated assets.  
**AC-010:** User can review generated collection in Collection Board.  
**AC-011:** User can regenerate one item without restarting the whole project.  
**AC-012:** User can include or exclude items from export.  
**AC-013:** User can upgrade at least one eligible item into a supported functional object.  
**AC-014:** System validates the project before export.  
**AC-015:** System exports installable Sims 4 content for supported assets.  
**AC-016:** Advanced Panel shows logs, traces, and artifact paths.  
**AC-017:** At least one eval harness can be run on the anchor prompt.  
**AC-018:** The pipeline supports mock adapters and real adapters behind stable interfaces.

### 26.2 Vertical Slice Acceptance Criteria

The first real vertical slice must prove:

1. CD player item spec can be generated from prompt.
2. Concept image can be generated.
3. Concept image can be converted into a candidate 3D mesh.
4. Mesh can be imported into Blender.
5. Cleanup/normalization can be attempted.
6. Preview render can be generated.
7. Mesh QA report can be produced.
8. UI can show the item and status.
9. Item can be selected as audio functional candidate.
10. Export scaffold or final export stage can consume the item.

### 26.3 UI Acceptance Criteria

The UI MVP must be considered complete only when:

1. All required screens exist.
2. Screens are connected by the primary workflow.
3. Mock data covers success, warning, and failure states.
4. The user can move from prompt to export screen without developer tools.
5. Advanced mode is available but not required for normal use.
6. UI can be connected to real pipeline operations without major redesign.

---

## 27. Implementation Guardrails for Coding Agents

The coding agent must follow these guardrails:

1. Do not implement the product as a single chat window.
2. Do not make UI dependent on real generation before mock flows exist.
3. Do not hard-code one image-to-3D provider into the core product model.
4. Do not hard-code deterministic Blender Python as the only possible cleanup method.
5. Do not hard-code Blender MCP as the only possible cleanup method.
6. Use adapters for model/tool integrations.
7. Use graph-like pipeline state rather than one monolithic function.
8. Persist project state locally.
9. Save artifacts by project and item.
10. Preserve artifact lineage.
11. Add status states for every long-running operation.
12. Add failure states before implementing happy paths only.
13. Keep creator mode simple.
14. Keep advanced diagnostics available.
15. Keep functional overlays as extensions of assets, not disconnected duplicated items.
16. Add validation before export.
17. Add eval harness scaffolding early.
18. Avoid over-scoping into CAS, animation, or arbitrary gameplay mods.

---

## 28. Risks and Mitigations

### 28.1 Risk: Image-to-3D Quality Is Inconsistent

Mitigation:

1. Use concept image review before 3D generation.
2. Support multiple model adapters.
3. Run mesh QA.
4. Allow per-item regeneration.
5. Capture human preference data.

### 28.2 Risk: Blender Automation Is Brittle

Mitigation:

1. Spike deterministic Python, MCP, and hybrid approaches.
2. Use a common test asset set.
3. Validate outputs after cleanup.
4. Keep manual fallback hooks as post-MVP option.

### 28.3 Risk: UI Blocks on Slow Generation

Mitigation:

1. Use async job statuses.
2. Build UI against mocks.
3. Show progress by item and stage.
4. Allow skip/cancel where feasible.

### 28.4 Risk: Functional Objects Expand Scope Too Quickly

Mitigation:

1. Limit functional archetypes.
2. Hide unsupported archetypes.
3. Require compatibility validation.
4. Keep functional overlays schema-driven.

### 28.5 Risk: Pipeline Becomes Unobservable

Mitigation:

1. Add tracing from the beginning.
2. Log artifacts and lineage.
3. Include Advanced Panel.
4. Implement eval harnesses.

### 28.6 Risk: Coding Agent Overbuilds Future Features

Mitigation:

1. Use MVP feature list as boundary.
2. Keep CAS, animation, and arbitrary gameplay out of MVP.
3. Build vertical slices before broad expansion.
4. Use acceptance criteria as implementation gates.

---

## 29. Open Questions

These should be resolved during MVP or TAD creation:

1. Which desktop framework should be used?
2. Which local project storage format should be used?
3. Which graph orchestration framework should be selected?
4. Which observability platform should be selected?
5. Which image model generates best concept images for image-to-3D?
6. Which image-to-3D model should be the first real adapter?
7. What hardware/cloud execution model should be used for 3D generation?
8. How should Blender be installed and invoked?
9. What is the result of Blender MCP vs deterministic Python spike?
10. What exact export/package builder path should be used first?
11. What are the minimum acceptance checks for installable Sims output?
12. Should test install be MVP or should it remain should-have?
13. How many concept candidates should be generated per item by default?
14. How many mesh candidates should be generated per item by default?
15. What is the preferred preview/thumbnail render style?

---

## 30. Suggested MVP Build Sequence

### Phase 0: Repo and Product Skeleton

1. Create app shell.
2. Define project folder structure.
3. Define product state types.
4. Define mock pipeline interface.
5. Create fake Y2K project data.

### Phase 1: UI Skeleton

1. Project Dashboard.
2. New Collection Wizard.
3. Collection Plan Review.
4. Collection Board.
5. Item Detail.
6. Validation/Export screens.
7. Advanced Panel.

### Phase 2: Prompt-to-Plan

1. Implement planner adapter.
2. Validate plan schema.
3. Connect plan output to UI.
4. Add prompt-to-plan eval harness.

### Phase 3: Concept Image Pipeline

1. Implement concept prompt generation.
2. Implement concept image adapter.
3. Connect Concept Review UI.
4. Add concept image eval harness.

### Phase 4: Image-to-3D Pipeline

1. Implement first image-to-3D adapter.
2. Store mesh candidates.
3. Add model bakeoff harness.
4. Connect mesh generation status to UI.

### Phase 5: Blender Automation Spike

1. Build deterministic Python cleanup prototype.
2. Build Blender MCP cleanup prototype.
3. Build hybrid experiment if needed.
4. Run spike harness across required assets.
5. Choose initial production strategy.

### Phase 6: Mesh QA and Preview

1. Implement mesh validation checks.
2. Implement preview render generation.
3. Show preview in Item Detail and Collection Board.
4. Add mesh QA harness.

### Phase 7: Functional Overlay MVP

1. Implement eligibility mapping.
2. Implement Functional Upgrade Wizard.
3. Implement audio, light, mirror, and moodlet/vibe overlay schemas.
4. Add functional overlay harness.

### Phase 8: Export MVP

1. Implement export flow.
2. Implement export report.
3. Connect validation center.
4. Add export harness.

### Phase 9: Observability and Hardening

1. Integrate observability platform.
2. Add trace IDs to Advanced Panel.
3. Add user approval/rejection capture.
4. Add retry paths.
5. Run full anchor scenario.

---

## 31. Coding Agent Working Contract

A coding agent implementing this product should proceed as follows:

1. Start by building the app shell and UI state model.
2. Define interfaces before real adapters.
3. Build mocks for every pipeline step.
4. Implement UI flows against mocks.
5. Implement real vertical slices incrementally.
6. Preserve all generated artifacts and statuses.
7. Never collapse item-level state into a single global job flag.
8. Keep pipeline runs resumable and inspectable.
9. Add eval harness scaffolding before optimizing models.
10. Treat the Y2K anchor scenario as the main test case.
11. Avoid adding post-MVP content types unless explicitly approved.

---

## 32. Appendix A: Candidate Tooling to Evaluate

This list informs spike work. It is not a final architecture decision.

### 32.1 Image-to-3D Candidates

1. Stable Fast 3D / SF3D.
2. SPAR3D.
3. TripoSR.
4. TripoSG.
5. TRELLIS / TRELLIS.2.
6. Hunyuan3D 2.x.
7. Future model adapters.

### 32.2 Blender Automation Candidates

1. Blender Python API scripts.
2. Blender MCP server.
3. Custom Blender add-on.
4. Hybrid deterministic/agentic workflow.

### 32.3 Orchestration Candidates

1. LangGraph.
2. Equivalent graph workflow engine.
3. Custom lightweight graph runner if needed.

### 32.4 Observability Candidates

1. Langfuse.
2. Arize Phoenix.
3. LangSmith.
4. OpenTelemetry-backed custom tracing.
5. OpenAI Agents SDK tracing if the stack uses that SDK.

### 32.5 Eval Candidates

1. Promptfoo.
2. DeepEval.
3. Pytest-based custom harnesses.
4. Human preference review dataset.

---

## 33. Appendix B: Research Notes for Tooling Context

These notes are included to give implementers context for why the PRD calls for adapters and spike tests.

1. SF3D is relevant because it targets fast single-image textured mesh reconstruction.
2. SPAR3D is relevant because it builds on single-image reconstruction and adds point-aware control/editing concepts.
3. TRELLIS and TRELLIS.2 are relevant because they target high-fidelity image-to-3D asset generation.
4. Hunyuan3D 2.x is relevant because it separates mesh and texture/PBR-oriented stages, which fits an asset pipeline.
5. Blender Python API is relevant because Blender can be automated as a local 3D processing engine.
6. Blender MCP is relevant because agent-driven Blender control may outperform deterministic scripts for some cleanup or repair tasks.
7. LangGraph or equivalent graph orchestration is relevant because the product needs stateful, resumable, multi-step workflows with human gates.
8. Langfuse, Phoenix, or equivalent observability is relevant because the product needs traces, evals, experiments, and artifact lineage.
9. Promptfoo, DeepEval, and pytest-style harnesses are relevant because the product needs repeatable evaluation of prompts, agents, and pipeline outputs.

---

## 34. Final MVP Definition

The final MVP definition is:

**AI Sims Creator MVP is a desktop application that lets a user create a Sims 4 Build/Buy custom content collection from a prompt, review generated concept images and 3D asset previews, refine individual items, optionally upgrade supported objects into functional objects, validate the project, and export installable Sims 4 content. The system is powered by a multi-stage agentic generation pipeline with pluggable AI/model/tool adapters, Blender automation experiments, observability, and eval harnesses.**

---

## 35. Final Alignment Statement

This PRD intentionally defines an MVP that is ambitious but constrained.

It is ambitious because it requires real asset generation, full UI, multi-agent orchestration, image-to-3D workflows, Blender automation, functional overlays, observability, and eval harnesses.

It is constrained because it focuses on supported Sims 4 Build/Buy object categories, does not attempt CAS, does not require custom animation, and does not claim arbitrary mod generation from any prompt.

The product should be built as a structured creator studio, not a magical one-shot generator.
