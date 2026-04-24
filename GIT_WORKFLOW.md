# AI Sims Creator — Git Workflow

This document is the authoritative reference for branching, commits, PRs, and releases on this project. `CODING_STANDARDS.md` links here for anything git-related.

## TL;DR

- Feature branches → PR to `dev` → squash-merge
- `main` ← periodic promotion from `dev` at phase-complete milestones
- Branch names: `phase-{N}/task-{X.Y}-{slug}`
- Commits: Conventional Commits
- Pre-commit + pre-push git hooks enforce everything below
- Never `git push --force`, never push directly to `main` or `dev`

## Branch Topology

```
main ──────●─────────────────●───────────────●──────►   (release-ready)
            ╲                 ╲               ╲
             ╲─── promote ─────╲── promote ────╲── promote
              ╲                 ╲               ╲
dev  ●────●────●────●────●────●────●────●────●────────►  (integration)
     │    │         │    │         │    │
     └feat└fix      └feat└refactor └feat└feat  (feature branches, PR'd into dev)
```

## Branch Naming

### Required patterns

| Pattern | Use for | Example |
|---|---|---|
| `phase-{N}/task-{X.Y}-{slug}` | Normal feature work tied to a phase task | `phase-3/task-3.4-texture-generation-pipeline` |
| `phase-{N}/spike-{slug}` | Research or investigation, typically resolves a deferred decision | `phase-1/spike-image-model-comparison` |
| `phase-{N}/fix-{slug}` | Bug fix within a phase | `phase-3/fix-swatch-regen-race-condition` |
| `hotfix/{slug}` | Emergency fix off `main` | `hotfix/corrupt-package-on-missing-sims-install` |
| `release/v{X.Y.Z}` | Release preparation branches | `release/v1.0.0` |

### Protected branches

- `main` — release-ready. Receives promotions from `dev`. No direct pushes. No direct PRs from feature branches.
- `dev` — integration. All feature branches PR here. No direct pushes.

The pre-push git hook (`scripts/hooks/check-branch-name.sh`) enforces these patterns. Attempts to push to a non-matching branch name are blocked.

### Slug conventions

- Lowercase
- Hyphens, not underscores
- No special characters
- Descriptive but brief — 3-6 words
- Matches the task description when there is one

## Commits

### Conventional Commits

Format: `type(scope): description (optional-ref)`

**Valid types:**
- `feat` — new feature
- `fix` — bug fix
- `refactor` — restructuring without behavior change
- `docs` — documentation only
- `test` — tests only
- `chore` — maintenance, deps, build config
- `build` — build system changes
- `ci` — CI configuration changes
- `perf` — performance improvements
- `style` — formatting only (rare — usually handled by the auto-formatter)

**Scope** — the module or feature area. Examples:
- `storage`, `ipc`, `texture_gen`, `planning`, `packaging`
- `frontend/collection-board`, `frontend/store`
- `archetypes/light`, `archetypes/mirror`
- `docs/prd`, `docs/tad`
- `ci`, `deps`, `infra`

**Description** — imperative present tense, lowercase, no period at end.

**Ref** — reference an FR, AC, or task where relevant.

### Examples

Good:
```
feat(storage): implement project CRUD operations (FR-001, FR-002)
fix(texture_gen): retry on Replicate timeout, max 3 attempts (FR-034)
refactor(packaging): extract DDS encoding into dedicated module
docs(tad): clarify archetype handler protocol vs base class
test(archetypes/light): cover edge cases for always_on configuration
chore(deps): bump pydantic to 2.8.0
```

Bad (and why):
```
Update code                           → no type, no scope, vague
feat: Add thing                       → no scope, doesn't say what
fixed bug                             → wrong tense, no type, no scope
feat(everything): big refactor        → scope too broad, mixed intent
```

### Commit discipline

- **One logical change per commit.** Use `git add -p` to stage selectively.
- **Every commit compiles.** Working state at every point in history. Use `git rebase -i` to clean up before pushing.
- **Reference shards, not monoliths.** `per docs/tad/04-pipelines.md §6.2`, not `per TAD §6.2`.
- **No WIP commits in PRs.** Squash-merge handles this at PR level, but keep local history clean anyway.
- **Typical commit size:** 50-300 lines. Over 500 lines = consider splitting.

### Commit message format enforcement

The `conventional-pre-commit` hook runs on the `commit-msg` stage and rejects messages that don't match the format. If a commit is rejected, fix the message and retry.

## Pull Requests

### Opening a PR

1. Ensure you're on a feature branch (not `main` or `dev`).
2. Run `/review-pr` in Claude Code — this executes lint, type check, tests, and codegen sync check.
3. If all checks pass, run `/open-pr` — this pushes the branch and opens the PR via `gh pr create --base dev`.
4. Alternatively do it manually: `git push -u origin <branch>`, then `gh pr create --base dev --title "..." --body "..."`.

### PR title

Format: `[Phase {N}] Task {X.Y}: Short description`

Examples:
- `[Phase 0] Task 0.5: Project storage layer`
- `[Phase 3] Task 3.4: Texture generation pipeline`
- `[Phase 5] Task 5.2: Light on/off archetype handler`

For branches that aren't tied to a specific task (spikes, fixes), use a descriptive title:
- `[Phase 1] Spike: Image model comparison for D-2 resolution`
- `[Phase 3] Fix: Swatch regeneration race condition`

### PR description

Use `.github/pull_request_template.md` — it's auto-loaded by GitHub. Required sections:

1. **Task** — what this implements
2. **Requirements Satisfied** — FRs, ACs, MVP-ACs
3. **Scope** — what's in, what's deferred
4. **Testing** — what was tested, coverage delta, manual verification if any
5. **Screenshots / Evidence** — for UI changes; optional but encouraged for pipeline output
6. **Checklist** — the verification items the hooks enforce
7. **Notes for Reviewer** — anything needing special attention

### PR size

- Target: 50-400 lines of diff.
- Over 800 lines: consider splitting unless there's a structural reason (initial scaffolding, generated code, large schema additions).
- Claude Code agents are configured to flag when a PR grows beyond this.

### PR target

- Always `dev`. Never `main`.
- The pre-push hook checks this. Manually targeting `main` via `gh pr create --base main` is allowed only by the maintainer for promotion PRs.

### Review

- **Self-review:** run `/review-pr` before opening. Fix everything the hook checks surface.
- **Human review:** required for every PR into `dev` or `main`.
- **Review turnaround:** aim for same-day on small PRs, next-day on larger.
- **Reviewers run through the PR checklist** and verify claims made in the description.

### Merge strategy

- **Squash-merge into `dev`.** The PR title becomes the squash commit message.
- **No merge commits in `dev`.** Linear history.
- **Never rebase-merge.** Squash only — preserves a clean phase task history.

## Promotions to `main`

Periodic, at phase-complete milestones. The maintainer creates a promotion PR manually:

1. Open a PR from `dev` to `main` with title `Promote: Phase {N} complete → v{X.Y.Z}`.
2. Body lists: phase name, completed tasks, satisfied FRs/ACs, any known issues carrying forward.
3. Squash-merge.
4. Tag the merge commit: `git tag v{X.Y.Z}` and `git push --tags`.
5. The next feature branch cycle resumes off `dev`.

## Git Hooks Setup

First-time setup (done once after cloning the repo):

```bash
pip install pre-commit
pre-commit install                    # pre-commit stage (per file on commit)
pre-commit install --hook-type pre-push      # pre-push stage (full suite before push)
pre-commit install --hook-type commit-msg    # commit-msg stage (conventional commits)
```

After this, hooks run automatically on `git commit` and `git push`. See `.pre-commit-config.yaml` for the exact rules.

### What runs when

| Trigger | Hook | What it does | Blocks on failure |
|---|---|---|---|
| `git commit` | Trailing whitespace, EOF newline | Fix automatically | No (auto-fixes, re-stage) |
| `git commit` | `ruff check --fix` | Lint Python, auto-fix | No (auto-fixes) |
| `git commit` | `ruff format` | Format Python | No (auto-fixes) |
| `git commit` | `mypy --strict` | Type check Python | **Yes** |
| `git commit` | `eslint` | Lint TS | **Yes** |
| `git commit` | `tsc --noEmit` | Type check TS | **Yes** |
| `git commit` | Codegen sync check | Verify TS types match Pydantic | **Yes** |
| `git commit --amend`, every commit | Conventional Commits check | Verify message format | **Yes** |
| `git push` | Branch name check | Verify branch pattern | **Yes** |
| `git push` | Full pytest suite | Run Python unit + integration | **Yes** |
| `git push` | Full vitest suite | Run TS tests | **Yes** |

### Bypassing hooks

Never bypass hooks with `--no-verify`. If a hook is wrong, fix the hook (separate PR) rather than skip it. The one exception is emergency hotfixes where the maintainer has documented a specific bypass rationale in the PR description.

## Claude Code Hooks vs Git Hooks

These are two separate systems:

- **Claude Code hooks** (`.claude/settings.json` + `scripts/hooks/`) fire during Claude Code's agentic loop. They guide Claude Code's behavior — blocking dangerous edits, auto-regenerating types, injecting session context. See `.claude/settings.json` for configuration.

- **Git hooks** (`.pre-commit-config.yaml`) fire during git operations. They enforce repo invariants regardless of who or what is committing — Claude Code, a human, or CI.

Both exist because neither covers the other's scope. Claude Code hooks can't prevent a human from committing broken code directly. Git hooks can't prevent Claude Code from writing bad code in the first place — they only fire on commit, too late to guide composition.

The belt-and-suspenders pattern is intentional.

## Common Commands

```bash
# Start a new feature task
git checkout dev
git pull
git checkout -b phase-3/task-3.4-texture-generation-pipeline

# Commit work
git add -p
git commit -m "feat(texture_gen): implement per-zone prompt generation (FR-028)"

# Push and open PR
git push -u origin HEAD
gh pr create --base dev

# After PR is merged, clean up
git checkout dev
git pull
git branch -d phase-3/task-3.4-texture-generation-pipeline
git push origin --delete phase-3/task-3.4-texture-generation-pipeline  # if the GH auto-delete is off
```

Or with Claude Code:

```
# In Claude Code:
/load-phase 3                         # load the phase 3 task list
# ... work on task 3.4 ...
/review-pr                            # self-review
/open-pr                              # push + open PR
```

## Questions

If a workflow question comes up that isn't covered here, update this document in the same PR that answers it. This file is the source of truth for git workflow; keeping it current makes the rules clear to humans and to Claude Code alike.
