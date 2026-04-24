# Template Library — Blender Authoring Guidance

You are working inside `/templates/` at the repo root. This directory contains the **actual mesh files and manifests** for the Tier 1 template library. The Python loader that reads these files lives in `sidecar/aisc/templates/` (with its own `CLAUDE.md`).

This file is about authoring templates in Blender, not writing Python code.

## Layout

```
templates/
├── decor/
│   ├── cylindrical_small_tabletop/
│   │   ├── mesh.glb
│   │   ├── manifest.json
│   │   └── thumbnail_preview.png       # maintainer-facing, not in-game
│   ├── cylindrical_tall_floor/
│   ├── boxy_electronic_small_tabletop/
│   ... (11 decor primitives total)
├── furniture/
│   ├── seat_single_upholstered/
│   ├── seat_multi_upholstered/
│   ... (8 furniture primitives total)
```

Tier 2 templates do not live here. They live under the user's app data directory at runtime. Only Tier 1 (curated, shipped) templates belong in `/templates/`.

## Authoring Standard

Each Tier 1 template mesh must satisfy:

1. **Polygon count:** 1500–3000 triangles. Semi-Alpha style target.
2. **Single mesh object** per template (no nested objects, no multi-part rigs).
3. **Clean UV unwrap with no overlapping islands.** Every face has a unique UV assignment.
4. **Texture zones explicitly marked and labeled** in the UV layout. Each zone occupies a distinct UV rectangle. Zone labels match the manifest exactly.
5. **Proper Sims footprint and slot data** where applicable. Footprint conventions match `docs/tad/02-data-model.md` (see `FootprintType`).
6. **Center pivot** at the object's logical base (bottom center for tabletop/floor, wall surface for wall-mounted).
7. **Y-up orientation.** Z-forward.
8. **No materials assigned.** Templates ship unmaterialized; textures are generated per project. Leave material slots empty or with a single default material named "Base".
9. **Exported as `.glb`** (GLTF 2.0 binary) with embedded geometry only (no textures, no materials beyond the slot placeholder).

## UV Zone Conventions

Each template declares its texture zones in `manifest.json`. The UV bounds must match the actual layout in the mesh file.

Convention: zones occupy non-overlapping axis-aligned rectangles in UV space (0..1, 0..1). Example for `cylindrical_small_tabletop`:

- `base`: u=0.0-0.5, v=0.0-0.25 (bottom-left quadrant, roughly)
- `vessel`: u=0.0-1.0, v=0.25-0.9 (spans middle, largest area)
- `cap`: u=0.5-1.0, v=0.0-0.25 (bottom-right quadrant)

Document the intended material types per zone in the manifest (`typical_materials` field): e.g., vessel zone expects glass/translucent plastic/ceramic.

## Footprint and Slots

Sims 4 objects have two spatial concepts:

- **Footprint:** the floor tiles the object occupies. Templates declare `footprint_type` matching the enum in `docs/tad/02-data-model.md`.
- **Slots:** points where Sims interact with the object or where other objects can sit on top (e.g., items on a tabletop). For most decor templates, the slot data is inherited from the base-game reference when functional; for pure decor, no slot data is needed.

For MVP, slot authoring for pure decor is minimal. Functional items inherit slot data from their cloned base-game tuning. Detailed slot authoring conventions are a post-MVP concern.

## Manifest File

Every template folder has a `manifest.json` matching the schema in `sidecar/aisc/schemas/template.py`. Full format lives in `docs/tad/07-template-library.md` §9.3.

Required fields:

- `id` (must match folder name)
- `tier` (always `"tier_1"` for files in this directory)
- `shape_class`
- `dimension_ranges` (min/max in cm)
- `footprint_type`
- `texture_zones` (list with labels, UV bounds, typical materials)
- `compatible_archetypes` (subset of the four MVP archetypes)
- `example_objects` (user-facing; used by AI matching)
- `schema_version` (always `1` in MVP)

Optional:

- `authoring_notes` (maintainer-facing)

## Thumbnail Preview

Each template folder has a `thumbnail_preview.png` rendered with a neutral placeholder texture. This is a **maintainer-facing visual reference** that helps admin users recognize templates in the admin template browser. It is not used in-game.

Generate it by running `scripts/render_template_previews.py` after authoring a new template. Do not hand-create.

## Git LFS

Template `.glb` files are stored via Git LFS because they're binary and can be large. Before committing a new template:

1. Ensure Git LFS is installed: `git lfs install`
2. Confirm `.glb` is in `.gitattributes` as LFS-tracked (it is, at repo root)
3. Commit normally; LFS transparently handles the upload

## The 19 Tier 1 Templates

Authoritative list: `docs/mvp/02-template-roster.md`.

**Decor/clutter (11):**

- `cylindrical_small_tabletop`
- `cylindrical_tall_floor`
- `boxy_electronic_small_tabletop`
- `boxy_electronic_medium_tabletop`
- `rectangular_wall_flat`
- `rectangular_wall_shelf`
- `organic_soft_tabletop`
- `planar_floor_rug`
- `stacked_low_tabletop`
- `thin_tall_tabletop`
- `rectangular_floor_standing`

**Furniture (8):**

- `seat_single_upholstered`
- `seat_multi_upholstered`
- `seat_dining_hard`
- `bed_single`
- `bed_double`
- `table_low`
- `table_standard`
- `storage_tall`

Adding a new Tier 1 template requires updating `docs/mvp/02-template-roster.md` as well.

## Authoring Workflow

1. Open `scripts/blender/template_starter.blend` (if available) or a blank file.
2. Model the shape following the authoring standard above.
3. UV unwrap with zones laid out as rectangles matching the manifest.
4. Verify polygon count (1500–3000).
5. Export as `.glb` with: selection-only, GLTF 2.0 binary, no materials, no textures.
6. Write `manifest.json` matching the schema.
7. Run `scripts/render_template_previews.py` to generate `thumbnail_preview.png`.
8. Run `python scripts/validate_template.py {template_id}` to check schema and mesh integrity.
9. Commit the folder. Git LFS handles the `.glb`.

## Common Pitfalls

- **Overlapping UV islands** will cause texture generation artifacts. Use Blender's "Select overlapping" to check.
- **Forgetting to apply transforms** before export leads to weird scale/rotation in-game. Apply all transforms (Ctrl+A) before export.
- **Triangulating inconsistently** can cause LOD issues. Leave the mesh as quads; let the exporter triangulate.
- **Including materials in the `.glb`** ships unnecessary data. Verify the export is geometry-only.
- **Mismatch between manifest `texture_zones` and actual UV layout.** This is the most common bug and the hardest to debug later. Triple-check.

## Load These Docs When...

- Adding a new template: `docs/tad/07-template-library.md` + `docs/mvp/02-template-roster.md`
- Understanding visual style (semi-Alpha): `docs/prd/05-content-and-style.md`
- Phase 2 (when all 19 templates are authored): `docs/mvp/07-phase-2-templates.md`
- Phase 1 POC (the single lava lamp template): `docs/mvp/06-phase-1-poc.md` Task 1.1
- Authoring new shape primitives beyond the MVP 19: defer to post-MVP; update the roster and this guide first
