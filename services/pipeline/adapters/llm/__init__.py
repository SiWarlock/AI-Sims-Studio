"""Real LLM adapters (§7) + a thin name→constructor factory seam.

``LLM_PROVIDERS`` mirrors the mock ``MOCK_PROVIDERS`` seam: a STATIC map Phase-2 selects a backend
through (via the open-registry seam). Nothing self-registers or self-instantiates on import — no
provider hard-wire (forbidden-pattern 2); the values are constructors, not pre-built instances.
"""

from __future__ import annotations

from collections.abc import Callable

from aisims_contracts.providers import LLMProvider

from .anthropic import AnthropicLLMProvider
from .openrouter import OpenRouterLLMProvider

# name → constructor. Static, not a self-registering global registry (parity with MOCK_PROVIDERS).
LLM_PROVIDERS: dict[str, Callable[..., LLMProvider]] = {
    "anthropic": AnthropicLLMProvider,
    "openrouter": OpenRouterLLMProvider,
}

__all__ = [
    "LLM_PROVIDERS",
    "AnthropicLLMProvider",
    "OpenRouterLLMProvider",
]
