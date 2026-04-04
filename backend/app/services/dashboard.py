from __future__ import annotations

from typing import TYPE_CHECKING

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricEntry, MetricType
from app.models.result import ExerciseType, ResultEntry
from app.services.goal import _compute_current_value, _compute_progress

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def get_summary(db: Session) -> dict:
    """Aggregate dashboard summary across all domains."""

    # Recent journal entries (last 5)
    recent_journals = (
        db.query(JournalEntry)
        .order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        .limit(5)
        .all()
    )

    # Active goals with progress
    active_goals_raw = (
        db.query(Goal).filter(Goal.status == "active").order_by(Goal.created_at.desc()).all()
    )
    active_goals = []
    for goal in active_goals_raw:
        current = _compute_current_value(db, goal)
        progress = _compute_progress(current, goal.target_value)
        active_goals.append(
            {
                "id": goal.id,
                "title": goal.title,
                "target_type": goal.target_type,
                "target_value": goal.target_value,
                "current_value": current,
                "progress": progress,
                "status": goal.status,
                "deadline": goal.deadline.isoformat() if goal.deadline else None,
            }
        )

    # Latest metrics: most recent entry per metric type
    metric_types = db.query(MetricType).all()
    latest_metrics = []
    for mt in metric_types:
        latest = (
            db.query(MetricEntry)
            .filter(MetricEntry.metric_type_id == mt.id)
            .order_by(MetricEntry.recorded_date.desc(), MetricEntry.created_at.desc())
            .first()
        )
        if latest:
            latest_metrics.append(
                {
                    "metric_type_id": mt.id,
                    "metric_name": mt.name,
                    "unit": mt.unit,
                    "value": latest.value,
                    "recorded_date": latest.recorded_date.isoformat(),
                }
            )

    # Recent PRs (last 5)
    recent_prs_raw = (
        db.query(ResultEntry)
        .filter(ResultEntry.is_pr.is_(True))
        .order_by(ResultEntry.recorded_date.desc(), ResultEntry.created_at.desc())
        .limit(5)
        .all()
    )
    recent_prs = []
    for pr in recent_prs_raw:
        et = db.get(ExerciseType, pr.exercise_type_id)
        recent_prs.append(
            {
                "id": pr.id,
                "exercise_name": et.name if et else "Unknown",
                "value": pr.value,
                "display_value": pr.display_value,
                "recorded_date": pr.recorded_date.isoformat(),
                "is_rx": pr.is_rx,
            }
        )

    return {
        "recent_journals": [
            {
                "id": j.id,
                "title": j.title,
                "entry_date": j.entry_date.isoformat(),
            }
            for j in recent_journals
        ],
        "active_goals": active_goals,
        "latest_metrics": latest_metrics,
        "recent_prs": recent_prs,
    }
