"""RED — C2: the two real LLM adapters (Claude direct + OpenRouter) behind the frozen §7 seam.

Behavioral, client-agnostic: each test pins a contract (conformance / return shape / sync-raise
classification / re-validation / secrets-at-call-time / scrubbed cassettes / factory seam), never
the HTTP-client internals. Cassette content is authored at GREEN to match the adapter's wire shape.
"""

from __future__ import annotations

from collections.abc import Callable
from contextlib import AbstractContextManager

import pytest
from aisims_contracts.error import ErrorCode
from aisims_contracts.providers import LLMProvider

from obs.secrets import InMemorySecretsAccessor

from .conftest import CASSETTE_DIR, DemoPlan, SpyAccessor

Cassette = Callable[[str], AbstractContextManager[None]]

_EXPECTED_CASSETTES = {
    "anthropic_complete",
    "anthropic_structured",
    "anthropic_malformed",
    "anthropic_429",
    "anthropic_401",
    "openrouter_complete",
    "openrouter_structured",
    "openrouter_malformed",
}


def _anthropic() -> LLMProvider:
    from adapters.llm import AnthropicLLMProvider

    return AnthropicLLMProvider(
        secrets=InMemorySecretsAccessor({"ANTHROPIC_API_KEY": "sk-ant-test-PLACEHOLDER"}),
        model="claude-sonnet-4",
    )


def _openrouter() -> LLMProvider:
    from adapters.llm import OpenRouterLLMProvider

    return OpenRouterLLMProvider(
        secrets=InMemorySecretsAccessor({"OPENROUTER_API_KEY": "sk-or-test-PLACEHOLDER"}),
        model="anthropic/claude-sonnet-4",
    )


def test_adapters_conform_to_llmprovider_protocol() -> None:
    """spec(§7) — both real adapters structurally satisfy the frozen LLMProvider Protocol (the
    typed bindings ARE the mypy --strict conformance assertion; parity with the mock)."""
    from adapters.llm import AnthropicLLMProvider, OpenRouterLLMProvider

    secrets = InMemorySecretsAccessor({"ANTHROPIC_API_KEY": "x", "OPENROUTER_API_KEY": "x"})
    anthropic: LLMProvider = AnthropicLLMProvider(secrets=secrets, model="claude-sonnet-4")
    openrouter: LLMProvider = OpenRouterLLMProvider(secrets=secrets, model="openai/gpt-4o-mini")

    for provider in (anthropic, openrouter):
        assert callable(provider.complete)
        assert callable(provider.structured)


def test_complete_returns_text(llm_cassette: Cassette) -> None:
    """spec(§7) — complete() returns the model's free-text completion as a str."""
    adapter = _anthropic()
    with llm_cassette("anthropic_complete"):
        out = adapter.complete("Say hello", {})
    assert out == "Hello from Claude."


def test_structured_returns_validated_model(llm_cassette: Cassette) -> None:
    """spec(§7) — structured() returns a validated instance of the caller's schema (== recorded
    JSON), via schema.model_validate (never trusting the provider enforced the shape)."""
    adapter = _anthropic()
    with llm_cassette("anthropic_structured"):
        plan = adapter.structured("Plan a chair", DemoPlan, {})
    assert isinstance(plan, DemoPlan)
    assert plan == DemoPlan(title="Cozy Chair", count=3)


def test_structured_malformed_raises_malformed_output(
    llm_cassette: Cassette,
) -> None:
    """spec(§16) — deterministic validation: an unparseable/invalid-shape response raises
    ProviderError(MALFORMED_OUTPUT) (retryable; the bounded repair loop is Phase-2)."""
    adapter = _anthropic()
    from adapters.errors import ProviderError

    with llm_cassette("anthropic_malformed"), pytest.raises(ProviderError) as exc:
        adapter.structured("Plan a chair", DemoPlan, {})
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT
    assert exc.value.envelope.retryable is True


def test_http_429_raises_rate_limit(llm_cassette: Cassette) -> None:
    """spec(§17) — sync calls RAISE on a provider HTTP failure; 429 → PROVIDER_RATE_LIMIT
    (retryable)."""
    adapter = _anthropic()
    from adapters.errors import ProviderError

    with llm_cassette("anthropic_429"), pytest.raises(ProviderError) as exc:
        adapter.complete("hi", {})
    assert exc.value.envelope.code is ErrorCode.PROVIDER_RATE_LIMIT
    assert exc.value.envelope.retryable is True


def test_http_401_raises_auth_quota_not_retryable(
    llm_cassette: Cassette,
) -> None:
    """spec(§17) — 401 → PROVIDER_AUTH_QUOTA, a terminal-config failure (NOT retryable)."""
    adapter = _anthropic()
    from adapters.errors import ProviderError

    with llm_cassette("anthropic_401"), pytest.raises(ProviderError) as exc:
        adapter.complete("hi", {})
    assert exc.value.envelope.code is ErrorCode.PROVIDER_AUTH_QUOTA
    assert exc.value.envelope.retryable is False


def test_openrouter_complete_returns_text(llm_cassette: Cassette) -> None:
    """spec(§7) — the second backend's distinct wire shape (OpenAI-compatible chat-completions)
    parses to free text."""
    adapter = _openrouter()
    with llm_cassette("openrouter_complete"):
        out = adapter.complete("Say hello", {})
    assert out == "Hello from OpenRouter."


def test_openrouter_structured_returns_validated_model(
    llm_cassette: Cassette,
) -> None:
    """spec(§7) — the second backend's structured() re-validates to the caller's schema."""
    adapter = _openrouter()
    with llm_cassette("openrouter_structured"):
        plan = adapter.structured("Plan a lamp", DemoPlan, {})
    assert plan == DemoPlan(title="Modern Lamp", count=2)


def test_openrouter_structured_malformed_raises(llm_cassette: Cassette) -> None:
    """spec(§16) — the OpenRouter structured path is distinct from Anthropic's: its content is a
    JSON *string* re-validated via model_validate_json. A non-JSON content (model ignored
    response_format) → ProviderError(MALFORMED_OUTPUT), exercising the str branch of
    extract_and_validate that the Anthropic dict-payload malformed test does not reach."""
    adapter = _openrouter()
    from adapters.errors import ProviderError

    with llm_cassette("openrouter_malformed"), pytest.raises(ProviderError) as exc:
        adapter.structured("Plan a lamp", DemoPlan, {})
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT
    assert exc.value.envelope.retryable is True


def test_key_pulled_via_accessor_not_persisted(llm_cassette: Cassette) -> None:
    """safety rule 5 — the key is pulled via SecretsAccessor.get(name) AT CALL TIME, never at
    construction, never stashed as a raw instance attribute, never in repr/str."""
    from adapters.llm import AnthropicLLMProvider

    secret_value = "sk-ant-SUPER-SECRET-abc123"
    spy = SpyAccessor({"ANTHROPIC_API_KEY": secret_value})
    adapter = AnthropicLLMProvider(secrets=spy, model="claude-sonnet-4")

    assert spy.get_calls == []  # nothing pulled at construction

    with llm_cassette("anthropic_complete"):
        adapter.complete("hi", {})

    assert "ANTHROPIC_API_KEY" in spy.get_calls  # pulled through the accessor, by name
    assert secret_value not in repr(adapter)
    assert secret_value not in str(adapter)
    # the raw key is never held as a plain string attribute on the adapter
    str_attrs = [v for v in vars(adapter).values() if isinstance(v, str)]
    assert secret_value not in str_attrs


def test_cassettes_have_no_authorization_header() -> None:
    """safety rule 5 — every committed cassette is scrubbed: no Authorization/x-api-key header and
    no live key bytes land in git."""
    cassettes = sorted(CASSETTE_DIR.glob("*.yaml"))
    present = {c.stem for c in cassettes}
    assert _EXPECTED_CASSETTES <= present, f"missing cassettes: {_EXPECTED_CASSETTES - present}"

    for cassette in cassettes:
        text = cassette.read_text().lower()
        assert "authorization" not in text, f"{cassette.name} leaks an Authorization header"
        assert "x-api-key" not in text, f"{cassette.name} leaks an x-api-key header"
        assert "bearer sk-" not in text, f"{cassette.name} leaks a bearer key"


def test_factory_seam_no_self_registration() -> None:
    """fp-2 (no provider lock-in) — adapters resolve through a static name→constructor map; nothing
    self-registers or self-instantiates on import (parity with the mock MOCK_PROVIDERS seam)."""
    from adapters.llm import LLM_PROVIDERS, AnthropicLLMProvider, OpenRouterLLMProvider
    from adapters.mock import MOCK_PROVIDERS

    assert set(LLM_PROVIDERS) == {"anthropic", "openrouter"}
    assert LLM_PROVIDERS["anthropic"] is AnthropicLLMProvider
    assert LLM_PROVIDERS["openrouter"] is OpenRouterLLMProvider
    # values are CONSTRUCTORS (classes), not pre-built instances → no self-instantiation on import
    assert all(isinstance(ctor, type) for ctor in LLM_PROVIDERS.values())
    # cross-registry isolation: importing adapters.llm did not bleed into the mock seam
    assert "anthropic" not in MOCK_PROVIDERS
    assert "openrouter" not in MOCK_PROVIDERS
