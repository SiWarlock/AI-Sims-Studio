# AI Sims Creator — Product Requirements Document (PRD)

## 1. Document Status

- **Project:** AI Sims Creator
- **Document Type:** Product Requirements Document (PRD)
- **Document Version:** 1.0
- **Status:** Draft for review
- **Supersedes:** AI Sims Creator — Project Overview (vision document)
- **Purpose:** Define the product requirements in a form suitable for implementation by engineering and AI coding agents, with all foundational decisions resolved.
- **Intended Audience:** Project owner, maintainer, AI coding agents (primarily Claude Code), future collaborators.
- **Scope:** MVP-first, with forward-looking structure that avoids dead-end implementation decisions and explicitly accommodates known v1.5+ features.
- **Related Documents:**
  - MVP Specification (to follow)
  - Technical Architecture Document (to follow)
  - Architecture Diagrams (to follow)
  - API Specification for internal IPC (to follow)

---

## 2. Purpose of This Document

This PRD translates the product concept into actionable product requirements that can guide design and implementation. It is written to be directly consumable by a coding agent.

This document answers:

- What must be built?
- Who is it for?
- What user problems does it solve?
- What capabilities are required in MVP?
- What is explicitly out of scope?
- What workflows must exist?
- What behaviors, validations, and outputs are required?
- How should success be measured?

This document intentionally defers detailed schema design, implementation sequencing, and architecture to the MVP Specification and Technical Architecture Document.

---

## 3. Product Summary

AI Sims Creator is a desktop-first creator studio for The Sims 4 that enables a non-technical creator to generate, refine, validate, and export themed custom content collections — and selected functional objects — through guided, AI-assisted workflows.

The product supports two creation paths that share a common underlying asset model:

1. **Decorative / Build-Buy Custom Content Pipeline** — generate themed collections of decorative clutter and furniture.
2. **Functional Object Pipeline** — upgrade selected decorative items into supported interactive objects by cloning base-game tuning.

These pipelines share a common internal asset model so that a generated decorative object can be upgraded into a functional object without being recreated.

The product is not a generic chatbot. It is a domain-specific Sims content studio with structured workflows, controlled generation, deterministic validation and build steps, and a creator-friendly UI.

---

## 4. Product Positioning

### 4.1 Core Value Proposition

A Sims creator should be able to describe a themed collection in natural language, receive a coherent set of playable in-game assets, refine them visually, optionally make selected items functional, and export installable content without manually operating the full Sims modding toolchain.

### 4.2 Product Category

AI-assisted creator studio for Sims 4 custom content and selected functional mod generation.

### 4.3 Product Promise

The MVP must prove that a creator can:

- start from a theme prompt,
- generate a coherent collection of decorative and furniture assets,
- review and selectively regenerate assets,
- make a supported generated object functional,
- validate the output,
- and export installable game content that appears correctly in-game.

---

## 5. Users

### 5.1 Primary User — The Creator

**Profile:** Non-technical Sims creator building personal content and world builds.

**Concrete user:** The product owner's girlfriend, who is an experienced Sims builder, prefers Alpha CC styling, uses a Mac, and is non-technical.

**Traits:**

- Understands Sims gameplay, build mode, and the CC ecosystem as a consumer and builder
- Has strong aesthetic judgment and distinct style preferences
- Knows what items she wants in a collection and how she wants them to look
- Does not want to interact with Blender, DBPF internals, tuning XML, S4Studio, or any low-level modding tooling
- Will install the app herself via a standard installer

**Needs:**

- Prompt-driven collection creation
- Visual previews she can trust
- Control over style and collection composition
- Safe, guided functional upgrades
- Reliable exports that actually work in her game
- Auto-install to her Mods folder
- Minimal technical friction throughout

### 5.2 Secondary User — The Administrator / Maintainer

**Profile:** Technical maintainer who authors templates, inspects failures, manages the template library, and keeps the system healthy.

**Concrete user:** The product owner, a technical developer who will use a Windows machine for admin and debugging work.

**Traits:**

- Comfortable with code, XML, Blender, Sims modding tools
- May use external tools (Sims 4 Studio, Mod Constructor, XML Extractor) for template authoring and debugging
- Responsible for growing the template library
- Responsible for fixing the app when something breaks

**Needs:**

- Admin mode accessible from within the app, providing:
  - Template library browser and editor
  - Base-game mesh importer (Tier 2 template management)
  - Build logs, job history, validation detail
  - Reference object browser for inspecting base-game tuning
  - Manual rebuild and diagnostic controls
- Deterministic rebuilds
- Inspectable project state
- Clear error reporting

**Important:** The administrator is not treated as a separate product persona with its own full UX. Admin functionality is a **mode within the same application**, accessible via keyboard shortcut or menu, but hidden from the primary creator flow.

### 5.3 Future Users (Out of Scope for MVP)

The product should not be architected in ways that permanently block:

- Small creator teams (multi-user projects)
- Other non-technical creators beyond the primary user
- Distribution of exports to a wider audience

These are non-requirements for MVP but must not be permanently foreclosed by architectural decisions.

---

## 6. Problem Statement

Current Sims 4 custom content creation workflows are fragmented, technical, and inconsistent. Creators must combine multiple tools (Blender, S4Studio, image editors, sometimes XML editors) and execute manual steps to produce even simple custom content, and more for functional objects.

This creates the following product problems:

1. **Technical barrier** — game-savvy creators are blocked by technical implementation details.
2. **Workflow fragmentation** — multiple tools, file formats, and manual steps.
3. **Low throughput** — themed collections take significant time to produce and maintain.
4. **Low reuse** — decorative objects and functional objects are typically separate efforts even when they share shape.
5. **Quality inconsistency** — hand-assembled or loosely-generated content may not be game-ready or stylistically coherent.
6. **Patch fragility** — exported content may break as the game evolves, with no clear repair path.

---

## 7. Product Goals

### 7.1 Primary Goals

1. Reduce technical friction for Sims content creation to near-zero for the primary creator.
2. Enable automatic generation of coherent object collections from natural language prompts.
3. Support generated objects that are playable in-game as Build/Buy content.
4. Support promoting selected generated objects into supported functional objects.
5. Provide visual review and iterative refinement without forcing the user into external tools.
6. Produce reliable, installable exports with validation.
7. Provide auto-install to the user's Mods folder.

### 7.2 Secondary Goals

1. Provide admin mode capable of diagnostics and template library management.
2. Support future growth into richer content categories and styles.
3. Enable deterministic rebuilds and a future patch-repair workflow.
4. Keep creator UX simple while preserving advanced control layers under admin mode.

---

## 8. Non-Goals

The MVP must not attempt to solve all possible Sims creation problems.

Out of scope for MVP:

- Full arbitrary mod generation from any prompt
- Fully custom animation generation
- Create-A-Sim (CAS) content of any kind
- Broad script-heavy gameplay overhauls
- Multi-user collaboration
- Public marketplace/distribution automation
- Plugin ecosystem
- Every possible Build/Buy object type
- AI-generated novel 3D meshes (MVP uses a template library)
- Automated in-game test playthroughs
- Telemetry or crash reporting to remote servers
- Auto-update infrastructure
- Localization beyond English
- Maxis Match visual style (architected for, shipped post-MVP)

The MVP must focus on a constrained, reliable path.

---

## 9. Product Thesis

The correct product approach is **AI-assisted, schema-driven, template-based, and deterministic where required**.

The system must not rely on an unconstrained frontier model directly controlling external tools or generating arbitrary 3D geometry.

Instead:

- **AI is used for planning, ideation, texture generation, metadata drafting, and tuning value suggestions.**
- **Structured domain schemas represent collections, items, templates, texture zones, functional overlays, and archetypes.**
- **A curated template library provides the 3D geometry foundation.** AI never generates meshes; it selects and styles them.
- **Deterministic code assembles textured meshes, renders thumbnails, clones base-game tuning, and packages DBPF files.**
- **Validation gates ensure output quality before export.**

This is a product requirement, not only an implementation preference. The value proposition depends on AI contributions being channeled through reliable deterministic steps.

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

## 11. Product Principles

1. **Prompt-driven but not uncontrolled.** User intent is captured as prompts, but every generation runs through structured schemas and deterministic assembly.
2. **Collection-first, single-item-supported.** The primary unit of work is a themed collection, but a collection of one is a legitimate use case.
3. **One asset, multiple outputs.** A generated decorative object can be upgraded to functional without reconstruction.
4. **Reviewable before export.** Every item is previewable, every swatch inspectable, every piece of metadata editable.
5. **Structured under the hood, simple on the surface.** Schemas are rich; the creator UI is clean.
6. **Deterministic where game constraints matter.** Packaging, tuning cloning, and validation are not AI-driven.
7. **Progressive disclosure for advanced users.** Admin mode exposes depth without cluttering the primary flow.
8. **Optimize for creator trust, not AI novelty.** The product must be honest about what it can and cannot do.
9. **Template library is the foundation.** Visual quality and variety scale through the template library, not through per-item AI geometry generation.
10. **Style is a first-class property of a collection.** Every collection picks a visual style; all items in it inherit that style.

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

## 14. Supported Content Categories and Archetypes for MVP

### 14.1 Template Primitives (Tier 1)

The MVP ships with a curated library of approximately 15–18 template primitives. Exact count and roster is defined in the MVP Specification.

Primitives are organized by shape class, not by specific object name.

**Decor and clutter primitives (target ~10):**

- Cylindrical small tabletop (vases, candles, small lamps, lava lamps, mugs as decor)
- Cylindrical tall floor (floor lamps, plant stands, coat racks)
- Boxy electronic small tabletop (CD players, radios, small appliances, retro tech)
- Boxy electronic medium tabletop (laptops, small TVs, microwaves)
- Rectangular wall flat (mirrors, paintings, posters, wall clocks)
- Rectangular wall deep / shelf (wall cabinets, shadow boxes, floating shelves)
- Organic soft tabletop (plush toys, fabric piles, pillow clusters as decor)
- Planar floor rug
- Stacked low tabletop (books, magazines, trays)
- Thin tall tabletop (bottles, slim vases, statues)

**Furniture primitives (target ~8):**

- Single-seat upholstered (armchair)
- Multi-seat upholstered (sofa, loveseat)
- Dining chair (hard-seated chair)
- Bed single
- Bed double
- Low table (coffee, side)
- Standard table (dining, desk)
- Tall storage (bookshelf, dresser, armoire — height/width variations)

The MVP Specification will confirm the final list. Templates can be added to the library post-MVP without architectural changes.

### 14.2 Tier 2 — User-Imported Templates

Admin mode includes an importer that reads base-game meshes from the user's Sims 4 installation and registers them as Tier 2 templates. Tier 2 templates:

- Have auto-extracted metadata (dimensions, slot data, footprint, base-game category)
- Do not require full texture-zone or archetype schemas to be usable
- Can be used in decorative-only projects immediately
- Can be promoted to Tier 1 by authoring their full schema in admin mode

### 14.3 Functional Archetypes

The MVP supports the following functional archetypes. Each archetype corresponds to a base-game reference object that will be cloned for tuning:

1. **Light on/off archetype** — e.g., lava lamp. Reference object: base-game floor/table lamp. Supports on/off state, light color, emissive region.
2. **Audio device archetype** — e.g., CD player. Reference object: base-game cheap stereo. Supports play/pause, basic interactions.
3. **Mirror archetype** — e.g., funky mirror. Reference object: base-game wall mirror. Supports "Practice Speech," "Check Appearance," and similar mirror interactions.
4. **Moodlet emitter archetype** — e.g., decor item that emits a mood effect. Reference object: base-game decor object with broadcaster or buff emission. Supports user-selectable moodlet type and duration.

These four archetypes are the complete MVP set. Additional archetypes (e.g., computer archetype) are explicitly deferred to post-MVP.

The app must never imply support for archetypes beyond this list.

---

## 15. Visual Style Strategy

### 15.1 Style Concept

Sims 4 custom content generally falls into two visual styles:

- **Maxis Match** — stylized, cartoony, painted-look textures matching the base-game aesthetic
- **Alpha CC** — photorealistic textures, higher geometric detail, real-material look

The MVP defines a third working target:

- **Semi-Alpha** — moderate poly counts (1500–3000), high-resolution textures (2K diffuse, normal, specular), realistic materials, but without the most expensive topology work that full Alpha demands. This is where modern CC creators like Felixandre and Harrie often sit.

### 15.2 MVP Commitment

- MVP ships **semi-Alpha as the only available style**.
- The architecture supports Maxis Match as a future addition (schemas, pipelines, and UI all accept a style parameter; only the MM implementation is deferred).
- Every collection has a `style_preference` attribute. In MVP, this attribute always resolves to semi-Alpha. In v1.5+, the UI will present a style picker at collection creation.
- Style is set at collection creation and immutable thereafter.

### 15.3 Visual Quality Requirements

- Semi-Alpha textures must look credibly realistic at normal in-game camera distance
- Material maps (diffuse, normal, specular) must be coordinated and visually consistent within a swatch
- Swatches within an item must feel like variations of the same object
- Items within a collection must feel stylistically coherent

---

## 16. Template Library Model

### 16.1 Two-Tier Architecture

The template library is organized into two tiers.

#### 16.1.1 Tier 1 — Curated Primitives

- Hand-authored or carefully curated templates with full schema
- Ship with the app
- Reasoned over by the AI during collection planning
- Declare: shape class, dimension ranges, texture zones, footprint type, compatible archetypes, example objects

#### 16.1.2 Tier 2 — User-Imported Base-Game Meshes

- Imported via admin mode from the user's local Sims 4 installation
- Auto-extracted metadata only
- Usable for decorative-only projects immediately
- Can be promoted to Tier 1 by authoring the additional schema in admin mode

### 16.2 Template Authoring Path

- Tier 2 → Tier 1 promotion is an admin-mode workflow
- New Tier 1 templates can also be authored from scratch in Blender following a documented standard (see MVP Specification and TAD)
- The app must never break if a Tier 2 template is referenced and its schema is incomplete; it must gracefully degrade to decorative-only use of that template

### 16.3 Why Templates, Not AI Mesh Generation

Template primitives provide:

- **Predictable Sims-correct geometry** (correct footprints, slot data, poly budget)
- **Legal clarity** for functional items cloned from base-game references
- **Quality consistency** that AI mesh generation cannot yet reliably provide
- **Deterministic performance** independent of model availability

AI mesh generation may be revisited as a v2+ feature. It is not a v1 option.

### 16.4 Shape Fidelity Honesty

The app must be clear with the user when a requested item has a poor template match. See FR-013 and FR-080.

---

## 17. User Stories

### 17.1 Creator Stories

1. As a creator, I want to start a new collection project from a simple prompt.
2. As a creator, I want to create a single-item project without being forced into a collection.
3. As a creator, I want the system to propose a coherent item list based on my prompt.
4. As a creator, I want to review and modify the proposed item list before generation.
5. As a creator, I want the system to generate usable decorative objects from the plan.
6. As a creator, I want previews, swatches, and metadata to feel consistent across the collection.
7. As a creator, I want to regenerate or refine one item without restarting the project.
8. As a creator, I want to exclude items from export without deleting them.
9. As a creator, I want to edit item names, descriptions, tags, prices, and categories.
10. As a creator, I want to assign items to my own custom Build/Buy catalog filter if I choose.
11. As a creator, I want to mark one item as functional and upgrade it through a guided flow.
12. As a creator, I want the app to warn me when a requested item won't match any template well, and let me proceed or skip.
13. As a creator, I want the app to auto-install my exports to the correct Mods folder.
14. As a creator, I want to verify in-game that my items appear correctly and record that verification.
15. As a creator, I want to reopen a project and continue where I left off.

### 17.2 Administrator Stories

1. As the administrator, I want to inspect generation and build logs.
2. As the administrator, I want to view job history and artifact references.
3. As the administrator, I want to browse the template library and inspect each template's schema.
4. As the administrator, I want to import base-game meshes as Tier 2 templates.
5. As the administrator, I want to promote Tier 2 templates to Tier 1 by authoring their schema.
6. As the administrator, I want to rerun builds deterministically from saved project state.
7. As the administrator, I want to browse base-game reference objects for inspection.
8. As the administrator, I want to access error details and stack traces when something fails.

### 17.3 UX Stories

1. As a non-technical user, I want the app to guide me step-by-step.
2. As a user, I want to see previews before exporting.
3. As a user, I want warnings explained in plain language.
4. As a user, I never want to interact with raw package internals, tuning XML, or Blender.
5. As an administrator, I want advanced details available without cluttering the default UX.

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

## 37. Open Questions Deferred to MVP Specification and TAD

These are intentionally deferred.

1. Exact Tier 1 template roster and count
2. Exact mesh format and authoring standard for Tier 1 templates
3. Exact Pydantic/TypeScript schema definitions
4. Exact project storage layout under the project folder
5. Exact model selections (specific Replicate-hosted image model, etc.)
6. DBPF library choice (evaluate during POC)
7. Dependency specifics for the Python sidecar
8. Pipeline concurrency and retry policies
9. Auto-install conflict handling (overwrite? rename?)
10. User verification flow exact UI and data capture

These belong in the MVP Specification and Technical Architecture Document.

---

## 38. Recommended Next Documents

After this PRD is reviewed and approved, the following documents follow in sequence.

1. **MVP Specification**
   - Exact feature cut for the first build
   - Implementation phases and sequencing
   - Milestone zero (texturing POC) detailed plan
   - Supported template roster
   - Supported archetype-to-reference-object mapping
   - Acceptance tests
   - Task breakdowns for Claude Code consumption

2. **Technical Architecture Document (TAD)**
   - Component architecture
   - Frontend / Python sidecar split and IPC
   - Job orchestration
   - Internal schemas (Pydantic and TypeScript)
   - Project storage layout
   - External integrations (Replicate, Anthropic, local Sims install, Blender)
   - DBPF packaging pipeline
   - Tuning clone pipeline
   - Validation pipeline
   - Auto-install mechanism
   - Platform-specific details

3. **Architecture Diagrams (standalone document)**
   - Container diagram (frontend, sidecar, external deps)
   - Pipeline sequence diagram (prompt → plan → generation → assembly → validation → export → install)
   - Data model diagram
   - Admin mode architecture

4. **Internal API Specification**
   - Tauri ↔ Python sidecar IPC contract
   - Request/response schemas
   - Job lifecycle events

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
