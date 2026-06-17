# [SAFETY-RULE-6 · Inv5 · D16] Graph-level ordered-gate wiring proof.
"""Inv5 safety pin (task 2.1, test 8 — graph wiring).

The graph wires the ordered-gate guard into each gate node: a Command(resume) that
targets a later gate while the run is paused at an earlier one is rejected
(no out-of-order advance). Structurally needs build_graph, so it rides with the
build commit; the guard itself is unit-pinned in test_gates_ordered.py.
"""

from __future__ import annotations

import pytest
from aisims_contracts import GateKind
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from graph import PipelineState, build_graph
from graph.gates import GateOrderError


def test_graph_rejects_out_of_order_resume(mem_saver: InMemorySaver) -> None:
    """Asserts a resume targeting a later gate while paused earlier is rejected. spec(§5)"""
    g = build_graph(mem_saver)
    cfg: RunnableConfig = {"configurable": {"thread_id": "ord"}}
    g.invoke(PipelineState(projectId="p", runId="r"), cfg, durability="sync")  # pause at plan_gate
    with pytest.raises(GateOrderError):
        # Resume targeting the mesh gate while paused at the plan gate.
        g.invoke(Command(resume={"gate": GateKind.MESH.value}), cfg, durability="sync")


def test_graph_rejects_unknown_gate_resume(mem_saver: InMemorySaver) -> None:
    """Asserts a resume naming an unknown gate is rejected (fail-closed GateOrderError). spec(§5)"""
    g = build_graph(mem_saver)
    cfg: RunnableConfig = {"configurable": {"thread_id": "bogus"}}
    g.invoke(PipelineState(projectId="p", runId="r"), cfg, durability="sync")  # pause at plan_gate
    with pytest.raises(GateOrderError):
        # An out-of-domain gate value must not escape as a bare ValueError.
        g.invoke(Command(resume={"gate": "not-a-gate"}), cfg, durability="sync")
