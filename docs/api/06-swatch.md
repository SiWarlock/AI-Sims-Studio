# API Spec — swatch.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §9

> swatch.regenerate, swatch.delete, swatch.add.

---

## 9. Namespace: `swatch.*`

### 9.1 `swatch.regenerate`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Regenerate a single swatch of an item.

**Params:**

```json
{
  "swatch_id": "uuid-swatch-1"
}
```

**Result:**

```json
{
  "job_id": "job_regen_456"
}
```

### 9.2 `swatch.delete`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Remove a swatch from an item. Not allowed if it is the last swatch.

**Params:**

```json
{
  "swatch_id": "uuid-swatch-1"
}
```

**Result:**

```json
{
  "deleted": true
}
```

**Errors:** `LAST_SWATCH_PROTECTED`

### 9.3 `swatch.add`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Generate a new swatch for an item (using the existing spec, new seed).

**Params:**

```json
{
  "item_id": "uuid-item-1"
}
```

**Result:**

```json
{
  "job_id": "job_newswatch_789",
  "swatch_id": "uuid-swatch-new"
}
```

---
