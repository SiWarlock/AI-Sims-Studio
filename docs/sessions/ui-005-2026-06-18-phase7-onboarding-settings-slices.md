# Session ui-005 — Phase 7 onboarding/settings slices (keychain-read · readiness-gate · provider-test · telemetry-optout · full-replace RMW fix)

- **Date:** 2026-06-18
- **Role:** ui-desktop-implementer (track: ui, Phase 7) — cycle successor (persists; no cycle this round)
- **Predecessor:** [`ui-004-…orchestrator-handoff-phase7.md`](./ui-004-2026-06-18-orchestrator-handoff-phase7.md)
- **Successor:** _(none yet — implementer persists)_

## Why this session existed

Continue Phase 7 (Creator UI + Onboarding/Settings) on `track/ui`. The §4 readiness contract had just
merged (`d18c8f5`), unblocking the readiness-gate slice. The orchestrator dispatched the remaining 7.2
onboarding/settings deterministic surface as a sequence of `/tdd` slices, plus a mid-round correctness
fix when the user resolved the open `PUT /settings` merge-semantics finding to **full-replace**.

## What was built (5 slices, 5 commits — all on `track/ui`)

| Slice | Commit | Area |
|---|---|---|
| 7.2b-2 sidecar keychain READ accessor | `f8a851f` | `services/pipeline/` (cross-area Python) |
| 7.2 readiness-gate | `528bbdb` | `apps/desktop/` |
| 7.2b-3 per-provider test-call | `c173f75` | `apps/desktop/` |
| 7.2b-4 privacy/telemetry opt-out | `432a468` | `apps/desktop/` |
| 7.2 settings full-replace RMW (data-loss fix) | `2894a26` | `apps/desktop/` |

### Files created
- `services/pipeline/obs/keychain_secrets.py` — `KeychainSecretsAccessor` (structural `SecretsAccessor` Protocol impl, `keyring`-backed at `service="AISimsCreator"`, account=providerId) + `KeychainUnavailableError` + the `KEYCHAIN_SERVICE` constant. Rule-5: repr/str/exception/log surfaces never expose a value; `active_values()` fail-safe for the §16 redactor.
- `services/pipeline/tests/obs/test_keychain_secrets.py` — 11 tests (get/absent/active_values/redaction-canary/Protocol/service-constant/injected-backend/unavailable-typed/fail-safe/no-log/dedup).
- `apps/desktop/src/onboarding/readiness-gate.ts` — `ReadinessGate` view type + `computeReadinessGate` (pure; precedence blocked > indeterminate > ready, fail-safe allow-list) + `evaluateNewProjectReadiness` controller.
- `apps/desktop/test/onboarding/readiness-gate.test.ts` — 10 tests (blocked/ready/degraded/indeterminate/surfaces-every/derives-from-checks/fail-safe/precedence/all-degraded/controller).
- `apps/desktop/src/onboarding/provider-test.ts` — `ProviderTestResult` (discriminated union) + `interpretProviderTest` (parseErrorCode-tolerant; surfaces `creatorMessage` only) + `testProviderConnectivity` controller (validates providerId via `sanitizeProviderId`).
- `apps/desktop/test/onboarding/provider-test.test.ts` — 7 tests (ok+latency/known/unknown→SYSTEM/missing→SYSTEM/message-preserved/composition/rejects-malformed-id).

### Files modified
- `services/pipeline/pyproject.toml` + `uv.lock` — added `keyring>=25.7.0` (ships `py.typed`).
- `apps/desktop/src/ipc/endpoints.ts` — added the `GET /readiness` read-only catalog entry (turned the post-merge drift-guard green).
- `apps/desktop/src/ipc/client.ts` — added `getReadiness()` + `testProvider()` to `IpcClient` (interface + impl).
- `apps/desktop/test/ipc/client.test.ts` — +2 getReadiness tests, +3 testProvider tests, endpoint count 14→15.
- `apps/desktop/src/settings/settings.ts` — added `persistTelemetryEnabled` (7.2b-4), then reworked both helpers to read-modify-write the full resource via a shared private `writeSettings` (#11 full-replace fix).
- `apps/desktop/test/settings/settings.test.ts` — telemetry tests (7.2b-4), then inverted to the full-replace contract (6 tests: GET-before-PUT, both-fields-on-body, sibling-survives-via-RMW, mock-resets-omitted).
- `apps/desktop/test/fixtures/mock-settings.ts` — flipped PUT from PATCH-merge to full-replace (#11), so it can no longer mask a partial-PUT regression.

## Decisions made
- **7.2b-2 keychain unavailability split:** missing key → `None`; locked/unavailable backend (`KeyringError`, incl. macOS `KeyringLocked`) → typed `KeychainUnavailableError` (name only, `raise … from None`, no raw cause). `active_values()` is fail-SAFE (per-provider `KeyringError` swallowed) so the §16 redactor never breaks.
- **readiness-gate semantics:** precedence **blocked > indeterminate > ready**; fail-safe allow-list (canStart iff every check ∈ {ready,degraded}); derives from per-`check.status`, ignores advisory `report.overall`; empty/off-contract → indeterminate (both indeterminate paths surface empty `blocking`/`degraded`).
- **7.2b-3 error surfacing:** surface `ErrorEnvelope.creatorMessage` (rule-5-safe), NEVER `maintainerDetail`; `parseErrorCode` tolerates unknown/missing → SYSTEM. providerId validated via the reused exported `sanitizeProviderId` (not a new `PROVIDER_ID_RE` consumer → ledger T14 unaffected).
- **§4 PUT /settings = FULL-REPLACE (user-pinned):** write helpers must read-modify-write the full object; the mock models full-replace so a partial-PUT regression fails loudly. Shared `writeSettings` resolves each field explicitly (patch-or-current) to dodge the `exactOptionalPropertyTypes` spread footgun with boolean-false.

## Decisions explicitly NOT made (deferred)
- **Boot-time selection** of `KeychainSecretsAccessor` over `InMemorySecretsAccessor` — Phase-2 supervisor TODO (this slice ships the accessor + the Protocol conformance only).
- **Read-modify-write TOCTOU** (GET→PUT window) — accepted + documented (single-user onboarding, low-contention); optimistic concurrency is a future concern.
- **Zod-validating the REST responses** (readiness/provider-test) — kept the existing cast posture; the interpretation/gate functions are the defensive boundary. A REST-wide Zod boundary is its own cross-cutting slice.
- **`UpdateSettingsRequest` required-fields** — flagged (full-replace footgun); contracts/core decision, tracked by the orchestrator (ledger).

## TDD compliance
Clean — every slice was test-first (RED watched to fail for the right reason before GREEN). The #11 fix inverted the existing settings tests as its RED (the RMW-dependent assertions failed against the shipped partial-PUT impl + PATCH-merge mock). No violations.

## Reachability (Step 7.5)
- `KeychainSecretsAccessor` — Protocol-satisfying drop-in for the §16 redactor; runtime boot-selection is a Phase-2 supervisor TODO (constructed-and-Protocol-satisfying, verified by the Protocol-assignment test + `mypy --strict`).
- `getReadiness()` / `testProvider()` — reachable via the wired `IpcClient` surface (`createIpcClient` ← `bootstrap.ts` ← `renderer-entry.ts`).
- `persistModsPath` — reachable via `src/surfaces/onboarding/OnboardingScreen.tsx`.
- **Tested-but-unwired (→ Future TODOs, deferred-wiring pattern):** `evaluateNewProjectReadiness` (consumer = 7.3 New-Project gate screen), `testProviderConnectivity` (consumer = onboarding API-key screen, ledger T17), `persistTelemetryEnabled` (consumer = Settings/onboarding telemetry-toggle screen, ledger T18).

## Open follow-ups
- **Future TODOs (phase-scoped, orchestrator-routed to the ledger):** T16 readiness-gate screen, T17 API-key screen (consumes `testProviderConnectivity`), T18 telemetry-toggle screen (consumes `persistTelemetryEnabled`).
- **Convention/Lessons (orchestrator writes hot):** Lesson 9 (parseErrorCode tolerance), Lesson 10 (surface `creatorMessage` never `maintainerDetail`), Lesson 11 (full-replace ⇒ read-modify-write).
- **Architecture/contracts (orchestrator/lead):** §4 full-replace arch-note (ledger A7) + the cross-track Phase-2 `/settings` handler + acceptance test; `UpdateSettingsRequest` required-fields footgun (contracts/core).
- **Deferred reviewer lows (non-blocking):** `expect(put).toBeDefined()` points a missing-PUT failure one assertion late (suite-wide idiom); `persistTelemetryEnabled` idempotency coverage now implicit via the shared `writeSettings` path.

## Cross-doc invariant audit
No model field changes this session — every slice was **consume-only** (imported generated contract types; defined only UI-local view types `ReadinessGate`/`ProviderTestResult`). Confirmed at each Step 9 ("Cross-doc invariant change — NONE"). Multi-track memory check: nothing owed.
