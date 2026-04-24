# API Spec — verification.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §13

> verification.mark_item, verification.mark_collection, verification.get.

---

## 13. Namespace: `verification.*`

### 13.1 `verification.mark_item`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Record per-item in-game verification status.

**Params:**

```json
{
  "artifact_id": "uuid-artifact-1",
  "item_id": "uuid-item-1",
  "status": "verified",
  "notes": "Appears correctly in the decor catalog. Placed in world. Swatches switch. Functional on/off works."
}
```

`status` is one of `"verified"` · `"needs_attention"` · `"broken"`.

**Result:**

```json
{
  "recorded": true
}
```

### 13.2 `verification.mark_collection`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Mark the entire collection as verified (shortcut for per-item).

**Params:**

```json
{
  "artifact_id": "uuid-artifact-1",
  "status": "verified"
}
```

**Result:**

```json
{
  "recorded": true
}
```

### 13.3 `verification.get`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Get verification status for an artifact.

**Params:**

```json
{
  "artifact_id": "uuid-artifact-1"
}
```

**Result:**

```json
{
  "collection_status": "verified",
  "items": [
    { "item_id": "uuid-item-1", "status": "verified", "notes": "...", "recorded_at": "..." }
  ]
}
```

---
