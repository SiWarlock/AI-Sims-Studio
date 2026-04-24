# API Spec — item.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §8

> item.get, item.regenerate, item.replace, item.exclude, item.include, item.update_metadata, item.set_primary_swatch.

---

## 8. Namespace: `item.*`

### 8.1 `item.get`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Get a single item with all nested entities (spec, swatches, overlay).

**Params:**

```json
{
  "item_id": "uuid-item-1"
}
```

**Result:**

```json
{
  "item": { /* Item */ },
  "spec": { /* ItemSpec | null */ },
  "swatches": [ /* Swatch[] */ ],
  "texture_sets": [ /* TextureSet[] */ ],
  "overlay": { /* FunctionalOverlay | null */ }
}
```

### 8.2 `item.regenerate`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Regenerate textures and thumbnail for an item, keeping the existing spec. New seed is used.

**Params:**

```json
{
  "item_id": "uuid-item-1",
  "regenerate_swatches": true,
  "regenerate_thumbnail": true
}
```

If `regenerate_swatches` is false and `regenerate_thumbnail` is true, only the thumbnail is re-rendered (same textures). Both false is a no-op.

**Result:**

```json
{
  "job_id": "job_xyz789"
}
```

### 8.3 `item.replace`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Regenerate the item from scratch: new spec, new textures, new thumbnail. Equivalent to deleting and recreating, but preserves the item ID so references remain stable.

**Params:**

```json
{
  "item_id": "uuid-item-1"
}
```

**Result:**

```json
{
  "job_id": "job_xyz789"
}
```

### 8.4 `item.exclude`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Exclude an item from the final export without deleting it.

**Params:**

```json
{
  "item_id": "uuid-item-1"
}
```

**Result:**

```json
{
  "excluded": true
}
```

### 8.5 `item.include`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Re-include a previously excluded item.

**Params:**

```json
{
  "item_id": "uuid-item-1"
}
```

**Result:**

```json
{
  "included": true
}
```

### 8.6 `item.update_metadata`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Update user-facing metadata (name, description, tags, price, category, custom filter tag).

**Params:**

```json
{
  "item_id": "uuid-item-1",
  "metadata": {
    "name": "Chromabyte Lava Lamp",
    "description": "A translucent purple lava lamp with chrome base, evoking the turn-of-the-millennium aesthetic.",
    "tags": ["y2k", "lava lamp", "retro", "decor"],
    "price": 150,
    "build_buy_category": "decor_misc",
    "custom_filter_tag": "y2k_bedroom"
  }
}
```

All fields are optional; missing fields are not updated.

**Result:**

```json
{
  "updated": true,
  "metadata": { /* ItemMetadata */ }
}
```

**Errors:** `USER_INPUT_ERROR` (e.g., invalid price, invalid category)

### 8.7 `item.set_primary_swatch`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Set which swatch is used as the primary thumbnail for the item.

**Params:**

```json
{
  "item_id": "uuid-item-1",
  "swatch_id": "uuid-swatch-2"
}
```

**Result:**

```json
{
  "primary_swatch_id": "uuid-swatch-2",
  "thumbnail_path": "/path/to/new_primary_thumb.png"
}
```

---
