"""add commitment worst-case effort (p80)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-06-26 00:30:00.000000

Confidence-scored estimates (feature #3). est_effort_minutes is the expected
(p50) effort; effort_p80_minutes is the worst-case the planner buffers against.
Nullable so existing rows keep working - the planner falls back to 1.5x p50.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "commitments",
        sa.Column("effort_p80_minutes", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("commitments", "effort_p80_minutes")
