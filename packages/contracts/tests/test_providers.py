"""RED tests for the §7 provider-adapter contracts — slice 0.5a.

Freezes the three model-agnostic provider interfaces (Image3DProvider / ImageGenProvider /
LLMProvider) as Protocols + the value models they exchange (ProviderJobRef, PollResult,
PollStatus, ProviderUsage), with ErrorEnvelope (0.2) as the failure carrier. The value models
get a spec(§7) JSON-Schema snapshot; the Protocols (no JSON schema) get a signature-freeze test.
Concrete mock/real adapters are 0.8 / Phase-2, NOT here.
"""

import inspect
import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from types import ModuleType
from typing import Any, get_type_hints

import pytest
from pydantic import ValidationError

import aisims_contracts.providers as providers_mod
from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope
from aisims_contracts.providers import (
    Image3DProvider,
    ImageGenProvider,
    LLMProvider,
    PollResult,
    PollStatus,
    ProviderJobRef,
    ProviderUsage,
    providers_schema,
)

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "providers.schema.json"

EXPECTED_POLL_STATUS = {"submitted", "running", "succeeded", "failed", "expired"}

# Per-interface expected method → ordered non-self param names (the signature-freeze surface).
EXPECTED_SIGNATURES: dict[type, dict[str, list[str]]] = {
    Image3DProvider: {"submit": ["image", "params"], "poll": ["ref"], "fetch": ["urls"]},
    ImageGenProvider: {"submit": ["prompt", "params"], "poll": ["ref"], "fetch": ["urls"]},
    LLMProvider: {"complete": ["prompt", "params"], "structured": ["prompt", "schema", "params"]},
}


def _methods(cls: type) -> set[str]:
    """The Protocol's own declared methods (excludes dunders + Protocol machinery)."""
    return {n for n, v in vars(cls).items() if not n.startswith("_") and callable(v)}


def _job_ref() -> ProviderJobRef:
    return ProviderJobRef(
        provider="fal",
        model="hunyuan3d-2.1",
        jobId="job-1",
        submittedAt=datetime(2026, 6, 17, 12, 0, 0),
    )


def test_provider_interfaces_present() -> None:  # spec(§7)
    """The 3 provider interfaces exist, each exposing exactly its §7 method set."""
    assert _methods(Image3DProvider) == {"submit", "poll", "fetch"}
    assert _methods(ImageGenProvider) == {"submit", "poll", "fetch"}
    assert _methods(LLMProvider) == {"complete", "structured"}


def test_provider_interface_signatures() -> None:  # spec(§7)
    """Each Protocol freezes its method signatures (param names) + the contract-critical types.

    Protocols have no JSON schema, so this signature test is their §2.5-seam freeze (Q5): a
    drift in method set, parameter names, or the value-model return/param types fails here.
    """
    for interface, methods in EXPECTED_SIGNATURES.items():
        assert _methods(interface) == set(methods), interface.__name__
        for method_name, expected_params in methods.items():
            sig = inspect.signature(getattr(interface, method_name))
            params = [p for p in sig.parameters if p != "self"]
            assert params == expected_params, (interface.__name__, method_name)
    # Contract-critical return/param types (the value-model seam the interfaces hand around):
    assert get_type_hints(Image3DProvider.submit)["return"] is ProviderJobRef
    assert get_type_hints(Image3DProvider.poll)["return"] is PollResult
    assert get_type_hints(Image3DProvider.poll)["ref"] is ProviderJobRef
    assert get_type_hints(ImageGenProvider.submit)["return"] is ProviderJobRef
    assert get_type_hints(ImageGenProvider.poll)["return"] is PollResult
    assert get_type_hints(ImageGenProvider.poll)["ref"] is ProviderJobRef
    assert get_type_hints(LLMProvider.complete)["return"] is str
    # params is the open, model-agnostic seam (dict[str, Any]) — the §7 analogue of Inv6.
    assert get_type_hints(Image3DProvider.submit)["params"] == dict[str, Any]
    assert get_type_hints(LLMProvider.complete)["params"] == dict[str, Any]


def test_provider_job_ref_model() -> None:  # spec(§7)
    """ProviderJobRef has the 5 §7 fields (expiresAt optional); strict + round-trip."""
    assert set(ProviderJobRef.model_fields) == {
        "provider",
        "model",
        "jobId",
        "submittedAt",
        "expiresAt",
    }
    assert ProviderJobRef.model_fields["expiresAt"].annotation == (datetime | None)
    ref = _job_ref()
    assert ProviderJobRef.model_validate_json(ref.model_dump_json()) == ref
    with pytest.raises(ValidationError):
        ProviderJobRef.model_validate({**ref.model_dump(mode="json"), "bogus": 1})


def test_poll_status_members() -> None:  # spec(§7)
    """PollStatus membership == the §7 set (exact ==); includes 'expired' for the Tripo 24h race."""
    assert {m.value for m in PollStatus} == EXPECTED_POLL_STATUS
    assert PollStatus.EXPIRED.value == "expired"


def test_poll_result_model() -> None:  # spec(§7)
    """PollResult carries status + optional progress/urls/usage/error; strict + round-trips."""
    result = PollResult(
        status=PollStatus.RUNNING,
        progress=0.5,
        urls=None,
        usage=ProviderUsage(latencyMs=1200),
    )
    assert PollResult.model_validate_json(result.model_dump_json()) == result
    # progress is a structural [0,1] fraction (safety rule 6) — both bounds rejected.
    with pytest.raises(ValidationError):
        PollResult(status=PollStatus.RUNNING, progress=1.5)
    with pytest.raises(ValidationError):
        PollResult(status=PollStatus.RUNNING, progress=-0.001)
    with pytest.raises(ValidationError):
        PollResult.model_validate({"status": "running", "bogus": 1})


def test_cost_latency_carrier() -> None:  # spec(§7)
    """ProviderUsage: latencyMs required, costCents nullable (§21 price-table fallback)."""
    usage = ProviderUsage(latencyMs=900)
    assert usage.costCents is None
    assert ProviderUsage.model_fields["latencyMs"].is_required()
    assert ProviderUsage.model_fields["costCents"].annotation == (int | None)
    # latencyMs is mandatory — a usage record with no latency is rejected.
    with pytest.raises(ValidationError):
        ProviderUsage.model_validate({})
    with pytest.raises(ValidationError):
        ProviderUsage.model_validate({"latencyMs": 1, "bogus": 2})
    # latencyMs/costCents are non-negative structural ranges (Lesson 3).
    with pytest.raises(ValidationError):
        ProviderUsage(latencyMs=-1)
    with pytest.raises(ValidationError):
        ProviderUsage(latencyMs=1, costCents=-5)


def test_provider_failure_uses_error_envelope() -> None:  # spec(§17)
    """A failed poll carries the 0.2 ErrorEnvelope, not a bespoke error shape."""
    assert PollResult.model_fields["error"].annotation == (ErrorEnvelope | None)
    env = ErrorEnvelope(
        code=ErrorCode.PROVIDER_TIMEOUT,
        category=ErrorCategory.PROVIDER,
        retryable=True,
        creatorMessage="x",
        maintainerDetail="y",
    )
    result = PollResult(status=PollStatus.FAILED, error=env)
    assert PollResult.model_validate_json(result.model_dump_json()) == result
    assert result.error == env


def test_providers_import_direction(intra_imports: Callable[[ModuleType], set[str]]) -> None:
    """providers.py imports `error` only — its own §2.5 seam, sibling of domain (acyclic DAG).

    spec(§7). Extends the 0.4b intra-package DAG guard (helper hoisted to conftest): providers
    sits at the same layer as domain (both import error); it must NOT import ipc/domain/responses.
    """
    imports = intra_imports(providers_mod)
    assert imports == {"error"}, imports
    assert imports.isdisjoint({"ipc", "domain", "responses"}), imports


def test_providers_schema_snapshot() -> None:  # spec(§7)
    """§2.5-seam guard: the value-model schema == the checked-in snapshot (drift = failure).

    Regenerate deliberately (never a blind regen) and review the diff:
        uv run python -c "import json; from aisims_contracts.providers import providers_schema; \
            json.dump(providers_schema(), open('tests/__snapshots__/providers.schema.json','w'), \
            indent=2, sort_keys=True)"
    """
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert providers_schema() == expected
