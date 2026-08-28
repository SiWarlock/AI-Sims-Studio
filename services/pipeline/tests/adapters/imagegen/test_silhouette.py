"""RED — C2: the deterministic silhouette-quality gate (scores an RGBA concept image; selects the
best of N candidates). Pure functions — no network, no wall-clock, no randomness.

Fixtures are generated programmatically (PIL + numpy) so they're inspectable and deterministic: a
clean centered single-component silhouette scores high; empty/transparent and fragmented multi-blob
images score low.
"""

from __future__ import annotations

import io

import numpy as np
import pytest
from aisims_contracts.error import ErrorCode
from PIL import Image

_THRESHOLD = 0.5


def _png(alpha: np.ndarray) -> bytes:
    """Encode an HxW uint8 alpha mask as RGBA PNG bytes (opaque pixels white)."""
    h, w = alpha.shape
    rgb = np.full((h, w, 3), 255, dtype=np.uint8)
    rgba = np.dstack([rgb, alpha])
    buf = io.BytesIO()
    Image.fromarray(rgba, mode="RGBA").save(buf, format="PNG")
    return buf.getvalue()


def _clean(size: int = 128) -> bytes:
    """A single centered opaque square — clean, centered, one component."""
    alpha = np.zeros((size, size), dtype=np.uint8)
    alpha[size // 4 : 3 * size // 4, size // 4 : 3 * size // 4] = 255
    return _png(alpha)


def _empty(size: int = 128) -> bytes:
    """Fully transparent — no silhouette."""
    return _png(np.zeros((size, size), dtype=np.uint8))


def _fragmented(size: int = 128) -> bytes:
    """Two separate opaque blobs — fragmented / multi-component."""
    alpha = np.zeros((size, size), dtype=np.uint8)
    alpha[10:40, 10:40] = 255
    alpha[88:118, 88:118] = 255
    return _png(alpha)


def test_silhouette_score_clean_silhouette_high() -> None:
    """A clean centered single-component silhouette scores at/above the gate threshold."""
    from adapters.imagegen.silhouette import silhouette_score

    score = silhouette_score(_clean())
    assert 0.0 <= score <= 1.0
    assert score >= _THRESHOLD


def test_silhouette_score_empty_and_fragmented_low() -> None:
    """Empty (transparent) and fragmented (multi-blob) images score below threshold."""
    from adapters.imagegen.silhouette import silhouette_score

    assert silhouette_score(_empty()) < _THRESHOLD
    assert silhouette_score(_fragmented()) < _THRESHOLD


def test_select_best_picks_highest_above_threshold() -> None:
    """Given N fetched candidates, select_best returns the highest-scoring one above threshold —
    with its silhouette score riding along (the EVAL-002 metric the Phase-2 node records)."""
    from adapters.imagegen.silhouette import select_best

    clean = _clean()
    chosen = select_best([_empty(), clean, _fragmented()], threshold=_THRESHOLD)
    assert chosen.image == clean
    assert chosen.index == 1
    assert chosen.score >= _THRESHOLD


def test_select_best_none_pass_surfaces_failure() -> None:
    """spec(§17) — when no candidate clears the gate, select_best raises the defined failure
    (deterministic validation gate rejecting output → VALIDATION_FAILED, not retryable)."""
    from adapters.errors import ProviderError
    from adapters.imagegen.silhouette import select_best

    with pytest.raises(ProviderError) as exc:
        select_best([_empty(), _fragmented()], threshold=_THRESHOLD)
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED
    assert exc.value.envelope.retryable is False


def test_silhouette_score_corrupt_bytes_raises_malformed() -> None:
    """spec(§16) — an undecodable/non-image candidate surfaces as ProviderError(MALFORMED_OUTPUT),
    not a raw PIL error (one consistent provider-error type for the gate's callers)."""
    from adapters.errors import ProviderError
    from adapters.imagegen.silhouette import silhouette_score

    with pytest.raises(ProviderError) as exc:
        silhouette_score(b"this is definitely not a valid image")
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT


def test_silhouette_score_deterministic() -> None:
    """Pure function — identical bytes yield an identical score (no wall-clock / randomness)."""
    from adapters.imagegen.silhouette import silhouette_score

    image = _clean()
    assert silhouette_score(image) == silhouette_score(image)
