# MVP Spec — Functional Archetype → Reference Object Mapping

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §7

> Light on/off, audio device, mirror, moodlet emitter — reference targets, selection criteria, compatible templates, and configuration parameters.

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
