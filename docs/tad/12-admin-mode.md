# TAD — Admin Mode Architecture

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §14

> Gating, admin endpoints, admin UI architecture, admin-only features.

---

## 14. Admin Mode Architecture

### 14.1 Gating

Admin mode is entered via:

- Keyboard shortcut (macOS: ⌘⇧A, Windows: Ctrl+Shift+A)
- Menu bar item under a "Developer" menu

On entry, the frontend sends `system.set_admin_mode(true)` to the sidecar. The sidecar flags admin endpoints as available.

Admin mode is not a security boundary. It exists to prevent the primary creator from accidentally accessing maintainer features.

### 14.2 Admin Endpoints

- `admin.template.list` / `admin.template.get` / `admin.template.update` / `admin.template.promote`
- `admin.mesh.import_from_sims` / `admin.mesh.list_tier2`
- `admin.logs.query` / `admin.logs.tail`
- `admin.jobs.list` / `admin.jobs.detail`
- `admin.reference.list` / `admin.reference.get_tuning`
- `admin.config.get` / `admin.config.set`
- `admin.rebuild` — deterministic rebuild of an export from saved project state

### 14.3 Admin UI Architecture

Admin screens live under `/admin/*` routes (memory routed). A top-level `AdminModeGate` component blocks rendering of admin screens unless admin mode is active in Redux state. If admin mode is exited while on an admin screen, the user is redirected to the home screen.

### 14.4 Admin-Only Features

- Full log detail (user mode shows only user-level messages)
- Full error stack traces
- Per-job artifact browsing
- Template schema editing
- Reference object tuning inspection

---
