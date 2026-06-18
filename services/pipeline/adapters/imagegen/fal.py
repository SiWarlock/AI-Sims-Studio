"""``FalImageGenProvider`` — fal (FLUX) concept images behind the frozen §7 seam.

A second bakeoff backend (EVAL-002) on the established foundation (LESSONS 9/10/11). fal's queue API
completes in TWO GETs: ``submit`` → ``request_id``; ``poll`` GETs the STATUS, and on ``COMPLETED``
GETs the RESULT response for the image urls. BOTH GETs are inside poll's guard so poll NEVER raises
(lesson 10) — a status- or result-GET failure (or a fal ``error``/``error_type``) rides
``PollResult.error``. ``submit``/``fetch`` RAISE (no result error field). Keys via the
``SecretsAccessor`` at call time (rule 5); ``fetch`` reuses the hardened ``get_bytes`` (SSRF +
byte-cap) + ``validate_content`` + ``safe_scratch_path`` — the §16 path is NOT re-implemented.
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

DEFAULT_BASE_URL = "https://queue.fal.run"
DEFAULT_MODEL = "fal-ai/flux-pro/v1.1"
DEFAULT_KEY_NAME = "FAL_KEY"
DEFAULT_TIMEOUT = 60.0
_IMAGE_KINDS = {ContentKind.PNG, ContentKind.JPEG, ContentKind.WEBP}

# fal queue status → our §7 PollStatus, for the pending states.
_PENDING_STATUS = {"IN_QUEUE": PollStatus.SUBMITTED, "IN_PROGRESS": PollStatus.RUNNING}
_PENDING_PROGRESS = {PollStatus.SUBMITTED: 0.0, PollStatus.RUNNING: 0.5}


def build_submit_body(prompt: str, params: dict[str, Any]) -> dict[str, Any]:
    """fal FLUX submit body — prompt + optional seed/image_size; png output. Pure (unit-testable —
    vcr matches on method+uri, not body)."""
    body: dict[str, Any] = {"prompt": prompt, "num_images": 1, "output_format": "png"}
    if "seed" in params:
        body["seed"] = int(params["seed"])
    if "image_size" in params:
        body["image_size"] = params["image_size"]
    return body


class FalImageGenProvider:
    """Synchronous-call fal (FLUX) adapter. Conforms to the frozen §7 ImageGenProvider Protocol."""

    PROVIDER = "fal"

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
        return {"Authorization": f"Key {key}", "content-type": "application/json"}

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
        request_id = data.get("request_id")
        if not request_id:
            raise ProviderError(
                build_envelope(
                    ErrorCode.MALFORMED_OUTPUT,
                    maintainer_detail=f"submit response missing request_id from {self._host}",
                )
            )
        # fal submit carries no created_at — real submit time (real I/O, not a mock seeded epoch)
        return ProviderJobRef(
            provider=self.PROVIDER,
            model=self._model,
            jobId=str(request_id),
            submittedAt=datetime.now(UTC),
        )

    def poll(self, ref: ProviderJobRef) -> PollResult:
        # poll NEVER raises (lesson 10). Inlined (not a helper) so the whole flow — the status GET,
        # the fal error fields, AND the second (result) GET on COMPLETED — is provably covered: each
        # GET has its own guard riding PollResult.error, and the post-GET parsing is defensive.
        try:
            key = self._key()
            status_url = f"{self._base_url}/{self._model}/requests/{ref.jobId}/status"
            with open_client(self._client, self._timeout) as client:
                status_data = request_json(
                    client, "GET", status_url, headers=self._auth_headers(key), host=self._host
                )
        except ProviderError as exc:
            return PollResult(status=PollStatus.FAILED, error=exc.envelope)

        # fal signals a job failure via error/error_type — presence-based (a falsy-but-present value
        # is still a failure), not truthiness.
        if status_data.get("error") is not None or status_data.get("error_type") is not None:
            return PollResult(
                status=PollStatus.FAILED,
                error=build_envelope(
                    ErrorCode.PROVIDER_OUTAGE, maintainer_detail="fal reported a job error"
                ),
            )

        status = str(status_data.get("status", ""))
        if status != "COMPLETED":
            mapped = _PENDING_STATUS.get(status, PollStatus.RUNNING)
            return PollResult(status=mapped, progress=_PENDING_PROGRESS[mapped])

        # COMPLETED → the second GET for the result response (image urls). A failure here also rides
        # PollResult.error, RETRYABLE — the job IS done, so Phase-2 can re-fetch the result.
        result_url = f"{self._base_url}/{self._model}/requests/{ref.jobId}"
        try:
            with open_client(self._client, self._timeout) as client:
                result = request_json(
                    client, "GET", result_url, headers=self._auth_headers(key), host=self._host
                )
        except ProviderError:
            return PollResult(
                status=PollStatus.FAILED,
                error=build_envelope(
                    ErrorCode.PROVIDER_OUTAGE,
                    maintainer_detail="fal result fetch failed after COMPLETED (retryable)",
                ),
            )

        images = result.get("images")
        urls = (
            [str(img["url"]) for img in images if isinstance(img, dict) and img.get("url")]
            if isinstance(images, list)
            else []
        )
        usage = _usage(status_data)
        if usage is not None:
            usage = usage.model_copy(
                update={"costCents": estimate_cost(self.PROVIDER, self._model)}
            )
        return PollResult(status=PollStatus.SUCCEEDED, progress=1.0, urls=urls, usage=usage)

    def fetch(self, urls: list[str]) -> list[str]:
        # §16 trust boundary — identical to WaveSpeed: count-cap, then SSRF+size-guarded download +
        # magic-byte validation before bytes touch scratch. Every violation RAISES (no error field).
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
        return f"FalImageGenProvider(model={self._model!r}, key_name={self._key_name!r})"


def _usage(status_data: dict[str, Any]) -> ProviderUsage | None:
    """latencyMs from the COMPLETED status metrics.inference_time (fal reports SECONDS → ms),
    defensively — never raises (poll rides the result)."""
    metrics = status_data.get("metrics")
    inference = metrics.get("inference_time") if isinstance(metrics, dict) else None
    try:
        latency = int(float(inference) * 1000)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return ProviderUsage(latencyMs=latency) if latency >= 0 else None
