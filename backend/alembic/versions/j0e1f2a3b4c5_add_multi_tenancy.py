"""add_multi_tenancy

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2026-06-29 06:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j0e1f2a3b4c5'
down_revision: Union[str, None] = 'i9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # We create the users table first.
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('display_name', sa.String(), nullable=False),
        sa.Column('is_demo', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create the demo user with ID 1 so existing data can be migrated to it
    op.execute(
        "INSERT INTO users (id, email, hashed_password, display_name, is_demo) VALUES (1, 'demo@example.com', 'dummy_hash', 'Demo User', true);"
    )

    # For each table, add user_id column with default value 1
    tables = [
        'commitments',
        'busy_blocks',
        'decision_ledger',
        'documents',
        'renegotiation_messages',
        'stakeholders'
    ]

    for table in tables:
        op.add_column(table, sa.Column('user_id', sa.Integer(), server_default='1', nullable=False))
        op.create_foreign_key(f'fk_{table}_user_id', table, 'users', ['user_id'], ['id'], ondelete='CASCADE')
        op.create_index(op.f(f'ix_{table}_user_id'), table, ['user_id'], unique=False)
        
        # Remove server_default so new inserts require user_id
        op.alter_column(table, 'user_id', server_default=None)

    # Modify unique index on stakeholders
    op.drop_index('ix_stakeholders_name', table_name='stakeholders')
    op.create_index('ix_stakeholders_user_name', 'stakeholders', ['user_id', 'name'], unique=True)


def downgrade() -> None:
    # Revert stakeholders index
    op.drop_index('ix_stakeholders_user_name', table_name='stakeholders')
    op.create_index('ix_stakeholders_name', 'stakeholders', ['name'], unique=True)

    tables = [
        'stakeholders',
        'renegotiation_messages',
        'documents',
        'decision_ledger',
        'busy_blocks',
        'commitments',
    ]

    for table in tables:
        op.drop_index(op.f(f'ix_{table}_user_id'), table_name=table)
        op.drop_constraint(f'fk_{table}_user_id', table, type_='foreignkey')
        op.drop_column(table, 'user_id')

    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
