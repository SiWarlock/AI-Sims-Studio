"""StateGraph topology + gate-pause pins (task 2.1, tests 3-4).

Five stage nodes wired START→plan→concept→mesh→overlay→export→END, each fronted by
an ``interrupt()`` approval gate (§5: one node/subgraph per stage; gates =
interrupt()/Command(resume)).
"""

from __future__ import annotations

from aisims_contracts import GateKind
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from graph import PipelineState, build_graph

STAGE_ORDER = ["plan", "concept", "mesh", "overlay", "export"]


def _stage_path(compiled: object) -> list[str]:
    """Walk the compiled graph from __start__, returning stage nodes in edge order."""
    drawable = compiled.get_graph()  # type: ignore[attr-defined]
    succ: dict[str, list[str]] = {}
    for edge in drawable.edges:
        succ.setdefault(edge.source, []).append(edge.target)
    order: list[str] = []
    node, seen = "__start__", set()
    while node in succ and node not in seen:
        seen.add(node)
        assert len(succ[node]) == 1, f"non-linear topology: {node} → {succ[node]}"
        nxt = succ[node][0]
        if nxt in STAGE_ORDER:
            order.append(nxt)
        node = nxt
    return order


def test_build_graph_has_five_ordered_stage_nodes(mem_saver: InMemorySaver) -> None:
    """Asserts the 5 stage nodes exist and are linearly wired in pipeline order. spec(§5)"""
    g = build_graph(mem_saver)
    nodes = set(g.get_graph().nodes)
    for stage in STAGE_ORDER:
        assert stage in nodes
    assert _stage_path(g) == STAGE_ORDER


def test_each_gate_interrupts(mem_saver: InMemorySaver) -> None:
    """Asserts a run pauses at the plan gate via interrupt(); resume advances. spec(§5)"""
    g = build_graph(mem_saver)
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-build"}}
    out = g.invoke(PipelineState(projectId="p", runId="r"), cfg, durability="sync")
    assert "__interrupt__" in out
    assert g.get_state(cfg).next == ("plan_gate",)
    payload = out["__interrupt__"][0].value
    assert payload["gate"] == GateKind.PLAN.value
    # Command(resume) continues from the paused position to the next gate.
    out2 = g.invoke(Command(resume="approve"), cfg, durability="sync")
    assert "__interrupt__" in out2
    assert g.get_state(cfg).next == ("concept_gate",)
