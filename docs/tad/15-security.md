# TAD — Security and Privacy Implementation

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §17

> Network access scope, credential storage in platform keyrings, file system access boundaries, process isolation, user data handling.

---

## 17. Security and Privacy Implementation

### 17.1 Network Access

The sidecar makes outbound network calls only to:

- `api.anthropic.com` — AI inference
- `api.replicate.com` — image generation
- Anthropic's and Replicate's CDN domains for model result downloads

Any other outbound traffic indicates a bug or compromise. Network calls are logged.

### 17.2 Credentials

API keys for Anthropic and Replicate are stored in:

- **macOS:** Keychain, accessed via `keyring` Python library
- **Windows:** Windows Credential Manager, accessed via `keyring`

Keys never appear in logs, project files, or UI. First-run flow prompts the user to paste keys; admin mode includes a "replace API keys" action.

### 17.3 File System Access

The sidecar reads from:

- App data directory (read-write)
- Projects directory (read-write)
- Logs directory (write)
- User's Sims install directory (**read-only**)
- User's Mods folder (**write**, for installed packages)
- Blender executable (read-only, to invoke)

The Sims install directory is never written to. A guard in the `sims_install` module enforces read-only access.

### 17.4 Process Isolation

The Python sidecar runs with the same privileges as the Tauri host. No privilege escalation. Tauri's security model restricts what the frontend can access directly, so all sensitive operations go through the sidecar.

### 17.5 User Data

All user data (prompts, projects, exports) stays local. The only data sent outside the machine is:

- Prompts and template schemas sent to Anthropic for reasoning
- Texture generation prompts sent to Replicate for image generation

These are necessary for the product to function. Users are informed at first launch. Admin mode includes a "privacy summary" that shows exactly what data is sent where.

---
