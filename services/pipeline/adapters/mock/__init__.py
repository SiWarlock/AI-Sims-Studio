"""Mock adapter framework (§7/§8/§9 + §17 failure injection) — Phase-0 test infra.

Public surface: the mock provider/worker constructors, the failure-injection API, and a thin
name→constructor factory seam (``MOCK_PROVIDERS`` / ``MOCK_WORKERS``) Phase-2 selects through.
Registry SELECTION / self-registration is Phase-2 (the load-time validator is 0.5c) — nothing
self-registers on import (forbidden-pattern 2: no provider hard-wire).
"""

from __future__ import annotations

from collections.abc import Callable

from .failure import (
    FailurePlan,
    FailureRule,
    MockOp,
    ProviderError,
    envelope_for,
)
from .providers import (
    MockImage3DProvider,
    MockImageGenProvider,
    MockLLMProvider,
)
from .workers import (
    MockBlenderWorker,
    MockExportWorker,
)

# Thin factory seam: resolve a mock CLASS by name. Static maps, not a global self-registering
# registry — Phase-2 selects a mock through this seam; it does not import a concrete mock directly.
MOCK_PROVIDERS: dict[
    str, Callable[..., MockImage3DProvider | MockImageGenProvider | MockLLMProvider]
] = {
    "image3d": MockImage3DProvider,
    "imagegen": MockImageGenProvider,
    "llm": MockLLMProvider,
}
MOCK_WORKERS: dict[str, Callable[..., MockBlenderWorker | MockExportWorker]] = {
    "blender": MockBlenderWorker,
    "export": MockExportWorker,
}

__all__ = [
    "MOCK_PROVIDERS",
    "MOCK_WORKERS",
    "FailurePlan",
    "FailureRule",
    "MockBlenderWorker",
    "MockExportWorker",
    "MockImage3DProvider",
    "MockImageGenProvider",
    "MockLLMProvider",
    "MockOp",
    "ProviderError",
    "envelope_for",
]
