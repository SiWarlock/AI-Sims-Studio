"""Fixtures for the graph (StateGraph + checkpointer) tests.

The in-memory saver fixture keeps the topology/gate tests (C2) independent of the
``make_checkpointer`` factory (C3); the checkpointer/resume tests build their own
file-backed savers and register them with ``close_savers`` for disposal (no leaked
sqlite handles), while ``tmp_path`` cleans the temp files.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from langgraph.checkpoint.memory import InMemorySaver


@pytest.fixture
def mem_saver() -> InMemorySaver:
    """A process-local checkpointer for topology + gate-pause tests."""
    return InMemorySaver()


@pytest.fixture
def close_savers() -> Iterator[list[object]]:
    """Register savers for teardown disposal — closes their DB connection if still open."""
    registered: list[object] = []
    yield registered
    for saver in registered:
        conn = getattr(saver, "conn", None)
        close = getattr(conn, "close", None)
        if callable(close):
            try:
                close()
            except Exception:  # teardown best-effort — a double-close must not fail the test
                pass
