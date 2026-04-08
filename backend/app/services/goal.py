from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.models.goal import Goal
from app.models.metric import MetricEntry
from app.models.result import ResultEntry
from app.services.search import index_entity, remove_from_index
from app.services.tags import delete_entity_tags, get_tags, sync_tags

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.schemas.goal import GoalCreate, GoalUpdate


# ---------------------------------------------------------------------------
# Progress computation
# ---------------------------------------------------------------------------


def _compute_current_value(db: Session, goal: Goal) -> float:
    """Compute the current value for a goal based on its target type."""
    if goal.target_type == "metric":
        latest = (
            db.query(MetricEntry)
            .filter(MetricEntry.metric_type_id == goal.target_id)
            .order_by(MetricEntry.recorded_date.desc(), MetricEntry.created_at.desc())
            .first()
        )
        return latest.value if latest else 0.0

    if goal.target_type == "result":
        best = (
            db.query(ResultEntry)
            .filter(
                ResultEntry.exercise_type_id == goal.target_id,
                ResultEntry.is_pr.is_(True),
            )
            .order_by(ResultEntry.created_at.desc())
            .first()
        )
        return best.value if best else 0.0

    return goal.current_value


def _compute_progress(
    current_value: float,
    target_value: float,
    *,
    lower_is_better: bool = False,
    start_value: float | None = None,
) -> float:
    """Compute progress as a percentage (0-100), clamped.

    When start_value is provided, progress is measured as the proportion of
    the distance from start to target that has been covered.
    """
    if start_value is not None:
        span = start_value - target_value if lower_is_better else target_value - start_value
        if span == 0:
            return 100.0
        covered = start_value - current_value if lower_is_better else current_value - start_value
        pct = (covered / span) * 100.0
        return max(0.0, min(100.0, pct))

    # Legacy behaviour when no start_value is set
    if lower_is_better:
        if current_value <= target_value:
            return 100.0
        if target_value == 0:
            return 0.0
        pct = (target_value / current_value) * 100.0
        return max(0.0, min(100.0, pct))

    if target_value == 0:
        return 100.0 if current_value > 0 else 0.0
    pct = (current_value / target_value) * 100.0
    return max(0.0, min(100.0, pct))


def _enrich_goal(db: Session, goal: Goal) -> Goal:
    """Update goal's current_value dynamically and add progress + tags attributes."""
    goal.current_value = _compute_current_value(db, goal)
    goal.progress = _compute_progress(  # type: ignore[attr-defined]
        goal.current_value,
        goal.target_value,
        lower_is_better=goal.lower_is_better,
        start_value=goal.start_value,
    )
    goal.tags = get_tags(db, "goal", goal.id)  # type: ignore[attr-defined]
    return goal


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def create_goal(db: Session, data: GoalCreate) -> Goal:
    goal = Goal(
        title=data.title,
        description=data.description,
        plan=data.plan,
        target_type=data.target_type,
        target_id=data.target_id,
        target_value=data.target_value,
        start_value=data.start_value,
        lower_is_better=data.lower_is_better,
        status=data.status,
        deadline=data.deadline,
    )
    db.add(goal)
    db.flush()
    if data.tags is not None:
        sync_tags(db, "goal", goal.id, data.tags)
    body = "\n".join(filter(None, [data.description, data.plan]))
    extra_parts = [data.status or ""]
    if data.target_type:
        extra_parts.append(data.target_type)
    if data.deadline:
        extra_parts.append(str(data.deadline))
    if data.tags:
        extra_parts.extend(data.tags)
    index_entity(db, "goal", goal.id, data.title, body, " ".join(extra_parts))
    db.commit()
    db.refresh(goal)
    return _enrich_goal(db, goal)


def get_goal(db: Session, goal_id: str) -> Goal:
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    return _enrich_goal(db, goal)


def list_goals(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
    goal_status: str | None = None,
    tag: str | None = None,
) -> tuple[list[Goal], int]:
    from app.models.tag import EntityTag

    query = db.query(Goal)

    if goal_status is not None:
        query = query.filter(Goal.status == goal_status)
    if tag is not None:
        query = query.filter(
            Goal.id.in_(
                db.query(EntityTag.entity_id).filter(
                    EntityTag.entity_type == "goal",
                    EntityTag.tag == tag.strip().lower(),
                )
            )
        )

    total = query.count()
    items = (
        query.order_by(Goal.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    )
    return [_enrich_goal(db, g) for g in items], total


def update_goal(db: Session, goal_id: str, data: GoalUpdate) -> Goal:
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    update_data = data.model_dump(exclude_unset=True)
    tags = update_data.pop("tags", None)
    for key, value in update_data.items():
        setattr(goal, key, value)
    if tags is not None:
        sync_tags(db, "goal", goal.id, tags)
    body = "\n".join(filter(None, [goal.description, goal.plan]))
    extra_parts = [goal.status or ""]
    if goal.target_type:
        extra_parts.append(goal.target_type)
    if goal.deadline:
        extra_parts.append(str(goal.deadline))
    tag_list = get_tags(db, "goal", goal.id)
    extra_parts.extend(tag_list)
    index_entity(db, "goal", goal.id, goal.title, body, " ".join(extra_parts))
    db.commit()
    db.refresh(goal)
    return _enrich_goal(db, goal)


def delete_goal(db: Session, goal_id: str) -> None:
    goal = db.get(Goal, goal_id)
    if goal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
    remove_from_index(db, "goal", goal.id)
    delete_entity_tags(db, "goal", goal.id)
    db.delete(goal)
    db.commit()
