"""``WaveSpeedImageGenProvider`` — FLUX.2 [pro] concept images behind the frozen §7 seam.

Async submit/poll/fetch over the WaveSpeed v3 API (POST ``/{model}``; GET
``/predictions/{id}/result``; GET the output CDN urls). Three-way error channel (§17 — the
real-adapter refinement of lesson 5): ``submit``/``fetch`` RAISE ``ProviderError`` (no ref / no
paths to return); ``poll`` rides ``PollResult.error`` (a job failure or a poll-HTTP failure surfaces
as FAILED and never raises). Keys via the ``SecretsAccessor`` at call time only (rule 5);
``transparent_bg`` + a pinned ``seed`` ride the submit body; fetch is scratch-guarded (rule 3).
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from aisims_contracts.error import ErrorCode
from aisims_contracts.providers import PollResult, PollStatus, ProviderJobRef, ProviderUsage

from adapters._http import get_bytes, open_client, request_json
from adapters.errors import ProviderError, build_envelope
from adapters.pricing import estimate_cost
from adapters.validation import (
    DEFAULT_MAX_CANDIDATES,
    DEFAULT_MAX_IMAGE_BYTES,
    ContentKind,
    enforce_candidate_count,
    validate_content,
)
from obs.secrets import SecretsAccessor

from ._base import safe_scratch_path

DEFAULT_BASE_URL = "https://api.wavespeed.ai/api/v3"
DEFAULT_MODEL = "wavespeed-ai/flux-2-pro/text-to-image"
DEFAULT_KEY_NAME = "WAVESPEED_API_KEY"
DEFAULT_TIMEOUT = 60.0
# concept-image content kinds the §16 gate accepts for this adapter (mesh kinds are 3.1).
_IMAGE_KINDS = {ContentKind.PNG, ContentKind.JPEG, ContentKind.WEBP}

# WaveSpeed data.status → our §7 PollStatus, for the pending states (created/processing).
_PENDING_STATUS = {"created": PollStatus.SUBMITTED, "processing": PollStatus.RUNNING}
_PENDING_PROGRESS = {PollStatus.SUBMITTED: 0.0, PollStatus.RUNNING: 0.5}


def build_submit_body(prompt: str, params: dict[str, Any]) -> dict[str, Any]:
    """The FLUX.2 submit request body: prompt + a pinned seed + transparent_bg, sync/base64 off.

    Pure (no I/O) so request construction is unit-testable directly (vcr matches on method+uri, not
    body, so a cassette can't pin it). ``seed`` defaults to -1 (provider random)."""
    body: dict[str, Any] = {
        "prompt": prompt,
        "seed": int(params.get("seed", -1)),
        "transparent_bg": bool(params.get("transparent_bg", True)),
        "enable_base64_output": False,
        "enable_sync_mode": False,
    }
    if "size" in params:
        body["size"] = params["size"]
    return body


class WaveSpeedImageGenProvider:
    """Synchronous-call WaveSpeed adapter. Conforms to the frozen §7 ImageGenProvider Protocol."""

    PROVIDER = "wavespeed"

    def __init__(
        self,
        *,
        secrets: SecretsAccessor,
        model: str = DEFAULT_MODEL,
        scratch_dir: Path,
        key_name: str = DEFAULT_KEY_NAME,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        http_client: httpx.Client | None = None,
        max_bytes: int = DEFAULT_MAX_IMAGE_BYTES,
        max_candidates: int = DEFAULT_MAX_CANDIDATES,
        allowed_hosts: set[str] | None = None,
        resolver: Callable[[str], list[str]] | None = None,
    ) -> None:
        self._secrets = secrets  # accessor reference only — NEVER the resolved key (rule 5)
        self._model = model
        self._scratch_dir = scratch_dir
        self._key_name = key_name
        self._base_url = base_url.rstrip("/")
        self._host = httpx.URL(base_url).host
        self._timeout = timeout
        self._client = http_client
        # §16 fetch caps + SSRF: allowed_hosts defaults None so private-IP rejection ALWAYS runs;
        # resolver is injectable (tests map the CDN host → a public IP to skip real DNS).
        self._max_bytes = max_bytes
        self._max_candidates = max_candidates
        self._allowed_hosts = allowed_hosts
        self._resolver = resolver

    def _key(self) -> str:
        key = self._secrets.get(self._key_name)
        if not key:
            raise ProviderError(
                build_envelope(
                    ErrorCode.PROVIDER_AUTH_QUOTA,
                    maintainer_detail=f"no secret configured for {self._key_name}",
                )
            )
        return key

    def _auth_headers(self, key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {key}", "content-type": "application/json"}

    def submit(self, prompt: str, params: dict[str, Any]) -> ProviderJobRef:
        key = self._key()
        body = build_submit_body(prompt, params)
        with open_client(self._client, self._timeout) as client:
            data = request_json(
                client,
                "POST",
                f"{self._base_url}/{self._model}",
                headers=self._auth_headers(key),
                host=self._host,
                json_body=body,
            )
        payload = _data(data)
        job_id = payload.get("id")
        if not job_id:
            raise ProviderError(
                build_envelope(
                    ErrorCode.MALFORMED_OUTPUT,
                    maintainer_detail=f"submit response missing data.id from {self._host}",
                )
            )
        return ProviderJobRef(
            provider=self.PROVIDER,
            model=self._model,
            jobId=str(job_id),
            submittedAt=_parse_ts(payload.get("created_at")),
        )

    def poll(self, ref: ProviderJobRef) -> PollResult:
        # async channel (lesson 5 / §17): poll NEVER raises — a missing key, a poll-HTTP failure,
        # or any classified error rides PollResult.error. The key-pull is INSIDE the guard.
        try:
            key = self._key()
            url = f"{self._base_url}/predictions/{ref.jobId}/result"
            with open_client(self._client, self._timeout) as client:
                data = request_json(
                    client, "GET", url, headers=self._auth_headers(key), host=self._host
                )
        except ProviderError as exc:
            return PollResult(status=PollStatus.FAILED, error=exc.envelope)

        payload = _data(data)
        status = str(payload.get("status", ""))
        usage = _usage(payload)  # defensive — never raises (bad/negative inference → None)
        if status == "completed":
            outputs = payload.get("outputs")
            urls = [str(u) for u in outputs] if isinstance(outputs, list) else []
            if usage is not None:
                # cost attributed ONCE on success, alongside latency (§7). WaveSpeed's result has
                # no inline cost field → table estimate (actual=None); unknown model → None.
                # estimate_cost is pure (no I/O) so this post-guard line keeps poll non-raising.
                usage = usage.model_copy(
                    update={"costCents": estimate_cost(self.PROVIDER, self._model)}
                )
            return PollResult(status=PollStatus.SUCCEEDED, progress=1.0, urls=urls, usage=usage)
        if status == "failed":
            return PollResult(
                status=PollStatus.FAILED,
                usage=usage,
                error=build_envelope(
                    ErrorCode.PROVIDER_OUTAGE,
                    maintainer_detail=f"WaveSpeed prediction failed (status={status})",
                ),
            )
        mapped = _PENDING_STATUS.get(status, PollStatus.RUNNING)
        return PollResult(status=mapped, progress=_PENDING_PROGRESS[mapped], usage=usage)

    def fetch(self, urls: list[str]) -> list[str]:
        # §16 trust boundary: cap the fanout BEFORE any download, then for each output CDN url
        # SSRF+size-guard the (unauthenticated) download and magic-byte-validate the bytes before
        # they touch scratch. Every violation RAISES (fetch has no result error field — LESSONS 10).
        enforce_candidate_count(urls, max_candidates=self._max_candidates)
        self._scratch_dir.mkdir(parents=True, exist_ok=True)
        paths: list[str] = []
        with open_client(self._client, self._timeout) as client:
            for index, url in enumerate(urls):
                content = get_bytes(
                    client,
                    url,
                    max_bytes=self._max_bytes,
                    allowed_hosts=self._allowed_hosts,
                    resolver=self._resolver,
                )
                validate_content(content, allowed=_IMAGE_KINDS)
                dest = safe_scratch_path(self._scratch_dir, url, index=index)
                dest.write_bytes(content)
                paths.append(str(dest))
        return paths

    def __repr__(self) -> str:
        # model + key NAME only — never the resolved key value (this can land in a log/trace).
        return f"WaveSpeedImageGenProvider(model={self._model!r}, key_name={self._key_name!r})"


def _data(response: dict[str, Any]) -> dict[str, Any]:
    """The WaveSpeed ``data`` envelope (defensive — never trust the wrapper exists)."""
    payload = response.get("data")
    return payload if isinstance(payload, dict) else {}


def _usage(payload: dict[str, Any]) -> ProviderUsage | None:
    """latencyMs from data.timings.inference, defensively — NEVER raises (poll rides the result, so
    a non-numeric / negative inference must degrade to None, not blow up the poll)."""
    timings = payload.get("timings")
    if not isinstance(timings, dict):
        return None
    try:
        latency = int(timings.get("inference"))  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return ProviderUsage(latencyMs=latency) if latency >= 0 else None


def _parse_ts(value: object) -> datetime:
    """Parse the provider's ISO created_at if present; else the real submit time (real I/O — not
    the mock's seeded epoch, which the determinism rule governs)."""
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.now(UTC)
