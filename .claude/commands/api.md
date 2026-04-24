---
description: Load a specific API namespace spec shard. Alias for /load-api with identical behavior.
argument-hint: [namespace e.g. project, collection, functional, admin]
allowed-tools: Read
---

Load the API spec shard for namespace `$ARGUMENTS`.

This is the same behavior as `/load-api` — kept as a separate alias for consistency with `/prd`, `/tad`, `/mvp`, `/diagrams`.

Mapping of namespace → shard file:

- `overview` → `docs/api/00-overview.md`
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
- `errors` or `error-codes` → `docs/api/14-error-codes.md`
- `protocol` → `docs/api/15-protocol-details.md`

If no argument is passed, list the available namespaces.

Never load the full API spec (all namespaces at once).
