# MVP Spec — Phase 2 — Template Library

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.3

> Author all 19 Tier 1 templates and build the template loader infrastructure.

---

**Phase goal:** Author all 19 Tier 1 templates and build the template loader infrastructure. No AI integration in this phase.

**Phase acceptance gate:** All 19 templates exist as `.glb` files with full schemas. The template loader can query them by attribute. Each template renders correctly in Blender and each has been inspected at a placeholder texture for visual correctness.

#### Tasks

**2.1 — Template authoring pipeline**
Document the template authoring standard as a living reference. Set up a workflow for authoring new templates in Blender: topology guidelines, UV unwrapping conventions, texture zone marking, footprint/slot data conventions, `.glb` export settings.

*Outputs:* An authoring guide in the repo documenting every step. A Blender file template with the conventions pre-applied.
*Dependencies:* 1.1, 1.5.
*Acceptance:* Following the guide, a new template can be authored from a base reference without ambiguity.

**2.2 — Tier 1 template authoring: decor primitives (11)**
Author all 11 decor and clutter templates listed in §6.1 following the authoring pipeline. Each template includes geometry, clean UVs, labeled texture zones, and footprint data.

*Outputs:* 11 `.glb` files under the template library.
*Dependencies:* 2.1.
*Acceptance:* Each template renders correctly, each has correct texture zones, each passes the authoring checklist.

**2.3 — Tier 1 template authoring: furniture primitives (8)**
Author all 8 furniture templates listed in §6.2 following the authoring pipeline.

*Outputs:* 8 `.glb` files under the template library.
*Dependencies:* 2.1.
*Acceptance:* Each template renders correctly, each has correct texture zones and slot data, each passes the authoring checklist.

**2.4 — Template schema loader**
Build a Python module that loads all templates from disk, parses their metadata, validates schemas, and exposes a query API (by shape class, dimension range, archetype compatibility, etc.).

*Outputs:* A template registry with a typed query API.
*Dependencies:* 2.2, 2.3.
*Acceptance:* All 19 templates load successfully. Queries return correct subsets. Schema validation catches malformed templates.

**2.5 — Template visual inspection harness**
Build a simple internal tool that renders each template with a neutral placeholder texture and outputs thumbnails for manual review. This is a maintainer-facing sanity check tool.

*Outputs:* A script that produces a thumbnail gallery of all 19 templates.
*Dependencies:* 2.4, 1.5.
*Acceptance:* Gallery is generated and all templates look correct.

---
