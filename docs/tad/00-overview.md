# TAD — Document Meta, Architecture Overview, and Summary

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §1, §2, §23

> Document meta, architecture overview including system shape and principles, and executive summary.

---

## 1. Document Status

- **Project:** AI Sims Creator
- **Document Type:** Technical Architecture Document (TAD)
- **Document Version:** 1.0
- **Status:** Draft for review
- **Depends On:** AI Sims Creator PRD v1.0 (approved), AI Sims Creator MVP Specification v1.0 (approved)
- **Precedes:** Architecture Diagrams, API Specification
- **Purpose:** Define the technical architecture, component design, data schemas, pipelines, and integration patterns for AI Sims Creator MVP v1.0. This document is the source of truth for implementation.
- **Intended Audience:** Project maintainer, Claude Code (primary implementation agent), future contributors.

---



## 2. Architecture Overview

### 2.1 System Shape

AI Sims Creator is a cross-platform desktop application composed of three primary layers:

1. **Frontend** — Tauri v2 shell hosting a React application. Renders all user interfaces, handles user input, dispatches requests to the sidecar, receives and reacts to events from the sidecar.
2. **Python Sidecar** — A single long-running Python process launched by Tauri as a subprocess. Owns all generation logic, AI integrations, file operations, DBPF packaging, tuning cloning, validation, and project persistence.
3. **External Systems** — The Anthropic API (Claude models), Replicate API (image generation), the user's local Sims 4 installation (read-only), the user's Sims 4 Mods folder (write), and a local Blender installation (subprocess invocation).

The frontend never calls external services directly. All network access, all file system access beyond what Tauri handles natively, and all invocation of external tools runs through the Python sidecar.

### 2.2 Architectural Principles

1. **Deterministic pipelines where game compatibility matters.** AI touches planning, texture generation, metadata drafting, and tuning value suggestions. AI never touches DBPF packaging, mesh geometry, tuning XML structure, or validation logic.
2. **Schema-enforced boundaries.** Every IPC message, every AI response, every persisted record passes through a Pydantic schema on the Python side. Types are auto-generated into TypeScript for the frontend.
3. **Single responsibility per component.** Each pipeline stage is a discrete module with a clear input schema, output schema, and failure mode.
4. **Crash-resilient persistence.** Generation state is snapshotted at phase boundaries. Crashes lose in-flight work but not completed work.
5. **Observable.** Every stage logs structured events. Admin mode surfaces them directly.
6. **Platform-parity.** The same codebase produces identical outputs on macOS and Windows. Platform-specific logic is isolated to path resolution, install detection, and log file location.

### 2.3 High-Level Data Flow

A generation run proceeds through these stages:

1. User prompt → Frontend collects inputs → IPC request to sidecar
2. Sidecar dispatches to Collection Planning stage → Claude Sonnet produces structured plan
3. User reviews and approves plan via frontend
4. Sidecar dispatches to Per-Item Spec Generation stage (parallel per item) → Claude Sonnet produces per-item specs
5. Sidecar dispatches to Texture Generation stage (parallel per swatch) → Replicate produces texture maps
6. Sidecar dispatches to Thumbnail Render stage (sequential, Blender subprocess) → PNG thumbnails produced
7. Sidecar persists all artifacts to project storage → Status events stream to frontend
8. User reviews items, issues regenerate/replace/exclude actions as needed
9. User triggers export → Sidecar runs Validation → DBPF Build → Auto-Install → Reports status

Functional upgrades follow a parallel sub-pipeline: archetype configuration → base-game resource extraction → tuning clone with user values → functional variant packaging.

---



## 23. Executive Summary

AI Sims Creator is a monorepo Tauri v2 + React frontend paired with a Python 3.12 sidecar communicating via stdio JSON-RPC. The sidecar is a single persistent asyncio process owning all generation logic, AI integrations, and file operations.

Data is modeled via Pydantic v2 with types auto-generated for TypeScript. Persistence is SQLite per project with yoyo-migrations. Projects are self-contained folders containing the database, assets, and exports.

The generation pipeline is composed of discrete stages with clean schemas: collection planning (Claude Sonnet), per-item spec generation (Claude Sonnet), texture generation (Replicate image model), thumbnail rendering (Blender subprocess), DBPF packaging (deterministic), validation (structural), auto-install (direct copy to Mods folder).

Four functional archetype handlers (light, audio, mirror, moodlet) clone base-game tuning from the user's Sims install and apply targeted edits based on user configuration.

The template library is the central technical investment: 19 Tier 1 curated primitives with rich schemas, plus a Tier 2 importer for user-added base-game meshes. The library grows through admin-mode workflows without architectural change.

Cross-platform parity is enforced through isolated path-handling modules, deterministic build pipelines, and byte-equality tests on rebuilt exports across macOS and Windows.

No telemetry. No auto-update. Local-only observability. API keys in platform keyrings. Sims install accessed read-only.

The architecture supports the PRD's forward paths (Maxis Match visual style, additional archetypes, AI mesh generation exploration, multi-user features) without requiring rework of the foundational layers.

---

*End of TAD v1.0*
