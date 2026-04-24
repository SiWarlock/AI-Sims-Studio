---
description: Load the MVP Spec task file for a specific phase so you have the full task list and acceptance gate in context.
argument-hint: [phase-number, 0 through 7]
allowed-tools: Read
---

Load `docs/mvp/0{N+5}-phase-{N}-{slug}.md` where `{N}` is $ARGUMENTS.

The mapping of phase numbers to shard files:

- Phase 0 → `docs/mvp/05-phase-0-foundation.md`
- Phase 1 → `docs/mvp/06-phase-1-poc.md`
- Phase 2 → `docs/mvp/07-phase-2-templates.md`
- Phase 3 → `docs/mvp/08-phase-3-decorative.md`
- Phase 4 → `docs/mvp/09-phase-4-validation-export.md`
- Phase 5 → `docs/mvp/10-phase-5-functional.md`
- Phase 6 → `docs/mvp/11-phase-6-admin.md`
- Phase 7 → `docs/mvp/12-phase-7-polish.md`

After loading, summarize the phase's goal, its acceptance gate, and the task count. Do not load any other phase file — only the one requested.
