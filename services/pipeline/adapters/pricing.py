"""§7 per-op cost estimate — a provider-agnostic per-model price table + best-effort estimate.

Latency MUST be recorded for every cloud op; cost SHOULD, via a per-model price-table estimate
(§7). ``estimate_cost`` prefers a provider-reported ``actual`` cost, falls back to the table, and
yields ``None`` for an unknown model — NEVER a fabricated guess. The table is the single source the
Phase-2 run-rollup / soft-budget node + the LLM node (LLM cost is node-level — the frozen
``LLMProvider`` returns no token counts) + 3.1 image3d share.

The cents are ROUGH per-op ESTIMATES (the §7 contract is "estimate"). Real per-op cost comes from
the Phase-2 budget config / a provider billing API (e.g. WaveSpeed's ``/predictions`` billing
search) — a Phase-2 reconciliation replaces the estimate via the ``actual`` path. The config-file
loader is also Phase-2; this is a deliberately small seeded table.
"""

from __future__ import annotations

# (provider, model) → estimated cost in integer CENTS per op (matches ProviderUsage.costCents).
# One row per landed default model; extend as adapters/models land. ESTIMATES — see the docstring.
_PRICE_TABLE: dict[tuple[str, str], int] = {
    ("wavespeed", "wavespeed-ai/flux-2-pro/text-to-image"): 5,
    ("fal", "fal-ai/flux-pro/v1.1"): 5,
    ("anthropic", "claude-sonnet-4"): 2,
    ("openrouter", "anthropic/claude-sonnet-4"): 2,
}


def estimate_cost(provider: str, model: str, *, actual: int | None = None) -> int | None:
    """Best-effort cents for one op: the provider-reported ``actual`` if present, else the table
    estimate, else ``None`` (unknown model — never fabricate)."""
    if actual is not None:
        return actual
    return _PRICE_TABLE.get((provider, model))
