"""PipelineState shape pins (task 2.1, tests 1-2).

The graph-runtime State references domain entities BY ID and imports the §12 enums
from ``aisims_contracts`` — it never redefines a domain entity or enum (§5: "State
references domain entities by id, does not redefine them").
"""

from __future__ import annotations

import aisims_contracts
import pytest
from aisims_contracts import GateKind, ItemState
from pydantic import ValidationError

from graph.state import PipelineState

# The lean, by-id checkpoint shape: ids + status enums + job refs + gate cursor.
# artifactRefs/pollErrors added in 2.2 (still State-internal — fetched paths + poll envelopes).
EXPECTED_FIELDS = {
    "projectId",
    "runId",
    "itemStates",
    "providerJobRefs",
    "artifactRefs",
    "pollErrors",
    "gateCursor",
}


def test_pipeline_state_references_entities_by_id() -> None:
    """Asserts PipelineState is id+status-typed, with no embedded §12 entity body. spec(§5)"""
    s = PipelineState(
        projectId="proj-1",
        runId="run-1",
        itemStates={"item-1": ItemState.PLANNED},
    )
    assert s.projectId == "proj-1"
    assert s.runId == "run-1"
    assert s.itemStates["item-1"] is ItemState.PLANNED
    # The shape is exactly the by-id/status fields — no embedded ItemSpec/entity field.
    assert set(PipelineState.model_fields) == EXPECTED_FIELDS
    # An embedded entity body is NOT a valid status-map value (by-id only).
    with pytest.raises(ValidationError):
        PipelineState(
            projectId="p",
            runId="r",
            itemStates={"item-1": {"id": "item-1", "name": "chair"}},  # type: ignore[dict-item]
        )


def test_pipeline_state_imports_contract_enums() -> None:
    """Asserts gateCursor/itemStates use the *contract* enums by identity. spec(§12)"""
    s = PipelineState(
        projectId="p",
        runId="r",
        gateCursor=GateKind.PLAN,
        itemStates={"i": ItemState.MESH_PENDING},
    )
    # Identity, not a structurally-similar local redefinition.
    assert type(s.gateCursor) is aisims_contracts.GateKind
    assert type(s.itemStates["i"]) is aisims_contracts.ItemState
    # The state module must not shadow GateKind with a local enum.
    import graph.state as state_mod

    assert getattr(state_mod, "GateKind", aisims_contracts.GateKind) is aisims_contracts.GateKind
