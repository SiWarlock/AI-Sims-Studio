# Session ui-004 — Orchestrator handoff (cycle-1 → cycle-2), Phase 7

- **Date:** 2026-06-18
- **Role:** ui-desktop-orchestrator (track: ui, Phase 7) — **context-cycle handoff** (outgoing orch at WARN/70%)
- **Predecessor:** [`ui-003-…contracts-012….md`](./ui-003-2026-06-18-contracts-012-readiness-snapshot-codegen.md)
- **Successor:** [`ui-005-…phase7-onboarding-settings-slices.md`](./ui-005-2026-06-18-phase7-onboarding-settings-slices.md)
- **Audience:** the **fresh ui-desktop-orchestrator** (same name) who runs `/orchestrate-start` after this cycle.
  Re-orient off THIS doc + the **integration ledger** + session docs ui-001/002/003 + `IMPLEMENTATION_PLAN.md`.

> **READ FIRST, then act:** your **first action** is to **author + dispatch the readiness-gate slice** to the
> waiting `ui-desktop-implementer` (registry 6a17be85, idle on track/ui at the merged HEAD). The brief is **not**
> pre-written (deliberately — it would have climbed the outgoing orch's context). Everything you need is below.

## The single most important artifact: the integration ledger
`docs/team-handoffs/ui-integration-doc-edits.md` is the **complete integration manifest**. In this multi-track
build, **root shared docs (`IMPLEMENTATION_PLAN.md`, `ARCHITECTURE.md`) are NEVER edited in the worktree** — every
plan tick / arch-note / TODO that would normally be a hot-write is captured there and applied to `main` at the
**lead's integration pass**. It currently holds: P1/P2 (7.1 tick, 7.2-partial), A1–A6 (§4/§16/§13 arch-notes incl.
readiness + keychain scheme), C1 (ErrorEnvelope carry-forward landed), T1–T15 (TODOs incl. signed-app ACL risk
T11, mooted classifier T12, Phase-2 boot-selection T15), MERGE-1 (session-doc renumber), 0.10 add+tick (T10), and
the plan Log entry. **Keep appending there; never edit the root docs directly.**

## Phase-7 state (what's landed on track/ui)
HEAD = `f8a851f`; **pushed seal after this handoff's checkpoint** (currently origin = 4032b4d, ~9 ahead).
- **7.1** (`c22e5cd`/`49de4d2`) — Electron shell + SSE thin-observer + token + §21 test.
- **7.2a** (`27513c2`/`523f8b3`) — onboarding detect/Mods-path/settings + React 19/Vite toolchain.
- **7.2c** (`26e148e`) — live preload FS bridge.
- **7.2b-1** (`c355105`/`d566774`) — rule-5 write-only keychain bridge (UI write).
- **7.2b-2** (`f8a851f`) — sidecar keychain read accessor (Python, `services/pipeline/obs/keychain_secrets.py`).
  **→ the F2=B keychain vertical is COMPLETE** (write + read at the shared contract).
- **contracts-012** merged in via **`d18c8f5`** (I pulled `track/contract-readiness`→`track/ui`; hooks passed, UI
  tsc clean): additive `GET /readiness → ReadinessReport` + 0.5b min_length + codegen `ipc-catalog.ts`. **The
  readiness TS is now in `generated/contracts.ts`.**

## THE QUEUE (your sequencing — in order)
1. **readiness-gate slice (DISPATCH FIRST — now unblocked by the merge).** The §18(4) system-readiness gate that
   blocks/queues "New Project" until prerequisites are ready. Consumes the merged **`GET /readiness →
   ReadinessReport{overall: ReadyState, checks: ReadinessCheck[]}`** (`ReadyState='ready'|'degraded'|'blocked'`;
   `ReadinessCheck{subsystem: ReadinessSubsystem, status, detail?, remediation?}`;
   `ReadinessSubsystem='postgres'|'blender'|'sims_install'|'mods_path'|'providers'`) — all in
   `packages/contracts/generated/contracts.ts`. Endpoint `GET /readiness` is READ_ONLY (no idempotency key);
   the IPC client (7.1, `src/ipc/client.ts`) issues it (consider the new `generated/ipc-catalog.ts` for the
   endpoint catalog — the UI `endpoints.ts` can later swap to it, ledger T3). Deterministic surface: the gate
   logic (compute "can start New Project?" from a ReadinessReport — blocked if any subsystem blocked) + the
   client call + empty-`checks` handling ("not yet determined"). The **visual** gate screen → design-fixture
   (D4), not `/tdd`. Brief it as a `/tdd` slice (anchors §18 + §4; widens-scope NOT needed — both in-phase).
2. **7.2b-3** — per-provider test-call (`POST /settings/providers/{p}/test` → `TestProviderResponse{ok,
   latencyMs?, error?}`); the onboarding API-key flow validates a written key. TS, mock-sidecar, uses `parseErrorCode`.
3. **7.2b-4** — privacy/telemetry disclosure + tracing opt-out toggle (`PUT /settings telemetryEnabled`; flips the
   §14 seam). TS.
4. **7.3 (creator screens) / 7.4 (dev panel) — HELD** for a dedicated decomposition + **user scope input** on the
   10 screens (D4 blessed the design-fixture-review pattern, but not the screen scope). Do NOT ad-hoc dispatch;
   escalate to the user via the lead when you reach them.

## The decision trail (load-bearing; do not re-litigate)
- **F1=B** — re-open §4 with an **additive** `GET /readiness` (done; merged `d18c8f5`).
- **F2=B** — ui owns the **full keychain vertical** incl. the sidecar Python read (`obs/keychain_secrets.py`, a new
  class implementing the structural `SecretsAccessor` Protocol, **zero edits to existing pipeline files**;
  boot-selection InMemory→Keychain is a Phase-2 supervisor TODO, ledger T15). Done (7.2b-1 + 7.2b-2).
- **D3 = shared NAMED OS-keychain entry** — `service="AISimsCreator"`, `account=providerId` (NOT Electron
  safeStorage — a Python sidecar can't decrypt it; verified Finding). UI writes via `@napi-rs/keyring`, sidecar
  reads via Python `keyring`; interop proven by spike 7.2b-0. **The `service` constant is byte-identical both ends**
  (`apps/desktop/electron/keychain.ts:KEYCHAIN_SERVICE` ≡ `obs/keychain_secrets.py:KEYCHAIN_SERVICE`).
- **D4** — 7.2a/7.2b decomposition + locked React/Vite + **design-fixture-review for VISUAL screens** (logic is
  `/tdd`; the rendered screen's visuals are not). Mapped as `not-tested-because: visual/wiring` on coverage maps.
- **Integration-doc-edit policy** — batch root-doc edits in the ledger (above).
- **Cross-track contracts micro-slice model** — the lead spawns a separate implementer on a dedicated branch; the
  orchestrator authors the brief + Step-2.5/Step-9 reviews; the **consuming track (ui) pulls the merge** (I did
  d18c8f5 — run the pre-commit hooks here, conventional merge message via `--no-ff`, renumber colliding session
  docs); the lead owns spin-up/down + the integration pass.

## Conventions + review discipline (how I ran it)
- **Per-slice review:** Step-2.5 (verify the per-test `Asserts:` + the acceptance→test coverage map; reply
  `APPROVED.`/`TWEAK:`/`ADD:`); Step-9 (commit-message-first, then hot-route). **Pattern that paid off every
  slice:** the security/quality reviewers caught a real boundary each time, and my Step-2.5 ADDs pinned the
  *complete* boundary (e.g. token-on-SSE-reconnect, GET-no-idempotency, channel reject-default, bridge-path
  secret-canary, no-secret-in-logs). Keep directing the "pin the whole boundary, not just the happy path" ADD.
- **spec-lint** (`scripts/spec-lint.sh brief <path>`) is the **mandatory pre-dispatch gate** — include the
  `@<hash>` PASS stamp in the dispatch. Cite anchors within the phase's `Spec anchors:` line (Phase 7 = §3/§4/§18)
  or add a `widens phase scope because…` line (used for §21, §16, §13). Avoid the literal token `§2.5` in prose
  (it trips the subset check — write "shared-contract-seam").
- **Lessons 1–8** are banked in `apps/desktop/LESSONS.md` (+ `CLAUDE.md` index/enforcement): SSE/token, Zod-parity,
  no-argv handoff, framework-agnostic-UI/design-fixture, gated GET/PUT client, narrow renderer↔main bridge,
  write-only keychain bridge, rule-5 redaction discipline. The pipeline keychain-read Convention is in the ledger
  (T15) for integration (avoid editing `services/pipeline/LESSONS.md` from this worktree — cross-track conflict).
- **Commit cadence:** implementer commits the slice (code+tests, explicit `git add <path>`, never `-A`); orchestrator
  authors every commit message + commits the round docs at `/orchestrate-end`; **push only at `/orchestrate-end`**.
  Trailer: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`.

## The team
- **ui-desktop-implementer** — FRESH (registry 6a17be85), on track/ui at the merged HEAD, **idle awaiting your
  first dispatch** (the readiness-gate). It cycled once already (handled the cross-area Python 7.2b-2 cleanly).
- **Lead** persists (coordination + the integration pass + cross-tree merges + spawn/spin-down). Escalate the 4
  categories (safety, findings, deferments, load-bearing Option-A/B/C) to the user **via the lead**.

## Open follow-ups / risks (also in the ledger)
- T11 signed-app keychain-ACL re-verify (Phase 10). · T15 Phase-2 boot-selection. · A5 the 0.5b min_length moved
  §7/§8/§11 snapshots → core/providers/mesh-export rebase at integration. · MERGE-1 done (ui-003 renumber landed
  in `d18c8f5`). · 7.3/7.4 await user scope.
