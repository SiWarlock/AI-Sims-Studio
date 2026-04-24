# TAD — Data Model

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §4

> Pydantic v2 schemas for all 13 core entities, SQLite schema philosophy, project folder layout, migrations, and TypeScript codegen.

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
