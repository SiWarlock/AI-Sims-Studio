"""Deterministic silhouette-quality gate for concept images (§7 N-candidate gate; EVAL-002).

``silhouette_score`` scores an RGBA image in [0,1]: high for a clean, centered, single-component
silhouette; low for empty/transparent or fragmented/multi-blob. The score is the product of three
[0,1] factors over the (downsampled) alpha mask — coverage, centeredness, and a
single-component factor (largest-blob fraction divided by component count). ``select_best`` returns
the highest-scoring candidate above ``threshold``, or raises ``ProviderError(VALIDATION_FAILED)``
when none pass (a deterministic validation gate rejecting output — §17 / rule 6). Pure: no
wall-clock, no randomness — identical bytes yield an identical score.
"""

from __future__ import annotations

import io
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from aisims_contracts.error import ErrorCode
from numpy.typing import NDArray
from PIL import Image

from adapters.errors import ProviderError, build_envelope

DEFAULT_THRESHOLD = 0.5
_SCORE_MAX_DIM = 128  # downsample the alpha mask → resolution-independent + bounded CC cost
_ALPHA_OPAQUE = 128  # alpha > this counts as opaque
_MIN_COVERAGE = 0.02  # below this opaque fraction, the silhouette is effectively absent


@dataclass(frozen=True)
class SilhouetteSelection:
    """The chosen candidate + its silhouette score (the EVAL-002 metric the Phase-2 concept node
    records onto the Step/trace — returned alongside the bytes so the caller need not re-score)."""

    index: int
    score: float
    image: bytes


def silhouette_score(image_bytes: bytes) -> float:
    """Score an RGBA concept image in [0,1]; 0.0 for an empty/transparent image."""
    mask = _alpha_mask(image_bytes)
    total = int(mask.sum())
    if total == 0:
        return 0.0
    coverage_factor = _coverage_factor(total / mask.size)
    centered_factor = _centered_factor(mask)
    num_components, largest = _connected_components(mask)
    component_factor = (largest / total) / num_components
    return float(coverage_factor * centered_factor * component_factor)


def select_best(
    candidates: Sequence[bytes], threshold: float = DEFAULT_THRESHOLD
) -> SilhouetteSelection:
    """Return the highest-scoring candidate above ``threshold``; raise
    ProviderError(VALIDATION_FAILED) when none pass (the gate rejecting output)."""
    if not candidates:
        raise ProviderError(
            build_envelope(
                ErrorCode.VALIDATION_FAILED, maintainer_detail="no concept candidates to score"
            )
        )
    best_index = 0
    best_score = -1.0
    for index, image in enumerate(candidates):
        score = silhouette_score(image)
        if score > best_score:
            best_index, best_score = index, score
    if best_score < threshold:
        raise ProviderError(
            build_envelope(
                ErrorCode.VALIDATION_FAILED,
                maintainer_detail=(
                    f"no concept candidate passed the silhouette gate "
                    f"(best={best_score:.3f} < {threshold:.3f})"
                ),
            )
        )
    return SilhouetteSelection(index=best_index, score=best_score, image=candidates[best_index])


def _alpha_mask(image_bytes: bytes) -> NDArray[np.bool_]:
    """The opaque-pixel boolean mask of an RGBA image, downsampled to ``_SCORE_MAX_DIM``.

    Undecodable bytes (a corrupt / non-image candidate) → ProviderError(MALFORMED_OUTPUT) rather
    than a raw PIL error, so the gate's callers see one consistent provider-error type (§16)."""
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
        image.thumbnail((_SCORE_MAX_DIM, _SCORE_MAX_DIM))
    except (OSError, ValueError) as exc:
        raise ProviderError(
            build_envelope(
                ErrorCode.MALFORMED_OUTPUT,
                maintainer_detail="concept candidate was not a decodable image",
            )
        ) from exc
    alpha = np.asarray(image)[:, :, 3]
    mask: NDArray[np.bool_] = alpha > _ALPHA_OPAQUE
    return mask


def _coverage_factor(coverage: float) -> float:
    """Ramp from 0 below ``_MIN_COVERAGE``; a near-full frame isn't a clean silhouette either."""
    if coverage <= 0.0:
        return 0.0
    factor = min(coverage / _MIN_COVERAGE, 1.0)
    if coverage > 0.95:
        factor *= 0.3
    return factor


def _centered_factor(mask: NDArray[np.bool_]) -> float:
    """1.0 when the opaque centroid sits at the image center, ramping to 0 at the far corner."""
    ys, xs = np.nonzero(mask)
    height, width = mask.shape
    centroid_y = float(ys.mean())
    centroid_x = float(xs.mean())
    dist = ((centroid_y - (height - 1) / 2) ** 2 + (centroid_x - (width - 1) / 2) ** 2) ** 0.5
    max_dist = (((height - 1) / 2) ** 2 + ((width - 1) / 2) ** 2) ** 0.5
    return 1.0 - (dist / max_dist if max_dist else 0.0)


def _connected_components(mask: NDArray[np.bool_]) -> tuple[int, int]:
    """(num_components, largest_component_size) via iterative 4-connectivity flood fill over the
    (≤128²) downsampled mask — pure numpy/Python, no scipy/opencv."""
    visited = np.zeros_like(mask, dtype=bool)
    height, width = mask.shape
    num_components = 0
    largest = 0
    for start_y in range(height):
        for start_x in range(width):
            if not mask[start_y, start_x] or visited[start_y, start_x]:
                continue
            num_components += 1
            size = 0
            stack = [(start_y, start_x)]
            visited[start_y, start_x] = True
            while stack:
                y, x = stack.pop()
                size += 1
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if (
                        0 <= ny < height
                        and 0 <= nx < width
                        and mask[ny, nx]
                        and not visited[ny, nx]
                    ):
                        visited[ny, nx] = True
                        stack.append((ny, nx))
            largest = max(largest, size)
    return num_components, largest
