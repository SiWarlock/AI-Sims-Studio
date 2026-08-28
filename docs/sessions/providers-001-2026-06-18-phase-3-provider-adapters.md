# providers-001 — Phase 3 real provider adapters (LLM + concept-image + §16 + cost + fal)

- **Date:** 2026-06-18
- **Phase / Track:** Phase 3 (Provider adapters + bakeoffs) · track `providers` · area `services/pipeline/adapters`
- **Predecessor:** `docs/sessions/contract-004-2026-06-17-services-pipeline-phase0-tail.md` (Phase-0 seal — froze the §7/§17 contracts this round builds on; the `providers` track forked off `origin/track/contract`)
- **Successor:** _TBD_
- **Branch:** `track/providers` · **Round commits:** `e46df25` `1a437cd` · `cf34267` `51aaf38` `7709171` · `4aba4d6` `a69b689` · `4697b2d` `2ceb139` · `6ed415b`

## Why this session existed

Phase 0 froze the §7 provider interfaces (`LLMProvider` / `ImageGenProvider` / `Image3DProvider` Protocols + `ProviderJobRef`/`PollResult`/`ProviderUsage`) and shipped the mock adapters. Phase 3's job: stand up the **real** provider adapters behind those frozen seams, model-agnostic, with deterministic harnessing (recorded cassettes + env-gated live smoke), provider-output validation, and cost/latency capture. This session delivered the LLM backend, the concept-image backend + silhouette gate, the §16 trust-boundary hardening, cost capture, and a second image-gen backend (fal) — establishing the shared real-adapter foundation the rest of Phase 3 (and 3.1) reuse.

## What was built

Five slices (tasks 3.3, 3.2, 3.4a, 3.4b, 3.2-cont), test-first throughout. Cassettes are **recorded-cassette (vcr) Option A** — synthesized from Context7-verified wire shapes (no live keys), replayed offline; secret-scrubbed; env-gated live smokes skipped without keys.

### Files created
- `adapters/errors.py` — neutral `ProviderError` (hoisted from `mock/failure.py`) + `classify(status)→ErrorCode` + `build_envelope(code, *, maintainer_detail)` (§17 category/retryable). [3.3 C1; extended in 3.4a with `VALIDATION_FAILED`]
- `adapters/_http.py` — **secret-free** shared HTTP transport: `open_client`, `request_json`/`post_json`, `get_bytes` (SSRF + streaming byte-cap, added 3.4a). Reused by every real adapter family. [3.2 C0 hoist + 3.4a hardening]
- `adapters/llm/{__init__,_base,anthropic,openrouter}.py` — `LLMProvider` backends (Claude direct + OpenRouter, raw httpx), `LLM_PROVIDERS` factory seam, `extract_and_validate`/`extract_text`. [3.3 C2]
- `adapters/imagegen/{__init__,_base,wavespeed,silhouette}.py` — `WaveSpeedImageGenProvider` (FLUX.2 [pro], async submit/poll/fetch), `safe_scratch_path` scratch-guard, deterministic silhouette gate (`silhouette_score`/`select_best`→`SilhouetteSelection`), `IMAGEGEN_PROVIDERS` factory seam. [3.2 C1/C2]
- `adapters/imagegen/fal.py` — `FalImageGenProvider` (fal queue API, two-GET completion). [3.2-cont]
- `adapters/validation.py` — §16 provider-output content validation (`ContentKind` magic-byte map + `validate_content` + `enforce_candidate_count`). [3.4a C1]
- `adapters/pricing.py` — §7 per-op cost: per-model price table + `estimate_cost` (actual→table→None). [3.4b C1]
- Tests: `tests/adapters/llm/{test_errors,test_llm_adapters,test_llm_live_smoke,conftest}.py`; `tests/adapters/imagegen/{test_wavespeed,test_silhouette,test_imagegen_live_smoke,test_fal,conftest}.py`; `tests/adapters/{test_validation,test_http_hardening,test_pricing}.py` + committed scrubbed cassettes under `tests/adapters/{llm,imagegen}/cassettes/`.

### Files modified
- `adapters/mock/failure.py` — re-imports the hoisted `ProviderError` from `adapters/errors.py` (mock surface unchanged). [3.3]
- `adapters/llm/{_base,anthropic,openrouter}.py` — re-pointed HTTP primitives to `adapters/_http.py`. [3.2 C0]
- `adapters/errors.py` — `+ VALIDATION_FAILED → (VALIDATION, not-retryable)` in `_CLASSIFICATION`. [3.4a]
- `adapters/imagegen/wavespeed.py` — `fetch` wired to the §16 `get_bytes`/`validate_content`/scratch-guard + `max_bytes`/`max_candidates`/`allowed_hosts`/`resolver` params [3.4a]; `costCents` on the SUCCEEDED poll via `usage.model_copy` [3.4b].
- `adapters/imagegen/__init__.py` — registered `fal`. `adapters/pricing.py` — `+ fal FLUX row`. [3.2-cont]
- `services/pipeline/pyproject.toml` (+`httpx`, +`pillow`/`numpy`) + root `pyproject.toml` (+`vcrpy` dev) + `uv.lock`.

## Decisions made
- **Raw httpx over provider SDKs** (LLM + both image backends) — thin one-shot/queue seams, cassette wire-fidelity under our control (no SDK-version coupling), fewer deps, sidesteps SDK↔vcr interception risk. (3.3, orchestrator-approved over the brief's SDK default.)
- **Secret-free shared transport** (`adapters/_http.py`) — the `SecretsAccessor` key-pull + auth-header injection stay at each adapter; the rule-5 chokepoint does NOT migrate into shared code. (3.2 [B].)
- **§16 error-code SPLIT** (3.4a [Q1], approved over the brief's all-`VALIDATION_FAILED` default): content problems (empty/wrong-magic/oversized) → `MALFORMED_OUTPUT` (retryable — repair loop regenerates); SSRF/policy/count-cap → `VALIDATION_FAILED` (not-retryable). The retryable posture matches reality.
- **SSRF floor = reject `not ip.is_global`, FAIL-CLOSED** (empty/failed resolution → reject) — one check subsuming private/loopback/link-local/reserved/multicast/CGNAT/unspecified; `allowed_hosts` defaults `None` so the IP floor always runs; the resolver is injectable for tests. (3.4a, after a code-quality HIGH caught an empty-resolver fail-open.)
- **Streaming byte-cap** (`get_bytes` uses `client.stream`+`iter_bytes`, raises mid-stream) — a real DoS guard, not a post-hoc `len()`.
- **Three-way async error channel** (real-adapter refinement of Lesson 5/10): `submit`/`fetch` RAISE; `poll` NEVER raises (key-pull + usage parsing + the fal two-GET completion all inside poll's guard).
- **Cost = best-effort estimate** (`actual→table→None`, never fabricated), attributed once on the SUCCEEDED poll; the table is the shared Phase-2/LLM/3.1 source. (3.4b.)
- **fal modeled on the WaveSpeed structure, no shared async base extracted** — fal's two-GET completion diverges enough that a base would be mostly abstract; the genuinely-shared pieces are already shared modules. (3.2-cont [Q3].)

## Decisions explicitly NOT made (deferred — tracked, not cut)
- **rembg background-removal fallback** — DEFERRED to its own continuation slice (lead-approved). fal-FLUX lacks native transparent-bg, but rembg is a heavy `onnxruntime` + ~170MB-model dep and a provider-agnostic FLOW-level helper the Phase-2 concept node applies post-fetch — independent of the fal backend.
- **Replicate + OpenRouter image-gen backends** — further continuation slices (OpenRouter image-gen viability is research-required).
- **SSRF resolve→connect TOCTOU** (httpx re-resolves at connect) — Phase-2 transport-level IP pinning; documented in `_http.py`, security-reviewer-acked.
- **Cost reconciliation + table tuning** — the rough table cents + a billing-API reconcile (e.g. WaveSpeed `/predictions` billing endpoint via the `actual` path; validate `actual>=0`) are Phase-2/3.4b-budget-config.
- **LLM node-level cost + run-rollup/soft-budget** (REQ-NF-103) — Phase-2 (the frozen `LLMProvider` returns no token counts).
- **Mesh `ContentKind`s (GLB/GLTF)** + image3d fetch wiring — 3.1.

## TDD compliance
**Clean.** Every slice followed RED → Step-2.5 review → GREEN strictly; no implementation landed before its test. Cassette content (authored at GREEN) is test data, not behavior. No safety-critical code skipped TDD.

## Reachability (per each slice's Step 7.5)
- **No live graph-node call path this round** — production provider *selection* is Phase-2. Each adapter is reachable via its factory seam: `LLM_PROVIDERS` / `IMAGEGEN_PROVIDERS["wavespeed"|"fal"]` (analogues of the 0.8 `MOCK_PROVIDERS` seam) + the env-gated live smokes (real-call proof / cassette-refresh source).
- `adapters/_http.py` + `adapters/errors.py` are shared transport/error modules reached by every adapter; `adapters/validation.py` + `safe_scratch_path` reached via each `fetch`; `adapters/pricing.py` via the SUCCEEDED poll; the silhouette gate via the (Phase-2) concept flow over fetched candidates.
- **No tested-but-unwired gap introduced** — the phase-exit reachability audit covers the cross-phase Phase-2 node-wiring gap (stated at each Step 7.5).

## Open follow-ups (Step-9 categorized — routed hot to the orchestrator during the session)
- **Architecture-doc NOTES (§7/§16/§17)** — orchestrator writes hot / queues for the integration merge: real `LLMProvider` (2 backends) + `ImageGenProvider` (wavespeed + fal, queue two-GET) behind the factory seams; `ProviderError` in neutral `adapters/errors.py`; §16 validation in `adapters/validation.py` + SSRF/streaming-cap in `_http.py::get_bytes`; cost estimate via `adapters/pricing.py`. (No cross-doc-invariant **table** row — no contract model field changed.)
- **LESSONS** (orchestrator wrote/folding): §9 real-adapter recipe; §10 three-way async error channel; §11 §16 validation (error split + fail-closed `not is_global` floor); cost convention folded into §9.
- **fal cassette re-record (live-smoke)** — the fal cassettes are Context7-SYNTHESIZED; before fal is production-trusted, the env-gated live smoke must validate: `metrics.inference_time` location (status vs result response), the result-URL form (`/requests/{id}` vs `/response`), and whether fal png output carries alpha (informs the rembg need).
- **Deploy/packaging** — rembg `onnxruntime` + model-download weight (bundle vs first-run-fetch) when rembg lands.
- **Phase-2** — provider selection + resumable N-candidate submit/poll/fetch loop (needs a max-poll-attempts cap, bounding the unknown-status→RUNNING fallback); run-rollup→soft-budget (REQ-NF-103); LLM node-level cost; SSRF TOCTOU IP-pinning; cost reconciliation.
- **3.1 image-to-3D (S2-blocked)** — reuses `_http`/errors/validation/pricing/scratch-guard + the fal queue HTTP/auth pattern.

## How to use what was built
A new real provider backend = mirror `adapters/imagegen/wavespeed.py` (or `fal.py` for a queue API): pull the key via `SecretsAccessor` at call time, build the request body in a pure `build_submit_body`, use `adapters/_http.py` for transport, `adapters/errors.py::classify`/`build_envelope` for errors, `validate_content` + `get_bytes` + `safe_scratch_path` for §16-safe fetch, `estimate_cost` for cost on the SUCCEEDED poll; register it in the area factory seam; `submit`/`fetch` RAISE, `poll` never raises. Tests: vcr cassettes (scrubbed) + an env-gated live smoke.
