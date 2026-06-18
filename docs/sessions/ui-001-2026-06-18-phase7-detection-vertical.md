# Session ui-001 — Phase 7 detection vertical (orchestrator round)

- **Date:** 2026-06-18 (work spanned 2026-06-17→18)
- **Role:** ui-desktop-orchestrator (track: ui, Phase 7)
- **Type:** orchestrator round-recap (no implementer `/session-end` ran — checkpoint round)
- **Predecessor:** none (first ui-track session doc)
- **Round seal:** `origin/track/ui` — see the round commit hash in the Log.

## What was built (landed on `track/ui`)
The onboarding **detection vertical** — 6 slice commits across 3 dispatches, each Step-2.5-reviewed, each green:

- **7.1** (`c22e5cd` + `49de4d2`) — Electron shell + SSE thin-observer: token-bearing IPC client (`X-AISims-Token`
  on every request, `Idempotency-Key` on mutating endpoints), fetch-based SSE subscription with a Zod runtime
  boundary over the frozen §4 taxonomy (`parseErrorCode→SYSTEM` tolerance — carry-forward 0.2/D10b last-consumer),
  `Last-Event-ID` reconnect-replay + idempotent projection (no durable pipeline authority), loopback token handoff
  (sync-IPC closure-getter, **no argv**), and the **§21 UI-responsiveness contract test**.
- **7.2a** (`27513c2` + `523f8b3`) — onboarding Sims-install detection + Mods-path validation + settings
  persistence (over the frozen `GET/PUT /settings`) + the **React 19 + Vite** renderer toolchain (replaced the
  static placeholder). Visual screen → design-fixture review (D4), not `/tdd`.
- **7.2c** (`26e148e`) — preload FS bridge: narrow read-only `node:fs` probes under `window.aisims.fs`
  (`sendSync`, single allowlisted channel, top-frame sender gate) — detection is now **live**.

Reviewer fan-out earned its keep every slice: 7.1 (argv-token §16 leak), 7.2a (type-open IPC method override),
7.2c (IPC sender-frame gap) — each caught + hardened in-slice.

## Decisions made (user, via lead)
- **F1 = B** — re-open §4 with an **additive** `GET /readiness → ReadinessReport` surface (a real readiness
  contract, not client-side inference). Authored as contracts micro-slice `contract-012` on `track/contract-readiness`.
- **F2 = B** — ui owns the **full keychain vertical**, including the sidecar-side read accessor
  (`obs/keychain_secrets.py`, a new class implementing the structural `SecretsAccessor` Protocol, zero edits to
  existing pipeline files; boot-selection = a Phase-2 supervisor TODO).
- **D3 = shared NAMED OS-keychain entry** — UI writes via a Node binding (`@napi-rs/keyring`; keytar archived),
  sidecar reads via Python `keyring`, agreed `(service, account)` names. **Revised from Electron `safeStorage`** after
  a verified Finding: safeStorage returns app-persisted ciphertext + the macOS key is guarded against other apps, so
  a Python sidecar can't decrypt it.
- **D4** — the 7.2a/7.2b decomposition + locked React/Vite + design-fixture-review for visual screens. Approved.
- **Integration-doc-edit policy** — root-doc edits (`IMPLEMENTATION_PLAN.md`/`ARCHITECTURE.md`) batch at the
  track→integration merge via `docs/team-handoffs/ui-integration-doc-edits.md` (never edited in-worktree).

## Decisions explicitly NOT made / deferred
- **7.3 (creator screens) + 7.4 (dev panel)** — HELD for a dedicated decomposition + design-fixture approach + user
  scope input on the 10 screens. No ad-hoc dispatch.
- **Readiness gate (ui)** — deferred until `contract-012` lands + the new generated TS propagates to `track/ui`.
- **Keychain library final pick + CI-mock** — `@napi-rs/keyring` is the candidate; the interop spike (7.2b-0) confirms
  it + the naming scheme before the `/tdd` slices.

## Open follow-ups (in flight / next)
- **`contract-012`** (task #4, `ui-contracts-implementer`, `track/contract-readiness`) — additive `GET /readiness` +
  0.5b snapshot-hardening + codegen IPC-catalog. I author + Step-2.5/Step-9; lead merges → `track/ui` on green.
- **7.2b-0 spike** (task #5, `ui-desktop-implementer`) — `@napi-rs/keyring` ↔ Python `keyring` interop round-trip.
  On PASS I author the 7.2b `/tdd` slices (Node write [rule-5 own commit] + `obs/keychain_secrets.py` + per-provider
  test-call + tracing opt-out).
- **Integration ledger** — `docs/team-handoffs/ui-integration-doc-edits.md` carries every queued root-doc edit
  (P1/P2 ticks, A1–A3 §4/§16 arch-notes, C1 carry-forward landing, T1–T10 TODOs incl. the 0.10 plan entry) +
  the Log entry, for the lead to apply at integration.

## Lessons banked (apps/desktop/LESSONS.md §1–6)
1 fetch-based SSE + header token · 2 Zod-boundary/generated-type parity manifest · 3 no-argv token handoff ·
4 framework-agnostic UI logic + design-fixture visuals · 5 gated GET/PUT client split · 6 narrow renderer↔main bridge.
