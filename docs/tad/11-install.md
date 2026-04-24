# TAD — Auto-Install Mechanism

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §13

> Mods folder detection, pre-install checks, conflict handling, atomicity, script mods detection.

---

## 13. Auto-Install Mechanism

### 13.1 Mods Folder Detection

- **macOS:** `~/Documents/Electronic Arts/The Sims 4/Mods/`
- **Windows:** `%USERPROFILE%\Documents\Electronic Arts\The Sims 4\Mods\`

Detection checks the path exists. If not, the app shows a manual-override UI where the user can point at their Mods folder.

### 13.2 Pre-Install Checks

- Mods folder exists and is writable
- Sufficient disk space (at least 2x the package size)
- Script mods enabled in Sims (for functional items; warning if not detected, not blocker)

### 13.3 Conflict Handling

When a file with the same name exists:

- SHA-256 compared
- If identical: skip, log "already installed"
- If different: UI prompts user with options:
  - Overwrite the existing file
  - Rename the new file (with timestamp suffix)
  - Skip installation (keep the exported file in the project folder only)

### 13.4 Atomicity

File copy is atomic: write to a temp file in the Mods folder, fsync, then rename. This prevents partial writes if the app crashes mid-copy.

### 13.5 Script Mods Detection

For functional items, the app checks whether script mods are enabled in Sims 4 (via inspecting `Options.ini` or equivalent). If disabled, a warning is shown with instructions to enable.

---
