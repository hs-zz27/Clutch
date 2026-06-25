"""create busy_blocks table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-06-25 23:25:00.000000

Unavailable time spans (manual or imported from an .ics feed) that reduce the
computed focus capacity used by triage.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

busy_source = sa.Enum("manual", "ics", name="busy_source")


def upgrade() -> None:
    op.create_table(
        "busy_blocks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("label", sa.String(length=512), nullable=True),
        sa.Column(
            "source", busy_source, server_default="manual", nullable=False
        ),
        sa.Column("external_uid", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_busy_blocks_start", "busy_blocks", ["start"])
    op.create_index("ix_busy_blocks_source", "busy_blocks", ["source"])


def downgrade() -> None:
    op.drop_index("ix_busy_blocks_source", table_name="busy_blocks")
    op.drop_index("ix_busy_blocks_start", table_name="busy_blocks")
    op.drop_table("busy_blocks")
    busy_source.drop(op.get_bind(), checkfirst=True)
