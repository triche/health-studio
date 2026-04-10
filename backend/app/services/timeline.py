"""Unified timeline service — Phase 4 of the digital thread.

Builds a chronological feed that interleaves journal entries, metric entries,
result entries, and goals. Each entity is projected to a common TimelineItem
shape, sorted by date descending, with support for type/tag/date filtering
and pagination.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricEntry, MetricType
from app.models.result import ExerciseType, ResultEntry
from app.models.tag import EntityTag
from app.services.tags import get_tags

if TYPE_CHECKING:
    from datetime import date

    from sqlalchemy.orm import Session


def _truncate(text: str, max_len: int = 200) -> str:
    """Return the first *max_len* characters of *text*, adding '…' if truncated."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "…"


def _date_str(d: date) -> str:
    return d.isoformat()


# ---------------------------------------------------------------------------
# Per-type query helpers
# ---------------------------------------------------------------------------


def _query_journals(
    db: Session,
    *,
    tag: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list[dict]:
    query = db.query(JournalEntry)
    if date_from:
        query = query.filter(JournalEntry.entry_date >= date_from)
    if date_to:
        query = query.filter(JournalEntry.entry_date <= date_to)
    if tag:
        query = query.filter(
            JournalEntry.id.in_(
                db.query(EntityTag.entity_id).filter(
                    EntityTag.entity_type == "journal",
                    EntityTag.tag == tag.strip().lower(),
                )
            )
        )
    items = []
    for j in query.all():
        tags = get_tags(db, "journal", j.id)
        items.append(
            {
                "type": "journal",
                "id": j.id,
                "title": j.title,
                "summary": _truncate(j.content),
                "date": _date_str(j.entry_date),
                "tags": tags,
                "metadata": {},
            }
        )
    return items


def _query_metrics(
    db: Session,
    *,
    tag: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list[dict]:
    query = db.query(MetricEntry).join(MetricType, MetricEntry.metric_type_id == MetricType.id)
    if date_from:
        query = query.filter(MetricEntry.recorded_date >= date_from)
    if date_to:
        query = query.filter(MetricEntry.recorded_date <= date_to)
    if tag:
        query = query.filter(
            MetricEntry.metric_type_id.in_(
                db.query(EntityTag.entity_id).filter(
                    EntityTag.entity_type == "metric_type",
                    EntityTag.tag == tag.strip().lower(),
                )
            )
        )
    items = []
    for me in query.all():
        mt = db.get(MetricType, me.metric_type_id)
        tags = get_tags(db, "metric_type", me.metric_type_id) if mt else []
        unit = mt.unit if mt else ""
        display = f"{me.value} {unit}".strip()
        items.append(
            {
                "type": "metric",
                "id": me.id,
                "title": mt.name if mt else "Unknown",
                "summary": display,
                "date": _date_str(me.recorded_date),
                "tags": tags,
                "metadata": {
                    "value": me.value,
                    "unit": unit,
                    "metric_type_id": me.metric_type_id,
                },
            }
        )
    return items


def _query_results(
    db: Session,
    *,
    tag: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list[dict]:
    query = db.query(ResultEntry).join(
        ExerciseType, ResultEntry.exercise_type_id == ExerciseType.id
    )
    if date_from:
        query = query.filter(ResultEntry.recorded_date >= date_from)
    if date_to:
        query = query.filter(ResultEntry.recorded_date <= date_to)
    if tag:
        query = query.filter(
            ResultEntry.exercise_type_id.in_(
                db.query(EntityTag.entity_id).filter(
                    EntityTag.entity_type == "exercise_type",
                    EntityTag.tag == tag.strip().lower(),
                )
            )
        )
    items = []
    for re in query.all():
        et = db.get(ExerciseType, re.exercise_type_id)
        tags = get_tags(db, "exercise_type", re.exercise_type_id) if et else []
        display = re.display_value or f"{re.value}"
        items.append(
            {
                "type": "result",
                "id": re.id,
                "title": et.name if et else "Unknown",
                "summary": display,
                "date": _date_str(re.recorded_date),
                "tags": tags,
                "metadata": {
                    "value": re.value,
                    "display_value": re.display_value,
                    "is_pr": re.is_pr,
                    "is_rx": re.is_rx,
                    "exercise_type_id": re.exercise_type_id,
                },
            }
        )
    return items


def _query_goals(
    db: Session,
    *,
    tag: str | None,
    date_from: date | None,
    date_to: date | None,
) -> list[dict]:
    query = db.query(Goal)
    # Goals use created_at as their timeline date
    if date_from:
        query = query.filter(Goal.created_at >= date_from)
    if date_to:
        # Include the full day of date_to
        from datetime import datetime, time

        end = datetime.combine(date_to, time.max)
        query = query.filter(Goal.created_at <= end)
    if tag:
        query = query.filter(
            Goal.id.in_(
                db.query(EntityTag.entity_id).filter(
                    EntityTag.entity_type == "goal",
                    EntityTag.tag == tag.strip().lower(),
                )
            )
        )
    items = []
    for g in query.all():
        tags = get_tags(db, "goal", g.id)
        # Compute progress
        from app.services.goal import _compute_current_value, _compute_progress

        current = _compute_current_value(db, g)
        progress = _compute_progress(
            current,
            g.target_value,
            lower_is_better=g.lower_is_better,
            start_value=g.start_value,
        )
        summary = f"{g.status.capitalize()} • {progress:.0f}% progress"
        goal_date = g.created_at.date() if hasattr(g.created_at, "date") else g.created_at
        items.append(
            {
                "type": "goal",
                "id": g.id,
                "title": g.title,
                "summary": summary,
                "date": _date_str(goal_date),
                "tags": tags,
                "metadata": {
                    "status": g.status,
                    "progress": progress,
                    "event": "created",
                },
            }
        )
    return items


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_TYPE_QUERIES = {
    "journal": _query_journals,
    "metric": _query_metrics,
    "result": _query_results,
    "goal": _query_goals,
}

_ALL_TYPES = list(_TYPE_QUERIES.keys())


def get_timeline(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
    types: list[str] | None = None,
    tag: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> dict:
    """Return a paginated, chronological timeline of health data.

    Args:
        db: SQLAlchemy session.
        page: 1-based page number.
        per_page: Items per page.
        types: Optional list of entity types to include.
        tag: Optional tag to filter by (applies to the parent entity type).
        date_from: Optional inclusive start date.
        date_to: Optional inclusive end date.

    Returns:
        dict with keys: items, total, page, per_page.
    """
    active_types = types if types else _ALL_TYPES
    kwargs = {"tag": tag, "date_from": date_from, "date_to": date_to}

    all_items: list[dict] = []
    for t in active_types:
        query_fn = _TYPE_QUERIES.get(t)
        if query_fn:
            all_items.extend(query_fn(db, **kwargs))

    # Sort by date descending
    all_items.sort(key=lambda x: x["date"], reverse=True)

    total = len(all_items)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = all_items[start:end]

    return {
        "items": page_items,
        "total": total,
        "page": page,
        "per_page": per_page,
    }
