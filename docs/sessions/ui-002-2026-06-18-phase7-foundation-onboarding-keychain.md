# Session ui-002 — Phase 7 UI foundation + onboarding + keychain-write (implementer)

- **Date:** 2026-06-18
- **Role:** ui-desktop-implementer (track: ui, Phase 7 — `apps/desktop`)
- **Type:** implementer `/session-end` (technical close-out)
- **Predecessor:** [`ui-001-2026-06-18-phase7-detection-vertical.md`](./ui-001-2026-06-18-phase7-detection-vertical.md) (orchestrator round-recap)
- **Successor:** _(fresh `ui-desktop-implementer` — impl-only context cycle; picks up 7.2b-2 / readiness-gate / screens)_
- **Branch:** `track/ui` (not pushed by me — orchestrator pushes at `/orchestrate-end`)

## Why this session existed
Stand up the Phase-7 `apps/desktop` foundation and the onboarding/detection + keychain-write verticals via `/tdd` cycles (plus one throwaway interop spike). Cycled (impl-only) at a clean boundary after 7.2b-1 landed — context climbing, and the next slice (7.2b-2) is cross-area Python that risks a mid-slice stop.

## What was built (this session, on `track/ui`)

### 7.1 — Electron shell + SSE thin-observer (`c22e5cd`, `49de4d2`)
- **Created:** `src/ipc/{endpoints,token,client,sse-schema,sse}.ts`, `src/state/projection.ts`, `src/bootstrap.ts`, `src/renderer-entry.ts`, `electron/{token-handoff,preload,main}.ts`, `index.html`, `test/ipc/*`, `test/state/projection.test.ts`, `test/electron/token-handoff.test.ts`, `test/responsiveness.test.ts`, `test/bootstrap.test.ts`, `test/fixtures/mock-sse.ts`.
- Token-bearing IPC client (`X-AISims-Token` always; `Idempotency-Key` on mutating; throws without token), fetch-based SSE + Zod boundary over the frozen §4 taxonomy (compile-time parity manifest; `parseErrorCode→SYSTEM`), `Last-Event-ID` reconnect-replay + idle-backoff + §16 buffer cap, idempotent projection (no durable authority), §21 responsiveness test. Token handoff = sync-IPC closure-getter (no `process.argv`).

### 7.2a — onboarding detect/validate/settings + React 19 + Vite (`27513c2`, `523f8b3`)
- **Created:** `src/onboarding/{fs-probe,detect,mods-path,renderer-fs}.ts`, `src/settings/settings.ts`, `src/main.tsx`, `src/surfaces/onboarding/{App,OnboardingScreen}.tsx`, `vite.config.ts`, `test/onboarding/*`, `test/settings/settings.test.ts`, `test/renderer-entry.test.ts`, `test/fixtures/mock-settings.ts`.
- **Modified:** `src/ipc/client.ts` (gated `getSettings`/`updateSettings` + effective-method idempotency), `src/renderer-entry.ts` (injectable `startRenderer`, auto-run removed), `electron/main.ts` (Vite loader, dev/prod CSP), `index.html` (Vite entry), `tsconfig.json` (jsx + DOM lib), `package.json` (react/react-dom/vite + dev/build scripts).
- `detectSimsInstall`/`validateModsPath` over an injected `FsProbe`; settings round-trip over `GET/PUT /settings`; React/Vite replaced the static placeholder (visual screen → design-fixture, D4).

### 7.2c — preload FS bridge (live detection) (`26e148e`)
- **Created:** `electron/fs-bridge.ts`, `test/electron/fs-bridge.test.ts`, `test/onboarding/renderer-fs.test.ts`.
- **Modified:** `electron/token-handoff.ts` (generalized to compose `window.aisims` with an `extra` member bag — the single-`exposeInMainWorld` constraint), `electron/preload.ts`, `electron/main.ts` (register FS handlers).
- Narrow read-only `node:fs` probes under `window.aisims.fs` (`sendSync`, single allowlisted channel, top-frame sender gate); `resolveFsProbe` (7.2a) now resolves the real probe → detection is live.

### 7.2b-0 — keychain interop SPIKE (throwaway; no committed files)
- Verdict **PASS**: `@napi-rs/keyring` (Node) ↔ Python `keyring` interop byte-exact on one `genp` entry (`svce`=service, `acct`=account). Locked naming: `service="AISimsCreator"`, `account=providerId`. CI mockable both sides. Carry-forward risk: signed-app cross-process ACL prompt → Phase-10 re-verify (ledger T11). Scratch code + keychain entry cleaned up.

### 7.2b-1 — keychain provider-key WRITE (rule-5) (`c355105`, `d566774`)
- **Created:** `electron/keychain.ts` (KeychainWriter secret core + KeychainEntry boundary + KeychainUnavailableError + InvalidProviderIdError + `KEYCHAIN_SERVICE` + validation), `electron/keychain-bridge.ts` (`dispatchKeychain`/`registerKeychainBridge`/`createKeychainBridge`), `src/keychain/provider-keys.ts` (renderer client + `sanitizeProviderId`), `test/electron/{keychain,keychain-bridge}.test.ts`, `test/keychain/provider-keys.test.ts`.
- **Modified:** `electron/preload.ts` (`window.aisims.keychain`), `electron/main.ts` (napi factory + register), `package.json` (`@napi-rs/keyring ^1.3.0`).
- Write-only bridge (set/has/delete, **no get** — secret never read back); rule-5 redaction pinned on both the writer and the bridge path; locked → `KeychainUnavailableError`.

## Decisions made (implementer-level; user/lead decisions are in ui-001)
- **File splits for clean commit boundaries:** `keychain.ts` (secret core, own rule-5 commit) / `keychain-bridge.ts` (bridge) — per-file split avoids hunk-staging.
- **`dispatch*` pure helpers** (`dispatchFsProbe`, `dispatchKeychain`) so the channel reject-default is unit-testable (Lesson 6 consistency).
- **Writer-authoritative validation** (providerId + empty-key) at the main-process trust boundary; the renderer client sanitizes too (defense-in-depth, fail-safe).
- **Native boundaries are typecheck-only** (`import type` electron / the @napi-rs/keyring factory in `main.ts`) so unit tests load no native module and touch no real keychain/FS.
- **All keychain-boundary errors → one redacted `KeychainUnavailableError`** (no `cause`) — fail-safe redaction over diagnostic granularity (a raw error could echo the secret).
- **Removed the `isNoEntryError` classifier** after verifying (via the installed `.d.ts`) the sync `Entry` returns `string|null`/`bool` sentinels for absent (neither throws) — so the prod factory is trivial pass-throughs (mooted ledger T12).

## Decisions explicitly NOT made / deferred
- **7.2b-2 Python read accessor** (`obs/keychain_secrets.py`) — cross-area (`services/pipeline`), NOT my area; must read the SAME `(service="AISimsCreator", account=providerId)` — constants must match `keychain.ts` `KEYCHAIN_SERVICE`.
- **Onboarding API-key visual screen** wiring `createProviderKeysClient` — design-fixture (D4), not `/tdd`.
- **7.3 creator screens + 7.4 dev panel** — held for a dedicated decomposition (ui-001).
- **Readiness gate (ui)** — waits on `contract-012` landing + generated-TS propagation to `track/ui`.

## TDD compliance — CLEAN
Every deterministic slice was RED-first (test written + confirmed failing for the right reason before GREEN); each paused at Step-2.5 for orchestrator review. Exempt-and-followed: React screens (`App`/`OnboardingScreen`) ship via design-fixture review (D4), not `/tdd`; Electron `main`/`preload` + the @napi-rs/keyring prod factory are typecheck-only wiring (their logic is extracted into tested pure helpers — `isTopFrameSender`, `dispatch*`, the injected boundaries). 7.2b-0 was an exploratory spike (throwaway, not `/tdd` — appropriate). **No TDD violations.**

## Cross-doc invariant audit — NONE changed
Multi-track memory check: every slice this session was **consume-only** — no new §2.5-seam model defined, no schema-snapshot owed, no §-contract field add/remove/rename. The `(service="AISimsCreator", account=providerId)` secret-name contract is **ui-owned** (a Convention, flagged at Step 9 → routed to the integration ledger), not a frozen §-model. Nothing to flag.

## Reachability (carried from each slice's Step-7.5)
- **7.1** `bootstrapObserver` ← `index.html` → `src/renderer-entry.ts:startRenderer` → client + SSE + projection. (Vite TS→JS build of `renderer-entry`/`main.tsx` was wired in 7.2a.)
- **7.2a** `detectSimsInstall`/`validateModsPath`/`loadSettings`/`persistModsPath` ← `OnboardingScreen` ← `App` ← `src/main.tsx` (Vite build green).
- **7.2c** `registerFsBridge` ← `electron/main.ts` (app.whenReady); `window.aisims.fs` ← preload; `resolveFsProbe` ← `main.tsx`.
- **7.2b-1** `registerKeychainBridge` ← `electron/main.ts`; `window.aisims.keychain` ← preload (Lesson-6 helper, token+fs preserved).
- **GAP (tested-but-not-yet-screen-wired):** `createProviderKeysClient` (`src/keychain/provider-keys.ts`) — consumed by the onboarding API-key-entry screen, which is design-fixture/next. The write path itself (main → bridge → keychain) is fully wired. → open follow-up.

## Open follow-ups (for the successor)
1. **7.2b-2 — Python read accessor** (`obs/keychain_secrets.py`, `services/pipeline`): read `keyring.get_password("AISimsCreator", providerId)`; constants MUST match `keychain.ts:KEYCHAIN_SERVICE`. Cross-area — likely a pipeline implementer, not ui.
2. **Onboarding API-key visual screen** wires `createProviderKeysClient` (design-fixture, D4) — closes the 7.2b-1 reachability gap.
3. **Onboarding screen visual design (7.2a)** — design-fixture review (D4).
4. **Readiness gate (ui)** — after `contract-012` + generated-TS propagation.
5. **Shared providerId validator** — `PROVIDER_ID_RE` is duplicated `keychain.ts` (authoritative) / `provider-keys.ts` (UX); fail-safe but extract a shared validator (+ optional length cap) if it grows.
6. **Header-level CSP + sidecar-port `connect-src` pin** — carried from 7.1/7.2a (today: tight meta CSP + loopback-wide connect-src; dev relaxation is `apply:"serve"`-only).
7. **Signed-app cross-process keychain ACL re-verify** — ledger T11, Phase 10.
8. **7.3 creator screens + 7.4 dev panel** — held for decomposition.

## Lessons banked (apps/desktop/LESSONS.md)
§1–6 from the detection vertical (fetch-SSE+header-token · Zod/generated parity manifest · no-argv handoff · framework-agnostic logic+design-fixture visuals · gated GET/PUT client split · narrow renderer↔main bridge) + §7–8 from 7.2b-1 (write-only keychain bridge · rule-5 redaction discipline) — written by the orchestrator.

## How to use what was built
- Renderer reaches main only through `window.aisims` = `{ getToken, fs, keychain }` (composed via the single Lesson-6 `exposeInMainWorld` helper; all narrow, sender-gated).
- Provider keys: renderer `createProviderKeysClient(window.aisims.keychain).setProviderKey(providerId, key)`; the sidecar reads the same `(service, account)` entry. The renderer NEVER reads a key back.
