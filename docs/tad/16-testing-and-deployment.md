# TAD — Testing, Dependencies, Deployment, and Boundaries

> **Source:** `docs/MONOLITHIC/TAD.md` · **Area:** TAD · **Sections:** §18, §19, §20, §21, §22

> Testing architecture, dependency inventory, build and deployment, open technical questions, architectural boundaries of the TAD itself.

---

## 18. Testing Architecture

### 18.1 Test Layers

- **Unit tests (Python):** pytest, coverage target >80% for non-UI modules. Mock external services.
- **Unit tests (TypeScript):** vitest + React Testing Library for component behavior.
- **Integration tests:** pytest fixtures that spin up the sidecar, inject mocked external clients, and run full pipelines end-to-end.
- **Manual acceptance tests:** the MVP-AC-### list executed against built app on both platforms.

### 18.2 Mock Strategy

External clients (Anthropic, Replicate, Blender, Sims install reader) are injected as dependencies. Tests use mock implementations that return canned responses. A small library of fixture responses lives in `tests/fixtures/`.

### 18.3 Integration Test Environment

A synthetic Sims install fixture (stripped-down, rights-respecting) is NOT bundled with tests. Instead, integration tests that need Sims install data use a set of anonymized sample tuning files committed to the repo under `tests/fixtures/sims_samples/`. These are structurally representative but do not include proprietary EA content.

For tests that require genuine Sims install integration, tests are gated behind an environment variable and skipped in normal CI. Developers with a local install can opt in.

### 18.4 Determinism Tests

Critical determinism test cases:

- Identical project state produces byte-identical `.package` files on rebuild
- Same project rebuilt on Mac and Windows produces byte-identical `.package` files
- TGI ID generation is stable across runs

### 18.5 Visual Quality Tests

Non-automated. Phase 1 POC and Phase 7 acceptance run visual checks in-game. These are documented as signed-off test artifacts with screenshots.

---



## 19. Dependencies

### 19.1 Python (sidecar)

- Runtime: Python 3.12
- Core: `pydantic>=2.0`, `httpx`, `structlog`, `yoyo-migrations`
- AI: `anthropic`, `replicate`
- Image: `Pillow`, `numpy`
- XML: `lxml`
- Mesh: `pygltflib`
- DBPF: (selected in Phase 1 POC — `sims4-tools` or custom)
- Platform: `keyring`
- Testing: `pytest`, `pytest-asyncio`, `pytest-mock`

Complete pinned list lives in `pyproject.toml`.

### 19.2 Frontend

- Runtime: Node 20+ for dev, Tauri-bundled webview for runtime
- Core: `react@18`, `react-dom@18`, `@reduxjs/toolkit`, `react-redux`, `react-router-dom@6`
- UI: `tailwindcss`, `@radix-ui/*` primitives as needed
- Build: `vite`, `typescript`
- Tauri: `@tauri-apps/api`, `@tauri-apps/cli`
- Testing: `vitest`, `@testing-library/react`

### 19.3 External (user-installed or bundled)

- **Blender** — user-installed prerequisite. Minimum version: 4.0 (assumption for MVP).
- **Sims 4** — user-installed prerequisite. Any current patched version.

### 19.4 Development Tooling

- `ruff` — Python linting and formatting
- `mypy` — Python type checking
- `eslint`, `prettier` — TypeScript linting and formatting
- `pre-commit` — git hooks

---



## 20. Deployment and Build

### 20.1 Build Process

Monorepo has a top-level build script:

- `scripts/build.sh` (macOS) / `scripts/build.ps1` (Windows)

The script:

1. Installs Python dependencies into a virtualenv
2. Bundles the Python sidecar into a standalone binary (pyoxidizer or PyInstaller; chosen during Phase 0)
3. Generates TypeScript types from Pydantic schemas (`scripts/generate_types.py`)
4. Builds the frontend (`cd frontend && npm run build`)
5. Invokes Tauri build (`cargo tauri build`)
6. Produces platform-native installer in `target/release/bundle/`

### 20.2 Versioning

Semantic versioning: `MAJOR.MINOR.PATCH`. MVP v1.0 is 1.0.0.

Version string baked into the app binary and reported by `system.version` IPC call.

### 20.3 Distribution

Installers distributed as direct downloads for MVP. No auto-update mechanism (per PRD §8).

### 20.4 CI

No hosted CI required for MVP. Local test runs and manual acceptance testing suffice. A future post-MVP concern is to add GitHub Actions for automated test runs on PRs.

---



## 21. Open Technical Questions

These are tracked for resolution during implementation. They do not block the TAD; they are items the MVP Spec §8 and §12 identify as decisions to be made or refined during specific phases.

1. **Sidecar bundling tool** (`pyoxidizer` vs `PyInstaller` vs alternative) — resolved in Phase 0 based on cross-platform reliability.
2. **DBPF library choice** (D-1) — resolved in Phase 1 POC.
3. **Primary image generation model** (D-2) — resolved in Phase 1 POC.
4. **Normal/specular derivation strategy** (D-3) — resolved in Phase 1 POC.
5. **Exact base-game reference object IDs** (D-4) — resolved in Phase 5.
6. **Blender render recipe specifics** (D-5) — resolved in Phase 1 POC.
7. **Texture resolution policy** (D-6) — confirmed during Phase 1 POC.
8. **Thumbnail dimensions exact** (T-9 assumption) — confirmed when verifying against actual Sims catalog behavior.
9. **Build/Buy category taxonomy mapping** — sourced from Sims 4 documentation during Phase 4.
10. **Sims patch detection mechanism** — verified when building the resource indexer in Phase 5.

---



## 22. Architectural Boundaries — What This Document Is Not

This TAD defines the architecture and pipeline structure but does not contain:

- **Exact IPC method signatures and parameter schemas.** Those live in the API Specification document.
- **Visual diagrams.** Those live in the Architecture Diagrams document.
- **Detailed per-screen UI designs.** Those are implementation choices within the React frontend.
- **Hour-by-hour task breakdowns.** Those are the MVP Specification's concern.
- **Exact tuning field names or resource IDs.** Those are identified during Phase 5 and recorded in code + inline documentation.

---
