"""§13 store — ORM table models (hybrid persistence).

Each top-level entity is stored as a HYBRID row: a few key columns (id PK, status,
projectId where applicable, schema_version) are relational/indexed for cheap queries, and
the full frozen pydantic entity (0.4a) rides in a ``JSONB`` document column. This keeps
schema evolution cheap under ``schemaVersion`` (no per-field column churn) while preserving
queryability on the hot keys. Skeleton scope: project / pipeline_run / step + schema_meta;
the other entities land as Phase 2 needs them.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, json_doc


class ProjectRow(Base):
    __tablename__ = "project"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    status: Mapped[str] = mapped_column(String, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    entity: Mapped[dict[str, Any]] = mapped_column(json_doc(), nullable=False)


class PipelineRunRow(Base):
    __tablename__ = "pipeline_run"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(String, index=True)
    status: Mapped[str] = mapped_column(String, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    entity: Mapped[dict[str, Any]] = mapped_column(json_doc(), nullable=False)


class StepRow(Base):
    __tablename__ = "step"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    state: Mapped[str] = mapped_column(String, index=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    entity: Mapped[dict[str, Any]] = mapped_column(json_doc(), nullable=False)


class SchemaMetaRow(Base):
    """Singleton (id=1) version-stamp row — the data store's compat source-of-truth (§13 R-i)."""

    __tablename__ = "schema_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False)
    registry_version: Mapped[int] = mapped_column(Integer, nullable=False)
    app_version: Mapped[str] = mapped_column(String, nullable=False)
    data_dir_version: Mapped[int] = mapped_column(Integer, nullable=False)
