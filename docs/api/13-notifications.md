# API Spec — Notifications

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §16

> All sidecar-to-frontend notifications: progress, status changes, conflicts, log events, errors, sidecar ready.

---

## 16. Notifications

All notifications are sidecar-to-frontend, no response expected.

### 16.1 `generation.progress`

**Description:** Fine-grained progress within a generation stage.

```json
{
  "jsonrpc": "2.0",
  "method": "generation.progress",
  "params": {
    "job_id": "job_abc123",
    "stage": "texture_gen",
    "target_entity_type": "Swatch",
    "target_entity_id": "uuid-swatch-1",
    "progress_ratio": 0.4,
    "message_user": "Generating Y2K lava lamp textures... (2 of 3 zones complete)"
  }
}
```

### 16.2 `item.status_changed`

**Description:** An item transitioned to a new state.

```json
{
  "jsonrpc": "2.0",
  "method": "item.status_changed",
  "params": {
    "item_id": "uuid-item-1",
    "previous_status": "generating",
    "new_status": "generated"
  }
}
```

### 16.3 `collection.status_changed`

**Description:** A collection transitioned to a new state.

```json
{
  "jsonrpc": "2.0",
  "method": "collection.status_changed",
  "params": {
    "collection_id": "6ba7b810-...",
    "previous_status": "generating",
    "new_status": "generated"
  }
}
```

### 16.4 `swatch.status_changed`

**Description:** A swatch transitioned to a new state.

```json
{
  "jsonrpc": "2.0",
  "method": "swatch.status_changed",
  "params": {
    "swatch_id": "uuid-swatch-1",
    "previous_status": "generating",
    "new_status": "generated"
  }
}
```

### 16.5 `job.state_changed`

**Description:** A job transitioned to a new state.

```json
{
  "jsonrpc": "2.0",
  "method": "job.state_changed",
  "params": {
    "job_id": "job_abc123",
    "previous_status": "running",
    "new_status": "succeeded",
    "duration_ms": 4523
  }
}
```

### 16.6 `install.conflict_detected`

**Description:** Auto-install detected a file conflict requiring user resolution. The request that triggered the install is left pending until `export.resolve_conflict` is called.

```json
{
  "jsonrpc": "2.0",
  "method": "install.conflict_detected",
  "params": {
    "artifact_id": "uuid-artifact-1",
    "conflict_id": "conflict_abc",
    "existing_file_path": "/Users/x/Documents/.../Mods/Y2K Bedroom.package",
    "existing_file_sha256": "xxx",
    "new_file_sha256": "yyy",
    "size_existing": 5234567,
    "size_new": 5245678
  }
}
```

### 16.7 `log.emitted`

**Description:** A log entry was emitted. Sent only to admin-mode subscribers via `admin.logs.tail`.

```json
{
  "jsonrpc": "2.0",
  "method": "log.emitted",
  "params": {
    "subscription_id": "sub_logs_abc",
    "timestamp": "2026-04-21T15:52:13.456Z",
    "level": "warning",
    "module": "texture_gen",
    "event": "replicate_retry",
    "context": { "model": "flux-1.1-pro", "retry_count": 1 }
  }
}
```

### 16.8 `error.occurred`

**Description:** An asynchronous error occurred (e.g., during a running job) that is not tied to an active request.

```json
{
  "jsonrpc": "2.0",
  "method": "error.occurred",
  "params": {
    "error_code": "BLENDER_SUBPROCESS_ERROR",
    "message_user": "The thumbnail renderer failed for 'Y2K lava lamp'. Try regenerating.",
    "message_admin": "Blender subprocess exited with code 1. stderr: 'GLTF import error: invalid mesh data...'",
    "target_entity_type": "Item",
    "target_entity_id": "uuid-item-1",
    "suggested_action": "regenerate_item",
    "retriable": true
  }
}
```

### 16.9 `system.sidecar_ready`

**Description:** Emitted once on startup when the sidecar has finished initialization and is ready to accept requests.

```json
{
  "jsonrpc": "2.0",
  "method": "system.sidecar_ready",
  "params": {
    "sidecar_version": "1.0.0",
    "templates_loaded": 19,
    "startup_duration_ms": 1245
  }
}
```

### 16.10 `system.paths_changed`

**Description:** Emitted when path detection runs and any path differs from the last known value (e.g., Sims updated and install location changed).

```json
{
  "jsonrpc": "2.0",
  "method": "system.paths_changed",
  "params": {
    "changed": ["sims_install_path", "mods_folder_path"]
  }
}
```

---
