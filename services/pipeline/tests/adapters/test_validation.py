"""RED — C1: §16 provider-output content validation (provider-agnostic).

Pure/deterministic — no network. magic-byte/content-type detection over the image kinds (extensible
to mesh kinds when 3.1 lands) + the candidate-count fanout cap. A content mismatch / empty body →
ProviderError(MALFORMED_OUTPUT) (unusable output, retryable); too-many-candidates →
ProviderError(VALIDATION_FAILED) (policy gate, not-retryable) — the Step-2.5 Q1 split.
"""

from __future__ import annotations

import pytest
from aisims_contracts.error import ErrorCode

# valid leading bytes per kind (signatures only — not full-file validity)
_PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16
_WEBP = b"RIFF" + b"\x00\x00\x00\x20" + b"WEBP" + b"\x00" * 16


def test_validate_content_accepts_image_kinds() -> None:
    """spec(§16) — valid PNG/JPEG/WebP leading bytes pass when their kind is allowed."""
    from adapters.validation import ContentKind, validate_content

    allowed = {ContentKind.PNG, ContentKind.JPEG, ContentKind.WEBP}
    assert validate_content(_PNG, allowed=allowed) is ContentKind.PNG
    assert validate_content(_JPEG, allowed=allowed) is ContentKind.JPEG
    assert validate_content(_WEBP, allowed=allowed) is ContentKind.WEBP


def test_validate_content_rejects_mismatch() -> None:
    """spec(§16) — wrong content (an HTML/text error page, or a real kind that isn't allowed) →
    ProviderError(MALFORMED_OUTPUT): a swapped/poisoned artifact is unusable output."""
    from adapters.errors import ProviderError
    from adapters.validation import ContentKind, validate_content

    with pytest.raises(ProviderError) as exc:
        validate_content(b"<html><body>error</body></html>", allowed={ContentKind.PNG})
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT

    # a real kind that isn't in the allowed set is also a mismatch
    with pytest.raises(ProviderError) as exc2:
        validate_content(_PNG, allowed={ContentKind.JPEG})
    assert exc2.value.envelope.code is ErrorCode.MALFORMED_OUTPUT


def test_validate_content_rejects_empty() -> None:
    """spec(§16) — an empty body is degenerate output → ProviderError(MALFORMED_OUTPUT)."""
    from adapters.errors import ProviderError
    from adapters.validation import ContentKind, validate_content

    with pytest.raises(ProviderError) as exc:
        validate_content(b"", allowed={ContentKind.PNG})
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT


def test_candidate_count_cap() -> None:
    """spec(§16) — more than max_candidates urls is an unbounded-fanout policy violation →
    ProviderError(VALIDATION_FAILED), raised BEFORE any download; within the cap passes."""
    from adapters.errors import ProviderError
    from adapters.validation import enforce_candidate_count

    with pytest.raises(ProviderError) as exc:
        enforce_candidate_count(["u1", "u2", "u3", "u4", "u5"], max_candidates=2)
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED

    enforce_candidate_count(["u1", "u2"], max_candidates=2)  # at the cap → no raise
