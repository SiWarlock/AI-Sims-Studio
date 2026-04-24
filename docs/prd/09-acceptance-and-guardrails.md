# PRD — Acceptance, Constraints, Guardrails, and Summary

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §22, §23, §24, §25, §26, §27, §28, §29, §30, §31, §32, §33, §34, §35, §36, §39

> Acceptance criteria AC-001 through AC-016, feature-area requirements, playable-in-game definition, trust/data/AI/error/logging/security/quality requirements, edge cases, metrics, release criteria, implementation guardrails, assumptions, and executive summary.

---

## 22. Detailed MVP Acceptance Criteria

The MVP is successful only if all of the following are verifiable.

- **AC-001 — New Project.** A user can create and save a new collection project or single-item project.
- **AC-002 — Prompt to Plan.** A user can enter a natural language prompt and receive a coherent collection plan with per-item template matches and confidence scores.
- **AC-003 — Plan Editing.** A user can edit, add, remove, and reorder items in the proposed plan before generation.
- **AC-004 — Decorative Generation.** A user can generate a supported collection of decorative objects from the plan using semi-Alpha style.
- **AC-005 — Item Review.** Each generated item shows a preview, swatches, and metadata.
- **AC-006 — Per-Item Iteration.** A user can regenerate, exclude, or replace any single item without restarting the project.
- **AC-007 — Functional Upgrade.** A user can upgrade at least one supported generated item into a functional object through the guided flow, using base-game tuning cloning.
- **AC-008 — Validation.** The product catches common pre-export readiness issues and clearly separates blockers from warnings.
- **AC-009 — Export.** A user can export the collection successfully as `.package` files.
- **AC-010 — Auto-Install.** The app auto-installs to the detected Mods folder.
- **AC-011 — In-Game Verification.** A user can optionally confirm in-game that the exported items appear correctly.
- **AC-012 — Deterministic Project State.** An administrator can reopen the project and rerun the build deterministically from saved state.
- **AC-013 — Admin Template Import.** An administrator can import a base-game mesh as a Tier 2 template via admin mode.
- **AC-014 — Admin Template Promotion.** An administrator can promote a Tier 2 template to Tier 1 by authoring its schema in admin mode.
- **AC-015 — Cross-Platform Parity.** Both Mac and Windows builds produce identical exports from identical projects.
- **AC-016 — Style Architecture.** The collection style parameter is present in the data model and schemas, even though only semi-Alpha is implemented.

---



## 23. Requirements by Feature Area

### 23.1 Project Lifecycle

Enable a persistent, project-based workflow.

- Create, open, save
- Portable storage
- Recent projects
- Single-item and collection modes
- Deterministic rebuild support

### 23.2 Prompt-to-Collection Planning

Translate user intent into an editable plan.

- Theme summary
- Candidate item list
- Template matches with confidence scores
- Material/palette/style hints
- User edits before and after generation

### 23.3 Template Library

Provide the geometric foundation.

- Tier 1 curated primitives with full schema
- Tier 2 user-imported base-game meshes
- Promotion path
- Graceful degradation for incomplete schemas

### 23.4 Object Generation

Produce Sims-ready decorative assets.

- Template-based geometry
- AI-generated textures with coordinated maps
- Deterministic thumbnails
- Metadata generation
- Multiple swatches per item

### 23.5 Collection Coherence

Ensure generated outputs feel like one set.

- Collection-level style context
- Shared palette and material guidance
- Consistent metadata tone
- Shared visual aesthetic

### 23.6 Functional Overlays

Upgrade decorative items to functional objects.

- Supported archetype list
- Compatibility filtering by template
- Guided configuration
- Base-game tuning cloning
- Variant export choice

### 23.7 Validation and Export

Produce reliable installable output.

- Pre-export validation
- Error/warning separation
- Structural DBPF integrity checks
- Auto-install
- In-game verification

### 23.8 Admin Mode

Support the technical maintainer.

- Template library management
- Base-game mesh import
- Logs and job history
- Configuration access

---



## 24. Requirements for "Playable In-Game" Output

The phrase "playable in-game" must be interpreted consistently across the product.

### 24.1 Decorative Objects

The MVP must satisfy:

- Object appears in exported `.package`
- Object is installable through auto-install
- Object appears in the correct Build/Buy catalog category
- Object is placeable in the world
- Object visually resembles its intended design within acceptable generation quality bounds
- Swatches switch correctly
- Thumbnail in catalog matches the in-world appearance

### 24.2 Functional Objects

The MVP must satisfy:

- Object exports successfully
- Object is installable
- Object presents its archetype's supported state or interaction
- Object behaves according to its selected archetype at a basic usable level
- Cloned tuning does not corrupt the user's save or cause game crashes under normal use

### 24.3 Honesty Requirement

The product must not market unsupported generated objects as fully validated functional content. Archetypes outside the MVP list must not be offered.

---



## 25. Creator Trust Requirements

The product must preserve user trust through these behaviors:

- Make supported vs unsupported capabilities clear
- Show status and validation results clearly
- Never fabricate confidence for low-confidence outputs
- Allow the user to inspect exactly what will be included in export
- Avoid hiding blockers behind vague messaging
- Warn when template match is poor and let the user choose whether to proceed
- Never imply the app produced a mesh it did not produce (templates are reused geometry)

---



## 26. Data / Domain Requirements (Product-Level)

The following conceptual entities must exist in the data model. Exact schema definitions belong to the TAD.

- **Project** — the top-level unit
- **Collection** — a grouping of items within a project, with a style preference
- **Item** — one generated object
- **Template** — a Tier 1 or Tier 2 template primitive
- **TemplateSchema** — the structured metadata on a Template
- **Swatch** — a texture variant of an Item
- **TextureSet** — diffuse, normal, specular maps per zone for a swatch
- **FunctionalOverlay** — functional behavior applied to an Item
- **Archetype** — a functional archetype definition with a base-game reference
- **ReferenceObject** — a base-game object used for cloning
- **BuildJob** — a build/generation job instance with status and artifacts
- **ValidationResult** — outcome of validation
- **ExportArtifact** — the output `.package` and related outputs
- **ReferenceInput** — optional user-provided style references
- **GenerationAttempt** — provenance of a generation step

These entities must support persistence, status tracking, rebuilds, and extensibility.

---



## 27. AI Usage Requirements

### 27.1 AI Stages in the Pipeline

The product uses AI at bounded stages. The TAD specifies exact models; the PRD specifies the stages.

1. **Collection planning** — prompt → structured plan
2. **Per-item spec generation** — item + template schema → detailed texture prompts and metadata
3. **Texture generation** — prompts → diffuse, normal, specular texture images
4. **Tuning value suggestion** — archetype + user inputs → concrete tuning parameter values
5. **Validation explanation** — validation result → user-readable message
6. **Repair suggestion** — failure → suggested user action

Non-AI stages (must be deterministic):

- Template selection execution
- Mesh loading
- Texture-to-mesh application
- Thumbnail rendering
- DBPF packaging
- Tuning cloning and editing
- Structural validation
- Auto-install

### 27.2 Rules

1. AI must be used in bounded stages.
2. AI must not bypass required validation.
3. The user must not be forced to understand which model is doing what.
4. Generation failures must be treated as recoverable workflow events.
5. AI orchestration must serve the product workflow, not dominate it.
6. AI must never generate or modify a `.package` file directly.
7. AI must never write tuning XML; it only suggests values that are injected into cloned tuning.

### 27.3 Model Tier Considerations

Model selection is specified in the TAD. At the PRD level, only the division of responsibilities is fixed:

- Reasoning and structured output stages use frontier reasoning models
- Texture generation uses hosted image models via a commercial provider
- Thumbnail rendering is deterministic via Blender
- No local model inference is required on the user's machine

---



## 28. Error Handling Requirements

### 28.1 User-Facing Errors

- Understandable
- Specific enough to guide action
- Free of internal jargon
- Offer a next step where possible

### 28.2 Maintainer-Facing Errors

Admin mode exposes:

- Stage name
- Item affected
- Failure type
- Retry/rebuild context
- Sufficient detail to investigate root cause
- Full stack traces where applicable

### 28.3 Partial Failure Handling

If one item fails generation or validation, the rest of the project must remain usable where possible. Failures must be isolated and clearly attributed.

---



## 29. Logging and Observability Requirements

### 29.1 Required Logging

- Job lifecycle events
- Item-level status transitions
- Validation outcomes
- Export outcomes
- Generation attempt records
- Error events with context

### 29.2 Recommended Logging

- Artifact references
- Elapsed time per stage
- Retry counts
- Confidence annotations where meaningful

### 29.3 Storage

- Per-OS standard locations:
  - macOS: `~/Library/Logs/AISimsCreator/`
  - Windows: `%APPDATA%\AISimsCreator\logs\`
- Per-session log files
- Locally stored only; no remote telemetry

---



## 30. Security and Safety Requirements

- Local project files must not be silently corrupted by failed jobs.
- Destructive actions (project deletion, template deletion) must be confirmable and ideally reversible.
- External model/tool failures must not leave project state unusable.
- Exported content state must be inspectable before final build completion.
- The app must not modify the user's Sims 4 installation directory (read-only access).
- The app must not modify the user's Mods folder beyond writing its own exported `.package` files.

---



## 31. Quality Requirements

### 31.1 Collection Quality

- Items feel thematically coherent
- Metadata is not random-feeling
- Thumbnails are usable for review
- Texture quality holds up at in-game camera distance

### 31.2 Usability Quality

- Common user path is understandable without technical documentation
- One-item regeneration is straightforward
- Functional upgrade flow does not feel like a developer form
- Errors guide the user rather than block them

### 31.3 Build Quality

- Export flow is consistent
- Validation catches obvious project issues
- Rebuilds do not randomly diverge
- Auto-install works reliably on standard Sims installs

---



## 32. Edge Cases

1. User wants fewer or more items after initial plan generation.
2. One generated item is poor quality while the rest are acceptable.
3. User changes theme direction mid-project.
4. A decorative item is not eligible for any requested functional archetype.
5. One item fails validation while others are export-ready.
6. User wants decor-only export for one item and functional export for another.
7. Project is reopened after partial progress.
8. Build succeeds for some items and fails for others.
9. User wants to keep a prior swatch instead of a regenerated one.
10. Template match confidence is poor for a requested item.
11. User's Sims 4 install is in a non-standard location.
12. User's Mods folder is on a different drive from the Sims install.
13. Blender is not installed when the app launches.
14. User has an older Sims 4 patch than the app expects.
15. User imports a base-game mesh whose slot data the app cannot fully parse.
16. A Replicate (or equivalent) API call fails or times out mid-generation.
17. User cancels a job mid-run.
18. User tries to open a project from a different machine with a different Sims install path.

---



## 33. Product Metrics

### 33.1 MVP Success Metrics

- Project completion rate (projects created vs projects exported)
- Time to first export
- Per-item regeneration frequency
- Functional upgrade completion rate
- Validation failure rate
- Export success rate
- Auto-install success rate
- Number of maintainer interventions per project

### 33.2 Product Health Metrics

- Number of blocked exports
- Most common validation failures
- Templates with highest poor-match rate
- Average attempts per accepted item
- Distribution of creator actions across flows

### 33.3 Quality Metrics

- User-reported "looks right in game" confirmations
- Number of items excluded vs kept
- Rate of template promotion from Tier 2 to Tier 1

---



## 34. Release Criteria for MVP

The MVP is complete when all are true:

1. A user can create a new project (collection or single item) from a prompt.
2. A user can review and edit the generated collection plan, including resolving low-confidence matches.
3. A user can generate a multi-item decorative collection in semi-Alpha style using Tier 1 templates.
4. A user can regenerate individual items and swatches.
5. A user can view previews, metadata, and status for each item.
6. A user can make at least one supported item functional via base-game tuning cloning.
7. A user can validate and export the project.
8. Exported output auto-installs to the user's Mods folder.
9. User can verify in-game appearance and record confirmation.
10. Project state can be reopened and rebuilt deterministically.
11. Admin mode provides template library access, base-game importer, logs, and job history.
12. Both macOS and Windows builds ship and pass parity tests.
13. AC-001 through AC-016 all pass on manual acceptance testing.
14. Milestone zero (texture proof-of-concept) was passed before full build.

---



## 35. Implementation Guardrails for Engineering / Coding Agents

These are mandatory product guardrails.

1. **Do not implement the system as a single free-form agent controlling everything.** Stages are bounded; orchestration is explicit.
2. **Do not make external tool automation the only path to success.** No dependency on S4Studio, Blender GUI, or any other external tool being driven programmatically at runtime.
3. **Do not couple decorative generation and functional generation as totally separate object systems.** They share an underlying item model.
4. **Do not hide project state in opaque transient memory only.** State must be persisted to SQLite and the file tree.
5. **Do not make the default UX depend on the user understanding modding internals.** All technical language belongs in admin mode.
6. **Do not over-scope MVP into unsupported categories.** No CAS, no animation authoring, no scripting beyond tuning clones.
7. **Do not skip validation or deterministic rebuild support.**
8. **Do not present unsupported functionality as production-ready.**
9. **Do not generate `.package` files using AI.** Packaging is deterministic code.
10. **Do not generate tuning XML from scratch using AI.** Tuning is cloned from base-game references; only values are AI-suggested.
11. **Do not generate 3D meshes using AI in MVP.** Geometry comes from templates only.
12. **Do not ship without the style parameter in the schema.** Even though only semi-Alpha is implemented, the parameter must exist for v1.5.
13. **Do not ship telemetry.** Local logging only.
14. **Do not bundle Blender.** Blender is a separate install prerequisite.

---



## 36. Assumptions

- The product is initially personal-use.
- The primary creator is the product owner's girlfriend; the administrator is the product owner.
- The primary creator uses macOS; the administrator uses Windows.
- Both have a standard Sims 4 install via Origin / EA App.
- The MVP is desktop-first on macOS and Windows, shared codebase.
- The MVP targets Sims 4 only.
- Supported object archetypes are constrained to the four MVP archetypes.
- Alpha-style CC is the creator's preference; semi-Alpha is the MVP implementation target.
- Future documents (MVP Specification, TAD, Architecture Diagrams, API Specification) will define the technical details.

---



## 39. Executive Summary

AI Sims Creator is a cross-platform desktop creator studio for The Sims 4 that enables a non-technical creator to generate themed custom content collections, refine them, optionally upgrade selected items into functional objects through base-game tuning cloning, validate the outputs, and auto-install them into the user's Mods folder.

The MVP is not a planning assistant. It generates real supported assets that are usable in-game within defined template primitives and functional archetypes.

The product succeeds by combining:

- Prompt-driven creation
- Collection-level coherence
- A curated template library that provides geometric foundation
- AI-generated semi-Alpha textures, metadata, and tuning values
- Guided functional upgrades via base-game reference cloning
- Deterministic validation, packaging, and installation
- A clean primary creator experience with an admin mode for the maintainer
- Shared codebase across macOS (primary user) and Windows (administrator)

This PRD defines the product behavior and boundaries that the MVP Specification, Technical Architecture Document, and coding agent implementation must follow.

---

*End of PRD v1.0*
