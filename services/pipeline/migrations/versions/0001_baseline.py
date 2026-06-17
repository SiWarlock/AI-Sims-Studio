"""baseline store schema: project, pipeline_run, step, schema_meta (§13)

Revision ID: 0001_baseline
Revises:
Create Date: 2026-06-17

Skeleton baseline — establishes the hybrid-row pattern (key columns + a JSONB entity doc)
and the singleton schema_meta version-stamp table. The remaining entities land as Phase 2
needs them. pgvector columns are deferred to the Phase-2 embeddings work.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

from store.db import json_doc

revision = "0001_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "project",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("entity", json_doc(), nullable=False),
    )
    op.create_index("ix_project_status", "project", ["status"])

    op.create_table(
        "pipeline_run",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("project_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("entity", json_doc(), nullable=False),
    )
    op.create_index("ix_pipeline_run_project_id", "pipeline_run", ["project_id"])
    op.create_index("ix_pipeline_run_status", "pipeline_run", ["status"])

    op.create_table(
        "step",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("run_id", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("entity", json_doc(), nullable=False),
    )
    op.create_index("ix_step_run_id", "step", ["run_id"])
    op.create_index("ix_step_state", "step", ["state"])

    op.create_table(
        "schema_meta",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("schema_version", sa.Integer(), nullable=False),
        sa.Column("registry_version", sa.Integer(), nullable=False),
        sa.Column("app_version", sa.String(), nullable=False),
        sa.Column("data_dir_version", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("schema_meta")
    op.drop_index("ix_step_state", table_name="step")
    op.drop_index("ix_step_run_id", table_name="step")
    op.drop_table("step")
    op.drop_index("ix_pipeline_run_status", table_name="pipeline_run")
    op.drop_index("ix_pipeline_run_project_id", table_name="pipeline_run")
    op.drop_table("pipeline_run")
    op.drop_index("ix_project_status", table_name="project")
    op.drop_table("project")
