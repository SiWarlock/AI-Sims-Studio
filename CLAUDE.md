# AI Sims Creator — Claude Code Global Context

You are working on AI Sims Creator, a cross-platform desktop app (macOS + Windows) that lets a non-technical creator generate themed Sims 4 custom content collections through AI-assisted workflows. The primary user is a non-technical Sims creator (prefers Alpha-style CC); the secondary user is the technical maintainer who uses an in-app admin mode for template authoring and debugging.

## Critical Rules

1. **Load only the documentation you need.** Never load all the docs at once. Consult `docs/CLAUDE.md` for the task → shard map. Typical task loads 1-3 shards (~3-5k tokens) not the full spec (~47k tokens).
2. **Follow `CODING_STANDARDS.md` strictly.** All rules there are enforced by pre-commit hooks. Lint failures block commits.
3. **Follow `GIT_WORKFLOW.md` for anything git-related.** This file has a short summary below; load `GIT_WORKFLOW.md` itself if you need the full details.
4. **Never edit files in `docs/MONOLITHIC/`.** They are regenerated from shards. Edit the shards. (A Claude Code hook blocks this anyway.)
5. **Never edit files in `shared-types/`.** They are regenerated from Pydantic schemas. Edit the schemas. (Another hook blocks this.)
6. **Never generate AI-authored `.package` files, tuning XML, or 3D meshes.** These are deterministic outputs. AI contributes to planning, texture prompts, metadata, and tuning *values* only — never to formats the game parses.
7. **Every change lives on a feature branch, merges to `dev` via PR.** See "Git Workflow Summary" below.
8. **One session = one task = one PR.** Do not bundle unrelated changes. If you discover something out of scope, note it and open a follow-up task using `.github/ISSUE_TEMPLATE/follow_up.md`.

## Project Summary

- **Primary user:** non-technical Sims 4 creator on macOS, Alpha-CC aesthetic.
- **Admin user:** technical maintainer on Windows (same codebase, cross-platform build).
- **Output:** installable `.package` files for Sims 4 Build/Buy mode, including up to 4 functional archetypes (light on/off, audio device, mirror, moodlet emitter).
- **Not shipping in MVP:** Create-A-Sim content, custom animations, script mods beyond tuning clones, Maxis Match style, marketplace/distribution, auto-updates, telemetry.

## Architecture At A Glance

```
Tauri v2 host (Rust)
  └── React 18 + TypeScript + Redux Toolkit frontend
      └── JSON-RPC 2.0 over stdio
          └── Python 3.12 sidecar (single persistent asyncio process)
              ├── Pydantic v2 schemas (source of truth for types)
              ├── SQLite per project + file-tree assets
              ├── Anthropic API (Claude Sonnet 4.6 / Haiku 4.5)
              ├── Replicate API (image generation, exact model TBD in Phase 1 POC)
              ├── Blender subprocess (thumbnail rendering)
              ├── Local Sims 4 install (read-only, for base-game reference resources)
              └── Local Mods folder (write, for auto-install)
```

**All schemas are Pydantic v2 on the Python side, auto-generated to TypeScript for the frontend.** Never hand-write TypeScript types for IPC payloads. Import from `shared-types/`.

## Directory Map

```
./
├── CLAUDE.md                    # this file (always loaded)
├── CODING_STANDARDS.md          # enforced rules; read before coding
├── GIT_WORKFLOW.md              # authoritative git workflow reference
├── README.md                    # repo-level setup and contributing
├── shard_docs.py                # doc sharding tool (rarely run)
├── .pre-commit-config.yaml      # git hook configuration (see GIT_WORKFLOW.md)
├── .claude/
│   ├── settings.json            # Claude Code tool permissions + hook bindings
│   ├── agents/                  # 9 specialized subagents
│   └── commands/                # 19 slash commands
├── .github/
│   ├── pull_request_template.md # auto-loaded on PR creation
│   └── ISSUE_TEMPLATE/          # bug_report.md + follow_up.md
├── frontend/                    # Tauri + React + RTK
│   ├── CLAUDE.md                # frontend-specific rules (auto-loaded when working here)
│   └── src/
├── sidecar/                     # Python sidecar
│   ├── CLAUDE.md                # sidecar-specific rules
│   └── aisc/                    # package root
│       ├── archetypes/CLAUDE.md
│       ├── dbpf_lib/CLAUDE.md
│       └── templates/CLAUDE.md
├── templates/                   # Tier 1 .glb template files + manifests (Git LFS)
│   └── CLAUDE.md                # template authoring standard
├── scripts/                     # build scripts, codegen, Blender render scripts
│   ├── CLAUDE.md
│   └── hooks/                   # shell scripts used by Claude Code hooks + git hooks
├── shared-types/                # auto-generated TypeScript types (never hand-edit)
└── docs/                        # project documentation
    ├── CLAUDE.md                # doc navigation guide (when loading docs)
    ├── README.md                # doc index
    ├── MONOLITHIC/              # never edit; regenerated from shards
    ├── build_monolithic.py
    ├── prd/                     # 10 shards
    ├── mvp/                     # 16 shards
    ├── tad/                     # 17 shards
    ├── api/                     # 16 shards
    └── diagrams/                # 11 Mermaid shards
```

## Current Phase

**Phase 0: Foundation.** Scaffolding the monorepo, Tauri shell, Python sidecar, project storage (SQLite + file tree), platform detection, Sims install detection, logging, Blender discovery.

When picking up a task, check `docs/mvp/05-phase-0-foundation.md` for the full task list. When Phase 0 is complete, Phase 1 is Milestone Zero (Texturing POC) — a hard quality gate that must pass before committing to Phase 2+.

Update this section when the current phase changes.

## Working on a Task

The typical development loop:

1. **Find the task.** Check `docs/mvp/0{N+5}-phase-{N}-{slug}.md` for your phase's task list. Or run `/load-phase N`.
2. **Create a feature branch.** `phase-{N}/task-{X.Y}-short-slug`. Example: `phase-0/task-0.5-project-storage-layer`. (The pre-push git hook enforces this pattern.)
3. **Load only relevant docs.** See `docs/CLAUDE.md` for the task → shard map. Don't preload the whole spec.
4. **Write the code.** Follow the rules in `CODING_STANDARDS.md` and the relevant subdirectory `CLAUDE.md`.
5. **Write the tests alongside.** Non-UI Python: unit tests required in the same PR. Critical paths: integration test.
6. **Run lint, type check, tests locally.** Or run `/run-tests` and `/review-pr`.
7. **Commit with conventional-commits format.** Reference FR-### or MVP-AC-### in the message where relevant.
8. **Push and open a PR into `dev`.** Use `/open-pr` or follow `GIT_WORKFLOW.md` manually.

## Git Workflow Summary

Full details in `GIT_WORKFLOW.md`. Quick reference:

- **Branches:** `main` (release-ready), `dev` (integration), feature branches (`phase-{N}/task-{X.Y}-slug`).
- **PR target:** always `dev`. Never push directly to `main` or `dev` (hooks block this).
- **PR title format:** `[Phase {N}] Task {X.Y}: Short description`.
- **Commit format:** Conventional Commits. `feat(storage): implement SQLite project persistence (FR-002)`.
- **Merge strategy:** squash-merge into `dev`. `main` receives periodic promotions from `dev` at phase-complete milestones.
- **Pre-commit and pre-push hooks enforce** lint, type check, tests, codegen sync, branch name pattern, and conventional commit format. Never use `--no-verify`.

**When to load `GIT_WORKFLOW.md`:** when the summary above doesn't answer the git question you have — for example, release branching, hotfix procedure, promotion PRs, or the exact hook order.

## How To Run Things

Exact command set lives in `README.md` and is maintained there. Quick reference:

- **Install deps:** `npm install` (monorepo tooling) + `pip install -e ./sidecar` (Python sidecar) + `pip install pre-commit && pre-commit install && pre-commit install --hook-type pre-push && pre-commit install --hook-type commit-msg`
- **Generate TS types from Pydantic:** `python scripts/generate_types.py` (also auto-runs via Claude Code hook when you edit schemas)
- **Lint Python:** `ruff check sidecar/`
- **Type check Python:** `mypy sidecar/`
- **Lint TS:** `cd frontend && npm run lint`
- **Type check TS:** `cd frontend && npx tsc --noEmit`
- **Run Python tests:** `cd sidecar && pytest`
- **Run TS tests:** `cd frontend && npm test`
- **Dev app:** `npm run tauri:dev` (from repo root)
- **Build (macOS):** `npm run build:macos` or `/build-macos` in Claude Code
- **Build (Windows):** `npm run build:windows` or `/build-windows` in Claude Code

## Documentation Navigation

When you need a piece of context, consult `docs/CLAUDE.md` for the task → shard map. Summary of common paths:

| Need | Load |
|---|---|
| Implement an IPC method | `docs/api/{namespace}.md` + relevant `docs/tad/` shard |
| A pipeline stage | `docs/tad/04-pipelines.md` + related AI/assembly shard |
| Phase N task list | `docs/mvp/0{N+5}-phase-{N}-{slug}.md` |
| Data model / new Pydantic | `docs/tad/02-data-model.md` |
| Archetype handler work | `docs/tad/06-archetype-handlers.md` + `docs/mvp/03-archetype-mapping.md` |
| DBPF work | `docs/tad/08-dbpf-packaging.md` |
| Tuning work | `docs/tad/09-tuning-clone.md` |
| Verify against FR-### | `docs/prd/07-functional-requirements.md` or run `/fr {id}` |
| Verify against AC-### | `docs/prd/09-acceptance-and-guardrails.md` or `docs/mvp/13-acceptance-criteria.md` or run `/ac {id}` |
| Git workflow question | `GIT_WORKFLOW.md` |

## What Never To Do

- **Do not load all documentation at once.** It wastes 47k of context for no reason. Load shards as needed.
- **Do not edit `docs/MONOLITHIC/` files.** They are outputs; edit the shards. (Hook-blocked.)
- **Do not edit `shared-types/` files.** They are outputs; edit the Pydantic schemas. (Hook-blocked.)
- **Do not hand-write TypeScript IPC types.** They come from `scripts/generate_types.py`.
- **Do not commit without running lint + type check + tests locally.** Pre-commit hooks reject the commit.
- **Do not push directly to `main` or `dev`.** Feature branch → PR only. (Hook-blocked.)
- **Do not use `--no-verify`** to skip hooks. If a hook is wrong, fix the hook in a separate PR.
- **Do not force-push.** (Hook-blocked.)
- **Do not bundle unrelated changes in one PR.** One task, one PR.
- **Do not generate `.package` files, tuning XML, or meshes via AI.** These are deterministic pipelines with hard game-compatibility requirements. AI contributes to inputs to these pipelines, never to their outputs.
- **Do not bypass the IPC boundary.** The frontend never calls external APIs, never touches the file system beyond Tauri's scoped access, never invokes Blender. All of that flows through the sidecar.
- **Do not hardcode secrets.** API keys live in the platform keyring via the `keyring` library. See `docs/tad/15-security.md`.
- **Do not ship a new feature past scope.** Check `docs/prd/04-mvp-definition.md` and `docs/mvp/00-overview.md` if unsure whether something belongs in MVP.

## Agents and Commands

This project has specialized Claude Code agents for recurring task shapes (backend feature, frontend feature, pipeline stage, archetype handler, template authoring, DBPF work, test writing, refactor, debug investigation). See `.claude/agents/` for the full list. Claude Code auto-routes to them based on each agent's `description` field.

Slash commands for common workflows live in `.claude/commands/`. Notable ones:

- `/load-phase N` — load the phase's task file
- `/load-api {namespace}` — load a specific API namespace doc
- `/fr {id}` / `/ac {id}` / `/d {id}` — look up specific requirements, criteria, or deferred decisions
- `/new-handler {namespace.method}` — scaffold a new IPC handler
- `/review-pr` — pre-commit PR self-review
- `/open-pr` — push branch and open PR into `dev`
- `/run-tests` — unit + integration

See `.claude/commands/` for the full list.

## Hooks

Two separate hook systems operate on this project. Both are enforced strictly.

**Claude Code hooks** (`.claude/settings.json` + `scripts/hooks/*.sh`):
- Block edits to regenerated files (`shared-types/`, `docs/MONOLITHIC/`)
- Block direct commits/pushes to `main`/`dev` and force-pushes
- Auto-regenerate TypeScript types when Pydantic schemas change
- Auto-format Python files with `ruff format` after edits
- Inject session context (branch, phase) at session start
- Remind about uncommitted changes on protected branches at session stop

**Git hooks** (`.pre-commit-config.yaml` + `scripts/hooks/check-*.sh`):
- Pre-commit: ruff, mypy, eslint, tsc --noEmit, codegen sync, file hygiene
- Commit-msg: Conventional Commits format
- Pre-push: branch name pattern, full pytest + vitest + integration suite

See `GIT_WORKFLOW.md` for the full table of what runs when.
