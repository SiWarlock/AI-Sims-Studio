# Diagrams — Document Meta, Conventions, Index, and Maintenance

> **Source:** `docs/MONOLITHIC/Architecture_Diagrams.md` · **Area:** Diagrams · **Sections:** §1, §2, §14, §15

> Document meta, shape/arrow/color conventions, full diagram index, maintenance notes.

---

## 1. Document Status

- **Project:** AI Sims Creator
- **Document Type:** Architecture Diagrams
- **Document Version:** 1.0
- **Status:** Draft for review
- **Depends On:** AI Sims Creator PRD v1.0, MVP Specification v1.0, TAD v1.0
- **Precedes:** API Specification
- **Purpose:** Provide visual reference diagrams for every major architectural concept in the TAD. Diagrams are authored in Mermaid so they are version-controllable, editable, and render natively in GitHub, Claude Code, and most markdown viewers.
- **Intended Audience:** Project maintainer, Claude Code, future contributors.

---



## 2. Diagram Conventions

### 2.1 Shape Language

| Shape | Meaning |
|---|---|
| Rectangle | Module, component, service |
| Rounded rectangle | Entry point, UI screen, user-facing surface |
| Cylinder | Data store (SQLite, file system, cache) |
| Parallelogram / hexagon | External system (API, user's Sims install, Blender) |
| Circle | State (in state diagrams) |
| Diamond | Decision point |

### 2.2 Arrow Language

| Arrow | Meaning |
|---|---|
| Solid arrow `-->` | Synchronous call, direct data flow, or dependency |
| Dashed arrow `-.->` | Asynchronous event, notification, or progress message |
| Thick arrow `==>` | Primary user-driven flow (emphasized path) |

### 2.3 Color Coding

Colors are applied via Mermaid `classDef` for visual grouping. The scheme used throughout:

- **Frontend / UI** — blue
- **Sidecar / Python** — green
- **External systems** — gray
- **Data stores / persistence** — orange
- **AI-driven stages** — purple
- **Deterministic stages** — teal
- **Admin-only** — red

---



## 14. Diagram Index

Quick reference.

| § | Diagram | Kind | Shows |
|---|---|---|---|
| 3.1 | Container Diagram | Flowchart | Processes, external systems, top-level data stores |
| 3.2 | Sidecar Component | Flowchart | Python modules and dependencies |
| 3.3 | Frontend Component | Flowchart | React screens, Redux slices, IPC client |
| 3.4 | Deployment Topology | Flowchart | Where files live on disk |
| 4.1 | Entity Relationships | ER | Domain entities and their cardinalities |
| 4.2 | Project Folder Layout | Tree | Per-project directory structure |
| 5.1 | Project Creation | Sequence | New project → approved plan |
| 5.2 | Collection Generation | Sequence | Approved plan → generated collection |
| 5.3 | Per-Item Regeneration | Sequence | Single item regen isolated |
| 5.4 | Functional Overlay | Sequence | Decor → functional upgrade |
| 5.5 | Validation and Export | Sequence | Validate → build → auto-install |
| 5.6 | Deterministic Rebuild | Sequence | Admin rebuild with parity check |
| 5.7 | IPC Message Flow | Sequence | stdio JSON-RPC mechanics |
| 6.1 | Item Lifecycle | State | Item state transitions |
| 6.2 | Collection Lifecycle | State | Collection state transitions |
| 6.3 | BuildJob Lifecycle | State | Job state transitions |
| 6.4 | Swatch Lifecycle | State | Swatch state transitions |
| 6.5 | Functional Overlay Lifecycle | State | Overlay state transitions |
| 7.1 | Template Tier Flow | Flowchart | Tier 1/2 relationships and promotion |
| 7.2 | Template Resolution | Flowchart | Request → template match logic |
| 8.1 | AI Stages Overview | Flowchart | Where AI fits in the pipeline |
| 8.2 | Retry and Failure | Flowchart | Per-stage retry policy |
| 9.1 | Admin Mode Gating | State | Creator ↔ admin mode |
| 9.2 | Admin Operations | Flowchart | Admin action inventory |
| 10.1 | Error Flow | Flowchart | Error path from failure to user |
| 11.1 | Phase Dependencies | Flowchart | MVP phase gating |
| 11.2 | Phase 3 Task Deps | Flowchart | Representative intra-phase deps |
| 12.1 | Cross-Platform Paths | Flowchart | macOS vs Windows path resolution |
| 13.1 | Data Trust Boundaries | Flowchart | What leaves the machine |
| 13.2 | File Access Permissions | Flowchart | R/W, RO, and denied paths |

---



## 15. Diagram Maintenance

These diagrams are intended to be living artifacts. When the TAD changes, the corresponding diagrams in this document should be updated. Pull requests that modify core architecture are expected to update both the TAD and the Architecture Diagrams document in the same commit.

Mermaid diagrams render natively in:

- GitHub markdown
- Claude Code
- VS Code with Mermaid preview extension
- Most static site generators (MkDocs, Docusaurus, etc.)

No separate rendering step is required for development.

---

*End of Architecture Diagrams v1.0*
