# API Spec — Error Codes

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §17

> Complete enum of error codes organized by category.

---

## 17. Error Codes

All error codes are strings in `data.error_code`. Grouped by category.

### 17.1 User Input

- `USER_INPUT_ERROR` — Invalid input to a method (malformed, missing required field, out of range).
- `NAME_CONFLICT` — Project or template name conflicts with an existing one.
- `CONFIRMATION_REQUIRED` — Destructive action requires a confirmation token.

### 17.2 Not Found

- `PROJECT_NOT_FOUND`
- `COLLECTION_NOT_FOUND`
- `ITEM_NOT_FOUND`
- `SWATCH_NOT_FOUND`
- `OVERLAY_NOT_FOUND`
- `TEMPLATE_NOT_FOUND`
- `ARTIFACT_NOT_FOUND`
- `JOB_NOT_FOUND`
- `REFERENCE_OBJECT_NOT_FOUND`

### 17.3 State

- `COLLECTION_NOT_APPROVED` — Generation attempted before plan approval.
- `LAST_SWATCH_PROTECTED` — Attempted to delete the last swatch of an item.
- `SCHEMA_MIGRATION_REQUIRED` — Project was created with a newer schema version.
- `JOB_NOT_CANCELLABLE` — Attempted to cancel a job that has already completed.
- `INCOMPATIBLE_ARCHETYPE` — Archetype not compatible with item's template.
- `INVALID_CONFIGURATION` — Archetype configuration failed validation.
- `VALIDATION_FAILED` — Validation blockers prevent export.

### 17.4 Configuration

- `CONFIG_ERROR`
- `API_KEY_MISSING`
- `API_KEY_INVALID`
- `SIMS_INSTALL_NOT_FOUND`
- `MODS_FOLDER_NOT_FOUND`
- `BLENDER_NOT_FOUND`
- `DISK_SPACE_INSUFFICIENT`
- `PERMISSION_DENIED`

### 17.5 External Dependencies

- `ANTHROPIC_API_ERROR`
- `ANTHROPIC_RATE_LIMIT`
- `ANTHROPIC_AUTH_ERROR`
- `REPLICATE_API_ERROR`
- `REPLICATE_TIMEOUT`
- `REPLICATE_CONTENT_POLICY_REJECTION`
- `REPLICATE_AUTH_ERROR`
- `BLENDER_SUBPROCESS_ERROR`
- `SIMS_INSTALL_READ_ERROR`

### 17.6 Generation

- `AI_CALL_FAILED`
- `AI_MALFORMED_RESPONSE`
- `TEXTURE_GENERATION_FAILED`
- `THUMBNAIL_RENDER_FAILED`
- `TEMPLATE_SCHEMA_INVALID`

### 17.7 Build and Install

- `DBPF_WRITE_ERROR`
- `TUNING_PARSE_ERROR`
- `TUNING_CLONE_ERROR`
- `TUNING_REFERENCE_UNRESOLVED`
- `DDS_ENCODE_ERROR`
- `INSTALL_CONFLICT_UNRESOLVED`
- `INSTALL_COPY_FAILED`

### 17.8 Admin

- `ADMIN_REQUIRED` — Admin-only method called without admin mode active.
- `TEMPLATE_AUTHORING_INCOMPLETE` — Promotion attempted with missing schema fields.

### 17.9 Internal

- `INTERNAL_ERROR` — Unexpected exception (bug). Always includes stack trace in admin-mode data.
- `STORAGE_ERROR` — SQLite or file system error.
- `NOT_IMPLEMENTED` — Feature architected but not implemented in MVP (e.g., Maxis Match style).

### 17.10 Protocol

Standard JSON-RPC 2.0 codes, returned at the protocol level (not wrapped in `data.error_code`):

- `-32700` Parse error — malformed JSON
- `-32600` Invalid request — not a valid JSON-RPC object
- `-32601` Method not found
- `-32602` Invalid params — schema mismatch
- `-32603` Internal error — sidecar-side JSON-RPC infrastructure error

---
