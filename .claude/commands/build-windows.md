---
description: Build the app for Windows. Runs codegen, type checks, and the Tauri build for x86_64 Windows.
allowed-tools: Bash, Read
---

Build AI Sims Creator for Windows.

Execute:

1. **Confirm platform:** `!uname -s` should report something containing `MINGW`, `MSYS`, or `CYGWIN` (running via Git Bash / WSL on Windows), OR the environment should otherwise indicate Windows. If not, stop — Windows builds must run on Windows hosts.
2. **Regenerate TypeScript types:** `!python scripts/generate_types.py`
3. **Type check Python:** `!cd sidecar && mypy .`
4. **Type check TypeScript:** `!cd frontend && npx tsc --noEmit`
5. **Build the sidecar bundle:** `!powershell -File scripts/build.ps1 -Target windows`
6. **Build the Tauri app:** `!cd frontend && npm run tauri:build -- --target x86_64-pc-windows-msvc`
7. **Report the output:** list the produced `.msi` installer path with file size.

If any step fails, stop and report the failure with context. Do not continue subsequent steps.

The final artifact lives under `frontend/src-tauri/target/x86_64-pc-windows-msvc/release/bundle/msi/`.

Note: code signing is a separate step handled by the maintainer, not by this command.
