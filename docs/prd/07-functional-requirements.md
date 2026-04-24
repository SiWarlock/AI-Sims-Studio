# PRD — Functional Requirements

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §18

> All functional requirements FR-001 through FR-087 across project management, planning, templates, generation, functional overlay, review, validation, export, and admin mode.

---

## 18. Functional Requirements

### 18.1 Project Management

- **FR-001 — Project Creation**
  The system must allow creating a new project with: project name; theme prompt; optional style notes; optional reference images; desired collection size (1–12); single-item or collection mode selection.
- **FR-002 — Project Persistence**
  The system must persist project state locally and allow reopening a project later.
- **FR-003 — Project Version Safety**
  The system must support internal save points sufficient for rollback and deterministic rebuild.
- **FR-004 — Project Portability**
  A project must be self-contained in a single folder that can be copied or zipped and moved.
- **FR-005 — Single-Item Projects**
  The system must support a project containing exactly one item. A collection of one is a legitimate project.

### 18.2 Prompt and Collection Planning

- **FR-010 — Prompt Intake**
  The system must accept natural language prompts describing a collection concept.
- **FR-011 — Collection Plan Generation**
  The system must produce a structured collection plan including: project theme summary; proposed item list; template primitive per item (with confidence score); style attributes; palette and material direction.
- **FR-012 — Editable Collection Plan**
  The user must be able to edit the collection plan before generation and after initial generation.
- **FR-013 — Template Match Confidence**
  The system must expose a per-item confidence score indicating how well the requested item maps to an available template. Low-confidence items must surface a warning in the UI.
- **FR-014 — Item Count Control**
  The user must be able to specify or adjust desired collection size within allowed bounds (1–12 in MVP).
- **FR-015 — Collection Coherence**
  The system must preserve style coherence across all generated items in a collection, including shared palette guidance, shared material vocabulary, and shared tone in metadata.
- **FR-016 — Best-Effort with Warning**
  When no template matches an item well, the system must warn the user and offer options: proceed with the best available match, skip the item, or replace the request with a suggested alternative.

### 18.3 Template System

- **FR-020 — Tier 1 Template Library**
  The system must ship with a Tier 1 template library. The library must be loadable, queryable by attributes, and referenceable by ID.
- **FR-021 — Tier 2 Importer**
  The system must provide an admin-mode importer that reads base-game meshes from the user's Sims 4 installation and registers them as Tier 2 templates.
- **FR-022 — Template Promotion**
  The system must support promoting a Tier 2 template to Tier 1 via admin-mode schema authoring.
- **FR-023 — Template Schema**
  Every Tier 1 template must declare: unique ID; shape class; dimension ranges; texture zones with labels; footprint type; compatible archetypes; example object types.
- **FR-024 — Graceful Degradation**
  The system must not break when a Tier 2 template is referenced with incomplete schema; it must operate on the available schema and degrade gracefully.

### 18.4 Decorative Asset Generation

- **FR-030 — Item Generation**
  The system must generate a supported decorative object for each planned item using its selected template primitive.
- **FR-031 — Texture Set Generation**
  For each swatch, the system must generate a coordinated set of texture maps (diffuse, normal, specular) per declared texture zone.
- **FR-032 — Swatch Support**
  The system must support multiple swatches (minimum 1, target 3) per item.
- **FR-033 — Thumbnail Generation**
  The system must render a deterministic thumbnail for each item from its textured mesh using a headless 3D render pipeline. Thumbnails must match in-game appearance.
- **FR-034 — Metadata Generation**
  The system must generate initial metadata per item: name, description, tags, price suggestion, Build/Buy category, optional custom catalog filter tag.
- **FR-035 — Per-Item Regenerate**
  The user must be able to regenerate any single item without restarting the project.
- **FR-036 — Per-Item Replace**
  The user must be able to replace any single item with a newly generated alternative.
- **FR-037 — Per-Item Exclude**
  The user must be able to exclude an item from final export without deleting it.
- **FR-038 — Swatch Regenerate**
  The user must be able to regenerate individual swatches of an item.

### 18.5 Functional Overlay

- **FR-040 — Functional Candidate Selection**
  The user must be able to select an item and request a functional upgrade.
- **FR-041 — Archetype Filter**
  The system must present only archetypes compatible with the selected item's template.
- **FR-042 — Guided Functional Setup**
  The system must guide the user through configuration of supported behavior (e.g., on/off state behavior, moodlet type and duration, interaction availability).
- **FR-043 — Functional Overlay Model**
  The system must represent functional behavior as an overlay on top of the underlying item, not as a separate item definition.
- **FR-044 — Base-Game Reference Cloning**
  The system must clone tuning from the appropriate base-game reference object for the selected archetype, using the user's local Sims 4 installation as the source.
- **FR-045 — Functional Preview Summary**
  Before export, the system must show a human-readable summary of the functional behavior.
- **FR-046 — Variant Export Choice**
  The system must allow exporting any combination of: decor-only variant; functional variant; both.

### 18.6 Review and Editing

- **FR-050 — Collection Board**
  The system must provide a collection-level view showing all items with previews, status, and quick actions.
- **FR-051 — Item Detail View**
  The system must provide an item-level detail view with larger preview, swatch list, metadata view and edit, regenerate controls, and functional upgrade action.
- **FR-052 — Metadata Edit**
  The user must be able to edit name, description, tags, price, Build/Buy category, and custom catalog filter tag.
- **FR-053 — Status Visibility**
  Each item must visibly communicate its status: planned, generating, generated, needs review, functional candidate, export-ready, warning, error.
- **FR-054 — Style Lock**
  Collection style is immutable after creation. Attempts to change it must be rejected with a clear message.

### 18.7 Validation

- **FR-060 — Pre-Export Validation**
  The system must validate project readiness before export.
- **FR-061 — Error vs Warning**
  The system must distinguish between blocking errors and non-blocking warnings.
- **FR-062 — Validation Scope (MVP)**
  Validation must cover: asset completeness; thumbnail presence; metadata completeness; DBPF structural integrity; TGI resource ID consistency; tuning XML schema compliance (for functional items); internal project consistency.
- **FR-063 — Validation Reporting**
  Validation results must be shown in user-readable form in the primary UI and in detail form in admin mode.
- **FR-064 — User Verification Flow**
  The system must provide an optional in-game verification step after auto-install, where the user confirms items appeared correctly.

### 18.8 Export and Installation

- **FR-070 — Export Entry Point**
  The system must provide a clear export action in the creator UI.
- **FR-071 — Export Summary**
  Before export executes, the system must show a summary: included items, functional variants, warnings, blockers, output target.
- **FR-072 — Build Execution**
  The system must build export outputs (`.package` files) for supported content.
- **FR-073 — Mods Folder Auto-Detection**
  The system must auto-detect the user's Sims 4 Mods folder on both macOS and Windows standard installs.
- **FR-074 — Auto-Install**
  After successful export, the system must auto-install the `.package` files to the detected Mods folder and confirm installation visibly.
- **FR-075 — Export Result Visibility**
  The system must show success, partial success, or failure after export.
- **FR-076 — Deterministic Rebuild**
  The system must be able to rerun a prior build deterministically from saved project state.

### 18.9 Admin Mode

- **FR-080 — Admin Mode Access**
  Admin mode must be accessible via keyboard shortcut or application menu and must be hidden from the primary creator flow.
- **FR-081 — Template Browser**
  Admin mode must provide a browser of all Tier 1 and Tier 2 templates with their full schemas.
- **FR-082 — Template Import**
  Admin mode must provide a base-game mesh importer that reads from the local Sims 4 install.
- **FR-083 — Template Promotion Editor**
  Admin mode must provide a schema editor for promoting Tier 2 templates to Tier 1.
- **FR-084 — Build Logs**
  Admin mode must expose build and generation logs with full detail.
- **FR-085 — Job History**
  Admin mode must retain per-job status history and artifact references.
- **FR-086 — Reference Object Browser**
  Admin mode must provide a browser of base-game reference objects (for archetype inspection) read from the local Sims 4 install.
- **FR-087 — Configurability**
  Admin mode must expose advanced configuration settings (model selection, retry policies, path overrides) without cluttering the default UX.

---
