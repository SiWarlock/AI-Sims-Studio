"""§13 store — the repository layer (the sidecar is the SOLE writer, rule 3).

A typed generic ``Repository[TEntity, TRow]`` (get / put / list_ids) + one concrete
``ProjectRepository`` for the skeleton; the rest land as their entities are needed (Phase 2).
This layer — never a worker — is the only writer of Postgres (forbidden-pattern 4). Workers
write only sidecar-provided scratch dirs and return paths; the engine repo commits the row.
"""

from __future__ import annotations

from aisims_contracts.domain import Project
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .db import Base
from .models import ProjectRow


class Repository[TEntity: BaseModel, TRow: Base]:
    """Base async repo: upsert (``put``), fetch (``get``) a frozen domain entity by id."""

    row_type: type[TRow]

    def __init__(self, sessionmaker: async_sessionmaker[AsyncSession]) -> None:
        self._sessionmaker = sessionmaker

    def _to_row(self, entity: TEntity) -> TRow:  # pragma: no cover - overridden
        raise NotImplementedError

    def _to_entity(self, row: TRow) -> TEntity:  # pragma: no cover - overridden
        raise NotImplementedError

    async def put(self, entity: TEntity) -> None:
        async with self._sessionmaker() as session:
            # merge = upsert by PK; the returned managed instance is intentionally discarded
            # (the skeleton has no DB-generated columns to read back — revisit in Phase 2).
            await session.merge(self._to_row(entity))
            await session.commit()

    async def get(self, entity_id: str) -> TEntity | None:
        async with self._sessionmaker() as session:
            row = await session.get(self.row_type, entity_id)
            return None if row is None else self._to_entity(row)


class ProjectRepository(Repository[Project, ProjectRow]):
    row_type = ProjectRow

    def _to_row(self, entity: Project) -> ProjectRow:
        return ProjectRow(
            id=entity.id,
            status=str(entity.status),
            schema_version=entity.schemaVersion,
            entity=entity.model_dump(mode="json"),
        )

    def _to_entity(self, row: ProjectRow) -> Project:
        return Project.model_validate(row.entity)

    async def list_ids(self) -> list[str]:
        async with self._sessionmaker() as session:
            result = await session.execute(select(ProjectRow.id))
            return list(result.scalars().all())
