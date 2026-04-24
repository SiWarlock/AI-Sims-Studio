# MVP Spec — Template Roster

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §6

> The 19 Tier 1 template primitives that ship with MVP, with schema and authoring standards.

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
