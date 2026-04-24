# AI Sims Creator

A cross-platform desktop app (macOS + Windows) that lets a non-technical creator
generate themed Sims 4 custom content collections through AI-assisted workflows.

Built with Tauri v2 (Rust host) + React/Redux Toolkit/TypeScript (frontend) +
Python 3.12 sidecar (generation pipelines, DBPF packaging, AI orchestration).

See `CLAUDE.md` for architecture, `CODING_STANDARDS.md` for rules, and
`GIT_WORKFLOW.md` for branching and PR conventions.

---

## Prerequisites

- **Node.js** 20+ and npm 10+
- **Python** 3.12 (the sidecar targets 3.12; see `sidecar/pyproject.toml`)
- **Rust** toolchain (`rustup`) with a recent stable compiler
- **Blender** 4.x (only needed for generation pipelines from Phase 3 onward)

Platform-specific extras:

- **macOS:** Xcode Command Line Tools (`xcode-select --install`)
- **Windows:** Microsoft C++ Build Tools, WebView2 runtime (usually preinstalled)

## First-time setup

From the repo root:

```bash
# Install monorepo JS deps (frontend + shared-types workspace)
npm install

# Install the Python sidecar in editable mode (creates / uses sidecar/.venv)
python3.12 -m venv sidecar/.venv
source sidecar/.venv/bin/activate        # Windows: sidecar\.venv\Scripts\activate
pip install -e ./sidecar[dev]

# Install git hooks
pip install pre-commit
pre-commit install
pre-commit install --hook-type pre-push
pre-commit install --hook-type commit-msg
```

## Common commands

| Command | Purpose |
|---|---|
| `npm run tauri:dev` | Launch the app in dev mode |
| `npm run tauri:build` | Build the platform binary (calls Tauri for the host OS) |
| `npm run build:macos` | Full macOS release build (calls `scripts/build.sh`) |
| `npm run build:windows` | Full Windows release build (calls `scripts/build.ps1`) |
| `npm run gen:types` | Regenerate `shared-types/` from Pydantic schemas |
| `npm run lint` | Lint the frontend |
| `npm run test` | Run frontend tests |
| `cd sidecar && pytest -q` | Run Python tests |
| `cd sidecar && ruff check .` | Lint Python |
| `cd sidecar && mypy --strict .` | Type-check Python |

## Repo layout

See `CLAUDE.md` — "Directory Map" — for the authoritative tree. High-level:

- `frontend/` — Tauri v2 host (Rust) + React/TypeScript/RTK frontend
- `sidecar/` — Python 3.12 sidecar (generation, DBPF, AI orchestration)
- `shared-types/` — auto-generated TypeScript types from Pydantic (never hand-edit)
- `templates/` — Tier 1 template primitives (Git LFS)
- `scripts/` — code generation, build, Blender subprocess scripts
- `docs/` — project documentation (PRD, TAD, MVP spec, API, diagrams)

## Contributing

Every change lives on a feature branch and merges to `dev` via PR. See
`GIT_WORKFLOW.md` for the full workflow. Quick reference:

```bash
# Start work on a phase task
git checkout dev && git pull
git checkout -b phase-{N}/task-{X.Y}-short-slug

# ... make changes ...

git commit -m "feat(scope): short description (FR-###)"
git push -u origin HEAD
# Open PR targeting `dev` via GitHub UI or `gh pr create --base dev`
```
