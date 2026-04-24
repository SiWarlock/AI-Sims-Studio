# API Spec — functional.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §10

> functional.list_compatible_archetypes, functional.available_moodlets, functional.preview, functional.create, functional.update, functional.delete.

---

## 10. Namespace: `functional.*`

### 10.1 `functional.list_compatible_archetypes`

**Direction:** Request / Response
**Admin-only:** No
**Description:** List archetypes compatible with an item's template.

**Params:**

```json
{
  "item_id": "uuid-item-1"
}
```

**Result:**

```json
{
  "archetypes": [
    {
      "id": "light_on_off",
      "display_name": "Light (on/off)",
      "description": "Turns on and off, emits colored light, affects room ambience.",
      "configuration_schema": {
        "light_color": { "type": "hex_color", "required": true, "default": "#FFAA00" },
        "intensity": { "type": "enum", "values": ["low", "medium", "high"], "required": true, "default": "medium" },
        "always_on": { "type": "boolean", "required": false, "default": false }
      }
    },
    {
      "id": "moodlet_emitter",
      "display_name": "Mood Emitter",
      "description": "Broadcasts a moodlet to Sims nearby.",
      "configuration_schema": {
        "moodlet_id": { "type": "enum_ref", "values_endpoint": "functional.available_moodlets", "required": true },
        "duration_hours": { "type": "integer", "min": 1, "max": 8, "required": true, "default": 2 },
        "emission_radius_tiles": { "type": "integer", "min": 1, "max": 4, "required": true, "default": 2 }
      }
    }
  ]
}
```

### 10.2 `functional.available_moodlets`

**Direction:** Request / Response
**Admin-only:** No
**Description:** List the curated safe moodlets available for the moodlet emitter archetype.

**Params:** none

**Result:**

```json
{
  "moodlets": [
    { "id": "focused", "display_name": "Focused", "icon_hint": "brain" },
    { "id": "inspired", "display_name": "Inspired", "icon_hint": "lightbulb" },
    { "id": "happy", "display_name": "Happy", "icon_hint": "smile" },
    { "id": "playful", "display_name": "Playful", "icon_hint": "party" },
    { "id": "flirty", "display_name": "Flirty", "icon_hint": "heart" },
    { "id": "confident", "display_name": "Confident", "icon_hint": "star" }
  ]
}
```

### 10.3 `functional.preview`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Validate a proposed archetype configuration and return a human-readable summary without committing.

**Params:**

```json
{
  "item_id": "uuid-item-1",
  "archetype": "light_on_off",
  "configuration": {
    "light_color": "#FF00AA",
    "intensity": "medium",
    "always_on": false
  }
}
```

**Result:**

```json
{
  "valid": true,
  "summary": "This lava lamp will function as a light that Sims can turn on and off. When on, it emits pink light at medium intensity.",
  "warnings": []
}
```

**Errors:** `INVALID_CONFIGURATION`, `INCOMPATIBLE_ARCHETYPE`

### 10.4 `functional.create`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Create a functional overlay on an item. Runs the clone pipeline.

**Params:** Same as `functional.preview`.

**Result:**

```json
{
  "overlay_id": "uuid-overlay-1",
  "job_id": "job_overlay_build_123"
}
```

### 10.5 `functional.update`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Update the configuration of an existing functional overlay. Triggers rebuild.

**Params:**

```json
{
  "overlay_id": "uuid-overlay-1",
  "configuration": {
    "light_color": "#00FF00",
    "intensity": "high"
  }
}
```

**Result:**

```json
{
  "job_id": "job_overlay_rebuild_456"
}
```

### 10.6 `functional.delete`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Remove a functional overlay. The underlying item reverts to decorative-only.

**Params:**

```json
{
  "overlay_id": "uuid-overlay-1"
}
```

**Result:**

```json
{
  "deleted": true
}
```

---
