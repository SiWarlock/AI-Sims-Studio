"""Secret-free shared HTTP transport primitives for the real provider adapters (§7).

A neutral home (sibling of ``adapters/errors.py``) for the raw-httpx plumbing every real adapter
family reuses — LLM (3.3), imagegen (3.2), image3d (3.1): a per-call client, a request→classify
helper, and a guarded byte download. **SECRET-FREE by design** — the ``SecretsAccessor`` key-pull
and the auth-header injection stay at the adapter (the rule-5 chokepoint does NOT migrate into
shared code); callers pass fully-formed ``headers`` in. Transport/HTTP failures map to the
§17-classified ``ProviderError`` via ``adapters.errors`` (bounded ``maintainerDetail``: status +
host, never the response body).
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import httpx
from aisims_contracts.error import ErrorCode

from adapters.errors import ProviderError, build_envelope, classify


@contextmanager
def open_client(injected: httpx.Client | None, timeout: float) -> Iterator[httpx.Client]:
    """Yield the caller-injected client (tests / live smoke) or a fresh, timeout-bounded
    ``httpx.Client`` per call. Shared so every adapter gets identical client lifecycle handling."""
    if injected is not None:
        yield injected
    else:
        with httpx.Client(timeout=timeout) as client:
            yield client


def _transport_error(exc: httpx.TransportError, host: str) -> ProviderError:
    """A timeout/connection error (no usable HTTP response) → PROVIDER_TIMEOUT."""
    detail = (
        f"timeout contacting {host}"
        if isinstance(exc, httpx.TimeoutException)
        else f"connection error to {host}"
    )
    return ProviderError(build_envelope(classify(None), maintainer_detail=detail))


def _raise_for_status(response: httpx.Response, host: str) -> None:
    if response.status_code >= 400:
        raise ProviderError(
            build_envelope(
                classify(response.status_code),
                maintainer_detail=f"HTTP {response.status_code} from {host}",
            )
        )


def request_json(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    host: str,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send ``method`` ``url`` and return the parsed JSON object. Transport error →
    PROVIDER_TIMEOUT; any ``>= 400`` → the §17-classified code; non-JSON / non-object body →
    MALFORMED_OUTPUT."""
    try:
        response = client.request(method, url, headers=headers, json=json_body)
    except httpx.TransportError as exc:
        raise _transport_error(exc, host) from exc

    _raise_for_status(response, host)

    try:
        parsed = response.json()
    except ValueError as exc:
        raise ProviderError(
            build_envelope(
                ErrorCode.MALFORMED_OUTPUT, maintainer_detail=f"non-JSON response from {host}"
            )
        ) from exc
    if not isinstance(parsed, dict):
        raise ProviderError(
            build_envelope(
                ErrorCode.MALFORMED_OUTPUT,
                maintainer_detail=f"non-object JSON ({type(parsed).__name__}) from {host}",
            )
        )
    return parsed


def post_json(
    client: httpx.Client,
    url: str,
    *,
    headers: dict[str, str],
    json_body: dict[str, Any],
    host: str,
) -> dict[str, Any]:
    """POST convenience wrapper (the 3.3 LLM adapters' entry point)."""
    return request_json(client, "POST", url, headers=headers, host=host, json_body=json_body)


def get_bytes(
    client: httpx.Client,
    url: str,
    *,
    host: str,
    headers: dict[str, str] | None = None,
) -> bytes:
    """GET raw bytes (artifact download). Transport error → PROVIDER_TIMEOUT; ``>= 400`` →
    the §17-classified ProviderError. The §16 byte-cap / magic-byte hardening lands in 3.4."""
    try:
        response = client.get(url, headers=headers or {})
    except httpx.TransportError as exc:
        raise _transport_error(exc, host) from exc

    _raise_for_status(response, host)
    return response.content
