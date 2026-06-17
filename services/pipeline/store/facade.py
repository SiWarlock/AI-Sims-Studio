"""§13 store — the open/wire-up facade.

``open_store`` is the single entry point that wires the async engine + session factory,
runs migrations to head, persists/validates the version stamp (§13 R-i), and exposes the
repository layer (the sole writer, rule 3). Production callers: the supervisor / startup
(0.9) and the LangGraph nodes (Phase 2).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from .migrations.runner import run_migrations
from .repository import ProjectRepository
from .versioning import (
    CURRENT_STAMP,
    CompatVerdict,
    IncompatibleStoreError,
    check_compat,
    read_stamp,
    write_stamp,
)


@dataclass
class Store:
    """An opened store: engine + session factory + canonical artifact root + repositories."""

    engine: AsyncEngine
    sessionmaker: async_sessionmaker[AsyncSession]
    canonical_root: Path
    projects: ProjectRepository

    async def close(self) -> None:
        await self.engine.dispose()


async def open_store(
    database_url: str,
    *,
    canonical_root: Path,
    migrate: bool = True,
    enforce_compat: bool = True,
) -> Store:
    """Open the store: migrate → stamp-or-compat-check → expose repositories.

    On first open the current version stamp is persisted. On a later open a stored stamp is
    compat-checked; an incompatible stamp raises ``IncompatibleStoreError`` (never silently
    opened). The canonical artifact root is ensured to exist.

    ``migrate=False`` is a test-only escape (the caller pre-migrated). ``enforce_compat=False``
    is likewise test-only — production opens MUST enforce. The version stamp lives in the
    ``schema_meta`` table (created by the migration), so the compat check necessarily runs
    AFTER migrate; a pre-migration on-disk-stamp guard is deferred to the Phase-2 migrate runner.
    """
    engine = create_async_engine(database_url)
    try:
        if migrate:
            await run_migrations(engine)

        sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
        async with sessionmaker() as session:
            stored = await read_stamp(session)
            if stored is None:
                await write_stamp(session, CURRENT_STAMP)
                await session.commit()
            elif enforce_compat and check_compat(stored) is CompatVerdict.REFUSE:
                raise IncompatibleStoreError(stored, CURRENT_STAMP)

        canonical_root.mkdir(parents=True, exist_ok=True)
    except Exception:
        # never leak the engine's connection pool on a failed open (migration error,
        # commit error, or an incompatible-store refusal)
        await engine.dispose()
        raise

    return Store(
        engine=engine,
        sessionmaker=sessionmaker,
        canonical_root=canonical_root,
        projects=ProjectRepository(sessionmaker),
    )
