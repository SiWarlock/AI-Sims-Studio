"""§13 store — SQLAlchemy 2.0 declarative base + portable JSON-document column.

The store targets app-managed Postgres (JSONB) in production; the deterministic unit-test
layer runs on SQLite. ``json_doc()`` renders ``JSONB`` on PostgreSQL and ``JSON`` on SQLite
via ``with_variant`` so the SAME ORM models exercise both with no per-dialect branching.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import TypeEngine


class Base(DeclarativeBase):
    """Declarative base for every store table (the canonical relational schema)."""


def json_doc() -> TypeEngine[Any]:
    """A JSON-document column: ``JSONB`` on PostgreSQL, ``JSON`` on SQLite."""
    return JSONB().with_variant(JSON(), "sqlite")
