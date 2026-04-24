---
description: Load a specific API namespace spec shard so you have the full method specs in context for that namespace only.
argument-hint: [namespace e.g. project, collection, functional, admin]
allowed-tools: Read
---

Load the API spec shard for namespace `$ARGUMENTS`.

Mapping of namespace → shard file:

- `system` → `docs/api/01-system.md`
- `config` → `docs/api/02-config.md`
- `project` → `docs/api/03-project.md`
- `collection` → `docs/api/04-collection.md`
- `item` → `docs/api/05-item.md`
- `swatch` → `docs/api/06-swatch.md`
- `functional` → `docs/api/07-functional.md`
- `validation` → `docs/api/08-validation.md`
- `export` → `docs/api/09-export.md`
- `verification` → `docs/api/10-verification.md`
- `templates` → `docs/api/11-templates.md`
- `admin` → `docs/api/12-admin.md`
- `notifications` → `docs/api/13-notifications.md`
- `errors` → `docs/api/14-error-codes.md`

If the requested namespace isn't in this list, check if the user meant a different one or if it's a new namespace being added.

After loading, summarize: the namespace's purpose, method count, and any admin-only gating. Do not load other namespaces unless explicitly asked.
