# /tdd brief — provider_output_validation

## Feature
The §16 provider-output trust-boundary validation: a provider-agnostic validation module (magic-byte / content-type + candidate-count cap) plus an SSRF/redirect-hardened **streaming** byte download in the shared transport, wired into the imagegen fetch path. (This is **3.4a** — the §16 security half of task 3.4; the cost/latency capture half is sequenced as 3.4b — see Dependencies.)

## Use case + traceability
- **Task ID:** 3.4 (the §16 half — 3.4a)
- **Architecture sections it implements:** `ARCHITECTURE.md §16` (sidecar↔cloud trust boundary — **provider-output validation: bytes cap, magic-byte/content-type, path sanitize — before persisting/feeding Blender; deterministic validation gate before any state write**), §17 (violations surface as a classified `ErrorEnvelope`), §7 (the fetch path being hardened).
- **Related context:**
  - The hardening target: `adapters/_http.py::get_bytes` (landed 3.2 C0 — its docstring explicitly defers "the §16 byte-cap / magic-byte hardening lands in 3.4") + `adapters/imagegen/wavespeed.py::fetch` (downloads provider-returned CDN urls into scratch via `safe_scratch_path`).
  - Foundation reused: `adapters/errors.py` (`ProviderError`, `build_envelope`, `classify`), `adapters/_http.py` (the shared secret-free transport). See LESSONS 9 (real-adapter recipe) + LESSONS 10 (async error channel — **fetch RAISES**, no result error field).
  - Security context: the 3.2 security-reviewer flagged byte-cap + **SSRF/redirect guard** + candidate-count cap as the §16 forward-scope this slice now closes.
- *(Cost/latency `Implements: REQ-NF-103` is the 3.4b half, not this slice.)*

## Acceptance criteria (what "done" means)
- [ ] `adapters/validation.py` — a provider-agnostic `validate_content(data, *, allowed: set[ContentKind])` raises `ProviderError` on a magic-byte/content-type mismatch and passes on a match; a `ContentKind` enum + signature map covers the image kinds now (PNG / JPEG / WebP) and is **extensible** (mesh kinds GLB/GLTF added when 3.1 lands — do not hard-close it).
- [ ] `validate_content` rejects an empty body.
- [ ] `get_bytes` enforces a **streaming** `max_bytes` cap — it does NOT buffer the full body before checking; exceeding the cap raises `ProviderError` mid-stream (DoS guard, not a post-hoc `len()` check).
- [ ] `get_bytes` enforces an **SSRF guard**: https-only scheme; `follow_redirects=False`; rejects a URL whose host resolves to a private / loopback / link-local IP (the cloud-metadata-endpoint class). Optional `allowed_hosts` param (default permissive over public IPs).
- [ ] A **candidate-count cap** rejects more than `max_candidates` urls before any download.
- [ ] Every §16 violation **RAISES** `ProviderError` (fetch has no result error field — LESSONS 10) with the agreed §17 code (Step-2.5 Q1).
- [ ] `WaveSpeedImageGenProvider.fetch` wires the validation (image content-kinds + the caps); the existing 3.2 happy-path fetch (a valid small image within caps) **still passes** (parity preserved).
- [ ] image3d fetch wiring is explicitly **deferred to 3.1** (the validation module is parameterized by content-kind — image3d passes mesh kinds; no image3d code here).
- [ ] All unit tests in `services/pipeline/tests/adapters/` for validation + the hardened download pass; existing LLM + imagegen + mock tests stay green.
- [ ] `/preflight` clean.

## Wiring / entry point (Step 7.5)
The validation wires into `WaveSpeedImageGenProvider.fetch` — a **live path inside the landed adapter**, reachable via the `adapters/imagegen` factory seam + the env-gated live smoke (the §16 module is exercised through `fetch`, not an orphan). The hardened `get_bytes` is shared transport reached by every adapter's download path. No new graph node (production concept-stage wiring is Phase-2). State exactly this at Step 7.5.

## Files expected to touch
**New:**
- `services/pipeline/adapters/validation.py` — `ContentKind` + signature map + `validate_content` + the candidate-count cap helper.
- `services/pipeline/tests/adapters/test_validation.py` — validator unit tests.
- `services/pipeline/tests/adapters/test_http_hardening.py` — streaming-cap + SSRF unit tests (a caller-injected client / mocked resolver; no live network).

**Modified:**
- `services/pipeline/adapters/_http.py` — `get_bytes` gains `max_bytes` (streaming cap) + the SSRF guard (https-only, `follow_redirects=False`, private-IP rejection, optional `allowed_hosts`).
- `services/pipeline/adapters/imagegen/wavespeed.py` — `fetch` passes the caps + image content-kinds + calls `validate_content` on the downloaded bytes.
- `services/pipeline/tests/adapters/imagegen/test_wavespeed.py` — add oversized / wrong-magic / too-many-candidates rejection cases (cassettes as needed); keep the happy-path green.

If implementation needs files beyond this list, **flag at Step 2.5** before GREEN.

## RED test outline (Step 2)
`tests/adapters/test_validation.py`:
1. **`test_validate_content_accepts_image_kinds`** — valid PNG/JPEG/WebP leading bytes pass for `allowed={PNG,JPEG,WEBP}`. Why: §16 content check.
2. **`test_validate_content_rejects_mismatch`** — HTML/text bytes when an image is expected → `ProviderError` (code per Q1). Why: §16 reject wrong content (a swapped/poisoned artifact).
3. **`test_validate_content_rejects_empty`** — empty body → `ProviderError`. Why: §16 degenerate output.
4. **`test_candidate_count_cap`** — > `max_candidates` urls → `ProviderError` before any download. Why: §16 unbounded-fanout guard.

`tests/adapters/test_http_hardening.py`:
5. **`test_get_bytes_streaming_cap_raises_midstream`** — a body exceeding `max_bytes` raises `ProviderError` without buffering the whole body. Why: §16 byte-cap (DoS) — must be streaming, not post-hoc.
6. **`test_get_bytes_rejects_non_https`** — an `http://` url → `ProviderError`. Why: SSRF (scheme).
7. **`test_get_bytes_rejects_private_ip_host`** — a host resolving to loopback/private/link-local → `ProviderError`. Why: SSRF (the cloud-metadata-endpoint class).
8. **`test_get_bytes_does_not_follow_redirects`** — a 3xx is not followed (treated as a `>=400`-class rejection or surfaced, not silently chased). Why: SSRF (redirect pivot).
9. **`test_get_bytes_within_cap_returns_bytes`** — a small body under the cap returns intact. Why: parity (the guard doesn't break the happy path).

`tests/adapters/imagegen/test_wavespeed.py` (additions):
10. **`test_fetch_rejects_oversized`** (cassette) — an oversized download → `ProviderError`. Why: §16 wired into fetch.
11. **`test_fetch_rejects_wrong_magic`** (cassette, non-image body) → `ProviderError`. Why: §16 content check wired into fetch.
12. **`test_fetch_happy_within_caps`** (existing/extended cassette) — a valid small image still fetches to scratch. Why: 3.2 parity preserved.

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — no contract model added/extended; no shared-contract-seam touched → **no schema-snapshot test**.
- **Orchestrator doc rows to write hot (Step 9 routing):** an `ARCHITECTURE.md §16` note (the provider-output validation is realized in `adapters/validation.py` + the SSRF/streaming-cap hardening in the shared `adapters/_http.py::get_bytes`; violations raise `ProviderError`). **Multi-track: queued for the integration owner** (root-doc edits batch at the merge). No cross-doc-invariant **table** row.
- **Shared-contract-seam model touched?** No.

> Orchestrator territory (canonical list: `services/pipeline/CLAUDE.md` "must NOT touch"): flag at Step 9 categorized; orchestrator writes hot + commits at `/orchestrate-end`.

## Things to flag at Step 2.5
1. **Error code for §16 violations** (oversized / wrong-magic / empty / SSRF). My default vote: **`VALIDATION_FAILED` for all §16 rejections** — its frozen meaning is "deterministic validation gate rejected the output before a state write (rule 6)," which is exactly the §16 gate; one consistent code. Alternative: `MALFORMED_OUTPUT` for wrong-magic/oversized (provider returned unusable output) + `VALIDATION_FAILED` for SSRF/policy. Confirm one or the split.
2. **SSRF depth.** My default vote: **https-only + `follow_redirects=False` + private/loopback/link-local-IP rejection** (resolve the host; that's the real metadata-endpoint protection) + an optional `allowed_hosts`. https-only-alone leaves `https://internal-host` reachable. Verify the resolution path stays deterministic under the injected-client/cassette tests (mock the resolver, or use hosts that resolve predictably).
3. **Byte-cap limit source.** My default vote: **a named constant in `validation.py`** (`DEFAULT_MAX_IMAGE_BYTES`, e.g. ~25 MB) + a param override — do NOT pre-build the Phase-2 budget config knob here; that's 3.4b / Phase-2.
4. **Content-kinds this slice supports.** My default vote: **image kinds (PNG/JPEG/WebP) now + an extensible signature map**; mesh kinds (GLB/GLTF) are added when 3.1 lands. Do not hard-close the enum.
5. **Defer cost/latency (the price-table half) to 3.4b?** My default vote: **yes** — latency is already captured (`usage.latencyMs`); the cost price-table + budget config coordinates with Phase-2, so sequence it as 3.4b (carry-forward, NOT a cut). Push back if you want a minimal price-table estimate folded in now.

## Dependencies + sequencing
- **Depends on:** 3.2 (`_http.py::get_bytes` + the imagegen fetch + `safe_scratch_path` — landed `cf34267`/`51aaf38`), `adapters/errors.py` (3.3).
- **Blocks:** 3.1 image-to-3D (S2-blocked) reuses `validation.py` for mesh-output validation; 3.4b (cost/latency capture, REQ-NF-103) builds on the same fetch/usage path.
- **Sequenced after this:** 3.4b cost/latency (price-table estimate + per-op capture) — carry-forward, not dropped.

## Estimated commit count
**2.** Both are §16 trust-boundary work → **security-reviewer fires** (Step-8 policy `invariant`); `code-quality-reviewer` every-slice.
- **C1** — `adapters/validation.py` (`ContentKind` + signature map + `validate_content` + count-cap) + its tests. Pure, deterministic, no network.
- **C2** — `_http.py` streaming byte-cap + SSRF guard + the imagegen `fetch` wiring + tests. **`[SAFETY §16]`** — the trust-boundary download hardening; kept as its own commit.

Keep the happy-path imagegen fetch green throughout (parity). If the SSRF resolver work balloons C2, split the streaming-cap and the SSRF guard into separate commits and flag at Step 7.5.

## Lessons-logged candidates anticipated
- **Convention candidate** — "§16 provider-output validation lives in a provider-agnostic `adapters/validation.py` + a streaming-cap/SSRF-hardened shared `get_bytes`; every fetched artifact is magic-byte + size + SSRF validated before it touches scratch/Blender, and a violation RAISES `ProviderError` (fetch has no error field)."
- **Architecture-doc note candidate** — `ARCHITECTURE.md §16`: the provider-output validation realization (module + hardened transport) + the SSRF private-IP-rejection policy.
- **Future TODO — 3.4b / Phase-2** — cost/latency capture (price-table estimate + per-op cost), the byte-cap config knob, and (3.1) the mesh content-kinds.
