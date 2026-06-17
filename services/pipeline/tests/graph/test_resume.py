"""Resume-across-restart pin (task 2.1, test 7) — the core resumability contract.

A run interrupted at a gate and checkpointed to a SQLite file resumes from the last
checkpoint when the graph + saver are rebuilt fresh against the same store + thread_id
(simulating process exit). Completed nodes are NOT re-executed (§5: survive process exit).
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from aisims_contracts import GateKind
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from graph import PipelineState, build_graph
from graph.checkpointer import make_checkpointer


def test_resume_across_simulated_restart(tmp_path: Path, close_savers: list[object]) -> None:
    """Asserts a checkpointed run resumes after a rebuild and never re-runs done nodes. spec(§5)"""
    db = str(tmp_path / "ckpt.sqlite")
    cfg: RunnableConfig = {"configurable": {"thread_id": "run-x"}}
    counter: Counter[GateKind] = Counter()

    def probe(gate: GateKind) -> None:
        counter.update([gate])

    # Session 1 — run to the first gate, then drop everything (process "exits").
    cp1 = make_checkpointer(sqlite_path=db)
    close_savers.append(cp1)
    g1 = build_graph(cp1, on_stage=probe)
    out1 = g1.invoke(PipelineState(projectId="p", runId="r"), cfg, durability="sync")
    assert "__interrupt__" in out1
    assert g1.get_state(cfg).next == ("plan_gate",)
    assert counter[GateKind.PLAN] == 1
    assert isinstance(cp1, SqliteSaver)  # narrow to access the typed sqlite connection
    cp1.conn.close()  # close the handle — a real process exit releases the file lock
    del g1

    # Session 2 — fresh saver + builder bound to the SAME file + thread_id.
    cp2 = make_checkpointer(sqlite_path=db)
    close_savers.append(cp2)
    g2 = build_graph(cp2, on_stage=probe)
    out = g2.invoke(Command(resume="approve"), cfg, durability="sync")
    while "__interrupt__" in out:
        out = g2.invoke(Command(resume="approve"), cfg, durability="sync")

    assert out["gateCursor"] == GateKind.EXPORT
    # The plan stage body ran exactly once — it was NOT re-executed after the restart.
    assert counter[GateKind.PLAN] == 1
