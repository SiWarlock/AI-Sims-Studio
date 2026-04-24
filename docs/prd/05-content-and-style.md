# PRD — Content Categories, Visual Style, and Template Library

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §14, §15, §16

> Supported content categories and archetypes, visual style strategy (semi-Alpha first), two-tier template library model.

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
