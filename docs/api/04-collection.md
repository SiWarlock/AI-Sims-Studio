# API Spec — collection.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §7

> collection.create, collection.plan, collection.update_plan, collection.approve_plan, collection.generate, collection.cancel, collection.get.

---

## 7. Namespace: `collection.*`

### 7.1 `collection.create`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Create an additional collection within an existing project (MVP allows one collection per project, but schema permits more for v2).

**Params:**

```json
{
  "project_id": "550e8400-...",
  "name": "Y2K Bedroom Part 2",
  "mode": "collection",
  "target_item_count": 6,
  "style_preference": "semi_alpha"
}
```

**Result:**

```json
{
  "collection_id": "6ba7b810-..."
}
```

### 7.2 `collection.plan`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Generate a collection plan via the planning stage. Returns the proposed plan for user review.

**Params:**

```json
{
  "collection_id": "6ba7b810-..."
}
```

**Result:**

```json
{
  "plan": {
    "theme_summary": "A Y2K-themed bedroom collection featuring translucent electronics, holographic decor, and chrome accents.",
    "palette_direction": "Saturated purples and pinks, translucent plastics, chrome highlights",
    "material_direction": "Translucent polycarbonate, brushed metal, holographic foil",
    "items": [
      {
        "source_request": "lava lamp",
        "template_id": "cylindrical_small_tabletop",
        "template_match_confidence": 0.95,
        "template_match_warning": null,
        "order_index": 0
      },
      {
        "source_request": "CD player",
        "template_id": "boxy_electronic_small_tabletop",
        "template_match_confidence": 0.91,
        "template_match_warning": null,
        "order_index": 1
      },
      {
        "source_request": "hamster wheel",
        "template_id": "cylindrical_small_tabletop",
        "template_match_confidence": 0.32,
        "template_match_warning": "No template closely matches 'hamster wheel' — the closest primitive is a small cylindrical tabletop shape. This may not look convincingly like a hamster wheel.",
        "order_index": 2
      }
    ]
  }
}
```

**Errors:** `COLLECTION_NOT_FOUND`, `AI_CALL_FAILED`, `AI_MALFORMED_RESPONSE`

### 7.3 `collection.update_plan`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Update the plan with user edits (add, remove, reorder, rename items).

**Params:**

```json
{
  "collection_id": "6ba7b810-...",
  "items": [
    {
      "source_request": "lava lamp",
      "template_id": "cylindrical_small_tabletop",
      "order_index": 0
    },
    {
      "source_request": "CD player",
      "template_id": "boxy_electronic_small_tabletop",
      "order_index": 1
    }
  ]
}
```

**Result:**

```json
{
  "updated": true,
  "item_count": 2
}
```

### 7.4 `collection.approve_plan`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Lock the plan and mark it ready for generation. Items are created in `planned` state.

**Params:**

```json
{
  "collection_id": "6ba7b810-..."
}
```

**Result:**

```json
{
  "item_ids": ["uuid-item-1", "uuid-item-2"]
}
```

### 7.5 `collection.generate`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Kick off full generation for the collection. Returns immediately with a job ID; progress is delivered via notifications.

**Params:**

```json
{
  "collection_id": "6ba7b810-...",
  "swatch_count": 3
}
```

**Result:**

```json
{
  "job_id": "job_abc123",
  "started_at": "2026-04-21T15:45:00.000Z"
}
```

**Errors:** `COLLECTION_NOT_FOUND`, `COLLECTION_NOT_APPROVED`, `API_KEY_MISSING`

### 7.6 `collection.cancel`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Cancel an in-flight collection generation. Already-completed items are kept; in-flight items are marked `error` with a cancellation note.

**Params:**

```json
{
  "collection_id": "6ba7b810-..."
}
```

**Result:**

```json
{
  "cancelled": true,
  "items_completed": 4,
  "items_cancelled": 2
}
```

### 7.7 `collection.get`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Get a single collection's current state including all items.

**Params:**

```json
{
  "collection_id": "6ba7b810-..."
}
```

**Result:**

```json
{
  "collection": { /* Collection */ },
  "items": [ /* Item[] */ ]
}
```

---
