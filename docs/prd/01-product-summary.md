# PRD — Product Summary, Positioning, and Thesis

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §3, §4, §9

> What the product is, its category and promise, and the core thesis for how it's built.

---

## 3. Product Summary

AI Sims Creator is a desktop-first creator studio for The Sims 4 that enables a non-technical creator to generate, refine, validate, and export themed custom content collections — and selected functional objects — through guided, AI-assisted workflows.

The product supports two creation paths that share a common underlying asset model:

1. **Decorative / Build-Buy Custom Content Pipeline** — generate themed collections of decorative clutter and furniture.
2. **Functional Object Pipeline** — upgrade selected decorative items into supported interactive objects by cloning base-game tuning.

These pipelines share a common internal asset model so that a generated decorative object can be upgraded into a functional object without being recreated.

The product is not a generic chatbot. It is a domain-specific Sims content studio with structured workflows, controlled generation, deterministic validation and build steps, and a creator-friendly UI.

---



## 4. Product Positioning

### 4.1 Core Value Proposition

A Sims creator should be able to describe a themed collection in natural language, receive a coherent set of playable in-game assets, refine them visually, optionally make selected items functional, and export installable content without manually operating the full Sims modding toolchain.

### 4.2 Product Category

AI-assisted creator studio for Sims 4 custom content and selected functional mod generation.

### 4.3 Product Promise

The MVP must prove that a creator can:

- start from a theme prompt,
- generate a coherent collection of decorative and furniture assets,
- review and selectively regenerate assets,
- make a supported generated object functional,
- validate the output,
- and export installable game content that appears correctly in-game.

---



## 9. Product Thesis

The correct product approach is **AI-assisted, schema-driven, template-based, and deterministic where required**.

The system must not rely on an unconstrained frontier model directly controlling external tools or generating arbitrary 3D geometry.

Instead:

- **AI is used for planning, ideation, texture generation, metadata drafting, and tuning value suggestions.**
- **Structured domain schemas represent collections, items, templates, texture zones, functional overlays, and archetypes.**
- **A curated template library provides the 3D geometry foundation.** AI never generates meshes; it selects and styles them.
- **Deterministic code assembles textured meshes, renders thumbnails, clones base-game tuning, and packages DBPF files.**
- **Validation gates ensure output quality before export.**

This is a product requirement, not only an implementation preference. The value proposition depends on AI contributions being channeled through reliable deterministic steps.

---
