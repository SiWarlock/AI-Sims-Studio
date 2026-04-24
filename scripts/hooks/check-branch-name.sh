#!/usr/bin/env bash
# Git pre-push hook: verify the current branch name matches the project convention.
#
# Valid patterns:
#   phase-{N}/task-{X.Y}-{slug}       # feature work (normal case)
#   phase-{N}/spike-{slug}            # research/investigation branches
#   phase-{N}/fix-{slug}              # bug fix branches within a phase
#   hotfix/{slug}                     # emergency fixes off main
#   release/{version}                 # release prep branches
#
# main and dev are protected — direct pushes are blocked by separate mechanism,
# this script just verifies feature branches look right.
#
# Exit 0 = valid, allow push.
# Exit non-zero = invalid, block push.

set -euo pipefail

BRANCH=$(git branch --show-current 2>/dev/null || echo "")

if [[ -z "$BRANCH" ]]; then
    # Detached HEAD or other unusual state. Let it proceed — push will fail naturally.
    exit 0
fi

# Protected branches: never push directly. Blocked elsewhere, also catch here.
case "$BRANCH" in
    main|master|dev|develop)
        echo "ERROR: cannot push directly to protected branch '$BRANCH'." >&2
        echo "Create a feature branch: git checkout -b phase-{N}/task-{X.Y}-{slug}" >&2
        exit 1
        ;;
esac

# Valid feature branch patterns
VALID_PATTERNS=(
    '^phase-[0-9]+/task-[0-9]+\.[0-9]+-[a-z0-9-]+$'
    '^phase-[0-9]+/spike-[a-z0-9-]+$'
    '^phase-[0-9]+/fix-[a-z0-9-]+$'
    '^hotfix/[a-z0-9-]+$'
    '^release/v[0-9]+\.[0-9]+\.[0-9]+$'
)

for pattern in "${VALID_PATTERNS[@]}"; do
    if echo "$BRANCH" | grep -qE "$pattern"; then
        exit 0
    fi
done

echo "ERROR: branch name '$BRANCH' does not match any allowed pattern." >&2
echo "" >&2
echo "Allowed patterns:" >&2
echo "  phase-{N}/task-{X.Y}-{slug}   (most common — a numbered task in a phase)" >&2
echo "  phase-{N}/spike-{slug}        (research/investigation)" >&2
echo "  phase-{N}/fix-{slug}          (bug fix within a phase)" >&2
echo "  hotfix/{slug}                 (emergency fix off main)" >&2
echo "  release/v{X.Y.Z}              (release prep)" >&2
echo "" >&2
echo "Examples:" >&2
echo "  phase-0/task-0.5-project-storage-layer" >&2
echo "  phase-3/task-3.4-texture-generation-pipeline" >&2
echo "  phase-1/spike-image-model-comparison" >&2
exit 1
