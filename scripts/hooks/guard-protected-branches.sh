#!/usr/bin/env bash
# PreToolUse hook: block direct pushes/commits to protected branches.
#
# Triggered on: Bash
# Blocks when:
#   - Currently on main or dev branch AND the command is a git commit, git push, or git merge
#   - OR command is "git push * main" or "git push * dev" (force-target a protected branch)
#
# Exit code 2 = block the action.
# Exit code 0 = allow.

set -euo pipefail

INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [[ -z "$COMMAND" ]]; then
    exit 0
fi

# Check if we're on a protected branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

is_protected_branch() {
    case "$1" in
        main|master|dev|develop) return 0 ;;
        *) return 1 ;;
    esac
}

# Pattern: git commit, git push, git merge while on a protected branch
if is_protected_branch "$CURRENT_BRANCH"; then
    case "$COMMAND" in
        *"git commit"*|*"git push"*|*"git merge"*)
            echo "BLOCKED: you are on branch '$CURRENT_BRANCH' which is protected." >&2
            echo "Create a feature branch first:" >&2
            echo "  git checkout -b phase-{N}/task-{X.Y}-{slug}" >&2
            exit 2
            ;;
    esac
fi

# Pattern: git push * main or git push * dev (pushing FROM anywhere TO a protected branch)
# Matches 'git push origin main', 'git push upstream dev:main', etc.
if echo "$COMMAND" | grep -qE 'git push[[:space:]]+[^[:space:]]+[[:space:]]+(main|master|dev|develop)([[:space:]]|$|:)'; then
    echo "BLOCKED: direct push to a protected branch." >&2
    echo "Open a pull request targeting 'dev' instead. Use /open-pr or 'gh pr create --base dev'." >&2
    exit 2
fi

# Pattern: git push --force or -f
if echo "$COMMAND" | grep -qE 'git push[[:space:]].*(--force|--force-with-lease|-f[[:space:]]|-f$)'; then
    echo "BLOCKED: force-push detected." >&2
    echo "This project does not allow force-pushes. If you need to rewrite history, do it locally and discuss with the maintainer." >&2
    exit 2
fi

exit 0
