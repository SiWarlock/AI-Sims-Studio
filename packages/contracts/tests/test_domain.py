"""RED tests for the domain model (§12, Appendix A, DATA_MODEL.md) — slice 0.4a.

The 16 domain entities + their state-machine StrEnums + the structurally-expressible invariants,
guarded by a spec(§12) schema-snapshot. State MEMBERSHIP only (transitions are Phase-2 engine).
Open-registry keys (archetype/placementCategory) stay str (Invariant 6). The full exportability
gate (Inv 1) + ordered gates (Inv 5) are Phase-2 validator items (D16 pin) — only the structural
variant-ref part is encoded here.
"""

import json
from pathlib import Path

import pytest
from pydantic import BaseModel, ValidationError

from aisims_contracts.domain import (
    AssetVariant,
    AssetVariantState,
    CleanupStatus,
    CollectionPlan,
    ConceptCandidate,
    ConceptState,
    ExportArtifact,
    ExportMode,
    ExportReport,
    ExportState,
    FunctionalOverlay,
    ItemSpec,
    ItemState,
    MeshCandidate,
    MeshState,
    OverlayState,
    PipelineRun,
    Project,
    ProjectState,
    QaStatus,
    ReviewEvent,
    Severity,
    Step,
    StepState,
    StyleBible,
    Swatch,
    Trace,
    ValidationResult,
    ValidationScope,
)

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "domain.schema.json"

# Top-level persisted entities carry schemaVersion (§13); embedded value objects do not.
TOP_LEVEL_ENTITIES: list[type[BaseModel]] = [
    Project,
    CollectionPlan,
    ItemSpec,
    ConceptCandidate,
    MeshCandidate,
    AssetVariant,
    FunctionalOverlay,
    PipelineRun,
    Step,
    ValidationResult,
    ExportArtifact,
    ReviewEvent,
    Trace,
]
EMBEDDED_ENTITIES: list[type[BaseModel]] = [StyleBible, Swatch, ExportReport]

EXPECTED_ENUM_MEMBERS = {
    "ProjectState": (
        ProjectState,
        {
            "created",
            "planned",
            "generating",
            "curating",
            "validating",
            "exporting",
            "exported",
            "export-failed",
        },
    ),
    "ItemState": (
        ItemState,
        {
            "planned",
            "concept-pending",
            "concept-generating",
            "concept-review-needed",
            "mesh-pending",
            "mesh-generating",
            "mesh-qa-pending",
            "blender-cleanup-pending",
            "preview-ready",
            "needs-review",
            "export-ready",
            "failed",
            "excluded",
            "skipped",
            "unsupported",
            "cancelled",
            "test-installed",
            "in-game-verified",
            "in-game-failed",
        },
    ),
    "StepState": (
        StepState,
        {
            "pending",
            "running",
            "succeeded",
            "failed",
            "waiting-for-user",
            "cancelled",
            "retrying",
            "skipped",
        },
    ),
    "AssetVariantState": (AssetVariantState, {"candidate", "selected", "locked", "superseded"}),
    "ConceptState": (ConceptState, {"generated", "approved", "rejected", "superseded"}),
    "MeshState": (MeshState, {"generated", "accepted", "rejected", "superseded"}),
    "QaStatus": (QaStatus, {"pending", "pass", "fail"}),
    "CleanupStatus": (CleanupStatus, {"pending", "running", "done", "failed"}),
    "OverlayState": (OverlayState, {"draft", "validated", "approved", "invalid"}),
    "ExportState": (
        ExportState,
        {"building", "success", "success-with-warnings", "partial", "failed", "cancelled"},
    ),
    "ExportMode": (ExportMode, {"decor", "functional", "both"}),
    "Severity": (Severity, {"error", "warn", "info", "pass"}),
    "ValidationScope": (ValidationScope, {"project", "item", "mesh", "overlay", "export"}),
}


def _swatch() -> Swatch:
    return Swatch(id="s1", variantId="v1", label="default", texturePaths=["t.png"], isDefault=True)


def _variant(**overrides: object) -> AssetVariant:
    kwargs: dict[str, object] = {
        "id": "v1",
        "itemId": "i1",
        "conceptRef": "c1",
        "meshRef": "m1",
        "swatches": [_swatch()],
        "state": AssetVariantState.SELECTED,
    }
    kwargs.update(overrides)
    return AssetVariant(**kwargs)


def test_domain_models_present() -> None:  # spec(§12)
    """The 16 entities exist; top-level ones carry schemaVersion, embedded ones do not (§13)."""
    assert len(TOP_LEVEL_ENTITIES) == 13
    assert len(EMBEDDED_ENTITIES) == 3
    for model in TOP_LEVEL_ENTITIES:
        assert "schemaVersion" in model.model_fields, model.__name__
    for model in EMBEDDED_ENTITIES:
        assert "schemaVersion" not in model.model_fields, model.__name__


def test_state_enum_membership() -> None:  # spec(§12)
    """Each state StrEnum's members == the DATA_MODEL set (exact ==, no extras/omissions)."""
    for name, (enum_cls, expected) in EXPECTED_ENUM_MEMBERS.items():
        assert {member.value for member in enum_cls} == expected, name


def test_open_registry_keys_are_str() -> None:  # spec(§12)
    """Open-registry keys stay str, never closed enums (Invariant 6, §11)."""
    assert ItemSpec.model_fields["archetype"].annotation is str
    assert ItemSpec.model_fields["placementCategory"].annotation is str
    assert FunctionalOverlay.model_fields["archetype"].annotation is str


def test_structural_invariants() -> None:  # spec(§12)
    """Type-expressible invariants hold + reject violations (Inv 2, Inv 7, lineage ref)."""
    # Inv 2: a FunctionalOverlay references the SAME ItemSpec identity by id (a str ref), never an
    # embedded/duplicate ItemSpec.
    assert FunctionalOverlay.model_fields["sourceItemId"].annotation is str
    # Inv 7: an AssetVariant requires >=1 Swatch (the default appearance).
    _variant()
    with pytest.raises(ValidationError):
        _variant(swatches=[])
    # Variant lineage ref (the structural export-ready part, D16): a realized variant references
    # its source concept + mesh (required). The full exportability gate is the Phase-2 validator.
    with pytest.raises(ValidationError):
        AssetVariant.model_validate(
            {"id": "v1", "itemId": "i1", "swatches": [_swatch().model_dump()], "state": "candidate"}
        )


def test_domain_round_trip() -> None:  # spec(§12)
    """JSON round-trip preserves equality across the wire form (§4/§13)."""
    project = Project(
        id="p1",
        name="My Kitchen",
        prompt="a cozy retro kitchen set",
        desiredItemCount=8,
        status=ProjectState.PLANNED,
    )
    assert Project.model_validate_json(project.model_dump_json()) == project
    variant = _variant()
    assert AssetVariant.model_validate_json(variant.model_dump_json()) == variant


def test_boundary_rejection() -> None:  # spec(§12)
    """extra='forbid' rejects unknown fields + out-of-enum states (safety rule 6)."""
    with pytest.raises(ValidationError):
        ItemSpec.model_validate(
            {
                "id": "i1",
                "displayName": "Toaster",
                "archetype": "appliance",
                "placementCategory": "counter",
                "status": "planned",
                "bogusField": "boom",
            }
        )
    with pytest.raises(ValidationError):
        Step.model_validate({"id": "st1", "runId": "r1", "name": "concept", "state": "not-a-state"})


def test_domain_schema_snapshot() -> None:  # spec(§12)
    """§2.5-seam guard: the domain schema == the checked-in snapshot (a drift is the failure).

    Regenerate deliberately (never a blind regen) and review the diff:
        uv run python -c "import json; from aisims_contracts.domain import domain_schema; \
            json.dump(domain_schema(), open('tests/__snapshots__/domain.schema.json','w'), \
            indent=2, sort_keys=True)"
    """
    from aisims_contracts.domain import domain_schema

    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert domain_schema() == expected
