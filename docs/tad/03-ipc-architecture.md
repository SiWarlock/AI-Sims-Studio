# TAD — IPC Architecture

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §5

> JSON-RPC 2.0 over stdio protocol, message categories, method naming, error handling, progress events, admin gating.

---

## 5. IPC Architecture

### 5.1 Protocol

The frontend ↔ sidecar channel uses **JSON-RPC 2.0 over stdio**.

- Messages are newline-delimited JSON objects written to stdout (sidecar → frontend) and stdin (frontend → sidecar).
- Each request has an ID; responses include the matching ID.
- Notifications (no response expected) are used for progress events.
- Tauri's sidecar API handles process lifecycle and byte streaming.

### 5.2 Message Categories

- **Request / Response** — client-initiated, expects a response. Examples: `project.create`, `collection.generate`, `export.run`.
- **Notification (sidecar-initiated)** — progress events, log events, error events. Examples: `generation.progress`, `item.status_changed`, `log.emitted`.

### 5.3 Method Naming

Methods use dotted namespaces:

- `project.*` — project CRUD
- `collection.*` — collection planning, editing, generation
- `item.*` — item operations
- `swatch.*` — swatch regeneration
- `functional.*` — functional overlay operations
- `validation.*` — validation requests
- `export.*` — export and install
- `admin.*` — admin mode operations (gated)
- `config.*` — configuration CRUD
- `system.*` — health, shutdown, paths

Complete method inventory is the subject of the API Specification document.

### 5.4 Error Handling

Errors use a structured format extending JSON-RPC:

```json
{
  "jsonrpc": "2.0",
  "id": "...",
  "error": {
    "code": -32000,
    "message": "Generation failed",
    "data": {
      "error_code": "REPLICATE_TIMEOUT",
      "message_user": "The image generator took too long. Try again in a moment.",
      "message_admin": "Replicate API call exceeded 120s timeout for model flux-1.1-pro...",
      "suggested_action": "retry",
      "retriable": true,
      "target_entity_id": "..."
    }
  }
}
```

Error codes are an enum defined in `sidecar/errors/codes.py` and re-exported to TypeScript.

### 5.5 Progress Event Schema

All progress notifications follow a uniform shape:

```json
{
  "jsonrpc": "2.0",
  "method": "generation.progress",
  "params": {
    "job_id": "...",
    "stage": "texture_gen",
    "target_entity_type": "Swatch",
    "target_entity_id": "...",
    "progress_ratio": 0.4,
    "message_user": "Generating Y2K lava lamp textures..."
  }
}
```

### 5.6 Admin Gating

Admin mode methods (`admin.*`) are accepted by the sidecar only when the frontend has declared admin mode active via a `system.set_admin_mode` call. Admin mode has no authentication; this gating is not a security boundary, it is a safety rail that prevents UI bugs from inadvertently calling admin endpoints from non-admin screens.

---
