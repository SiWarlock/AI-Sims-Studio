---
description: Verify the current code against a specific acceptance criterion. Loads the AC from the appropriate shard and checks whether the implementation satisfies it.
argument-hint: [AC-id e.g. AC-007 or MVP-AC-012]
allowed-tools: Read, Grep, Glob, Bash
---

Verify the codebase satisfies acceptance criterion `$ARGUMENTS`.

1. Determine the source:
   - If the ID starts with `MVP-AC-`, load `docs/mvp/13-acceptance-criteria.md`
   - If the ID starts with `AC-` (no `MVP-` prefix), load `docs/prd/09-acceptance-and-guardrails.md`
   - Otherwise, ask which AC list the user means.
2. Find the specific criterion and read its exact wording.
3. Identify what code path would satisfy the criterion. Use `grep` / `Grep` to locate it.
4. Verify:
   - The code exists
   - Tests cover the relevant behavior
   - The tests currently pass (run the relevant test subset)
   - Any dependent data model / schema / IPC method is in place
5. Report back:
   - AC wording
   - Verdict: satisfied / partially satisfied / not satisfied / untestable-yet
   - Evidence (files, tests, behaviors verified)
   - Gaps (if any)
   - Suggested next action (if the AC isn't fully satisfied)

Do not implement missing functionality. This command only verifies.
