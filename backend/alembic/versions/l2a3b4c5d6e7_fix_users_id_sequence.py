"""fix_users_id_sequence

Revision ID: l2a3b4c5d6e7
Revises: k1f2a3b4c5d6
Create Date: 2026-06-29 06:55:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'l2a3b4c5d6e7'
down_revision: Union[str, None] = 'k1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # The manual INSERT of id=1 left the sequence behind.
    # Reset it to the next available value.
    op.execute("SELECT setval(pg_get_serial_sequence('users', 'id'), COALESCE(MAX(id), 1)) FROM users;")


def downgrade() -> None:
    pass  # no-op, sequence state is transient
