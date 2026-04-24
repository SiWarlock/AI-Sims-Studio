# PRD — Users and Problem Statement

> **Source:** `docs/MONOLITHIC/PRD.md` · **Area:** PRD · **Sections:** §5, §6

> Primary creator, administrator, and future users. The problems this product solves.

---

## 5. Users

### 5.1 Primary User — The Creator

**Profile:** Non-technical Sims creator building personal content and world builds.

**Concrete user:** The product owner's girlfriend, who is an experienced Sims builder, prefers Alpha CC styling, uses a Mac, and is non-technical.

**Traits:**

- Understands Sims gameplay, build mode, and the CC ecosystem as a consumer and builder
- Has strong aesthetic judgment and distinct style preferences
- Knows what items she wants in a collection and how she wants them to look
- Does not want to interact with Blender, DBPF internals, tuning XML, S4Studio, or any low-level modding tooling
- Will install the app herself via a standard installer

**Needs:**

- Prompt-driven collection creation
- Visual previews she can trust
- Control over style and collection composition
- Safe, guided functional upgrades
- Reliable exports that actually work in her game
- Auto-install to her Mods folder
- Minimal technical friction throughout

### 5.2 Secondary User — The Administrator / Maintainer

**Profile:** Technical maintainer who authors templates, inspects failures, manages the template library, and keeps the system healthy.

**Concrete user:** The product owner, a technical developer who will use a Windows machine for admin and debugging work.

**Traits:**

- Comfortable with code, XML, Blender, Sims modding tools
- May use external tools (Sims 4 Studio, Mod Constructor, XML Extractor) for template authoring and debugging
- Responsible for growing the template library
- Responsible for fixing the app when something breaks

**Needs:**

- Admin mode accessible from within the app, providing:
  - Template library browser and editor
  - Base-game mesh importer (Tier 2 template management)
  - Build logs, job history, validation detail
  - Reference object browser for inspecting base-game tuning
  - Manual rebuild and diagnostic controls
- Deterministic rebuilds
- Inspectable project state
- Clear error reporting

**Important:** The administrator is not treated as a separate product persona with its own full UX. Admin functionality is a **mode within the same application**, accessible via keyboard shortcut or menu, but hidden from the primary creator flow.

### 5.3 Future Users (Out of Scope for MVP)

The product should not be architected in ways that permanently block:

- Small creator teams (multi-user projects)
- Other non-technical creators beyond the primary user
- Distribution of exports to a wider audience

These are non-requirements for MVP but must not be permanently foreclosed by architectural decisions.

---



## 6. Problem Statement

Current Sims 4 custom content creation workflows are fragmented, technical, and inconsistent. Creators must combine multiple tools (Blender, S4Studio, image editors, sometimes XML editors) and execute manual steps to produce even simple custom content, and more for functional objects.

This creates the following product problems:

1. **Technical barrier** — game-savvy creators are blocked by technical implementation details.
2. **Workflow fragmentation** — multiple tools, file formats, and manual steps.
3. **Low throughput** — themed collections take significant time to produce and maintain.
4. **Low reuse** — decorative objects and functional objects are typically separate efforts even when they share shape.
5. **Quality inconsistency** — hand-assembled or loosely-generated content may not be game-ready or stylistically coherent.
6. **Patch fragility** — exported content may break as the game evolves, with no clear repair path.

---
