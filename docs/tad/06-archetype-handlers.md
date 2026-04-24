# TAD — Archetype Handlers

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §8

> Common handler interface, per-archetype implementation notes (light, audio, mirror, moodlet), curated moodlet list.

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
