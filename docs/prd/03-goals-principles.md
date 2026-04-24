# PRD — Goals, Non-Goals, and Product Principles

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §7, §8, §11

> Primary and secondary goals, explicit non-goals, and product principles.

---

## 7. Product Goals

### 7.1 Primary Goals

1. Reduce technical friction for Sims content creation to near-zero for the primary creator.
2. Enable automatic generation of coherent object collections from natural language prompts.
3. Support generated objects that are playable in-game as Build/Buy content.
4. Support promoting selected generated objects into supported functional objects.
5. Provide visual review and iterative refinement without forcing the user into external tools.
6. Produce reliable, installable exports with validation.
7. Provide auto-install to the user's Mods folder.

### 7.2 Secondary Goals

1. Provide admin mode capable of diagnostics and template library management.
2. Support future growth into richer content categories and styles.
3. Enable deterministic rebuilds and a future patch-repair workflow.
4. Keep creator UX simple while preserving advanced control layers under admin mode.

---



## 8. Non-Goals

The MVP must not attempt to solve all possible Sims creation problems.

Out of scope for MVP:

- Full arbitrary mod generation from any prompt
- Fully custom animation generation
- Create-A-Sim (CAS) content of any kind
- Broad script-heavy gameplay overhauls
- Multi-user collaboration
- Public marketplace/distribution automation
- Plugin ecosystem
- Every possible Build/Buy object type
- AI-generated novel 3D meshes (MVP uses a template library)
- Automated in-game test playthroughs
- Telemetry or crash reporting to remote servers
- Auto-update infrastructure
- Localization beyond English
- Maxis Match visual style (architected for, shipped post-MVP)

The MVP must focus on a constrained, reliable path.

---



## 11. Product Principles

1. **Prompt-driven but not uncontrolled.** User intent is captured as prompts, but every generation runs through structured schemas and deterministic assembly.
2. **Collection-first, single-item-supported.** The primary unit of work is a themed collection, but a collection of one is a legitimate use case.
3. **One asset, multiple outputs.** A generated decorative object can be upgraded to functional without reconstruction.
4. **Reviewable before export.** Every item is previewable, every swatch inspectable, every piece of metadata editable.
5. **Structured under the hood, simple on the surface.** Schemas are rich; the creator UI is clean.
6. **Deterministic where game constraints matter.** Packaging, tuning cloning, and validation are not AI-driven.
7. **Progressive disclosure for advanced users.** Admin mode exposes depth without cluttering the primary flow.
8. **Optimize for creator trust, not AI novelty.** The product must be honest about what it can and cannot do.
9. **Template library is the foundation.** Visual quality and variety scale through the template library, not through per-item AI geometry generation.
10. **Style is a first-class property of a collection.** Every collection picks a visual style; all items in it inherit that style.

---
