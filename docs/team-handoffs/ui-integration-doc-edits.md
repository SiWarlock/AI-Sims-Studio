# ui-track — Integration Doc-Edits Ledger (running)

> **Policy (lead-set, 2026-06-17):** root shared docs (`IMPLEMENTATION_PLAN.md`, `ARCHITECTURE.md`) are
> **never edited in the ui worktree** (merge-conflict + cross-track race on `main`). Every queued root-doc
> edit the ui track accrues is captured here and applied to `main` in **one serialized pass** when ui merges
> to integration. This file is track-local (`ui-` prefixed) and rides the orchestrator's `/orchestrate-end`
> round commits.
>
> **Scope of this ledger:** ONLY edits to the shared root docs. Track-local docs (`apps/desktop/LESSONS.md`,
> `apps/desktop/CLAUDE.md`, `docs/briefs/ui-*`, session docs) are committed normally in-worktree and are **not**
> listed here.
>
> **Status legend:** `QUEUED` (awaiting integration pass) · `APPLIED` (landed on main at merge).

---

## `ARCHITECTURE.md`

| # | § | Edit | Origin | Status |
|---|---|---|---|---|
| A1 | §4 | Add a one-line note: the UI SSE consumer is **fetch-based with a header-borne token** (`X-AISims-Token` on open *and* reconnect) — **not** native `EventSource` (which can't set headers; a URL token would leak). 7.2/7.3/7.4 depend on this. | 7.1 (`c22e5cd`) | QUEUED |
| A2 | §16 | Add a one-line note: the UI→renderer **loopback-token handoff is no-argv** (synchronous IPC, closure-held in main, `contextBridge` closure-getter) — `process.argv`/`additionalArguments` is enumerable by other local processes (security-review finding, fixed in 7.1). The Phase-7+ real sidecar→renderer handshake MUST preserve this. | 7.1 (`49de4d2`) | QUEUED |
| A3 | §16 | Add a one-line note: the renderer↔main **IPC handlers are top-frame sender-gated** (`senderFrame` must be the top frame) on both the fs-probe and token channels, and host access is a **narrow read-only bridge** (allowlisted single channel, no raw `fs`) — the 7.2b real keychain/sidecar handshake MUST preserve both the no-argv (A2) and sender-gate posture. | 7.2c | QUEUED |

## `IMPLEMENTATION_PLAN.md`

### Checkbox ticks
| # | Target | Edit | Origin | Status |
|---|---|---|---|---|
| P1 | 7.1 | Tick **7.1 [x]** — Electron shell + SSE observer + Last-Event-ID reconnect + loopback token + §21 responsiveness test. Landed on `track/ui`: C1 `c22e5cd` (IPC client + SSE thin-observer core) + C2 `49de4d2` (Electron shell + token handoff + renderer wiring); 17 tests green. | 7.1 | QUEUED |
| P2 | 7.2 | **7.2 stays `[ ]` — PARTIAL.** Landed: **7.2a** (`27513c2`+`523f8b3`, onboarding detect/Mods-path/settings + React/Vite) + **7.2c** (`26e148e`, preload FS bridge — detection live). Still missing: **7.2b** (keychain write + per-provider test-call + tracing opt-out — in flight, interop spike first) + the **readiness gate** (waits on the §4 micro-slice). Note: `(partial: 7.2a/7.2c landed; 7.2b + readiness-gate pending)`. | 7.2a/7.2c | QUEUED |

### Carry-forward landings
| # | Item | Edit | Origin | Status |
|---|---|---|---|---|
| C1 | ErrorEnvelope `code` consumer-tolerance (0.2/D10b) | Mark **last-consumer LANDED** — `apps/desktop/src/ipc/sse-schema.ts` routes an unknown `error.code` → `SYSTEM` via `parseErrorCode`, pinned by `test_sse_error_event_code_tolerance`. The "Phase-7 UI Zod-boundary wiring / Last-consumer-slice: Phase 7" note resolves. | 7.1 | QUEUED |

### New phase-scoped TODOs (add as task bullets in the right phase/subphase)
| # | Phase | TODO | Origin | Status |
|---|---|---|---|---|
| T1 | 7.2 | Pin CSP `connect-src` to the negotiated sidecar port + header-level CSP (`onHeadersReceived`) + define the SSE reconnect-on-non-2xx policy (today it fails loud) + real sidecar-minted token (**preserve no-argv** handoff, see A2). | 7.1 | QUEUED |
| T2 | 7.2a | Vite build so the renderer is built/loaded by the Electron shell. **RE-TARGETED 7.3→7.2a** per D4. **RESOLVED in 7.2a** (React/Vite toolchain + `vite build` → dist/renderer landed) — **no plan TODO needed; drop at integration.** | 7.1 → 7.2a | RESOLVED |
| T4 | 7.2 / contracts | **F1=B (user, 2026-06-17):** re-open §4 with an **additive** readiness surface (proposed: new read-only `GET /readiness → ReadinessReport{overall, checks:[{subsystem,status,detail?,remediation?}]}`) on the contract/integration owning tree, re-froze + codegen'd + propagated; the UI **readiness gate** is deferred until it lands. Routed by the lead as a contracts/integration micro-slice (batchable w/ 0.5b + T3). | 7.2 (F1=B) | QUEUED |
| T5 | 7.2 | **Preload FS bridge** — `node:fs`-backed `FsProbe` under `window.aisims.fs`, narrow read-only + top-frame sender gate. **RESOLVED in 7.2c** — Sims-install detection is now live (no longer safe-defaulting). No plan TODO needed; drop at integration. | 7.2a → 7.2c | RESOLVED |
| T8 | 7.3 | **Exact-renderer-URL sender-origin pin** on the renderer↔main IPC handlers (today: top-frame-only gate, landed 7.2c). Tighten to pin the exact renderer origin when the screens/packaging URL is fixed. | 7.2c | QUEUED |
| T9 | 7.x (if needed) | **`isDirectory` error-distinction** — the boolean `FsProbe.isDirectory` conflates not-exist vs permission-denied (EACCES). Accepted limitation (the sync boolean interface has no error channel; detection checks `exists` first). Enrich only if a consumer needs the distinction (ripples the 7.2a `FsProbe` interface). | 7.2c | QUEUED (accepted) |
| T10 | 0 / contracts | **Add plan task 0.10** — the post-seal `packages/contracts` micro-slice (additive `GET /readiness` + 0.5b snapshot-hardening + codegen IPC-catalog; brief `contract-012`). Lands on `track/contract-readiness`, merges → `track/ui`. The `spec-lint brief` task-ID check for `contract-012` is **waived** until 0.10 exists (anchors/wiring/widens-scope all PASS). Add the task entry at integration. | 7.2/F1=B | QUEUED |
| T6 | 7.2 / 7.3 | **Onboarding screen visual design = design-fixture review (D4)** — the 7.2a screen wires the tested logic but its visuals aren't `/tdd`'d. Route a design-fixture-review task (can batch with the 7.3 creator screens). | 7.2a (D4) | QUEUED |
| T7 | 10 | **Electron packaging layout** — finalize the `dist/renderer` path + Electron build/packaging at the packaging phase (signing/notarization, §19). | 7.2a | QUEUED |
| T3 | contracts-track follow-up | Extend the 0.6 codegen to emit the **IPC protocol/endpoint catalog** (paths, mutating-set, header names, `contractVersion`) so a later UI slice imports it instead of the drift-guarded hand-authored `apps/desktop/src/ipc/endpoints.ts`. Analogous to the existing 0.5b snapshot-hardening micro-slice; needs a `packages/contracts` implementer. | 7.1 | QUEUED |

---

## `IMPLEMENTATION_PLAN.md` — Log entry (add at integration)

```markdown
### 2026-06-18 — Phase 7 detection vertical (ui track, checkpoint round)

- Landed on `track/ui`: 7.1 (Electron shell + SSE thin-observer + Last-Event-ID reconnect + loopback token + §21
  responsiveness test), 7.2a (onboarding Sims-install detect + Mods-path picker + settings persistence + React 19/Vite
  toolchain), 7.2c (preload FS bridge — detection now live). 6 slice commits, all green; sealed + pushed to
  `origin/track/ui` this checkpoint.
- Decisions made (user): F1=B (re-open §4 with an additive `GET /readiness` surface — contracts micro-slice
  `contract-012` on `track/contract-readiness`); F2=B (ui owns the full keychain vertical incl. the sidecar read
  accessor `obs/keychain_secrets.py`); D3 = shared NAMED OS-keychain entry (Node `@napi-rs/keyring` write ↔ Python
  `keyring` read — NOT Electron safeStorage, which a Python sidecar can't decrypt); D4 = the 7.2a/7.2b decomposition +
  design-fixture-review for visuals.
- Cross-cutting: integration-doc-edit policy SET (batch root-doc edits at the track→integration merge; this ledger).
  ErrorEnvelope `code`-tolerance carry-forward (0.2/D10b) LANDED (last consumer = 7.2a `sse-schema`). Lessons 1–6 banked.
- Scope shifts: 7.2 split into 7.2a (landed) / 7.2c (landed) / 7.2b (in flight) / readiness-gate (blocked on §4).
  React/Vite re-targeted 7.3→7.2a (ledger T2).
- New blockers / open questions: 7.2b interop-gate spike (`@napi-rs/keyring` ↔ Python `keyring` round-trip) in flight;
  readiness-gate blocked until `contract-012` lands + merges to `track/ui`.
- Next session target: 7.2b /tdd slices on the proven keychain scheme; the readiness gate after `contract-012` merges;
  7.3/7.4 held for a dedicated decomposition + user scope input.
- Reference: orchestrator session doc `ui-001-2026-06-18-phase7-detection-vertical.md` (no implementer `/session-end`
  ran this round — checkpoint).
```

---

_Appended per slice as the round accrues root-doc edits. Next slice's edits go under the same tables._
