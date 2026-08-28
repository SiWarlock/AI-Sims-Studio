"""RED — §7 per-op cost estimate (provider-agnostic price table). Pure/deterministic, no I/O.

estimate_cost prefers a provider-reported actual cost, falls back to the per-model table estimate,
and yields None for an unknown model — never a fabricated guess. The table seeds the landed default
models so the Phase-2 run-rollup / LLM node + 3.1 image3d consume the same source.
"""

from __future__ import annotations

# the landed default models the table must price (Step-2.5 Q3).
_FLUX = ("wavespeed", "wavespeed-ai/flux-2-pro/text-to-image")
_CLAUDE = ("anthropic", "claude-sonnet-4")
_OPENROUTER = ("openrouter", "anthropic/claude-sonnet-4")


def test_estimate_cost_known_model_returns_table_estimate() -> None:
    """spec(§7) — a seeded (provider, model) yields the table's non-negative cents estimate."""
    from adapters.pricing import estimate_cost

    cost = estimate_cost(*_FLUX)
    assert isinstance(cost, int)
    assert cost >= 0


def test_estimate_cost_unknown_model_returns_none() -> None:
    """spec(§7) — an unknown model yields None (best-effort; never a fabricated guess)."""
    from adapters.pricing import estimate_cost

    assert estimate_cost("wavespeed", "nope/not-a-real-model") is None


def test_estimate_cost_prefers_actual_over_estimate() -> None:
    """spec(§7) — a provider-reported actual cost wins over the table estimate (and prices an
    otherwise-unknown model)."""
    from adapters.pricing import estimate_cost

    assert estimate_cost(*_FLUX, actual=999) == 999
    assert estimate_cost("other", "unknown/model", actual=42) == 42


def test_price_table_covers_landed_defaults() -> None:
    """spec(§7) — the table prices the landed defaults (imagegen FLUX.2 [pro] + the LLM defaults) so
    the Phase-2 node has them."""
    from adapters.pricing import estimate_cost

    for provider, model in (_FLUX, _CLAUDE, _OPENROUTER):
        assert estimate_cost(provider, model) is not None
