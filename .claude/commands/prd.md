---
description: Load a specific PRD shard. Pass a section keyword to load just that shard, not the full PRD.
argument-hint: [section e.g. users, goals, mvp, content, stories, fr, nonfunctional, acceptance]
allowed-tools: Read
---

Load the PRD shard for keyword `$ARGUMENTS`.

Mapping of keyword → shard file:

- `meta` or `document-meta` → `docs/prd/00-document-meta.md`
- `summary` or `product-summary` → `docs/prd/01-product-summary.md`
- `users` → `docs/prd/02-users.md`
- `goals` or `principles` → `docs/prd/03-goals-principles.md`
- `mvp` or `mvp-definition` → `docs/prd/04-mvp-definition.md`
- `content` or `style` → `docs/prd/05-content-and-style.md`
- `stories` or `user-stories` → `docs/prd/06-user-stories.md`
- `fr` or `requirements` → `docs/prd/07-functional-requirements.md`
- `nonfunctional` or `workflows` → `docs/prd/08-non-functional-and-workflows.md`
- `acceptance` or `guardrails` → `docs/prd/09-acceptance-and-guardrails.md`

If no argument is passed or the keyword is unrecognized, list the available shards and ask which one to load.

Never load the full PRD (all shards at once). If multiple PRD sections are needed, load them in sequence as the task demands.

To look up a specific FR, use `/fr {id}` instead — it's more targeted.
