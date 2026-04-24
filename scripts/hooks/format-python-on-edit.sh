#!/usr/bin/env bash
# PostToolUse hook: format Python files with ruff after edits.
#
# Triggered on: Write, Edit, MultiEdit
# Runs when: a .py file under sidecar/ or scripts/ was just written or edited.
#
# Behavior: runs `ruff format` on the single file. Idempotent and fast (< 100ms typically).
# This keeps Python files formatted consistently without waiting for pre-commit.
#
# Exit code 0 regardless of outcome. Formatting is best-effort — if ruff isn't
# installed yet (early in Phase 0), this silently no-ops.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
if [[ "$FILE_PATH" == "$PROJECT_DIR/"* ]]; then
    REL_PATH="${FILE_PATH#"$PROJECT_DIR/"}"
else
    REL_PATH="$FILE_PATH"
fi

# Only fire on .py files in sidecar/ or scripts/
case "$REL_PATH" in
    sidecar/*.py|scripts/*.py)
        ;;
    *)
        exit 0
        ;;
esac

# Silent no-op if ruff isn't installed
if ! command -v ruff >/dev/null 2>&1; then
    exit 0
fi

# Format the single file. Ignore non-zero exit from ruff (formatter failure shouldn't
# block Claude Code's forward progress).
ruff format "$FILE_PATH" >/dev/null 2>&1 || true

exit 0
