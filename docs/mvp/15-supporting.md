# MVP Spec — Decisions Log, Docs, Risks, Success, and Summary

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §12, §13, §14, §15, §16, §17

> Decisions resolution log, documentation deliverables, risks and mitigations, release success criteria, post-MVP directions, and executive summary.

---

## 12. Decisions Made During MVP (Resolution Log)

This section is populated during Phase 1 and onwards. Each entry records a decision, its context, and when it was resolved.

- **D-1 — DBPF library choice.** Resolution target: Phase 1, Task 1.6.
- **D-2 — Primary image generation model.** Resolution target: Phase 1, Task 1.3.
- **D-3 — Normal and specular map derivation strategy.** Resolution target: Phase 1, Task 1.3.
- **D-4 — Exact base-game reference object IDs.** Resolution target: Phase 5, Task 5.2.
- **D-5 — Blender headless render recipe.** Resolution target: Phase 1, Task 1.5.
- **D-6 — Texture resolution policy.** Resolution target: Phase 1, Task 1.3–1.4.

Additional decisions encountered during implementation are logged here with the same format.

---



## 13. Documentation Deliverables

All produced during Phase 7.

- **README.md** — repo-level technical setup and contributing notes.
- **User manual** — end-user guide for the primary creator. Plain language, screenshots, walkthrough.
- **Maintainer guide** — admin-mode reference, template authoring, debugging, Windows tooling recommendations, failure recovery.

These are in addition to the PRD, this MVP Specification, the TAD, the Architecture Diagrams document, and the API Specification.

---



## 14. Risks and Mitigations

### 14.1 Texture Quality Below Acceptable Bar

**Risk:** The selected image model cannot produce semi-Alpha quality textures that hold up at in-game distance.
**Mitigation:** Phase 1 is a hard gate. If POC fails, pause MVP for approach revision before committing to Phases 2+.

### 14.2 Base-Game Reference Cloning Fragility

**Risk:** Cloned tuning references break under a Sims 4 patch.
**Mitigation:** Document exact reference IDs and tuning fields touched. Accept that patch-repair is a post-MVP concern. Validation extensions can detect common breakage patterns.

### 14.3 Cross-Platform Divergence

**Risk:** Mac and Windows builds diverge in subtle ways (path handling, file encoding, DBPF byte order).
**Mitigation:** Parity test as part of Phase 7. Deterministic rebuild test in Phase 4 catches non-determinism early.

### 14.4 Template Authoring Backlog

**Risk:** Authoring 19 templates at Tier 1 quality is a significant solo effort.
**Mitigation:** Templates can be seeded from base-game meshes as starting points (via Phase 5 extraction tools, which exist by Phase 2). Authoring standard (Task 2.1) exists before 2.2 and 2.3 start.

### 14.5 Replicate API Instability

**Risk:** Replicate (or the selected model) has an outage or deprecates a model.
**Mitigation:** The Anthropic and Replicate integrations are isolated modules. Alternative providers (Fal, Wavespeed) can be swapped in without pipeline redesign.

---



## 15. Success Criteria for the MVP Release

The MVP is considered successful when:

1. The primary user creates a themed collection end-to-end without maintainer intervention.
2. The exported items work correctly in her Sims 4 game.
3. She expresses confidence in using the tool for her own builds.
4. The maintainer can diagnose and fix any single-project failure using admin mode alone.
5. All acceptance criteria in §10 pass on both platforms.

---



## 16. What Comes After MVP v1.0

Out of scope for MVP but architected to support:

- Maxis Match visual style (v1.5)
- Additional functional archetypes (computer, stove, appliance categories)
- Patch-repair flow for tuning references that break under Sims updates
- AI-generated mesh exploration (v2+)
- Multi-user or team features (v2+)
- Project archive format with versioning and portability

These are not committed; they are documented forward paths that the MVP architecture does not foreclose.

---



## 17. Executive Summary

MVP v1.0 of AI Sims Creator is an eight-phase delivery: foundation, texturing proof-of-concept, template library, decorative generation, export and install, functional overlay, admin mode, and cross-platform polish.

The anchor of the MVP is Phase 1, Milestone Zero — a hard quality gate where one complete pipeline is built end-to-end, validated in-game, and confirmed visually before the remaining phases commit. This structure front-loads the highest-risk element (AI texture quality at production scale) while minimizing wasted work if that element fails the bar.

The template library is the central engineering investment. 19 curated Tier 1 primitives plus the Tier 2 base-game importer give the product the versatility to handle arbitrary themed collections without AI-generated geometry, and grow over time as gaps appear.

The administrator is the product owner, operating inside the same app through admin mode. The primary user is a non-technical creator who should experience a guided, prompt-driven, visually rich workflow that hides every technical detail below.

Tasks throughout are scoped at medium granularity for Claude Code consumption, with decomposition into subtasks expected at implementation time. Time estimates are intentionally omitted.

---

*End of MVP Specification v1.0*
