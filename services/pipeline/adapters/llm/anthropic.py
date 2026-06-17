"""``AnthropicLLMProvider`` — Claude direct, behind the frozen §7 ``LLMProvider`` seam.

Raw httpx against the Messages API (``POST /v1/messages``): ``complete`` reads the first text block;
``structured`` forces a single tool (derived from ``schema.model_json_schema()``) and re-validates
the tool ``input`` against the caller's schema. Keys are pulled from the ``SecretsAccessor`` AT CALL
TIME only (never stored on the instance, never in repr/logs/traces — safety rule 5).
"""

from __future__ import annotations

from typing import Any

import httpx
from aisims_contracts.error import ErrorCode
from pydantic import BaseModel

from adapters.errors import ProviderError, build_envelope
from obs.secrets import SecretsAccessor

from ._base import extract_and_validate, extract_text, open_client, post_json

DEFAULT_BASE_URL = "https://api.anthropic.com"
DEFAULT_KEY_NAME = "ANTHROPIC_API_KEY"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MAX_TOKENS = 1024


def _tool_input(data: dict[str, Any]) -> dict[str, Any]:
    """The ``input`` of the first ``tool_use`` content block (the forced structured output)."""
    block = next(b for b in data["content"] if b.get("type") == "tool_use")
    payload: dict[str, Any] = block["input"]
    return payload


class AnthropicLLMProvider:
    """Synchronous Claude-direct adapter. Conforms to the frozen §7 ``LLMProvider`` Protocol."""

    def __init__(
        self,
        *,
        secrets: SecretsAccessor,
        model: str,
        key_name: str = DEFAULT_KEY_NAME,
        base_url: str = DEFAULT_BASE_URL,
        anthropic_version: str = ANTHROPIC_VERSION,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        timeout: float = 30.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._secrets = secrets  # accessor reference only — NEVER the resolved key (rule 5)
        self._model = model
        self._key_name = key_name
        self._base_url = base_url.rstrip("/")
        self._host = httpx.URL(base_url).host
        self._version = anthropic_version
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
        return {
            "x-api-key": key,
            "anthropic-version": self._version,
            "content-type": "application/json",
        }

    def _max(self, params: dict[str, Any]) -> int:
        return int(params.get("max_tokens", self._max_tokens))

    def complete(self, prompt: str, params: dict[str, Any]) -> str:
        key = self._key()  # pulled at call time, used locally, never retained
        body = {
            "model": self._model,
            "max_tokens": self._max(params),
            "messages": [{"role": "user", "content": prompt}],
        }
        with open_client(self._client, self._timeout) as client:
            data = post_json(
                client,
                f"{self._base_url}/v1/messages",
                headers=self._headers(key),
                json_body=body,
                host=self._host,
            )
        return extract_text(data, lambda d: d["content"][0]["text"])

    def structured[T: BaseModel](self, prompt: str, schema: type[T], params: dict[str, Any]) -> T:
        key = self._key()
        tool_name = schema.__name__
        body = {
            "model": self._model,
            "max_tokens": self._max(params),
            "messages": [{"role": "user", "content": prompt}],
            "tools": [
                {
                    "name": tool_name,
                    "description": f"Emit a {tool_name} object.",
                    "input_schema": schema.model_json_schema(),
                }
            ],
            "tool_choice": {"type": "tool", "name": tool_name},
        }
        with open_client(self._client, self._timeout) as client:
            data = post_json(
                client,
                f"{self._base_url}/v1/messages",
                headers=self._headers(key),
                json_body=body,
                host=self._host,
            )
        return extract_and_validate(schema, data, _tool_input)

    def __repr__(self) -> str:
        # model + key NAME only — never the resolved key value (this can land in a log/trace).
        return f"AnthropicLLMProvider(model={self._model!r}, key_name={self._key_name!r})"
