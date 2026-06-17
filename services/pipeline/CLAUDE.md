# AI Sims Creator `services/pipeline/` — Build Guide

> **You're in `services/pipeline/`.** This file plus root `CLAUDE.md` both load. The root file covers global project conventions + shared comm rules (track-prefix, escalation taxonomy, messaging budget); this file owns code-area conventions for the Python pipeline sidecar.

## Launch protocol

| Working on... | cwd | Loads |
|---|---|---|
| Planning / docs / commits | repo root (`AISimsStudio/`) | root `CLAUDE.md` only |
| the Python pipeline sidecar code | `services/pipeline/` | this `CLAUDE.md` + root |

<!-- For a multi-area project, add a row per additional code area. -->

If you find yourself fighting the wrong conventions, check your cwd.

## Session start/end protocol

**At session start:**
1. Read `IMPLEMENTATION_PLAN.md` (repo root) **by section, not whole** — `grep -n "^##" IMPLEMENTATION_PLAN.md` for offsets, then Read with offset/limit just "Currently in progress" + the active phase. (The file grows; never load it whole.)
2. Confirm with the user what feature this session is targeting.
3. Read the relevant section of `ARCHITECTURE.md` from the lookup table below.

**At session end** (only when the user explicitly says we're done):

1. **Implementer runs `/session-end`.** Implementer writes ONLY:
   - `services/pipeline/` code files (the slice's implementation)
   - test files (the slice's tests)
   - dependency manifest / lockfile (deps the slice adds)
   - `docs/sessions/<NNN>-<date>-<topic>.md` (session doc, created at `/session-end` Step 5)

   **Implementer must NOT touch (all orchestrator territory).** *This list is the canonical statement
   of the territory rule — `/session-end`, the brief template, and the generated
   `scripts/guards/territory-guard.sh` PreToolUse hook (which mechanically enforces it in team mode)
   all point here.*
   - `IMPLEMENTATION_PLAN.md`
   - `services/pipeline/LESSONS.md`
   - `services/pipeline/CLAUDE.md` (entire file — both the Cross-doc invariants table AND the Lessons logged index)
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
| Pipeline orchestration (LangGraph) | `ARCHITECTURE.md` | §5 |
| Job/run engine + supervisor | `ARCHITECTURE.md` | §6 |
| Lessons logged (full prose) | `services/pipeline/LESSONS.md` | by lesson # |

<!-- Starts near-empty. Add a row whenever a topic is looked up twice. -->

**Code intelligence & docs (when available):** prefer a code-intelligence MCP / docs MCP over grep+read loops — see root `CLAUDE.md` "Code intelligence & docs."

## Stack

<!-- ▼ EXAMPLE BLOCK [id=area-stack]: stack quick-reference for implementer sessions. Canonical stack lives in root CLAUDE.md + ARCHITECTURE.md; this is the cheat sheet. ▼ -->

- **Runtime:** Python 3.13
- **Framework:** FastAPI + LangGraph
- **Validation:** Pydantic v2
- **Lint / types / tests:** ruff / mypy --strict / pytest

<!-- ▲ END EXAMPLE BLOCK [id=area-stack] ▲ -->

## Standard commands

```bash
# Install deps (run once; re-run when the manifest changes)
uv sync

# Run the dev server (if applicable)
uv run uvicorn pipeline.main:app --reload

# Tests
uv run pytest

# Quality
uv run ruff check .
uv run ruff format --check .
uv run mypy services/pipeline

# Preflight (use before saying "done" with a feature)
uv run ruff check . && uv run mypy services/pipeline && uv run pytest
```

## TDD protocol

**Write the failing test first.** Applies to deterministic code — see the TDD posture in root `CLAUDE.md` for what is test-first vs. exempt.

**Commit per slice when practical.** Never bundle a safety-critical slice with anything else.

## Forbidden patterns

<!-- ▼ EXAMPLE BLOCK [id=forbidden-patterns]: forbidden patterns — 3-5 narrow, enforceable, domain-specific rules. Shape: "Don't <pattern X> because <reason / past incident>; use <alternative Y>." Test-pin them where possible. Starts small; accretes as lessons surface. ▼ -->

Do not:

1. **Write code without a failing test first** (for deterministic code). Even one-line functions.
2. **Hard-code a single image-gen / image-to-3D / LLM provider** — go through the adapter + registry (ADR-03/04/14); a provider lock-in breaks the bakeoff (§7) and the model-agnostic guarantee. Use the `Image3DProvider` / `ImageGenProvider` / `LLMProvider` interfaces + the provider registry instead.
3. **Collapse item-level state into one global flag** — per-item, per-step state is the 13-state item machine (§12); a single run-wide flag loses skip/unsupported/cancelled re-entry. Use the per-item state machine instead.
4. **Let a worker write Postgres or the canonical artifact tree** — the sidecar is the SOLE writer (§6/§13); workers (§8/§9) write only to sidecar-provided scratch dirs and return paths. Have the engine repo layer commit the row after the worker returns a path.
5. **Write secrets into LangGraph `State` / logs / traces** — cloud/LLM keys live ONLY in the OS keychain (§13/§16); redaction at every egress, tracing is fail-open. Pull keys at the adapter boundary; never persist them in graph State.

**Enforcement patterns (machine-readable — `/preflight` warn-greps the staged diff against these).**
One `grep -E` (or `ast-grep`) expression per line, each tied to a numbered rule above. Rules that can't
be expressed as a pattern carry a `pin:` (test ref) or `accepted:` note on the rule itself instead.

```forbidden-patterns
# rule 2 (provider lock-in): \b(fal|wavespeed|replicate|openrouter|tripo|hunyuan|flux|claude)\b.*=.*(client|sdk|api_key)  pin: tests/adapters/test_registry.py
# rule 3 (global item flag): \bself\.(item_done|all_items_ready|run_state)\s*=
# rule 4 (worker DB/tree write): pin: tests/store/test_sidecar_sole_writer.py
# rule 5 (secrets in State/logs/traces): (api_key|secret|token)\s*[:=].*(State|log\.|trace|span)
```

<!-- ▲ END EXAMPLE BLOCK [id=forbidden-patterns] ▲ -->

## Cross-doc invariants — schema/docs mirroring

Several typed models in this codebase are **contracts** mirrored in `ARCHITECTURE.md` and indexed in the table below. The architecture doc is the canonical contract; the model is the executable enforcement. Drift produces silent disagreement.

**Authoring discipline (orchestrator owns this table).** The implementer never edits this table or `ARCHITECTURE.md` directly — it flags a field add/remove/rename at Step 9 as a `Cross-doc invariant change`; the orchestrator writes the row + the arch edit hot the same round (see root `CLAUDE.md` + `docs/orchestrator-briefing.md`). Commits stagger; the working tree stays aligned within the round.

| Model | `ARCHITECTURE.md` section | Notes |
|---|---|---|
| <model> | §X | <field summary> |

<!-- Starts empty (or with the first model if one exists). Populated as contract models land. -->

## Module organization

<!-- ▼ EXAMPLE BLOCK [id=module-layout]: module layout + layer dependency rule. Replace with the project's real directory tree and import-direction DAG. ▼ -->

```
services/pipeline/
  graph/          # §5 LangGraph StateGraph — one node/subgraph per stage; typed State; interrupt() gates; checkpointer
  engine/         # §6 job/run engine + supervisor — bounded-parallel scheduler, startup reconciler, single-writer lock, process-tree teardown
  adapters/       # §7 provider adapters — Image3DProvider / ImageGenProvider / LLMProvider (mock + real behind each), bakeoff
  registries/     # §11 open registries — PlacementType / FunctionalArchetype / DonorMapping (config = source of truth, loaded into PG cache)
  store/          # §13 repo layer (sole writer of Postgres + canonical artifact tree) — Alembic, write-bytes-then-commit-row
  obs/            # §14 observability — thin tracing seam (LangSmith), fail-open background export, redaction chokepoint
```

Layer dependency direction (top depends on bottom, never reverse):

```
graph → engine → { adapters, registries }
engine → store
( obs, security/redaction, errors, config ) = cross-cutting — imported from anywhere
```

The sidecar (`graph` + `engine`) is the only writer of Postgres + the canonical artifact tree; workers (Blender §8, export §9) write only to sidecar-provided scratch dirs and return paths. No upward or cross-sibling imports.

Cross-cutting layers can be imported from anywhere. Enforce the rule mechanically with a test where possible — the test *is* the spec for the rule.

<!-- ▲ END EXAMPLE BLOCK [id=module-layout] ▲ -->

## Subagents

See `.claude/agents/README.md` for the canonical inventory + integration points.

<!-- ▼ EXAMPLE BLOCK [id=area-subagent-candidates]: area-specific subagent candidates — list candidates that would earn their keep specifically in this area (e.g. an ABI/types syncer for a frontend area, a Pyth/feed verifier for a contracts area). Build only on real friction. ▼ -->

- *(illustrative — build only on real friction)* a **reconciler-table verifier** that checks the startup-reconciler decision-table (§6) against its test matrix.
- *(illustrative)* a **graph-node two-phase auditor** that flags cloud steps missing the persist-`ProviderJobRef`-before-side-effect ordering (R9, §5).

<!-- ▲ END EXAMPLE BLOCK [id=area-subagent-candidates] ▲ -->

## Lessons logged from prior sessions

The full prose for each lesson lives in `services/pipeline/LESSONS.md`. This index is the compact orientation surface.

**Lesson numbers are stable IDs** — once assigned, they don't change. New lessons get the next sequential number. `/session-end` proposes additions when it detects them; the user approves before the entry is written and a row is added here.

Lessons start at §1.

| # | Date | Topic | Rule (one-liner) |
|--:|---|---|---|
| | | | |

<!-- Starts empty. Each row links to its `LESSONS.md` anchor. -->

<!-- Slash commands: see root CLAUDE.md "Slash commands available." Implementer pair: /session-start + /session-end. -->
