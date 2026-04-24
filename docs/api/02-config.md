# API Spec — config.* Namespace

> **Source:** `docs/MONOLITHIC/API_Specification.md` · **Area:** API Spec · **Sections:** §5

> config.get, config.set, config.set_api_key, config.clear_api_key, config.redetect_paths.

---

## 5. Namespace: `config.*`

### 5.1 `config.get`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Return full current configuration (non-secret fields).

**Params:** none

**Result:**

```json
{
  "sims_install_path": "/Applications/The Sims 4.app",
  "mods_folder_path": "/Users/x/Documents/Electronic Arts/The Sims 4/Mods",
  "blender_path": "/Applications/Blender.app/Contents/MacOS/Blender",
  "log_level": "info",
  "has_anthropic_key": true,
  "has_replicate_key": true,
  "texture_concurrency_cap": 4,
  "default_swatch_count": 3
}
```

API keys themselves are never returned; only whether they are configured.

### 5.2 `config.set`

**Direction:** Request / Response
**Admin-only:** No (admin-only for certain fields; see below)
**Description:** Update one or more configuration fields.

**Params:**

```json
{
  "sims_install_path": "/Applications/The Sims 4.app",
  "blender_path": "/Applications/Blender.app/Contents/MacOS/Blender",
  "log_level": "debug"
}
```

Admin-only fields (return `ADMIN_REQUIRED` error if set outside admin mode): `texture_concurrency_cap`, retry policy overrides.

**Result:** Same shape as `config.get`.

### 5.3 `config.set_api_key`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Store an API key in the platform keyring.

**Params:**

```json
{
  "service": "anthropic",
  "key": "sk-ant-..."
}
```

`service` is one of `"anthropic"` · `"replicate"`.

**Result:**

```json
{
  "stored": true
}
```

The key is not echoed back. It is stored in the platform keyring (macOS Keychain or Windows Credential Manager).

### 5.4 `config.clear_api_key`

**Direction:** Request / Response
**Admin-only:** Yes
**Description:** Remove a stored API key from the keyring.

**Params:**

```json
{
  "service": "anthropic"
}
```

**Result:**

```json
{
  "cleared": true
}
```

### 5.5 `config.redetect_paths`

**Direction:** Request / Response
**Admin-only:** No
**Description:** Re-run auto-detection for Sims install, Mods folder, and Blender.

**Params:** none

**Result:** Same shape as `system.paths`.

---
