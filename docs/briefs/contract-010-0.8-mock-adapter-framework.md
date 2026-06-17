# /tdd brief — mock_adapter_framework

## Feature
Stand up the **mock-adapter framework + deterministic failure injection** (REQ-T-101 / PIPE-002): in-process
**mock implementations behind every provider + worker interface** (the three §7 provider Protocols + the §8/§9
worker job→report executors), plus a **seeded, deterministic failure-injection mode** that can emit a valid
`ErrorEnvelope` (§17) spanning the **entire** error-code taxonomy. Phase-0 test-infra — the seam every Phase-2
pipeline test + the Phase-8 eval harness drives to exercise success **and** failure paths on mocks; NO real
providers, NO engine/LangGraph wiring.

## Use case + traceability
- **Task ID:** 0.8  *(second `services/pipeline`-area slice; same area + implementer as the store-skeleton slice)*
- **Architecture sections it implements:** `ARCHITECTURE.md §7` (provider adapters — "mock+real behind each",
  the `submit/poll/fetch` + `complete/structured` interfaces, model-agnostic; the async `ProviderJobRef`→poll
  reconcile spine + the Tripo 24h `expiresAt` expiry race), §8 (Blender worker `BlenderJob→BlenderReport`
  envelope + `GateMetrics`), §9 (export worker `ExportJob→ExportJobReport` envelope, incl. the `partial` status),
  §17 (the `ErrorEnvelope` taxonomy every stage — **mock+real** — emits; transient vs rate-limited vs
  terminal-config classification). *(Requirement IDs: PIPE-002 mock+real adapters; REQ-T-101 mock adapters incl.
  failure injection — the REQ index files REQ-T-101 under the evals/testing section, but the framework itself
  implements the §7/§8/§9 contract shapes, so those are the spec anchors.)*
- **Related context:** Phase 0, contract track (owns all of Phase 0). The 7 §2.5 contracts are FROZEN + on origin;
  the mocks **import** the Protocols + value models from `aisims_contracts.providers` / `aisims_contracts.workers`
  / `aisims_contracts.error` — they **never redefine** a contract shape. Area conventions
  (`services/pipeline/CLAUDE.md`): `mypy --strict`, Pydantic v2, **forbidden-pattern 2** (no provider lock-in —
  go through the adapter/registry seam; the mock is itself an adapter behind the interface), **forbidden-pattern 4**
  (a worker/mock-worker must NEVER write Postgres/the canonical tree — write only to sidecar-provided scratch +
  return paths; rule 3), **forbidden-pattern 5** (secrets only in the keychain, never State/logs/traces).

## Acceptance criteria (what "done" means)

**A. Mock providers conform to the §7 Protocols (PIPE-002, no lock-in)**
- [ ] `services/pipeline/adapters/mock/` provides a mock for **each** §7 interface: `Image3DProvider`,
  `ImageGenProvider` (`submit/poll/fetch`), `LLMProvider` (`complete/structured`). Each **structurally conforms**
  to the imported `Protocol` (verified by a conformance test — assigned to a `Image3DProvider`-typed variable /
  `isinstance` against the `runtime_checkable` Protocol if available).
- [ ] **Async lifecycle (per Q3):** `submit→ProviderJobRef`; `poll` progresses `SUBMITTED→RUNNING→SUCCEEDED`
  deterministically over a configurable poll-count; `PollResult.progress` interpolates `[0,1]`; `usage.latencyMs`
  always set (§7: latency MUST be recorded); `expiresAt` set so the EXPIRED race is reachable in a test.
- [ ] `fetch(urls)→list[str]` returns **local scratch paths** the mock wrote deterministic placeholder bytes to
  (see E — sole-writer).

**B. Mock workers conform to the §8/§9 envelopes (rule 6 consistency holds)**
- [ ] A mock **Blender** executor `BlenderJob→BlenderReport` (success ⟹ `geomBytesRef` + `gateMetrics` present,
  no error — satisfies the model's `model_validator`) and a mock **export** executor `ExportJob→ExportJobReport`
  (success ⟹ `packagePath`; supports the `partial` status with a per-item error). Reports are built **through the
  frozen models**, so a malformed status↔outputs combo can't be produced.

**C. Deterministic failure injection spanning the §17 taxonomy (REQ-T-101)**
- [ ] A **seeded, deterministic** failure-injection mechanism (per Q1/Q2) that, on demand, makes any mock emit a
  failure carrying a valid `ErrorEnvelope`. Async providers surface it via `PollResult(status=FAILED|EXPIRED,
  error=…)`; mock workers via `BlenderReport(status=FAILED, error=…)` / `ExportJobReport(status∈{FAILED,PARTIAL},
  error=…)`; the **sync** `LLMProvider.complete/structured` surface it by **raising** an `ErrorEnvelope`-bearing
  exception (per Q5 — the sync calls have no error channel in the contract).
- [ ] **Taxonomy coverage:** the injector can produce a valid `ErrorEnvelope` for **every** `ErrorCode` member
  (all 13), each with a sensible `category` + `retryable` (transient→retryable; `PROVIDER_AUTH_QUOTA`→terminal,
  not retryable). A **parametrized test over `list(ErrorCode)`** asserts all 13 are emittable + valid.
- [ ] **Determinism:** same seed + same call sequence ⟹ byte-identical outputs (success refs, latencies, and
  injected failures all reproduce). A test runs a mock twice with one seed and asserts equality.

**D. Injected envelopes are egress-realistic (forward-link to the 0.9 redaction pin)**
- [ ] Injected `ErrorEnvelope`s populate **both** `creatorMessage` and `maintainerDetail` with realistic free
  text, and at least one fixture seeds `maintainerDetail` with a **secret-looking token** — so the 0.9 redaction
  chokepoint (the PINNED rule-5 item) and the eval harness have a real egress surface to scrub. *(0.8 does NOT
  redact — it only produces the surface; 0.9 owns the redaction pin.)*

**E. [rule 3 / forbidden-pattern 4] Mocks honor the sole-writer boundary**
- [ ] Mock providers/workers write artifacts **only** under a **sidecar-provided scratch dir** + return paths;
  they touch **no** Postgres and **no** canonical artifact tree. A test asserts a mock writes only within the
  scratch dir it was given. *(This is a conformance test, not the sole-writer enforcement pin — that is 0.7's
  `test_sidecar_sole_writer`; confirm at Q6 whether you want it as its own commit anyway.)*

**F. Tests + preflight**
- [ ] Deterministic tests in `services/pipeline/tests/adapters/`: Protocol conformance (A), worker-envelope
  success+partial+fail (B), the all-13-`ErrorCode` parametrized injection (C), the same-seed reproducibility (C),
  the sync-call raise path (C/Q5), the scratch-only write (E). `/preflight` clean (**`uv sync --all-packages`**
  from workspace root — D19).

## Wiring / entry point (Step 7.5)
`none wired to a live run yet — Phase-0 mock framework.` Production callers are the **Phase-2 LangGraph nodes**,
which select a mock provider/worker through the **registry/factory seam** (§7/§11) rather than importing a
concrete mock (forbidden-pattern 2 — no hard-wire); the failure-injection seam is driven by **Phase-2 pipeline
tests + the Phase-8 eval harness**. Reachability surface **this** slice = the mocks structurally conform to the
Protocols, the injector emits a valid envelope for every `ErrorCode`, and a seeded run reproduces. See Q7 for how
much registration/factory hook lands now vs Phase-2.

## Files expected to touch
**New:**
- `services/pipeline/adapters/mock/__init__.py` — package + (per Q7) a thin factory/registration helper.
- `services/pipeline/adapters/mock/providers.py` — mock `Image3DProvider` / `ImageGenProvider` / `LLMProvider`.
- `services/pipeline/adapters/mock/workers.py` — mock Blender + export executors.
- `services/pipeline/adapters/mock/failure.py` — the failure-injection core (the `FailurePlan`/behavior model +
  the seeded-determinism engine + the per-`ErrorCode`→`ErrorEnvelope` builder + the sync-call exception type).
- `services/pipeline/tests/adapters/*` — `test_mock_providers.py`, `test_mock_workers.py`, `test_mock_failure.py`.

**Modified:**
- `services/pipeline/pyproject.toml` — only if a dep is genuinely needed (expect **none** — contracts + stdlib).

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2) — `services/pipeline/tests/adapters/`
1. **`test_mock_providers_conform_to_protocols`** — each mock is assignable to its §7 `Protocol` type / passes a
   `runtime_checkable` check. Why: §7 "mock behind each" + forbidden-pattern 2.
2. **`test_mock_provider_async_lifecycle`** — `submit`→ref; successive `poll`s go `SUBMITTED→RUNNING→SUCCEEDED`,
   `progress` rises in `[0,1]`, `usage.latencyMs` set, `expiresAt` present. Why: §7 reconcile-spine + latency MUST.
3. **`test_mock_provider_expired_race`** — a mock configured past `expiresAt` polls `EXPIRED` with an
   `ARTIFACT_EXPIRED` envelope. Why: §7 Tripo 24h expiry race.
4. **`test_mock_workers_build_valid_reports`** — Blender success ⟹ `geomBytesRef`+`gateMetrics`; export success ⟹
   `packagePath`; export `partial` ⟹ `packagePath` + per-item error. Why: §8/§9 + rule-6 `model_validator`.
5. **`test_failure_injection_covers_all_error_codes`** *(parametrized over `list(ErrorCode)`)* — the injector
   emits a valid `ErrorEnvelope` for each of the 13 codes with a sensible `category`/`retryable`. Why: §17 +
   REQ-T-101 ("spanning the taxonomy").
6. **`test_llm_sync_failure_raises_envelope`** — `complete`/`structured` raise the `ErrorEnvelope`-bearing
   exception on injected failure (the sync error channel). Why: §17 + Q5.
7. **`test_mock_determinism_same_seed`** — two runs, one seed ⟹ identical outputs (refs, latencies, injected
   failures). Why: REQ-T-101 deterministic.
8. **`test_mock_writes_only_to_scratch`** *(rule 3 / fp-4)* — a mock writes artifacts only under its provided
   scratch dir; no Postgres / canonical-tree write. Why: rule 3.
9. **`test_llm_structured_returns_schema_instance`** — `structured(prompt, schema, params)` returns a valid
   instance of the caller's `schema` (`type[StructuredT]`). Why: §7 `LLMProvider.structured` + the `StructuredT`
   carry-forward (Q8).

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** **none** to the frozen contracts (the mocks CONSUME `aisims_contracts.{providers,
  workers,error}`, never redefine). The `FailurePlan`/behavior model + the sync-call exception are
  `services/pipeline`-internal, **not** §2.5 seams.
- **Possible contracts-package touch (Q8):** if implementing `LLMProvider.structured` turns out to require
  `StructuredT` in `aisims_contracts.__all__` (the 0.5a carry-forward), that is a **`packages/contracts` export
  change → flag at Step 9 as a cross-doc/contract change** (orchestrator writes; another track owns that file).
  Expected outcome: **no export needed** (a structural conformer doesn't import the TypeVar by name) — confirm.
- **Orchestrator doc rows to write hot (Step 9):** an `adapters/mock` lookup-table row in
  `services/pipeline/CLAUDE.md` (mock framework → §7/§8/§9); any new lesson (the failure-injection design; the
  sync-vs-async error-channel asymmetry; deterministic seeding).
- **§2.5-seam touched?** No. No safety-invariant pin is *introduced* here (the sole-writer pin is 0.7's; the
  redaction pin is 0.9's) — so this slice may bundle (see Estimated commit count).

## Things to flag at Step 2.5
1. **(LOAD-BEARING) Failure-injection API shape.** How does a test/eval tell a mock to fail with a given code at
   a given point? My default: **a typed `FailurePlan` (Pydantic) passed to the mock constructor** — a deterministic
   spec keyed by operation + call-sequence (e.g. `poll` attempt #2 → `PROVIDER_TIMEOUT`), living in
   `adapters/mock/failure.py`. Alternatives: (B) inject via the open `params` bag (`params={"__mock":…}`) — reuses
   the seam but is stringly-typed + pollutes the production params namespace; (C) a separate `FailureInjector`
   strategy object. **My vote: A** — typed, `mypy --strict`-clean, reproducible, no production-namespace bleed.
   This is the seam all of Phase-2/8 drives — surface your read.
2. **(LOAD-BEARING) Determinism mechanism.** My default: **explicit `seed: int` per mock**; every "random" output
   (poll-count-to-success, chosen urls, `latencyMs`, failure timing) is a pure function of `(seed, call-sequence)`
   — **no** bare `random`/wall-clock. Confirm (this is what makes Phase-2 tests + evals reproducible).
3. **Async lifecycle defaults.** My default: `submit` returns `SUBMITTED`; poll #1 → `RUNNING`; poll #N (default
   N=2) → `SUCCEEDED`; `progress` linear; `expiresAt = submittedAt + 24h` (Tripo). A submit-time-class failure
   (e.g. `PROVIDER_AUTH_QUOTA`) surfaces at the **first poll** as `FAILED` (the contract's only error channel for
   async providers is `PollResult.error`). Confirm the default poll-count + the "fail at first poll" choice.
4. **Worker `partial` modeling.** My default: the mock export executor can be told to return `PARTIAL` —
   `packagePath` present + an `error` describing the per-item failure (the only status where outputs **and** error
   coexist). Confirm you want `partial` exercised now (it's the trickiest §9 state).
5. **(LOAD-BEARING) Sync-call error channel.** `LLMProvider.complete/structured` return `str`/`StructuredT` — no
   error field. My default: define a **pipeline-local exception** `MockProviderError(Exception)` (or a more neutral
   `ProviderError`) wrapping an `ErrorEnvelope`, raised on injected failure. Open Q: should an
   `ErrorEnvelope`-bearing **exception type** be a shared contract instead of pipeline-local? My vote: **keep it
   pipeline-local for now** (the contract defines the *data* envelope; the sync error *channel* is a sidecar
   concern) — if you think it should be shared, that's a Step-9 cross-doc flag.
6. **Sole-writer test as its own commit?** My default: the scratch-only write (E) is a **conformance** test folded
   into the worker commit — NOT a separate safety-pin commit (the sole-writer *enforcement* invariant is 0.7's
   `test_sidecar_sole_writer`; 0.8 introduces no new safety invariant). Confirm, or split it out if you prefer.
7. **Registration/factory scope (no hard-wire — fp-2).** How much lands now? My default: expose mock
   **constructors** + a small registration/factory helper so Phase-2 can resolve `provider="mock"` through the
   registry seam — but the actual **engine selection/wiring is Phase 2** (and the registry load-time validator is
   0.5c). Confirm: self-register now, or just expose constructors + the helper?
8. **`structured` return + the `StructuredT` carry-forward (0.5a).** My default: the mock `structured` builds a
   **minimal valid instance of the caller's `schema`** deterministically (defaultable fields; or accept a
   caller-provided fixture). Verify whether this needs `StructuredT` exported from `aisims_contracts.__all__` —
   expected **no** (structural conformance). If yes → Step-9 cross-doc flag (see Cross-doc impact).
9. **Out of scope (confirm):** real provider/worker adapters (Phase 3); the §16 provider-output validation
   (max-bytes/magic-byte/path-sanitize — real-adapter impl logic); engine/LangGraph node wiring + the registry
   *selection* (Phase 2); webhook handling; the §17 retry/backoff *loop* + hang-watchdog (engine logic, Phase 2 —
   the mock only **emits** the classified envelope, it doesn't drive the retry policy).

## Dependencies + sequencing
- **Depends on:** **0.5** (the provider/worker contract Protocols + value models — frozen, on origin) and **0.2**
  (the `ErrorEnvelope` taxonomy — frozen). Both landed. Independent of 0.7 (the store) — the mocks return paths,
  they don't persist.
- **Blocks:** **Phase 2** (the pipeline core runs end-to-end **on these mocks**) and **0.9** (the supervisor/obs
  seam — the redaction pin consumes the egress-realistic envelopes from D). The Phase-8 eval harness also drives
  the failure-injection seam.

## Estimated commit count
**1–2.** No safety-invariant pin is introduced here, so bundling is allowed (root `CLAUDE.md` criteria). The
shared failure-injection core couples providers + workers, so a single cohesive commit is defensible; I lean
**2 for bisectability** — **C1**: failure-injection core (`failure.py`) + mock providers (incl. async lifecycle,
`structured`, the sync-raise channel); **C2**: mock worker executors (Blender + export, incl. `partial`) reusing
the core. Implementer's bisectability call.

## Lessons-logged candidates anticipated
- **Convention candidate** — deterministic seeded mocks: all "randomness" is a pure function of `(seed, call-seq)`
  so Phase-2 tests + evals reproduce byte-for-byte.
- **Convention candidate** — the sync-vs-async **error-channel asymmetry**: async providers carry failure in
  `PollResult.error`; sync `LLMProvider` calls **raise** an `ErrorEnvelope`-bearing exception (no contract error
  field). Document the chosen exception type + where it lives.
- **Architecture-doc note candidate** — record the mock framework + the failure-injection seam (the `FailurePlan`
  shape + "spans every `ErrorCode`") in §7/§17 / the area `CLAUDE.md`, as the surface Phase-2/8 tests depend on.

## How to invoke
1. **Same `services/pipeline` implementer/session as 0.7 — already oriented; skip `/session-start`.** Read this
   brief + `ARCHITECTURE.md §7` (+ §8/§9 worker envelopes, §17 taxonomy). The contract Protocols/value models to
   import: `aisims_contracts.providers`, `aisims_contracts.workers`, `aisims_contracts.error`.
2. **`/tdd mock_adapter_framework`**.
3. **Step 2.5** — answer Q1–Q9 (Q1 injection API, Q2 determinism, Q5 sync error channel are load-bearing); include
   the coverage map (each acceptance bullet → its covering test). Wait for `APPROVED.` before GREEN.
4. **Step 9** — surface the `adapters/mock` lookup row + the seeded-determinism + error-channel-asymmetry lessons,
   and the `StructuredT`-export resolution (Q8) — DELETE-or-act on the 0.5a carry-forward.
