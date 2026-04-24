---
description: Push the current feature branch and open a pull request into the dev branch. Runs /review-pr first to confirm readiness; refuses to proceed if the review fails.
allowed-tools: Bash, Read
---

Push the current branch and open a PR into `dev`.

Steps in order:

1. **Run `/review-pr` first.** If any check fails, stop and report the failures. Do not push or open a PR against failing checks.
2. **Verify branch name format.** `!git branch --show-current` should match `phase-{N}/task-{X.Y}-{slug}`. Stop if not.
3. **Confirm current branch is not `main` or `dev`.** Never push those directly.
4. **Push the branch:** `!git push -u origin $(git branch --show-current)`
5. **Open the PR using the `gh` CLI:** `!gh pr create --base dev --title "<title>" --body "<body>" --draft=false`
   - Title format: `[Phase {N}] Task {X.Y}: Short description`
   - Body: use the PR description draft produced by `/review-pr`
6. **Report the PR URL.**

If `gh` is not installed or not authenticated, stop and instruct the user how to install/authenticate, then let them open the PR manually with the draft body.

If the branch has unpushed changes that conflict with the remote, report the conflict without force-pushing. The user resolves manually.
