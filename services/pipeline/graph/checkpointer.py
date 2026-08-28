"""``make_checkpointer`` — the LangGraph checkpointer factory (task 2.1, ADR-002).

Postgres (``langgraph-checkpoint-postgres``) is the primary saver (same DB as §13);
when it is unavailable the factory falls back to the separate-module SQLite saver
(``langgraph-checkpoint-sqlite``) and logs the fallback. SQLite is the deterministic
unit path; the Postgres branch is exercised only when ``AISIMS_TEST_DATABASE_URL`` is
set (mirrors the 0.7 store test strategy).

Lifecycle: the returned saver owns a live DB connection; the CALLER owns its lifetime
(the 2.3 scheduler wires open/close). The checkpoint is authoritative for graph-
execution position ONLY — the store repository owns entity rows (§5 ownership partition).
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any
from urllib.parse import urlsplit

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.sqlite import SqliteSaver

logger = logging.getLogger(__name__)


def _safe_dsn(database_url: str) -> str:
    """A credential-free DSN label (scheme://host:port/path) for logging [SAFETY rule-5].

    A Postgres DSN can embed ``user:password@`` — never log the raw URL or the raw
    psycopg exception (its message can echo the DSN). This strips userinfo entirely.
    """
    try:
        parts = urlsplit(database_url)
        host = parts.hostname or "?"
        port = f":{parts.port}" if parts.port else ""
        return f"{parts.scheme}://{host}{port}{parts.path}"
    except ValueError:
        return "<unparseable-dsn>"


def make_checkpointer(
    database_url: str | None = None,
    *,
    sqlite_path: str = ":memory:",
    pg_connect_timeout: int = 5,
) -> BaseCheckpointSaver[Any]:
    """Return a checkpointer: Postgres when reachable, else the SQLite-saver fallback.

    database_url: the Postgres DSN (primary). When ``None`` or unreachable, fall back
        to a SQLite saver at ``sqlite_path`` and log the fallback (ADR-002).
    sqlite_path: the SQLite file path (``":memory:"`` by default for unit use).
    pg_connect_timeout: seconds before a Postgres connection attempt fast-fails.
    """
    if database_url:
        try:
            saver = _make_postgres_saver(database_url, pg_connect_timeout)
        except Exception as exc:  # any connect/availability failure ⇒ fall back to SQLite
            # [SAFETY rule-5] log the exception TYPE + a credential-free DSN label only —
            # never the raw exc (its message can echo the DSN password).
            logger.warning(
                "checkpointer: Postgres unavailable at %s (%s); "
                "falling back to SQLite saver [ADR-002]",
                _safe_dsn(database_url),
                type(exc).__name__,
            )
        else:
            logger.info("checkpointer: using Postgres saver [ADR-002 primary]")
            return saver
    else:
        logger.info("checkpointer: no database_url; using SQLite saver fallback [ADR-002]")
    return _make_sqlite_saver(sqlite_path)


def _make_sqlite_saver(sqlite_path: str) -> SqliteSaver:
    # check_same_thread=False: the saver may be touched from langgraph worker threads.
    conn = sqlite3.connect(sqlite_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver


def _make_postgres_saver(database_url: str, connect_timeout: int) -> BaseCheckpointSaver[Any]:
    # Imported lazily so the deterministic SQLite path never requires psycopg/PG at import.
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg import Connection
    from psycopg.rows import dict_row

    # PostgresSaver requires a dict-row connection (it reads rows by column name).
    conn = Connection.connect(
        database_url, autocommit=True, row_factory=dict_row, connect_timeout=connect_timeout
    )
    saver = PostgresSaver(conn)
    saver.setup()
    return saver
