# MVP Spec — Overview and MVP Definition

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §1, §2, §3, §5

> Document status, purpose, what MVP v1.0 is and is not, and explicit deferrals.

---

## 1. Document Status

- **Project:** AI Sims Creator
- **Document Type:** MVP Specification
- **Document Version:** 1.0
- **Status:** Draft for review
- **Depends On:** AI Sims Creator PRD v1.0 (approved)
- **Precedes:** Technical Architecture Document, Architecture Diagrams, API Specification
- **Purpose:** Define exactly what ships in the first version of AI Sims Creator and in what order, with tasks scoped for Claude Code consumption.
- **Intended Audience:** Project owner, maintainer, Claude Code (primary implementation agent).

---



## 2. Purpose of This Document

This MVP Specification translates the PRD into an executable plan. It answers:

- What exactly ships in MVP v1.0?
- What is explicitly not shipping in MVP v1.0 even though the PRD allows it?
- In what order is the work done?
- What gates separate one phase from the next?
- What tasks does each phase contain, scoped for a coding agent to execute?
- What must be tested and at what level?
- What decisions are deferred to POC time rather than pre-committed?
- What documentation deliverables are produced alongside the code?

This document does not define technical architecture (TAD), data schemas (TAD), diagrams (Architecture Diagrams doc), or internal IPC contracts (API Specification). It references them where needed.

---



## 3. MVP Definition

### 3.1 What MVP v1.0 Is

MVP v1.0 is a cross-platform desktop application (macOS and Windows) that enables a non-technical creator to:

1. Create a new project from a natural language prompt describing a themed collection (or a single-item project).
2. Receive a structured, editable collection plan with items matched to template primitives.
3. Generate decorative Build/Buy assets from the plan using a curated template library and AI-driven semi-Alpha texture generation.
4. Review items on a collection board and in detail views, with per-item regenerate, replace, and exclude controls.
5. Upgrade selected items to supported functional objects using base-game tuning cloning for four archetypes.
6. Validate the project structurally.
7. Export as `.package` files and auto-install to the user's Sims 4 Mods folder.
8. Optionally confirm in-game that items appear correctly.

Administrator mode within the same application provides template library management, base-game mesh import, logs, job history, and reference object inspection.

### 3.2 What MVP v1.0 Is Not

See §5 for the explicit deferrals list.

---



## 5. Explicit MVP Deferrals

The PRD permits these capabilities but they do not ship in MVP v1.0. They are deferred to v1.5 or later.

- **Maxis Match visual style.** Architecture supports a style parameter; UI ships locked to semi-Alpha.
- **Functional archetypes beyond the MVP four.** No computer, no stove, no novel archetypes. Only light on/off, audio device, mirror, moodlet emitter.
- **Template authoring via the UI.** Templates are either Tier 1 (shipped or authored in Blender following documented standards) or Tier 2 (imported from base-game). No in-app Blender substitute.
- **Project import/export as portable archives.** Project folders can be copy-pasted manually; no explicit archive format with versioning, signing, or import validation.
- **Batch operations across multiple projects.** One project at a time.
- **Multi-user collaboration.** Single-user local only.
- **Public distribution or marketplace integration.** No upload, no sharing, no metadata tied to public creator IDs.
- **CAS content of any kind.** No Sims, no clothing, no hair, no makeup.
- **Animation authoring.** No custom animations.
- **Script mods beyond tuning clones.** No Python script modding, no custom gameplay systems.
- **Localization beyond English.** All UI strings and generated metadata are English-only.
- **Telemetry or remote logging.** No outbound network traffic other than required AI API calls.
- **Auto-update mechanism.** Manual builds shipped by the maintainer.
- **Mobile or web clients.** Desktop only.
- **AI-generated mesh geometry.** All geometry comes from templates. Evaluated for v2+.

---
