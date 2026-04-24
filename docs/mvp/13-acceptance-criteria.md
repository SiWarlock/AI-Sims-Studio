# MVP Spec — MVP Acceptance Criteria

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §10

> MVP-AC-001 through MVP-AC-030 — the complete testable criteria for MVP release.

---

## 10. MVP Acceptance Criteria (Consolidated)

All of the following must pass for MVP v1.0 to ship.

- **MVP-AC-001** — App installs and launches on both macOS and Windows.
- **MVP-AC-002** — Sims 4 install and Mods folder are auto-detected on standard installs.
- **MVP-AC-003** — Blender presence is detected; user is prompted if missing.
- **MVP-AC-004** — A user can create a new project (collection or single item) with a prompt and parameters.
- **MVP-AC-005** — A collection plan is generated with template matches and confidence scores per item.
- **MVP-AC-006** — The user can edit the plan (add, remove, reorder, rename) before generation.
- **MVP-AC-007** — Low-confidence items are flagged with a clear warning and proceed/skip/rephrase options.
- **MVP-AC-008** — Decorative generation produces items with previews, swatches (3+), and metadata using semi-Alpha style.
- **MVP-AC-009** — The user can regenerate individual items and individual swatches.
- **MVP-AC-010** — The user can replace or exclude items.
- **MVP-AC-011** — The user can edit all metadata fields (name, description, tags, price, category, custom filter tag).
- **MVP-AC-012** — The user can upgrade at least one item per MVP archetype to a functional variant.
- **MVP-AC-013** — Structural validation runs before export and separates blockers from warnings.
- **MVP-AC-014** — Export produces valid `.package` files.
- **MVP-AC-015** — `.package` files auto-install to the detected Mods folder.
- **MVP-AC-016** — Export result summary clearly reports success/failure and install locations.
- **MVP-AC-017** — In-game verification flow is available and records user confirmation.
- **MVP-AC-018** — All exported decorative items appear correctly in Build/Buy in-game.
- **MVP-AC-019** — All exported functional items behave correctly in-game for their archetype.
- **MVP-AC-020** — Projects persist across app restarts and can be rebuilt deterministically.
- **MVP-AC-021** — Admin mode is accessible and hidden from primary flow.
- **MVP-AC-022** — Admin can browse and edit Tier 1 and Tier 2 templates.
- **MVP-AC-023** — Admin can import base-game meshes as Tier 2 templates.
- **MVP-AC-024** — Admin can promote Tier 2 templates to Tier 1.
- **MVP-AC-025** — Admin mode exposes logs, job history, and reference object browser.
- **MVP-AC-026** — Local-only logging works on both platforms at the correct standard paths.
- **MVP-AC-027** — No outbound telemetry; only required AI API calls.
- **MVP-AC-028** — Style parameter is present in schemas; semi-Alpha is the only implemented path.
- **MVP-AC-029** — Both platform builds produce identical exports from identical projects.
- **MVP-AC-030** — README, user manual, and maintainer guide are complete.

---
