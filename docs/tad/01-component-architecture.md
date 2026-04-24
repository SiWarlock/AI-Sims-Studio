# TAD — Component Architecture

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §3

> Frontend stack and state structure, Python sidecar process model and module structure, repo layout, build and distribution.

---

## 3. Component Architecture

### 3.1 Frontend Architecture

#### 3.1.1 Framework Stack

- **Shell:** Tauri v2 (Rust host, system webview)
- **UI Framework:** React 18
- **Language:** TypeScript (strict mode)
- **State Management:** Redux Toolkit (RTK) with RTK Query disabled (IPC is not REST-shaped)
- **Routing:** React Router v6 (memory router, not browser router — Tauri uses custom protocol)
- **Styling:** Tailwind CSS + CSS modules for component-specific styles
- **Component Primitives:** Radix UI primitives for accessible low-level components (dialogs, dropdowns, tooltips) — styled via Tailwind
- **Build Tool:** Vite

#### 3.1.2 State Structure

Redux state is organized into feature slices:

- **`projectSlice`** — Currently open project, its metadata, its collections and items. Hydrated from sidecar on project open.
- **`generationSlice`** — In-flight generation jobs, per-item status, progress events.
- **`uiSlice`** — UI mode (creator vs admin), current screen, modal state, selected items.
- **`templatesSlice`** — Loaded template registry, schemas, query helpers.
- **`configSlice`** — User configuration (Sims install path, Mods folder path, Blender path, log level).
- **`logsSlice`** — Recent log entries (admin mode only, size-capped).
- **`archetypesSlice`** — Archetype definitions and reference object mappings.

Every slice has explicit actions. Async operations use `createAsyncThunk`. IPC events from the sidecar are received by a top-level listener that dispatches actions into the appropriate slice.

#### 3.1.3 IPC Subscription

A single module owns the sidecar connection. It exposes:

- `request(method, params)` — send a JSON-RPC request, return a promise resolving to the response
- `subscribe(eventType, handler)` — subscribe to a category of push notifications from the sidecar

The IPC module dispatches typed Redux actions in response to events. No component talks to the IPC module directly except for explicit request/response calls; subscriptions flow through Redux.

#### 3.1.4 Screens

Mapped to PRD §20:

- `HomeScreen` — recent projects, new project button
- `NewProjectWizard` — prompt, mode, size, style
- `PlanReviewScreen` — proposed plan, editable
- `CollectionBoardScreen` — item grid with status
- `ItemDetailScreen` — preview, swatches, metadata, actions
- `FunctionalUpgradeWizard` — archetype, config, summary
- `ExportScreen` — validation, options, trigger, result
- `VerificationScreen` — optional post-install in-game check
- `AdminModeRoot` — gates all admin screens
  - `AdminTemplateBrowser`
  - `AdminTemplateEditor`
  - `AdminMeshImporter`
  - `AdminLogsViewer`
  - `AdminJobHistory`
  - `AdminReferenceBrowser`
  - `AdminConfigPanel`

### 3.2 Python Sidecar Architecture

#### 3.2.1 Stack

- **Language:** Python 3.12
- **Async runtime:** `asyncio` (stdlib)
- **Schema / Validation:** Pydantic v2
- **ORM / DB:** SQLite via `sqlite3` (stdlib) with thin typed wrappers; no SQLAlchemy
- **Migrations:** `yoyo-migrations`
- **HTTP:** `httpx` (for direct calls where SDKs are insufficient)
- **AI SDKs:** `anthropic`, `replicate`
- **Image processing:** `Pillow`
- **DDS encoding:** custom module built on `Pillow` + numpy, encapsulated behind a clean interface
- **DBPF:** decision deferred to Phase 1 POC (see MVP Spec §8, D-1). Evaluated options include the `sims4-tools` community Python library and a custom implementation. The codebase isolates DBPF access behind a `dbpf_lib` module so the final choice does not leak outside that boundary.
- **Mesh I/O:** `pygltflib` for `.glb` load/save
- **Logging:** `structlog` on top of stdlib `logging`

#### 3.2.2 Process Model

The sidecar is a **single long-running Python process**, launched by Tauri at app startup and shut down when Tauri exits. A shutdown protocol exists: the frontend can send a `shutdown` request, and the sidecar finishes in-flight jobs, persists state, and exits cleanly within a timeout. If the timeout is exceeded, Tauri force-kills the process.

Within the process:

- An asyncio event loop hosts the JSON-RPC server (over stdio) and the job scheduler
- Long-running jobs (generation, build) run as asyncio tasks
- Blocking operations (Blender subprocess calls, DBPF writes, large image encoding) run in a thread pool executor to avoid blocking the event loop

#### 3.2.3 Module Structure

```
sidecar/
  aisc/                     # package root
    __init__.py
    main.py                 # entry point, stdio JSON-RPC server
    ipc/                    # JSON-RPC protocol, typed handlers
    config/                 # app config, platform detection, paths
    storage/                # SQLite access, project CRUD, migrations
    schemas/                # Pydantic models (shared with frontend via codegen)
    planning/               # Claude-backed collection planning
    spec_gen/               # Claude-backed per-item spec generation
    texture_gen/            # Replicate texture generation pipeline
    thumbnail/              # Blender subprocess invocation
    assembly/               # mesh + texture → textured render asset
    dbpf_lib/               # DBPF library adapter (isolates D-1 outcome)
    packaging/              # DBPF assembly for decor and functional
    tuning/                 # tuning parsing, clone, targeted edit
    archetypes/             # archetype handlers (light, audio, mirror, moodlet)
    validation/             # validation engine
    install/                # Mods folder auto-install
    templates/              # template registry, loader, tier management
    sims_install/           # Sims install detection, resource extraction, indexing
    admin/                  # admin mode operations
    jobs/                   # async job scheduler, progress events
    logging_setup/          # structured logging configuration
    errors/                 # error taxonomy, user-facing message mapping
  tests/
  migrations/               # yoyo-migrations for SQLite schema
  scripts/                  # blender scripts invoked via subprocess
  pyproject.toml
```

### 3.3 Repository Structure

Monorepo layout at the root:

```
aisc/                       # project root
  frontend/                 # Tauri + React
    src/
    src-tauri/              # Tauri Rust shell
    package.json
    vite.config.ts
  sidecar/                  # Python sidecar (see 3.2.3)
  templates/                # Tier 1 template library (Git LFS)
    decor/
    furniture/
    manifests/              # template schema manifests
  shared-types/             # auto-generated TypeScript types from Pydantic schemas
  docs/
    PRD.md
    MVP_Specification.md
    TAD.md                  # this document
    Architecture_Diagrams.md
    API_Specification.md
    user-manual/
    maintainer-guide/
  scripts/                  # build scripts, codegen, dev helpers
  .github/                  # CI config (future)
  README.md
  pyproject.toml            # sidecar Python package
  package.json              # monorepo tooling
```

Template `.glb` files are stored via Git LFS. Large binary assets (reference textures, sample inputs) also via LFS.

### 3.4 Build and Distribution

- **macOS build:** Tauri produces a `.dmg` installer containing the app bundle with the embedded Python sidecar and template library. Intel and Apple Silicon targets supported; primary user is on Intel Mac so Intel build is the explicit target.
- **Windows build:** Tauri produces a `.msi` or `.exe` installer.
- **Python sidecar bundling:** Uses `pyoxidizer` or `PyInstaller` to bundle Python runtime and dependencies into a standalone executable that Tauri invokes as a subprocess. Exact bundler chosen during Phase 0 based on cross-platform reliability.
- **Template library bundling:** Template `.glb` files and manifests are included in the app resources directory at build time.
- **Blender:** Not bundled. Detected at first launch.

---
