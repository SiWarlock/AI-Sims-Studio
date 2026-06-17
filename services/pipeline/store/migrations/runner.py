"""Run Alembic migrations to head programmatically over an async engine (§13).

Alembic's command layer is synchronous, so we drive it through ``AsyncConnection.run_sync``
with the live connection shared into ``cfg.attributes`` (the async cookbook pattern). Used by
``open_store`` and by the tests; idempotent (a second call is a no-op at head).
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import AsyncEngine

# repo root for the pipeline area: <area>/store/migrations/runner.py -> <area>/alembic.ini
_ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


def _make_config() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    # Absolute script_location so migrations resolve regardless of the caller's cwd.
    cfg.set_main_option("script_location", str(_ALEMBIC_INI.parent / "migrations"))
    return cfg


def _upgrade_to_head(connection: Connection, cfg: Config) -> None:
    cfg.attributes["connection"] = connection
    command.upgrade(cfg, "head")


async def run_migrations(engine: AsyncEngine) -> None:
    """Upgrade the database behind ``engine`` to the latest Alembic revision (idempotent)."""
    cfg = _make_config()
    async with engine.begin() as connection:
        await connection.run_sync(_upgrade_to_head, cfg)
