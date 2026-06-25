"""add commitment depends_on_id (dependency-aware critical path)

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-26 00:45:00.000000

Feature #1 - true CPM. A commitment may depend on another (its prerequisite).
Self-referential FK, nullable, ON DELETE SET NULL so removing a prerequisite
never orphans its dependents.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "commitments",
        sa.Column("depends_on_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_commitments_depends_on_id", "commitments", ["depends_on_id"]
    )
    op.create_foreign_key(
        "fk_commitments_depends_on_id",
        "commitments",
        "commitments",
        ["depends_on_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_commitments_depends_on_id", "commitments", type_="foreignkey"
    )
    op.drop_index("ix_commitments_depends_on_id", table_name="commitments")
    op.drop_column("commitments", "depends_on_id")
