---
description: Run a pre-commit self-review on the current branch before opening a PR. Executes lint, type check, tests, and codegen sync, then summarizes readiness.
allowed-tools: Bash, Read, Grep
---

Run a pre-commit self-review of the current branch. This is what you run before opening a PR to make sure nothing obvious will block review.

Execute in order:

1. **Confirm branch format:** Run `!git branch --show-current`. The branch should match `phase-{N}/task-{X.Y}-{slug}`. If not, flag it.
2. **Confirm target branch:** This branch should be PR-ing into `dev`, never `main`. Note this for the PR description.
3. **Run Python linting:** `!cd sidecar && ruff check`
4. **Run Python formatting check:** `!cd sidecar && ruff format --check`
5. **Run Python type check:** `!cd sidecar && mypy .`
6. **Run Python tests:** `!cd sidecar && pytest -q`
7. **Run TypeScript linting:** `!cd frontend && npm run lint`
8. **Run TypeScript type check:** `!cd frontend && npx tsc --noEmit`
9. **Run TypeScript tests:** `!cd frontend && npm test -- --run`
10. **Verify codegen sync:** `!python scripts/generate_types.py` then `!git status shared-types/` — if there are uncommitted changes in `shared-types/`, types drifted.
11. **Summarize the diff:** `!git diff --stat dev..HEAD`
12. **Check for conventional commit format** in the branch's commit messages.

After all checks:

- **If everything passes:** produce a PR description draft following the template in `CODING_STANDARDS.md` (§"PR description"). Include what task this implements, FRs/ACs satisfied, testing notes.
- **If anything fails:** list the failures in order, with suggested next actions per failure.

Do not open the PR. Just verify readiness and produce the PR description draft.
