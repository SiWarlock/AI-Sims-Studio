# MVP Spec — Phase 6 — Admin Mode

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.7

> Template browser, base-game importer, Tier 2 promotion editor, logs viewer, job history, reference object browser.

---

**Phase goal:** Build the full administrator surface for template management, base-game inspection, logs, and diagnostics.

**Phase acceptance gate:** A maintainer can access admin mode, browse and edit templates, import Tier 2 templates from the Sims install, promote Tier 2 to Tier 1, view logs and job history, and inspect base-game reference objects.

#### Tasks

**6.1 — Admin mode entry point and shell**
Implement admin mode entry (keyboard shortcut, menu item) and the admin navigation shell.

*Outputs:* Admin mode accessible but not visible in primary UI.
*Dependencies:* 0.6.
*Acceptance:* Admin mode can be entered and exited. Not discoverable by the primary user accidentally.

**6.2 — Template library browser**
Build the admin-mode template browser: list all Tier 1 and Tier 2 templates, view full schemas, preview renders.

*Outputs:* React admin screen.
*Dependencies:* 2.4, 6.1.
*Acceptance:* All templates are listed with schema detail and thumbnails.

**6.3 — Base-game mesh importer (Tier 2)**
Build the importer surface: browse base-game objects from the user's Sims install, preview, select for import, auto-extract basic metadata, register as Tier 2 templates.

*Outputs:* Importer UI and import pipeline.
*Dependencies:* 5.1, 6.2.
*Acceptance:* Admin can import a base-game object as a Tier 2 template. It becomes available for decorative use.

**6.4 — Tier 2 to Tier 1 promotion editor**
Build the schema editor for promoting Tier 2 templates. Admin specifies texture zones, archetype compatibility, example object types, and promotes.

*Outputs:* Schema editor UI.
*Dependencies:* 6.3.
*Acceptance:* Admin can author full schema for a Tier 2 template and promote it. Promoted template is usable as Tier 1.

**6.5 — Logs viewer**
Build the admin-mode logs viewer. Display current session and historical logs with filtering by level, stage, and item.

*Outputs:* Logs UI.
*Dependencies:* 0.7, 6.1.
*Acceptance:* Admin can read logs, filter them, and copy entries for debugging.

**6.6 — Job history view**
Build the job history UI: list of all generation and build jobs run, their status, artifacts, and duration.

*Outputs:* Job history UI.
*Dependencies:* 3.6, 4.2, 6.1.
*Acceptance:* Admin can inspect any past job and its artifacts.

**6.7 — Reference object browser**
Build the base-game reference object browser for tuning inspection. Admin can browse base-game tuning, search, view raw XML.

*Outputs:* Reference browser UI.
*Dependencies:* 5.1, 6.1.
*Acceptance:* Admin can inspect tuning for reference objects used by archetype handlers.

**6.8 — Configuration panel**
Build the admin-mode configuration panel: model selection overrides, retry policies, path overrides (Sims install, Mods folder, Blender), log level.

*Outputs:* Configuration UI with persistent settings.
*Dependencies:* 6.1.
*Acceptance:* Settings persist across app restarts. Overrides take effect.

---
