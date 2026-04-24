# MVP Spec — Phase Overview and Gating

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §4

> The eight MVP phases and their gating structure. Phase 1 is a hard quality gate.

---

## 4. Implementation Phases

MVP v1.0 is delivered in eight phases, sequenced to minimize rework and to surface the highest-risk piece (texturing quality) as early as possible.

No time estimates are included. Phases are gated by completion of their acceptance criteria, not by calendar.

### 4.1 Phase Overview

1. **Phase 0 — Foundation**
   App shell, project storage, platform detection. No AI, no templates.
2. **Phase 1 — Milestone Zero: Texturing Proof-of-Concept**
   One template, one prompt, full pipeline to in-game verification. This is the quality gate that de-risks the entire product.
3. **Phase 2 — Template Library**
   Author all 19 Tier 1 templates with full schemas. Build template loader.
4. **Phase 3 — Decorative Generation Pipeline**
   Collection planning, per-item spec generation, full texture pipeline, thumbnail rendering, metadata generation, collection board UI, item detail UI.
5. **Phase 4 — Validation, Export, and Auto-Install**
   Structural validation, export screen, DBPF build pipeline, Mods folder auto-install.
6. **Phase 5 — Functional Overlay**
   Archetype configuration, tuning extraction, clone pipeline, functional variant packaging.
7. **Phase 6 — Admin Mode**
   Template browser, base-game importer, Tier 2 promotion editor, logs viewer, job history, reference object browser.
8. **Phase 7 — Cross-Platform Hardening and Polish**
   Windows parity, path handling edge cases, Blender discovery, verification flow polish, documentation.

### 4.2 Phase Gating

Each phase has explicit completion criteria. A phase is complete only when all its acceptance criteria pass. The next phase does not begin until the prior phase is complete.

Exception: Phase 1 (Milestone Zero) is a hard gate. If Phase 1 fails to produce a convincing in-game result, the MVP must pause for approach revision before Phase 2 begins.

---
