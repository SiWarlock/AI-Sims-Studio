# API Spec — project.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §6

> project.create, project.open, project.close, project.list_recent, project.rename, project.delete, project.get.

---

## 6. Namespace: `project.*`

### 6.1 `project.create`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Create a new project. A default collection is created simultaneously.

**Params:**

```json
{
  "name": "Y2K Bedroom",
  "theme_prompt": "A Y2K-themed bedroom with translucent plastics, chrome accents, and holographic finishes",
  "style_notes": "Think 1999-2001 aesthetic, saturated purples and pinks",
  "mode": "collection",
  "target_item_count": 6,
  "style_preference": "semi_alpha",
  "reference_inputs": []
}
```

**Result:**

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000",
  "collection_id": "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
  "created_at": "2026-04-21T15:30:45.123Z"
}
```

**Errors:** `USER_INPUT_ERROR`, `STORAGE_ERROR`

### 6.2 `project.open`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Load a project as the active project.

**Params:**

```json
{
  "project_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Result:**

```json
{
  "project": { /* Project */ },
  "collections": [ /* Collection[] */ ],
  "items": [ /* Item[] */ ],
  "swatches": [ /* Swatch[] */ ],
  "overlays": [ /* FunctionalOverlay[] */ ]
}
```

Full object graph is returned. Schemas follow TAD §4.2.

**Errors:** `PROJECT_NOT_FOUND`, `SCHEMA_MIGRATION_REQUIRED`, `STORAGE_ERROR`

### 6.3 `project.close`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Close the active project. Any pending jobs are allowed to complete.

**Params:** none

**Result:**

```json
{
  "closed": true
}
```

### 6.4 `project.list_recent`

**Direction:** Request / Response
**Admin-only:** No
**Description:** List recent projects ordered by `updated_at` descending.

**Params:**

```json
{
  "limit": 20
}
```

**Result:**

```json
{
  "projects": [
    {
      "id": "550e8400-...",
      "name": "Y2K Bedroom",
      "theme_prompt_preview": "A Y2K-themed bedroom with...",
      "created_at": "2026-04-21T15:30:45.123Z",
      "updated_at": "2026-04-21T17:12:30.456Z",
      "thumbnail_path": "/path/to/primary_thumbnail.png",
      "item_count": 6,
      "status": "generated"
    }
  ]
}
```

### 6.5 `project.rename`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Rename a project.

**Params:**

```json
{
  "project_id": "550e8400-...",
  "new_name": "Y2K Bedroom - Purple Edition"
}
```

**Result:**

```json
{
  "updated": true,
  "new_folder_path": "/Users/x/Documents/AISimsCreator/projects/Y2K Bedroom - Purple Edition"
}
```

**Errors:** `PROJECT_NOT_FOUND`, `NAME_CONFLICT`

### 6.6 `project.delete`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Delete a project permanently. The frontend must confirm with the user before calling.

**Params:**

```json
{
  "project_id": "550e8400-...",
  "confirm_token": "DELETE"
}
```

`confirm_token` must equal `"DELETE"` to proceed. This is a safety rail, not security.

**Result:**

```json
{
  "deleted": true
}
```

**Errors:** `PROJECT_NOT_FOUND`, `CONFIRMATION_REQUIRED`

### 6.7 `project.get`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Get full project object graph without making it active.

**Params:**

```json
{
  "project_id": "550e8400-..."
}
```

**Result:** Same shape as `project.open`.

---
