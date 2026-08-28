"""Two-phase cloud-node pins (task 2.2).

A cloud stage is two phases: a @task-wrapped idempotent submit whose ProviderJobRef is
checkpointed into State BEFORE any poll side-effect, then a poll/reconcile node that
drives the mock provider's async lifecycle to terminal and fetches on success (§5). On a
failed/expired poll the §17 ErrorEnvelope is surfaced into State unchanged (never
re-rolled). R9: no double-submit on replay. The provider is INJECTED (rule 2).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from aisims_contracts import ErrorCode, GateKind
from aisims_contracts.providers import ProviderJobRef
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from adapters.mock.failure import FailurePlan, FailureRule, MockOp, envelope_for
from adapters.mock.providers import MockImageGenProvider
from graph import PipelineState, build_graph
from graph.cloud_node import CloudStageSpec, PollWatchdogError

CONCEPT = GateKind.CONCEPT
CONCEPT_KEY = "concept"  # the per-stage step key for 2.2 (per-item keying arrives with iteration)


def _concept_spec(provider: Any) -> CloudStageSpec:
    """Inject `provider` as the concept cloud stage's submit/poll/fetch seam (rule 2)."""
    return CloudStageSpec(
        submit=lambda _state: provider.submit("mock-prompt", {}), provider=provider
    )


def _resume(graph: Any, cfg: RunnableConfig, **kw: Any) -> None:
    graph.invoke(Command(resume="approve"), cfg, durability="sync", **kw)


def _start(graph: Any, cfg: RunnableConfig) -> None:
    # Pauses at plan_gate (the first gate, before the concept cloud stage).
    graph.invoke(PipelineState(projectId="p", runId="r"), cfg, durability="sync")


class SpyProvider:
    """Wraps a real mock provider and counts calls — proves the INJECTED instance is used."""

    def __init__(self, inner: MockImageGenProvider) -> None:
        self.inner = inner
        self.submits = 0
        self.polls = 0
        self.fetches = 0

    def submit(self, prompt: str, params: dict[str, Any]) -> ProviderJobRef:
        self.submits += 1
        return self.inner.submit(prompt, params)

    def poll(self, ref: ProviderJobRef) -> Any:
        self.polls += 1
        return self.inner.poll(ref)

    def fetch(self, urls: list[str]) -> list[str]:
        self.fetches += 1
        return self.inner.fetch(urls)


def test_submit_persists_job_ref_before_poll(mem_saver: InMemorySaver, tmp_path: Path) -> None:
    """Asserts submit runs once and the ProviderJobRef is in State before any poll. spec(§5)"""
    spy = SpyProvider(MockImageGenProvider(seed=1, scratch_dir=tmp_path))
    g = build_graph(mem_saver, providers={CONCEPT: _concept_spec(spy)})
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-submit"}}
    _start(g, cfg)
    # Resume the plan gate but pause right AFTER the concept submit node (before its poll).
    _resume(g, cfg, interrupt_after=["concept"])
    values = g.get_state(cfg).values
    assert spy.submits == 1
    assert spy.polls == 0  # the poll node has NOT run yet
    assert isinstance(values["providerJobRefs"][CONCEPT_KEY], ProviderJobRef)
    assert CONCEPT_KEY not in values["artifactRefs"]


def test_poll_drives_to_succeeded_and_fetches(mem_saver: InMemorySaver, tmp_path: Path) -> None:
    """Asserts the poll node cycles to succeeded then fetches scratch paths into State. spec(§5)"""
    provider = MockImageGenProvider(seed=1, scratch_dir=tmp_path, succeed_after_polls=3)
    g = build_graph(mem_saver, providers={CONCEPT: _concept_spec(provider)})
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-poll"}}
    _start(g, cfg)
    _resume(g, cfg)  # runs concept submit + poll, pauses at concept_gate
    values = g.get_state(cfg).values
    paths = values["artifactRefs"][CONCEPT_KEY]
    assert paths and all(Path(p).exists() for p in paths)
    assert CONCEPT_KEY not in values["pollErrors"]


def test_failed_poll_surfaces_envelope_unrerolled(mem_saver: InMemorySaver, tmp_path: Path) -> None:
    """Asserts an injected poll failure surfaces the SAME §17 envelope unchanged. spec(§17)"""
    plan = FailurePlan(rules=[FailureRule(operation=MockOp.POLL, code=ErrorCode.PROVIDER_TIMEOUT)])
    provider = MockImageGenProvider(seed=1, scratch_dir=tmp_path, failure_plan=plan)
    g = build_graph(mem_saver, providers={CONCEPT: _concept_spec(provider)})
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-fail"}}
    _start(g, cfg)
    _resume(g, cfg)
    values = g.get_state(cfg).values
    assert values["pollErrors"][CONCEPT_KEY] == envelope_for(ErrorCode.PROVIDER_TIMEOUT)
    assert CONCEPT_KEY not in values["artifactRefs"]


def test_no_double_submit_on_resume(tmp_path: Path, close_savers: list[object]) -> None:
    """[R9 PIN] Asserts a run resumed after submit never re-submits and reuses the ref. spec(§5)"""
    from graph.checkpointer import make_checkpointer

    db = str(tmp_path / "r9.sqlite")
    spy = SpyProvider(MockImageGenProvider(seed=1, scratch_dir=tmp_path))
    spec = _concept_spec(spy)  # the SAME spy persists across the simulated restart
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-r9"}}

    cp1 = make_checkpointer(sqlite_path=db)
    close_savers.append(cp1)
    g1 = build_graph(cp1, providers={CONCEPT: spec})
    _start(g1, cfg)
    _resume(g1, cfg, interrupt_after=["concept"])  # pause after submit (ref persisted)
    ref_after_submit = g1.get_state(cfg).values["providerJobRefs"][CONCEPT_KEY]
    assert spy.submits == 1
    assert isinstance(cp1, SqliteSaver)  # narrow to close the typed connection (restart sim)
    cp1.conn.close()

    # Rebuild graph + saver against the same file/thread; the SAME spy instance persists.
    cp2 = make_checkpointer(sqlite_path=db)
    close_savers.append(cp2)
    g2 = build_graph(cp2, providers={CONCEPT: spec})
    _resume(g2, cfg)  # runs the poll node — must NOT re-submit
    values = g2.get_state(cfg).values
    assert spy.submits == 1  # R9: submit called exactly once across the restart
    assert values["providerJobRefs"][CONCEPT_KEY] == ref_after_submit  # same ref reused


def test_cloud_node_uses_injected_provider(mem_saver: InMemorySaver, tmp_path: Path) -> None:
    """Asserts the cloud node calls the INJECTED provider instance. spec(rule-2)"""
    spy = SpyProvider(MockImageGenProvider(seed=1, scratch_dir=tmp_path))
    g = build_graph(mem_saver, providers={CONCEPT: _concept_spec(spy)})
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-spy"}}
    _start(g, cfg)
    _resume(g, cfg)
    assert spy.submits == 1
    assert spy.polls >= 1
    assert spy.fetches == 1  # succeeded → fetched once


def test_durability_sync_checkpoints_ref_synchronously(
    mem_saver: InMemorySaver, tmp_path: Path
) -> None:
    """Asserts durability='sync' persists the ProviderJobRef in the checkpoint. spec(§5)"""
    provider = MockImageGenProvider(seed=1, scratch_dir=tmp_path)
    g = build_graph(mem_saver, providers={CONCEPT: _concept_spec(provider)})
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-dur"}}
    _start(g, cfg)
    _resume(g, cfg, interrupt_after=["concept"])
    # Read the ref back from the persisted checkpoint (the saver), not the in-flight return.
    persisted = g.get_state(cfg).values["providerJobRefs"]
    assert CONCEPT_KEY in persisted
    assert isinstance(persisted[CONCEPT_KEY], ProviderJobRef)


def test_poll_loop_bounded(mem_saver: InMemorySaver, tmp_path: Path) -> None:
    """Asserts a never-terminal poll trips the max_polls watchdog with a named error. spec(§17)"""
    # succeed_after_polls (999) far exceeds max_polls (5) → never reaches a terminal status.
    spy = SpyProvider(MockImageGenProvider(seed=1, scratch_dir=tmp_path, succeed_after_polls=999))
    spec = CloudStageSpec(submit=lambda _s: spy.submit("p", {}), provider=spy, max_polls=5)
    g = build_graph(mem_saver, providers={CONCEPT: spec})
    cfg: RunnableConfig = {"configurable": {"thread_id": "t-bound"}}
    _start(g, cfg)
    with pytest.raises(PollWatchdogError):
        _resume(g, cfg)  # the poll loop exhausts its budget → watchdog raises (pre-2.5 stopgap)
    assert spy.polls == 5  # polled exactly max_polls times, then the watchdog tripped


def test_build_wires_cloud_stages_only_when_injected(
    mem_saver: InMemorySaver, tmp_path: Path
) -> None:
    """Asserts an injected stage gains a `<stage>_poll` node; uninjected stays no-op. spec(§5)"""
    spec = _concept_spec(MockImageGenProvider(scratch_dir=tmp_path))
    concept_only = build_graph(mem_saver, providers={CONCEPT: spec})
    nodes = set(concept_only.get_graph().nodes)
    assert "concept_poll" in nodes  # concept is a two-phase cloud stage
    assert "mesh_poll" not in nodes  # mesh was not injected → stays a no-op stage
    # No providers at all → the 2.1 topology (no _poll nodes).
    plain = build_graph(mem_saver)
    plain_nodes = set(plain.get_graph().nodes)
    assert not any(n.endswith("_poll") for n in plain_nodes)
