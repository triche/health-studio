"""add search_index FTS5 virtual table

Revision ID: a1b2c3d4e5f6
Revises: 7e8d28a29697
Create Date: 2026-04-06 20:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
from sqlalchemy import text

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

    # Populate index with existing data
    conn = op.get_bind()

    for row in conn.execute(text("SELECT id, title, content, entry_date FROM journal_entries")):
        conn.execute(
            text(
                "INSERT INTO search_index(entity_type, entity_id, title, body, extra) "
                "VALUES (:et, :eid, :t, :b, :x)"
            ),
            {"et": "journal", "eid": row.id, "t": row.title, "b": row.content, "x": str(row.entry_date)},
        )

    for row in conn.execute(text("SELECT id, title, description, plan, status, target_type, deadline FROM goals")):
        body = "\n".join(filter(None, [row.description, row.plan]))
        extra_parts = [row.status or ""]
        if row.target_type:
            extra_parts.append(row.target_type)
        if row.deadline:
            extra_parts.append(str(row.deadline))
        conn.execute(
            text(
                "INSERT INTO search_index(entity_type, entity_id, title, body, extra) "
                "VALUES (:et, :eid, :t, :b, :x)"
            ),
            {"et": "goal", "eid": row.id, "t": row.title, "b": body, "x": " ".join(extra_parts)},
        )

    for row in conn.execute(text("SELECT id, name, unit FROM metric_types")):
        conn.execute(
            text(
                "INSERT INTO search_index(entity_type, entity_id, title, body, extra) "
                "VALUES (:et, :eid, :t, :b, :x)"
            ),
            {"et": "metric_type", "eid": row.id, "t": row.name, "b": "", "x": row.unit or ""},
        )

    for row in conn.execute(text("SELECT id, name, category, result_unit FROM exercise_types")):
        extra = " ".join(filter(None, [row.category, row.result_unit]))
        conn.execute(
            text(
                "INSERT INTO search_index(entity_type, entity_id, title, body, extra) "
                "VALUES (:et, :eid, :t, :b, :x)"
            ),
            {"et": "exercise_type", "eid": row.id, "t": row.name, "b": "", "x": extra},
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS search_index;")
