# Template Registry — Claude Code Guidance

You are working inside `sidecar/aisc/templates/`. This package manages the **template registry**: the loader, query API, and schema validator for the 19 Tier 1 primitives (shipped) and the user-imported Tier 2 templates (admin mode).

Reminder: `sidecar/CLAUDE.md` and `CODING_STANDARDS.md` set the general rules. This file covers rules specific to template registry work.

This is the registry/loader code. The actual `.glb` mesh files and authoring standard live in `/templates/` at the repo root (a different `CLAUDE.md` there covers Blender authoring).

## What This Package Does

1. Loads Tier 1 template manifests from the bundled `/templates/` directory at sidecar startup.
2. Loads Tier 2 template manifests from the user's app data directory.
3. Validates template schemas against `Template` Pydantic models.
4. Exposes a typed query API (by shape class, archetype compatibility, dimension range).
5. Handles Tier 2 → Tier 1 promotion via admin mode.

## Layout

```
templates/                   (inside sidecar/aisc/)
├── __init__.py              # public API re-exports
├── registry.py              # TemplateRegistry class
├── loader.py                # manifest loading, schema validation
├── query.py                 # typed query helpers
├── tier2_importer.py        # read base-game mesh → Tier 2 template
├── promotion.py             # Tier 2 → Tier 1 schema authoring + move
└── schema_validator.py      # extra validation beyond Pydantic
```

Do not confuse this with `/templates/` at the repo root (which contains the actual `.glb` files).

## Hard Rules

1. **Registry is loaded once at sidecar startup** and cached in memory. Changes via admin mode (promotion, editing) invalidate the cache and reload.
2. **Template IDs are stable.** Once a Tier 1 template has an ID, do not rename it. Projects reference templates by ID; renaming breaks existing projects.
3. **Tier 2 templates degrade gracefully** for fields they don't define (e.g., missing texture zones). The loader fills in sentinel "unknown" values; callers must handle those without crashing.
4. **Schema validation is strict for Tier 1, lenient for Tier 2.** Tier 1 must pass full Pydantic `extra="forbid"`. Tier 2 allows partial data.
5. **Never modify template files from this package.** Editing Tier 1 manifests is the admin editor's job. Importing Tier 2 uses `tier2_importer`. Promotion uses `promotion`. Each has a single well-defined responsibility.
6. **Template queries are pure.** `registry.query(...)` never modifies state.

## Manifest Format

Authoritative format lives in `docs/tad/07-template-library.md` §9.3. Quick reference:

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
    {"label": "base", "uv_bounds": {...}, "typical_materials": [...]},
    {"label": "vessel", "uv_bounds": {...}, "typical_materials": [...]},
    {"label": "cap", "uv_bounds": {...}, "typical_materials": [...]}
  ],
  "compatible_archetypes": ["light_on_off", "moodlet_emitter"],
  "example_objects": ["lava lamp", "vase", "candle", "small lamp"],
  "authoring_notes": "...",
  "schema_version": 1
}
```

The full Pydantic model for this is in `sidecar/aisc/schemas/template.py`.

## Registry API

```python
# sidecar/aisc/templates/registry.py

class TemplateRegistry:
    def __init__(self) -> None:
        self._templates: dict[str, Template] = {}

    async def load(self) -> None:
        """Load Tier 1 from bundled dir, Tier 2 from app data. Called once at startup."""
        ...

    def get(self, template_id: str) -> Template:
        """Return the Template or raise TemplateNotFoundError."""
        ...

    def query(
        self,
        *,
        shape_class: str | None = None,
        footprint_type: FootprintType | None = None,
        compatible_archetype: ArchetypeId | None = None,
        tier: TemplateTier | None = None,
    ) -> list[Template]:
        """Return templates matching all provided criteria."""
        ...

    def all_tier_1(self) -> list[Template]: ...
    def all_tier_2(self) -> list[Template]: ...

    async def reload(self) -> None:
        """Discard cache and reload. Called after admin mode edits."""
        ...
```

Callers in other packages (planning stage, admin mode, IPC handlers) depend on this interface. Don't break it without a migration.

## Tier 2 Importer

`tier2_importer` reads a base-game mesh from the user's Sims install via `sims_install` and extracts available metadata:

```python
async def import_from_base_game(
    base_game_object_id: str,
    override_template_id: str | None = None,
) -> Template:
    """
    Import a base-game object mesh as a Tier 2 template.

    Auto-extracted: mesh bounds → dimension_ranges, footprint inferred from Sims
    metadata, shape class heuristically assigned. Does NOT populate texture_zones
    or compatible_archetypes — those are admin-authored during promotion.
    """
    ...
```

Rules:

- Do not assume texture zones — imported Tier 2 templates have `texture_zones=[]` until promoted.
- Do not auto-assign archetype compatibility — that's a deliberate admin decision.
- Store the import provenance (`source_package`, `base_game_object_id`, `imported_at`) in the manifest for audit trail.

## Promotion

`promotion` takes a Tier 2 template + authored schema fields and produces a Tier 1 template:

```python
async def promote_to_tier_1(
    tier2_template_id: str,
    authored_schema: Tier1PromotionInput,
) -> Template:
    """
    Author full schema on a Tier 2 template and promote. The template moves from
    app_data/tier2_templates/ to templates/decor/ or templates/furniture/ based
    on shape class.
    """
    ...
```

After promotion, the registry reloads and the newly-promoted template is available for use in projects.

## Testing

- **Fixtures:** `tests/fixtures/templates/` has sample manifests for valid Tier 1, valid Tier 2, and invalid manifests.
- **Test coverage required:** loader error handling, schema validation, query correctness across all predicates, Tier 2 → Tier 1 promotion round trip.
- **Don't use real `.glb` files in unit tests.** Mock the mesh file presence check.

## Load These Docs When...

- Any template work: `docs/tad/07-template-library.md`
- The Tier 1 roster (exact IDs): `docs/mvp/02-template-roster.md`
- Template authoring in Blender: `/templates/CLAUDE.md` at the repo root
- Admin template UI: `docs/tad/12-admin-mode.md` + `docs/api/12-admin.md`
- Phase 2 work: `docs/mvp/07-phase-2-templates.md`
