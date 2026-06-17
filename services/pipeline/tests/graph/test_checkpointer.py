"""Checkpointer factory pins (task 2.1, tests 5-6).

``make_checkpointer`` selects Postgres as primary and falls back to a separate-module
SQLite saver when PG is unavailable, logging the fallback (§5 / ADR-002). SQLite is the
deterministic unit path; the PG branch is env-gated behind AISIMS_TEST_DATABASE_URL.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from aisims_contracts import GateKind
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.types import Command

from graph import build_graph
from graph.checkpointer import make_checkpointer

PG_URL = os.getenv("AISIMS_TEST_DATABASE_URL")


def _approve_all(compiled: object, thread: str) -> dict[str, object]:
    cfg = {"configurable": {"thread_id": thread}}
    out = compiled.invoke({"projectId": "p", "runId": "r"}, cfg, durability="sync")  # type: ignore[attr-defined]
    while "__interrupt__" in out:
        out = compiled.invoke(Command(resume="approve"), cfg, durability="sync")  # type: ignore[attr-defined]
    return out  # type: ignore[no-any-return]


def test_make_checkpointer_prefers_pg_falls_back_to_sqlite(
    caplog: pytest.LogCaptureFixture, close_savers: list[object]
) -> None:
    """Asserts no/invalid PG URL returns the SQLite saver and logs the fallback. spec(§5)"""
    with caplog.at_level(logging.INFO):
        cp = make_checkpointer(database_url=None)
    close_savers.append(cp)
    assert isinstance(cp, SqliteSaver)
    assert any(
        "sqlite" in r.message.lower() or "fallback" in r.message.lower() for r in caplog.records
    )

    # An invalid/unreachable PG URL fast-fails (connection refused) → SQLite fallback + log.
    caplog.clear()
    bad_url = "postgresql://u@127.0.0.1:1/none"
    with caplog.at_level(logging.WARNING):
        cp2 = make_checkpointer(database_url=bad_url, pg_connect_timeout=1)
    close_savers.append(cp2)
    assert isinstance(cp2, SqliteSaver)
    assert any(
        "fallback" in r.message.lower() or "unavailable" in r.message.lower()
        for r in caplog.records
    )


def test_make_checkpointer_fallback_log_redacts_dsn(
    caplog: pytest.LogCaptureFixture, close_savers: list[object]
) -> None:
    """Asserts the PG DSN credential never reaches the fallback log [SAFETY rule-5]. spec(§5)"""
    sentinel = "do-not-log-this-value"  # stands in for a DSN password
    dsn = f"postgresql://dbuser:{sentinel}@127.0.0.1:1/db"  # gitleaks:allow
    with caplog.at_level(logging.WARNING):
        cp = make_checkpointer(database_url=dsn, pg_connect_timeout=1)
    close_savers.append(cp)
    assert isinstance(cp, SqliteSaver)  # fell back

    logged = "\n".join(r.getMessage() for r in caplog.records)
    assert sentinel not in logged  # the password must be absent
    assert "dbuser:" not in logged  # userinfo (user:password) must be absent
    assert "127.0.0.1" in logged  # the credential-free host label IS logged (useful)


@pytest.mark.skipif(not PG_URL, reason="AISIMS_TEST_DATABASE_URL not set")
def test_make_checkpointer_uses_pg_when_available(close_savers: list[object]) -> None:
    """Asserts a valid AISIMS_TEST_DATABASE_URL selects the Postgres saver. spec(§5)"""
    from langgraph.checkpoint.postgres import PostgresSaver

    cp = make_checkpointer(database_url=PG_URL)
    close_savers.append(cp)
    assert isinstance(cp, PostgresSaver)


def test_checkpointer_parity_resume(tmp_path: Path, close_savers: list[object]) -> None:
    """Asserts interrupt→resume yields equal final State on SQLite (and PG, env-gated). spec(§5)"""
    sqlite_cp = make_checkpointer(sqlite_path=str(tmp_path / "a.sqlite"))
    close_savers.append(sqlite_cp)
    sqlite_final = _approve_all(build_graph(sqlite_cp), "sqlite-parity")
    assert sqlite_final["gateCursor"] == GateKind.EXPORT

    if PG_URL:
        pg_cp = make_checkpointer(database_url=PG_URL)
        close_savers.append(pg_cp)
        pg_final = _approve_all(build_graph(pg_cp), "pg-parity")

        def _strip(d: dict[str, object]) -> dict[str, object]:
            return {k: v for k, v in d.items() if k != "__interrupt__"}

        assert _strip(pg_final) == _strip(sqlite_final)
