# TAD — Cross-Platform Considerations

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §15

> Path resolution per platform, file encoding, Blender invocation, subprocess handling, parity testing.

---

## 15. Cross-Platform Considerations

### 15.1 Path Resolution

Platform-specific paths are owned by a single module (`sidecar/config/paths.py`):

| Purpose | macOS | Windows |
|---|---|---|
| App data | `~/Library/Application Support/AISimsCreator/` | `%APPDATA%\AISimsCreator\` |
| Logs | `~/Library/Logs/AISimsCreator/` | `%APPDATA%\AISimsCreator\logs\` |
| Projects | `~/Documents/AISimsCreator/projects/` | `%USERPROFILE%\Documents\AISimsCreator\projects\` |
| Sims install | Varies by installer, detected | Varies by installer, detected |
| Mods folder | `~/Documents/Electronic Arts/The Sims 4/Mods/` | `%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Mods\` |

All other code uses the path module rather than constructing paths directly.

### 15.2 File Encoding

- All text files UTF-8
- Line endings normalized to `\n` internally; converted to platform native only when a file is explicitly for external consumption

### 15.3 Blender Invocation

Blender path detection differs per platform:

- **macOS:** `/Applications/Blender.app/Contents/MacOS/Blender` is the canonical path
- **Windows:** typically `C:\Program Files\Blender Foundation\Blender X.Y\blender.exe`, falls back to registry lookup

The Blender path, once detected or user-specified, is persisted in config.

### 15.4 Subprocess Handling

Subprocess invocations on Windows require `shell=False` and explicit argument lists; PowerShell arg parsing quirks are avoided. Paths with spaces are passed as single arguments, not concatenated strings.

### 15.5 Parity Testing

CI (future) and manual acceptance tests must execute on both platforms. The deterministic rebuild test (MVP-AC-029) is the main parity gate: identical project state must produce byte-identical `.package` files on both platforms.

---
