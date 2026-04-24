#!/usr/bin/env bash
# SessionStart hook: inject project state context into Claude Code at session start.
#
# Provides current branch, most recent commits, current phase (from root CLAUDE.md),
# and uncommitted-change status so Claude Code knows where the project is at without
# having to grep for it.
#
# Output: JSON with additionalContext injected into the conversation.

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
cd "$PROJECT_DIR"

BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
RECENT=$(git log --oneline -5 2>/dev/null || echo "no commits yet")
DIRTY_COUNT=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')

# Extract current phase from root CLAUDE.md (looks for "Phase N: ..." in "Current Phase" section).
# Falls back to "unknown" if pattern not found.
PHASE=$(grep -A 1 "^## Current Phase" CLAUDE.md 2>/dev/null | tail -1 | grep -oE "Phase [0-9]+" | head -1 || echo "unknown")

CONTEXT=$(cat <<EOF
## Session Context

- Current branch: $BRANCH
- Current phase: $PHASE (per root CLAUDE.md)
- Uncommitted changes: $DIRTY_COUNT file(s)

Recent commits:
$RECENT
EOF
)

# Escape newlines and quotes for JSON
ESCAPED=$(echo "$CONTEXT" | jq -Rs .)

cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": $ESCAPED
  }
}
EOF

exit 0
