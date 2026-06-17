# [SAFETY-RULE-6 · Inv5 · D16] Ordered approval gates — plan→concept→mesh→overlay→export.
"""Inv5 safety pin (task 2.1, test 8 — unit) — the ordered-gate guard.

Gates may fire ONLY in canonical order: no mesh before concept, no overlay before
mesh, no export before overlay; an out-of-order approval is rejected. GateKind (from
aisims_contracts) is the canonical enum. SAFETY-RULE-6 / Invariant 5 (§5), D16-pinned.

Pure unit pin — depends only on graph.gates + aisims_contracts.GateKind (no langgraph),
so the guard's enforcement code and its pin land atomically as the first commit.
"""

from __future__ import annotations

import pytest
from aisims_contracts import GateKind

from graph.gates import GATE_ORDER, GateOrderError, assert_gate_order, next_gate


def test_gates_strictly_ordered() -> None:
    """Asserts the canonical gate order and that out-of-order approval is rejected. spec(§5)"""
    assert GATE_ORDER == (
        GateKind.PLAN,
        GateKind.CONCEPT,
        GateKind.MESH,
        GateKind.OVERLAY,
        GateKind.EXPORT,
    )

    # (a) Happy path: each gate is admissible only once its predecessor is the cursor.
    cursor: GateKind | None = None
    for gate in GATE_ORDER:
        assert next_gate(cursor) == gate
        assert_gate_order(cursor, gate)  # must not raise
        cursor = gate
    assert next_gate(cursor) is None  # all gates passed

    # (b) Out-of-order is rejected (skipping a predecessor, or re-approving the cursor).
    with pytest.raises(GateOrderError):
        assert_gate_order(None, GateKind.MESH)  # plan + concept skipped
    with pytest.raises(GateOrderError):
        assert_gate_order(GateKind.PLAN, GateKind.MESH)  # concept skipped
    with pytest.raises(GateOrderError):
        assert_gate_order(GateKind.PLAN, GateKind.PLAN)  # no forward progress
    with pytest.raises(GateOrderError):
        # Nothing is approvable once the final gate is the cursor.
        assert_gate_order(GateKind.EXPORT, GateKind.EXPORT)
