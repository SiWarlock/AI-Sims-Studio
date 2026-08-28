# /tdd brief — concept_image_fal_backend_plus_rembg

## Feature
The first 3.2-continuation slice: a second real `ImageGenProvider` backend — **fal** (FLUX) — behind the frozen §7 seam, plus the **rembg background-removal fallback** for a backend that doesn't return a transparent background natively. Bakeoff breadth (EVAL-002) on the now-established adapter foundation. (Replicate + OpenRouter alternates are sequenced as further continuation slices — see Dependencies.)

## Use case + traceability
- **Task ID:** 3.2 (continuation — the alternate-backends + rembg part of task 3.2; the WaveSpeed default + silhouette gate landed in the first 3.2 slice)
- **Architecture sections it implements:** `ARCHITECTURE.md §7` (ImageGenProvider seam — "WaveSpeed default + Replicate/**fal**/OpenRouter alternates; **rembg fallback**"), §16 (the fetch reuses the hardened `get_bytes`/`validation.py` path), §17 (async error channel — submit/fetch RAISE, poll rides `PollResult.error`).
- **Related context:**
  - **Established foundation/patterns** (reuse, do NOT re-derive): `adapters/_http.py` (secret-free transport), `adapters/errors.py` (classifier), `adapters/validation.py` (§16 content/SSRF), `adapters/pricing.py` (cost), the `adapters/imagegen` factory seam (`IMAGEGEN_PROVIDERS`), `adapters/imagegen/wavespeed.py` (the backend pattern to mirror), `adapters/imagegen/_base.py` (`safe_scratch_path`), `adapters/imagegen/silhouette.py` (the gate the fetched candidates feed). LESSONS 9 (recipe), 10 (3-way async error channel), 11 (§16 validation).
  - **Test strategy (locked, track-wide):** Option A — recorded cassettes (record-once, scrubbed) + env-gated live smoke. Same Context7 wire-fidelity rule as prior slices.
  - **fal is dual-purpose:** it's also an image-to-3D backend for 3.1 — the fal HTTP/auth pattern this slice establishes is reused there.
- **Implements:** EVAL-002 (bakeoff breadth).

## Acceptance criteria (what "done" means)
- [ ] `FalImageGenProvider` structurally conforms to the frozen `ImageGenProvider` Protocol (assignable; submit/poll/fetch callable) — parity with the mock + WaveSpeed.
- [ ] `submit`/`poll`/`fetch` follow the §17 three-way async error channel (submit/fetch RAISE `ProviderError`; poll rides `PollResult.error`, never raises — key-pull + usage parsing INSIDE poll's guard, per LESSONS 10).
- [ ] Keys pulled via `SecretsAccessor` at call time (rule 5); fetch reuses the hardened `get_bytes` (byte-cap + SSRF, default `allowed_hosts=None`) + `validate_content` (image kinds) + `safe_scratch_path` — the §16 path is NOT re-implemented.
- [ ] `usage.costCents` populated on the SUCCEEDED poll via `estimate_cost` (the fal FLUX model added to the `pricing.py` table) alongside `latencyMs`.
- [ ] `FalImageGenProvider` registered in the `adapters/imagegen` factory seam (`IMAGEGEN_PROVIDERS`); nothing self-registers on import (forbidden-pattern 2).
- [ ] **rembg fallback** (conditional — see Step-2.5 Q2): a provider-agnostic `remove_background(image_bytes)→bytes` that produces a transparent-bg image, applied when a backend's output lacks an alpha channel; the silhouette gate then scores the cleaned image. (If Context7 confirms fal-FLUX returns transparent bg natively, rembg defers — see Q2.)
- [ ] All unit tests in `services/pipeline/tests/adapters/imagegen/` for fal (+ rembg if in-scope) pass; existing WaveSpeed/silhouette/validation/pricing + LLM tests stay green.
- [ ] `/preflight` clean.

## Wiring / entry point (Step 7.5)
Same posture as the WaveSpeed slice: `FalImageGenProvider` is reachable via the `adapters/imagegen` factory seam (`IMAGEGEN_PROVIDERS["fal"]`) + the env-gated live smoke; rembg is a provider-agnostic helper the concept flow calls post-fetch. No new graph node — production selection / the bakeoff harness wiring is Phase-2 / `evals`. State exactly this at Step 7.5.

## Files expected to touch
**New:**
- `services/pipeline/adapters/imagegen/fal.py` — `FalImageGenProvider`.
- `services/pipeline/adapters/imagegen/background.py` — `remove_background` (rembg fallback) *(if in-scope per Q2)*.
- `services/pipeline/tests/adapters/imagegen/test_fal.py` + `cassettes/*.yaml`.
- `services/pipeline/tests/adapters/imagegen/test_background.py` *(if rembg in-scope)*.

**Modified:**
- `services/pipeline/adapters/imagegen/__init__.py` — register `fal` in `IMAGEGEN_PROVIDERS`.
- `services/pipeline/adapters/imagegen/_base.py` — *(optional)* extract a shared async submit/poll/fetch base from wavespeed if the overlap is clean (Q3); 3.1 image3d may reuse it.
- `services/pipeline/adapters/pricing.py` — add the fal FLUX model to the price table.
- `services/pipeline/pyproject.toml` — add `rembg` (+ its runtime deps) *(if in-scope; flag the dep weight — Q2)*.

If implementation needs files beyond this list, **flag at Step 2.5** before GREEN.

## RED test outline (Step 2)
`tests/adapters/imagegen/test_fal.py`:
1. **`test_fal_conforms_to_imagegenprovider_protocol`** [§7] — assignable to `ImageGenProvider`; submit/poll/fetch callable.
2. **`test_fal_submit_returns_jobref`** [§7] (cassette) — submit sends the prompt + params and returns a well-formed `ProviderJobRef`.
3. **`test_fal_poll_pending_then_succeeded`** [§7] (cassette) — SUBMITTED/RUNNING(progress) → SUCCEEDED(urls + usage.latencyMs + costCents).
4. **`test_fal_poll_job_failure_rides_pollresult_error`** [§17] (cassette) — job failure → `PollResult(FAILED, error)`; does NOT raise.
5. **`test_fal_submit_http_failure_raises`** [§17] (cassette 401) — submit RAISES `ProviderError(PROVIDER_AUTH_QUOTA)`.
6. **`test_fal_fetch_scratch_guarded_and_validated`** [§16] (cassette) — fetch reuses the hardened path (scratch-guarded, content-validated); a wrong-magic body raises.
7. **`test_fal_key_via_accessor_not_persisted`** [rule5] — key at call time; absent from repr/str/attrs.
8. **`test_fal_cassettes_have_no_authorization_header`** [rule5] — scrubbed.
9. **`test_fal_in_factory_seam`** [fp-2] — `IMAGEGEN_PROVIDERS["fal"]` resolves the class; no self-registration.
10. **`test_fal_live_smoke`** — `skipif(not AISIMS_IMAGEGEN_LIVE)`.

`tests/adapters/imagegen/test_background.py` *(if rembg in-scope)*:
11. **`test_remove_background_produces_transparent`** — an opaque fixture → an RGBA output with a transparent background (alpha present).
12. **`test_remove_background_idempotent_on_transparent`** — an already-transparent image is unchanged / safe.
13. **`test_silhouette_scores_higher_after_rembg`** — a rembg-cleaned image scores higher on the silhouette gate than its opaque original (the fallback's purpose).

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — frozen §7 `ImageGenProvider` consumed unchanged; no shared-contract-seam model added → **no schema-snapshot**.
- **Orchestrator doc rows to write hot (Step 9 routing):** an `ARCHITECTURE.md §7` note (real `ImageGenProvider` now has a fal backend behind the seam; rembg fallback realized in `adapters/imagegen/background.py`). **Multi-track: queued for the integration merge.** No cross-doc-invariant table row.
- **Shared-contract-seam model touched?** No.

> Orchestrator territory (`services/pipeline/CLAUDE.md` "must NOT touch"): flag at Step 9 categorized; orchestrator writes hot + commits at `/orchestrate-end`.

## Things to flag at Step 2.5
1. **fal FLUX image-gen wire shape — verify via Context7 (wire-fidelity).** Confirm: the fal queue submit/status/result endpoints, the param names (prompt, image_size, seed), auth header, result url shape. Model as async submit/poll/fetch per the Protocol; if fal's API is sync/queue-immediate, `submit` returns a ref whose first poll resolves. Verify before authoring cassettes.
2. **Does fal-FLUX return a transparent background natively? → rembg scope.** My default vote: **verify via Context7.** If fal-FLUX supports a transparent-bg/alpha output, rembg DEFERS to a further continuation slice (and this slice is fal-only). If NOT, rembg is in-scope here (fal output without a clean alpha fails the silhouette gate). Either way: rembg is a **heavy dep** (onnxruntime + a model download) with a packaging implication — flag it as a deploy/packaging carry-forward regardless.
3. **Shared async base extraction.** Extract a shared imagegen async submit/poll/fetch base (wavespeed + fal), or keep each backend self-contained? My default vote: **extract only if the overlap is genuinely clean** (the lifecycle is shared; the API parsing differs per backend) — a shared `_base` that 3.1 image3d also reuses is the extensible win, but don't force it if the backends diverge enough that a base is mostly abstract. Keep WaveSpeed green either way.
4. **rembg integration point.** Applied where — inside each backend's fetch, or as a post-fetch step in the (Phase-2) concept flow? My default vote: **a standalone `remove_background` helper** the concept flow calls when a candidate lacks alpha — NOT inside the backend (keeps the backend a thin §7 adapter; rembg is a flow-level fallback). The Phase-2 concept node wires it; this slice ships the helper + its tests.
5. **Replicate + OpenRouter sequencing.** My default vote: **defer both to further continuation slices** — and OpenRouter image-gen is research-required (verify it supports image-gen at all before committing a backend). This slice = fal (+ rembg per Q2).

## Dependencies + sequencing
- **Depends on:** the first 3.2 slice (foundation + imagegen seam + silhouette gate — landed) + 3.3/3.4 (the `_http`/errors/validation/pricing foundation — landed).
- **Blocks:** the EVAL-002 bakeoff (needs ≥2 backends); 3.1 image-to-3D (S2-blocked) reuses the fal HTTP/auth pattern.
- **Sequenced after this:** Replicate + OpenRouter(research-gated) alternate backends; rembg if deferred per Q2.

## Estimated commit count
**2–3.**
- **C1** — `FalImageGenProvider` + factory registration + pricing-table row + cassettes + tests. **Touches rule 5** (keys) → its own commit; **security-reviewer fires** (`invariant` policy).
- **C2** — rembg `remove_background` helper + tests (+ the `pyproject` dep) *(if in-scope per Q2; else this slice is C1 only + a deferral note)*.
- **(optional C0)** — `refactor` extract the shared async base (Q3), before C1, if done.

`code-quality-reviewer` every-slice. Keep WaveSpeed + silhouette + validation tests green throughout.

## Lessons-logged candidates anticipated
- **Convention candidate** — likely none new (this slice exercises the established LESSONS 9/10/11 recipe across a second backend — a good confirmation the foundation generalizes; flag if the fal API forces a deviation from the recipe).
- **Architecture-doc note candidate** — `ARCHITECTURE.md §7`: the fal ImageGenProvider backend + the rembg fallback realization.
- **Future TODO — deploy/packaging** — rembg's onnxruntime + model-download weight (bundle/first-run-fetch decision).
- **Future TODO — 3.2-continuation** — Replicate backend; OpenRouter image-gen viability (research-required) then backend.
