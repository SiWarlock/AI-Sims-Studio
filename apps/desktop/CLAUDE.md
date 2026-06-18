# AI Sims Creator `apps/desktop/` — Build Guide

> **You're in `apps/desktop/`.** This file plus root `CLAUDE.md` both load. The root file covers global project conventions + shared comm rules (track-prefix, escalation taxonomy, messaging budget); this file owns code-area conventions for the desktop UI.

## Launch protocol

| Working on... | cwd | Loads |
|---|---|---|
| Planning / docs / commits | repo root (`AISimsStudio/`) | root `CLAUDE.md` only |
| the desktop UI code | `apps/desktop/` | this `CLAUDE.md` + root |

<!-- For a multi-area project, add a row per additional code area. -->

If you find yourself fighting the wrong conventions, check your cwd.

## Session start/end protocol

**At session start:**
1. Read `IMPLEMENTATION_PLAN.md` (repo root) **by section, not whole** — `grep -n "^##" IMPLEMENTATION_PLAN.md` for offsets, then Read with offset/limit just "Currently in progress" + the active phase. (The file grows; never load it whole.)
2. Confirm with the user what feature this session is targeting.
3. Read the relevant section of `ARCHITECTURE.md` from the lookup table below.

**At session end** (only when the user explicitly says we're done):

1. **Implementer runs `/session-end`.** Implementer writes ONLY:
   - `apps/desktop/` code files (the slice's implementation)
   - test files (the slice's tests)
   - dependency manifest / lockfile (deps the slice adds)
   - `docs/sessions/<NNN>-<date>-<topic>.md` (session doc, created at `/session-end` Step 5)

   **Implementer must NOT touch (all orchestrator territory).** *This list is the canonical statement
   of the territory rule — `/session-end`, the brief template, and the generated
   `scripts/guards/territory-guard.sh` PreToolUse hook (which mechanically enforces it in team mode)
   all point here.*
   - `IMPLEMENTATION_PLAN.md`
   - `apps/desktop/LESSONS.md`
   - `apps/desktop/CLAUDE.md` (entire file — both the Cross-doc invariants table AND the Lessons logged index)
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
| UI / Frontend (surfaces, modes, thin-observer) | `ARCHITECTURE.md` | §3 |
| IPC contract (REST commands, SSE taxonomy, token) | `ARCHITECTURE.md` | §4 |
| Lessons logged (full prose) | `apps/desktop/LESSONS.md` | by lesson # |

<!-- Starts near-empty. Add a row whenever a topic is looked up twice. -->

**Code intelligence & docs (when available):** prefer a code-intelligence MCP / docs MCP over grep+read loops — see root `CLAUDE.md` "Code intelligence & docs."

## Stack

<!-- ▼ EXAMPLE BLOCK [id=area-stack]: stack quick-reference for implementer sessions. Canonical stack lives in root CLAUDE.md + ARCHITECTURE.md; this is the cheat sheet. ▼ -->

- **Runtime:** Node 22 LTS
- **Framework:** React 19 + Vite + Electron
- **Validation:** Zod
- **Lint / types / tests:** ESLint / tsc --noEmit / Vitest

<!-- ▲ END EXAMPLE BLOCK [id=area-stack] ▲ -->

## Standard commands

```bash
# Install deps (run once; re-run when the manifest changes)
pnpm install

# Run the dev server (if applicable)
pnpm dev

# Tests
pnpm test:run

# Quality (formatting is ESLint-enforced — there is no separate `format` script)
pnpm lint
pnpm typecheck

# Preflight (use before saying "done" with a feature)
pnpm lint && pnpm typecheck && pnpm test:run
```

## TDD protocol

**Write the failing test first.** Applies to deterministic code — see the TDD posture in root `CLAUDE.md` for what is test-first vs. exempt.

**Commit per slice when practical.** Never bundle a safety-critical slice with anything else.

## Forbidden patterns

<!-- ▼ EXAMPLE BLOCK [id=forbidden-patterns]: forbidden patterns — 3-5 narrow, enforceable, domain-specific rules. Shape: "Don't <pattern X> because <reason / past incident>; use <alternative Y>." Test-pin them where possible. Starts small; accretes as lessons surface. ▼ -->

Do not:

1. **Write code without a failing test first** (for deterministic code). Even one-line functions.
2. **Hold durable pipeline state in the renderer** — the sidecar is the source of truth (§3); the UI is a thin observer that renders server-driven state from SSE and reconnects via `Last-Event-ID` replay. Don't cache run/item/step state as the authority; derive it from the SSE stream + REST reads.
3. **Issue a REST/SSE/cancel request without the per-launch shared token** (§4/§16) — every call to the sidecar must present the token handed over the trusted parent→child channel; never hard-code, log, or persist it.

**Enforcement patterns (machine-readable — `/preflight` warn-greps the staged diff against these).**
One `grep -E` (or `ast-grep`) expression per line, each tied to a numbered rule above. Rules that can't
be expressed as a pattern carry a `pin:` (test ref) or `accepted:` note on the rule itself instead.

```forbidden-patterns
# rule 2: durable pipeline state in renderer (pin: thin-observer state test — derive run/item/step from SSE, not local cache)
# rule 3: sidecar request missing the per-launch token  fetch\([^)]*\)(?!.*Authorization)
# lesson 1: native EventSource for sidecar SSE — use fetch+ReadableStream w/ header-borne token  new[[:space:]]+EventSource\(
# lesson 2: Zod boundary drift from the generated contract (pin: test_sse_schema_type_parity_with_generated)
# lesson 3: loopback token via argv — use sync-IPC + closure-getter contextBridge  additionalArguments|process\.argv
# lesson 4: React/jsdom in a UI-logic unit test — test logic over injected ports in node env (pin: onboarding/settings tests are framework-agnostic)
# lesson 5: type-open IPC method override / post-hoc Idempotency-Key strip — gate the override + derive idempotency from the effective method  \.method\s*=|delete .*[Ii]dempotency
# lesson 6: raw fs/Node handle exposed to the renderer — expose a narrow read-only sendSync bridge w/ allowlist + top-frame sender gate  exposeInMainWorld\([^)]*require\(|contextBridge[^]*\bfs\b\s*:
# lesson 7: a keychain getProviderKey / read-back to the renderer — bridge is write-only (set/has/delete, no get)  getProviderKey|keychain[^]*\bget(Password|ProviderKey)\b.*renderer
# lesson 8: raw keychain/secret error propagated (cause/message may echo the secret) — throw a fresh typed error, coarse redacted codes  catch[^]*throw (err|error|e)\b|cause:\s*(err|error|e)\b
# lesson 9: a server-report gate that trusts report.overall or fails open on unknown status (pin: test_gate_derives_from_checks_not_overall + test_gate_fail_safe_on_unrecognized_status + test_gate_blocked_takes_precedence_over_unrecognized — decision derives from per-check status as a fail-safe allow-list, overall advisory)
# lesson 10: maintainerDetail surfaced/rendered in a UI/renderer path (rule-5 — surface creatorMessage only)  \bmaintainerDetail\b
# lesson 11: a full-replace PUT helper sending a partial body (data loss) (pin: test_persist_mods_path_read_modify_writes_full_object + test_persist_telemetry_read_modify_writes_full_object + test_mock_full_replace_resets_omitted_field — RMW the full resource; fixture models full-replace)
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
apps/desktop/
  electron/        # Electron main + preload (parent→child token handoff, window lifecycle)
  src/
    ipc/           # REST command client + SSE subscription (token-bearing); generated TS types from contracts
    state/         # server-driven state projection from SSE (NO durable pipeline state)
    surfaces/      # the 12 UI surfaces (dashboard, wizard, plan review, generation workspace,
                   #   concept review, collection board, item detail, functional wizard,
                   #   validation center, export center, dev panel) + Onboarding/Settings
    components/    # shared presentational components
    lib/           # cross-cutting UI utilities (cost formatting, mode gating, a11y helpers)
  test/            # Vitest unit/integration; mock-adapter / mock-sidecar fixtures (Track A)
```

Layer dependency direction (top depends on bottom, never reverse):

```
surfaces → state → ipc → (generated contracts types)
components/lib are cross-cutting (imported from anywhere; import nothing UI-stateful upward)
```

The UI imports **only** the IPC contract surface (§4) toward the sidecar — never sidecar/worker internals (§2.5 import-direction rule: `UI(§3) → IPC(§4) → …`, no upward or cross-sibling imports).

Cross-cutting layers can be imported from anywhere. Enforce the rule mechanically with a test where possible — the test *is* the spec for the rule.

<!-- ▲ END EXAMPLE BLOCK [id=module-layout] ▲ -->

## Subagents

See `.claude/agents/README.md` for the canonical inventory + integration points.

<!-- ▼ EXAMPLE BLOCK [id=area-subagent-candidates]: area-specific subagent candidates — list candidates that would earn their keep specifically in this area (e.g. an ABI/types syncer for a frontend area, a Pyth/feed verifier for a contracts area). Build only on real friction. ▼ -->

- *(illustrative — build only on real friction)* **IPC-types syncer** — verifies the generated TS IPC/SSE types (from `packages/contracts`) match what the UI consumes; flags drift against `ARCHITECTURE.md` §4 before it reaches the CI drift gate.

<!-- ▲ END EXAMPLE BLOCK [id=area-subagent-candidates] ▲ -->

## Lessons logged from prior sessions

The full prose for each lesson lives in `apps/desktop/LESSONS.md`. This index is the compact orientation surface.

**Lesson numbers are stable IDs** — once assigned, they don't change. New lessons get the next sequential number. `/session-end` proposes additions when it detects them; the user approves before the entry is written and a row is added here.

Lessons start at §1.

| # | Date | Topic | Rule (one-liner) |
|--:|---|---|---|
| 1 | 2026-06-17 | [SSE transport](LESSONS.md#1) | UI↔sidecar SSE = `fetch`+`ReadableStream`, token in the `X-AISims-Token` header on open *and* reconnect; never native `EventSource` with a URL token. Guard replay with a `Last-Event-ID` cursor-drop **and** an idempotent projection. |
| 2 | 2026-06-17 | [Zod boundary parity](LESSONS.md#2) | Zod is the runtime boundary; the generated contract is the type — a compile-time parity manifest pins `z.infer` to the generated members/enums so the validator can't drift. |
| 3 | 2026-06-17 | [Loopback token handoff](LESSONS.md#3) | Serve the per-launch token via sync-IPC + a closure-getter `contextBridge`; never `process.argv`/`additionalArguments` (enumerable by other local processes). |
| 4 | 2026-06-17 | [Framework-agnostic UI logic](LESSONS.md#4) | Test UI logic over injected ports (`node` env, no React); the React screen is a thin view whose visuals ride design-fixture review (D4), mapped `not-tested-because: visual/wiring`. |
| 5 | 2026-06-17 | [Conflated GET/PUT client split](LESSONS.md#5) | A frozen endpoint that conflates GET/PUT under one id splits in the client via a **gated** method override (throws outside the named endpoint) + idempotency derived from the effective method — never type-open or strip-after-the-fact. |
| 6 | 2026-06-17 | [Narrow renderer↔main bridge](LESSONS.md#6) | Renderer↔main host access = a narrow read-only bridge: `sendSync`, one allowlisted channel (`default→null`), read-only ops (`fs.access` for writability), a top-frame sender gate per handler; compose bridges into one `window.aisims` via the single helper (closure-getter last). |
| 7 | 2026-06-18 | [Write-only keychain bridge](LESSONS.md#7) | Provider secrets go through a **write-only** main-process keychain bridge (`set`/`has`(bool)/`delete`, **no `get`**) named `(service="AISimsCreator", account=providerId)`; the sidecar reads, the renderer never reads back; keep the secret-name constants identical both ends. |
| 8 | 2026-06-18 | [Rule-5 redaction discipline](LESSONS.md#8) | At a secret boundary: throw a fresh typed error (no raw `cause`) + coarse redacted codes; reject empty/missing secrets before the store; pin redaction with a secret-canary on **every** layer that touches the value (writer AND bridge), not just the innermost. |
| 9 | 2026-06-18 | [Server-report gate decision](LESSONS.md#9) | A gate over a server-driven report derives its OWN decision from per-element status (fail-safe **allow-list**; precedence `blocked > indeterminate > ready`; empty/off-contract ⇒ `indeterminate`, never optimistic-ready); the server's `overall` roll-up is advisory, never the safety decision. |
| 10 | 2026-06-18 | [ErrorEnvelope UI surfacing](LESSONS.md#10) | Render an `ErrorEnvelope`'s **`creatorMessage` only, never `maintainerDetail`** (rule-5 egress at the UI — make the view type structurally unable to hold maintainerDetail); normalize `code` via `parseErrorCode` (unknown/missing → `SYSTEM`); surface the message faithfully (incl. empty) rather than masking a producer violation with a fabricated fallback. |
| 11 | 2026-06-18 | [Full-replace ⇒ read-modify-write](LESSONS.md#11) | A **full-replace** PUT helper must read-modify-write the full resource (GET → overlay the changed field → PUT all fields, each resolved explicitly so falsy/null survive); the fixture must model full-replace (omitted → default) + sibling-survival tests use **non-default** values so a silent drop fails loudly. Confirm PUT semantics from the contract, not the mock. |

<!-- Starts empty. Each row links to its `LESSONS.md` anchor. -->

<!-- Slash commands: see root CLAUDE.md "Slash commands available." Implementer pair: /session-start + /session-end. -->
