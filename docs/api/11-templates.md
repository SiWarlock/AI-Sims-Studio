# API Spec — templates.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §14

> templates.list, templates.get.

---

## 14. Namespace: `templates.*`

### 14.1 `templates.list`

**Direction:** Request / Response
**Admin-only:** No
**Description:** List all templates available.

**Params:**

```json
{
  "tier": "tier_1",
  "include_tier_2": true
}
```

Both fields optional. If `tier` is omitted, both tiers are returned.

**Result:**

```json
{
  "templates": [
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
      "compatible_archetypes": ["light_on_off", "moodlet_emitter"],
      "example_objects": ["lava lamp", "vase", "candle", "small lamp"],
      "thumbnail_preview_path": "/path/to/preview.png"
    }
  ]
}
```

### 14.2 `templates.get`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Get full template detail including texture zones.

**Params:**

```json
{
  "template_id": "cylindrical_small_tabletop"
}
```

**Result:**

```json
{
  "template": { /* Template with all fields including texture_zones */ }
}
```

---
