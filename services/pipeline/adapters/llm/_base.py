"""Shared raw-httpx plumbing for the real LLM adapters.

Two backends (Claude direct, OpenRouter) differ only in URL / auth header / request+response
envelope; the failure handling is identical and lives HERE so the §17 sync-raise classification and
the §16 deterministic re-validation have a single definition (no per-backend divergence):

* ``post_json`` — POST + map a transport error → ``PROVIDER_TIMEOUT`` and any non-2xx → the
  §17-classified ``ProviderError`` (bounded ``maintainerDetail``: status + host, never the body).
* ``extract_and_validate`` — pull the structured payload via a per-backend ``extractor`` then
  ALWAYS re-validate against the caller's schema; any parse/extraction/validation failure →
  ``ProviderError(MALFORMED_OUTPUT)``. This is the single malformed→raise path both backends share.
* ``extract_text`` — pull the free-text completion via a per-backend ``extractor``, guarded the
  same way.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import httpx
from aisims_contracts.error import ErrorCode
from pydantic import BaseModel, ValidationError

from adapters.errors import ProviderError, build_envelope, classify

# extraction failures that mean "the provider's response wasn't the shape we require" → MALFORMED.
_EXTRACT_ERRORS = (KeyError, IndexError, StopIteration, TypeError, ValueError)


def _malformed(detail: str) -> ProviderError:
    return ProviderError(build_envelope(ErrorCode.MALFORMED_OUTPUT, maintainer_detail=detail))


@contextmanager
def open_client(injected: httpx.Client | None, timeout: float) -> Iterator[httpx.Client]:
    """Yield the caller-injected client (tests / live smoke) or a fresh, timeout-bounded
    ``httpx.Client`` per call. Shared so both adapters get identical client lifecycle handling."""
    if injected is not None:
        yield injected
    else:
        with httpx.Client(timeout=timeout) as client:
            yield client


def post_json(
    client: httpx.Client,
    url: str,
    *,
    headers: dict[str, str],
    json_body: dict[str, Any],
    host: str,
) -> dict[str, Any]:
    """POST ``json_body`` and return the parsed JSON object.

    A timeout/connection error (no HTTP response) → ``PROVIDER_TIMEOUT``; any ``>= 400`` status →
    the §17-classified code. ``maintainerDetail`` is a bounded ``"HTTP <status> from <host>"`` —
    never the raw response body (safety rule 5).
    """
    try:
        response = client.post(url, headers=headers, json=json_body)
    except httpx.TimeoutException as exc:
        raise ProviderError(
            build_envelope(classify(None), maintainer_detail=f"timeout contacting {host}")
        ) from exc
    except httpx.TransportError as exc:  # connect/read/protocol — no usable HTTP response
        raise ProviderError(
            build_envelope(classify(None), maintainer_detail=f"connection error to {host}")
        ) from exc

    if response.status_code >= 400:
        raise ProviderError(
            build_envelope(
                classify(response.status_code),
                maintainer_detail=f"HTTP {response.status_code} from {host}",
            )
        )

    try:
        parsed = response.json()
    except ValueError as exc:
        raise _malformed(f"non-JSON 200 from {host}") from exc
    if not isinstance(parsed, dict):
        raise _malformed(f"unexpected top-level JSON ({type(parsed).__name__}) from {host}")
    return parsed


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
