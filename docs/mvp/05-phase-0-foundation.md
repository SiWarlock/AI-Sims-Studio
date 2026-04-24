# MVP Spec — Phase 0 — Foundation

> **Source:** `docs/MONOLITHIC/MVP_Specification.md` · **Area:** MVP Spec · **Sections:** §9.1

> App shell, project storage, platform detection, and basic UI scaffolding. No AI, no templates.

---

**Phase goal:** Establish the app shell, project storage, platform detection, and basic UI scaffolding. No AI integration, no templates, no generation.

**Phase acceptance gate:** A user can launch the app on Mac or Windows, create a named project, close the app, reopen the app, and see the project in the recent projects list. The app detects the Sims 4 install and reports its path. No other functionality is required.

#### Tasks

**0.1 — Project repo scaffolding and toolchain setup**
Initialize the repository with Tauri v2 + React frontend + Python sidecar structure. Configure build scripts for both macOS and Windows targets. Set up linting, formatting, and testing scaffolding for both TypeScript and Python.

*Outputs:* Working repo with `npm run dev` launching the app on both platforms, `cargo tauri build` producing platform binaries, pytest and jest test runners functional.
*Dependencies:* None.
*Acceptance:* Repo clones cleanly on both Mac and Windows, dev mode launches successfully, test runners execute (even if no tests yet).

**0.2 — Tauri ↔ Python sidecar IPC foundation**
Establish the communication channel between the Tauri frontend and the Python sidecar process. Choose and implement the IPC mechanism (stdio JSON-RPC recommended). The sidecar launches when the app launches and shuts down cleanly on app exit.

*Outputs:* A working ping/pong from frontend to sidecar returning a response. Lifecycle management ensures no orphaned Python processes.
*Dependencies:* 0.1.
*Acceptance:* Frontend can call a sidecar function and receive a typed response. Sidecar terminates when app closes on both Mac and Windows.

**0.3 — Platform detection and path resolution**
Implement OS detection and platform-specific path resolution for: user home directory, app data directory, logs directory, projects root directory. Document the platform-specific conventions used.

*Outputs:* A Python module that returns correct paths for both Mac and Windows. All paths respect platform conventions (`~/Library/Application Support/AISimsCreator/` on Mac, `%APPDATA%\AISimsCreator\` on Windows).
*Dependencies:* 0.2.
*Acceptance:* Running the module on Mac produces Mac-standard paths; on Windows produces Windows-standard paths. Directories are created if missing.

**0.4 — Sims 4 install detection**
Auto-detect the user's Sims 4 installation on both platforms. Handle standard Origin / EA App install locations. Surface a clear error if not found, with manual override option.

*Outputs:* A module that returns the Sims 4 install path, data directory path, and Mods folder path. Returns structured error when not found.
*Dependencies:* 0.3.
*Acceptance:* On a Mac with standard Sims install, returns the correct paths. Same on Windows. Handles not-found gracefully.

**0.5 — Project storage layer (SQLite + file tree)**
Implement the project storage layer. Each project lives in a folder under the projects root. Folder contains a SQLite database for metadata and a structured subtree for assets. Schema is defined in the TAD.

*Outputs:* Python module exposing project CRUD: create, open, save, list recent, delete. SQLite schema migrations handled.
*Dependencies:* 0.3.
*Acceptance:* A project can be created, closed, reopened, and its metadata persisted. Corruption of one project does not affect others.

**0.6 — Application shell UI**
Build the Tauri + React application shell: main window, navigation structure, home screen with recent projects, new project button, project open action. No project-specific functionality yet.

*Outputs:* App launches to a home screen showing recent projects (empty initially). Clicking "New Project" opens a named prompt and creates a project. Projects appear in the list. Clicking a project opens a placeholder project view.
*Dependencies:* 0.2, 0.5.
*Acceptance:* UI renders correctly on both Mac and Windows. Navigation between home and project view works.

**0.7 — Local logging infrastructure**
Implement local logging for both the frontend and sidecar. Logs written to platform-standard paths. Per-session log files with timestamps. Configurable log levels.

*Outputs:* Python logger writing to `~/Library/Logs/AISimsCreator/` on Mac and `%APPDATA%\AISimsCreator\logs\` on Windows. Frontend errors captured and forwarded to the sidecar for logging.
*Dependencies:* 0.3.
*Acceptance:* Log files are created per session, contain timestamped entries from both frontend and sidecar, and are readable via standard text tools.

**0.8 — Blender discovery**
Detect whether Blender is installed on the user's system. On first launch if missing, prompt the user with a download link and prerequisite explanation. Remember the path once discovered.

*Outputs:* A module that returns the Blender executable path. First-launch flow that handles missing Blender cleanly.
*Dependencies:* 0.3.
*Acceptance:* On a system with Blender installed in a standard location, discovery succeeds. On a system without Blender, the user is clearly informed with a download link. Path can be manually overridden via settings.

---
