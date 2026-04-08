"""add entity_tags table

Revision ID: 5fb932efb44c
Revises: a1b2c3d4e5f6
Create Date: 2026-04-07 21:45:38.803296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5fb932efb44c'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('entity_tags',
    sa.Column('id', sa.Text(), nullable=False),
    sa.Column('entity_type', sa.Text(), nullable=False),
    sa.Column('entity_id', sa.Text(), nullable=False),
    sa.Column('tag', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('entity_type', 'entity_id', 'tag', name='uq_entity_tag')
    )
    op.create_index('ix_entity_tags_entity', 'entity_tags', ['entity_type', 'entity_id'], unique=False)
    op.create_index('ix_entity_tags_tag', 'entity_tags', ['tag'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_entity_tags_tag', table_name='entity_tags')
    op.drop_index('ix_entity_tags_entity', table_name='entity_tags')
    op.drop_table('entity_tags')
