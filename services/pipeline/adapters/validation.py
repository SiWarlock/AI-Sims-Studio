"""§16 provider-output content validation — provider-agnostic, deterministic, no I/O.

Magic-byte / content-type detection over the supported content kinds + the candidate-count fanout
cap. The error-code split (Step-2.5 Q1) follows the frozen §17 ``retryable`` posture:

* a content problem (empty / wrong-magic) is unusable provider OUTPUT → ``MALFORMED_OUTPUT``
  (retryable — the Phase-2 bounded repair loop may regenerate → a fresh URL → a valid download);
* the candidate-count cap is a policy/fanout guard → ``VALIDATION_FAILED`` (NOT retryable —
  re-passing the same overlong list can't help).

The signature map is EXTENSIBLE — mesh kinds (GLB/GLTF) are added at 3.1; do not hard-close it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from enum import StrEnum

from aisims_contracts.error import ErrorCode

from adapters.errors import ProviderError, build_envelope

# default §16 caps (a param override exists; the Phase-2 budget knob is out of scope — 3.4b).
DEFAULT_MAX_IMAGE_BYTES = 25 * 1024 * 1024
DEFAULT_MAX_CANDIDATES = 8


class ContentKind(StrEnum):
    """The artifact content kinds the §16 gate can attest. Image kinds now; mesh kinds at 3.1."""

    PNG = "png"
    JPEG = "jpeg"
    WEBP = "webp"


def _is_png(data: bytes) -> bool:
    return data[:8] == b"\x89PNG\r\n\x1a\n"


def _is_jpeg(data: bytes) -> bool:
    return data[:3] == b"\xff\xd8\xff"


def _is_webp(data: bytes) -> bool:
    return len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP"


# kind → leading-bytes predicate. Append mesh kinds here (3.1) — open, not hard-closed.
_SIGNATURES: dict[ContentKind, Callable[[bytes], bool]] = {
    ContentKind.PNG: _is_png,
    ContentKind.JPEG: _is_jpeg,
    ContentKind.WEBP: _is_webp,
}


def detect_kind(data: bytes) -> ContentKind | None:
    """The first content kind whose magic bytes match ``data``, or None. Iterates ``_SIGNATURES`` in
    insertion order; the image signatures are mutually exclusive, so order is not load-bearing —
    keep new (mesh) signatures non-overlapping when extending."""
    for kind, matches in _SIGNATURES.items():
        if matches(data):
            return kind
    return None


def validate_content(data: bytes, *, allowed: set[ContentKind]) -> ContentKind:
    """Return the detected ContentKind if it's in ``allowed``; else raise
    ProviderError(MALFORMED_OUTPUT). An empty body is degenerate output (also MALFORMED_OUTPUT)."""
    if not data:
        raise ProviderError(
            build_envelope(
                ErrorCode.MALFORMED_OUTPUT, maintainer_detail="empty provider response body"
            )
        )
    kind = detect_kind(data)
    if kind is None or kind not in allowed:
        detected = kind.value if kind is not None else "unknown"
        raise ProviderError(
            build_envelope(
                ErrorCode.MALFORMED_OUTPUT,
                maintainer_detail=(
                    f"content kind '{detected}' not in allowed {sorted(k.value for k in allowed)}"
                ),
            )
        )
    return kind


def enforce_candidate_count(
    urls: Sequence[object], *, max_candidates: int = DEFAULT_MAX_CANDIDATES
) -> None:
    """Raise ProviderError(VALIDATION_FAILED) when more than ``max_candidates`` urls are passed —
    an unbounded-fanout policy guard, checked BEFORE any download."""
    if len(urls) > max_candidates:
        raise ProviderError(
            build_envelope(
                ErrorCode.VALIDATION_FAILED,
                maintainer_detail=f"too many candidates ({len(urls)} > {max_candidates})",
            )
        )
