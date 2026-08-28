"""RED — C2: the SSRF/redirect-hardened, streaming-capped get_bytes (shared transport).

Uses an httpx.MockTransport + an injected resolver — no live network, no real DNS. The streaming
cap is proved mid-stream via a counting raw stream (we stop pulling before the whole body is read).
SSRF rejections (non-https / private-IP / redirect) → ProviderError(VALIDATION_FAILED); the size cap
→ ProviderError(MALFORMED_OUTPUT) (the Step-2.5 Q1 split).
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
from aisims_contracts.error import ErrorCode

from adapters.errors import ProviderError


def _client(handler: object) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))  # type: ignore[arg-type]


def _public(_host: str) -> list[str]:
    return ["93.184.216.34"]  # a public IP — passes the SSRF check


class _CountingStream(httpx.SyncByteStream):
    """A raw byte stream that records how many bytes were actually pulled (to prove mid-stream)."""

    def __init__(self, chunks: list[bytes]) -> None:
        self._chunks = chunks
        self.pulled = 0

    def __iter__(self) -> Iterator[bytes]:
        for chunk in self._chunks:
            self.pulled += len(chunk)
            yield chunk

    def close(self) -> None:
        pass


def test_get_bytes_within_cap_returns_bytes() -> None:
    """spec(§16) — a small body under the cap returns intact (the guard doesn't break parity)."""
    from adapters._http import get_bytes

    with _client(lambda request: httpx.Response(200, content=b"hello-bytes")) as client:
        out = get_bytes(client, "https://cdn.example.com/a.png", max_bytes=1000, resolver=_public)
    assert out == b"hello-bytes"


def test_get_bytes_streaming_cap_raises_midstream() -> None:
    """spec(§16) — a body exceeding max_bytes raises ProviderError(MALFORMED_OUTPUT) mid-stream,
    WITHOUT pulling the whole body (DoS guard — not a post-hoc len() check)."""
    from adapters._http import get_bytes

    stream = _CountingStream([b"x" * 50] * 10)  # 500 bytes total

    with _client(lambda request: httpx.Response(200, stream=stream)) as client:
        with pytest.raises(ProviderError) as exc:
            get_bytes(client, "https://cdn.example.com/big.png", max_bytes=100, resolver=_public)
    assert exc.value.envelope.code is ErrorCode.MALFORMED_OUTPUT
    assert stream.pulled < 500  # stopped before consuming the whole body


def test_get_bytes_rejects_non_https() -> None:
    """spec(§16/SSRF) — a non-https scheme is rejected before any request."""
    from adapters._http import get_bytes

    with _client(lambda request: httpx.Response(200, content=b"x")) as client:
        with pytest.raises(ProviderError) as exc:
            get_bytes(client, "http://cdn.example.com/a.png", max_bytes=1000, resolver=_public)
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED


def test_get_bytes_rejects_private_ip_host() -> None:
    """spec(§16/SSRF) — a host resolving to a private/loopback/link-local IP (the cloud-metadata
    endpoint class) is rejected."""
    from adapters._http import get_bytes

    with _client(lambda request: httpx.Response(200, content=b"x")) as client:
        with pytest.raises(ProviderError) as exc:
            get_bytes(
                client,
                "https://metadata.internal/a.png",
                max_bytes=1000,
                resolver=lambda _host: ["169.254.169.254"],  # link-local metadata endpoint
            )
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED


def test_get_bytes_rejects_host_not_in_allowlist() -> None:
    """spec(§16/SSRF) — when allowed_hosts is set, a host outside it is rejected (the optional
    name-level hardening gate, on top of the always-on IP floor)."""
    from adapters._http import get_bytes

    with _client(lambda request: httpx.Response(200, content=b"x")) as client:
        with pytest.raises(ProviderError) as exc:
            get_bytes(
                client,
                "https://cdn.example.com/a.png",
                max_bytes=1000,
                allowed_hosts={"trusted.example.com"},
                resolver=_public,
            )
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED


def test_get_bytes_resolver_failure_fails_closed() -> None:
    """spec(§16/SSRF) — a resolution failure fails CLOSED → VALIDATION_FAILED (not a retryable
    timeout): we can't verify the host is non-private, so we reject."""
    from adapters._http import get_bytes

    def _boom(_host: str) -> list[str]:
        raise OSError("dns down")

    with _client(lambda request: httpx.Response(200, content=b"x")) as client:
        with pytest.raises(ProviderError) as exc:
            get_bytes(client, "https://cdn.example.com/a.png", max_bytes=1000, resolver=_boom)
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED


def test_get_bytes_empty_resolution_fails_closed() -> None:
    """spec(§16/SSRF) — an EMPTY resolver result must NOT bypass the always-on IP floor; it fails
    closed → VALIDATION_FAILED (regression guard for the floor-bypass)."""
    from adapters._http import get_bytes

    with _client(lambda request: httpx.Response(200, content=b"x")) as client:
        with pytest.raises(ProviderError) as exc:
            get_bytes(
                client, "https://cdn.example.com/a.png", max_bytes=1000, resolver=lambda _h: []
            )
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED


def test_get_bytes_does_not_follow_redirects() -> None:
    """spec(§16/SSRF) — a 3xx is NOT followed (redirect-pivot guard); it surfaces as a rejection."""
    from adapters._http import get_bytes

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "https://evil.internal/x"})

    with _client(handler) as client:
        with pytest.raises(ProviderError) as exc:
            get_bytes(client, "https://cdn.example.com/a.png", max_bytes=1000, resolver=_public)
    assert exc.value.envelope.code is ErrorCode.VALIDATION_FAILED
