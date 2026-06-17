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

import ipaddress
import socket
from collections.abc import Callable, Iterator
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


def _default_resolver(host: str) -> list[str]:
    """Resolve ``host`` to its IP strings via the OS (the default SSRF resolver; tests inject)."""
    return [str(info[4][0]) for info in socket.getaddrinfo(host, None)]


def _check_ssrf(
    url: str, *, allowed_hosts: set[str] | None, resolver: Callable[[str], list[str]]
) -> str:
    """SSRF guard (§16): https-only; optional allowlist gate; and the ALWAYS-ON floor — reject a
    host resolving to a private / loopback / link-local / reserved / multicast address (the
    metadata-endpoint class). Returns the validated host; raises VALIDATION_FAILED on reject."""
    parsed = httpx.URL(url)
    if parsed.scheme != "https":
        raise ProviderError(
            build_envelope(
                ErrorCode.VALIDATION_FAILED,
                maintainer_detail=f"non-https url scheme '{parsed.scheme}'",
            )
        )
    host = parsed.host
    if not host:
        raise ProviderError(
            build_envelope(ErrorCode.VALIDATION_FAILED, maintainer_detail="url has no host")
        )
    # NOTE (TOCTOU): httpx re-resolves the host at connect time, so a DNS-rebinding attacker could
    # pass this guard then connect to a private IP. Robust fix = pin the validated IP at the
    # transport — deferred to 3.4b. allowed_hosts is a name-level gate, NOT an IP guarantee; the
    # always-on private-IP floor below is the load-bearing boundary.
    if allowed_hosts is not None and host not in allowed_hosts:
        raise ProviderError(
            build_envelope(
                ErrorCode.VALIDATION_FAILED, maintainer_detail=f"host '{host}' not in allowed_hosts"
            )
        )
    # ALWAYS-ON floor: resolve + reject anything not globally routable (private/loopback/link-local/
    # reserved/multicast/CGNAT/unspecified — the metadata-endpoint class). `not is_global` is one
    # check that subsumes them all. A resolution failure / empty result fails CLOSED (can't verify
    # the host is safe) → VALIDATION_FAILED, never a silent pass or a retryable timeout.
    try:
        addresses = resolver(host)
    except OSError as exc:
        raise ProviderError(
            build_envelope(
                ErrorCode.VALIDATION_FAILED, maintainer_detail=f"could not resolve host '{host}'"
            )
        ) from exc
    if not addresses:
        raise ProviderError(
            build_envelope(
                ErrorCode.VALIDATION_FAILED,
                maintainer_detail=f"no addresses resolved for host '{host}'",
            )
        )
    for raw in addresses:
        if not ipaddress.ip_address(raw).is_global:
            raise ProviderError(
                build_envelope(
                    ErrorCode.VALIDATION_FAILED,
                    maintainer_detail=f"host '{host}' resolves to a non-public address",
                )
            )
    return host


def get_bytes(
    client: httpx.Client,
    url: str,
    *,
    max_bytes: int,
    headers: dict[str, str] | None = None,
    allowed_hosts: set[str] | None = None,
    resolver: Callable[[str], list[str]] | None = None,
) -> bytes:
    """GET raw bytes (artifact download), §16-hardened. Pre-flight SSRF guard (https-only,
    private-IP rejection, optional allowlist), then a STREAMING read that raises
    ``MALFORMED_OUTPUT`` the moment the body exceeds ``max_bytes`` — it never buffers the whole body
    (DoS guard). ``follow_redirects=False``; a 3xx is rejected (redirect-pivot guard), ``>= 400`` →
    the §17-classified ProviderError, transport error → PROVIDER_TIMEOUT."""
    host = _check_ssrf(url, allowed_hosts=allowed_hosts, resolver=resolver or _default_resolver)
    try:
        with client.stream("GET", url, headers=headers or {}, follow_redirects=False) as response:
            if 300 <= response.status_code < 400:
                raise ProviderError(
                    build_envelope(
                        ErrorCode.VALIDATION_FAILED,
                        maintainer_detail=f"unexpected redirect {response.status_code} from {host}",
                    )
                )
            _raise_for_status(response, host)
            buffer = bytearray()
            for chunk in response.iter_bytes():
                buffer += chunk
                if len(buffer) > max_bytes:
                    raise ProviderError(
                        build_envelope(
                            ErrorCode.MALFORMED_OUTPUT,
                            maintainer_detail=f"download exceeds max_bytes {max_bytes} from {host}",
                        )
                    )
            return bytes(buffer)
    except httpx.TransportError as exc:
        raise _transport_error(exc, host) from exc
