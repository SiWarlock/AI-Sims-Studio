"""Alembic environment for the §13 store.

Online-only: the runner shares a live (async-driven) connection via
``config.attributes['connection']``; we configure the migration context against it and run.
Offline (``--sql``) mode is unsupported for the skeleton.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy.engine import Connection

from store import models  # noqa: F401  (registers every table on Base.metadata for --autogenerate)
from store.db import Base

target_metadata = Base.metadata


def _run(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = context.config.attributes.get("connection", None)
    if connectable is None:
        raise RuntimeError(
            "store migrations require a live connection in config.attributes['connection']"
        )
    _run(connectable)


if context.is_offline_mode():
    raise RuntimeError("offline (--sql) migrations are unsupported for the store skeleton")

run_migrations_online()
