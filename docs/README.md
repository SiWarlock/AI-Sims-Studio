# AI Sims Creator — Documentation Index

This directory contains the complete documentation for AI Sims Creator, organized into **shards** for efficient retrieval. Each shard is a focused slice of one of the five source documents, small enough to load without consuming excessive context.

## Source of Truth

Shards under `docs/prd/`, `docs/mvp/`, `docs/tad/`, `docs/api/`, and `docs/diagrams/` are the **authoritative source** of project documentation. The monolithic files under `docs/MONOLITHIC/` are **regenerated on demand** from the shards via `build_monolithic.py` and should not be edited directly.

Do not edit files in `docs/MONOLITHIC/` — your changes will be overwritten.

## How to Use This Documentation

- **Humans browsing the full spec**: run `python docs/build_monolithic.py` to regenerate fresh monoliths, then read from `docs/MONOLITHIC/`.
- **Claude Code working on a task**: read only the shards relevant to the task. See `docs/CLAUDE.md` for navigation guidance.
- **Updating documentation**: edit the shard file(s) only. Regenerate monoliths after the change if an export is needed.

## Sharding Workflow

```
docs/MONOLITHIC/*.md   (archived starting point, regenerated from shards)
        ↑
        │ build_monolithic.py  (optional regeneration)
        │
docs/{area}/*.md       (SOURCE OF TRUTH — edit these)
        ↑
        │ shard_docs.py  (one-time split; rerun only after editing the monolithics in MONOLITHIC/)
        │
docs/MONOLITHIC/*.md   (original full specs, preserved for reference)
```

In day-to-day use you only interact with the shards. The scripts exist for round-trip generation when needed.

---

## Document Areas

### PRD — Product Requirements
High-level product definition: what's being built, for whom, with what goals and constraints.

| Shard | Scope | Load when... |
|-------|-------|--------------|
| [`prd/00-document-meta.md`](prd/00-document-meta.md) | Document meta, deferred questions, next documents | Orientation only |
| [`prd/01-product-summary.md`](prd/01-product-summary.md) | Product summary, positioning, thesis | Need to explain what the product is |
| [`prd/02-users.md`](prd/02-users.md) | Users (creator, admin), problem statement | Working on user-facing features |
| [`prd/03-goals-principles.md`](prd/03-goals-principles.md) | Goals, non-goals, product principles | Scoping decisions, prioritization |
| [`prd/04-mvp-definition.md`](prd/04-mvp-definition.md) | MVP objective, anchor scenario, core capabilities, scope in/out | Understanding MVP boundaries |
| [`prd/05-content-and-style.md`](prd/05-content-and-style.md) | Content categories, visual style, template library model | Working on templates, styling, or archetypes |
| [`prd/06-user-stories.md`](prd/06-user-stories.md) | Creator, admin, and UX user stories | UX and feature design |
| [`prd/07-functional-requirements.md`](prd/07-functional-requirements.md) | All FR-001 through FR-087 | Implementing a specific FR-ID |
| [`prd/08-non-functional-and-workflows.md`](prd/08-non-functional-and-workflows.md) | Non-functional requirements, screens, workflows | Cross-cutting concerns, UX flow design |
| [`prd/09-acceptance-and-guardrails.md`](prd/09-acceptance-and-guardrails.md) | ACs, feature requirements, trust/safety/quality, metrics, release criteria, guardrails, assumptions | Verification, pre-release checks |

### MVP Spec — Implementation Plan
Exactly what ships in MVP v1.0, in what order, with what acceptance gates.

| Shard | Scope | Load when... |
|-------|-------|--------------|
| [`mvp/00-overview.md`](mvp/00-overview.md) | Document meta, MVP definition, deferrals | Orientation on what MVP is/isn't |
| [`mvp/01-phase-overview.md`](mvp/01-phase-overview.md) | The eight MVP phases and gating | Understanding project sequencing |
| [`mvp/02-template-roster.md`](mvp/02-template-roster.md) | The 19 Tier 1 template primitives | Template authoring, template-related code |
| [`mvp/03-archetype-mapping.md`](mvp/03-archetype-mapping.md) | Archetype → reference object mapping | Functional overlay work |
| [`mvp/04-deferred-decisions.md`](mvp/04-deferred-decisions.md) | D-1 through D-6 deferred to Phase 1 | Phase 1 POC work |
| [`mvp/05-phase-0-foundation.md`](mvp/05-phase-0-foundation.md) | Phase 0 tasks (foundation) | Working on Phase 0 |
| [`mvp/06-phase-1-poc.md`](mvp/06-phase-1-poc.md) | Phase 1 tasks (Milestone Zero POC) | Working on Phase 1 |
| [`mvp/07-phase-2-templates.md`](mvp/07-phase-2-templates.md) | Phase 2 tasks (template library) | Working on Phase 2 |
| [`mvp/08-phase-3-decorative.md`](mvp/08-phase-3-decorative.md) | Phase 3 tasks (decorative pipeline) | Working on Phase 3 |
| [`mvp/09-phase-4-validation-export.md`](mvp/09-phase-4-validation-export.md) | Phase 4 tasks (validation, export, install) | Working on Phase 4 |
| [`mvp/10-phase-5-functional.md`](mvp/10-phase-5-functional.md) | Phase 5 tasks (functional overlay) | Working on Phase 5 |
| [`mvp/11-phase-6-admin.md`](mvp/11-phase-6-admin.md) | Phase 6 tasks (admin mode) | Working on Phase 6 |
| [`mvp/12-phase-7-polish.md`](mvp/12-phase-7-polish.md) | Phase 7 tasks (cross-platform polish) | Working on Phase 7 |
| [`mvp/13-acceptance-criteria.md`](mvp/13-acceptance-criteria.md) | MVP-AC-001 through MVP-AC-030 | Pre-release verification |
| [`mvp/14-testing-strategy.md`](mvp/14-testing-strategy.md) | Unit, integration, manual, POC gate | Writing tests, QA planning |
| [`mvp/15-supporting.md`](mvp/15-supporting.md) | Decisions log, docs, risks, success, post-MVP, summary | Project hygiene, looking ahead |

### TAD — Technical Architecture
How the system is built: components, schemas, pipelines, integrations.

| Shard | Scope | Load when... |
|-------|-------|--------------|
| [`tad/00-overview.md`](tad/00-overview.md) | Doc meta, architecture overview, summary | Orientation |
| [`tad/01-component-architecture.md`](tad/01-component-architecture.md) | Frontend, sidecar, repo layout, build | Setting up new components, build changes |
| [`tad/02-data-model.md`](tad/02-data-model.md) | All Pydantic schemas, SQLite, codegen | Data model work, schema changes |
| [`tad/03-ipc-architecture.md`](tad/03-ipc-architecture.md) | JSON-RPC protocol, messages, errors | IPC-layer work |
| [`tad/04-pipelines.md`](tad/04-pipelines.md) | Every generation pipeline stage | Pipeline implementation |
| [`tad/05-ai-orchestration.md`](tad/05-ai-orchestration.md) | Model assignments, prompts, costs | AI-calling code |
| [`tad/06-archetype-handlers.md`](tad/06-archetype-handlers.md) | Archetype handler interface and handlers | Functional overlay work |
| [`tad/07-template-library.md`](tad/07-template-library.md) | Registry, storage, manifests, promotion | Template library work |
| [`tad/08-dbpf-packaging.md`](tad/08-dbpf-packaging.md) | DBPF library, TGI IDs, DDS, catalog entries | Packaging work |
| [`tad/09-tuning-clone.md`](tad/09-tuning-clone.md) | Tuning parsing, cloning, targeted edits | Tuning/functional work |
| [`tad/10-validation.md`](tad/10-validation.md) | Validation engine structure and checks | Validation work |
| [`tad/11-install.md`](tad/11-install.md) | Mods folder detection, install, conflicts | Install flow work |
| [`tad/12-admin-mode.md`](tad/12-admin-mode.md) | Admin mode gating, endpoints, UI | Admin mode work |
| [`tad/13-cross-platform.md`](tad/13-cross-platform.md) | Paths, encoding, Blender, subprocess | Cross-platform bugs |
| [`tad/14-errors-logging.md`](tad/14-errors-logging.md) | Error taxonomy, structured logging | Error handling, observability |
| [`tad/15-security.md`](tad/15-security.md) | Network, credentials, file access, privacy | Security-sensitive code |
| [`tad/16-testing-and-deployment.md`](tad/16-testing-and-deployment.md) | Testing architecture, deps, deployment, open questions | CI, build, test infrastructure |

### API Spec — IPC Contract
Every method, notification, and error across the frontend ↔ sidecar boundary.

| Shard | Scope | Load when... |
|-------|-------|--------------|
| [`api/00-overview.md`](api/00-overview.md) | Protocol basics, type conventions, common enums | IPC orientation |
| [`api/01-system.md`](api/01-system.md) | `system.*` methods | Implementing system methods |
| [`api/02-config.md`](api/02-config.md) | `config.*` methods | Implementing config methods |
| [`api/03-project.md`](api/03-project.md) | `project.*` methods | Implementing project methods |
| [`api/04-collection.md`](api/04-collection.md) | `collection.*` methods | Implementing collection methods |
| [`api/05-item.md`](api/05-item.md) | `item.*` methods | Implementing item methods |
| [`api/06-swatch.md`](api/06-swatch.md) | `swatch.*` methods | Implementing swatch methods |
| [`api/07-functional.md`](api/07-functional.md) | `functional.*` methods | Functional overlay IPC |
| [`api/08-validation.md`](api/08-validation.md) | `validation.*` methods | Validation IPC |
| [`api/09-export.md`](api/09-export.md) | `export.*` methods | Export IPC |
| [`api/10-verification.md`](api/10-verification.md) | `verification.*` methods | Verification IPC |
| [`api/11-templates.md`](api/11-templates.md) | `templates.*` methods | Template read IPC |
| [`api/12-admin.md`](api/12-admin.md) | `admin.*` methods | Admin mode IPC |
| [`api/13-notifications.md`](api/13-notifications.md) | All sidecar → frontend notifications | Progress, status events |
| [`api/14-error-codes.md`](api/14-error-codes.md) | Complete error code enum | Error handling |
| [`api/15-protocol-details.md`](api/15-protocol-details.md) | Concurrency, versioning, examples | Protocol-level work |

### Diagrams — Visual Reference
Mermaid diagrams for every major architectural concept.

| Shard | Scope | Load when... |
|-------|-------|--------------|
| [`diagrams/00-overview.md`](diagrams/00-overview.md) | Conventions, index, maintenance | Diagram orientation |
| [`diagrams/01-system-architecture.md`](diagrams/01-system-architecture.md) | Container, sidecar, frontend, deployment | Big picture |
| [`diagrams/02-data-architecture.md`](diagrams/02-data-architecture.md) | ER diagram, project folder | Data model work |
| [`diagrams/03-pipelines.md`](diagrams/03-pipelines.md) | 7 sequence diagrams for flows | Pipeline implementation |
| [`diagrams/04-state-machines.md`](diagrams/04-state-machines.md) | State transitions per entity | State-change code |
| [`diagrams/05-template-library.md`](diagrams/05-template-library.md) | Tier structure, promotion, resolution | Template work |
| [`diagrams/06-ai-orchestration.md`](diagrams/06-ai-orchestration.md) | AI stages overview, retry logic | AI code |
| [`diagrams/07-admin-mode.md`](diagrams/07-admin-mode.md) | Admin gating, operations | Admin work |
| [`diagrams/08-error-flow.md`](diagrams/08-error-flow.md) | Error propagation | Error handling |
| [`diagrams/09-phase-deps.md`](diagrams/09-phase-deps.md) | Phase sequence, Phase 3 task deps | Project sequencing |
| [`diagrams/10-cross-platform-security.md`](diagrams/10-cross-platform-security.md) | Paths, trust boundaries | Platform/security work |

---

## Regenerating the Monolithic Docs

When you need a consolidated document (for export, review, or sharing):

```bash
python docs/build_monolithic.py
```

This reads all shards and regenerates the five files under `docs/MONOLITHIC/`. Safe to run any time — it is a pure concatenation of shards in deterministic order.

## Re-Sharding

If for some reason the monoliths are edited directly and you need to re-shard (not a normal workflow):

```bash
python shard_docs.py
```

This overwrites the shards from the monoliths. Only run when intentionally resetting.

---

## Conventions for Editing Shards

1. Keep the shard's front-matter intact (the `> **Source:**` and description lines).
2. If a cross-reference to another shard is needed, use the path: `docs/tad/02-data-model.md §4.2` rather than just `TAD §4.2`.
3. If a shard grows significantly, consider splitting it — but update `docs/README.md` and `docs/CLAUDE.md` to match.
4. Do not edit files in `docs/MONOLITHIC/`. Those are derived.
