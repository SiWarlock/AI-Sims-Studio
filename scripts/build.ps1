# Windows release build for AI Sims Creator.
#
# Orchestrates the full build:
#   1. Regenerate shared-types/ from Pydantic schemas
#   2. Install frontend deps
#   3. Build via Tauri (produces a .msi / .exe in frontend/src-tauri/target/)
#
# The Python sidecar bundling step (PyOxidizer or PyInstaller — choice deferred
# to Phase 0) is intentionally not wired here yet.

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path "$PSScriptRoot\.."
Set-Location $RepoRoot

Write-Host "==> [1/3] Regenerating shared-types/"
python scripts/generate_types.py

Write-Host "==> [2/3] Installing frontend dependencies"
npm install

Write-Host "==> [3/3] Running Tauri build (Windows)"
npm run tauri:build

Write-Host ""
Write-Host "Build complete. Artifacts under frontend/src-tauri/target/"
