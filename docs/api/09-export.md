# API Spec — export.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §12

> export.run, export.retry_install, export.resolve_conflict, export.list_artifacts.

---

## 12. Namespace: `export.*`

### 12.1 `export.run`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Build and auto-install the collection as a `.package` file.

**Params:**

```json
{
  "collection_id": "6ba7b810-...",
  "variant_choices": {
    "uuid-item-1": "functional",
    "uuid-item-2": "decor_only",
    "uuid-item-3": "both"
  },
  "ignore_warnings": false
}
```

`variant_choices` is keyed by item ID with values `"decor_only"` · `"functional"` · `"both"`. Items without a functional overlay can only be `"decor_only"`. Items not in the map default to `"decor_only"`.

If `ignore_warnings` is true, validation warnings do not block export (errors still do).

**Result:**

```json
{
  "job_id": "job_export_789",
  "artifact_id": "uuid-artifact-1"
}
```

**Errors:** `VALIDATION_FAILED`, `MODS_FOLDER_NOT_FOUND`, `DISK_SPACE_INSUFFICIENT`

### 12.2 `export.retry_install`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Retry the auto-install step for a previously built artifact (e.g., after the user resolved a Mods folder issue).

**Params:**

```json
{
  "artifact_id": "uuid-artifact-1"
}
```

**Result:**

```json
{
  "installed": true,
  "install_path": "/Users/x/Documents/Electronic Arts/The Sims 4/Mods/Y2K Bedroom.package"
}
```

### 12.3 `export.resolve_conflict`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Resolve a file conflict detected during auto-install.

**Params:**

```json
{
  "artifact_id": "uuid-artifact-1",
  "resolution": "overwrite"
}
```

`resolution` is one of `"overwrite"` · `"rename"` · `"skip"`.

**Result:**

```json
{
  "resolved": true,
  "install_path": "/Users/x/Documents/.../Mods/Y2K Bedroom.package"
}
```

### 12.4 `export.list_artifacts`

**Direction:** Request / Response
**Admin-only:** No
**Description:** List all export artifacts for a project.

**Params:**

```json
{
  "project_id": "550e8400-..."
}
```

**Result:**

```json
{
  "artifacts": [
    {
      "id": "uuid-artifact-1",
      "collection_id": "6ba7b810-...",
      "package_path": "/path/to/exports/.../Y2K Bedroom.package",
      "install_path": "/Users/x/Documents/.../Mods/Y2K Bedroom.package",
      "item_ids_included": ["..."],
      "functional_item_ids": ["..."],
      "size_bytes": 5234567,
      "sha256": "abc123...",
      "built_at": "2026-04-21T16:15:00.000Z",
      "installed_at": "2026-04-21T16:15:05.000Z",
      "verified_in_game": null
    }
  ]
}
```

---
