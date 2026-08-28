"""Real concept-image adapters (§7) + a thin name→constructor factory seam.

``IMAGEGEN_PROVIDERS`` mirrors the mock ``MOCK_PROVIDERS`` and the 3.3 ``LLM_PROVIDERS`` seams: a
STATIC map Phase-2 selects a backend through (via the open-registry seam). Nothing self-registers or
self-instantiates on import — no provider hard-wire (forbidden-pattern 2). The deterministic
silhouette gate lives in ``adapters.imagegen.silhouette`` (imported directly by its consumers, not
re-exported here, so importing this package pulls no image libraries).
"""

from __future__ import annotations

from collections.abc import Callable

from aisims_contracts.providers import ImageGenProvider

from .fal import FalImageGenProvider
from .wavespeed import WaveSpeedImageGenProvider

# name → constructor. Static, not a self-registering global registry (parity with MOCK/LLM seams).
IMAGEGEN_PROVIDERS: dict[str, Callable[..., ImageGenProvider]] = {
    "wavespeed": WaveSpeedImageGenProvider,
    "fal": FalImageGenProvider,
}

__all__ = [
    "IMAGEGEN_PROVIDERS",
    "FalImageGenProvider",
    "WaveSpeedImageGenProvider",
]
