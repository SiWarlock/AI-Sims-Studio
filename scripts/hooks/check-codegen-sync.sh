#!/usr/bin/env bash
# Git pre-commit hook: block commits where Pydantic schemas changed but TypeScript
# types in shared-types/ are stale.
#
# This is the mechanism that prevents type drift between the sidecar and the frontend.
#
# Strategy:
#   1. Run the codegen into a temp directory.
#   2. Diff it against the current shared-types/ content.
#   3. If they differ, the developer changed a schema without regenerating types.
#      Block the commit and tell them to run `python scripts/generate_types.py`.
#
# Exit code 0 = in sync, allow commit.
# Exit code non-zero = out of sync, block commit.

set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel)}"
cd "$PROJECT_DIR"

TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT

# Run codegen into the temp directory.
# The codegen script must accept --output to redirect its output; we document this
# as a contract of the codegen script.
if ! python scripts/generate_types.py --output "$TMPDIR" > /tmp/aisc-codegen-check.log 2>&1; then
    echo "ERROR: codegen script failed. Output:" >&2
    cat /tmp/aisc-codegen-check.log >&2
    exit 1
fi

# Diff the temp output against the current shared-types/
if ! diff -r shared-types "$TMPDIR" > /tmp/aisc-codegen-diff.log 2>&1; then
    echo "ERROR: shared-types/ is out of sync with current Pydantic schemas." >&2
    echo "" >&2
    echo "Differences:" >&2
    cat /tmp/aisc-codegen-diff.log >&2
    echo "" >&2
    echo "To fix:" >&2
    echo "  1. Run: python scripts/generate_types.py" >&2
    echo "  2. Stage the updated files in shared-types/" >&2
    echo "  3. Commit again" >&2
    exit 1
fi

exit 0
