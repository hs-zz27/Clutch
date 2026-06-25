"""create decision_ledger table

Revision ID: g7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-06-26 01:05:00.000000

Feature #9 - explainable decision ledger. Append-only record of every
state-changing action with reasoning and an optional JSON before-snapshot for
undo.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "g7b8c9d0e1f2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "decision_ledger",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.Integer(), nullable=True),
        sa.Column("summary", sa.String(length=512), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=True),
        sa.Column(
            "payload", sa.JSON(), nullable=False, server_default=sa.text("'{}'")
        ),
        sa.Column(
            "reversible", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "undone", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_decision_ledger_action", "decision_ledger", ["action"])
    op.create_index(
        "ix_decision_ledger_target_id", "decision_ledger", ["target_id"]
    )
    op.create_index("ix_decision_ledger_undone", "decision_ledger", ["undone"])
    op.create_index(
        "ix_decision_ledger_created_at", "decision_ledger", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_decision_ledger_created_at", table_name="decision_ledger")
    op.drop_index("ix_decision_ledger_undone", table_name="decision_ledger")
    op.drop_index("ix_decision_ledger_target_id", table_name="decision_ledger")
    op.drop_index("ix_decision_ledger_action", table_name="decision_ledger")
    op.drop_table("decision_ledger")
