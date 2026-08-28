# /tdd brief — real_llm_adapter

## Feature
The first **real** `LLMProvider` (§7) — two concrete, model-agnostic backends (Claude direct + OpenRouter) behind the FROZEN `LLMProvider` Protocol, plus the shared real-adapter foundation the rest of Phase 3 reuses: a neutral `adapters/errors.py` (the hoisted `ProviderError` + HTTP→`ErrorCode` classification) and the keychain key-pull / cassette-test pattern.

## Use case + traceability
- **Task ID:** 3.3
- **Architecture sections it implements:** `ARCHITECTURE.md §7` (LLMProvider seam — `complete()`/`structured()`, Claude direct + OpenRouter, API-key auth), §17 (error taxonomy: transient/rate-limited/terminal-config classification; sync calls RAISE), §16 (secrets from keychain at call time only; never into State/logs/traces).
- **Related context:**
  - FROZEN contract: `packages/contracts/src/aisims_contracts/providers.py` — `LLMProvider` Protocol (`complete(prompt, params)→str`, `structured(prompt, schema, params)→StructuredT`), signature-frozen; do **not** redefine or widen it.
  - Parity target: `services/pipeline/adapters/mock/providers.py::MockLLMProvider` (sync; raises `ProviderError` on injected failure) + `adapters/mock/__init__.py` factory seam (`MOCK_PROVIDERS`, no global self-registration).
  - Error channel: `adapters/mock/failure.py::ProviderError` (to be hoisted — see Files) + `aisims_contracts.error` (`ErrorEnvelope`/`ErrorCode`/`ErrorCategory`).
  - Secrets seam: `services/pipeline/obs/secrets.py::SecretsAccessor` (Protocol; `get(name)`/`active_values()`); real OS-keychain backend is Phase 7 — use the `SecretsAccessor` seam now (`InMemorySecretsAccessor` in tests).
  - **Test strategy (locked, human decision 2026-06-17, track-wide):** Option A — **recorded cassettes** replayed in unit tests + an **env-gated live smoke** test (mirrors the 0.7 `AISIMS_TEST_DATABASE_URL` env-gated pattern).
- **Implements:** REQ-I-102.

## Acceptance criteria (what "done" means)
- [ ] `adapters/errors.py` exists and defines `ProviderError` (carrying `.envelope: ErrorEnvelope`); `adapters/mock/failure.py` re-imports it from there so `from adapters.mock import ProviderError` and all existing mock tests stay green (no behavior change to the mock).
- [ ] An HTTP-status → `ErrorCode` classifier in `adapters/errors.py` maps: timeout/connect-error → `PROVIDER_TIMEOUT`; 429 → `PROVIDER_RATE_LIMIT`; 401/402 → `PROVIDER_AUTH_QUOTA`; 5xx/503 → `PROVIDER_OUTAGE`; otherwise → `SYSTEM`. The built `ErrorEnvelope` carries the §17 `retryable` posture (transient/rate-limit/outage/timeout = retryable; auth-quota = NOT retryable).
- [ ] Two concrete adapters — `AnthropicLLMProvider` (Claude direct) + `OpenRouterLLMProvider` (OpenAI-compatible, custom base_url) — each **structurally conforms** to the frozen `LLMProvider` Protocol (verified by an `isinstance`/assignment-to-`LLMProvider` parity test, same as the mock).
- [ ] `complete(prompt, params)` returns the model's free-text completion as `str`.
- [ ] `structured(prompt, schema, params)` returns a **validated** instance of `schema` (the adapter ALWAYS re-validates the returned JSON via `schema.model_validate(...)` — never trusts the provider enforced the shape). Malformed/unparseable output → raises `ProviderError(MALFORMED_OUTPUT)` (retryable; the bounded repair loop is Phase-2, not here).
- [ ] On a provider HTTP failure, `complete`/`structured` **raise** `ProviderError` (sync error channel — the frozen `LLMProvider` has no result error field), with `.envelope.code` per the classifier.
- [ ] Keys are pulled via `SecretsAccessor.get(<name>)` **at call time**, never stored on the instance beyond the accessor reference, never written into params/State/logs/traces (safety rule 5). Adapter `__repr__`/`__str__` never expose the key.
- [ ] **Cassettes are secret-scrubbed before commit**: the `Authorization` / `x-api-key` headers (and any auth material in request/response bodies) are filtered out of every recorded cassette (vcr `filter_headers` / `before_record_*`). No live key bytes land in `docs`/`tests`/git. (Security-reviewable; safety rule 5.)
- [ ] Unit tests replay committed cassettes deterministically (no network); the env-gated live smoke test is **skipped** unless its env var (e.g. `AISIMS_LLM_LIVE=1` + the relevant keys) is set.
- [ ] Adapters are exported through an `adapters/llm` factory seam (a name→constructor map mirroring `MOCK_PROVIDERS`); **nothing self-registers on import** (forbidden-pattern 2 — no provider hard-wire; selection is Phase-2 via the open-registry seam).
- [ ] All unit tests in `services/pipeline/tests/adapters/llm/` pass; existing mock tests still green.
- [ ] `/preflight` clean (ruff + `mypy --strict` + pytest).

## Wiring / entry point (Step 7.5)
**No live graph-node call path this slice** — production *selection* of an `LLMProvider` is Phase-2 (the planning/repair LangGraph node picks an adapter via the open-registry seam and calls `complete`/`structured`). This slice's reachable surface is the **`adapters/llm` factory seam** (the name→constructor map, the analogue of `MOCK_PROVIDERS` that 0.8 shipped without a live node either) **plus the env-gated live smoke test** as the real-call reachability proof. Production node wiring lands in Phase 2 (2.x); the phase-exit reachability audit covers the cross-phase gap. State exactly this at Step 7.5; do not invent a premature caller.

## Files expected to touch
**New:**
- `services/pipeline/adapters/errors.py` — neutral home for `ProviderError` (hoisted from `mock/failure.py`) + the HTTP-status→`ErrorCode` classifier / `ErrorEnvelope` builder.
- `services/pipeline/adapters/llm/__init__.py` — the two adapters' package + the factory seam (name→constructor map).
- `services/pipeline/adapters/llm/anthropic.py` — `AnthropicLLMProvider` (Claude direct).
- `services/pipeline/adapters/llm/openrouter.py` — `OpenRouterLLMProvider` (OpenAI-compatible).
- `services/pipeline/adapters/llm/_base.py` *(optional — if a shared HTTP/key-pull/structured-validate helper emerges; fold into `__init__` if thin)*.
- `services/pipeline/tests/adapters/llm/__init__.py`
- `services/pipeline/tests/adapters/llm/test_llm_adapters.py` — cassette-replayed unit tests + parity test.
- `services/pipeline/tests/adapters/llm/test_errors.py` — classifier tests.
- `services/pipeline/tests/adapters/llm/test_llm_live_smoke.py` — env-gated live smoke.
- `services/pipeline/tests/adapters/llm/cassettes/*` — committed, secret-scrubbed recordings.

**Modified:**
- `services/pipeline/adapters/mock/failure.py` — `ProviderError` now imported from `adapters.errors` and re-exported (backward-compatible; `mock/__init__.py` `from .failure import ProviderError` keeps working).
- `services/pipeline/pyproject.toml` — add the provider SDKs (`anthropic`, `openai`) + the cassette test lib (e.g. `pytest-recording`/`vcrpy`) under the right groups.

If implementation needs files beyond this list, **flag at Step 2.5** before going GREEN.

## RED test outline (Step 2)
Tests in `services/pipeline/tests/adapters/llm/test_errors.py`:
1. **`test_classify_http_status_to_error_code`** — Asserts: 429→`PROVIDER_RATE_LIMIT`, 401/402→`PROVIDER_AUTH_QUOTA`, 503/5xx→`PROVIDER_OUTAGE`, timeout→`PROVIDER_TIMEOUT`, other→`SYSTEM`. Why: §17 provider-error classification.
2. **`test_auth_quota_not_retryable_transient_retryable`** — Asserts: built envelope's `retryable` is False for `PROVIDER_AUTH_QUOTA`, True for timeout/rate-limit/outage. Why: §17 terminal-config vs transient.
3. **`test_provider_error_carries_envelope`** — Asserts: `ProviderError(envelope).envelope is envelope` and importable from BOTH `adapters.errors` and `adapters.mock`. Why: the hoist keeps the mock surface intact (carry-forward 0.8/0.9).

Tests in `services/pipeline/tests/adapters/llm/test_llm_adapters.py`:
4. **`test_adapters_conform_to_llmprovider_protocol`** — Asserts: instances are assignable to `LLMProvider` (parity with the mock; runtime structural check). Why: §7 frozen seam, mock+real parity.
5. **`test_complete_returns_text`** (cassette) — Asserts: `complete()` returns the recorded completion `str`. Why: §7 `complete()`.
6. **`test_structured_returns_validated_model`** (cassette) — Asserts: `structured(prompt, SomeModel, {})` returns a `SomeModel` instance equal to the recorded JSON. Why: §7 `structured()`.
7. **`test_structured_malformed_raises_malformed_output`** (cassette of a bad/invalid-JSON response) — Asserts: raises `ProviderError` with `.envelope.code == MALFORMED_OUTPUT`. Why: §16 deterministic validation; never trust provider-enforced shape.
8. **`test_http_429_raises_rate_limit`** (cassette of a 429) — Asserts: `complete()` raises `ProviderError` with `.envelope.code == PROVIDER_RATE_LIMIT`, `retryable True`. Why: §17 sync raise + classification.
9. **`test_http_401_raises_auth_quota_not_retryable`** (cassette of a 401) — Asserts: raises `ProviderError`, `code == PROVIDER_AUTH_QUOTA`, `retryable False`. Why: §17 terminal-config.
10. **`test_key_pulled_via_accessor_not_persisted`** — Asserts: the adapter calls `SecretsAccessor.get(...)`; the key is absent from `repr(adapter)`, from the returned value, and never set as a plain instance attribute holding the raw key. Why: safety rule 5.
11. **`test_cassettes_have_no_authorization_header`** — Asserts: every committed cassette's recorded requests have no `Authorization`/`x-api-key` value (scrubbed). Why: safety rule 5 — no secret bytes in git.
12. **`test_factory_seam_no_self_registration`** — Asserts: the `adapters/llm` factory map resolves a constructor by name; importing the package does not self-register into any global registry. Why: forbidden-pattern 2.

`services/pipeline/tests/adapters/llm/test_llm_live_smoke.py`:
13. **`test_live_complete_smoke`** — `@pytest.mark.skipif(not env)` — a single real `complete()` against each backend when `AISIMS_LLM_LIVE=1` + keys present. Why: Option A env-gated live proof; the cassette refresh source.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — the frozen §7 `LLMProvider` Protocol + value models are consumed unchanged; no shared-contract-seam model is added or extended, so **no schema-snapshot test** is required this slice.
- **Orchestrator doc rows to write hot (Step 9 routing):** likely an `ARCHITECTURE.md §7` note that the real `LLMProvider` is realized by `AnthropicLLMProvider`/`OpenRouterLLMProvider` behind the `adapters/llm` factory seam, and that `ProviderError` now lives in `adapters/errors.py` (consumes the 0.8/0.9 carry-forward — flag it DONE). No cross-doc *invariant* table row (no contract field changed).
- **Shared-contract-seam model touched?** No.

> Orchestrator territory (canonical list: `services/pipeline/CLAUDE.md` "must NOT touch"): flag at Step 9 categorized; the orchestrator writes hot + commits at `/orchestrate-end`.

## Things to flag at Step 2.5
1. **SDKs vs raw httpx.** Use the official `anthropic` SDK (Claude) + `openai` SDK pointed at OpenRouter's base_url, OR raw `httpx` for both? My default vote: **official SDKs** — they track API changes, handle auth/streaming, and both let you inject a custom `httpx` client so cassettes still intercept at the transport layer; wrap them behind our `LLMProvider` so the §7 seam stays model-agnostic. Raise if cassette interception against the SDKs proves flaky.
2. **Cassette library.** `pytest-recording`/`vcrpy` (record-once YAML, the Option-A intent) vs a transport-level recorder. My default vote: **`pytest-recording` (vcrpy)** with httpx support + mandatory `filter_headers=["authorization","x-api-key"]`. Verify vcrpy↔httpx↔SDK interception works in the RED step; if it doesn't, ping back before GREEN.
3. **Where the §17 code→(category, retryable) classification lives.** Duplicate a small map in `adapters/errors.py`, or extract the shared classification out of the mock's `_TAXONOMY`? My default vote: **a small dedicated `classify(code)→(category, retryable)` in `adapters/errors.py`** — the transient-vs-terminal rule is a §17 fact independent of the mock's canned creator/maintainer messages; leave the mock taxonomy untouched to avoid churn. The real adapter builds `creatorMessage` from a generic per-code template and `maintainerDetail` from the (header-scrubbed) provider response.
4. **Structured-output request mechanism.** Tool-use (Anthropic) / `response_format=json_schema` (OpenAI) derived from `schema.model_json_schema()`, vs prompt-and-parse. My default vote: **use each backend's native JSON/structured mode**, but ALWAYS re-validate via `schema.model_validate` regardless (acceptance #4) — the validation is the contract, the request mode is best-effort.
5. **LLM latency/cost capture — confirm OUT of scope here.** Per the frozen §7 the LLM per-op latency (node wall-clock) + cost (the Phase-2 price-table estimate) are recorded at the calling LangGraph node onto the domain `Step`, NOT on a contract result wrapper — so the adapter returns plain `str`/model and adds no `ProviderUsage`. My default vote: **confirm out-of-scope** (node-level, Phase-2); keep the adapter conforming exactly to the frozen Protocol. (Cross-cloud cost/latency capture is 3.4.)

## Dependencies + sequencing
- **Depends on:** 0.5a (frozen §7 contract — landed), 0.8 (`ProviderError`/mock parity target — landed), 0.9 (`SecretsAccessor` — landed).
- **Blocks:** 3.4 (provider-output validation + cost/latency reuses `adapters/errors.py` + the key-pull/test pattern); 3.2/3.1 reuse the same real-adapter foundation (errors module, keychain pull, cassette pattern, factory seam).

## Estimated commit count
**2.**
- **C1** — `adapters/errors.py` (hoist `ProviderError` + classifier) + the `mock/failure.py` re-import + `test_errors.py`. Pure-deterministic foundation, no live calls; consumes the 0.8/0.9 `ProviderError`-hoist carry-forward.
- **C2** — the two real LLM adapters + key-pull + cassette tests + live smoke + factory seam + manifest deps. **Touches safety rule 5** (secrets at the keychain boundary; cassette scrubbing) → kept as its own commit and **security-reviewer fires** (Step-8 policy `invariant`). `code-quality-reviewer` runs every-slice.

Do NOT bundle C1's classifier with anything that changes the mock taxonomy. If cassette plumbing balloons C2 beyond a reviewable sitting, split the second backend into a third commit and flag at Step 7.5.

## Lessons-logged candidates anticipated
- **Convention candidate** — "Real adapters pull keys via the `SecretsAccessor` seam at call time and re-validate provider output against the pydantic schema even when the provider claims structured mode; cassettes scrub auth headers before commit." (The track-wide real-adapter recipe.)
- **Architecture-doc note candidate** — `ARCHITECTURE.md §7`: the real `LLMProvider` is two backends behind the `adapters/llm` factory seam; `ProviderError` now lives in the neutral `adapters/errors.py` (carry-forward consumed).
- **Future TODO — operational** — env-gated live smoke needs real keys in CI/onboarding (Phase 7 keychain) to refresh cassettes; note it for the holistic-CI infra round.
