# PRD — Non-Functional Requirements, Screens, and Workflows

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §19, §20, §21

> Non-functional requirements (reliability, usability, etc.), screen inventory, and primary workflows A through D.

---

## 19. Non-Functional Requirements

### 19.1 Reliability

- Prefer deterministic build paths over purely generative output wherever game compatibility is affected.
- Fail gracefully with actionable messages.
- Isolate per-item failures where possible; do not cascade.

### 19.2 Usability

- Default UI must be approachable for a non-technical creator.
- Minimize or explain technical terms.
- Break complex workflows into guided steps.

### 19.3 Transparency

- Indicate high-confidence vs lower-confidence outputs where relevant.
- Show exactly what will be exported before export.
- Surface template match confidence clearly.

### 19.4 Extensibility

- Structured so new archetypes, templates, pipelines, and validators can be added.
- Schema supports Maxis Match as a future style without rework.
- Schema supports additional archetypes without core changes.

### 19.5 Inspectability

- Sufficient logs and state exposed for diagnosing failures via admin mode.

### 19.6 Performance

- Visible progress during long-running jobs.
- Avoid blocking the UI for single-item generation where possible.
- Parallelize independent generation steps where feasible.

### 19.7 Portability

- Project files stored in a portable layout supporting backup, transfer, and reloading.

### 19.8 Cross-Platform Parity

- Both macOS and Windows builds must produce identical outputs from identical inputs.
- Platform-specific behavior limited to: install detection, Mods folder path, log file location, Blender discovery path.

### 19.9 Privacy

- No telemetry to remote servers.
- No outbound data beyond AI API calls explicitly required for generation.
- All logs stored locally.
- User's project data never leaves the local machine.

---



## 20. Information Architecture / Screen Requirements

### 20.1 Home / Project Hub

- Create project
- Open existing project
- Recent projects list with thumbnails and status
- Single-item quick-start
- Admin mode entry (keyboard shortcut or discoverable menu)

### 20.2 New Project Wizard

Required inputs:

- Project name
- Mode selector (collection or single item)
- Theme prompt
- Desired item count (collections only, 1–12)
- Optional reference description
- Optional style notes
- Style preference (semi-Alpha only in MVP; locked in UI)

### 20.3 Collection Plan Review

- Proposed items list
- Template match confidence per item
- Edit, add, remove, reorder items
- Warning indicators for low-confidence matches
- "Generate" button to proceed

### 20.4 Collection Board

- Grid of items with thumbnails
- Status per item
- Include/exclude toggle
- Open item detail
- Functional candidate indicator
- Project-level generate / regenerate / export controls

### 20.5 Item Detail Screen

- Large preview
- Swatch list with per-swatch regenerate
- Metadata view and edit (name, description, tags, price, category, custom filter tag)
- Regenerate item
- Replace item
- Make functional action (if eligible)
- Per-item diagnostics (basic view for creator, detailed view in admin mode)

### 20.6 Functional Upgrade Wizard

- Archetype selection (filtered by template compatibility)
- Behavior configuration for the selected archetype
- Summary preview
- Confirmation step

### 20.7 Validation / Export Screen

- Validation summary
- Errors and warnings with plain-language explanations
- Export choices (per-item variant selection)
- Export trigger
- Export result summary
- Auto-install confirmation
- Optional "verify in-game" step

### 20.8 Admin Mode Surfaces

- Template library browser
- Template schema editor
- Base-game mesh importer
- Base-game reference object browser
- Build logs viewer
- Job history
- Configuration panel

---



## 21. Primary Workflows

### 21.1 Workflow A — Create a Collection

1. User starts a new project.
2. User enters a theme prompt and desired item count.
3. System generates a collection plan with template matches and confidence scores.
4. User reviews, edits, and approves the plan.
5. User starts generation.
6. System generates supported assets with textures, thumbnails, swatches, and metadata.
7. User reviews the collection board.
8. User regenerates, replaces, or excludes items as needed.
9. User approves the set for export or further functional upgrades.

### 21.2 Workflow B — Upgrade an Item to Functional

1. User opens an item.
2. User selects "Make Functional."
3. System presents compatible archetypes.
4. User configures supported behavior.
5. System clones the appropriate base-game reference object's tuning and applies the user's mesh, textures, strings, and configured values.
6. System shows summary.
7. User chooses export variant (decor-only, functional, or both).

### 21.3 Workflow C — Validate, Export, and Install

1. User opens export screen.
2. System runs structural validation.
3. User reviews blockers and warnings.
4. User resolves blockers or excludes problem items.
5. User triggers export.
6. System builds `.package` files.
7. System auto-installs to Mods folder.
8. System reports result.
9. User optionally launches Sims, verifies in-game, and records confirmation.

### 21.4 Workflow D — Admin Template Import and Promotion

1. Admin enters admin mode.
2. Admin opens base-game mesh importer.
3. Admin browses objects from the local Sims 4 install.
4. Admin imports selected meshes as Tier 2 templates.
5. Admin opens the schema editor for a Tier 2 template.
6. Admin authors texture zones, archetype compatibility, and example object types.
7. Admin saves, promoting the template to Tier 1.

---
