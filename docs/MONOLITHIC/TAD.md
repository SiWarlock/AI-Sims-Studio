# AI Sims Creator — Technical Architecture Document (TAD)

## 1. Document Status

- **Project:** AI Sims Creator
- **Document Type:** Technical Architecture Document (TAD)
- **Document Version:** 1.0
- **Status:** Draft for review
- **Depends On:** AI Sims Creator PRD v1.0 (approved), AI Sims Creator MVP Specification v1.0 (approved)
- **Precedes:** Architecture Diagrams, API Specification
- **Purpose:** Define the technical architecture, component design, data schemas, pipelines, and integration patterns for AI Sims Creator MVP v1.0. This document is the source of truth for implementation.
- **Intended Audience:** Project maintainer, Claude Code (primary implementation agent), future contributors.

---

## 2. Architecture Overview

### 2.1 System Shape

AI Sims Creator is a cross-platform desktop application composed of three primary layers:

1. **Frontend** — Tauri v2 shell hosting a React application. Renders all user interfaces, handles user input, dispatches requests to the sidecar, receives and reacts to events from the sidecar.
2. **Python Sidecar** — A single long-running Python process launched by Tauri as a subprocess. Owns all generation logic, AI integrations, file operations, DBPF packaging, tuning cloning, validation, and project persistence.
3. **External Systems** — The Anthropic API (Claude models), Replicate API (image generation), the user's local Sims 4 installation (read-only), the user's Sims 4 Mods folder (write), and a local Blender installation (subprocess invocation).

The frontend never calls external services directly. All network access, all file system access beyond what Tauri handles natively, and all invocation of external tools runs through the Python sidecar.

### 2.2 Architectural Principles

1. **Deterministic pipelines where game compatibility matters.** AI touches planning, texture generation, metadata drafting, and tuning value suggestions. AI never touches DBPF packaging, mesh geometry, tuning XML structure, or validation logic.
2. **Schema-enforced boundaries.** Every IPC message, every AI response, every persisted record passes through a Pydantic schema on the Python side. Types are auto-generated into TypeScript for the frontend.
3. **Single responsibility per component.** Each pipeline stage is a discrete module with a clear input schema, output schema, and failure mode.
4. **Crash-resilient persistence.** Generation state is snapshotted at phase boundaries. Crashes lose in-flight work but not completed work.
5. **Observable.** Every stage logs structured events. Admin mode surfaces them directly.
6. **Platform-parity.** The same codebase produces identical outputs on macOS and Windows. Platform-specific logic is isolated to path resolution, install detection, and log file location.

### 2.3 High-Level Data Flow

A generation run proceeds through these stages:

1. User prompt → Frontend collects inputs → IPC request to sidecar
2. Sidecar dispatches to Collection Planning stage → Claude Sonnet produces structured plan
3. User reviews and approves plan via frontend
4. Sidecar dispatches to Per-Item Spec Generation stage (parallel per item) → Claude Sonnet produces per-item specs
5. Sidecar dispatches to Texture Generation stage (parallel per swatch) → Replicate produces texture maps
6. Sidecar dispatches to Thumbnail Render stage (sequential, Blender subprocess) → PNG thumbnails produced
7. Sidecar persists all artifacts to project storage → Status events stream to frontend
8. User reviews items, issues regenerate/replace/exclude actions as needed
9. User triggers export → Sidecar runs Validation → DBPF Build → Auto-Install → Reports status

Functional upgrades follow a parallel sub-pipeline: archetype configuration → base-game resource extraction → tuning clone with user values → functional variant packaging.

---

## 3. Component Architecture

### 3.1 Frontend Architecture

#### 3.1.1 Framework Stack

- **Shell:** Tauri v2 (Rust host, system webview)
- **UI Framework:** React 18
- **Language:** TypeScript (strict mode)
- **State Management:** Redux Toolkit (RTK) with RTK Query disabled (IPC is not REST-shaped)
- **Routing:** React Router v6 (memory router, not browser router — Tauri uses custom protocol)
- **Styling:** Tailwind CSS + CSS modules for component-specific styles
- **Component Primitives:** Radix UI primitives for accessible low-level components (dialogs, dropdowns, tooltips) — styled via Tailwind
- **Build Tool:** Vite

#### 3.1.2 State Structure

Redux state is organized into feature slices:

- **`projectSlice`** — Currently open project, its metadata, its collections and items. Hydrated from sidecar on project open.
- **`generationSlice`** — In-flight generation jobs, per-item status, progress events.
- **`uiSlice`** — UI mode (creator vs admin), current screen, modal state, selected items.
- **`templatesSlice`** — Loaded template registry, schemas, query helpers.
- **`configSlice`** — User configuration (Sims install path, Mods folder path, Blender path, log level).
- **`logsSlice`** — Recent log entries (admin mode only, size-capped).
- **`archetypesSlice`** — Archetype definitions and reference object mappings.

Every slice has explicit actions. Async operations use `createAsyncThunk`. IPC events from the sidecar are received by a top-level listener that dispatches actions into the appropriate slice.

#### 3.1.3 IPC Subscription

A single module owns the sidecar connection. It exposes:

- `request(method, params)` — send a JSON-RPC request, return a promise resolving to the response
- `subscribe(eventType, handler)` — subscribe to a category of push notifications from the sidecar

The IPC module dispatches typed Redux actions in response to events. No component talks to the IPC module directly except for explicit request/response calls; subscriptions flow through Redux.

#### 3.1.4 Screens

Mapped to PRD §20:

- `HomeScreen` — recent projects, new project button
- `NewProjectWizard` — prompt, mode, size, style
- `PlanReviewScreen` — proposed plan, editable
- `CollectionBoardScreen` — item grid with status
- `ItemDetailScreen` — preview, swatches, metadata, actions
- `FunctionalUpgradeWizard` — archetype, config, summary
- `ExportScreen` — validation, options, trigger, result
- `VerificationScreen` — optional post-install in-game check
- `AdminModeRoot` — gates all admin screens
  - `AdminTemplateBrowser`
  - `AdminTemplateEditor`
  - `AdminMeshImporter`
  - `AdminLogsViewer`
  - `AdminJobHistory`
  - `AdminReferenceBrowser`
  - `AdminConfigPanel`

### 3.2 Python Sidecar Architecture

#### 3.2.1 Stack

- **Language:** Python 3.12
- **Async runtime:** `asyncio` (stdlib)
- **Schema / Validation:** Pydantic v2
- **ORM / DB:** SQLite via `sqlite3` (stdlib) with thin typed wrappers; no SQLAlchemy
- **Migrations:** `yoyo-migrations`
- **HTTP:** `httpx` (for direct calls where SDKs are insufficient)
- **AI SDKs:** `anthropic`, `replicate`
- **Image processing:** `Pillow`
- **DDS encoding:** custom module built on `Pillow` + numpy, encapsulated behind a clean interface
- **DBPF:** decision deferred to Phase 1 POC (see MVP Spec §8, D-1). Evaluated options include the `sims4-tools` community Python library and a custom implementation. The codebase isolates DBPF access behind a `dbpf_lib` module so the final choice does not leak outside that boundary.
- **Mesh I/O:** `pygltflib` for `.glb` load/save
- **Logging:** `structlog` on top of stdlib `logging`

#### 3.2.2 Process Model

The sidecar is a **single long-running Python process**, launched by Tauri at app startup and shut down when Tauri exits. A shutdown protocol exists: the frontend can send a `shutdown` request, and the sidecar finishes in-flight jobs, persists state, and exits cleanly within a timeout. If the timeout is exceeded, Tauri force-kills the process.

Within the process:

- An asyncio event loop hosts the JSON-RPC server (over stdio) and the job scheduler
- Long-running jobs (generation, build) run as asyncio tasks
- Blocking operations (Blender subprocess calls, DBPF writes, large image encoding) run in a thread pool executor to avoid blocking the event loop

#### 3.2.3 Module Structure

```
sidecar/
  aisc/                     # package root
    __init__.py
    main.py                 # entry point, stdio JSON-RPC server
    ipc/                    # JSON-RPC protocol, typed handlers
    config/                 # app config, platform detection, paths
    storage/                # SQLite access, project CRUD, migrations
    schemas/                # Pydantic models (shared with frontend via codegen)
    planning/               # Claude-backed collection planning
    spec_gen/               # Claude-backed per-item spec generation
    texture_gen/            # Replicate texture generation pipeline
    thumbnail/              # Blender subprocess invocation
    assembly/               # mesh + texture → textured render asset
    dbpf_lib/               # DBPF library adapter (isolates D-1 outcome)
    packaging/              # DBPF assembly for decor and functional
    tuning/                 # tuning parsing, clone, targeted edit
    archetypes/             # archetype handlers (light, audio, mirror, moodlet)
    validation/             # validation engine
    install/                # Mods folder auto-install
    templates/              # template registry, loader, tier management
    sims_install/           # Sims install detection, resource extraction, indexing
    admin/                  # admin mode operations
    jobs/                   # async job scheduler, progress events
    logging_setup/          # structured logging configuration
    errors/                 # error taxonomy, user-facing message mapping
  tests/
  migrations/               # yoyo-migrations for SQLite schema
  scripts/                  # blender scripts invoked via subprocess
  pyproject.toml
```

### 3.3 Repository Structure

Monorepo layout at the root:

```
aisc/                       # project root
  frontend/                 # Tauri + React
    src/
    src-tauri/              # Tauri Rust shell
    package.json
    vite.config.ts
  sidecar/                  # Python sidecar (see 3.2.3)
  templates/                # Tier 1 template library (Git LFS)
    decor/
    furniture/
    manifests/              # template schema manifests
  shared-types/             # auto-generated TypeScript types from Pydantic schemas
  docs/
    PRD.md
    MVP_Specification.md
    TAD.md                  # this document
    Architecture_Diagrams.md
    API_Specification.md
    user-manual/
    maintainer-guide/
  scripts/                  # build scripts, codegen, dev helpers
  .github/                  # CI config (future)
  README.md
  pyproject.toml            # sidecar Python package
  package.json              # monorepo tooling
```

Template `.glb` files are stored via Git LFS. Large binary assets (reference textures, sample inputs) also via LFS.

### 3.4 Build and Distribution

- **macOS build:** Tauri produces a `.dmg` installer containing the app bundle with the embedded Python sidecar and template library. Intel and Apple Silicon targets supported; primary user is on Intel Mac so Intel build is the explicit target.
- **Windows build:** Tauri produces a `.msi` or `.exe` installer.
- **Python sidecar bundling:** Uses `pyoxidizer` or `PyInstaller` to bundle Python runtime and dependencies into a standalone executable that Tauri invokes as a subprocess. Exact bundler chosen during Phase 0 based on cross-platform reliability.
- **Template library bundling:** Template `.glb` files and manifests are included in the app resources directory at build time.
- **Blender:** Not bundled. Detected at first launch.

---

## 4. Data Model

### 4.1 Schema Philosophy

All persisted data is modeled as Pydantic v2 models in Python. Corresponding SQLite tables are normalized with foreign key relationships. TypeScript types for the frontend are auto-generated from the Pydantic models via `pydantic-to-typescript` (or equivalent) during build.

Every schema has a `schema_version` field to support future migrations.

### 4.2 Core Entity Schemas

#### 4.2.1 Project

```python
class Project(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime
    schema_version: int
    theme_prompt: str
    style_notes: Optional[str]
    collections: list[UUID]          # Collection IDs
    reference_inputs: list[UUID]     # ReferenceInput IDs
    archived: bool
```

#### 4.2.2 Collection

```python
class Collection(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    style_preference: StylePreference  # Literal["semi_alpha", "maxis_match"]
    target_item_count: int             # 1..12
    mode: CollectionMode               # Literal["single_item", "collection"]
    theme_summary: Optional[str]       # populated by planning stage
    palette_direction: Optional[str]
    material_direction: Optional[str]
    items: list[UUID]                  # Item IDs, ordered
    status: CollectionStatus           # planned, generating, generated, exported
    created_at: datetime
    updated_at: datetime
```

#### 4.2.3 Item

```python
class Item(BaseModel):
    id: UUID
    collection_id: UUID
    order_index: int
    source_request: str                # user's original phrase, e.g. "Y2K CD player"
    template_id: str                   # ID of selected template
    template_match_confidence: float   # 0..1
    template_match_warning: Optional[str]  # populated if low confidence
    included_in_export: bool
    status: ItemStatus                 # planned, generating, generated, needs_review, error, excluded

    # Populated by spec generation stage
    spec: Optional[ItemSpec]

    # Populated by generation stages
    swatches: list[UUID]               # Swatch IDs
    primary_swatch_id: Optional[UUID]  # swatch used for thumbnail
    thumbnail_path: Optional[str]      # relative path in project folder

    # Metadata, editable by user
    metadata: ItemMetadata

    # Optional functional overlay
    functional_overlay_id: Optional[UUID]

    created_at: datetime
    updated_at: datetime
```

#### 4.2.4 ItemSpec

```python
class ItemSpec(BaseModel):
    item_id: UUID
    texture_zone_prompts: dict[str, TextureZonePrompt]  # keyed by zone label
    name_suggestion: str
    description_suggestion: str
    tags_suggestion: list[str]
    price_suggestion: int
    category_suggestion: str           # Build/Buy category
    custom_filter_tag_suggestion: Optional[str]
    confidence: float
    generated_at: datetime

class TextureZonePrompt(BaseModel):
    zone_label: str                    # e.g. "base", "vessel", "cap"
    diffuse_prompt: str
    material_hints: str                # "translucent plastic", "brushed metal"
    palette_anchors: list[str]         # hex colors
```

#### 4.2.5 ItemMetadata

```python
class ItemMetadata(BaseModel):
    name: str
    description: str
    tags: list[str]
    price: int
    build_buy_category: str
    custom_filter_tag: Optional[str]
    user_edited: bool                  # true if user has overridden auto-generated values
```

#### 4.2.6 Swatch and TextureSet

```python
class Swatch(BaseModel):
    id: UUID
    item_id: UUID
    index: int                         # 0..N-1
    texture_set_id: UUID
    thumbnail_path: Optional[str]
    status: SwatchStatus               # planned, generating, generated, error
    created_at: datetime

class TextureSet(BaseModel):
    id: UUID
    swatch_id: UUID
    zone_maps: dict[str, ZoneMaps]     # keyed by zone label

class ZoneMaps(BaseModel):
    zone_label: str
    diffuse_path: str                  # relative path in project folder
    normal_path: str
    specular_path: str
    generation_prompt: str
    generation_seed: Optional[int]
    model_used: str                    # e.g. "flux-1.1-pro"
```

#### 4.2.7 FunctionalOverlay

```python
class FunctionalOverlay(BaseModel):
    id: UUID
    item_id: UUID
    archetype: ArchetypeId             # light_on_off, audio_device, mirror, moodlet_emitter
    configuration: dict[str, Any]      # archetype-specific, validated against archetype schema
    reference_object_id: str           # Sims 4 resource ID cloned from
    status: OverlayStatus              # configured, built, error
    created_at: datetime
    updated_at: datetime
```

Archetype-specific configuration is validated by an archetype handler module (see §8). A discriminated union ensures each archetype's configuration conforms to its own schema.

#### 4.2.8 Template

```python
class Template(BaseModel):
    id: str                            # e.g. "cylindrical_small_tabletop"
    tier: TemplateTier                 # tier_1, tier_2
    shape_class: str
    dimension_ranges: DimensionRanges
    footprint_type: FootprintType
    texture_zones: list[TextureZoneDef]
    compatible_archetypes: list[ArchetypeId]
    example_objects: list[str]         # user-facing examples
    mesh_path: str                     # relative to templates/ directory
    authoring_notes: Optional[str]
    schema_version: int

class TextureZoneDef(BaseModel):
    label: str                         # e.g. "base", "vessel"
    uv_bounds: UVBounds                # UV rectangle on the mesh
    typical_materials: list[str]       # material hints for prompting

class DimensionRanges(BaseModel):
    height_cm: tuple[float, float]
    width_cm: tuple[float, float]
    depth_cm: tuple[float, float]

class FootprintType(str, Enum):
    TABLETOP_SINGLE = "tabletop_single"
    FLOOR_1X1 = "floor_1x1"
    FLOOR_1X2 = "floor_1x2"
    FLOOR_2X1 = "floor_2x1"
    FLOOR_2X2 = "floor_2x2"
    WALL_FLAT = "wall_flat"
    WALL_SHELF = "wall_shelf"
    SEAT_SINGLE = "seat_single"
    SEAT_MULTI = "seat_multi"
    # additional footprints as needed
```

#### 4.2.9 BuildJob

```python
class BuildJob(BaseModel):
    id: UUID
    project_id: UUID
    kind: JobKind                      # planning, spec_gen, texture_gen, thumbnail, packaging, validation, install
    status: JobStatus                  # queued, running, succeeded, failed, cancelled
    target_entity_type: str            # "Collection", "Item", "Swatch"
    target_entity_id: UUID
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    artifacts: list[str]               # paths to any produced artifacts
    error: Optional[JobError]
    retry_count: int
```

#### 4.2.10 ValidationResult

```python
class ValidationResult(BaseModel):
    id: UUID
    project_id: UUID
    collection_id: UUID
    run_at: datetime
    errors: list[ValidationIssue]
    warnings: list[ValidationIssue]
    passed: bool

class ValidationIssue(BaseModel):
    code: str                          # e.g. "MISSING_THUMBNAIL", "INVALID_DBPF_HEADER"
    severity: Severity                 # error, warning
    target_entity_type: Optional[str]
    target_entity_id: Optional[UUID]
    message_user: str                  # creator-facing, plain language
    message_admin: str                 # admin-facing, full detail
    suggested_action: Optional[str]
```

#### 4.2.11 ExportArtifact

```python
class ExportArtifact(BaseModel):
    id: UUID
    project_id: UUID
    collection_id: UUID
    package_path: str                  # absolute path to the .package file
    install_path: Optional[str]        # absolute path where installed
    item_ids_included: list[UUID]
    functional_item_ids: list[UUID]
    size_bytes: int
    sha256: str
    built_at: datetime
    installed_at: Optional[datetime]
    verified_in_game: Optional[bool]
    verification_recorded_at: Optional[datetime]
```

#### 4.2.12 ReferenceInput

```python
class ReferenceInput(BaseModel):
    id: UUID
    project_id: UUID
    kind: ReferenceKind                # image, text_description
    content_path: Optional[str]        # for images
    content_text: Optional[str]        # for descriptions
    uploaded_at: datetime
```

#### 4.2.13 GenerationAttempt

```python
class GenerationAttempt(BaseModel):
    id: UUID
    target_entity_type: str            # "Item", "Swatch", "TextureSet"
    target_entity_id: UUID
    stage: GenerationStage             # planning, spec, texture, thumbnail
    model_used: str
    prompt: str
    seed: Optional[int]
    result: Optional[str]              # path to generated artifact
    success: bool
    error_code: Optional[str]
    timestamp: datetime
```

### 4.3 SQLite Schema

The SQLite schema follows the Pydantic models with a table per entity. Foreign keys enforce referential integrity. Key indices:

- `items(collection_id)` — fast lookup of items in a collection
- `swatches(item_id)` — fast lookup of swatches for an item
- `build_jobs(project_id, started_at)` — job history ordered
- `generation_attempts(target_entity_id, timestamp)` — provenance trail
- `validation_results(collection_id, run_at DESC)` — latest validation

Complex nested fields (e.g., `ItemSpec.texture_zone_prompts`, `FunctionalOverlay.configuration`) are stored as JSON columns with Pydantic doing the serialization on write and deserialization on read. This keeps the relational structure clean while allowing flexible nested data.

### 4.4 Project Folder Layout

A project is a self-contained folder:

```
~/Documents/AISimsCreator/projects/{project_name}/
  project.sqlite              # project metadata database
  assets/
    thumbnails/
      {item_id}.png
      {item_id}_swatch_{index}.png
    textures/
      {swatch_id}/
        {zone}_diffuse.png
        {zone}_normal.png
        {zone}_specular.png
    references/
      {reference_id}.{ext}
  exports/
    {export_id}/
      {collection_name}.package
      export_manifest.json
  logs/
    session_{timestamp}.log
```

The project folder is portable. Copying it to another machine with the same app installed produces an openable project, subject to local Sims install availability for functional items.

### 4.5 Migration Strategy

Schema migrations use `yoyo-migrations`:

- Each migration is a numbered Python file in `sidecar/migrations/`
- Migrations are applied on app startup if the project's schema version is behind the current version
- Migrations are forward-only in MVP (no rollback support)
- Before a migration runs, the project's SQLite file is backed up with a timestamp suffix

Template schema migrations are handled separately — the template loader validates each template against its declared schema version and can transform older versions to current at load time.

### 4.6 Type Generation for Frontend

TypeScript types are auto-generated from Pydantic schemas as part of the build. Script location: `scripts/generate_types.py`. Output: `shared-types/index.ts`.

The frontend never defines its own types for IPC-transmitted data. If a type is needed in the frontend, it either comes from `shared-types/` or is a frontend-only type (e.g., UI state).

---

## 5. IPC Architecture

### 5.1 Protocol

The frontend ↔ sidecar channel uses **JSON-RPC 2.0 over stdio**.

- Messages are newline-delimited JSON objects written to stdout (sidecar → frontend) and stdin (frontend → sidecar).
- Each request has an ID; responses include the matching ID.
- Notifications (no response expected) are used for progress events.
- Tauri's sidecar API handles process lifecycle and byte streaming.

### 5.2 Message Categories

- **Request / Response** — client-initiated, expects a response. Examples: `project.create`, `collection.generate`, `export.run`.
- **Notification (sidecar-initiated)** — progress events, log events, error events. Examples: `generation.progress`, `item.status_changed`, `log.emitted`.

### 5.3 Method Naming

Methods use dotted namespaces:

- `project.*` — project CRUD
- `collection.*` — collection planning, editing, generation
- `item.*` — item operations
- `swatch.*` — swatch regeneration
- `functional.*` — functional overlay operations
- `validation.*` — validation requests
- `export.*` — export and install
- `admin.*` — admin mode operations (gated)
- `config.*` — configuration CRUD
- `system.*` — health, shutdown, paths

Complete method inventory is the subject of the API Specification document.

### 5.4 Error Handling

Errors use a structured format extending JSON-RPC:

```json
{
  "jsonrpc": "2.0",
  "id": "...",
  "error": {
    "code": -32000,
    "message": "Generation failed",
    "data": {
      "error_code": "REPLICATE_TIMEOUT",
      "message_user": "The image generator took too long. Try again in a moment.",
      "message_admin": "Replicate API call exceeded 120s timeout for model flux-1.1-pro...",
      "suggested_action": "retry",
      "retriable": true,
      "target_entity_id": "..."
    }
  }
}
```

Error codes are an enum defined in `sidecar/errors/codes.py` and re-exported to TypeScript.

### 5.5 Progress Event Schema

All progress notifications follow a uniform shape:

```json
{
  "jsonrpc": "2.0",
  "method": "generation.progress",
  "params": {
    "job_id": "...",
    "stage": "texture_gen",
    "target_entity_type": "Swatch",
    "target_entity_id": "...",
    "progress_ratio": 0.4,
    "message_user": "Generating Y2K lava lamp textures..."
  }
}
```

### 5.6 Admin Gating

Admin mode methods (`admin.*`) are accepted by the sidecar only when the frontend has declared admin mode active via a `system.set_admin_mode` call. Admin mode has no authentication; this gating is not a security boundary, it is a safety rail that prevents UI bugs from inadvertently calling admin endpoints from non-admin screens.

---

## 6. Pipeline Architecture

Every generation pipeline stage is implemented as a module with a standard shape:

- An input Pydantic schema
- An output Pydantic schema
- A pure async function `run(input) -> output` (or `run(input) -> AsyncIterator[ProgressEvent, output]`)
- Dependency-injected external clients (Anthropic, Replicate, Blender) so tests can mock them
- Structured logging with stage name, target entity, and outcome

### 6.1 Collection Planning Stage

**Input:** `PlanningInput` — user prompt, desired item count, style preference, template registry snapshot, optional reference inputs.

**Output:** `CollectionPlan` — theme summary, ordered item list, each with source request, selected template ID, confidence score, and optional warning text.

**Model:** Claude Sonnet 4.6 via Anthropic SDK, using tool use to enforce structured output.

**Prompt strategy:**

- System prompt describes the product's role, the template registry schema, the style preference, and the rules (no items outside the template registry's shape-matching capabilities, flag low-confidence matches, produce coherent plans).
- User prompt includes the creator's theme prompt and desired item count.
- Tool definition: a single `submit_plan` tool with the `CollectionPlan` schema.
- Temperature: low (~0.3) for consistency.

**Failure modes:**
- Rate limit: retry with exponential backoff
- Tool call malformed: retry up to 2 times with stricter prompt
- All retries exhausted: surface error to user with retry option

### 6.2 Per-Item Spec Generation Stage

**Input:** `SpecInput` — item source request, selected template (full schema), collection context (theme, palette, style preference, other items in collection for coherence).

**Output:** `ItemSpec` — per-zone prompts, name, description, tags, price, category, optional filter tag.

**Model:** Claude Sonnet 4.6 via Anthropic SDK.

**Prompt strategy:**

- System prompt describes the item spec generation task, the texture-zone schema, the style preference, and the rules (prompts must be image-model-ready, material-descriptive, photographic language for semi-Alpha; names must feel consistent with other items in collection).
- User prompt includes the source request, template schema, and collection context.
- Tool use: `submit_item_spec` tool with the `ItemSpec` schema.

**Parallelization:** Items in a collection can be spec-generated in parallel. The collection context is passed to each call so coherence is maintained across parallel generations.

**Failure modes:**
- Same as planning stage with per-item isolation (one item's failure does not block others)

### 6.3 Texture Generation Stage

**Input:** `TextureGenInput` — item spec, template schema (for zone UV bounds), swatch index (for seed variation), style preference.

**Output:** `TextureSet` — per-zone diffuse/normal/specular PNG paths on disk.

**Model:** decision D-2 (selected during Phase 1 POC). Default working assumption: Flux 1.1 Pro via Replicate for diffuse; normal and specular handled per D-3.

**Pipeline:**

1. For each texture zone in the template, construct the image generation prompt from `ItemSpec.texture_zone_prompts[zone]` combined with material hints and style directives.
2. Submit the diffuse generation request to Replicate.
3. Per D-3: either submit coordinated normal/specular requests, or derive normal/specular from diffuse via a height-map inference step.
4. Download results, save to the swatch's texture folder.
5. Validate output images (correct dimensions, not corrupted, plausibly matching the prompt via a simple sanity check such as non-uniform content).
6. Return the `TextureSet` record.

**Parallelization:** Swatches across items, and zones within a swatch, can generate in parallel. Concurrency is capped to respect Replicate rate limits (working default: 4 concurrent requests).

**Failure modes:**
- Replicate timeout: retry once with same seed
- Content policy rejection: retry once with prompt rephrased by Haiku
- Zone-level failure: mark zone failed, continue other zones
- Swatch-level failure (all zones failed): mark swatch failed, item still usable with remaining swatches

### 6.4 Thumbnail Render Stage

**Input:** `ThumbnailInput` — item, primary swatch's texture set, template mesh path.

**Output:** `ThumbnailArtifact` — paths to rendered PNGs (item catalog thumbnail, per-swatch catalog thumbnails, large preview for app).

**Tool:** Blender invoked as subprocess.

**Pipeline:**

1. Sidecar prepares a Blender job spec (template mesh, texture maps per zone, camera and lighting settings from D-5).
2. Sidecar writes the job spec to a temp file and invokes Blender headless:
   `blender --background --python scripts/render_thumbnail.py -- <job_spec_path>`
3. Blender script loads the `.glb`, assigns materials from the texture maps, renders at configured resolutions (catalog thumbnail 128×128, swatch thumbnail 64×64, app preview 512×512 per T-9 working assumption).
4. Blender writes PNG outputs to predetermined paths.
5. Sidecar reads outputs, validates them, and returns paths.

**Parallelization:** Thumbnail rendering is sequential per item (one Blender subprocess at a time) to avoid Blender lock issues. Items can render in parallel only if separate Blender instances are managed carefully; for MVP, thumbnail rendering is strictly serial.

**Failure modes:**
- Blender subprocess failure: retry once (likely transient)
- Repeated failure: mark item needs-review with admin-visible detail

### 6.5 Metadata Finalization Stage

Not a separate AI call. Takes `ItemSpec` auto-suggestions and merges with any user edits stored on the `Item`. User edits always win. Final metadata is persisted to the item record.

### 6.6 Validation Stage

**Input:** A collection ID.

**Output:** `ValidationResult` with errors and warnings.

**Checks (MVP scope):**

1. **Asset completeness per item** — required fields present, thumbnails exist, textures exist.
2. **Metadata completeness** — name not empty, price in valid range, category is a recognized Build/Buy category.
3. **DBPF integrity** — for built packages, verify DBPF header, TGI resource IDs non-colliding, required resources present.
4. **Tuning integrity** — for functional items, verify cloned tuning is valid XML with all expected fields present and references resolvable.
5. **Archetype-template compatibility** — confirm any functional overlays' archetypes are in their item's template's compatibility list.
6. **Project consistency** — no dangling references, no orphaned items.

Each check is an independent module returning zero or more `ValidationIssue`s. Validation is deterministic and re-runnable.

### 6.7 DBPF Packaging Stage

**Input:** A collection ID, plus per-item variant choices (decor-only, functional, or both).

**Output:** `ExportArtifact` — a `.package` file on disk.

**Pipeline (one `.package` per collection, per T-8):**

1. Initialize a new DBPF container.
2. For each included item:
   - Encode texture maps to DDS (DXT1 for diffuse without alpha, DXT5 with alpha, per standard Sims conventions)
   - Assemble the textured mesh as a `.geom` or Sims-appropriate mesh resource
   - Generate TGI resource IDs for all resources (mesh, textures, catalog entry, string table entries, thumbnail)
   - Build the catalog entry (object definition) with metadata from `ItemMetadata`
   - Build the string table entries for name and description
   - Build the thumbnail resource
3. If the item has a functional overlay:
   - Retrieve the cloned-and-edited tuning from the functional overlay record
   - Add tuning resources to the package with new TGI IDs
   - Update catalog entry to reference the functional tuning
4. Write the DBPF container to disk.
5. Compute SHA-256 of the output file.
6. Return `ExportArtifact`.

**Determinism:** The same input produces byte-identical output. TGI ID generation uses a deterministic hash from the item ID + resource kind so rebuilds are stable.

### 6.8 Auto-Install Stage

**Input:** An `ExportArtifact`.

**Output:** Updated `ExportArtifact` with `install_path` populated.

**Pipeline:**

1. Confirm Mods folder path is available (re-detect if stale).
2. Check for existing file at target path:
   - If missing: copy file directly
   - If exists and SHA-256 matches: skip, report "already installed"
   - If exists and SHA-256 differs: prompt user (overwrite / rename / skip)
3. Copy with fsync to ensure file is flushed.
4. Update the artifact record with `install_path` and `installed_at`.

**Failure modes:**
- Permission denied: prompt user for alternative location or manual install
- Disk full: clear error with remediation

### 6.9 Verification Stage

Not a generation pipeline. A UI flow that:

1. Displays a "Launch Sims" button
2. Presents a per-item checklist for the user to mark "appeared correctly" or "something looks wrong"
3. Persists verification state to the `ExportArtifact.verified_in_game` field and per-item notes

---

## 7. AI Orchestration Layer

### 7.1 Model Assignments (Current)

As established in the PRD and MVP Spec:

- **Collection planning:** Claude Sonnet 4.6 via Anthropic API (official SDK)
- **Per-item spec generation:** Claude Sonnet 4.6
- **Tuning value suggestion:** Claude Sonnet 4.6
- **Repair suggestions:** Claude Sonnet 4.6
- **Validation explanation rewriting:** Claude Haiku 4.5
- **Content policy prompt rephrasing (texture gen retry):** Claude Haiku 4.5
- **Texture generation:** model selected during Phase 1 POC (D-2), working default Flux 1.1 Pro via Replicate (official SDK)
- **Thumbnail rendering:** Blender (not AI)

### 7.2 Client Wrappers

Both Anthropic and Replicate SDKs are wrapped in thin internal clients that:

- Enforce request schemas (input validated before dispatch)
- Enforce response schemas (output validated before return)
- Log every call with prompt, model, latency, token counts, cost estimate
- Implement the retry policy from T-12
- Surface structured errors conforming to the error taxonomy

### 7.3 Prompt Library

Prompts live in a dedicated module (`sidecar/prompts/`) with one file per stage. Each prompt is a function that accepts a typed context object and returns the prompt string (or structured messages for Claude).

No prompts are hardcoded at call sites. All prompts are in the prompt library for discoverability, reviewability, and iteration.

### 7.4 Cost Tracking

Every AI call records its estimated cost in the `GenerationAttempt` record. Cost estimates use current published rates for Anthropic and Replicate. The admin mode includes a cost view summing costs per project, per day, and per session.

Cost is tracked for observability; there is no enforcement or rate limiting on cost in MVP.

### 7.5 Determinism Notes

AI outputs are not guaranteed deterministic even at temperature 0. Re-running a stage typically produces similar but not identical results. The pipeline treats AI outputs as generated artifacts that, once accepted, are persisted and not re-run unless the user explicitly requests regeneration.

Determinism is enforced at the non-AI stages: template loading, mesh assembly, thumbnail rendering (with fixed seeds in Blender), DBPF packaging, install.

---

## 8. Archetype Handlers

Each MVP archetype is implemented as a handler module conforming to a common interface.

### 8.1 Handler Interface

```python
class ArchetypeHandler(Protocol):
    archetype_id: ArchetypeId
    reference_object_lookup: ReferenceObjectLookup
    configuration_schema: type[BaseModel]    # archetype-specific config model
    compatible_templates: list[str]          # template IDs

    async def build_overlay(
        self,
        item: Item,
        template: Template,
        configuration: BaseModel,
        reference_resources: ReferenceResources,
    ) -> BuiltOverlay:
        ...

    def validate_configuration(self, configuration: BaseModel) -> list[ValidationIssue]:
        ...

    def summarize_behavior(self, configuration: BaseModel) -> str:
        ...
```

### 8.2 Light On/Off Handler

- **Reference object lookup:** criteria per MVP Spec §7.1. Exact ID resolved during Phase 5.
- **Configuration schema:** `LightOnOffConfig` with `light_color` (hex), `intensity` (enum low/medium/high), `always_on` (bool).
- **Compatible templates:** `cylindrical_small_tabletop`, `cylindrical_tall_floor`, `boxy_electronic_small_tabletop`.
- **Build pipeline:**
  1. Extract reference lamp tuning from user's Sims install
  2. Parse tuning, locate light-related fields (color, intensity reference, state machine)
  3. Apply user's configured values
  4. Emit new tuning resources with fresh TGI IDs
  5. Return `BuiltOverlay` with tuning resource list

### 8.3 Audio Device Handler

- **Reference:** cheapest base-game stereo, per MVP Spec §7.2
- **Configuration:** `AudioDeviceConfig` with `genre_category` (enum from base-game genres), `default_volume` (int 1–5)
- **Compatible templates:** `boxy_electronic_small_tabletop`, `boxy_electronic_medium_tabletop`
- **Build pipeline:** clone stereo tuning, override genre reference, emit resources

### 8.4 Mirror Handler

- **Reference:** base-game wall mirror, per MVP Spec §7.3
- **Configuration:** `MirrorConfig` — none in MVP (empty model)
- **Compatible templates:** `rectangular_wall_flat`
- **Build pipeline:** clone mirror tuning verbatim, no value overrides

### 8.5 Moodlet Emitter Handler

- **Reference:** base-game broadcaster decor, per MVP Spec §7.4
- **Configuration:** `MoodletEmitterConfig` with `moodlet_id` (from curated safe list), `duration_hours` (int 1–8), `emission_radius_tiles` (int 1–4)
- **Compatible templates:** broad list covering most decor primitives
- **Build pipeline:** clone broadcaster tuning, override moodlet reference and broadcaster parameters

### 8.6 Curated Moodlet List

A whitelist of safe base-game moodlets that won't break saves or cause unexpected effects. Defined in `sidecar/archetypes/moodlet_catalog.py`. Includes common positive moodlets (Focused, Inspired, Happy, Playful, Flirty, Confident) with approximate durations.

---

## 9. Template Library Implementation

### 9.1 Template Registry

The `templates` module exposes:

- `load_registry() -> TemplateRegistry` — loads all Tier 1 and Tier 2 templates from disk at sidecar startup.
- `TemplateRegistry.get(template_id) -> Template` — lookup by ID.
- `TemplateRegistry.query(criteria) -> list[Template]` — query by shape class, archetype compatibility, dimension range, etc.
- `TemplateRegistry.compatible_templates_for_request(request: str, style: StylePreference) -> list[TemplateMatch]` — used by the planning stage; ranks templates by fit to a user request string.

### 9.2 Storage Layout

```
templates/
  decor/
    cylindrical_small_tabletop/
      mesh.glb
      manifest.json             # Template schema JSON
      thumbnail_preview.png     # maintainer-facing preview
    [... other decor templates]
  furniture/
    [... furniture templates]
  tier2/                         # user-imported, located under app data not repo
    {imported_id}/
      mesh.glb
      manifest.json
      source_reference.json     # info about the base-game object it was imported from
```

Tier 1 templates are in the repo and bundled with the app. Tier 2 templates live in the app data directory.

### 9.3 Template Manifest Format

```json
{
  "id": "cylindrical_small_tabletop",
  "tier": "tier_1",
  "shape_class": "cylindrical",
  "dimension_ranges": {
    "height_cm": [8.0, 40.0],
    "width_cm": [6.0, 15.0],
    "depth_cm": [6.0, 15.0]
  },
  "footprint_type": "tabletop_single",
  "texture_zones": [
    {
      "label": "base",
      "uv_bounds": {"u_min": 0.0, "u_max": 0.5, "v_min": 0.0, "v_max": 0.25},
      "typical_materials": ["metal", "plastic", "wood"]
    },
    {
      "label": "vessel",
      "uv_bounds": {"u_min": 0.0, "u_max": 1.0, "v_min": 0.25, "v_max": 0.9},
      "typical_materials": ["glass", "translucent_plastic", "ceramic"]
    },
    {
      "label": "cap",
      "uv_bounds": {"u_min": 0.5, "u_max": 1.0, "v_min": 0.0, "v_max": 0.25},
      "typical_materials": ["metal", "plastic"]
    }
  ],
  "compatible_archetypes": ["light_on_off", "moodlet_emitter"],
  "example_objects": ["lava lamp", "vase", "candle", "small lamp"],
  "authoring_notes": "Center pivot at base. UVs laid out with base on bottom-left tile, vessel spanning middle, cap on bottom-right.",
  "schema_version": 1
}
```

### 9.4 Tier 2 Import

The Tier 2 importer:

1. Reads a selected base-game object from the user's Sims install (via `sims_install` module)
2. Extracts the mesh resources
3. Converts to `.glb` format
4. Auto-extracts available metadata (dimensions from mesh bounds, footprint from base-game object data)
5. Generates a partial manifest with `tier: "tier_2"`, missing texture zones and compatible archetypes
6. Registers in the Tier 2 directory

### 9.5 Tier 2 → Tier 1 Promotion

The admin promotion editor:

1. Loads a Tier 2 template
2. Prompts the admin to author texture zones (by painting UV regions on a preview render), archetype compatibility, example objects, and authoring notes
3. Saves the enriched manifest
4. Moves the template's files to the Tier 1 directory (under `templates/decor/` or `templates/furniture/` based on shape class)
5. Updates the registry

### 9.6 Graceful Degradation

If a Tier 2 template is referenced in a project but its schema is incomplete:

- It can be used for decorative-only projects
- Texture zones that don't exist are skipped (whole-mesh texture fallback)
- Archetype compatibility is assumed empty; the item cannot be made functional
- Warnings are emitted but generation proceeds

---

## 10. DBPF Packaging

### 10.1 Library Boundary

All DBPF access is isolated behind the `dbpf_lib` module. This module exposes a stable interface:

```python
class DBPFWriter(Protocol):
    def open(self, path: str) -> None: ...
    def add_resource(self, tgi: TGI, data: bytes) -> None: ...
    def close(self) -> None: ...

class DBPFReader(Protocol):
    def open(self, path: str) -> None: ...
    def list_resources(self) -> list[TGI]: ...
    def read_resource(self, tgi: TGI) -> bytes: ...
    def close(self) -> None: ...
```

The underlying implementation (external library or custom, decided by D-1) is a detail of `dbpf_lib`.

### 10.2 TGI ID Generation

TGI (Type-Group-Instance) IDs are generated deterministically:

- **Type:** fixed per resource kind (mesh, diffuse texture, catalog entry, tuning, STBL)
- **Group:** a project-specific hash prefix (derived from project ID) to avoid collisions with base game and other mods
- **Instance:** derived from `item_id + resource_kind + swatch_index` as appropriate, via stable hash

This guarantees that the same project state produces the same TGI IDs on rebuild.

### 10.3 Resource Types Produced

Per decor item:

- Catalog entry (object definition)
- Mesh resource (low LOD + high LOD, if LODs are authored)
- Diffuse texture resources per zone, per swatch (DDS encoded)
- Normal texture resources per zone, per swatch
- Specular texture resources per zone, per swatch
- Thumbnail resource
- String table entries (name, description)

Per functional item (additive on top of decor):

- Object tuning XML
- Interaction tuning XML (if archetype adds/modifies interactions)
- Any broadcaster, state, or buff tuning needed by the archetype
- Additional string table entries for interaction names

### 10.4 DDS Encoding

Textures generated as PNG by the texture pipeline are encoded to DDS at packaging time:

- Diffuse with alpha: DXT5
- Diffuse without alpha: DXT1
- Normal: DXT5 (with tangent-space normal conventions)
- Specular: DXT1 or grayscale depending on channel content

The DDS encoder is a custom Python module built on `Pillow` + `numpy`, because cross-platform DDS libraries are inconsistent. Unit tests verify encoded output round-trips correctly.

### 10.5 Catalog Entry Construction

Catalog entries reference the object's mesh, textures (by swatch), thumbnail, and metadata (name, description, category, tags, price). Category assignment uses Sims 4's Build/Buy category taxonomy; the `ItemMetadata.build_buy_category` field is mapped to the correct internal category ID at packaging time.

### 10.6 Custom Catalog Filter Tags

When `ItemMetadata.custom_filter_tag` is set, a custom tag resource is added enabling the item to appear under a user-defined filter in Build/Buy. This uses the Sims 4 custom tag system (not custom category).

---

## 11. Tuning Clone Pipeline

### 11.1 Extraction

The `sims_install` module reads the user's Sims install lazily:

- On first use, builds an index of `.package` files in the install's Data directory
- Index maps TGI IDs to `(package_path, offset, size)` for fast lookup
- Index is cached under the app data directory
- Index is rebuilt when the Sims install directory's `GameVersion.txt` (or equivalent patch marker) changes

The index is not a full resource extraction; resources are read on demand.

### 11.2 Tuning Parsing

Sims 4 tuning is XML. The `tuning` module:

- Parses tuning XML into a typed tree (using `lxml` for stability and XPath)
- Represents each tunable field as a node with type, value, and references
- Handles special fields: resource references (`TunableReference`), lists, variants
- Preserves unknown fields so clones don't lose data

### 11.3 Clone Operation

To clone a reference object:

1. Read the reference object's tuning resource by ID
2. Parse to typed tree
3. Deep copy the tree
4. Assign new instance IDs to all resource references that must be unique (not shared with the base game)
5. Apply archetype handler's targeted edits (e.g., light color, moodlet reference)
6. Serialize back to XML

### 11.4 Targeted Edit Module

Each archetype handler specifies which fields it can edit. The edit module enforces that only declared fields are modified. This prevents accidental breakage of inherited behavior.

For the MVP archetypes, the editable field lists are documented in each handler module.

### 11.5 Validation of Cloned Tuning

After cloning, tuning is validated:

- All resource references are resolvable (either to new resources the app is creating, or to base-game resources that exist in the user's install)
- No syntactically invalid XML
- No fields with out-of-range values per the archetype handler's configuration schema

Validation failures here are blocking errors.

---

## 12. Validation Engine

### 12.1 Structure

The validation engine is a registry of check functions. Each check:

- Declares its target entity type
- Returns zero or more `ValidationIssue`s
- Is pure (depends only on passed-in state, no side effects)

### 12.2 Check Categories

- **Integrity checks** — database consistency, referential integrity, schema conformance
- **Asset checks** — required files exist, are readable, are non-corrupted
- **Content checks** — metadata completeness, valid category assignments, non-empty names
- **Structural checks** — DBPF header valid, TGI IDs non-colliding, required resources present
- **Tuning checks** — cloned tuning valid, references resolvable
- **Archetype checks** — functional overlay archetype compatible with item template

### 12.3 Execution

`validate(collection_id)`:

1. Loads collection and all related entities
2. Runs all applicable checks in parallel where independent
3. Aggregates results into a `ValidationResult`
4. Returns result (does not persist unless explicitly requested)

Validation is fast (target <1 second for a 12-item collection) so it can run on demand.

### 12.4 Messages

Every `ValidationIssue` has both a `message_user` (plain language) and `message_admin` (full detail). The creator UI shows the user messages; admin mode shows both.

---

## 13. Auto-Install Mechanism

### 13.1 Mods Folder Detection

- **macOS:** `~/Documents/Electronic Arts/The Sims 4/Mods/`
- **Windows:** `%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Mods\`

Detection checks the path exists. If not, the app shows a manual-override UI where the user can point at their Mods folder.

### 13.2 Pre-Install Checks

- Mods folder exists and is writable
- Sufficient disk space (at least 2x the package size)
- Script mods enabled in Sims (for functional items; warning if not detected, not blocker)

### 13.3 Conflict Handling

When a file with the same name exists:

- SHA-256 compared
- If identical: skip, log "already installed"
- If different: UI prompts user with options:
  - Overwrite the existing file
  - Rename the new file (with timestamp suffix)
  - Skip installation (keep the exported file in the project folder only)

### 13.4 Atomicity

File copy is atomic: write to a temp file in the Mods folder, fsync, then rename. This prevents partial writes if the app crashes mid-copy.

### 13.5 Script Mods Detection

For functional items, the app checks whether script mods are enabled in Sims 4 (via inspecting `Options.ini` or equivalent). If disabled, a warning is shown with instructions to enable.

---

## 14. Admin Mode Architecture

### 14.1 Gating

Admin mode is entered via:

- Keyboard shortcut (macOS: ⌘⇧A, Windows: Ctrl+Shift+A)
- Menu bar item under a "Developer" menu

On entry, the frontend sends `system.set_admin_mode(true)` to the sidecar. The sidecar flags admin endpoints as available.

Admin mode is not a security boundary. It exists to prevent the primary creator from accidentally accessing maintainer features.

### 14.2 Admin Endpoints

- `admin.template.list` / `admin.template.get` / `admin.template.update` / `admin.template.promote`
- `admin.mesh.import_from_sims` / `admin.mesh.list_tier2`
- `admin.logs.query` / `admin.logs.tail`
- `admin.jobs.list` / `admin.jobs.detail`
- `admin.reference.list` / `admin.reference.get_tuning`
- `admin.config.get` / `admin.config.set`
- `admin.rebuild` — deterministic rebuild of an export from saved project state

### 14.3 Admin UI Architecture

Admin screens live under `/admin/*` routes (memory routed). A top-level `AdminModeGate` component blocks rendering of admin screens unless admin mode is active in Redux state. If admin mode is exited while on an admin screen, the user is redirected to the home screen.

### 14.4 Admin-Only Features

- Full log detail (user mode shows only user-level messages)
- Full error stack traces
- Per-job artifact browsing
- Template schema editing
- Reference object tuning inspection

---

## 15. Cross-Platform Considerations

### 15.1 Path Resolution

Platform-specific paths are owned by a single module (`sidecar/config/paths.py`):

| Purpose | macOS | Windows |
|---|---|---|
| App data | `~/Library/Application Support/AISimsCreator/` | `%APPDATA%\AISimsCreator\` |
| Logs | `~/Library/Logs/AISimsCreator/` | `%APPDATA%\AISimsCreator\logs\` |
| Projects | `~/Documents/AISimsCreator/projects/` | `%USERPROFILE%\Documents\AISimsCreator\projects\` |
| Sims install | Varies by installer, detected | Varies by installer, detected |
| Mods folder | `~/Documents/Electronic Arts/The Sims 4/Mods/` | `%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Mods\` |

All other code uses the path module rather than constructing paths directly.

### 15.2 File Encoding

- All text files UTF-8
- Line endings normalized to `\n` internally; converted to platform native only when a file is explicitly for external consumption

### 15.3 Blender Invocation

Blender path detection differs per platform:

- **macOS:** `/Applications/Blender.app/Contents/MacOS/Blender` is the canonical path
- **Windows:** typically `C:\Program Files\Blender Foundation\Blender X.Y\blender.exe`, falls back to registry lookup

The Blender path, once detected or user-specified, is persisted in config.

### 15.4 Subprocess Handling

Subprocess invocations on Windows require `shell=False` and explicit argument lists; PowerShell arg parsing quirks are avoided. Paths with spaces are passed as single arguments, not concatenated strings.

### 15.5 Parity Testing

CI (future) and manual acceptance tests must execute on both platforms. The deterministic rebuild test (MVP-AC-029) is the main parity gate: identical project state must produce byte-identical `.package` files on both platforms.

---

## 16. Error Handling, Logging, Observability

### 16.1 Error Taxonomy

Errors are categorized:

- **USER_INPUT_ERROR** — user input invalid (e.g., prompt empty)
- **CONFIG_ERROR** — configuration missing or invalid (e.g., Sims install not found)
- **DEPENDENCY_ERROR** — external dependency unavailable (Anthropic API down, Blender not installed)
- **GENERATION_ERROR** — AI call failed after retries
- **VALIDATION_ERROR** — project state failed validation
- **BUILD_ERROR** — DBPF build or tuning clone failed
- **INSTALL_ERROR** — file copy to Mods folder failed
- **INTERNAL_ERROR** — unexpected exception, bug

Every error has a unique code and both user-facing and admin-facing messages.

### 16.2 Error Flow

Within the sidecar, errors are caught at stage boundaries and converted to structured error responses. The frontend displays the user message; admin mode shows the admin message and stack trace.

### 16.3 Logging

Structured logging with `structlog`:

- Every log entry has timestamp, level, module, event name, and context fields
- Sensitive data (API keys, user prompts) is redacted in logs by default; admin mode can toggle verbose logging for debugging
- Log files rotate per session (one file per app launch)
- Log files older than 30 days are auto-deleted on startup

### 16.4 Observable Events

Key events logged at INFO level or above:

- App startup / shutdown
- Project create / open / close
- Generation job start / progress / complete / failed
- AI API call dispatched / completed / retried / failed
- Blender invocation
- DBPF package built
- Validation run
- Export completed
- Install completed
- Admin mode entered / exited

### 16.5 No Telemetry

Per PRD §8 and §19.9: no logs, metrics, or data are sent to any remote server. All observability is local.

---

## 17. Security and Privacy Implementation

### 17.1 Network Access

The sidecar makes outbound network calls only to:

- `api.anthropic.com` — AI inference
- `api.replicate.com` — image generation
- Anthropic's and Replicate's CDN domains for model result downloads

Any other outbound traffic indicates a bug or compromise. Network calls are logged.

### 17.2 Credentials

API keys for Anthropic and Replicate are stored in:

- **macOS:** Keychain, accessed via `keyring` Python library
- **Windows:** Windows Credential Manager, accessed via `keyring`

Keys never appear in logs, project files, or UI. First-run flow prompts the user to paste keys; admin mode includes a "replace API keys" action.

### 17.3 File System Access

The sidecar reads from:

- App data directory (read-write)
- Projects directory (read-write)
- Logs directory (write)
- User's Sims install directory (**read-only**)
- User's Mods folder (**write**, for installed packages)
- Blender executable (read-only, to invoke)

The Sims install directory is never written to. A guard in the `sims_install` module enforces read-only access.

### 17.4 Process Isolation

The Python sidecar runs with the same privileges as the Tauri host. No privilege escalation. Tauri's security model restricts what the frontend can access directly, so all sensitive operations go through the sidecar.

### 17.5 User Data

All user data (prompts, projects, exports) stays local. The only data sent outside the machine is:

- Prompts and template schemas sent to Anthropic for reasoning
- Texture generation prompts sent to Replicate for image generation

These are necessary for the product to function. Users are informed at first launch. Admin mode includes a "privacy summary" that shows exactly what data is sent where.

---

## 18. Testing Architecture

### 18.1 Test Layers

- **Unit tests (Python):** pytest, coverage target >80% for non-UI modules. Mock external services.
- **Unit tests (TypeScript):** vitest + React Testing Library for component behavior.
- **Integration tests:** pytest fixtures that spin up the sidecar, inject mocked external clients, and run full pipelines end-to-end.
- **Manual acceptance tests:** the MVP-AC-### list executed against built app on both platforms.

### 18.2 Mock Strategy

External clients (Anthropic, Replicate, Blender, Sims install reader) are injected as dependencies. Tests use mock implementations that return canned responses. A small library of fixture responses lives in `tests/fixtures/`.

### 18.3 Integration Test Environment

A synthetic Sims install fixture (stripped-down, rights-respecting) is NOT bundled with tests. Instead, integration tests that need Sims install data use a set of anonymized sample tuning files committed to the repo under `tests/fixtures/sims_samples/`. These are structurally representative but do not include proprietary EA content.

For tests that require genuine Sims install integration, tests are gated behind an environment variable and skipped in normal CI. Developers with a local install can opt in.

### 18.4 Determinism Tests

Critical determinism test cases:

- Identical project state produces byte-identical `.package` files on rebuild
- Same project rebuilt on Mac and Windows produces byte-identical `.package` files
- TGI ID generation is stable across runs

### 18.5 Visual Quality Tests

Non-automated. Phase 1 POC and Phase 7 acceptance run visual checks in-game. These are documented as signed-off test artifacts with screenshots.

---

## 19. Dependencies

### 19.1 Python (sidecar)

- Runtime: Python 3.12
- Core: `pydantic>=2.0`, `httpx`, `structlog`, `yoyo-migrations`
- AI: `anthropic`, `replicate`
- Image: `Pillow`, `numpy`
- XML: `lxml`
- Mesh: `pygltflib`
- DBPF: (selected in Phase 1 POC — `sims4-tools` or custom)
- Platform: `keyring`
- Testing: `pytest`, `pytest-asyncio`, `pytest-mock`

Complete pinned list lives in `pyproject.toml`.

### 19.2 Frontend

- Runtime: Node 20+ for dev, Tauri-bundled webview for runtime
- Core: `react@18`, `react-dom@18`, `@reduxjs/toolkit`, `react-redux`, `react-router-dom@6`
- UI: `tailwindcss`, `@radix-ui/*` primitives as needed
- Build: `vite`, `typescript`
- Tauri: `@tauri-apps/api`, `@tauri-apps/cli`
- Testing: `vitest`, `@testing-library/react`

### 19.3 External (user-installed or bundled)

- **Blender** — user-installed prerequisite. Minimum version: 4.0 (assumption for MVP).
- **Sims 4** — user-installed prerequisite. Any current patched version.

### 19.4 Development Tooling

- `ruff` — Python linting and formatting
- `mypy` — Python type checking
- `eslint`, `prettier` — TypeScript linting and formatting
- `pre-commit` — git hooks

---

## 20. Deployment and Build

### 20.1 Build Process

Monorepo has a top-level build script:

- `scripts/build.sh` (macOS) / `scripts/build.ps1` (Windows)

The script:

1. Installs Python dependencies into a virtualenv
2. Bundles the Python sidecar into a standalone binary (pyoxidizer or PyInstaller; chosen during Phase 0)
3. Generates TypeScript types from Pydantic schemas (`scripts/generate_types.py`)
4. Builds the frontend (`cd frontend && npm run build`)
5. Invokes Tauri build (`cargo tauri build`)
6. Produces platform-native installer in `target/release/bundle/`

### 20.2 Versioning

Semantic versioning: `MAJOR.MINOR.PATCH`. MVP v1.0 is 1.0.0.

Version string baked into the app binary and reported by `system.version` IPC call.

### 20.3 Distribution

Installers distributed as direct downloads for MVP. No auto-update mechanism (per PRD §8).

### 20.4 CI

No hosted CI required for MVP. Local test runs and manual acceptance testing suffice. A future post-MVP concern is to add GitHub Actions for automated test runs on PRs.

---

## 21. Open Technical Questions

These are tracked for resolution during implementation. They do not block the TAD; they are items the MVP Spec §8 and §12 identify as decisions to be made or refined during specific phases.

1. **Sidecar bundling tool** (`pyoxidizer` vs `PyInstaller` vs alternative) — resolved in Phase 0 based on cross-platform reliability.
2. **DBPF library choice** (D-1) — resolved in Phase 1 POC.
3. **Primary image generation model** (D-2) — resolved in Phase 1 POC.
4. **Normal/specular derivation strategy** (D-3) — resolved in Phase 1 POC.
5. **Exact base-game reference object IDs** (D-4) — resolved in Phase 5.
6. **Blender render recipe specifics** (D-5) — resolved in Phase 1 POC.
7. **Texture resolution policy** (D-6) — confirmed during Phase 1 POC.
8. **Thumbnail dimensions exact** (T-9 assumption) — confirmed when verifying against actual Sims catalog behavior.
9. **Build/Buy category taxonomy mapping** — sourced from Sims 4 documentation during Phase 4.
10. **Sims patch detection mechanism** — verified when building the resource indexer in Phase 5.

---

## 22. Architectural Boundaries — What This Document Is Not

This TAD defines the architecture and pipeline structure but does not contain:

- **Exact IPC method signatures and parameter schemas.** Those live in the API Specification document.
- **Visual diagrams.** Those live in the Architecture Diagrams document.
- **Detailed per-screen UI designs.** Those are implementation choices within the React frontend.
- **Hour-by-hour task breakdowns.** Those are the MVP Specification's concern.
- **Exact tuning field names or resource IDs.** Those are identified during Phase 5 and recorded in code + inline documentation.

---

## 23. Executive Summary

AI Sims Creator is a monorepo Tauri v2 + React frontend paired with a Python 3.12 sidecar communicating via stdio JSON-RPC. The sidecar is a single persistent asyncio process owning all generation logic, AI integrations, and file operations.

Data is modeled via Pydantic v2 with types auto-generated for TypeScript. Persistence is SQLite per project with yoyo-migrations. Projects are self-contained folders containing the database, assets, and exports.

The generation pipeline is composed of discrete stages with clean schemas: collection planning (Claude Sonnet), per-item spec generation (Claude Sonnet), texture generation (Replicate image model), thumbnail rendering (Blender subprocess), DBPF packaging (deterministic), validation (structural), auto-install (direct copy to Mods folder).

Four functional archetype handlers (light, audio, mirror, moodlet) clone base-game tuning from the user's Sims install and apply targeted edits based on user configuration.

The template library is the central technical investment: 19 Tier 1 curated primitives with rich schemas, plus a Tier 2 importer for user-added base-game meshes. The library grows through admin-mode workflows without architectural change.

Cross-platform parity is enforced through isolated path-handling modules, deterministic build pipelines, and byte-equality tests on rebuilt exports across macOS and Windows.

No telemetry. No auto-update. Local-only observability. API keys in platform keyrings. Sims install accessed read-only.

The architecture supports the PRD's forward paths (Maxis Match visual style, additional archetypes, AI mesh generation exploration, multi-user features) without requiring rework of the foundational layers.

---

*End of TAD v1.0*
