"""add_auth_state_tables

Revision ID: b4e7a1c9d302
Revises: 6593ce0a7822
Create Date: 2026-04-05 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e7a1c9d302'
down_revision: Union[str, Sequence[str], None] = '6593ce0a7822'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create auth state tables for persistent sessions, challenges, and rate limits."""
    op.create_table(
        'auth_sessions',
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.Column('last_seen', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('token'),
    )
    op.create_table(
        'auth_challenges',
        sa.Column('challenge_hex', sa.Text(), nullable=False),
        sa.Column('challenge', sa.LargeBinary(), nullable=False),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.Column('display_name', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('challenge_hex'),
    )
    op.create_table(
        'auth_rate_limits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('ip', sa.Text(), nullable=False),
        sa.Column('attempted_at', sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_auth_rate_limits_ip'), 'auth_rate_limits', ['ip'], unique=False)


def downgrade() -> None:
    """Drop auth state tables."""
    op.drop_index(op.f('ix_auth_rate_limits_ip'), table_name='auth_rate_limits')
    op.drop_table('auth_rate_limits')
    op.drop_table('auth_challenges')
    op.drop_table('auth_sessions')
