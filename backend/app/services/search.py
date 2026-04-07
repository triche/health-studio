"""Full-text search service using SQLite FTS5.

All SQL in this module uses ``_FTS5_TABLE`` — a module-level constant, not user
input — so S608 (SQL-injection via string formatting) is a false positive.
"""
# ruff: noqa: S608

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import text

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricType
from app.models.result import ExerciseType

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


_FTS5_TABLE = "search_index"


def _has_fts5(db: Session) -> bool:
    """Check if the search_index FTS5 table exists."""
    row = db.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": _FTS5_TABLE},
    ).fetchone()
    return row is not None


def _get_rowid(db: Session, entity_type: str, entity_id: str) -> int | None:
    """Find the rowid of an existing entry in the FTS5 index."""
    row = db.execute(
        text(f"SELECT rowid FROM {_FTS5_TABLE} WHERE entity_type = :et AND entity_id = :eid"),
        {"et": entity_type, "eid": entity_id},
    ).fetchone()
    return row[0] if row else None


def index_entity(
    db: Session,
    entity_type: str,
    entity_id: str,
    title: str,
    body: str,
    extra: str = "",
) -> None:
    """Insert or replace a document in the FTS5 index."""
    if not _has_fts5(db):
        return

    # Delete existing entry first, then insert new one
    rowid = _get_rowid(db, entity_type, entity_id)
    if rowid is not None:
        db.execute(
            text(f"DELETE FROM {_FTS5_TABLE} WHERE rowid = :rid"),
            {"rid": rowid},
        )

    db.execute(
        text(
            f"INSERT INTO {_FTS5_TABLE}(entity_type, entity_id, title, body, extra) "
            f"VALUES (:et, :eid, :t, :b, :x)"
        ),
        {"et": entity_type, "eid": entity_id, "t": title, "b": body, "x": extra},
    )
    db.flush()


def remove_from_index(db: Session, entity_type: str, entity_id: str) -> None:
    """Remove a document from the FTS5 index."""
    if not _has_fts5(db):
        return

    rowid = _get_rowid(db, entity_type, entity_id)
    if rowid is not None:
        db.execute(
            text(f"DELETE FROM {_FTS5_TABLE} WHERE rowid = :rid"),
            {"rid": rowid},
        )
        db.flush()


def rebuild_index(db: Session) -> None:
    """Full rebuild — drop all content and re-index every entity."""
    if not _has_fts5(db):
        return

    # Clear entire FTS5 index
    db.execute(text(f"DELETE FROM {_FTS5_TABLE}"))
    db.flush()

    # Index all journals
    for j in db.query(JournalEntry).all():
        index_entity(db, "journal", j.id, j.title, j.content, str(j.entry_date))

    # Index all goals
    for g in db.query(Goal).all():
        body = "\n".join(filter(None, [g.description, g.plan]))
        extra_parts = [g.status or ""]
        if g.target_type:
            extra_parts.append(g.target_type)
        if g.deadline:
            extra_parts.append(str(g.deadline))
        index_entity(db, "goal", g.id, g.title, body, " ".join(extra_parts))

    # Index all metric types
    for mt in db.query(MetricType).all():
        index_entity(db, "metric_type", mt.id, mt.name, "", mt.unit or "")

    # Index all exercise types
    for et in db.query(ExerciseType).all():
        extra = " ".join(filter(None, [et.category, et.result_unit]))
        index_entity(db, "exercise_type", et.id, et.name, "", extra)

    db.flush()


def search(
    db: Session,
    query: str,
    entity_types: list[str] | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """Full-text search with BM25 ranking and optional type filtering.

    Returns: [{entity_type, entity_id, title, snippet, rank}]
    """
    if not query or not query.strip():
        return []

    if not _has_fts5(db):
        return []

    # Build the FTS5 query
    # Weight: entity_type=0, entity_id=0, title=10, body=1, extra=0.5
    if entity_types:
        placeholders = ", ".join(f":type_{i}" for i in range(len(entity_types)))
        sql = text(
            f"SELECT entity_type, entity_id, title, "
            f"snippet({_FTS5_TABLE}, 3, '<mark>', '</mark>', '...', 40) as snippet, "
            f"bm25({_FTS5_TABLE}, 0.0, 0.0, 10.0, 1.0, 0.5) as rank "
            f"FROM {_FTS5_TABLE} "
            f"WHERE {_FTS5_TABLE} MATCH :query "
            f"AND entity_type IN ({placeholders}) "
            f"ORDER BY rank "
            f"LIMIT :lim OFFSET :off"
        )
        params: dict = {"query": query, "lim": limit, "off": offset}
        for i, t in enumerate(entity_types):
            params[f"type_{i}"] = t
    else:
        sql = text(
            f"SELECT entity_type, entity_id, title, "
            f"snippet({_FTS5_TABLE}, 3, '<mark>', '</mark>', '...', 40) as snippet, "
            f"bm25({_FTS5_TABLE}, 0.0, 0.0, 10.0, 1.0, 0.5) as rank "
            f"FROM {_FTS5_TABLE} "
            f"WHERE {_FTS5_TABLE} MATCH :query "
            f"ORDER BY rank "
            f"LIMIT :lim OFFSET :off"
        )
        params = {"query": query, "lim": limit, "off": offset}

    rows = db.execute(sql, params).fetchall()
    return [
        {
            "entity_type": row[0],
            "entity_id": row[1],
            "title": row[2],
            "snippet": row[3],
            "rank": row[4],
        }
        for row in rows
    ]


def search_count(
    db: Session,
    query: str,
    entity_types: list[str] | None = None,
) -> int:
    """Count total matches (for pagination metadata)."""
    if not query or not query.strip():
        return 0

    if not _has_fts5(db):
        return 0

    if entity_types:
        placeholders = ", ".join(f":type_{i}" for i in range(len(entity_types)))
        sql = text(
            f"SELECT COUNT(*) FROM {_FTS5_TABLE} "
            f"WHERE {_FTS5_TABLE} MATCH :query "
            f"AND entity_type IN ({placeholders})"
        )
        params: dict = {"query": query}
        for i, t in enumerate(entity_types):
            params[f"type_{i}"] = t
    else:
        sql = text(f"SELECT COUNT(*) FROM {_FTS5_TABLE} WHERE {_FTS5_TABLE} MATCH :query")
        params = {"query": query}

    row = db.execute(sql, params).fetchone()
    return row[0] if row else 0
