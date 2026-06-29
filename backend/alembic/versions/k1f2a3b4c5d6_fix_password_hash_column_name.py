"""fix_password_hash_column_name

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-06-29 06:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'k1f2a3b4c5d6'
down_revision: Union[str, None] = 'j0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Fix column name: migration created 'hashed_password', model expects 'password_hash'
    op.alter_column('users', 'hashed_password', new_column_name='password_hash')

    # Fix display_name: model says nullable=True, migration said nullable=False
    op.alter_column('users', 'display_name', nullable=True)

    # Fix demo email: service expects 'demo@clutch.app', migration seeded 'demo@example.com'
    op.execute(
        "UPDATE users SET email = 'demo@clutch.app', password_hash = 'no-password' WHERE id = 1;"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE users SET email = 'demo@example.com', hashed_password = 'dummy_hash' WHERE id = 1;"
    )
    op.alter_column('users', 'display_name', nullable=False)
    op.alter_column('users', 'password_hash', new_column_name='hashed_password')
