---
description: Load a specific MVP Spec shard. For phase task files, prefer /load-phase {N} — it has the exact mapping.
argument-hint: [section e.g. overview, templates, archetypes, deferrals, acceptance, testing]
allowed-tools: Read
---

Load the MVP Spec shard for keyword `$ARGUMENTS`.

Mapping of keyword → shard file:

- `overview` → `docs/mvp/00-overview.md`
- `phases` or `phase-overview` → `docs/mvp/01-phase-overview.md`
- `templates` or `template-roster` → `docs/mvp/02-template-roster.md`
- `archetypes` or `archetype-mapping` → `docs/mvp/03-archetype-mapping.md`
- `deferrals` or `deferred` → `docs/mvp/04-deferred-decisions.md`
- `acceptance` or `ac` → `docs/mvp/13-acceptance-criteria.md`
- `testing` → `docs/mvp/14-testing-strategy.md`
- `supporting` or `risks` or `success` → `docs/mvp/15-supporting.md`
- For phase N (0-7), use `/load-phase {N}` instead — it routes directly to the correct file.

If no argument is passed, list the available shards and ask which one to load.

Never load the full MVP Spec (all shards at once).
