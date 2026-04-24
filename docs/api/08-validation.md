# API Spec — validation.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §11

> validation.run.

---

## 11. Namespace: `validation.*`

### 11.1 `validation.run`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Run validation on a collection. Returns structured results.

**Params:**

```json
{
  "collection_id": "6ba7b810-..."
}
```

**Result:**

```json
{
  "result": {
    "id": "uuid-validation-1",
    "passed": false,
    "run_at": "2026-04-21T16:00:00.000Z",
    "errors": [
      {
        "code": "MISSING_THUMBNAIL",
        "severity": "error",
        "target_entity_type": "Item",
        "target_entity_id": "uuid-item-3",
        "message_user": "The 'Y2K fax machine' item is missing its preview image. Regenerate it to fix.",
        "message_admin": "Item uuid-item-3 has no thumbnail_path set. Last thumbnail job failed: BLENDER_SUBPROCESS_ERROR at 2026-04-21T15:52.",
        "suggested_action": "regenerate_item"
      }
    ],
    "warnings": [
      {
        "code": "LOW_CONFIDENCE_MATCH",
        "severity": "warning",
        "target_entity_type": "Item",
        "target_entity_id": "uuid-item-5",
        "message_user": "This item had a low template match. It will export but may not look exactly like what you asked for.",
        "message_admin": "Item uuid-item-5 matched template X with confidence 0.32 (threshold 0.6).",
        "suggested_action": null
      }
    ]
  }
}
```

---
