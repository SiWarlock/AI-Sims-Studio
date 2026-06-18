"""The §11 registry entry-schema contracts + the load-time validator — slice 0.5c.

The three open registries (PlacementType / FunctionalArchetype / DonorMapping) are data-driven,
version-controlled config = source of truth (§11), loaded + validated into the §13 store as a read
cache. This module freezes the entry ENVELOPES + a flexible ``RuleSpec`` rule representation + a
per-registry ``registryVersion`` collection wrapper + a pure ``validate_registry`` load-time
validator. The registries stay OPEN (Inv6): id/key/name are ``str``, adding an entry is
config+donor+test, never an enum/engine change.

The tuning-graft + eligibility sub-grammars are pinned by spike S3 (Phase 1) — so the rule lists are
``list[RuleSpec]`` (a thin ``{kind, open params}`` envelope), deliberately NOT a typed grammar;
closing it now is the same regression as closing an open registry. ``validate_registry``
checks ONLY structural validity + ``registryVersion`` present + id/key uniqueness — NOT donor
resolution (Donor-Library / Phase-1) or rule-semantics evaluation (S3 / the engine). It is the
eventual load-time enforcement point for Inv6 (the domain ``archetype``/``placementCategory`` keys
validate against these registries), but the registry *content* + loading are 0.7 / runtime.

Import direction: ``registries`` imports ``error`` only (findings carry the §17 ``ErrorEnvelope`` so
the 0.7 store loader surfaces registry-load failures via the standard channel); it does NOT import
ipc/domain/responses/providers/workers. Conventions follow 0.2–0.5b.
"""

from abc import abstractmethod
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from aisims_contracts.error import ErrorCategory, ErrorCode, ErrorEnvelope


class _Registry(BaseModel):
    """Base for every registry value model: strict boundary (extra='forbid'), camelCase (§4)."""

    model_config = ConfigDict(extra="forbid")


class RuleSpec(_Registry):
    """One rule in a registry entry's rule list — a thin open envelope: a ``kind`` tag + an open
    ``params`` bag. The tuning-graft/eligibility grammar is pinned by spike S3; this stays flexible
    so the freeze doesn't pre-empt the spike (the §11 analogue of the open-key rule)."""

    # min_length=1 (0.5b): kind is the rule's identifying tag, never blank (Inv6 keeps it open str).
    kind: str = Field(min_length=1)
    params: dict[str, Any] = Field(default_factory=dict)


# --- entry models (§11): open registries — id/key/name are str (Inv6), never closed enums ---
class PlacementType(_Registry):
    # min_length=1 (0.5b): id + donorRef (uniqueness key / ref) never blank; name stays plain.
    id: str = Field(min_length=1)
    name: str
    donorRef: str = Field(min_length=1)
    footprintRules: list[RuleSpec] = Field(default_factory=list)


class FunctionalArchetype(_Registry):
    # min_length=1 (0.5b): id + donorRef (uniqueness key / ref) never blank; name stays plain.
    id: str = Field(min_length=1)
    name: str
    donorRef: str = Field(min_length=1)
    tuningGraftRules: list[RuleSpec] = Field(default_factory=list)
    eligibilityRules: list[RuleSpec] = Field(default_factory=list)
    validationRules: list[RuleSpec] = Field(default_factory=list)


class DonorMapping(_Registry):
    # min_length=1 (0.5b): key (uniqueness key) + donorObjectKey (ref) are never blank.
    key: str = Field(min_length=1)
    donorObjectKey: str = Field(min_length=1)
    requiredResources: list[str] = Field(default_factory=list)
    tuningKeys: list[str] = Field(default_factory=list)
    preserveKeys: list[str] = Field(default_factory=list)


# --- versioned collection wrappers (§11/§13): one registryVersion per registry file ---
class _RegistryFile(_Registry):
    """Base for a registry collection: the ``registryVersion`` stamp + the uniqueness key accessor
    (overridden per registry — ``id`` for Placement/Archetype, ``key`` for DonorMapping)."""

    registryVersion: int

    @abstractmethod
    def entry_keys(self) -> list[str]:
        """The uniqueness keys of this registry's entries (id or key, per subclass)."""
        ...


class PlacementTypeRegistry(_RegistryFile):
    entries: list[PlacementType] = Field(default_factory=list)

    def entry_keys(self) -> list[str]:
        return [entry.id for entry in self.entries]


class FunctionalArchetypeRegistry(_RegistryFile):
    entries: list[FunctionalArchetype] = Field(default_factory=list)

    def entry_keys(self) -> list[str]:
        return [entry.id for entry in self.entries]


class DonorMappingRegistry(_RegistryFile):
    entries: list[DonorMapping] = Field(default_factory=list)

    def entry_keys(self) -> list[str]:
        return [entry.key for entry in self.entries]


# --- load-time validator findings ---
class RegistryIssue(StrEnum):
    """The closed set of load-time registry issues (structural only — Q2 scope)."""

    MISSING_VERSION = "missing-version"
    DUPLICATE_KEY = "duplicate-key"
    MALFORMED_ENTRY = "malformed-entry"


class RegistryFinding(_Registry):
    """A load-time registry validation finding: a granular registry-local ``issue`` + the §17
    ``ErrorEnvelope`` (so the 0.7 store loader surfaces it through the standard error channel);
    ``entryKey`` names the offending entry where applicable."""

    issue: RegistryIssue
    error: ErrorEnvelope
    entryKey: str | None = None


def _envelope(detail: str) -> ErrorEnvelope:
    """A VALIDATION_FAILED envelope (§17) for a registry finding — structural, never retryable."""
    return ErrorEnvelope(
        code=ErrorCode.VALIDATION_FAILED,
        category=ErrorCategory.VALIDATION,
        retryable=False,
        creatorMessage="A registry config failed load-time validation.",
        maintainerDetail=detail,
    )


def _findings_from_error(exc: ValidationError) -> list[RegistryFinding]:
    """Map a ValidationError to structural findings (missing-version / malformed-entry)."""
    findings: list[RegistryFinding] = []
    for err in exc.errors():
        loc = err["loc"]
        if loc == ("registryVersion",) and err["type"] == "missing":
            findings.append(
                RegistryFinding(
                    issue=RegistryIssue.MISSING_VERSION,
                    error=_envelope("registryVersion is required (§13 version stamp)"),
                )
            )
        else:
            path = ".".join(str(part) for part in loc) or "<root>"
            findings.append(
                RegistryFinding(
                    issue=RegistryIssue.MALFORMED_ENTRY,
                    error=_envelope(f"malformed registry data at {path}: {err['msg']}"),
                )
            )
    return findings


def validate_registry(data: object, registry_type: type[_RegistryFile]) -> list[RegistryFinding]:
    """Pure load-time validation of a registry config (§11): structure + ``registryVersion`` present
    + id/key uniqueness. Returns findings ([] = valid). Does NOT resolve donors or evaluate rule
    semantics (Q2 — Phase-1/S3/engine). No I/O; the 0.7 store loader is the production caller."""
    try:
        registry = registry_type.model_validate(data)
    except ValidationError as exc:
        return _findings_from_error(exc)
    findings: list[RegistryFinding] = []
    # One DUPLICATE_KEY finding per repeat occurrence (N copies of a key → N-1 findings).
    seen: set[str] = set()
    for key in registry.entry_keys():
        if key in seen:
            findings.append(
                RegistryFinding(
                    issue=RegistryIssue.DUPLICATE_KEY,
                    error=_envelope(f"duplicate registry key: {key!r}"),
                    entryKey=key,
                )
            )
        seen.add(key)
    return findings


# The frozen registry value-model surface for the §2.5-seam snapshot (the _RegistryFile base is a
# private impl detail — not snapshotted; the wrappers inherit its registryVersion field).
_VALUE_MODELS: dict[str, type[BaseModel]] = {
    "RuleSpec": RuleSpec,
    "PlacementType": PlacementType,
    "FunctionalArchetype": FunctionalArchetype,
    "DonorMapping": DonorMapping,
    "PlacementTypeRegistry": PlacementTypeRegistry,
    "FunctionalArchetypeRegistry": FunctionalArchetypeRegistry,
    "DonorMappingRegistry": DonorMappingRegistry,
    "RegistryFinding": RegistryFinding,
}


def registries_schema() -> dict[str, Any]:
    """The combined §11 registry surface for the §2.5-seam snapshot — each model's JSON-Schema
    (RuleSpec / the entry models / RegistryIssue / the embedded ErrorEnvelope ride in ``$defs``)."""
    return {name: model.model_json_schema() for name, model in _VALUE_MODELS.items()}
