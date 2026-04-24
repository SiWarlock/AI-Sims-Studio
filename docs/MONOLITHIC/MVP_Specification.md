# AI Sims Creator — MVP Specification

## 1. Document Status

- **Project:** AI Sims Creator
- **Document Type:** MVP Specification
- **Document Version:** 1.0
- **Status:** Draft for review
- **Depends On:** AI Sims Creator PRD v1.0 (approved)
- **Precedes:** Technical Architecture Document, Architecture Diagrams, API Specification
- **Purpose:** Define exactly what ships in the first version of AI Sims Creator and in what order, with tasks scoped for Claude Code consumption.
- **Intended Audience:** Project owner, maintainer, Claude Code (primary implementation agent).

---

## 2. Purpose of This Document

This MVP Specification translates the PRD into an executable plan. It answers:

- What exactly ships in MVP v1.0?
- What is explicitly not shipping in MVP v1.0 even though the PRD allows it?
- In what order is the work done?
- What gates separate one phase from the next?
- What tasks does each phase contain, scoped for a coding agent to execute?
- What must be tested and at what level?
- What decisions are deferred to POC time rather than pre-committed?
- What documentation deliverables are produced alongside the code?

This document does not define technical architecture (TAD), data schemas (TAD), diagrams (Architecture Diagrams doc), or internal IPC contracts (API Specification). It references them where needed.

---

## 3. MVP Definition

### 3.1 What MVP v1.0 Is

MVP v1.0 is a cross-platform desktop application (macOS and Windows) that enables a non-technical creator to:

1. Create a new project from a natural language prompt describing a themed collection (or a single-item project).
2. Receive a structured, editable collection plan with items matched to template primitives.
3. Generate decorative Build/Buy assets from the plan using a curated template library and AI-driven semi-Alpha texture generation.
4. Review items on a collection board and in detail views, with per-item regenerate, replace, and exclude controls.
5. Upgrade selected items to supported functional objects using base-game tuning cloning for four archetypes.
6. Validate the project structurally.
7. Export as `.package` files and auto-install to the user's Sims 4 Mods folder.
8. Optionally confirm in-game that items appear correctly.

Administrator mode within the same application provides template library management, base-game mesh import, logs, job history, and reference object inspection.

### 3.2 What MVP v1.0 Is Not

See §5 for the explicit deferrals list.

---

## 4. Implementation Phases

MVP v1.0 is delivered in eight phases, sequenced to minimize rework and to surface the highest-risk piece (texturing quality) as early as possible.

No time estimates are included. Phases are gated by completion of their acceptance criteria, not by calendar.

### 4.1 Phase Overview

1. **Phase 0 — Foundation**
   App shell, project storage, platform detection. No AI, no templates.
2. **Phase 1 — Milestone Zero: Texturing Proof-of-Concept**
   One template, one prompt, full pipeline to in-game verification. This is the quality gate that de-risks the entire product.
3. **Phase 2 — Template Library**
   Author all 19 Tier 1 templates with full schemas. Build template loader.
4. **Phase 3 — Decorative Generation Pipeline**
   Collection planning, per-item spec generation, full texture pipeline, thumbnail rendering, metadata generation, collection board UI, item detail UI.
5. **Phase 4 — Validation, Export, and Auto-Install**
   Structural validation, export screen, DBPF build pipeline, Mods folder auto-install.
6. **Phase 5 — Functional Overlay**
   Archetype configuration, tuning extraction, clone pipeline, functional variant packaging.
7. **Phase 6 — Admin Mode**
   Template browser, base-game importer, Tier 2 promotion editor, logs viewer, job history, reference object browser.
8. **Phase 7 — Cross-Platform Hardening and Polish**
   Windows parity, path handling edge cases, Blender discovery, verification flow polish, documentation.

### 4.2 Phase Gating

Each phase has explicit completion criteria. A phase is complete only when all its acceptance criteria pass. The next phase does not begin until the prior phase is complete.

Exception: Phase 1 (Milestone Zero) is a hard gate. If Phase 1 fails to produce a convincing in-game result, the MVP must pause for approach revision before Phase 2 begins.

---

## 5. Explicit MVP Deferrals

The PRD permits these capabilities but they do not ship in MVP v1.0. They are deferred to v1.5 or later.

- **Maxis Match visual style.** Architecture supports a style parameter; UI ships locked to semi-Alpha.
- **Functional archetypes beyond the MVP four.** No computer, no stove, no novel archetypes. Only light on/off, audio device, mirror, moodlet emitter.
- **Template authoring via the UI.** Templates are either Tier 1 (shipped or authored in Blender following documented standards) or Tier 2 (imported from base-game). No in-app Blender substitute.
- **Project import/export as portable archives.** Project folders can be copy-pasted manually; no explicit archive format with versioning, signing, or import validation.
- **Batch operations across multiple projects.** One project at a time.
- **Multi-user collaboration.** Single-user local only.
- **Public distribution or marketplace integration.** No upload, no sharing, no metadata tied to public creator IDs.
- **CAS content of any kind.** No Sims, no clothing, no hair, no makeup.
- **Animation authoring.** No custom animations.
- **Script mods beyond tuning clones.** No Python script modding, no custom gameplay systems.
- **Localization beyond English.** All UI strings and generated metadata are English-only.
- **Telemetry or remote logging.** No outbound network traffic other than required AI API calls.
- **Auto-update mechanism.** Manual builds shipped by the maintainer.
- **Mobile or web clients.** Desktop only.
- **AI-generated mesh geometry.** All geometry comes from templates. Evaluated for v2+.

---

## 6. Template Roster for MVP v1.0

MVP ships with **19 Tier 1 template primitives** organized as follows.

### 6.1 Decor and Clutter (11)

1. `cylindrical_small_tabletop` — lava lamp, vase, candle, small lamp body, goblet, decorative bottle
2. `cylindrical_tall_floor` — floor lamp, plant stand, coat rack, tall vase
3. `boxy_electronic_small_tabletop` — CD player, radio, alarm clock, retro tech, fax machine analog
4. `boxy_electronic_medium_tabletop` — laptop, small TV, microwave, speaker
5. `rectangular_wall_flat` — mirror, painting, poster, wall clock, flat art
6. `rectangular_wall_shelf` — floating shelf, wall cabinet, shadow box
7. `organic_soft_tabletop` — plush toy, pillow-as-decor, fabric pile
8. `planar_floor_rug` — rug, mat
9. `stacked_low_tabletop` — book stack, magazine stack, tray of small items
10. `thin_tall_tabletop` — bottle, slim vase, small statue
11. `rectangular_floor_standing` — trash can, laundry basket, pet bed, small chest, short cabinet

### 6.2 Furniture (8)

12. `seat_single_upholstered` — armchair
13. `seat_multi_upholstered` — sofa, loveseat
14. `seat_dining_hard` — dining chair, desk chair
15. `bed_single` — twin bed
16. `bed_double` — double bed
17. `table_low` — coffee table, side table
18. `table_standard` — dining table, desk
19. `storage_tall` — bookshelf, dresser, armoire

### 6.3 Template Schema

Each Tier 1 template declares:

- Unique template ID
- Shape class
- Dimension ranges (min/max for each axis)
- Footprint type (Sims tile footprint convention)
- Texture zones (named regions with approximate UV extent)
- Compatible functional archetypes (subset of the four MVP archetypes)
- Example object types (for AI matching and user-facing descriptions)
- Authoring notes (for the maintainer)

Exact field-level schema is defined in the TAD.

### 6.4 Template Authoring Standard

Each Tier 1 template mesh must satisfy:

- Polygon count in the 1500–3000 range
- Clean UV unwrap with no overlapping islands
- Texture zones explicitly marked and labeled
- Proper Sims footprint and slot data where applicable
- Exported as `.glb` for the canonical library format
- Rendered at 2K diffuse resolution in thumbnail tests
- Passes visual inspection at normal in-game camera distance

The Tier 1 library is the highest-investment artifact in the MVP. Each template is authored once and used indefinitely.

---

## 7. Functional Archetype Reference Object Mapping

The four MVP archetypes clone tuning from specific base-game reference objects. Exact object IDs are identified during Phase 1 POC work against a live Sims 4 install and locked in the TAD.

### 7.1 Light On/Off

- **Reference target:** A simple base-game table lamp or floor lamp with clean on/off state and swappable light color.
- **Selection criteria:** Minimal interaction graph, single-state toggle, color parameter exposed in tuning.
- **Example user creations:** lava lamp, novelty lamp, mood light, decorative sconce.
- **Compatible templates:** `cylindrical_small_tabletop`, `cylindrical_tall_floor`, `boxy_electronic_small_tabletop`.

### 7.2 Audio Device

- **Reference target:** The cheapest base-game stereo with basic play/pause interactions.
- **Selection criteria:** Simplest interaction graph, no skill gate requirements, minimal tuning dependencies.
- **Example user creations:** CD player, retro radio, boombox, record player.
- **Compatible templates:** `boxy_electronic_small_tabletop`, `boxy_electronic_medium_tabletop`.

### 7.3 Mirror

- **Reference target:** A base-game wall mirror supporting the mirror interaction set.
- **Selection criteria:** Exposes Check Appearance, Practice Speech, and standard mirror interactions; cleanest tuning footprint.
- **Example user creations:** funky mirror, themed wall mirror, vanity mirror.
- **Compatible templates:** `rectangular_wall_flat`.

### 7.4 Moodlet Emitter

- **Reference target:** A base-game decor object with buff broadcaster emission.
- **Selection criteria:** Clean broadcaster pattern, user-configurable moodlet reference, minimal additional gameplay effects.
- **Example user creations:** inspirational decor, themed mood emitter, ambient enhancer.
- **Compatible templates:** Most decor primitives where a buff emission makes sense contextually.

### 7.5 Archetype Configuration Parameters

Each archetype exposes a minimal set of user-configurable values:

- **Light on/off:** light color, intensity level (low/medium/high), always-on option.
- **Audio device:** music genre category (from base-game genres), default volume.
- **Mirror:** none (behavior inherited from reference).
- **Moodlet emitter:** moodlet type (selected from a curated list of safe base-game moodlets), duration, emission radius.

These are the only configurable parameters exposed in MVP. Additional tuning values inherited from the reference object remain at reference defaults.

---

## 8. Decisions Deferred to Phase 1 (POC)

The following decisions cannot be pre-committed without hands-on work against a live Sims 4 install or a live Replicate integration. Phase 1 must resolve them before Phase 2 begins.

- **D-1 — DBPF library choice.** Evaluate `sims4-tools` (community Python) vs rolling a custom thin wrapper on the documented DBPF format spec. Decision locked into TAD at end of Phase 1.
- **D-2 — Primary image generation model.** Evaluate Flux 1.1 Pro, Flux Dev, and any material-specific alternatives (MatForger-class, Materialize-class) available on Replicate. Quality of diffuse + coordinated normal/specular output is the selection criterion.
- **D-3 — Normal and specular map derivation strategy.** Either native multi-map generation from the image model, or post-process inference from diffuse via a height-map step. Decision depends on D-2 outcomes.
- **D-4 — Exact base-game reference object IDs.** For each of the four archetypes, identify the exact resource IDs in the user's Sims 4 install that will be cloned. Locked into TAD.
- **D-5 — Blender headless render recipe.** Settings for lighting, camera angle, and material pipeline that produce thumbnails matching in-game appearance. Locked as template authoring guidance.
- **D-6 — Texture resolution policy.** 2K diffuse is the baseline; confirm performance is acceptable and artifacts are not visible at in-game camera distance. Adjust if needed.

---

## 9. Phase Task Breakdown

Tasks below are scoped for Claude Code consumption. Each task includes outputs, dependencies, and acceptance criteria. Claude Code is expected to further decompose tasks into subtasks at implementation time.

Tasks are numbered `{phase}.{task}` for cross-reference.

---

### 9.1 Phase 0 — Foundation

**Phase goal:** Establish the app shell, project storage, platform detection, and basic UI scaffolding. No AI integration, no templates, no generation.

**Phase acceptance gate:** A user can launch the app on Mac or Windows, create a named project, close the app, reopen the app, and see the project in the recent projects list. The app detects the Sims 4 install and reports its path. No other functionality is required.

#### Tasks

**0.1 — Project repo scaffolding and toolchain setup**
Initialize the repository with Tauri v2 + React frontend + Python sidecar structure. Configure build scripts for both macOS and Windows targets. Set up linting, formatting, and testing scaffolding for both TypeScript and Python.

*Outputs:* Working repo with `npm run dev` launching the app on both platforms, `cargo tauri build` producing platform binaries, pytest and jest test runners functional.
*Dependencies:* None.
*Acceptance:* Repo clones cleanly on both Mac and Windows, dev mode launches successfully, test runners execute (even if no tests yet).

**0.2 — Tauri ↔ Python sidecar IPC foundation**
Establish the communication channel between the Tauri frontend and the Python sidecar process. Choose and implement the IPC mechanism (stdio JSON-RPC recommended). The sidecar launches when the app launches and shuts down cleanly on app exit.

*Outputs:* A working ping/pong from frontend to sidecar returning a response. Lifecycle management ensures no orphaned Python processes.
*Dependencies:* 0.1.
*Acceptance:* Frontend can call a sidecar function and receive a typed response. Sidecar terminates when app closes on both Mac and Windows.

**0.3 — Platform detection and path resolution**
Implement OS detection and platform-specific path resolution for: user home directory, app data directory, logs directory, projects root directory. Document the platform-specific conventions used.

*Outputs:* A Python module that returns correct paths for both Mac and Windows. All paths respect platform conventions (`~/Library/Application Support/AISimsCreator/` on Mac, `%APPDATA%\AISimsCreator\` on Windows).
*Dependencies:* 0.2.
*Acceptance:* Running the module on Mac produces Mac-standard paths; on Windows produces Windows-standard paths. Directories are created if missing.

**0.4 — Sims 4 install detection**
Auto-detect the user's Sims 4 installation on both platforms. Handle standard Origin / EA App install locations. Surface a clear error if not found, with manual override option.

*Outputs:* A module that returns the Sims 4 install path, data directory path, and Mods folder path. Returns structured error when not found.
*Dependencies:* 0.3.
*Acceptance:* On a Mac with standard Sims install, returns the correct paths. Same on Windows. Handles not-found gracefully.

**0.5 — Project storage layer (SQLite + file tree)**
Implement the project storage layer. Each project lives in a folder under the projects root. Folder contains a SQLite database for metadata and a structured subtree for assets. Schema is defined in the TAD.

*Outputs:* Python module exposing project CRUD: create, open, save, list recent, delete. SQLite schema migrations handled.
*Dependencies:* 0.3.
*Acceptance:* A project can be created, closed, reopened, and its metadata persisted. Corruption of one project does not affect others.

**0.6 — Application shell UI**
Build the Tauri + React application shell: main window, navigation structure, home screen with recent projects, new project button, project open action. No project-specific functionality yet.

*Outputs:* App launches to a home screen showing recent projects (empty initially). Clicking "New Project" opens a named prompt and creates a project. Projects appear in the list. Clicking a project opens a placeholder project view.
*Dependencies:* 0.2, 0.5.
*Acceptance:* UI renders correctly on both Mac and Windows. Navigation between home and project view works.

**0.7 — Local logging infrastructure**
Implement local logging for both the frontend and sidecar. Logs written to platform-standard paths. Per-session log files with timestamps. Configurable log levels.

*Outputs:* Python logger writing to `~/Library/Logs/AISimsCreator/` on Mac and `%APPDATA%\AISimsCreator\logs\` on Windows. Frontend errors captured and forwarded to the sidecar for logging.
*Dependencies:* 0.3.
*Acceptance:* Log files are created per session, contain timestamped entries from both frontend and sidecar, and are readable via standard text tools.

**0.8 — Blender discovery**
Detect whether Blender is installed on the user's system. On first launch if missing, prompt the user with a download link and prerequisite explanation. Remember the path once discovered.

*Outputs:* A module that returns the Blender executable path. First-launch flow that handles missing Blender cleanly.
*Dependencies:* 0.3.
*Acceptance:* On a system with Blender installed in a standard location, discovery succeeds. On a system without Blender, the user is clearly informed with a download link. Path can be manually overridden via settings.

---

### 9.2 Phase 1 — Milestone Zero: Texturing Proof-of-Concept

**Phase goal:** Prove the end-to-end pipeline from "user prompt" to "item appears correctly in Sims 4 Build/Buy catalog" using one template, one hardcoded prompt scenario, and the simplest possible implementation of each stage.

**Phase acceptance gate:** A maintainer can run the POC end-to-end and visually confirm a Y2K-themed lava lamp appears in the Build/Buy catalog of Sims 4, is placeable in the world, renders correctly, and matches the thumbnail shown at export time. The maintainer and primary user both confirm the visual quality meets the bar for full MVP commitment. If this gate fails, approach revision is required before Phase 2.

#### Tasks

**1.1 — Single template preparation**
Author or extract a single lava-lamp-shaped mesh following the Tier 1 template authoring standard, including clean UVs, three texture zones (base, vessel, cap), Sims tabletop footprint, and 2K-ready UV layout.

*Outputs:* One `.glb` file for `cylindrical_small_tabletop` with all required metadata.
*Dependencies:* None (can proceed in parallel with Phase 0 late tasks).
*Acceptance:* Template loads in Blender cleanly, renders correctly, and all three texture zones are addressable by UV bounds.

**1.2 — Replicate API integration**
Integrate with Replicate for image generation. Authenticate, submit requests, poll for completion, handle retries and errors.

*Outputs:* Python client module with a typed interface for submitting image generation jobs and retrieving results.
*Dependencies:* 0.2.
*Acceptance:* A test call produces an image for a simple prompt. Error conditions (auth failure, timeout, content policy rejection) are handled distinctly.

**1.3 — Image model evaluation (D-2, D-3)**
Evaluate candidate image models on Replicate for semi-Alpha material quality. Test: Flux 1.1 Pro, Flux Dev, any material-specific alternatives identified. Produce sample textures for the lava lamp's three zones using each candidate. Compare visual quality.

*Outputs:* Side-by-side comparison report with decisions D-2 and D-3 resolved.
*Dependencies:* 1.2.
*Acceptance:* A primary image model is selected. Normal and specular map strategy (native multi-map vs post-process derivation) is decided and documented.

**1.4 — Texture generation pipeline (POC scope)**
Build a minimal pipeline that, given a prompt and the lava lamp template's texture zones, generates diffuse, normal, and specular maps per zone using the selected model.

*Outputs:* Python function that accepts a prompt string and returns a complete texture set for the lava lamp template.
*Dependencies:* 1.1, 1.3.
*Acceptance:* Running with a Y2K prompt produces three coordinated texture maps per zone. Maps are visually consistent and at target resolution.

**1.5 — Blender headless render setup (D-5)**
Set up a headless Blender Python script that loads a template `.glb`, applies a texture set, and renders a thumbnail. Determine lighting, camera angle, and material settings that match in-game appearance.

*Outputs:* A Blender Python script invoked from the sidecar via subprocess that produces a PNG thumbnail. Decision D-5 locked.
*Dependencies:* 1.1, 1.4, 0.8.
*Acceptance:* Running the script produces a thumbnail PNG that visually matches in-game appearance.

**1.6 — DBPF library evaluation (D-1)**
Evaluate DBPF library options. Test reading and writing `.package` files with `sims4-tools` or equivalent. If no viable library exists, scope the custom implementation.

*Outputs:* Decision D-1 resolved. A working library (external or custom) capable of producing a valid `.package` file containing the resources required for a Build/Buy object.
*Dependencies:* None.
*Acceptance:* A test `.package` containing a known base-game-cloned object opens correctly in the game.

**1.7 — POC `.package` build pipeline**
Assemble a complete `.package` file for the lava lamp: the textured mesh, the thumbnail, the catalog metadata (hardcoded for POC), and a Build/Buy category assignment. Produce a valid DBPF.

*Outputs:* A `.package` file for one Y2K lava lamp.
*Dependencies:* 1.4, 1.5, 1.6.
*Acceptance:* The file validates structurally and contains all expected resources with correct TGI IDs.

**1.8 — Mods folder install for POC**
Copy the generated `.package` to the user's Sims 4 Mods folder.

*Outputs:* The file is installed into the detected Mods folder.
*Dependencies:* 1.7, 0.4.
*Acceptance:* File appears in the Mods folder with correct permissions.

**1.9 — In-game verification**
Maintainer launches Sims 4, verifies the lava lamp appears in the Build/Buy catalog in the expected category, places it in the world, and confirms it matches the thumbnail.

*Outputs:* Written verification notes with screenshots. If verification fails, documented failure modes and next steps.
*Dependencies:* 1.8.
*Acceptance:* Lava lamp appears in-game, is placeable, is visually correct. Both maintainer and primary user confirm visual quality meets MVP bar.

**1.10 — Phase 1 decision freeze**
Lock all decisions resolved during POC (D-1 through D-6) into the TAD. Document any deviations from the pre-Phase 1 assumptions.

*Outputs:* TAD is updated with final decisions. Any approach changes are recorded and approved.
*Dependencies:* 1.9.
*Acceptance:* TAD reflects the resolved decisions and the project is cleared to proceed to Phase 2.

---

### 9.3 Phase 2 — Template Library

**Phase goal:** Author all 19 Tier 1 templates and build the template loader infrastructure. No AI integration in this phase.

**Phase acceptance gate:** All 19 templates exist as `.glb` files with full schemas. The template loader can query them by attribute. Each template renders correctly in Blender and each has been inspected at a placeholder texture for visual correctness.

#### Tasks

**2.1 — Template authoring pipeline**
Document the template authoring standard as a living reference. Set up a workflow for authoring new templates in Blender: topology guidelines, UV unwrapping conventions, texture zone marking, footprint/slot data conventions, `.glb` export settings.

*Outputs:* An authoring guide in the repo documenting every step. A Blender file template with the conventions pre-applied.
*Dependencies:* 1.1, 1.5.
*Acceptance:* Following the guide, a new template can be authored from a base reference without ambiguity.

**2.2 — Tier 1 template authoring: decor primitives (11)**
Author all 11 decor and clutter templates listed in §6.1 following the authoring pipeline. Each template includes geometry, clean UVs, labeled texture zones, and footprint data.

*Outputs:* 11 `.glb` files under the template library.
*Dependencies:* 2.1.
*Acceptance:* Each template renders correctly, each has correct texture zones, each passes the authoring checklist.

**2.3 — Tier 1 template authoring: furniture primitives (8)**
Author all 8 furniture templates listed in §6.2 following the authoring pipeline.

*Outputs:* 8 `.glb` files under the template library.
*Dependencies:* 2.1.
*Acceptance:* Each template renders correctly, each has correct texture zones and slot data, each passes the authoring checklist.

**2.4 — Template schema loader**
Build a Python module that loads all templates from disk, parses their metadata, validates schemas, and exposes a query API (by shape class, dimension range, archetype compatibility, etc.).

*Outputs:* A template registry with a typed query API.
*Dependencies:* 2.2, 2.3.
*Acceptance:* All 19 templates load successfully. Queries return correct subsets. Schema validation catches malformed templates.

**2.5 — Template visual inspection harness**
Build a simple internal tool that renders each template with a neutral placeholder texture and outputs thumbnails for manual review. This is a maintainer-facing sanity check tool.

*Outputs:* A script that produces a thumbnail gallery of all 19 templates.
*Dependencies:* 2.4, 1.5.
*Acceptance:* Gallery is generated and all templates look correct.

---

### 9.4 Phase 3 — Decorative Generation Pipeline

**Phase goal:** Build the full decorative generation flow: collection planning, per-item spec generation, texture generation at scale, thumbnail rendering, metadata generation, and the creator-facing UI to review and iterate.

**Phase acceptance gate:** A user can enter a prompt, receive a plan, edit the plan, generate a complete multi-item collection, review items on a collection board, open item detail views, regenerate items and swatches, and edit metadata. No export or functional capability yet.

#### Tasks

**3.1 — Anthropic API integration**
Integrate with the Anthropic API for Claude Sonnet 4.6 and Haiku 4.5. Authenticate, submit structured output requests, handle retries and errors. Support tool use for structured response enforcement.

*Outputs:* Python client with typed interfaces for the planning and metadata stages.
*Dependencies:* 0.2.
*Acceptance:* Test calls produce structured responses. Errors are handled distinctly.

**3.2 — Collection planning stage**
Implement the planning stage. Takes user prompt + desired count + template registry. Produces a structured plan: theme summary, item list, template match per item with confidence score, style attributes, palette direction.

*Outputs:* Python function returning a typed `CollectionPlan` object.
*Dependencies:* 3.1, 2.4.
*Acceptance:* For a Y2K bedroom prompt with 6 items, produces a coherent plan with sensible template matches. Low-confidence matches are flagged. User can request fewer or more items.

**3.3 — Per-item spec generation stage**
Implement the per-item spec stage. Takes a plan item + its template schema + collection-level style context. Produces a typed `ItemSpec`: per-zone texture prompts, item name, description, tags, price suggestion, Build/Buy category, optional custom catalog filter tag.

*Outputs:* Python function returning a typed `ItemSpec` object.
*Dependencies:* 3.1, 2.4.
*Acceptance:* For a planned Y2K lava lamp, produces per-zone prompts that feel appropriately coordinated, plus sensible metadata.

**3.4 — Per-item texture generation pipeline**
Build the pipeline that takes an item spec plus its template's texture-zone schema and produces coordinated diffuse, normal, and specular texture maps per zone, per swatch, via Replicate.

*Outputs:* Async Python function `generate_textures(item_spec, template, swatch_count) -> TextureSet` returning a fully populated TextureSet. Includes retry logic and per-zone prompt construction.
*Dependencies:* 1.4, 3.3.
*Acceptance:* Generates a 3-swatch texture set for any template given an item spec. Maps per swatch are visually coordinated.

**3.5 — Thumbnail rendering pipeline**
Generalize the Phase 1 thumbnail pipeline to work for all templates with all texture sets. Render deterministic thumbnails per item per swatch.

*Outputs:* Python function that accepts a template + texture set and returns a thumbnail PNG.
*Dependencies:* 1.5, 2.4, 3.4.
*Acceptance:* Produces thumbnails for every template type. Thumbnails match the in-game appearance they will have once exported.

**3.6 — Collection orchestration**
Build the orchestrator that takes an approved plan and executes full generation: per-item spec generation, per-item texture generation with N swatches, thumbnail rendering, metadata finalization. Handles failures per item without aborting the whole collection.

*Outputs:* Async orchestrator with progress events surfaced to the UI.
*Dependencies:* 3.2, 3.3, 3.4, 3.5.
*Acceptance:* Given an approved plan, generates all items. Per-item failures are isolated and reported.

**3.7 — Collection plan review UI**
Build the UI surface where the user reviews the proposed plan, edits the item list (add, remove, reorder, rename intent), sees template match confidence per item, resolves low-confidence items (proceed / skip / rephrase), and triggers generation.

*Outputs:* React screens with full interaction.
*Dependencies:* 3.2, 0.6.
*Acceptance:* User can reach this screen from the new-project flow, make edits, and trigger generation.

**3.8 — Collection board UI**
Build the collection board: grid of items with thumbnails, status indicators, include/exclude toggles, functional-candidate indicators, project-level actions. Updates live as generation progresses.

*Outputs:* React screen with live update via IPC events.
*Dependencies:* 3.6, 0.6.
*Acceptance:* User can see items populate as they generate. Include/exclude toggles work. Clicking an item opens its detail view.

**3.9 — Item detail UI**
Build the item detail view: large preview, swatch list with per-swatch regenerate, metadata view and edit form, regenerate item, replace item, make-functional button (disabled until Phase 5).

*Outputs:* React screen with full editing and regeneration controls.
*Dependencies:* 3.8, 3.6.
*Acceptance:* User can regenerate individual swatches, regenerate the full item, replace the item, and edit metadata fields.

**3.10 — Metadata editing and validation**
Implement metadata editing: name, description, tags, price, Build/Buy category, custom catalog filter tag. Validate edits (name not empty, price in valid range, etc.).

*Outputs:* Editing functionality with client-side and server-side validation.
*Dependencies:* 3.9.
*Acceptance:* Edits persist to project storage. Invalid inputs are rejected clearly.

**3.11 — Progress and status event system**
Implement the event system that surfaces generation progress to the UI in real time. Status transitions per item (planned → generating → generated → needs_review etc.) are reflected immediately.

*Outputs:* Event bus with typed events, subscriptions from UI components.
*Dependencies:* 3.6, 0.2.
*Acceptance:* During generation, the UI shows live progress per item. Errors surface immediately with user-friendly messages.

**3.12 — Style parameter architecture**
Ensure the `style_preference` parameter is threaded through the entire pipeline end-to-end, even though only `semi_alpha` is implemented. Schemas accept it, prompts reference it, future MM can be added by extending handlers without schema changes.

*Outputs:* Every relevant function signature and schema includes `style_preference`. Semi-Alpha is the only implementation path; MM raises a clear "not yet implemented" exception if invoked.
*Dependencies:* 3.3, 3.4.
*Acceptance:* Schema inspection confirms the parameter exists. A maintainer could add MM handlers in v1.5 without altering schemas.

---

### 9.5 Phase 4 — Validation, Export, and Auto-Install

**Phase goal:** Take a reviewed collection and produce validated, installed `.package` files in the user's Mods folder.

**Phase acceptance gate:** A user can export a decorative collection, see validation results, have the `.package` files auto-installed, and receive a clear success/failure report. Exported items appear correctly in Build/Buy in-game.

#### Tasks

**4.1 — Structural validation engine**
Build the validation engine covering: asset completeness (mesh, textures, thumbnail, metadata present), DBPF structural integrity, TGI resource ID consistency, project internal consistency, metadata completeness.

*Outputs:* A validation module returning structured results with severity (error vs warning) and actionable messages.
*Dependencies:* 3.6.
*Acceptance:* Catches known failure modes (missing textures, malformed metadata, duplicate IDs). Differentiates errors from warnings.

**4.2 — DBPF build pipeline (decorative)**
Extend the Phase 1 POC DBPF pipeline to handle all templates and all items in a collection. Produce one `.package` per item (or a grouped `.package` per collection if that is the design decision, locked in TAD).

*Outputs:* Build function that takes a collection and produces the set of `.package` files.
*Dependencies:* 1.7, 3.6.
*Acceptance:* All items in a test collection produce valid `.package` files.

**4.3 — Export summary UI**
Build the export screen: validation summary with user-readable messages, error and warning lists, per-item variant choices (decor-only / functional / both — functional disabled until Phase 5), export trigger.

*Outputs:* React screen with all export controls.
*Dependencies:* 4.1, 3.8.
*Acceptance:* User can see validation results, resolve blockers or exclude problem items, and trigger export.

**4.4 — Mods folder auto-install**
Implement auto-install. After successful DBPF build, copy `.package` files to the detected Mods folder. Handle conflicts (file with same name exists) with clear policy (ask user — overwrite / rename / skip).

*Outputs:* Install function with conflict handling UX.
*Dependencies:* 4.2, 0.4.
*Acceptance:* Files are installed to the correct Mods folder. Conflicts are handled without data loss.

**4.5 — Export result summary**
Build the post-export UI showing what succeeded, what failed, where files were installed, and a link to launch Sims for verification.

*Outputs:* Result screen with clear per-item status.
*Dependencies:* 4.4.
*Acceptance:* User understands exactly what happened.

**4.6 — In-game verification flow**
Build the optional verification step: user launches Sims from a button, manually confirms items appear correctly, marks per-item verification status in the project.

*Outputs:* Verification UI with per-item checkboxes. Verification state persists to the project.
*Dependencies:* 4.5, 0.5.
*Acceptance:* User can record verification. State persists across app restarts.

**4.7 — Deterministic rebuild**
Ensure the export pipeline can be rerun against saved project state with identical results. This validates the rebuild requirement and exposes any non-determinism in the pipeline.

*Outputs:* Rebuild action in the UI and CLI. Produces byte-identical `.package` files given identical input state.
*Dependencies:* 4.2, 0.5.
*Acceptance:* Rebuilding a project produces identical outputs. Test harness verifies byte equality.

---

### 9.6 Phase 5 — Functional Overlay

**Phase goal:** Enable upgrading selected items to functional objects via base-game tuning cloning for the four MVP archetypes.

**Phase acceptance gate:** A user can upgrade at least one item per archetype (lava lamp → light on/off, CD player → audio device, mirror → mirror archetype, decor object → moodlet emitter) and the functional variant works in-game.

#### Tasks

**5.1 — Base-game resource extraction**
Build the module that reads base-game resources from the user's local Sims 4 install. Must extract specific reference objects (meshes, tuning, strings) by ID without modifying the install.

*Outputs:* Read-only extraction module. Given a TGI ID, returns the resource bytes.
*Dependencies:* 0.4, 1.6.
*Acceptance:* Can extract known resources from a standard Sims install. Never writes to the install directory.

**5.2 — Reference object identification (D-4)**
Identify the exact resource IDs for each of the four archetype reference objects. Document in TAD. Build a lookup table mapping archetype to reference object IDs.

*Outputs:* A mapping in the TAD and a corresponding Python constant. Decision D-4 resolved.
*Dependencies:* 5.1.
*Acceptance:* All four archetypes have confirmed reference object IDs that extract correctly.

**5.3 — Tuning XML parser and editor**
Build a tuning XML parser and targeted-edit module. Must parse tuning, identify editable fields relevant to each archetype, and produce modified tuning without breaking references.

*Outputs:* Python module with typed tuning access.
*Dependencies:* 5.1.
*Acceptance:* Can parse reference tuning, modify targeted fields (light color, moodlet reference, etc.), and serialize valid tuning XML.

**5.4 — Archetype handler: light on/off**
Implement the light on/off archetype handler. Given a user item + configured parameters, clone the reference lamp tuning, swap in the user's mesh/textures/strings, apply configured light color and intensity, produce a functional tuning set.

*Outputs:* Handler module that produces tuning ready for packaging.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional lava lamp turns on and off in-game, changes color correctly.

**5.5 — Archetype handler: audio device**
Implement the audio device archetype handler.

*Outputs:* Handler module.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional CD player plays and pauses audio in-game.

**5.6 — Archetype handler: mirror**
Implement the mirror archetype handler.

*Outputs:* Handler module.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional mirror exposes standard mirror interactions in-game.

**5.7 — Archetype handler: moodlet emitter**
Implement the moodlet emitter archetype handler with user-selectable moodlet type, duration, and radius.

*Outputs:* Handler module and curated safe moodlet list.
*Dependencies:* 5.2, 5.3.
*Acceptance:* Functional emitter applies the configured moodlet to nearby Sims with the configured duration.

**5.8 — Functional upgrade wizard UI**
Build the wizard UI: archetype selection (filtered by template compatibility), per-archetype configuration form, summary preview, confirmation step.

*Outputs:* React wizard component.
*Dependencies:* 5.4 through 5.7, 3.9.
*Acceptance:* User can launch the wizard from the item detail view, select and configure an archetype, and see a summary before committing.

**5.9 — Functional variant packaging**
Extend the DBPF build pipeline to produce functional `.package` variants. Support decor-only, functional, or both-variant exports per item.

*Outputs:* Build function handling both variants.
*Dependencies:* 4.2, 5.4 through 5.7.
*Acceptance:* Functional `.package` files are valid, installable, and behave as expected.

**5.10 — Functional validation extension**
Extend validation to cover functional variant completeness, tuning integrity, and archetype-template compatibility.

*Outputs:* Extended validation rules.
*Dependencies:* 4.1, 5.9.
*Acceptance:* Invalid functional configurations are caught before export.

---

### 9.7 Phase 6 — Admin Mode

**Phase goal:** Build the full administrator surface for template management, base-game inspection, logs, and diagnostics.

**Phase acceptance gate:** A maintainer can access admin mode, browse and edit templates, import Tier 2 templates from the Sims install, promote Tier 2 to Tier 1, view logs and job history, and inspect base-game reference objects.

#### Tasks

**6.1 — Admin mode entry point and shell**
Implement admin mode entry (keyboard shortcut, menu item) and the admin navigation shell.

*Outputs:* Admin mode accessible but not visible in primary UI.
*Dependencies:* 0.6.
*Acceptance:* Admin mode can be entered and exited. Not discoverable by the primary user accidentally.

**6.2 — Template library browser**
Build the admin-mode template browser: list all Tier 1 and Tier 2 templates, view full schemas, preview renders.

*Outputs:* React admin screen.
*Dependencies:* 2.4, 6.1.
*Acceptance:* All templates are listed with schema detail and thumbnails.

**6.3 — Base-game mesh importer (Tier 2)**
Build the importer surface: browse base-game objects from the user's Sims install, preview, select for import, auto-extract basic metadata, register as Tier 2 templates.

*Outputs:* Importer UI and import pipeline.
*Dependencies:* 5.1, 6.2.
*Acceptance:* Admin can import a base-game object as a Tier 2 template. It becomes available for decorative use.

**6.4 — Tier 2 to Tier 1 promotion editor**
Build the schema editor for promoting Tier 2 templates. Admin specifies texture zones, archetype compatibility, example object types, and promotes.

*Outputs:* Schema editor UI.
*Dependencies:* 6.3.
*Acceptance:* Admin can author full schema for a Tier 2 template and promote it. Promoted template is usable as Tier 1.

**6.5 — Logs viewer**
Build the admin-mode logs viewer. Display current session and historical logs with filtering by level, stage, and item.

*Outputs:* Logs UI.
*Dependencies:* 0.7, 6.1.
*Acceptance:* Admin can read logs, filter them, and copy entries for debugging.

**6.6 — Job history view**
Build the job history UI: list of all generation and build jobs run, their status, artifacts, and duration.

*Outputs:* Job history UI.
*Dependencies:* 3.6, 4.2, 6.1.
*Acceptance:* Admin can inspect any past job and its artifacts.

**6.7 — Reference object browser**
Build the base-game reference object browser for tuning inspection. Admin can browse base-game tuning, search, view raw XML.

*Outputs:* Reference browser UI.
*Dependencies:* 5.1, 6.1.
*Acceptance:* Admin can inspect tuning for reference objects used by archetype handlers.

**6.8 — Configuration panel**
Build the admin-mode configuration panel: model selection overrides, retry policies, path overrides (Sims install, Mods folder, Blender), log level.

*Outputs:* Configuration UI with persistent settings.
*Dependencies:* 6.1.
*Acceptance:* Settings persist across app restarts. Overrides take effect.

---

### 9.8 Phase 7 — Cross-Platform Hardening and Polish

**Phase goal:** Final cross-platform testing, edge case handling, polish, documentation, and release readiness.

**Phase acceptance gate:** Both macOS and Windows builds pass all acceptance criteria in §10. Documentation deliverables in §13 are complete.

#### Tasks

**7.1 — Cross-platform parity testing**
Run the full MVP acceptance test suite on both Mac and Windows. Fix any platform-specific divergences.

*Outputs:* All ACs pass on both platforms. Divergences documented and fixed.
*Dependencies:* All prior phases.
*Acceptance:* Identical projects produce identical exports on both platforms.

**7.2 — Path edge case handling**
Handle non-standard Sims install locations, Mods folder on different drives, and permission edge cases. Provide manual overrides where auto-detection fails.

*Outputs:* Robust path handling across edge cases.
*Dependencies:* 0.3, 0.4, 4.4.
*Acceptance:* Non-standard installs work via manual override. Permission errors produce clear messages.

**7.3 — Error message polish**
Review every user-facing error message for clarity, actionability, and tone. Replace jargon with plain language. Ensure every error surfaces a next step.

*Outputs:* Polished error message set across the entire app.
*Dependencies:* All prior phases.
*Acceptance:* Primary user can understand and act on every error.

**7.4 — README**
Write the repository README covering project overview, dev setup, build instructions for both platforms, and contributing notes.

*Outputs:* `README.md` in the repo root.
*Dependencies:* All prior phases.
*Acceptance:* A developer cloning the repo can follow the README and get a working dev environment.

**7.5 — User manual**
Write a user-facing guide for the primary creator (girlfriend). Cover installation, first-project walkthrough, collection creation, functional upgrades, export and install, verification. Use plain language. Include screenshots.

*Outputs:* User manual in the repo, packaged with the app.
*Dependencies:* All prior phases.
*Acceptance:* A non-technical reader can follow the guide and complete a collection end-to-end.

**7.6 — Maintainer guide**
Write a maintainer-facing guide covering admin mode, template authoring, debugging workflows, Windows tooling recommendations (S4Studio, Sims4Tools, Mod Constructor, XML Extractor), common failure modes and recovery.

*Outputs:* Maintainer guide in the repo.
*Dependencies:* All prior phases.
*Acceptance:* The maintainer can reference the guide to perform any supported admin task.

**7.7 — Final acceptance test run**
Execute the full acceptance criteria list from the PRD (AC-001 through AC-016) and from §10 of this document. Sign off MVP completion.

*Outputs:* Completed acceptance test log.
*Dependencies:* All prior tasks.
*Acceptance:* All ACs pass. MVP v1.0 is shipped.

---

## 10. MVP Acceptance Criteria (Consolidated)

All of the following must pass for MVP v1.0 to ship.

- **MVP-AC-001** — App installs and launches on both macOS and Windows.
- **MVP-AC-002** — Sims 4 install and Mods folder are auto-detected on standard installs.
- **MVP-AC-003** — Blender presence is detected; user is prompted if missing.
- **MVP-AC-004** — A user can create a new project (collection or single item) with a prompt and parameters.
- **MVP-AC-005** — A collection plan is generated with template matches and confidence scores per item.
- **MVP-AC-006** — The user can edit the plan (add, remove, reorder, rename) before generation.
- **MVP-AC-007** — Low-confidence items are flagged with a clear warning and proceed/skip/rephrase options.
- **MVP-AC-008** — Decorative generation produces items with previews, swatches (3+), and metadata using semi-Alpha style.
- **MVP-AC-009** — The user can regenerate individual items and individual swatches.
- **MVP-AC-010** — The user can replace or exclude items.
- **MVP-AC-011** — The user can edit all metadata fields (name, description, tags, price, category, custom filter tag).
- **MVP-AC-012** — The user can upgrade at least one item per MVP archetype to a functional variant.
- **MVP-AC-013** — Structural validation runs before export and separates blockers from warnings.
- **MVP-AC-014** — Export produces valid `.package` files.
- **MVP-AC-015** — `.package` files auto-install to the detected Mods folder.
- **MVP-AC-016** — Export result summary clearly reports success/failure and install locations.
- **MVP-AC-017** — In-game verification flow is available and records user confirmation.
- **MVP-AC-018** — All exported decorative items appear correctly in Build/Buy in-game.
- **MVP-AC-019** — All exported functional items behave correctly in-game for their archetype.
- **MVP-AC-020** — Projects persist across app restarts and can be rebuilt deterministically.
- **MVP-AC-021** — Admin mode is accessible and hidden from primary flow.
- **MVP-AC-022** — Admin can browse and edit Tier 1 and Tier 2 templates.
- **MVP-AC-023** — Admin can import base-game meshes as Tier 2 templates.
- **MVP-AC-024** — Admin can promote Tier 2 templates to Tier 1.
- **MVP-AC-025** — Admin mode exposes logs, job history, and reference object browser.
- **MVP-AC-026** — Local-only logging works on both platforms at the correct standard paths.
- **MVP-AC-027** — No outbound telemetry; only required AI API calls.
- **MVP-AC-028** — Style parameter is present in schemas; semi-Alpha is the only implemented path.
- **MVP-AC-029** — Both platform builds produce identical exports from identical projects.
- **MVP-AC-030** — README, user manual, and maintainer guide are complete.

---

## 11. Testing Strategy

### 11.1 Unit Tests

Required for all non-UI Python code in the sidecar. Coverage targets:

- Project storage CRUD
- Template schema loading and validation
- Planning stage output parsing and validation
- Item spec generation output validation
- Texture pipeline coordination logic (mockable)
- DBPF read/write operations
- Tuning parsing and targeted editing
- Archetype handlers (with mocked reference resources)
- Validation engine rules
- Path resolution and platform detection

Unit tests must not require network access. AI calls, Replicate calls, and file system operations beyond the test sandbox are mocked.

### 11.2 Integration Tests

Required for the critical paths:

- New project → plan → generation → export → install (decorative only)
- New project → plan → generation → functional upgrade → export → install
- Project rebuild determinism
- Template loader querying across all 19 templates
- Admin mode Tier 2 import and promotion

Integration tests may use a dedicated test Sims install fixture (or documented mocking of the install).

### 11.3 Manual Acceptance Tests

Required for each of the MVP Acceptance Criteria (§10). The final acceptance test run in Task 7.7 executes the full list on both platforms.

Manual acceptance tests specifically require launching Sims 4 and visually confirming items appear and behave correctly. These cannot be fully automated.

### 11.4 POC Visual Quality Gate

Phase 1 concludes with a manual visual quality check by both maintainer and primary user. This is not a pass/fail unit test — it is a subjective quality gate that determines whether the MVP proceeds.

---

## 12. Decisions Made During MVP (Resolution Log)

This section is populated during Phase 1 and onwards. Each entry records a decision, its context, and when it was resolved.

- **D-1 — DBPF library choice.** Resolution target: Phase 1, Task 1.6.
- **D-2 — Primary image generation model.** Resolution target: Phase 1, Task 1.3.
- **D-3 — Normal and specular map derivation strategy.** Resolution target: Phase 1, Task 1.3.
- **D-4 — Exact base-game reference object IDs.** Resolution target: Phase 5, Task 5.2.
- **D-5 — Blender headless render recipe.** Resolution target: Phase 1, Task 1.5.
- **D-6 — Texture resolution policy.** Resolution target: Phase 1, Task 1.3–1.4.

Additional decisions encountered during implementation are logged here with the same format.

---

## 13. Documentation Deliverables

All produced during Phase 7.

- **README.md** — repo-level technical setup and contributing notes.
- **User manual** — end-user guide for the primary creator. Plain language, screenshots, walkthrough.
- **Maintainer guide** — admin-mode reference, template authoring, debugging, Windows tooling recommendations, failure recovery.

These are in addition to the PRD, this MVP Specification, the TAD, the Architecture Diagrams document, and the API Specification.

---

## 14. Risks and Mitigations

### 14.1 Texture Quality Below Acceptable Bar

**Risk:** The selected image model cannot produce semi-Alpha quality textures that hold up at in-game distance.
**Mitigation:** Phase 1 is a hard gate. If POC fails, pause MVP for approach revision before committing to Phases 2+.

### 14.2 Base-Game Reference Cloning Fragility

**Risk:** Cloned tuning references break under a Sims 4 patch.
**Mitigation:** Document exact reference IDs and tuning fields touched. Accept that patch-repair is a post-MVP concern. Validation extensions can detect common breakage patterns.

### 14.3 Cross-Platform Divergence

**Risk:** Mac and Windows builds diverge in subtle ways (path handling, file encoding, DBPF byte order).
**Mitigation:** Parity test as part of Phase 7. Deterministic rebuild test in Phase 4 catches non-determinism early.

### 14.4 Template Authoring Backlog

**Risk:** Authoring 19 templates at Tier 1 quality is a significant solo effort.
**Mitigation:** Templates can be seeded from base-game meshes as starting points (via Phase 5 extraction tools, which exist by Phase 2). Authoring standard (Task 2.1) exists before 2.2 and 2.3 start.

### 14.5 Replicate API Instability

**Risk:** Replicate (or the selected model) has an outage or deprecates a model.
**Mitigation:** The Anthropic and Replicate integrations are isolated modules. Alternative providers (Fal, Wavespeed) can be swapped in without pipeline redesign.

---

## 15. Success Criteria for the MVP Release

The MVP is considered successful when:

1. The primary user creates a themed collection end-to-end without maintainer intervention.
2. The exported items work correctly in her Sims 4 game.
3. She expresses confidence in using the tool for her own builds.
4. The maintainer can diagnose and fix any single-project failure using admin mode alone.
5. All acceptance criteria in §10 pass on both platforms.

---

## 16. What Comes After MVP v1.0

Out of scope for MVP but architected to support:

- Maxis Match visual style (v1.5)
- Additional functional archetypes (computer, stove, appliance categories)
- Patch-repair flow for tuning references that break under Sims updates
- AI-generated mesh exploration (v2+)
- Multi-user or team features (v2+)
- Project archive format with versioning and portability

These are not committed; they are documented forward paths that the MVP architecture does not foreclose.

---

## 17. Executive Summary

MVP v1.0 of AI Sims Creator is an eight-phase delivery: foundation, texturing proof-of-concept, template library, decorative generation, export and install, functional overlay, admin mode, and cross-platform polish.

The anchor of the MVP is Phase 1, Milestone Zero — a hard quality gate where one complete pipeline is built end-to-end, validated in-game, and confirmed visually before the remaining phases commit. This structure front-loads the highest-risk element (AI texture quality at production scale) while minimizing wasted work if that element fails the bar.

The template library is the central engineering investment. 19 curated Tier 1 primitives plus the Tier 2 base-game importer give the product the versatility to handle arbitrary themed collections without AI-generated geometry, and grow over time as gaps appear.

The administrator is the product owner, operating inside the same app through admin mode. The primary user is a non-technical creator who should experience a guided, prompt-driven, visually rich workflow that hides every technical detail below.

Tasks throughout are scoped at medium granularity for Claude Code consumption, with decomposition into subtasks expected at implementation time. Time estimates are intentionally omitted.

---

*End of MVP Specification v1.0*
