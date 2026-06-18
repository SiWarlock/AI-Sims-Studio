"""``PipelineState`` — the typed LangGraph checkpoint state for a pipeline run.

References §12 domain entities BY ID (project/run/item ids + status enums + provider
job refs + the current gate cursor); it does NOT redefine or embed domain entity
bodies (§5 ownership partition — the checkpoint is authoritative for graph-execution
position only; the store repository owns entity rows). Every enum is imported from the
frozen ``aisims_contracts`` package; none are redefined here.
"""

from __future__ import annotations

from aisims_contracts import ErrorEnvelope, GateKind, ItemState, ProviderJobRef
from pydantic import BaseModel, ConfigDict, Field


class PipelineState(BaseModel):
    """Lean, by-id graph state: ids + status enums + provider job refs + gate cursor."""

    model_config = ConfigDict(extra="forbid")

    projectId: str
    runId: str
    # Per-item status by id — NOT embedded ItemSpec bodies (the store owns those rows).
    itemStates: dict[str, ItemState] = Field(default_factory=dict)
    # Cloud job references by item/step id (populated by the two-phase cloud nodes, 2.2).
    providerJobRefs: dict[str, ProviderJobRef] = Field(default_factory=dict)
    # Fetched output scratch-path refs by step key (the cloud poll node, 2.2) — echoes the
    # domain Step.artifactRefs vocabulary; State-internal (paths, not entity rows).
    artifactRefs: dict[str, list[str]] = Field(default_factory=dict)
    # The §17 ErrorEnvelope surfaced by a failed/expired poll, by step key (never re-rolled);
    # the reconcile DECISION (re-submit / regenerate) is 2.4.
    pollErrors: dict[str, ErrorEnvelope] = Field(default_factory=dict)
    # The gate the run has most recently passed (None before the plan gate); the
    # authoritative ordered-gate cursor (Inv5).
    gateCursor: GateKind | None = None
