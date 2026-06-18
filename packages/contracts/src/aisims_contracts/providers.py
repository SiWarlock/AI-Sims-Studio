"""The §7 provider-adapter contracts — slice 0.5a.

The three model-agnostic provider interfaces (Image3DProvider / ImageGenProvider / LLMProvider)
as ``typing.Protocol`` seams, plus the value models they exchange (ProviderJobRef, PollResult,
PollStatus, ProviderUsage). The interfaces are model-agnostic by design (bakeoff, no model
lock-in): model-specific knobs ride in an open ``params: dict[str, Any]`` (the §7 analogue of the
Inv6 open-registry-key rule), validated per-model by the adapter impl (§16), never a closed
per-model schema here.

SHAPES only — concrete mock/real adapters are 0.8 / Phase-2; the §16 provider-output validation
(max-bytes/magic-byte/path-sanitize) is adapter-impl logic, not contract shape; ProviderConfig /
Secret are the Settings/onboarding surface (secrets in the OS keychain, safety rule 5), never a
field here. Import direction: ``providers`` imports ``error`` only — its own §2.5 seam, a sibling
of ``domain`` (both import ``error``); it does NOT import ipc/domain/responses. Conventions follow
0.2/0.3/0.4: ``extra="forbid"`` on wire models, camelCase fields, ``StrEnum`` for closed sets, one
``spec(§X)`` schema-snapshot per §2.5 seam (over the value models; the Protocols are frozen by the
signature test, having no JSON schema).
"""

from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from aisims_contracts.error import ErrorEnvelope

# A structured-output target — the pydantic model an LLMProvider.structured() call returns.
StructuredT = TypeVar("StructuredT", bound=BaseModel)


class _Provider(BaseModel):
    """Base for every provider value model: strict boundary (extra='forbid'), camelCase (§4)."""

    model_config = ConfigDict(extra="forbid")


class PollStatus(StrEnum):
    """The lifecycle of an async provider job (§7). ``expired`` covers the Tripo 24h URL-expiry
    race explicitly; adapters collapse provider-specific queue states onto submitted/running."""

    SUBMITTED = "submitted"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"


class ProviderUsage(_Provider):
    """Cost+latency carrier for a cloud op (§7/§21). ``latencyMs`` MUST be recorded for every cloud
    op; ``costCents`` SHOULD be (nullable — falls back to the §21 price-table estimate)."""

    latencyMs: int = Field(ge=0)
    costCents: int | None = Field(default=None, ge=0)


class ProviderJobRef(_Provider):
    """The reconcile-spine handle to an async provider job (§7) — persisted in graph State +
    Postgres so a resume can poll/re-fetch. ``expiresAt`` drives the Tripo 24h re-download race."""

    # min_length=1 (0.5b): a present provider/model/job id is a real identifier, never blank.
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    jobId: str = Field(min_length=1)
    submittedAt: datetime
    expiresAt: datetime | None = None


class PollResult(_Provider):
    """The result of polling a provider job (§7): ``status`` plus, where available, a [0,1]
    progress fraction, the output ``urls`` (on success), the ``usage`` carrier, and — on a failed
    or expired poll — the 0.2 ``ErrorEnvelope`` (§17 single failure contract, never re-rolled)."""

    status: PollStatus
    progress: float | None = Field(default=None, ge=0.0, le=1.0)
    urls: list[str] | None = None
    usage: ProviderUsage | None = None
    error: ErrorEnvelope | None = None


class Image3DProvider(Protocol):
    """Image-to-3D adapter seam (§7): submit a concept image, poll the async job, fetch outputs.
    Model-agnostic (Hunyuan3D / Tripo via fal / WaveSpeed bakeoff); concrete adapters are 0.8."""

    def submit(self, image: bytes, params: dict[str, Any]) -> ProviderJobRef: ...

    def poll(self, ref: ProviderJobRef) -> PollResult: ...

    def fetch(self, urls: list[str]) -> list[str]: ...


class ImageGenProvider(Protocol):
    """Text-to-image adapter seam (§7): submit a prompt, poll the async job, fetch outputs.
    Model-agnostic (FLUX.2 [pro] via WaveSpeed / Replicate / fal bakeoff); adapters are 0.8."""

    def submit(self, prompt: str, params: dict[str, Any]) -> ProviderJobRef: ...

    def poll(self, ref: ProviderJobRef) -> PollResult: ...

    def fetch(self, urls: list[str]) -> list[str]: ...


class LLMProvider(Protocol):
    """LLM adapter seam (§7): synchronous ``complete`` (free text) + ``structured`` (a typed model).
    Model-agnostic (Claude direct / OpenRouter bakeoff); concrete adapters are 0.8.

    These calls are synchronous (no ProviderJobRef/poll), so they carry no ``ProviderUsage`` —
    per §7 the per-op latency (MUST: node wall-clock) and cost (SHOULD: §21 price-table estimate)
    are recorded at the calling LangGraph node onto the domain ``Step`` (``Step.latencyMs`` /
    ``Step.costCents``), not on a contract result wrapper."""

    def complete(self, prompt: str, params: dict[str, Any]) -> str: ...

    def structured(
        self, prompt: str, schema: type[StructuredT], params: dict[str, Any]
    ) -> StructuredT: ...


# The frozen provider value-model surface, in stable definition order, for the §2.5-seam snapshot.
# (The Protocols have no JSON schema — they're frozen by the interface-signature test.)
_VALUE_MODELS: dict[str, type[BaseModel]] = {
    "ProviderJobRef": ProviderJobRef,
    "ProviderUsage": ProviderUsage,
    "PollResult": PollResult,
}


def providers_schema() -> dict[str, Any]:
    """The combined provider value-model surface for the §2.5-seam snapshot — each model's
    JSON-Schema (PollStatus + ProviderUsage + the embedded ErrorEnvelope ride in PollResult's
    ``$defs``)."""
    return {name: model.model_json_schema() for name, model in _VALUE_MODELS.items()}
