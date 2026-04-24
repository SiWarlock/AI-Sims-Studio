# PRD — MVP Definition and Scope

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §10, §12, §13

> MVP objective, anchor scenario, playable-in-game promise, core capabilities, in- and out-of-scope.

---

## 10. MVP Definition

### 10.1 MVP Objective

Deliver a cross-platform desktop creator studio (Mac + Windows, shared codebase) that allows a user to generate a themed Sims 4 object collection from a natural language prompt, preview and refine the collection, optionally convert selected items into supported functional objects, validate the result, and export and auto-install content to the user's Mods folder.

### 10.2 MVP Anchor Scenario

The primary creator wants to build a **Y2K clutter collection** including:

- CD player
- Lava lamp
- Retro translucent laptop
- Funky mirror
- Small Y2K vase
- Wall poster

The system must:

- Generate the collection plan from a single prompt plus item wishes
- Generate the items as decorative Build/Buy assets using template primitives and semi-Alpha style textures
- Present previews, swatches, and editable metadata
- Allow refinement per item
- Allow at least one supported item (e.g., the lava lamp) to be upgraded to a functional object
- Validate the output
- Export installable content
- Auto-install to the user's Sims 4 Mods folder
- Support user verification that items appear correctly in-game

### 10.3 MVP Scope of "Playable In-Game"

The MVP must produce supported, playable-in-game assets where "playable" means:

- Decorative items appear in the Build/Buy catalog in the correct category
- Decorative items can be placed in the world
- Swatches switch correctly
- Functional items can be installed and present their archetype behavior at a basic usable level

---



## 12. Core Product Capabilities

The application must support the following major capabilities.

### 12.1 Project Creation

- Create a new project with name, theme prompt, style preference (semi-Alpha in MVP), and optional style references.
- Create a single-item project or a collection project.
- Store project state persistently.
- Reopen and continue projects.

### 12.2 Collection Planning

- Convert prompt + desired item count into a proposed collection plan.
- Match each planned item to a template primitive from the Tier 1 library (or flagged as unmatched if no template fits well).
- Maintain stylistic consistency across the collection.
- Allow user edits to the collection plan before or after initial generation.

### 12.3 Decorative Asset Generation

- Select a template primitive for each item.
- Generate coordinated semi-Alpha texture sets (diffuse, normal, specular) per texture zone, per swatch.
- Render deterministic thumbnails from the textured mesh.
- Generate metadata including names, descriptions, tags, pricing suggestions, and Build/Buy category placement.
- Support multiple swatches per item.

### 12.4 Functional Upgrade Flow

- Allow user to select a generated decorative item and mark it as a functional candidate.
- Present only archetypes compatible with that item's template.
- Guide the user through supported behavior configuration.
- Clone a base-game reference object's tuning, swapping in the user's mesh, textures, strings, and configured values.
- Build both a decor-only and a functional variant of the object, or either alone per user choice.

### 12.5 Review and Iteration

- Per-item regeneration of textures, metadata, or swatches.
- Per-item exclusion from export (without deletion).
- Per-item replacement with a newly generated alternative.
- Edit collection composition (add, remove, reorder).
- Compare variants.
- Override auto-suggested metadata (name, description, price, tags, category).

### 12.6 Validation

- Validate asset completeness and integrity structurally.
- Validate export readiness.
- Identify high-confidence problems before export.
- Distinguish blockers from warnings.
- Present results in user-readable form (creator) and detailed form (admin).

### 12.7 Export and Installation

- Export installable `.package` files for supported content.
- Auto-detect the user's Sims 4 Mods folder.
- Auto-install exported packages to the Mods folder.
- Support export summary and status reporting.
- Support deterministic rebuild from saved project state.
- Support user in-game verification step.

### 12.8 Admin Mode

- Template library browser and editor
- Base-game mesh importer (Tier 2)
- Build logs and job history
- Regeneration provenance
- Internal state inspection
- Error detail view
- Reference object browser for base-game tuning inspection
- Configuration surfaces

---



## 13. MVP Scope

### 13.1 In Scope for MVP

#### A. Platform

- Cross-platform desktop application (macOS + Windows)
- Shared codebase, separate builds per OS
- Local project storage
- Guided primary creator UI
- Admin mode accessible via menu or keyboard shortcut
- Requires local Sims 4 installation at runtime (standard Origin / EA App install)
- Requires Blender installed separately (prompted on first launch if missing)

#### B. Content Types

- Decorative Build/Buy objects (clutter, shelf decor, wall-adjacent decor, tabletop decor)
- Furniture (seating, tables, beds, storage)
- Supported functional overlays for a defined set of archetypes

#### C. Visual Style

- Semi-Alpha visual style as default and only shipping style
- Architecture supports Maxis Match style (data model, schema, prompt library, material pipeline all accept a style parameter), but only semi-Alpha is implemented in MVP

#### D. Generation

- Prompt-to-collection planning
- Prompt-to-supported-object specification
- Texture set generation (diffuse, normal, specular) per texture zone, per swatch, using Replicate-hosted image models
- Deterministic thumbnail rendering via Blender headless pipeline
- Metadata generation (name, description, tags, pricing suggestion)
- Functional tuning value suggestion

#### E. Template Library

- Tier 1 curated library of 12–15 (or more) category-based shape primitives shipped with the app
- Each Tier 1 template declares: shape class, dimension ranges, texture zones, footprint type, archetype compatibility, example objects it can represent
- Tier 2 base-game mesh importer accessible in admin mode, supporting import of base-game meshes as lower-schema templates
- Promotion path from Tier 2 to Tier 1 via admin-mode metadata authoring

#### F. Editing / Review

- Collection board
- Per-item detail view
- Per-item regenerate, remove, replace
- Metadata editing
- Functional upgrade flow
- Collection-level style preference (set at creation, immutable thereafter)

#### G. Validation / Export

- Structural validation (DBPF integrity, TGI resource IDs, tuning XML schema)
- Error/warning distinction
- Auto-install to Mods folder
- User verification flow (optional manual in-game check)
- Build status and logs

#### H. Admin Mode

- All capabilities listed in section 12.8

### 13.2 Out of Scope for MVP

- Full CAS item support
- Animation-heavy custom objects as a core requirement
- Advanced script mod authoring for arbitrary systems
- Cloud collaboration, multi-user projects, project sharing
- Asset marketplace
- Public release management
- In-game automated test playthroughs
- Maxis Match visual style (deferred to v1.5)
- Multi-language localization (English-only in MVP)
- Telemetry or remote logging
- Auto-update mechanism
- Mobile or web clients

---
