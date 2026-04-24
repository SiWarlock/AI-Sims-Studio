---
description: Build the app for macOS. Runs codegen, type checks, and the Tauri build for Intel and Apple Silicon targets.
allowed-tools: Bash, Read
---

Build AI Sims Creator for macOS.

Execute:

1. **Confirm platform:** `!uname -s` should report `Darwin`. If not, stop — macOS builds only run on macOS hosts.
2. **Regenerate TypeScript types:** `!python scripts/generate_types.py`
3. **Type check Python:** `!cd sidecar && mypy .`
4. **Type check TypeScript:** `!cd frontend && npx tsc --noEmit`
5. **Build the sidecar bundle:** `!bash scripts/build.sh --target macos`
6. **Build the Tauri app:** `!cd frontend && npm run tauri:build -- --target universal-apple-darwin`
7. **Report the output:** list the produced `.app` bundle and `.dmg` installer paths, with file sizes.

If any step fails, stop and report the failure with context. Do not continue subsequent steps.

The final artifacts live under `frontend/src-tauri/target/universal-apple-darwin/release/bundle/`.

Note: signing and notarization are separate steps handled by the maintainer, not by this command.
