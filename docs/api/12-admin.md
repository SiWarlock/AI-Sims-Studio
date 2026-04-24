# API Spec — admin.* Namespace (admin-mode-gated)

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §15

> admin.template.*, admin.logs.*, admin.jobs.*, admin.reference.*, admin.rebuild, admin.cost_summary.

---

## 15. Namespace: `admin.*`

All methods in this namespace require admin mode to be active. Calls while admin mode is inactive return `ADMIN_REQUIRED` error.

### 15.1 `admin.template.update`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Update a Tier 1 template's editable metadata (texture zones, archetype compatibility, example objects, authoring notes). Mesh file and core shape class are not editable here (re-author in Blender for that).

**Params:**

```json
{
  "template_id": "cylindrical_small_tabletop",
  "updates": {
    "texture_zones": [ /* TextureZoneDef[] */ ],
    "compatible_archetypes": ["light_on_off", "moodlet_emitter"],
    "example_objects": ["lava lamp", "vase", "candle"],
    "authoring_notes": "Updated zones for Y2K use cases."
  }
}
```

**Result:**

```json
{
  "updated": true
}
```

### 15.2 `admin.template.import_from_sims`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Import a base-game mesh as a Tier 2 template.

**Params:**

```json
{
  "base_game_object_id": "ea_object_12345",
  "template_id_override": null
}
```

**Result:**

```json
{
  "template_id": "tier2_armchair_modern_001",
  "tier": "tier_2",
  "imported_from": "ea_object_12345",
  "auto_extracted": {
    "shape_class": "seat_single",
    "dimension_ranges": { /* ... */ },
    "footprint_type": "seat_single"
  }
}
```

### 15.3 `admin.template.promote`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Promote a Tier 2 template to Tier 1 by authoring its full schema.

**Params:**

```json
{
  "tier2_template_id": "tier2_armchair_modern_001",
  "authored_schema": {
    "id": "seat_single_upholstered_modern",
    "texture_zones": [ /* TextureZoneDef[] */ ],
    "compatible_archetypes": [],
    "example_objects": ["modern armchair", "accent chair"],
    "authoring_notes": "Promoted from Tier 2 base-game import."
  }
}
```

**Result:**

```json
{
  "promoted_template_id": "seat_single_upholstered_modern",
  "tier": "tier_1"
}
```

### 15.4 `admin.template.list_tier2`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** List Tier 2 templates and their import source info.

**Params:** none

**Result:**

```json
{
  "templates": [
    {
      "id": "tier2_armchair_modern_001",
      "imported_at": "2026-04-21T10:00:00.000Z",
      "source_reference": { "base_game_object_id": "ea_object_12345", "source_package": "Data/.../xyz.package" }
    }
  ]
}
```

### 15.5 `admin.logs.query`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Query the log store.

**Params:**

```json
{
  "filter": {
    "min_level": "warning",
    "module": "texture_gen",
    "since": "2026-04-21T15:00:00.000Z",
    "until": "2026-04-21T17:00:00.000Z",
    "item_id": null,
    "job_id": null
  },
  "limit": 200
}
```

**Result:**

```json
{
  "entries": [
    {
      "timestamp": "2026-04-21T15:52:13.456Z",
      "level": "warning",
      "module": "texture_gen",
      "event": "replicate_retry",
      "context": { "model": "flux-1.1-pro", "retry_count": 1, "reason": "timeout" }
    }
  ],
  "has_more": false
}
```

### 15.6 `admin.logs.tail`

**Direction:** Notification subscription (returns an active stream)
**Admin-only:** Yes
**Description:** Subscribe to live log events. Sidecar emits `log.emitted` notifications until unsubscribed.

**Params:**

```json
{
  "min_level": "info"
}
```

**Result:**

```json
{
  "subscription_id": "sub_logs_abc"
}
```

Unsubscribe via `admin.logs.untail(subscription_id)`.

### 15.7 `admin.jobs.list`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** List jobs with filtering.

**Params:**

```json
{
  "filter": {
    "project_id": null,
    "kind": null,
    "status": null,
    "since": null
  },
  "limit": 100
}
```

**Result:**

```json
{
  "jobs": [ /* BuildJob[] */ ]
}
```

### 15.8 `admin.jobs.detail`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Get full detail for a specific job including artifacts, generation attempts, and child jobs.

**Params:**

```json
{
  "job_id": "job_abc123"
}
```

**Result:**

```json
{
  "job": { /* BuildJob */ },
  "generation_attempts": [ /* GenerationAttempt[] */ ],
  "child_jobs": [ /* BuildJob[] */ ]
}
```

### 15.9 `admin.reference.list`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** List base-game reference objects by category.

**Params:**

```json
{
  "category": "lamps",
  "limit": 50
}
```

**Result:**

```json
{
  "objects": [
    {
      "id": "ea_object_67890",
      "display_name": "Luminaria Spire",
      "category": "lamps",
      "source_package": "Data/.../objects.package",
      "tags": ["light", "floor", "tall"]
    }
  ]
}
```

### 15.10 `admin.reference.get_tuning`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Get the raw tuning XML for a base-game reference object.

**Params:**

```json
{
  "base_game_object_id": "ea_object_67890"
}
```

**Result:**

```json
{
  "tuning_xml": "<?xml version=\"1.0\"?>\n<I ...>...</I>",
  "resource_id": "0xABC123...",
  "source_package": "Data/.../objects.package"
}
```

### 15.11 `admin.rebuild`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Deterministically rebuild an export from saved project state. Returns comparison with prior artifact if one exists.

**Params:**

```json
{
  "collection_id": "6ba7b810-...",
  "compare_with_artifact_id": "uuid-artifact-1"
}
```

**Result:**

```json
{
  "new_artifact_id": "uuid-artifact-2",
  "new_sha256": "def456...",
  "prior_sha256": "abc123...",
  "byte_identical": true
}
```

### 15.12 `admin.cost_summary`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Get cost tracking summary.

**Params:**

```json
{
  "scope": "session",
  "project_id": null
}
```

`scope` is one of `"session"` · `"project"` · `"day"` · `"all_time"`.

**Result:**

```json
{
  "scope": "session",
  "anthropic_cost_usd": 0.14,
  "replicate_cost_usd": 2.32,
  "total_cost_usd": 2.46,
  "breakdown": {
    "planning_calls": 2,
    "spec_gen_calls": 12,
    "texture_gen_calls": 108,
    "thumbnail_renders": 12
  }
}
```

---
