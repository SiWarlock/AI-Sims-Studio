"""``build_graph`` — the resumable LangGraph StateGraph spine (task 2.1).

One no-op stage node per pipeline stage (plan→concept→mesh→overlay→export), each
fronted by an ``interrupt()`` approval gate, wired linearly START→…→END. The real
stage bodies (provider / two-phase cloud calls) land in 2.2; here they are pure
placeholders. The gate nodes enforce the Inv5 ordering via ``graph.gates``.

durability: langgraph 1.x realizes ``durability`` as a runtime argument on
``invoke()`` / ``stream()`` — it is NOT a ``compile()`` parameter. The run-time caller
(the 2.3 scheduler) passes ``durability="sync"`` for this gate-bearing graph so
checkpoints survive process exit.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aisims_contracts import GateKind
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import interrupt

from graph.gates import GATE_ORDER, GateOrderError, assert_gate_order
from graph.state import PipelineState

# A GateKind-keyed hook invoked as each stage body runs. A test seam (the resume /
# re-execution proof) that doubles as the §14 tracing node-instrumentation point.
StageProbe = Callable[[GateKind], None]

# Node update mappings are heterogeneous (e.g. {"gateCursor": GateKind}); langgraph
# applies them to the typed channels. ``Any`` here is the framework's update contract.
NodeUpdate = dict[str, Any]

# The compiled graph type for this builder: StateGraph[PipelineState, None, In, Out].
PipelineGraph = CompiledStateGraph[PipelineState, None, PipelineState, PipelineState]


def _resume_target_gate(resume: object) -> GateKind | None:
    """If a resume payload explicitly names a target gate, return it; else ``None``.

    An unrecognized gate value is a malformed/out-of-domain resume and is rejected as an
    ordering violation (Inv5 fail-closed) — never a bare ValueError that escapes the node.
    """
    if isinstance(resume, dict):
        raw = resume.get("gate")
        if raw is not None:
            try:
                return GateKind(raw)
            except ValueError as exc:
                raise GateOrderError(f"resume named an unknown gate: {raw!r}") from exc
    return None


def _make_stage_node(
    gate: GateKind, on_stage: StageProbe | None
) -> Callable[[PipelineState], NodeUpdate]:
    def stage_node(state: PipelineState) -> NodeUpdate:
        if on_stage is not None:
            on_stage(gate)
        # No-op placeholder body — real generation is 2.2; State advances at the gate.
        return {}

    return stage_node


def _make_gate_node(gate: GateKind) -> Callable[[PipelineState], NodeUpdate]:
    def gate_node(state: PipelineState) -> NodeUpdate:
        decision = interrupt({"gate": gate.value, "runId": state.runId})
        # A resume may not target a gate other than the one the run is paused at.
        target = _resume_target_gate(decision)
        if target is not None and target != gate:
            raise GateOrderError(
                f"resume targeted gate {target.value} while paused at {gate.value}"
            )
        # [Inv5] reject an out-of-order approval; advance the authoritative cursor.
        assert_gate_order(state.gateCursor, gate)
        return {"gateCursor": gate}

    return gate_node


def build_graph(
    checkpointer: BaseCheckpointSaver[Any],
    *,
    on_stage: StageProbe | None = None,
) -> PipelineGraph:
    """Compile the 5-stage / 5-gate pipeline StateGraph bound to ``checkpointer``.

    on_stage: optional GateKind-keyed hook invoked as each stage body runs — a test
    seam (the resume / re-execution proof) that doubles as the §14 tracing hook.

    Returns the compiled graph. Invoke it with ``durability="sync"`` (see module note).
    """
    builder = StateGraph(PipelineState)
    prev: str = START
    for gate in GATE_ORDER:
        stage_name = gate.value
        gate_name = f"{gate.value}_gate"
        # NOTE: langgraph's add_node overloads can't infer NodeInputT from a Protocol-typed
        # node action under mypy --strict (1.x stubs) → localized call-overload ignores.
        builder.add_node(stage_name, _make_stage_node(gate, on_stage))  # type: ignore[call-overload]
        builder.add_node(gate_name, _make_gate_node(gate))  # type: ignore[call-overload]
        builder.add_edge(prev, stage_name)
        builder.add_edge(stage_name, gate_name)
        prev = gate_name
    builder.add_edge(prev, END)
    return builder.compile(checkpointer=checkpointer)
