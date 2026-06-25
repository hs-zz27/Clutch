"""create renegotiation_messages table

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-06-25 23:10:00.000000

Human-in-the-loop outbox of agent-drafted renegotiation messages.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

outbox_status = sa.Enum(
    "draft", "approved", "sent", "failed", name="outbox_status"
)


def upgrade() -> None:
    op.create_table(
        "renegotiation_messages",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("commitment_id", sa.Integer(), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=True),
        sa.Column("subject", sa.String(length=512), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column(
            "status",
            outbox_status,
            server_default="draft",
            nullable=False,
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["commitment_id"], ["commitments.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_renegotiation_messages_commitment_id",
        "renegotiation_messages",
        ["commitment_id"],
    )
    op.create_index(
        "ix_renegotiation_messages_status",
        "renegotiation_messages",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_renegotiation_messages_status", table_name="renegotiation_messages"
    )
    op.drop_index(
        "ix_renegotiation_messages_commitment_id",
        table_name="renegotiation_messages",
    )
    op.drop_table("renegotiation_messages")
    outbox_status.drop(op.get_bind(), checkfirst=True)
