# PRD — Document Meta, Deferred Questions, Next Documents

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §1, §2, §37, §38

> Document status, purpose, deferred open questions, and recommended next documents.

---

## 1. Document Status

- **Project:** AI Sims Creator
- **Document Type:** Product Requirements Document (PRD)
- **Document Version:** 1.0
- **Status:** Draft for review
- **Supersedes:** AI Sims Creator — Project Overview (vision document)
- **Purpose:** Define the product requirements in a form suitable for implementation by engineering and AI coding agents, with all foundational decisions resolved.
- **Intended Audience:** Project owner, maintainer, AI coding agents (primarily Claude Code), future collaborators.
- **Scope:** MVP-first, with forward-looking structure that avoids dead-end implementation decisions and explicitly accommodates known v1.5+ features.
- **Related Documents:**
  - MVP Specification (to follow)
  - Technical Architecture Document (to follow)
  - Architecture Diagrams (to follow)
  - API Specification for internal IPC (to follow)

---



## 2. Purpose of This Document

This PRD translates the product concept into actionable product requirements that can guide design and implementation. It is written to be directly consumable by a coding agent.

This document answers:

- What must be built?
- Who is it for?
- What user problems does it solve?
- What capabilities are required in MVP?
- What is explicitly out of scope?
- What workflows must exist?
- What behaviors, validations, and outputs are required?
- How should success be measured?

This document intentionally defers detailed schema design, implementation sequencing, and architecture to the MVP Specification and Technical Architecture Document.

---



## 37. Open Questions Deferred to MVP Specification and TAD

These are intentionally deferred.

1. Exact Tier 1 template roster and count
2. Exact mesh format and authoring standard for Tier 1 templates
3. Exact Pydantic/TypeScript schema definitions
4. Exact project storage layout under the project folder
5. Exact model selections (specific Replicate-hosted image model, etc.)
6. DBPF library choice (evaluate during POC)
7. Dependency specifics for the Python sidecar
8. Pipeline concurrency and retry policies
9. Auto-install conflict handling (overwrite? rename?)
10. User verification flow exact UI and data capture

These belong in the MVP Specification and Technical Architecture Document.

---



## 38. Recommended Next Documents

After this PRD is reviewed and approved, the following documents follow in sequence.

1. **MVP Specification**
   - Exact feature cut for the first build
   - Implementation phases and sequencing
   - Milestone zero (texturing POC) detailed plan
   - Supported template roster
   - Supported archetype-to-reference-object mapping
   - Acceptance tests
   - Task breakdowns for Claude Code consumption

2. **Technical Architecture Document (TAD)**
   - Component architecture
   - Frontend / Python sidecar split and IPC
   - Job orchestration
   - Internal schemas (Pydantic and TypeScript)
   - Project storage layout
   - External integrations (Replicate, Anthropic, local Sims install, Blender)
   - DBPF packaging pipeline
   - Tuning clone pipeline
   - Validation pipeline
   - Auto-install mechanism
   - Platform-specific details

3. **Architecture Diagrams (standalone document)**
   - Container diagram (frontend, sidecar, external deps)
   - Pipeline sequence diagram (prompt → plan → generation → assembly → validation → export → install)
   - Data model diagram
   - Admin mode architecture

4. **Internal API Specification**
   - Tauri ↔ Python sidecar IPC contract
   - Request/response schemas
   - Job lifecycle events

---
