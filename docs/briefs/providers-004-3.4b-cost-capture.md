# /tdd brief — provider_cost_capture

## Feature
The cost half of task 3.4 (**3.4b**): a provider-agnostic per-model **price table** + best-effort cost estimate, wired to populate `ProviderUsage.costCents` on the imagegen SUCCEEDED poll (latency is already captured in 3.2). Completes the §7 "results carry cost+latency" contract for the landed async adapter.

## Use case + traceability
- **Task ID:** 3.4b (the cost half of 3.4 — the §16 validation half landed as 3.4a)
- **Architecture sections it implements:** `ARCHITECTURE.md §7` — "Results carry **cost+latency** (latency MUST be recorded for every cloud op; **cost SHOULD, with a per-model price-table estimate fallback** from the budget config)." The `ProviderUsage{latencyMs, costCents}` value model is the frozen carrier.
- **Related context:**
  - The frozen `ProviderUsage` (`packages/contracts/.../providers.py`): `latencyMs: int` (required) + `costCents: int | None` (nullable — the estimate fallback). Consumed unchanged; `costCents` is an existing field this slice now populates.
  - The wiring target: `adapters/imagegen/wavespeed.py::_usage` already sets `latencyMs` from `data.timings.inference` (defensive, never raises — lesson 10) and leaves `costCents=None`. This slice fills `costCents`.
  - Foundation reused: `adapters/errors.py`, `adapters/_http.py`, `adapters/validation.py` (siblings; the new `pricing.py` joins them). LESSONS 9/10/11.
- **Implements:** REQ-NF-103 (cost data — the per-op estimate; the run-rollup → soft-budget warning is Phase-2).

## Acceptance criteria (what "done" means)
- [ ] `adapters/pricing.py` — a typed per-model price table keyed by `(provider, model)` → estimated cents-per-op + `estimate_cost(provider, model, *, actual=None)` → `int | None`: returns the provider-reported `actual` cost when present, else the table estimate, else `None` (best-effort — an unknown model yields `None`, never a fabricated guess).
- [ ] The table seeds the landed default models (imagegen FLUX.2 [pro]; the LLM Claude-class + OpenRouter defaults) and is **extensible** (one row per model; the Phase-2 LLM/run-rollup node + 3.1 image3d consume the same table).
- [ ] `WaveSpeedImageGenProvider` populates `usage.costCents` on the **SUCCEEDED** poll only (cost is attributed once to the completed generation, not per intermediate poll) — alongside the existing `latencyMs`.
- [ ] `costCents` population is **defensive** (mirrors `_usage`): an unknown model / missing price → `costCents=None`, never a raise (poll rides the result — lesson 10).
- [ ] All unit tests in `services/pipeline/tests/adapters/` for pricing + the imagegen cost wiring pass; existing LLM + imagegen + validation tests stay green.
- [ ] `/preflight` clean.

## Wiring / entry point (Step 7.5)
The cost estimate wires into `WaveSpeedImageGenProvider.poll` → the SUCCEEDED `PollResult.usage.costCents` — a live path in the landed adapter, reachable via the `adapters/imagegen` factory seam + the env-gated live smoke. The price table is also the source the **Phase-2** run-rollup / soft-budget node (REQ-NF-103) and the LLM node (LLM cost is node-level per §7) consume — those wirings are Phase-2, not here. No new graph node. State exactly this at Step 7.5.

## Files expected to touch
**New:**
- `services/pipeline/adapters/pricing.py` — the price table + `estimate_cost`.
- `services/pipeline/tests/adapters/test_pricing.py` — table/estimate unit tests.

**Modified:**
- `services/pipeline/adapters/imagegen/wavespeed.py` — populate `costCents` on the SUCCEEDED poll's `usage`.
- `services/pipeline/tests/adapters/imagegen/test_wavespeed.py` — assert `costCents` populated on success; pending polls attribute no cost.

If implementation needs files beyond this list, **flag at Step 2.5** before GREEN.

## RED test outline (Step 2)
`tests/adapters/test_pricing.py`:
1. **`test_estimate_cost_known_model_returns_table_estimate`** [§7] — a seeded `(provider, model)` → the table's cents.
2. **`test_estimate_cost_unknown_model_returns_none`** [§7] — an unknown model → `None` (best-effort, no fabricated guess).
3. **`test_estimate_cost_prefers_actual_over_estimate`** [§7] — when an `actual` cost is supplied, it wins over the table estimate.
4. **`test_price_table_covers_landed_defaults`** [§7] — the table includes the imagegen FLUX.2 [pro] default + the LLM defaults (so Phase-2's node has them).

`tests/adapters/imagegen/test_wavespeed.py` (additions):
5. **`test_poll_succeeded_populates_cost_and_latency`** [§7] (cassette) — a SUCCEEDED poll's `usage` carries BOTH `latencyMs` (existing) and `costCents` (new estimate).
6. **`test_poll_pending_attributes_no_cost`** [§7] (cassette) — a pending poll attributes no cost (usage None or `costCents` unset — cost is once, on success).
7. **`test_poll_succeeded_unknown_model_cost_none_no_raise`** [§7] (cassette, unknown model param) — an unknown model → `costCents=None`, poll does not raise (defensive, lesson 10).

## Cross-doc invariant impact (implementer flags at Step 9; orchestrator writes the docs)
- **Model field changes:** none — `ProviderUsage.costCents` is an existing frozen field now populated; no contract model added/extended → **no schema-snapshot test**.
- **Orchestrator doc rows to write hot (Step 9 routing):** an `ARCHITECTURE.md §7` note (the cost estimate is realized via `adapters/pricing.py`; the price table seeds the landed models and is the Phase-2 run-rollup / LLM-node source). **Multi-track: queued for the integration merge.** No cross-doc-invariant table row.
- **Shared-contract-seam model touched?** No.

> Orchestrator territory (canonical list: `services/pipeline/CLAUDE.md` "must NOT touch"): flag at Step 9 categorized; orchestrator writes hot + commits at `/orchestrate-end`.

## Things to flag at Step 2.5
1. **Price-table location/format.** A module-level typed table in `pricing.py` vs a config-file loader. My default vote: **a module-level typed table now** (a `dict[(provider, model), int]` with a clear "estimate, in cents" contract) — the config-file/budget loader is Phase-2 budget config; don't pre-build it here.
2. **Actual-vs-estimate precedence + does WaveSpeed return a cost field?** My default vote: **actual-if-present → table estimate → None.** Verify via Context7 whether the WaveSpeed v3 result carries a cost/billing field; if it doesn't, imagegen always uses the table estimate (the `actual` path is still tested for the Phase-2/other providers that do report cost).
3. **Which models seed the table.** My default vote: **the landed defaults** (FLUX.2 [pro]; the Claude-class + OpenRouter LLM defaults) + any alternates you can price confidently; an unknown model → `None` (+ maybe a one-line debug log, never a raise).
4. **Attribute cost on SUCCEEDED only?** My default vote: **yes** — set `costCents` on the SUCCEEDED `PollResult.usage` (cost is the completed generation's, once), not on intermediate polls.
5. **LLM cost stays node-level (Phase-2)?** My default vote: **yes** — the frozen `LLMProvider` returns no token counts, so per §7 LLM cost is recorded at the node onto `Step` (Phase-2) using this price table; 3.4b only wires the async imagegen `costCents`. image3d cost folds in at 3.1.

## Dependencies + sequencing
- **Depends on:** 3.2 (`wavespeed.py::_usage` / poll — landed), 3.3 (foundation).
- **Blocks:** Phase-2 run-rollup → soft-budget warning (REQ-NF-103); 3.1 image3d cost wiring reuses `pricing.py`.
- This closes task 3.4 (3.4a §16 + 3.4b cost/latency).

## Estimated commit count
**1–2.** No safety invariant (cost is observability/budget, not a trust boundary) → **security-reviewer does NOT fire**; `code-quality-reviewer` every-slice.
- **C1** — `adapters/pricing.py` (table + `estimate_cost`) + tests. Pure, deterministic.
- **C2** — the imagegen `costCents` wiring + tests. (Fold into one commit if small.)

## Lessons-logged candidates anticipated
- **Convention candidate** — "per-op cost is a best-effort `adapters/pricing.py` estimate (actual-if-reported → table → None, never a fabricated guess), attributed once on the SUCCEEDED poll alongside latency; the price table is the single source the Phase-2 run-rollup + LLM node share." (likely folds into the LESSONS 9/11 adapter recipe rather than a new lesson)
- **Architecture-doc note candidate** — `ARCHITECTURE.md §7`: cost estimate realized via `adapters/pricing.py`; the run-rollup → soft-budget warning is Phase-2.
- **Future TODO — Phase-2** — run-rollup of per-op cost → soft-budget warning (REQ-NF-103); the LLM-node cost wiring (token-based) using this table.
