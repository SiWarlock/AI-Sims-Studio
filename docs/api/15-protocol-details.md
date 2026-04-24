# API Spec — Concurrency, Versioning, Examples, and Implementation Notes

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §18, §19, §20, §21, §22

> Concurrency and rate limiting, versioning and backward compatibility, full flow examples, implementation notes for Claude Code, and open method-level items.

---

## 18. Concurrency and Rate Limiting

### 18.1 Request Concurrency

- The sidecar processes read-only requests concurrently.
- Writes to the same project are serialized by an in-memory per-project lock.
- Writes to different projects are concurrent.
- Long-running jobs do not block the request channel; they return a `job_id` and progress via notifications.

### 18.2 External API Rate Limiting

- Anthropic calls are throttled at the client library level with exponential backoff on rate-limit responses.
- Replicate calls are capped at `texture_concurrency_cap` concurrent requests (default 4, admin-configurable).
- Rate limit hits are surfaced to users as soft warnings, not blocking errors, unless all retries are exhausted.

### 18.3 Job Queue Limits

- No hard cap on queued jobs in MVP.
- Practical limit is per-project via the collection size cap (12 items × 3 swatches × 3 zones = 108 texture generation calls per collection).

---



## 19. Versioning

### 19.1 Schema Version

The API schema has a single version number, reported by `system.version.schema_version`. MVP v1.0 uses `1`.

### 19.2 Backward Compatibility

Within a major version, changes are additive:
- New methods may be added
- New optional fields may be added to params or results
- New enum values may be added

Breaking changes require a schema version bump.

### 19.3 Type Generation

TypeScript types are auto-generated from Pydantic schemas as part of the build (see TAD §4.6). Frontend code imports types from `shared-types/` and never redefines them.

### 19.4 Schema Version Mismatch

If the frontend and sidecar have mismatched schema versions, the sidecar refuses to proceed beyond `system.version` and returns `SCHEMA_VERSION_MISMATCH` for all other methods until the frontend is updated.

---



## 20. Examples

### 20.1 Complete Flow: Create, Plan, Generate, Export

```json
// 1. Create project
--> { "jsonrpc":"2.0", "id":"1", "method":"project.create",
      "params":{ "name":"Y2K Bedroom", "theme_prompt":"...", "mode":"collection",
                 "target_item_count":6, "style_preference":"semi_alpha" } }
<-- { "jsonrpc":"2.0", "id":"1",
      "result":{ "project_id":"p1", "collection_id":"c1", "created_at":"..." } }

// 2. Open project
--> { "jsonrpc":"2.0", "id":"2", "method":"project.open", "params":{ "project_id":"p1" } }
<-- { "jsonrpc":"2.0", "id":"2", "result":{ "project":{...}, "collections":[...], ... } }

// 3. Generate plan
--> { "jsonrpc":"2.0", "id":"3", "method":"collection.plan", "params":{ "collection_id":"c1" } }
<-- { "jsonrpc":"2.0", "id":"3", "result":{ "plan":{ "items":[...], ... } } }

// 4. User edits plan (omitted for brevity), then approve
--> { "jsonrpc":"2.0", "id":"4", "method":"collection.approve_plan",
      "params":{ "collection_id":"c1" } }
<-- { "jsonrpc":"2.0", "id":"4", "result":{ "item_ids":["i1","i2",...] } }

// 5. Generate
--> { "jsonrpc":"2.0", "id":"5", "method":"collection.generate",
      "params":{ "collection_id":"c1", "swatch_count":3 } }
<-- { "jsonrpc":"2.0", "id":"5", "result":{ "job_id":"j1", "started_at":"..." } }

// 6. Progress notifications stream in...
<-- { "jsonrpc":"2.0", "method":"generation.progress", "params":{ "job_id":"j1", ... } }
<-- { "jsonrpc":"2.0", "method":"item.status_changed",
      "params":{ "item_id":"i1", "previous_status":"generating", "new_status":"generated" } }
// ... many more ...
<-- { "jsonrpc":"2.0", "method":"collection.status_changed",
      "params":{ "collection_id":"c1", "previous_status":"generating", "new_status":"generated" } }

// 7. Validate
--> { "jsonrpc":"2.0", "id":"6", "method":"validation.run", "params":{ "collection_id":"c1" } }
<-- { "jsonrpc":"2.0", "id":"6", "result":{ "result":{ "passed":true, ... } } }

// 8. Export
--> { "jsonrpc":"2.0", "id":"7", "method":"export.run",
      "params":{ "collection_id":"c1", "variant_choices":{ "i1":"functional" },
                 "ignore_warnings":false } }
<-- { "jsonrpc":"2.0", "id":"7", "result":{ "job_id":"j2", "artifact_id":"a1" } }

// 9. Export progress, then completion via notifications...
```

### 20.2 Error Flow: Functional Upgrade with Incompatible Archetype

```json
--> { "jsonrpc":"2.0", "id":"10", "method":"functional.create",
      "params":{ "item_id":"i_mirror", "archetype":"audio_device",
                 "configuration":{ "genre_category":"pop", "default_volume":3 } } }
<-- { "jsonrpc":"2.0", "id":"10",
      "error":{
        "code":-32000,
        "message":"Server error",
        "data":{
          "error_code":"INCOMPATIBLE_ARCHETYPE",
          "message_user":"A mirror can't be turned into an audio device. Try 'mirror' instead.",
          "message_admin":"Item i_mirror uses template rectangular_wall_flat. Compatible archetypes: [mirror, moodlet_emitter]. Requested: audio_device.",
          "suggested_action":"choose_compatible_archetype",
          "retriable":false,
          "target_entity_type":"Item",
          "target_entity_id":"i_mirror"
        }
      } }
```

---



## 21. Implementation Notes for Claude Code

- Every method maps 1:1 to a Python handler in `sidecar/ipc/handlers/` organized by namespace.
- Every handler validates input via Pydantic before executing.
- Every handler returns a Pydantic model that serializes to the documented result shape.
- Error paths always raise a subclass of `AISCError` that is caught at the IPC layer and converted to the structured error response.
- Progress notifications are emitted via `ipc.notify(method, params)` from within stage code.
- The shared types generation script is the source of truth for TypeScript types; do not hand-write TS types for IPC payloads.
- Every method's test coverage must include: happy path, one validation failure path, one not-found path (if applicable), one external-dependency-failure path (mocked).

---



## 22. Open Items

These are method-level decisions that may be refined during implementation but do not block initial scaffolding:

- Final `build_buy_category` enum list (derived from Sims 4 internal category taxonomy; locked during Phase 4).
- Final moodlet list returned by `functional.available_moodlets` (locked during Phase 5).
- Exact shape of `admin.reference.list`'s `category` enum (derived from Sims object taxonomy during Phase 5).
- Exact fields in `admin.cost_summary.breakdown` (may expand as additional AI stages are added).

---
