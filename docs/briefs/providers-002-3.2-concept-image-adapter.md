# /tdd brief — concept_image_adapter

## Feature
The first **real** `ImageGenProvider` (§7) — a WaveSpeed FLUX.2 [pro] concept-image backend (async submit/poll/fetch, `transparent_bg`, pinned seed) behind the FROZEN Protocol — plus the deterministic **silhouette-quality gate** (score an RGBA concept image + select-best-of-candidates), reusing the 3.3 real-adapter foundation.

## Use case + traceability
- **Task ID:** 3.2
- **Architecture sections it implements:** `ARCHITECTURE.md §7` (ImageGenProvider seam — submit/poll/fetch; WaveSpeed default FLUX.2 [pro] `transparent_bg`; N-candidate + silhouette gate), §17 (async error channel: failure rides `PollResult.error`, NOT raise — lesson 5), §16 (fetch writes only to sidecar scratch; deterministic quality gate before downstream use).
- **Related context:**
  - FROZEN contract: `packages/contracts/src/aisims_contracts/providers.py` — `ImageGenProvider` Protocol (`submit(prompt, params)→ProviderJobRef`, `poll(ref)→PollResult`, `fetch(urls)→list[str]`), signature-frozen; do **not** redefine/widen.
  - **Foundation landed in 3.3** (reuse, don't re-create): `adapters/errors.py` (`ProviderError`, `classify(status)→ErrorCode`, `build_envelope`), the `SecretsAccessor` key-pull-at-call-time pattern, the vcr cassette pattern (`record_mode='none'`, `filter_headers`), the name→constructor factory seam, raw httpx. See LESSONS 9 (the real-adapter recipe).
  - Async parity target: `adapters/mock/providers.py::MockImageGenProvider` / `_BaseAsyncProvider` (SUBMITTED→RUNNING→SUCCEEDED; `PollResult.error` on failure; scratch-guarded `fetch`).
  - **Test strategy (locked, track-wide):** Option A — recorded cassettes (record-once, scrubbed) + env-gated live smoke. Same wire-fidelity rule as 3.3: verify the WaveSpeed/FLUX.2 wire shape via Context7; synthesize strictly from the verified schema if no live keys; re-record from live later.
- **Implements:** EVAL-002.

## Acceptance criteria (what "done" means)
- [ ] `WaveSpeedImageGenProvider` structurally conforms to the frozen `ImageGenProvider` Protocol (assignable to `ImageGenProvider`; submit/poll/fetch callable) — parity with the mock.
- [ ] `submit(prompt, params)` issues the generation request with `transparent_bg` + a **pinned seed** from params, and returns a `ProviderJobRef` (provider/model/jobId/submittedAt[/expiresAt]).
- [ ] `poll(ref)` returns a `PollResult`: SUBMITTED/RUNNING with `progress` while pending, SUCCEEDED with `urls` + `usage.latencyMs` set on completion.
- [ ] **Async error channel (lesson 5 / §17):** a provider **job-failure** or a poll-request HTTP failure surfaces as `PollResult(status=FAILED|EXPIRED, error=ErrorEnvelope)` classified via `adapters.errors` — `poll` does **NOT** raise. BUT `submit` and `fetch` (no result error field) **raise** `ProviderError` on HTTP failure (no ref / no paths to return). Pin all three channels.
- [ ] `fetch(urls)` writes downloaded bytes **only** under the sidecar-provided scratch dir with sanitized basenames; a path escaping scratch is rejected (rule 3 scratch-guard — the mock's `fetch` guard is the analogue; the §16 byte-cap/magic-byte hardening is 3.4).
- [ ] Keys pulled via `SecretsAccessor.get(...)` **at call time**, never persisted / in repr / State / logs / traces / envelope (rule 5).
- [ ] **Silhouette gate (deterministic):** `silhouette_score(image_bytes)→float` in [0,1] scores an RGBA concept image high for a clean, centered, single-component silhouette and low for empty/transparent or fragmented/multi-blob; `select_best(candidates, threshold)` returns the highest-scoring candidate above `threshold` and surfaces a defined failure when none passes (see Step-2.5 Q3).
- [ ] Cassettes are secret-scrubbed (`filter_headers=[authorization,x-api-key,api-key]`); no live key bytes in git. Unit tests replay deterministically (`record_mode='none'`); the live smoke is `skipif` env-gated.
- [ ] Exported through an `adapters/imagegen` factory seam (name→constructor map, mirroring `MOCK_PROVIDERS`/`LLM_PROVIDERS`); nothing self-registers on import (forbidden-pattern 2).
- [ ] All unit tests in `services/pipeline/tests/adapters/imagegen/` pass; existing mock + 3.3 LLM tests stay green.
- [ ] `/preflight` clean.

## Wiring / entry point (Step 7.5)
**No live graph-node call path this slice** (same posture as 3.3) — production concept-stage selection of an `ImageGenProvider` + the resumable N-candidate submit/poll loop are Phase-2. This slice's reachable surface is the **`adapters/imagegen` factory seam** + the **`silhouette` gate functions** (the deterministic selector the Phase-2 concept node will call on fetched candidates) + the env-gated live smoke. State exactly this at Step 7.5; do not invent a premature caller. NOTE: the N-candidate **generation** loop (submit-N → poll-each → fetch-each) is **Phase-2 resumable-node** logic — this slice provides the per-candidate provider + the *scoring/selection over already-fetched candidates*, not a sync poll-to-completion loop (which would conflict with the Phase-2 two-phase resumable node).

## Files expected to touch
**New:**
- `services/pipeline/adapters/imagegen/__init__.py` — package + factory seam (`IMAGEGEN_PROVIDERS`) + exports.
- `services/pipeline/adapters/imagegen/wavespeed.py` — `WaveSpeedImageGenProvider` (FLUX.2 [pro]).
- `services/pipeline/adapters/imagegen/silhouette.py` — `silhouette_score` + `select_best` (the gate).
- `services/pipeline/adapters/imagegen/_base.py` *(optional — a shared async submit/poll/fetch + scratch-guard helper if it emerges; 3.1 image-to-3D will reuse it. Fold into wavespeed.py if thin.)*
- `services/pipeline/tests/adapters/imagegen/{__init__,conftest,test_wavespeed,test_silhouette,test_imagegen_live_smoke}.py`
- `services/pipeline/tests/adapters/imagegen/cassettes/*.yaml` — committed, secret-scrubbed.

**Modified:**
- `services/pipeline/pyproject.toml` — add the image lib for silhouette scoring (Pillow + numpy, or per Step-2.5 Q5). `httpx` already landed (3.3).

If implementation needs files beyond this list, **flag at Step 2.5** before GREEN.

## RED test outline (Step 2)
`tests/adapters/imagegen/test_wavespeed.py`:
1. **`test_conforms_to_imagegenprovider_protocol`** [§7] — instance assignable to `ImageGenProvider`; submit/poll/fetch callable. Parity with the mock.
2. **`test_submit_returns_jobref_with_seed_and_transparent_bg`** [§7] (cassette) — `submit(prompt, {seed, transparent_bg})` sends both in the request body and returns a well-formed `ProviderJobRef`.
3. **`test_poll_pending_then_succeeded`** [§7] (cassette) — poll → SUBMITTED/RUNNING with `progress`, then SUCCEEDED with `urls` + `usage.latencyMs` set.
4. **`test_poll_job_failure_rides_pollresult_error`** [§17] (cassette of a failed job) — `poll` returns `PollResult(FAILED, error=ErrorEnvelope)` classified; does **NOT** raise (async channel, lesson 5).
5. **`test_submit_http_failure_raises`** [§17] (cassette of a 401) — `submit` RAISES `ProviderError(PROVIDER_AUTH_QUOTA)` (no ref to return).
6. **`test_fetch_http_failure_raises`** [§17] (cassette of a download error) — `fetch` RAISES `ProviderError` (no error field on the return).
7. **`test_fetch_writes_scratch_guarded`** [§16/rule3] (cassette) — fetch writes only under scratch, sanitized basenames, escape rejected.
8. **`test_key_via_accessor_not_persisted`** [rule5] — key pulled at call time; absent from repr/str/instance attrs.
9. **`test_cassettes_have_no_authorization_header`** [rule5] — every cassette scrubbed.
10. **`test_factory_seam_no_self_registration`** [fp-2] — `IMAGEGEN_PROVIDERS` maps name→class; import self-registers nothing.

`tests/adapters/imagegen/test_silhouette.py`:
11. **`test_silhouette_score_clean_silhouette_high`** — a fixture RGBA image with a clean centered single-component alpha scores ≥ threshold.
12. **`test_silhouette_score_empty_and_fragmented_low`** — fully-transparent / multi-blob fixtures score < threshold.
13. **`test_select_best_picks_highest_above_threshold`** — given N fetched candidate images, returns the highest-scoring one above threshold.
14. **`test_select_best_none_pass_surfaces_failure`** [§17] — all candidates below threshold → the defined failure (Step-2.5 Q3).
15. **`test_silhouette_score_deterministic`** — same bytes → same score (pure function; no wall-clock/random).

`tests/adapters/imagegen/test_imagegen_live_smoke.py`:
16. **`test_live_imagegen_smoke`** — `skipif(not AISIMS_IMAGEGEN_LIVE)` — one real submit→poll→fetch against WaveSpeed.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — the frozen §7 `ImageGenProvider` Protocol + value models are consumed unchanged; no shared-contract-seam model added/extended → **no schema-snapshot test**.
- **Orchestrator doc rows to write hot (Step 9 routing):** an `ARCHITECTURE.md §7` note (real `ImageGenProvider` = `WaveSpeedImageGenProvider` (FLUX.2 [pro]) behind the `adapters/imagegen` factory seam; silhouette gate in `adapters/imagegen/silhouette.py`; the async real-adapter error-channel mapping — submit/fetch raise, poll rides `PollResult.error`). This is the task's "extended (§7)" — an arch prose note, NOT a cross-doc-invariant **table** row (no contract field changed). **Multi-track: routed to the integration owner.**
- **Shared-contract-seam model touched?** No.

> Orchestrator territory (canonical list: `services/pipeline/CLAUDE.md` "must NOT touch"): flag at Step 9 categorized; orchestrator writes hot + commits at `/orchestrate-end`.

## Things to flag at Step 2.5
1. **WaveSpeed FLUX.2 [pro] wire shape — verify via Context7 (wire-fidelity, same as 3.3 Condition A).** Confirm: async submit/poll endpoints vs synchronous; the `transparent_bg` + `seed` param names; auth header; result URL shape + expiry. My default vote: **model as async submit/poll/fetch per the frozen Protocol**; if the API is synchronous, `submit` returns a ref whose first `poll` is immediately SUCCEEDED. Verify before authoring cassettes — a mis-modeled cassette passes the unit test but proves nothing.
2. **Async real-adapter error-channel mapping.** submit-HTTP-fail → raise (no ref); poll job-fail / poll-HTTP-fail → `PollResult.error` (no raise); fetch-HTTP-fail → raise (no paths). My default vote: **exactly that split** — it refines lesson 5 for *real* async adapters (the mock could defer submit-failures to first-poll because it makes no real call; a real submit can fail before any jobId exists). Likely a new lesson.
3. **`select_best` when no candidate passes the gate.** Raise `ProviderError(VALIDATION_FAILED)` vs return `None`/an empty result for the Phase-2 node to handle. My default vote: **raise `ProviderError(VALIDATION_FAILED)`** — the silhouette gate is a deterministic validation gate rejecting output (§17 wording); `select_best` is a sync helper, so raising matches the sync channel. The Phase-2 node decides regenerate-vs-fail. Confirm or pick the return-shape.
4. **rembg + the alternate backends (Replicate / fal / OpenRouter) — sequence to a 3.2-continuation slice.** WaveSpeed FLUX.2 [pro] returns `transparent_bg` natively, so rembg (background-removal fallback) is only needed for backends that don't — i.e. the alternates, which this slice doesn't add. My default vote: **defer rembg + the alternates to a 3.2-continuation slice** (this is slice-sequencing, not a scope cut — I'll record them as carry-forward with come-back markers, never dropped). Push back if you want WaveSpeed + one alternate bundled now.
5. **Image lib for silhouette scoring.** Pillow + numpy (alpha-channel coverage + connected-component count) vs opencv. My default vote: **Pillow + numpy** — lighter, sufficient for an alpha-channel silhouette metric; opencv is a heavy dep to avoid unless the metric needs it.

## Dependencies + sequencing
- **Depends on:** 0.5a (frozen §7 — landed), 3.3 (the real-adapter foundation: `adapters/errors.py`, key-pull, cassette pattern, factory seam — landed `e46df25`/`1a437cd`).
- **Blocks:** 3.4 (provider-output validation reuses the fetch scratch path + cost/latency); 3.1 image-to-3D (S2-blocked) will reuse the async submit/poll/fetch base + scratch-guard this slice establishes.

## Estimated commit count
**2.**
- **C1** — `WaveSpeedImageGenProvider` (submit/poll/fetch, async error-channel mapping, transparent_bg + pinned seed, scratch-guarded fetch, key-pull, cassettes, factory seam). **Touches safety rule 5** (keys) + rule-3 scratch-guard → its own commit; **security-reviewer fires** (Step-8 policy `invariant`).
- **C2** — `silhouette.py` (`silhouette_score` + `select_best`) + tests. Pure-deterministic image scoring; no live calls, no safety invariant.

`code-quality-reviewer` runs every-slice. If C1's async submit/poll/fetch wants a shared `_base` that 3.1 will reuse, that's fine inside C1 — don't pre-build 3.1's image3d specifics (S2-blocked).

## Lessons-logged candidates anticipated
- **Convention candidate** — "Real ASYNC adapters split the error channel three ways: submit/fetch RAISE `ProviderError` (no result error field), but poll rides `PollResult.error` — the real-adapter refinement of lesson 5 (the mock defers submit-failures to first-poll; a real submit can't)." (extends the LESSONS-9 recipe)
- **Architecture-doc note candidate** — `ARCHITECTURE.md §7`: real `ImageGenProvider` = WaveSpeed FLUX.2 [pro] behind the `adapters/imagegen` seam; silhouette gate is a deterministic concept-stage quality gate.
- **Future TODO — Phase-3 continuation** — rembg fallback + the Replicate/fal/OpenRouter alternate backends (bakeoff breadth, EVAL-002); the resumable N-candidate generation loop is Phase-2.
