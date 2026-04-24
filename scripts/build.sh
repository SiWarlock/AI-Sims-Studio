#!/usr/bin/env bash
# macOS release build for AI Sims Creator.
#
# Orchestrates the full build:
#   1. Regenerate shared-types/ from Pydantic schemas
#   2. Install frontend deps
#   3. Build via Tauri (produces a .app / .dmg in frontend/src-tauri/target/)
#
# The Python sidecar bundling step (PyOxidizer or PyInstaller — choice deferred
# to Phase 0) is intentionally not wired here yet. It will be added once the
# sidecar has actual functionality to bundle.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "==> [1/3] Regenerating shared-types/"
python scripts/generate_types.py

echo "==> [2/3] Installing frontend dependencies"
npm install

echo "==> [3/3] Running Tauri build (macOS)"
npm run tauri:build

echo ""
echo "Build complete. Artifacts under frontend/src-tauri/target/"
