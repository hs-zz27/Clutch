"""create stakeholders table

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-06-26 01:40:00.000000

Feature #8 - stakeholder relationship model used to tailor renegotiation tone.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "i9d0e1f2a3b4"
down_revision: Union[str, Sequence[str], None] = "h8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "stakeholders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("relationship", sa.String(length=64), nullable=True),
        sa.Column(
            "formality", sa.Integer(), nullable=False, server_default=sa.text("3")
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_stakeholders_name", "stakeholders", ["name"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_stakeholders_name", table_name="stakeholders")
    op.drop_table("stakeholders")
