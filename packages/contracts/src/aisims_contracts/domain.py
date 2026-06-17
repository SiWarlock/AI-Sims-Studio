"""The domain model (§12, Appendix A) — the 15 Appendix-A entities (+ ExportReport) as Pydantic v2
models, their state-machine ``StrEnum``s, and the structurally-expressible invariants.

Conventions follow 0.2/0.3: the ``aisims_contracts`` package, ``extra="forbid"``, camelCase wire
fields, ``StrEnum`` for closed sets, schema-snapshot freeze. The contract encodes state MEMBERSHIP,
not transitions (Phase-2 engine). Open-registry keys (``archetype``/``placementCategory``) stay
``str`` (Invariant 6, §11). Relationships are referenced by id; only true value objects (StyleBible,
Swatch, ExportReport) are embedded. The IPC completion (REST response bodies + tightening 0.3's SSE
fields to these enums) is slice 0.4b.

Exportability gate (Invariant 1) + ordered gates (Invariant 5): only the STRUCTURAL variant-lineage
part is encoded here (AssetVariant requires its conceptRef + meshRef). The full 3-condition gate
(included ∧ a state=selected AssetVariant ∧ no blocking validation) and the ordered-gate sequencing
are the Phase-2 engine validator (D16-pinned, mandatory Phase-2 acceptance items).
"""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from aisims_contracts.error import ErrorEnvelope


# ===========================================================================================
# State-machine enums (§12 / DATA_MODEL.md "State Machines") — membership only, ==-pinned.
# ===========================================================================================
class ProjectState(StrEnum):
    CREATED = "created"
    PLANNED = "planned"
    GENERATING = "generating"
    CURATING = "curating"
    VALIDATING = "validating"
    EXPORTING = "exporting"
    EXPORTED = "exported"
    EXPORT_FAILED = "export-failed"


class ItemState(StrEnum):
    """13 base states + 6 audit-added (R-d). The contract holds all 19; transitions are Phase-2."""

    PLANNED = "planned"
    CONCEPT_PENDING = "concept-pending"
    CONCEPT_GENERATING = "concept-generating"
    CONCEPT_REVIEW_NEEDED = "concept-review-needed"
    MESH_PENDING = "mesh-pending"
    MESH_GENERATING = "mesh-generating"
    MESH_QA_PENDING = "mesh-qa-pending"
    BLENDER_CLEANUP_PENDING = "blender-cleanup-pending"
    PREVIEW_READY = "preview-ready"
    NEEDS_REVIEW = "needs-review"
    EXPORT_READY = "export-ready"
    FAILED = "failed"
    EXCLUDED = "excluded"
    # audit-added (R-d)
    SKIPPED = "skipped"
    UNSUPPORTED = "unsupported"
    CANCELLED = "cancelled"
    TEST_INSTALLED = "test-installed"
    IN_GAME_VERIFIED = "in-game-verified"
    IN_GAME_FAILED = "in-game-failed"


class StepState(StrEnum):
    """The 8-state Run/Step machine (PipelineRun.status + Step.state share it)."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    WAITING_FOR_USER = "waiting-for-user"
    CANCELLED = "cancelled"
    RETRYING = "retrying"
    SKIPPED = "skipped"


class AssetVariantState(StrEnum):
    CANDIDATE = "candidate"
    SELECTED = "selected"
    LOCKED = "locked"
    SUPERSEDED = "superseded"


class ConceptState(StrEnum):
    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class MeshState(StrEnum):
    """Overall MeshCandidate state; qa + cleanup are separate axes (QaStatus / CleanupStatus)."""

    GENERATED = "generated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class QaStatus(StrEnum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"


class CleanupStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class OverlayState(StrEnum):
    DRAFT = "draft"
    VALIDATED = "validated"
    APPROVED = "approved"
    INVALID = "invalid"


class ExportState(StrEnum):
    BUILDING = "building"
    SUCCESS = "success"
    SUCCESS_WITH_WARNINGS = "success-with-warnings"
    PARTIAL = "partial"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportMode(StrEnum):
    """A FunctionalOverlay's export mode — the decor/functional/both closed set (§12)."""

    DECOR = "decor"
    FUNCTIONAL = "functional"
    BOTH = "both"


class Severity(StrEnum):
    """ValidationResult severity (§17 ⊃ the IPC ValidationEvent severity, tightened in 0.4b)."""

    ERROR = "error"
    WARN = "warn"
    INFO = "info"
    PASS = "pass"


class ValidationScope(StrEnum):
    PROJECT = "project"
    ITEM = "item"
    MESH = "mesh"
    OVERLAY = "overlay"
    EXPORT = "export"


# ===========================================================================================
# Bases. _Domain = strict wire model; _Persisted adds schemaVersion (top-level entities, §13).
# ===========================================================================================
class _Domain(BaseModel):
    model_config = ConfigDict(extra="forbid")


class _Persisted(_Domain):
    schemaVersion: int = 1


# --- embedded value objects (no own schemaVersion — version with their parent) ---
class StyleBible(_Domain):
    """Collection-level style lock (embedded 1-1 under CollectionPlan)."""

    themeSummary: str
    palette: list[str] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)
    shapeLanguage: str | None = None
    eraRefs: list[str] = Field(default_factory=list)
    renderStyle: str | None = None
    negativeConstraints: list[str] = Field(default_factory=list)


class Swatch(_Domain):
    """A color/texture preset of one mesh (Sims-native, embedded under AssetVariant)."""

    id: str
    variantId: str
    label: str
    texturePaths: list[str] = Field(default_factory=list)
    thumbnailPath: str | None = None
    isDefault: bool = False


class ExportReport(_Domain):
    """Human-readable export summary (embedded 1-1 under ExportArtifact)."""

    projectName: str
    timestamp: datetime
    includedItems: list[str] = Field(default_factory=list)
    excludedItems: list[str] = Field(default_factory=list)
    functionalItems: list[str] = Field(default_factory=list)
    validationSummary: str | None = None
    warnings: list[str] = Field(default_factory=list)
    artifactPaths: list[str] = Field(default_factory=list)
    runRef: str | None = None


# --- top-level persisted entities (schemaVersion) ---
class Project(_Persisted):
    id: str
    name: str
    prompt: str
    styleNotes: str | None = None
    desiredItemCount: int
    outputMode: str | None = None
    generationMode: str | None = None
    status: ProjectState
    createdAt: datetime | None = None
    updatedAt: datetime | None = None
    planRef: str | None = None
    exportSettings: dict[str, Any] | None = None
    runRefs: list[str] = Field(default_factory=list)


class CollectionPlan(_Persisted):
    id: str
    projectId: str
    styleBible: StyleBible
    itemSpecIds: list[str] = Field(default_factory=list)
    version: int = 1
    approvalStatus: str | None = None


class ItemSpec(_Persisted):
    """The stable item identity. archetype/placementCategory are open-registry keys (str)."""

    id: str
    displayName: str
    description: str | None = None
    required: bool = False
    archetype: str
    placementCategory: str
    functionalEligibility: bool = False
    conceptPrompt: str | None = None
    meshContext: str | None = None
    swatchPlan: str | None = None
    status: ItemState
    include: bool = True


class ConceptCandidate(_Persisted):
    id: str
    itemId: str
    prompt: str
    imagePath: str | None = None
    provider: str | None = None
    status: ConceptState
    userDecision: str | None = None
    readinessScore: float | None = None


class MeshCandidate(_Persisted):
    id: str
    itemId: str
    sourceConceptId: str
    adapter: str
    adapterConfig: dict[str, Any] | None = None
    meshPath: str | None = None
    texturePaths: list[str] = Field(default_factory=list)
    state: MeshState
    qaStatus: QaStatus = QaStatus.PENDING
    qaScore: float | None = None
    cleanupStatus: CleanupStatus = CleanupStatus.PENDING
    normalizedIntermediatePath: str | None = None
    previewPath: str | None = None
    userDecision: str | None = None


class AssetVariant(_Persisted):
    """A selectable realized item. Requires lineage refs (conceptRef + meshRef) and ≥1 Swatch."""

    id: str
    itemId: str
    conceptRef: str
    meshRef: str
    swatches: list[Swatch] = Field(min_length=1)
    previewRefs: list[str] = Field(default_factory=list)
    exportReadiness: bool = False
    state: AssetVariantState = AssetVariantState.CANDIDATE


class FunctionalOverlay(_Persisted):
    """Behavior on the SAME item identity (Inv 2): sourceItemId is a ref, never a duplicate."""

    id: str
    sourceItemId: str
    sourceVariantId: str
    archetype: str
    donorRef: str | None = None
    userConfig: dict[str, Any] | None = None
    behaviorSummary: str | None = None
    validationStatus: OverlayState = OverlayState.DRAFT
    exportMode: ExportMode = ExportMode.BOTH


class PipelineRun(_Persisted):
    id: str
    projectId: str
    itemId: str | None = None
    runType: str
    status: StepState
    stepIds: list[str] = Field(default_factory=list)
    traceRef: str | None = None
    startedAt: datetime | None = None
    endedAt: datetime | None = None


class Step(_Persisted):
    id: str
    runId: str
    name: str
    state: StepState
    inputs: dict[str, Any] | None = None
    artifactRefs: list[str] = Field(default_factory=list)
    attempts: int = 0
    error: ErrorEnvelope | None = None
    costCents: int | None = None
    latencyMs: int | None = None


class ValidationResult(_Persisted):
    id: str
    scope: ValidationScope
    severity: Severity
    message: str
    suggestedAction: str | None = None
    relatedRef: str | None = None
    error: ErrorEnvelope | None = None


class ExportArtifact(_Persisted):
    id: str
    projectId: str
    outputPath: str | None = None
    includedItems: list[str] = Field(default_factory=list)
    functionalOverlays: list[str] = Field(default_factory=list)
    buildStatus: ExportState = ExportState.BUILDING
    report: ExportReport | None = None
    timestamp: datetime | None = None


class ReviewEvent(_Persisted):
    id: str
    projectId: str
    itemId: str
    candidateId: str | None = None
    artifactType: str
    decision: str
    reason: str | None = None
    notes: str | None = None
    timestamp: datetime


class Trace(_Persisted):
    id: str
    projectId: str
    itemId: str | None = None
    prompt: str | None = None
    planVersion: int | None = None
    specVersion: int | None = None
    worker: str | None = None
    modelOrTool: str | None = None
    inputs: dict[str, Any] | None = None
    artifactRefs: list[str] = Field(default_factory=list)
    startedAt: datetime | None = None
    endedAt: datetime | None = None
    status: StepState | None = None
    error: ErrorEnvelope | None = None
    costCents: int | None = None
    latencyMs: int | None = None
    validationRefs: list[str] = Field(default_factory=list)
    reviewEventRefs: list[str] = Field(default_factory=list)


# The frozen domain surface, in stable definition order, for the §2.5-seam snapshot.
_ALL_MODELS: dict[str, type[BaseModel]] = {
    "StyleBible": StyleBible,
    "Swatch": Swatch,
    "ExportReport": ExportReport,
    "Project": Project,
    "CollectionPlan": CollectionPlan,
    "ItemSpec": ItemSpec,
    "ConceptCandidate": ConceptCandidate,
    "MeshCandidate": MeshCandidate,
    "AssetVariant": AssetVariant,
    "FunctionalOverlay": FunctionalOverlay,
    "PipelineRun": PipelineRun,
    "Step": Step,
    "ValidationResult": ValidationResult,
    "ExportArtifact": ExportArtifact,
    "ReviewEvent": ReviewEvent,
    "Trace": Trace,
}


def domain_schema() -> dict[str, Any]:
    """The combined domain surface for the §2.5-seam snapshot — each entity's JSON-Schema
    (enums + embedded value objects ride in each model's ``$defs``)."""
    return {name: model.model_json_schema() for name, model in _ALL_MODELS.items()}
