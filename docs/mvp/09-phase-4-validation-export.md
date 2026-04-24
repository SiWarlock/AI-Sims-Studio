# MVP Spec — Phase 4 — Validation, Export, and Auto-Install

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.5

> Structural validation, export screen, DBPF build pipeline, Mods folder auto-install.

---

**Phase goal:** Take a reviewed collection and produce validated, installed `.package` files in the user's Mods folder.

**Phase acceptance gate:** A user can export a decorative collection, see validation results, have the `.package` files auto-installed, and receive a clear success/failure report. Exported items appear correctly in Build/Buy in-game.

#### Tasks

**4.1 — Structural validation engine**
Build the validation engine covering: asset completeness (mesh, textures, thumbnail, metadata present), DBPF structural integrity, TGI resource ID consistency, project internal consistency, metadata completeness.

*Outputs:* A validation module returning structured results with severity (error vs warning) and actionable messages.
*Dependencies:* 3.6.
*Acceptance:* Catches known failure modes (missing textures, malformed metadata, duplicate IDs). Differentiates errors from warnings.

**4.2 — DBPF build pipeline (decorative)**
Extend the Phase 1 POC DBPF pipeline to handle all templates and all items in a collection. Produce one `.package` per item (or a grouped `.package` per collection if that is the design decision, locked in TAD).

*Outputs:* Build function that takes a collection and produces the set of `.package` files.
*Dependencies:* 1.7, 3.6.
*Acceptance:* All items in a test collection produce valid `.package` files.

**4.3 — Export summary UI**
Build the export screen: validation summary with user-readable messages, error and warning lists, per-item variant choices (decor-only / functional / both — functional disabled until Phase 5), export trigger.

*Outputs:* React screen with all export controls.
*Dependencies:* 4.1, 3.8.
*Acceptance:* User can see validation results, resolve blockers or exclude problem items, and trigger export.

**4.4 — Mods folder auto-install**
Implement auto-install. After successful DBPF build, copy `.package` files to the detected Mods folder. Handle conflicts (file with same name exists) with clear policy (ask user — overwrite / rename / skip).

*Outputs:* Install function with conflict handling UX.
*Dependencies:* 4.2, 0.4.
*Acceptance:* Files are installed to the correct Mods folder. Conflicts are handled without data loss.

**4.5 — Export result summary**
Build the post-export UI showing what succeeded, what failed, where files were installed, and a link to launch Sims for verification.

*Outputs:* Result screen with clear per-item status.
*Dependencies:* 4.4.
*Acceptance:* User understands exactly what happened.

**4.6 — In-game verification flow**
Build the optional verification step: user launches Sims from a button, manually confirms items appear correctly, marks per-item verification status in the project.

*Outputs:* Verification UI with per-item checkboxes. Verification state persists to the project.
*Dependencies:* 4.5, 0.5.
*Acceptance:* User can record verification. State persists across app restarts.

**4.7 — Deterministic rebuild**
Ensure the export pipeline can be rerun against saved project state with identical results. This validates the rebuild requirement and exposes any non-determinism in the pipeline.

*Outputs:* Rebuild action in the UI and CLI. Produces byte-identical `.package` files given identical input state.
*Dependencies:* 4.2, 0.5.
*Acceptance:* Rebuilding a project produces identical outputs. Test harness verifies byte equality.

---
