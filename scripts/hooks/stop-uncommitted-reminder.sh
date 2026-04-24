#!/usr/bin/env bash
# Stop hook: after Claude Code finishes responding, check for uncommitted changes.
#
# If there are uncommitted changes, inject a reminder into the conversation so
# the next user prompt has the info. This is a gentle nudge, not a block — some
# sessions end intentionally with a work-in-progress state.
#
# Critical: must check stop_hook_active to avoid infinite loops.

set -euo pipefail

INPUT=$(cat)

# Guard: if Stop hook is already firing, don't re-trigger (prevents infinite loops).
STOP_ACTIVE=$(echo "$INPUT" | jq -r '.stop_hook_active // false')
if [[ "$STOP_ACTIVE" == "true" ]]; then
    exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

DIRTY_COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

if [[ "$DIRTY_COUNT" == "0" ]]; then
    # Clean working tree. Nothing to remind about.
    exit 0
fi

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Check if we're on a feature branch (expected) or something unexpected
case "$BRANCH" in
    phase-*/task-*)
        # Expected. Silent - don't be naggy during normal development.
        exit 0
        ;;
    main|master|dev|develop)
        # Uncommitted changes on a protected branch = worth flagging.
        cat <<EOF
{
  "decision": "block",
  "reason": "You have $DIRTY_COUNT uncommitted change(s) on branch '$BRANCH', which is a protected branch. Before continuing, either (a) stash and switch to a feature branch with 'git checkout -b phase-{N}/task-{X.Y}-{slug}' and apply the stash, or (b) clarify with the user whether this work belongs on the protected branch."
}
EOF
        exit 0
        ;;
    *)
        # Other branch. Advisory reminder only.
        exit 0
        ;;
esac
