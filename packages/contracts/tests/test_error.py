"""RED tests for the frozen ErrorEnvelope contract (§17, Appendix A).

ErrorEnvelope is the 6th frozen shared contract — carried in the SSE ``error`` event,
``Step.error``, and ``ValidationResult``, and emitted by every stage (mock + real). These
tests freeze its field set, its two closed enums, boundary rejection, JSON round-trip
stability, and the §2.5-seam schema snapshot (the shared-contract freeze before tracks fork).
"""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "error_envelope.schema.json"

EXPECTED_FIELDS = {
    "code",
    "category",
    "retryable",
    "creatorMessage",
    "maintainerDetail",
    "traceRef",
    "suggestedAction",
}
EXPECTED_REQUIRED = {"code", "category", "retryable", "creatorMessage", "maintainerDetail"}
EXPECTED_OPTIONAL = {"traceRef", "suggestedAction"}

# §17 closed code set (PROVIDER_AUTH/QUOTA spelled PROVIDER_AUTH_QUOTA — see Step-2.5 Q1).
EXPECTED_CODES = {
    "PROVIDER_TIMEOUT",
    "PROVIDER_RATE_LIMIT",
    "PROVIDER_AUTH_QUOTA",
    "PROVIDER_OUTAGE",
    "ARTIFACT_EXPIRED",
    "MALFORMED_OUTPUT",
    "MESH_QA_FAILED",
    "GEOM_EXPORT_FAILED",
    "DBPF_WRITE_FAILED",
    "TEST_INSTALL_FAILED",
    "DISK_FULL",
    "VALIDATION_FAILED",
    "SYSTEM",
}
EXPECTED_CATEGORIES = {
    "provider",
    "network",
    "validation",
    "geometry",
    "packaging",
    "budget",
    "system",
}


def test_error_envelope_field_set() -> None:  # spec(§17)
    """Field set + required/optional split == Appendix-A row (Step-2.5 Q4)."""
    assert set(ErrorEnvelope.model_fields) == EXPECTED_FIELDS
    required = {name for name, field in ErrorEnvelope.model_fields.items() if field.is_required()}
    optional = set(ErrorEnvelope.model_fields) - required
    assert required == EXPECTED_REQUIRED
    assert optional == EXPECTED_OPTIONAL


def test_error_code_enum_members() -> None:  # spec(§17)
    """`code` is a closed enum == the §17 set (exact membership, no extras/omissions)."""
    assert {member.value for member in ErrorCode} == EXPECTED_CODES


def test_error_category_enum_members() -> None:  # spec(§17)
    """`category` is a closed enum == the §17 category set."""
    assert {member.value for member in ErrorCategory} == EXPECTED_CATEGORIES


def test_error_envelope_rejects_unknown_code() -> None:  # spec(§17)
    """Out-of-enum `code` is rejected at the wire boundary (safety rule 6)."""
    with pytest.raises(ValidationError):
        ErrorEnvelope.model_validate(
            {
                "code": "NOT_A_REAL_CODE",
                "category": "system",
                "retryable": False,
                "creatorMessage": "x",
                "maintainerDetail": "y",
            }
        )


def test_error_envelope_rejects_unknown_category() -> None:  # spec(§17)
    """Out-of-enum `category` is rejected at the wire boundary (safety rule 6)."""
    with pytest.raises(ValidationError):
        ErrorEnvelope.model_validate(
            {
                "code": "SYSTEM",
                "category": "not_a_category",
                "retryable": False,
                "creatorMessage": "x",
                "maintainerDetail": "y",
            }
        )


def test_error_envelope_rejects_unknown_field() -> None:  # spec(§17)
    """extra='forbid': an unknown field is rejected at the boundary (safety rule 6)."""
    with pytest.raises(ValidationError):
        ErrorEnvelope.model_validate(
            {
                "code": "SYSTEM",
                "category": "system",
                "retryable": False,
                "creatorMessage": "x",
                "maintainerDetail": "y",
                "unexpectedField": "boom",
            }
        )


def test_error_envelope_round_trip() -> None:  # spec(§4)
    """`model_validate_json(model_dump_json(x)) == x` — JSON is the py↔ts wire form (§4)."""
    full = ErrorEnvelope(
        code=ErrorCode.PROVIDER_TIMEOUT,
        category=ErrorCategory.PROVIDER,
        retryable=True,
        creatorMessage="The image provider timed out.",
        maintainerDetail="POST /submit exceeded the 30s wall-clock budget.",
        traceRef="trace-abc123",
        suggestedAction="Retry in a moment.",
    )
    assert ErrorEnvelope.model_validate_json(full.model_dump_json()) == full

    minimal = ErrorEnvelope(
        code=ErrorCode.SYSTEM,
        category=ErrorCategory.SYSTEM,
        retryable=False,
        creatorMessage="Something went wrong.",
        maintainerDetail="Unhandled error in stage X.",
    )
    assert ErrorEnvelope.model_validate_json(minimal.model_dump_json()) == minimal


def test_error_envelope_schema_snapshot() -> None:  # spec(§17)
    """§2.5-seam guard: model_json_schema() == the checked-in snapshot (a drift is the failure)."""
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert ErrorEnvelope.model_json_schema() == expected, (
        "ErrorEnvelope JSON-Schema drifted from the frozen snapshot. If intentional, "
        "regenerate error_envelope.schema.json deliberately and re-review (never a silent regen)."
    )
