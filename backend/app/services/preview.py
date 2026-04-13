from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.models.goal import Goal
from app.models.metric import MetricEntry, MetricType
from app.models.result import ExerciseType, ResultEntry
from app.services.goal import _compute_current_value, _compute_progress

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_preview_goal(db: Session, goal_id: str) -> dict:
    """Return a lightweight preview for a goal."""
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    current_value = _compute_current_value(db, goal)
    progress = _compute_progress(
        current_value,
        goal.target_value,
        lower_is_better=goal.lower_is_better,
        start_value=goal.start_value,
    )

    return {
        "entity_type": "goal",
        "entity_id": goal.id,
        "title": goal.title,
        "status": goal.status,
        "progress": progress,
        "target_value": goal.target_value,
        "current_value": current_value,
        "deadline": goal.deadline,
    }


def get_preview_metric_type(db: Session, metric_type_id: str) -> dict:
    """Return a lightweight preview for a metric type."""
    mt = db.get(MetricType, metric_type_id)
    if mt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric type not found")

    # Latest entry
    latest = (
        db.query(MetricEntry)
        .filter(MetricEntry.metric_type_id == metric_type_id)
        .order_by(MetricEntry.recorded_date.desc(), MetricEntry.created_at.desc())
        .first()
    )

    # Last 7 data points for trend (ordered ascending)
    trend_entries = (
        db.query(MetricEntry)
        .filter(MetricEntry.metric_type_id == metric_type_id)
        .order_by(MetricEntry.recorded_date.desc(), MetricEntry.created_at.desc())
        .limit(7)
        .all()
    )
    trend_entries.reverse()  # ascending order

    return {
        "entity_type": "metric_type",
        "entity_id": mt.id,
        "title": mt.name,
        "unit": mt.unit,
        "latest_value": latest.value if latest else None,
        "latest_date": latest.recorded_date if latest else None,
        "trend": [{"date": e.recorded_date, "value": e.value} for e in trend_entries],
    }


def get_preview_exercise_type(db: Session, exercise_type_id: str) -> dict:
    """Return a lightweight preview for an exercise type."""
    et = db.get(ExerciseType, exercise_type_id)
    if et is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise type not found")

    # Current PR
    pr = (
        db.query(ResultEntry)
        .filter(
            ResultEntry.exercise_type_id == exercise_type_id,
            ResultEntry.is_pr.is_(True),
        )
        .order_by(ResultEntry.recorded_date.desc(), ResultEntry.created_at.desc())
        .first()
    )

    # Last 5 results (ordered ascending)
    recent = (
        db.query(ResultEntry)
        .filter(ResultEntry.exercise_type_id == exercise_type_id)
        .order_by(ResultEntry.recorded_date.desc(), ResultEntry.created_at.desc())
        .limit(5)
        .all()
    )
    recent.reverse()  # ascending order

    return {
        "entity_type": "exercise_type",
        "entity_id": et.id,
        "title": et.name,
        "category": et.category,
        "result_unit": et.result_unit,
        "pr_value": pr.value if pr else None,
        "pr_date": pr.recorded_date if pr else None,
        "recent_results": [{"date": e.recorded_date, "value": e.value} for e in recent],
    }
