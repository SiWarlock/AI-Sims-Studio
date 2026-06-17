"""``OpenRouterLLMProvider`` — OpenAI-compatible chat-completions, behind the frozen §7 seam.

Raw httpx against ``POST /api/v1/chat/completions`` with a ``Bearer`` key: ``complete`` reads
``choices[0].message.content``; ``structured`` requests ``response_format=json_schema`` (derived
from ``schema.model_json_schema()``) and re-validates the returned JSON-string content against the
caller's schema. Keys are pulled from the ``SecretsAccessor`` AT CALL TIME only (rule 5).
"""

from __future__ import annotations

from typing import Any

import httpx
from aisims_contracts.error import ErrorCode
from pydantic import BaseModel

from adapters._http import open_client, post_json
from adapters.errors import ProviderError, build_envelope
from obs.secrets import SecretsAccessor

from ._base import extract_and_validate, extract_text

DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_KEY_NAME = "OPENROUTER_API_KEY"
DEFAULT_MAX_TOKENS = 1024


def _message_content(data: dict[str, Any]) -> str:
    """The assistant message content of the first choice (a free-text str, or a JSON string when
    ``response_format`` was a json_schema)."""
    content: str = data["choices"][0]["message"]["content"]
    return content


class OpenRouterLLMProvider:
    """Synchronous OpenRouter adapter (OpenAI-compatible). Conforms to the frozen §7 seam."""

    def __init__(
        self,
        *,
        secrets: SecretsAccessor,
        model: str,
        key_name: str = DEFAULT_KEY_NAME,
        base_url: str = DEFAULT_BASE_URL,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._secrets = secrets  # accessor reference only — NEVER the resolved key (rule 5)
        self._model = model
        self._key_name = key_name
        self._base_url = base_url.rstrip("/")
        self._host = httpx.URL(base_url).host
        self._max_tokens = max_tokens
        self._timeout = timeout
        self._client = http_client

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

    def _headers(self, key: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {key}", "content-type": "application/json"}

    def _max(self, params: dict[str, Any]) -> int:
        return int(params.get("max_tokens", self._max_tokens))

    def complete(self, prompt: str, params: dict[str, Any]) -> str:
        key = self._key()
        body = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self._max(params),
        }
        with open_client(self._client, self._timeout) as client:
            data = post_json(
                client,
                f"{self._base_url}/chat/completions",
                headers=self._headers(key),
                json_body=body,
                host=self._host,
            )
        return extract_text(data, _message_content)

    def structured[T: BaseModel](self, prompt: str, schema: type[T], params: dict[str, Any]) -> T:
        key = self._key()
        body = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": self._max(params),
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "strict": True,
                    "schema": schema.model_json_schema(),
                },
            },
        }
        with open_client(self._client, self._timeout) as client:
            data = post_json(
                client,
                f"{self._base_url}/chat/completions",
                headers=self._headers(key),
                json_body=body,
                host=self._host,
            )
        # content is a JSON string under response_format → extract_and_validate parses + validates.
        return extract_and_validate(schema, data, _message_content)

    def __repr__(self) -> str:
        return f"OpenRouterLLMProvider(model={self._model!r}, key_name={self._key_name!r})"
