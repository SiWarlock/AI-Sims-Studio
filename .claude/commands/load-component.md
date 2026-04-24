---
description: Load a specific TAD component shard covering one architectural area.
argument-hint: [component name e.g. data-model, pipelines, dbpf, archetypes, templates]
allowed-tools: Read
---

Load the TAD shard for component `$ARGUMENTS`.

Mapping of component keyword → shard file:

- `overview` → `docs/tad/00-overview.md`
- `components` or `component-architecture` → `docs/tad/01-component-architecture.md`
- `data-model` or `schemas` → `docs/tad/02-data-model.md`
- `ipc` → `docs/tad/03-ipc-architecture.md`
- `pipelines` → `docs/tad/04-pipelines.md`
- `ai` or `ai-orchestration` → `docs/tad/05-ai-orchestration.md`
- `archetypes` → `docs/tad/06-archetype-handlers.md`
- `templates` or `template-library` → `docs/tad/07-template-library.md`
- `dbpf` or `packaging` → `docs/tad/08-dbpf-packaging.md`
- `tuning` → `docs/tad/09-tuning-clone.md`
- `validation` → `docs/tad/10-validation.md`
- `install` → `docs/tad/11-install.md`
- `admin` or `admin-mode` → `docs/tad/12-admin-mode.md`
- `cross-platform` → `docs/tad/13-cross-platform.md`
- `errors` or `logging` → `docs/tad/14-errors-logging.md`
- `security` → `docs/tad/15-security.md`
- `testing` or `deployment` → `docs/tad/16-testing-and-deployment.md`

If the requested keyword isn't in this list, ask for clarification. Never load all TAD shards at once.

After loading, summarize what the component covers. Do not load other components unless explicitly asked.
