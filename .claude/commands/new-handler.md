---
description: Scaffold a new IPC handler following project conventions. Creates the handler function, Pydantic param/result schemas, and a stub test file.
argument-hint: [namespace.method_name e.g. project.rename]
allowed-tools: Read, Grep, Glob, Write, Edit, Bash
---

Scaffold a new IPC handler for `$ARGUMENTS`.

Follow these steps:

1. Parse the argument as `{namespace}.{method}`. If it doesn't split on a dot, ask for clarification.
2. Read `docs/api/{namespace}.md` to check whether this method is already specified. If yes, use the existing spec. If no, ask whether to proceed with a new method spec.
3. Read `sidecar/CLAUDE.md` for the handler pattern.
4. Read `sidecar/aisc/ipc/handlers/{namespace}.py` if it exists, or create it.
5. Add the handler function with the naming convention `{namespace}_{method}` (replacing dots with underscores).
6. Add the Pydantic param and result schemas to `sidecar/aisc/schemas/{namespace}.py`.
7. Register the handler in the IPC dispatcher (`sidecar/aisc/ipc/server.py` or equivalent).
8. Create a stub test file under `sidecar/tests/ipc/handlers/test_{namespace}.py` with a happy-path test and a not-found test skeleton.
9. Run `python scripts/generate_types.py` to regenerate TypeScript types.
10. Report what was created.

Do not implement the full handler body yet — that's the implementation task after scaffolding. Leave a `# TODO: implement` comment in the handler body.

If the API namespace doc doesn't have a spec for this method and the user didn't confirm proceeding anyway, stop and ask.
