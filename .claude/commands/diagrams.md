---
description: Load a specific architecture diagrams shard. Each contains Mermaid diagrams for one architectural area.
argument-hint: [section e.g. system, data, pipelines, state, templates]
allowed-tools: Read
---

Load the architecture diagrams shard for keyword `$ARGUMENTS`.

Mapping of keyword → shard file:

- `overview` → `docs/diagrams/00-overview.md`
- `system` or `system-architecture` → `docs/diagrams/01-system-architecture.md`
- `data` or `data-architecture` → `docs/diagrams/02-data-architecture.md`
- `pipelines` → `docs/diagrams/03-pipelines.md`
- `state` or `state-machines` → `docs/diagrams/04-state-machines.md`
- `templates` or `template-library` → `docs/diagrams/05-template-library.md`
- `ai` or `ai-orchestration` → `docs/diagrams/06-ai-orchestration.md`
- `admin` or `admin-mode` → `docs/diagrams/07-admin-mode.md`
- `error` or `error-flow` → `docs/diagrams/08-error-flow.md`
- `phases` or `phase-deps` → `docs/diagrams/09-phase-deps.md`
- `cross-platform` or `security` → `docs/diagrams/10-cross-platform-security.md`

If no argument is passed, list the available shards.

Never load all diagrams at once.
