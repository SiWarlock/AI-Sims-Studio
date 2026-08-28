"""RED — C1: the env-gated live smoke (Option A's real-call reachability proof + cassette source).

Skipped unless AISIMS_IMAGEGEN_LIVE=1 and WAVESPEED_API_KEY is present (mirrors the 0.7
AISIMS_TEST_DATABASE_URL env-gated pattern). The bounded poll loop lives in the TEST (the caller),
not the adapter — production resumable submit/poll/fetch is the Phase-2 two-phase node.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
from aisims_contracts.providers import PollStatus

from obs.secrets import InMemorySecretsAccessor

_LIVE = os.environ.get("AISIMS_IMAGEGEN_LIVE") == "1"


@pytest.mark.skipif(not _LIVE, reason="set AISIMS_IMAGEGEN_LIVE=1 (+ WAVESPEED_API_KEY) to run")
def test_live_imagegen_smoke(tmp_path: Path) -> None:
    """One real submit→poll→fetch against WaveSpeed — proves the real async path end to end."""
    from adapters.imagegen import IMAGEGEN_PROVIDERS

    key = os.environ.get("WAVESPEED_API_KEY")
    if not key:
        pytest.skip("WAVESPEED_API_KEY not set")

    provider = IMAGEGEN_PROVIDERS["wavespeed"](
        secrets=InMemorySecretsAccessor({"WAVESPEED_API_KEY": key}),
        scratch_dir=tmp_path,
    )
    ref = provider.submit(
        "a single red ceramic mug, centered, plain background",
        {"seed": 7, "transparent_bg": True},
    )

    result = provider.poll(ref)
    for _ in range(30):
        if result.status in (PollStatus.SUCCEEDED, PollStatus.FAILED, PollStatus.EXPIRED):
            break
        time.sleep(2)
        result = provider.poll(ref)

    assert result.status is PollStatus.SUCCEEDED
    assert result.urls
    paths = provider.fetch(result.urls)
    assert paths and Path(paths[0]).is_file()
