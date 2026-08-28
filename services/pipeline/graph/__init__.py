"""Pipeline graph package — the resumable LangGraph StateGraph spine (§5).

Exports the graph builder, the typed checkpoint State, the checkpointer factory, and
the Inv5 ordered-gate guard.
"""

from graph.build import build_graph
from graph.checkpointer import make_checkpointer
from graph.cloud_node import CloudStageSpec, PollWatchdogError, ProviderBundle
from graph.gates import GATE_ORDER, GateOrderError, assert_gate_order, next_gate
from graph.state import PipelineState

__all__ = [
    "GATE_ORDER",
    "CloudStageSpec",
    "GateOrderError",
    "PipelineState",
    "PollWatchdogError",
    "ProviderBundle",
    "assert_gate_order",
    "build_graph",
    "make_checkpointer",
    "next_gate",
]
