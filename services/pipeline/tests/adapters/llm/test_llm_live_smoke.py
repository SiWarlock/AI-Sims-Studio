"""RED — C2: the env-gated live smoke (Option A's real-call reachability proof + cassette source).

Skipped unless AISIMS_LLM_LIVE=1 and the relevant key is present in the environment (mirrors the
0.7 AISIMS_TEST_DATABASE_URL env-gated store integration pattern). When run with AISIMS_LLM_RECORD
set, the llm_cassette fixture's VCR records, refreshing the committed (scrubbed) cassettes.
"""

from __future__ import annotations

import os

import pytest

from obs.secrets import InMemorySecretsAccessor

_LIVE = os.environ.get("AISIMS_LLM_LIVE") == "1"

# (factory name, key env var, a cheap default model) per backend.
_BACKENDS = [
    ("anthropic", "ANTHROPIC_API_KEY", "claude-sonnet-4"),
    ("openrouter", "OPENROUTER_API_KEY", "anthropic/claude-sonnet-4"),
]


@pytest.mark.skipif(not _LIVE, reason="set AISIMS_LLM_LIVE=1 (+ provider keys) for the live smoke")
@pytest.mark.parametrize(("name", "key_env", "model"), _BACKENDS)
def test_live_complete_smoke(name: str, key_env: str, model: str) -> None:
    """A single real complete() against each backend — proves the real call path end to end."""
    from adapters.llm import LLM_PROVIDERS

    key = os.environ.get(key_env)
    if not key:
        pytest.skip(f"{key_env} not set")

    adapter = LLM_PROVIDERS[name](secrets=InMemorySecretsAccessor({key_env: key}), model=model)
    out = adapter.complete("Reply with the single word: pong", {})
    assert isinstance(out, str)
    assert out.strip()
