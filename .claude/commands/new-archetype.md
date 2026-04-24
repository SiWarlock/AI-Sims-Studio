---
description: Scaffold a new archetype handler following the handler protocol. Use only when explicitly expanding beyond the four MVP archetypes — new archetypes are post-MVP scope by default.
argument-hint: [archetype-id e.g. stove]
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

Scaffold a new archetype handler with ID `$ARGUMENTS`.

**Stop and confirm first:** the four MVP archetypes are `light_on_off`, `audio_device`, `mirror`, `moodlet_emitter`. Adding a new archetype is post-MVP scope unless Phase 5 has been explicitly extended. Confirm the user wants to proceed.

After confirmation:

1. Read `sidecar/aisc/archetypes/CLAUDE.md` for handler conventions.
2. Read `docs/tad/06-archetype-handlers.md` for the handler protocol.
3. Create `sidecar/aisc/archetypes/{$ARGUMENTS}.py` with:
   - The `{ArchetypeIdPascalCase}Config` Pydantic configuration class (frozen, extra=forbid)
   - The `{ArchetypeIdPascalCase}Handler` class implementing `ArchetypeHandlerBase`
   - A module-level docstring listing which tuning fields this archetype is allowed to edit
4. Add the new `ArchetypeId` enum value to `sidecar/aisc/schemas/base.py`.
5. Register the handler in `sidecar/aisc/archetypes/registry.py`.
6. Create a stub test file at `sidecar/tests/archetypes/test_{$ARGUMENTS}.py`.
7. Note the reference object criteria (exact base-game TGI ID will be resolved during implementation — don't hardcode).
8. Run `python scripts/generate_types.py` to regenerate TypeScript types for the new ArchetypeId enum value.
9. Report what was created and what needs to be filled in during implementation (reference object, configuration schema details, build_overlay body, tests).

Leave `# TODO: implement` comments in all method bodies. This command scaffolds; implementation is a separate task via the `archetype-handler` agent.
