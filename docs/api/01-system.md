# API Spec — system.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §4

> system.version, system.shutdown, system.health, system.paths, system.set_admin_mode, system.open_external_path.

---

## 4. Namespace: `system.*`

### 4.1 `system.version`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Return app and sidecar version information.

**Params:** none

**Result:**

```json
{
  "app_version": "1.0.0",
  "sidecar_version": "1.0.0",
  "schema_version": 1,
  "build_commit": "abc123def",
  "platform": "darwin"
}
```

`platform` is one of `"darwin"` or `"windows"`.

### 4.2 `system.shutdown`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Request graceful sidecar shutdown. In-flight jobs are cancelled, state is persisted, sidecar exits.

**Params:**

```json
{
  "timeout_ms": 10000
}
```

**Result:**

```json
{
  "acknowledged": true
}
```

The sidecar exits after responding. The frontend should detect the subprocess exit and not expect further messages.

### 4.3 `system.health`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Liveness check. Returns quickly with basic status.

**Params:** none

**Result:**

```json
{
  "ok": true,
  "uptime_ms": 145230,
  "active_jobs": 2,
  "memory_mb": 312.5
}
```

### 4.4 `system.paths`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Return resolved paths for the user's environment.

**Params:** none

**Result:**

```json
{
  "app_data_dir": "/Users/x/Library/Application Support/AISimsCreator",
  "logs_dir": "/Users/x/Library/Logs/AISimsCreator",
  "projects_root": "/Users/x/Documents/AISimsCreator/projects",
  "sims_install_path": "/Applications/The Sims 4.app",
  "sims_install_detected": true,
  "mods_folder_path": "/Users/x/Documents/Electronic Arts/The Sims 4/Mods",
  "mods_folder_detected": true,
  "blender_path": "/Applications/Blender.app/Contents/MacOS/Blender",
  "blender_detected": true
}
```

### 4.5 `system.set_admin_mode`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Toggle admin mode flag in the sidecar. Admin endpoints are only honored when this flag is `true`.

**Params:**

```json
{
  "enabled": true
}
```

**Result:**

```json
{
  "admin_mode": true
}
```

### 4.6 `system.open_external_path`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Open a file manager or the Sims game itself. The sidecar invokes the OS to open the path.

**Params:**

```json
{
  "path": "/Users/x/Documents/Electronic Arts/The Sims 4/Mods",
  "kind": "folder"
}
```

`kind` is one of `"folder"` · `"file"` · `"sims_game"`.

**Result:**

```json
{
  "opened": true
}
```

---
