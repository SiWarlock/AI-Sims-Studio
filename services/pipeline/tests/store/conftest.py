"""Shared helpers for the §13 store-skeleton tests.

The deterministic unit layer runs against an on-disk SQLite file (``sqlite+aiosqlite``)
so the same SQLAlchemy 2.0 async models exercise the real migration + repo paths with
**no database server**; the JSONB columns degrade to SQLite ``JSON`` via ``with_variant``
(``store.db``). A PG integration layer (true ``JSONB``) is gated behind
``AISIMS_TEST_DATABASE_URL`` (``test_pg_integration``); skipped when unset so CI stays
green without Docker.

Tests are plain ``def`` functions that drive the async store inside ``asyncio.run`` via
``run_sync`` — no pytest-asyncio plugin dependency.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from pathlib import Path
from typing import Any


def run_sync[T](coro: Coroutine[Any, Any, T]) -> T:
    """Drive a coroutine to completion on a fresh event loop (one per test call)."""
    return asyncio.run(coro)


def sqlite_url(tmp_path: Path) -> str:
    """An on-disk SQLite URL — file-backed so the schema persists across connections."""
    return f"sqlite+aiosqlite:///{tmp_path / 'store.db'}"
