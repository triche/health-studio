"""Export / Import service — handles JSON full backup, CSV per entity, Markdown journals."""

from __future__ import annotations

import csv
import io
from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricEntry, MetricType
from app.models.result import ExerciseType, ResultEntry

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

EXPORT_VERSION = 1


# ---------------------------------------------------------------------------
# Serialisation helpers
# ---------------------------------------------------------------------------


def _ser(val: Any) -> Any:
    """Convert date/datetime to ISO string for JSON serialisation."""
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    return val


def _row_dict(obj: Any, columns: list[str]) -> dict[str, Any]:
    return {col: _ser(getattr(obj, col)) for col in columns}


# Column definitions per entity
_METRIC_TYPE_COLS = ["id", "name", "unit", "created_at"]
_METRIC_ENTRY_COLS = ["id", "metric_type_id", "value", "recorded_date", "notes", "created_at"]
_EXERCISE_TYPE_COLS = ["id", "name", "category", "result_unit", "created_at"]
_RESULT_ENTRY_COLS = [
    "id",
    "exercise_type_id",
    "value",
    "display_value",
    "recorded_date",
    "is_pr",
    "is_rx",
    "notes",
    "created_at",
]
_JOURNAL_ENTRY_COLS = ["id", "title", "content", "entry_date", "created_at", "updated_at"]
_GOAL_COLS = [
    "id",
    "title",
    "description",
    "plan",
    "target_type",
    "target_id",
    "target_value",
    "start_value",
    "current_value",
    "lower_is_better",
    "status",
    "deadline",
    "created_at",
    "updated_at",
]

_ENTITY_MAP: dict[str, tuple[type, list[str]]] = {
    "metric_types": (MetricType, _METRIC_TYPE_COLS),
    "metric_entries": (MetricEntry, _METRIC_ENTRY_COLS),
    "exercise_types": (ExerciseType, _EXERCISE_TYPE_COLS),
    "result_entries": (ResultEntry, _RESULT_ENTRY_COLS),
    "journal_entries": (JournalEntry, _JOURNAL_ENTRY_COLS),
    "goals": (Goal, _GOAL_COLS),
}

VALID_ENTITIES = frozenset(_ENTITY_MAP.keys())

# Entities allowed for CSV import (metrics & results)
CSV_IMPORTABLE = frozenset({"metric_entries", "result_entries"})

# Required CSV columns per importable entity
_CSV_REQUIRED: dict[str, set[str]] = {
    "metric_entries": {"metric_type_id", "value", "recorded_date"},
    "result_entries": {"exercise_type_id", "value", "recorded_date"},
}


# ---------------------------------------------------------------------------
# JSON Export
# ---------------------------------------------------------------------------


def export_json(db: Session) -> dict[str, Any]:
    """Export all data as a JSON-serialisable dict."""
    result: dict[str, Any] = {"version": EXPORT_VERSION}
    for entity_name, (model, cols) in _ENTITY_MAP.items():
        rows = db.query(model).all()
        result[entity_name] = [_row_dict(r, cols) for r in rows]
    return result


# ---------------------------------------------------------------------------
# CSV Export
# ---------------------------------------------------------------------------


def export_csv(db: Session, entity: str) -> str:
    """Export a single entity type as CSV string."""
    model, cols = _ENTITY_MAP[entity]
    rows = db.query(model).all()

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=cols)
    writer.writeheader()
    for row in rows:
        writer.writerow(_row_dict(row, cols))
    return output.getvalue()


# ---------------------------------------------------------------------------
# Markdown Export (journals)
# ---------------------------------------------------------------------------


def export_journals_markdown(db: Session) -> str:
    """Export all journal entries as a single Markdown document."""
    entries = (
        db.query(JournalEntry)
        .order_by(JournalEntry.entry_date.asc(), JournalEntry.created_at.asc())
        .all()
    )
    if not entries:
        return "# Health Studio — Journal Entries\n\n_No entries._\n"

    parts: list[str] = []
    for entry in entries:
        parts.append(f"# {entry.title}\n")
        parts.append(f"_Date: {entry.entry_date.isoformat()}_\n")
        parts.append(f"{entry.content}\n")
        parts.append("---\n")

    return "\n".join(parts)


# ---------------------------------------------------------------------------
# JSON Import
# ---------------------------------------------------------------------------


def _coerce_value(col: str, val: Any) -> Any:
    """Coerce string values to proper Python types for SQLAlchemy."""
    if val is None or val == "":
        return None
    # Date columns (no time component)
    if col in ("entry_date", "recorded_date", "deadline"):
        if isinstance(val, str):
            return date.fromisoformat(val)
        return val
    # Datetime columns
    if col in ("created_at", "updated_at"):
        if isinstance(val, str):
            return datetime.fromisoformat(val)
        return val
    # Float columns
    if col in ("value", "target_value", "start_value", "current_value"):
        return float(val)
    # Bool columns
    if col in ("is_pr", "is_rx", "lower_is_better"):
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)
    return val


def import_json(db: Session, data: dict[str, Any]) -> dict[str, int]:
    """Import a full JSON backup. Skips records whose IDs already exist."""
    imported: dict[str, int] = {}
    skipped = 0

    # Import order matters — types before entries, entries before goals
    ordered_entities = [
        "metric_types",
        "exercise_types",
        "metric_entries",
        "result_entries",
        "journal_entries",
        "goals",
    ]

    for entity_name in ordered_entities:
        rows = data.get(entity_name, [])
        model, cols = _ENTITY_MAP[entity_name]
        count = 0
        for row in rows:
            # Skip if record with this ID already exists
            if row.get("id") and db.get(model, row["id"]):
                skipped += 1
                continue
            kwargs = {col: _coerce_value(col, row.get(col)) for col in cols if col in row}
            obj = model(**kwargs)
            db.add(obj)
            count += 1
        imported[entity_name] = count

    db.commit()
    imported["skipped"] = skipped

    # Re-derive entity mentions from journal content (self-healing on import)
    from app.services.mentions import sync_mentions

    journals = db.query(JournalEntry).all()
    for journal in journals:
        sync_mentions(db, journal.id, journal.content)
    db.commit()

    # Rebuild full-text search index so all imported entities are searchable
    from app.services.search import rebuild_index

    rebuild_index(db)
    db.commit()

    return imported


# ---------------------------------------------------------------------------
# CSV Import
# ---------------------------------------------------------------------------


def import_csv(db: Session, entity: str, file_content: str) -> dict[str, int]:
    """Import CSV rows for a given entity. Returns count of imported rows."""
    reader = csv.DictReader(io.StringIO(file_content))

    required = _CSV_REQUIRED[entity]
    fieldnames = set(reader.fieldnames or [])
    if not required.issubset(fieldnames):
        missing = required - fieldnames
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    model, cols = _ENTITY_MAP[entity]
    count = 0
    for row in reader:
        filtered = {
            col: _coerce_value(col, row[col]) for col in cols if col in row and row[col] != ""
        }
        obj = model(**filtered)
        db.add(obj)
        count += 1

    db.commit()
    return {"imported": count}
