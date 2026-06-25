"""create commitments table

Revision ID: f1a2b3c4d5e6
Revises: e386be5c970b
Create Date: 2026-06-25 22:40:00.000000

The previous autogenerate run produced an empty migration because env.py never
imported the models, so Base.metadata was empty. This migration creates the
commitments table for real, with a primary key and indexes on the columns the
planner filters/sorts by (deadline, status).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "e386be5c970b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

status_enum = sa.Enum(
    "not_started", "in_progress", "done", "dropped", "deferred", name="status"
)


def upgrade() -> None:
    op.create_table(
        "commitments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("est_effort_minutes", sa.Integer(), server_default="60", nullable=False),
        sa.Column("importance", sa.Integer(), server_default="3", nullable=False),
        sa.Column("stakeholder", sa.String(length=255), nullable=True),
        sa.Column("min_viable_definition", sa.Text(), nullable=True),
        sa.Column("status", status_enum, server_default="not_started", nullable=False),
        sa.Column("progress_pct", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_commitments_deadline", "commitments", ["deadline"])
    op.create_index("ix_commitments_status", "commitments", ["status"])


def downgrade() -> None:
    op.drop_index("ix_commitments_status", table_name="commitments")
    op.drop_index("ix_commitments_deadline", table_name="commitments")
    op.drop_table("commitments")
    status_enum.drop(op.get_bind(), checkfirst=True)
