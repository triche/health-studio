"""add search_index FTS5 virtual table

Revision ID: a1b2c3d4e5f6
Revises: 7e8d28a29697
Create Date: 2026-04-06 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "7e8d28a29697"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
            entity_type,
            entity_id UNINDEXED,
            title,
            body,
            extra,
            tokenize='porter unicode61'
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS search_index;")
