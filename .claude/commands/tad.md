---
description: Load a specific TAD shard. Pass a section keyword to load just that shard, not the full TAD.
argument-hint: [section e.g. data-model, pipelines, dbpf, archetypes]
allowed-tools: Read
---

Load the TAD shard for keyword `$ARGUMENTS`.

This is the same mapping as `/load-component` — kept as a separate alias for users who think in terms of "load a TAD section" vs "load a specific architectural component." Behavior is identical.

Mapping of keyword → shard file:

- `overview` → `docs/tad/00-overview.md`
- `components` → `docs/tad/01-component-architecture.md`
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
- `admin` → `docs/tad/12-admin-mode.md`
- `cross-platform` → `docs/tad/13-cross-platform.md`
- `errors` or `logging` → `docs/tad/14-errors-logging.md`
- `security` → `docs/tad/15-security.md`
- `testing` or `deployment` → `docs/tad/16-testing-and-deployment.md`

If no argument is passed, list the available shards and ask which one to load.

Never load the full TAD (all shards at once).
