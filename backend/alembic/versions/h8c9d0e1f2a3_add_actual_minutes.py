"""add actual_minutes to commitments (calibration loop)

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-06-26 01:25:00.000000

Feature #4 - records actual time spent so the planner can learn a personal
estimate-bias factor.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "h8c9d0e1f2a3"
down_revision: Union[str, Sequence[str], None] = "g7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "commitments",
        sa.Column("actual_minutes", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("commitments", "actual_minutes")
