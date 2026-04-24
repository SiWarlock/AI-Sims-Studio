#!/usr/bin/env bash
# PostToolUse hook: auto-regenerate TypeScript types when Pydantic schemas change.
#
# Triggered on: Write, Edit, MultiEdit
# Runs when: a file under sidecar/aisc/schemas/ was just written or edited.
#
# Behavior: runs scripts/generate_types.py quietly. If it fails, reports the error
# to Claude via additionalContext but does NOT block (type regeneration failure is
# a signal to investigate, not a reason to undo the schema edit).
#
# Exit code 0 with additionalContext JSON = success, optional message injected.
# Exit code 0 with no output = success, silent.

set -euo pipefail

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // empty')

if [[ -z "$FILE_PATH" ]]; then
    exit 0
fi

# Normalize to a relative path
PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(pwd)}"
if [[ "$FILE_PATH" == "$PROJECT_DIR/"* ]]; then
    REL_PATH="${FILE_PATH#"$PROJECT_DIR/"}"
else
    REL_PATH="$FILE_PATH"
fi

# Only fire on schema changes
case "$REL_PATH" in
    sidecar/aisc/schemas/*.py)
        ;;
    *)
        exit 0
        ;;
esac

# Regenerate types
cd "$PROJECT_DIR"
if python scripts/generate_types.py > /tmp/aisc-codegen.log 2>&1; then
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "TypeScript types regenerated from Pydantic schema change in $REL_PATH. Verify the generated shared-types/ output matches expectations, and stage the updated files."
  }
}
EOF
else
    ERR=$(cat /tmp/aisc-codegen.log)
    cat <<EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "WARNING: TypeScript codegen failed after schema change in $REL_PATH. Error output: $ERR. Fix the schema or codegen script before committing — the pre-commit git hook will block commits with stale types."
  }
}
EOF
fi

exit 0
