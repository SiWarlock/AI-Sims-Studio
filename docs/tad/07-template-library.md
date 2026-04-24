# TAD — Template Library Implementation

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §9

> Template registry, storage layout, manifest format, Tier 2 importer, Tier 2 → Tier 1 promotion, graceful degradation.

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
