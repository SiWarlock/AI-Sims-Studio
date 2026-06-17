# AI Sims Creator `workers/blender/` — Build Guide

> **You're in `workers/blender/`.** This file plus root `CLAUDE.md` both load. The root file covers global project conventions + shared comm rules (track-prefix, escalation taxonomy, messaging budget); this file owns code-area conventions for the Blender mesh/GEOM worker (bpy).

## Launch protocol

| Working on... | cwd | Loads |
|---|---|---|
| Planning / docs / commits | repo root (`AISimsStudio/`) | root `CLAUDE.md` only |
| the Blender mesh/GEOM worker (bpy) code | `workers/blender/` | this `CLAUDE.md` + root |

<!-- For a multi-area project, add a row per additional code area. -->

If you find yourself fighting the wrong conventions, check your cwd.

## Session start/end protocol

**At session start:**
1. Read `IMPLEMENTATION_PLAN.md` (repo root) **by section, not whole** — `grep -n "^##" IMPLEMENTATION_PLAN.md` for offsets, then Read with offset/limit just "Currently in progress" + the active phase. (The file grows; never load it whole.)
2. Confirm with the user what feature this session is targeting.
3. Read the relevant section of `ARCHITECTURE.md` from the lookup table below.

**At session end** (only when the user explicitly says we're done):

1. **Implementer runs `/session-end`.** Implementer writes ONLY:
   - `workers/blender/` code files (the slice's implementation)
   - test files (the slice's tests)
   - dependency manifest / lockfile (deps the slice adds)
   - `docs/sessions/<NNN>-<date>-<topic>.md` (session doc, created at `/session-end` Step 5)

   **Implementer must NOT touch (all orchestrator territory).** *This list is the canonical statement
   of the territory rule — `/session-end`, the brief template, and the generated
   `scripts/guards/territory-guard.sh` PreToolUse hook (which mechanically enforces it in team mode)
   all point here.*
   - `IMPLEMENTATION_PLAN.md`
   - `workers/blender/LESSONS.md`
   - `workers/blender/CLAUDE.md` (entire file — both the Cross-doc invariants table AND the Lessons logged index)
   - `ARCHITECTURE.md`
   - `docs/orchestrator-briefing.md` / `docs/tdd-brief-template.md` / `docs/briefs/` / `docs/runbooks/`
   - other top-level deliverable / design docs
   - `.gitignore` and root-level dotfiles (unless adding a new artifact to ignore, flagged at Step 9)

   At Step 10: **explicit `git add <path>` per slice file; never `git add -A`/`.`; never stage an orchestrator-territory file.** Changes to any orchestrator-territory file (a new cross-doc model, a lesson, an arch note) are **flagged at Step 9**, not edited here — the orchestrator writes them hot (root `CLAUDE.md` + the Step-9 matrix).

2. **Orchestrator runs `/orchestrate-end`** for round close-out + Carry-forward triage + round terminal commit + push.

## Lookup table — where to find canonical info

Don't paste these sections into the prompt. Grep the file:section, read only what you need. `/check-arch <topic>` dispatches off this table.

| Topic | File (relative to repo root) | Section |
|---|---|---|
| Mesh / Blender subsystem (game-ready gate, render bridge) | `ARCHITECTURE.md` | §8 |
| `BlenderJob`/`BlenderReport` worker contract (+ GEOM-bytes payload) | `ARCHITECTURE.md` | §8 / Appendix |
| Lessons logged (full prose) | `workers/blender/LESSONS.md` | by lesson # |

<!-- Starts near-empty. Add a row whenever a topic is looked up twice. -->

**Code intelligence & docs (when available):** prefer a code-intelligence MCP / docs MCP over grep+read loops — see root `CLAUDE.md` "Code intelligence & docs."

## Stack

<!-- ▼ EXAMPLE BLOCK [id=area-stack]: stack quick-reference for implementer sessions. Canonical stack lives in root CLAUDE.md + ARCHITECTURE.md; this is the cheat sheet. ▼ -->

- **Runtime:** Blender 5.1 bundled Python 3.13 (bpy==5.1.2)
- **Framework:** Blender bpy
- **Validation:** Pydantic v2 (job contracts)
- **Lint / types / tests:** ruff / mypy / pytest (unit) + blender --background (integration)

<!-- ▲ END EXAMPLE BLOCK [id=area-stack] ▲ -->

## Standard commands

```bash
# Install deps (run once; re-run when the manifest changes)
uv sync

# Run the dev server (if applicable)
# (no dev server for this worker — invoked as a CLI subprocess by the sidecar)

# Tests
uv run pytest

# Quality
uv run ruff check .
uv run ruff format --check .
uv run mypy workers/blender

# Preflight (use before saying "done" with a feature)
uv run ruff check . && uv run mypy workers/blender && uv run pytest
```

## TDD protocol

**Write the failing test first.** Applies to deterministic code — see the TDD posture in root `CLAUDE.md` for what is test-first vs. exempt.

**Commit per slice when practical.** Never bundle a safety-critical slice with anything else.

## Forbidden patterns

<!-- ▼ EXAMPLE BLOCK [id=forbidden-patterns]: forbidden patterns — 3-5 narrow, enforceable, domain-specific rules. Shape: "Don't <pattern X> because <reason / past incident>; use <alternative Y>." Test-pin them where possible. Starts small; accretes as lessons surface. ▼ -->

Do not:

1. **Write code without a failing test first** (for deterministic code). Even one-line functions.
2. **Write Postgres or the canonical artifact tree from this worker** — the sidecar is the *sole* writer of Postgres + the canonical artifact tree; this worker writes ONLY to the sidecar-provided scratch dir and returns paths in the `BlenderReport` (ARCHITECTURE.md §8 / §6 repo layer).
3. **Enable MCP-Blender as a STAGE EXECUTOR** — Blender runs via the `blender --background --factory-startup --python` CLI subprocess (ADR-006/008); MCP-Blender is only a measured *spike arm* for judgment-heavy repair, never the production stage path.

**Enforcement patterns (machine-readable — `/preflight` warn-greps the staged diff against these).**
One `grep -E` (or `ast-grep`) expression per line, each tied to a numbered rule above. Rules that can't
be expressed as a pattern carry a `pin:` (test ref) or `accepted:` note on the rule itself instead.

```forbidden-patterns
# rule 2: psycopg|asyncpg|sqlalchemy|create_engine|canonical.*artifact
# rule 3: blender[-_]?mcp|mcp.*blender
```

<!-- ▲ END EXAMPLE BLOCK [id=forbidden-patterns] ▲ -->

## Cross-doc invariants — schema/docs mirroring

Several typed models in this codebase are **contracts** mirrored in `ARCHITECTURE.md` and indexed in the table below. The architecture doc is the canonical contract; the model is the executable enforcement. Drift produces silent disagreement.

**Authoring discipline (orchestrator owns this table).** The implementer never edits this table or `ARCHITECTURE.md` directly — it flags a field add/remove/rename at Step 9 as a `Cross-doc invariant change`; the orchestrator writes the row + the arch edit hot the same round (see root `CLAUDE.md` + `docs/orchestrator-briefing.md`). Commits stagger; the working tree stays aligned within the round.

| Model | `ARCHITECTURE.md` section | Notes |
|---|---|---|
| `BlenderJob` / `BlenderReport` | §8 | job-file/result-file envelope: `{meshPath, params, donorBBox, jobId}` → `{geomBytesRef, previewRef, gateMetrics, status, error?}` |

<!-- Starts empty (or with the first model if one exists). Populated as contract models land. -->

## Module organization

<!-- ▼ EXAMPLE BLOCK [id=module-layout]: module layout + layer dependency rule. Replace with the project's real directory tree and import-direction DAG. ▼ -->

```
workers/blender/
  contracts/        # Pydantic v2 BlenderJob / BlenderReport models (job-file/result-file envelope)
  gate/             # game-ready gate: rescale-to-donor-bbox, floor-centered origin, normal recalc/transfer, UV validation (uv_0+uv_1), meshgroup-count match, LOD + shadow-LOD generation, per-tile poly budget
  geom/             # GEOM export stage + immediate structural validation (fast GEOM check)
  render/           # render bridge: blender --background multi-view render (Apple-Silicon offscreen path)
  cli/              # blender --background --factory-startup --python entrypoint (reads job-file, writes result-file)
  io/               # scratch-dir read/write helpers (sidecar-provided scratch only; never the canonical tree)
```

Layer dependency direction (top depends on bottom, never reverse):

```
cli  →  {gate, geom, render}  →  io  →  contracts
```

Cross-cutting layers can be imported from anywhere. Enforce the rule mechanically with a test where possible — the test *is* the spec for the rule.

<!-- ▲ END EXAMPLE BLOCK [id=module-layout] ▲ -->

## Subagents

See `.claude/agents/README.md` for the canonical inventory + integration points.

<!-- ▼ EXAMPLE BLOCK [id=area-subagent-candidates]: area-specific subagent candidates — list candidates that would earn their keep specifically in this area (e.g. an ABI/types syncer for a frontend area, a Pyth/feed verifier for a contracts area). Build only on real friction. ▼ -->

- *(candidate)* a game-ready-gate-metrics verifier that cross-checks `BlenderReport.gateMetrics` (normals, uv, lods, polyByTile, meshgroups) against the §8 thresholds before the export handoff. Build only on real friction.

<!-- ▲ END EXAMPLE BLOCK [id=area-subagent-candidates] ▲ -->

## Lessons logged from prior sessions

The full prose for each lesson lives in `workers/blender/LESSONS.md`. This index is the compact orientation surface.

**Lesson numbers are stable IDs** — once assigned, they don't change. New lessons get the next sequential number. `/session-end` proposes additions when it detects them; the user approves before the entry is written and a row is added here.

Lessons start at §1.

| # | Date | Topic | Rule (one-liner) |
|--:|---|---|---|
| | | | |

<!-- Starts empty. Each row links to its `LESSONS.md` anchor. -->

<!-- Slash commands: see root CLAUDE.md "Slash commands available." Implementer pair: /session-start + /session-end. -->
