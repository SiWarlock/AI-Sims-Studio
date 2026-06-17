"""RED — §13 Alembic baseline.

`alembic upgrade head` on an empty DB creates the skeleton tables (project, pipeline_run,
step) + the `schema_meta` version-stamp table, plus Alembic's own `alembic_version`.
Establishes the migration pattern, not all 16 entities (Q3).
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from .conftest import run_sync, sqlite_url

EXPECTED_TABLES = {"project", "pipeline_run", "step", "schema_meta"}


def test_alembic_baseline_builds_schema(tmp_path: Path) -> None:
    """spec(§13) — alembic upgrade head builds the skeleton schema + schema_meta."""
    from store.migrations.runner import run_migrations

    async def _run() -> set[str]:
        engine = create_async_engine(sqlite_url(tmp_path))
        try:
            await run_migrations(engine)
            async with engine.connect() as conn:
                names = await conn.run_sync(
                    lambda sync_conn: set(inspect(sync_conn).get_table_names())
                )
        finally:
            await engine.dispose()
        return names

    tables = run_sync(_run())
    assert EXPECTED_TABLES <= tables, f"missing baseline tables: {EXPECTED_TABLES - tables}"
    assert "alembic_version" in tables, "alembic stamp table absent — migration did not run"


def test_baseline_is_idempotent_to_head(tmp_path: Path) -> None:
    """spec(§13) — running migrations twice is a no-op (already at head)."""
    from store.migrations.runner import run_migrations

    async def _run() -> None:
        engine = create_async_engine(sqlite_url(tmp_path))
        try:
            await run_migrations(engine)
            await run_migrations(engine)  # second run: no error, stays at head

            def _rev(sync_conn: Connection) -> int:
                return len(inspect(sync_conn).get_table_names())

            async with engine.connect() as conn:
                count = await conn.run_sync(_rev)
        finally:
            await engine.dispose()
        assert count >= len(EXPECTED_TABLES)

    run_sync(_run())
