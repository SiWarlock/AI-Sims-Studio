"""LLM-specific response handling for the real LLM adapters (Claude direct, OpenRouter).

The two backends differ only in URL / auth header / request+response envelope; the §16
deterministic re-validation lives HERE so the malformed→raise path has a single definition (no
per-backend divergence). The raw-HTTP transport primitives (``open_client`` / ``post_json``) are the
secret-free shared layer in ``adapters/_http.py`` (3.2 hoist) — the adapters import them from there.

* ``extract_and_validate`` — pull the structured payload via a per-backend ``extractor`` then
  ALWAYS re-validate against the caller's schema; any parse/extraction/validation failure →
  ``ProviderError(MALFORMED_OUTPUT)``. This is the single malformed→raise path both backends share.
* ``extract_text`` — pull the free-text completion via a per-backend ``extractor``, guarded the
  same way.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aisims_contracts.error import ErrorCode
from pydantic import BaseModel, ValidationError

from adapters.errors import ProviderError, build_envelope

# extraction failures that mean "the provider's response wasn't the shape we require" → MALFORMED.
_EXTRACT_ERRORS = (KeyError, IndexError, StopIteration, TypeError, ValueError)


def _malformed(detail: str) -> ProviderError:
    return ProviderError(build_envelope(ErrorCode.MALFORMED_OUTPUT, maintainer_detail=detail))


def extract_and_validate[T: BaseModel](
    schema: type[T],
    data: dict[str, Any],
    extractor: Callable[[dict[str, Any]], dict[str, Any] | str],
) -> T:
    """Extract the structured payload (``extractor`` is per-backend) then re-validate it against
    ``schema`` (§16 — never trust the provider enforced the shape). Any failure → MALFORMED."""
    try:
        payload = extractor(data)
        if isinstance(payload, str):
            return schema.model_validate_json(payload)
        return schema.model_validate(payload)
    except ValidationError as exc:
        raise _malformed("provider structured output failed schema validation") from exc
    except _EXTRACT_ERRORS as exc:
        raise _malformed("provider structured output envelope was malformed") from exc


def extract_text(data: dict[str, Any], extractor: Callable[[dict[str, Any]], Any]) -> str:
    """Pull the free-text completion (``extractor`` is per-backend), guarded → MALFORMED."""
    try:
        text = extractor(data)
    except _EXTRACT_ERRORS as exc:
        raise _malformed("provider completion response was malformed") from exc
    if not isinstance(text, str):
        raise _malformed("provider completion response was not text")
    return text
