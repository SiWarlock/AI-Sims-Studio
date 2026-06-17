"""RED tests for the §11 registry entry-schema contracts + load-time validator — slice 0.5c.

Freezes the 3 open-registry entry envelopes (PlacementType / FunctionalArchetype / DonorMapping), a
flexible rule representation (the tuning-graft / eligibility grammars are pinned by S3 — not
over-specified here), per-registry `registryVersion` collection wrappers, and a pure
`validate_registry` load-time validator (structural validity + version + id/key uniqueness only).
Registry content, Postgres loading, donor resolution, and rule-semantics evaluation are out.
"""

import json
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest
from pydantic import ValidationError

import aisims_contracts.registries as registries_mod
from aisims_contracts.error import ErrorCode
from aisims_contracts.registries import (
    DonorMapping,
    DonorMappingRegistry,
    FunctionalArchetype,
    FunctionalArchetypeRegistry,
    PlacementType,
    PlacementTypeRegistry,
    RegistryFinding,
    RegistryIssue,
    RuleSpec,
    registries_schema,
    validate_registry,
)

SNAPSHOT_PATH = Path(__file__).parent / "__snapshots__" / "registries.schema.json"

VALUE_MODELS = {
    "RuleSpec",
    "PlacementType",
    "FunctionalArchetype",
    "DonorMapping",
    "PlacementTypeRegistry",
    "FunctionalArchetypeRegistry",
    "DonorMappingRegistry",
    "RegistryFinding",
}


def _placement(**overrides: Any) -> PlacementType:
    kwargs: dict[str, Any] = {
        "id": "counter",
        "name": "Counter",
        "donorRef": "donor/counter",
        "footprintRules": [RuleSpec(kind="grid", params={"w": 1, "h": 1})],
    }
    kwargs.update(overrides)
    return PlacementType(**kwargs)


def _archetype(**overrides: Any) -> FunctionalArchetype:
    kwargs: dict[str, Any] = {
        "id": "seating",
        "name": "Seating",
        "donorRef": "donor/chair",
        "tuningGraftRules": [RuleSpec(kind="copy", params={"from": "OBJD"})],
        "eligibilityRules": [RuleSpec(kind="has-slot", params={})],
        "validationRules": [RuleSpec(kind="resource-present", params={"res": "FTPT"})],
    }
    kwargs.update(overrides)
    return FunctionalArchetype(**kwargs)


def _donor(**overrides: Any) -> DonorMapping:
    kwargs: dict[str, Any] = {
        "key": "chair-dining",
        "donorObjectKey": "0xABC",
        "requiredResources": ["OBJD", "COBJ"],
        "tuningKeys": ["price"],
        "preserveKeys": ["FTPT", "RIG"],
    }
    kwargs.update(overrides)
    return DonorMapping(**kwargs)


def test_registry_entry_models() -> None:  # spec(§11)
    """The 3 entry models have exact §11 field sets; extra='forbid'; round-trip."""
    assert set(PlacementType.model_fields) == {"id", "name", "donorRef", "footprintRules"}
    assert set(FunctionalArchetype.model_fields) == {
        "id",
        "name",
        "donorRef",
        "tuningGraftRules",
        "eligibilityRules",
        "validationRules",
    }
    assert set(DonorMapping.model_fields) == {
        "key",
        "donorObjectKey",
        "requiredResources",
        "tuningKeys",
        "preserveKeys",
    }
    for entry in (_placement(), _archetype(), _donor()):
        assert type(entry).model_validate_json(entry.model_dump_json()) == entry
    with pytest.raises(ValidationError):
        PlacementType.model_validate({**_placement().model_dump(), "bogus": 1})


def test_open_registry_not_enum() -> None:  # spec(§11)
    """Inv6: registry id/key/name are open ``str`` keys, never closed enums."""
    assert PlacementType.model_fields["id"].annotation is str
    assert PlacementType.model_fields["name"].annotation is str
    assert FunctionalArchetype.model_fields["id"].annotation is str
    assert DonorMapping.model_fields["key"].annotation is str


def test_registry_issue_members() -> None:  # spec(§11)
    """RegistryIssue membership == the closed set (exact ==, Lesson 2)."""
    assert {m.value for m in RegistryIssue} == {
        "missing-version",
        "duplicate-key",
        "malformed-entry",
    }


def test_rule_subgrammar_representation() -> None:  # spec(§11)
    """The rule lists are a flexible RuleSpec rep ({kind, open params}), NOT an over-specified typed
    grammar — spike S3 pins it in Phase 1; closing it now would be the Inv6 mistake."""
    assert PlacementType.model_fields["footprintRules"].annotation == list[RuleSpec]
    assert FunctionalArchetype.model_fields["tuningGraftRules"].annotation == list[RuleSpec]
    assert FunctionalArchetype.model_fields["eligibilityRules"].annotation == list[RuleSpec]
    assert FunctionalArchetype.model_fields["validationRules"].annotation == list[RuleSpec]
    assert set(RuleSpec.model_fields) == {"kind", "params"}
    assert RuleSpec.model_fields["kind"].annotation is str
    assert RuleSpec.model_fields["params"].annotation == dict[str, Any]
    # any kind + any params round-trips (open — not pre-empting S3).
    rs = RuleSpec(kind="anything-s3-will-define", params={"nested": {"x": [1, 2]}})
    assert RuleSpec.model_validate_json(rs.model_dump_json()) == rs


def test_registry_version_present() -> None:  # spec(§11)
    """Each registry collection carries an ``int`` registryVersion (§13 stamp; rule 4)."""
    assert PlacementTypeRegistry.model_fields["registryVersion"].annotation is int
    assert DonorMappingRegistry.model_fields["registryVersion"].annotation is int
    # constructing a registry without registryVersion is a structural failure.
    with pytest.raises(ValidationError):
        PlacementTypeRegistry.model_validate({"entries": []})


def test_validate_registry_ok() -> None:  # spec(§11)
    """A well-formed registry (version present, unique ids, valid entries) yields NO findings."""
    data = {
        "registryVersion": 1,
        "entries": [_placement().model_dump(), _placement(id="floor", name="Floor").model_dump()],
    }
    assert validate_registry(data, PlacementTypeRegistry) == []


def test_validate_registry_rejects() -> None:  # spec(§11)
    """Missing version / duplicate id-or-key / malformed entry / non-dict → the right finding."""
    every: list[RegistryFinding] = []

    # missing registryVersion
    missing = validate_registry({"entries": [_placement().model_dump()]}, PlacementTypeRegistry)
    assert any(f.issue is RegistryIssue.MISSING_VERSION for f in missing)
    every += missing

    # duplicate id within the registry (entryKey names the offender)
    dup = {"registryVersion": 1, "entries": [_placement().model_dump(), _placement().model_dump()]}
    dup_f = validate_registry(dup, PlacementTypeRegistry)
    assert any(f.issue is RegistryIssue.DUPLICATE_KEY and f.entryKey == "counter" for f in dup_f)
    every += dup_f

    # duplicate key on a DonorMapping (the key field, not id)
    dmdup = {"registryVersion": 1, "entries": [_donor().model_dump(), _donor().model_dump()]}
    dm_f = validate_registry(dmdup, DonorMappingRegistry)
    assert any(
        f.issue is RegistryIssue.DUPLICATE_KEY and f.entryKey == "chair-dining" for f in dm_f
    )
    every += dm_f

    # malformed entry exercised on the FunctionalArchetypeRegistry path (missing required 'name')
    bad_arch = {"registryVersion": 1, "entries": [{"id": "x", "donorRef": "d"}]}
    arch_f = validate_registry(bad_arch, FunctionalArchetypeRegistry)
    assert any(f.issue is RegistryIssue.MALFORMED_ENTRY for f in arch_f)
    every += arch_f

    # non-dict top-level data (the 0.7 loader may hand us any deserialized JSON shape)
    nondict = validate_registry([], PlacementTypeRegistry)
    assert any(f.issue is RegistryIssue.MALFORMED_ENTRY for f in nondict)
    every += nondict

    # EVERY finding across all variants carries the §17 VALIDATION_FAILED envelope.
    assert every
    assert all(f.error.code is ErrorCode.VALIDATION_FAILED for f in every)


def test_validate_registry_scope_boundary() -> None:  # spec(§11)
    """Q2 boundary: the load-time validator does NOT do donor resolution or rule-semantics — an
    unresolved donorRef / an exotic RuleSpec.kind is NOT a finding here (those are Phase-1/S3)."""
    data = {
        "registryVersion": 1,
        "entries": [
            _placement(
                donorRef="donor/does-not-exist-yet",
                footprintRules=[RuleSpec(kind="grammar-s3-has-not-pinned", params={"k": "v"})],
            ).model_dump()
        ],
    }
    assert validate_registry(data, PlacementTypeRegistry) == []


def test_registries_import_direction(intra_imports: Callable[[ModuleType], set[str]]) -> None:
    """registries.py imports `error` only — findings carry the §17 ErrorEnvelope; spec(§11).

    Disjoint from {ipc,domain,responses,providers,workers}: the registry seam couples to nothing but
    the shared error contract (uses the intra_imports conftest fixture).
    """
    imports = intra_imports(registries_mod)
    assert imports == {"error"}, imports
    assert imports.isdisjoint({"ipc", "domain", "responses", "providers", "workers"}), imports


def test_registries_schema_snapshot() -> None:  # spec(§11)
    """§2.5-seam guard: the registry schema == the checked-in snapshot (drift = failure).

    Regenerate deliberately (never a blind regen) and review the diff:
        uv run python -c "import json; from aisims_contracts.registries import registries_schema; \
            json.dump(registries_schema(), open('tests/__snapshots__/registries.schema.json','w'), \
            indent=2, sort_keys=True)"
    """
    assert set(registries_schema()) == VALUE_MODELS
    expected = json.loads(SNAPSHOT_PATH.read_text())
    assert registries_schema() == expected
