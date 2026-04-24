<!--
  AI Sims Creator PR Template

  Before opening this PR:
    - Run `/review-pr` in Claude Code, or
    - Run locally: ruff check, mypy, pytest, eslint, tsc --noEmit

  PR title format: [Phase {N}] Task {X.Y}: Short description
  Target branch: dev (never main directly)
-->

## Task

<!--
  Which task does this implement? Reference the task number from docs/mvp/.
  Example: "Task 0.5 — Project storage layer (docs/mvp/05-phase-0-foundation.md)"
-->

-

## Requirements Satisfied

<!--
  List FRs and ACs this PR satisfies. Use /fr {id} and /ac {id} in Claude Code
  to look them up if you're unsure.
-->

- FR-
- AC-
- MVP-AC-

## Scope

### In scope

<!-- What this PR does -->

-

### Out of scope (deferred)

<!-- Anything you noticed during implementation but chose not to bundle here. Link follow-up issues if filed. -->

-

## Testing

<!--
  - What was tested (unit / integration / manual)?
  - Coverage delta, if measured.
  - Any tests explicitly skipped (and why)?
  - Any manual verification performed (e.g., in-game check for functional objects)?
-->

- Unit tests: ✅ / ⚠️ / ❌
- Integration tests: ✅ / ⚠️ / ❌ / N/A
- Manual verification: <!-- describe if applicable -->

## Screenshots / Evidence

<!-- Required for UI changes. Optional but encouraged for pipeline output (e.g., example textures, thumbnails). -->

## Checklist

<!-- The hooks enforce most of this, but double-check: -->

- [ ] Branch name matches `phase-{N}/task-{X.Y}-{slug}`
- [ ] PR targets `dev`, not `main`
- [ ] `ruff check` passes (Python)
- [ ] `mypy` passes (Python strict mode)
- [ ] `pytest` passes (unit + integration for affected modules)
- [ ] `npm run lint` passes (TypeScript)
- [ ] `npx tsc --noEmit` passes (TypeScript strict)
- [ ] `npm test` passes (frontend)
- [ ] `shared-types/` is in sync with Pydantic schemas (run `python scripts/generate_types.py`)
- [ ] Conventional commit format used on commits
- [ ] No `.env`, secrets, or large binaries accidentally committed

## Notes for Reviewer

<!-- Anything the reviewer should pay special attention to, e.g., architectural tradeoffs, unusual patterns, dependency version changes. -->

-
