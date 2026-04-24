# Documentation Navigation Guide for Claude Code

You are working inside the `docs/` tree of AI Sims Creator. This file is your guide to finding the right documentation shards without loading the entire spec.

## Core Rule

**Load only the shards you need for the task at hand.** Loading all docs consumes ~47k tokens and leaves little workspace for code. Loading one or two focused shards consumes 2–5k tokens and leaves ample room.

## Source of Truth

- **Shards** under `docs/prd/`, `docs/mvp/`, `docs/tad/`, `docs/api/`, `docs/diagrams/` are authoritative.
- **Monolithics** under `docs/MONOLITHIC/` are regenerated outputs — never edit them.
- When updating docs, always edit the shard, never the monolithic.

## When to Load What

### By task shape

| Task shape | Load |
|-----------|------|
| Implementing an IPC method | `docs/api/{namespace}.md` + relevant `docs/tad/` component shard |
| Implementing a pipeline stage | `docs/tad/04-pipelines.md` + relevant AI or assembly shard |
| Working on a Phase N task | `docs/mvp/0{N+5}-phase-{N}-{slug}.md` + any shards its tasks reference |
| Writing a new Pydantic model | `docs/tad/02-data-model.md` + `docs/api/00-overview.md` (for type conventions) |
| Adding an archetype handler | `docs/tad/06-archetype-handlers.md` + `docs/mvp/03-archetype-mapping.md` + `docs/tad/09-tuning-clone.md` |
| DBPF or tuning work | `docs/tad/08-dbpf-packaging.md` and/or `docs/tad/09-tuning-clone.md` |
| Template authoring | `docs/prd/05-content-and-style.md` + `docs/mvp/02-template-roster.md` + `docs/tad/07-template-library.md` |
| Validation logic | `docs/tad/10-validation.md` + `docs/api/08-validation.md` |
| Export / install | `docs/tad/11-install.md` + `docs/api/09-export.md` |
| Admin mode | `docs/tad/12-admin-mode.md` + `docs/api/12-admin.md` |
| Cross-platform bug | `docs/tad/13-cross-platform.md` + `docs/diagrams/10-cross-platform-security.md` |
| Error handling / logging | `docs/tad/14-errors-logging.md` + `docs/api/14-error-codes.md` |
| Implementing frontend screen | `docs/prd/08-non-functional-and-workflows.md` + `docs/tad/01-component-architecture.md` |
| Verification against an AC | `docs/prd/09-acceptance-and-guardrails.md` or `docs/mvp/13-acceptance-criteria.md` |
| Verification against an FR | `docs/prd/07-functional-requirements.md` |

### By FR / AC identifier

- **FR-001 through FR-087** — look in `docs/prd/07-functional-requirements.md`
- **AC-001 through AC-016** — look in `docs/prd/09-acceptance-and-guardrails.md`
- **MVP-AC-001 through MVP-AC-030** — look in `docs/mvp/13-acceptance-criteria.md`
- **D-1 through D-6** — look in `docs/mvp/04-deferred-decisions.md`

### By phase

Every phase has a dedicated file: `docs/mvp/0{N+5}-phase-{N}-{slug}.md`. Loading one phase file gives you its complete task list with acceptance criteria per task. Do not load more than one phase file at a time unless tasks explicitly cross phases.

## Quick Lookups That Don't Require Loading

Some questions don't need doc loading — the answer is in this file:

- **Total MVP phases:** 8 (Phase 0 through Phase 7)
- **Template library size in MVP:** 19 Tier 1 primitives (11 decor + 8 furniture)
- **Functional archetypes in MVP:** 4 (light on/off, audio device, mirror, moodlet emitter)
- **Visual style in MVP:** semi-Alpha only (architecture accepts style param for future MM)
- **Platform targets:** macOS + Windows, shared codebase
- **IPC mechanism:** JSON-RPC 2.0 over stdio
- **Primary runtime:** Tauri v2 host + React/RTK frontend + Python 3.12 sidecar
- **State management (frontend):** Redux Toolkit
- **Schema library:** Pydantic v2
- **AI models:** Claude Sonnet 4.6 for reasoning, Claude Haiku 4.5 for rewriting, Replicate-hosted image model for textures (exact model D-2 resolved during Phase 1 POC)

## Cross-Reference Rewriting

When referring to documentation in code comments or new docs, use shard paths:

- Good: `see docs/tad/02-data-model.md §4.2`
- Also good: `per FR-025 in docs/prd/07-functional-requirements.md`
- Avoid: `see TAD §4.2` (ambiguous about whether to load the whole TAD)

## Editing Shards

1. Edit the shard file directly.
2. Keep the shard's front-matter intact (the `> **Source:**` block at the top).
3. If cross-referencing another shard, use the full `docs/...` path.
4. Do not edit anything in `docs/MONOLITHIC/`. Those are regenerated.
5. After meaningful changes, optionally run `python docs/build_monolithic.py` to refresh the monoliths.

## When To Regenerate Monoliths

- Before sharing docs externally (export to PDF, send to a collaborator).
- Before a major release.
- Not after every shard edit (that would just be noise).

## Splitting a Shard

If a shard grows too large (beyond ~4k tokens), split it:

1. Decide on the split boundary (usually a subsection).
2. Create the new shard file(s).
3. Update `docs/README.md` to list the new shard(s).
4. Update this file (`docs/CLAUDE.md`) if the task→shard mapping is affected.
5. Update the corresponding entry in `shard_docs.py` so the sharding stays reproducible.

## Adding a New Doc Area

If a new document area is added (e.g., a user manual):

1. Create the directory under `docs/`.
2. Shard it following the same conventions.
3. Add an area block to `docs/README.md`.
4. Add relevant task mappings to this file.
5. Extend `build_monolithic.py` to emit a monolithic for the new area.
