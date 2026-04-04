from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy import func

from app.models.result import ExerciseType, ResultEntry

if TYPE_CHECKING:
    from datetime import date

    from sqlalchemy.orm import Session

    from app.schemas.result import (
        ExerciseTypeCreate,
        ExerciseTypeUpdate,
        ResultEntryCreate,
        ResultEntryUpdate,
    )


# ---------------------------------------------------------------------------
# Exercise Types
# ---------------------------------------------------------------------------


def create_exercise_type(db: Session, data: ExerciseTypeCreate) -> ExerciseType:
    existing = (
        db.query(ExerciseType).filter(func.lower(ExerciseType.name) == data.name.lower()).first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Exercise type '{data.name}' already exists",
        )
    et = ExerciseType(name=data.name, category=data.category, result_unit=data.result_unit)
    db.add(et)
    db.commit()
    db.refresh(et)
    return et


def get_exercise_type(db: Session, exercise_type_id: str) -> ExerciseType:
    et = db.get(ExerciseType, exercise_type_id)
    if et is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise type not found")
    return et


def list_exercise_types(db: Session) -> list[ExerciseType]:
    return db.query(ExerciseType).order_by(ExerciseType.name).all()


def update_exercise_type(
    db: Session, exercise_type_id: str, data: ExerciseTypeUpdate
) -> ExerciseType:
    et = get_exercise_type(db, exercise_type_id)
    update_data = data.model_dump(exclude_unset=True)
    if "name" in update_data:
        existing = (
            db.query(ExerciseType)
            .filter(func.lower(ExerciseType.name) == update_data["name"].lower())
            .filter(ExerciseType.id != exercise_type_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Exercise type '{update_data['name']}' already exists",
            )
    for key, value in update_data.items():
        setattr(et, key, value)
    db.commit()
    db.refresh(et)
    return et


def delete_exercise_type(db: Session, exercise_type_id: str) -> None:
    et = get_exercise_type(db, exercise_type_id)
    db.delete(et)
    db.commit()


# ---------------------------------------------------------------------------
# Result Entries
# ---------------------------------------------------------------------------


def _is_pr(
    db: Session,
    exercise_type: ExerciseType,
    value: float,
    *,
    is_rx: bool,
    exclude_id: str | None = None,
) -> bool:
    """Determine if a value is a personal record.

    For weight-based units (lbs, etc.), higher is better.
    For time-based units (seconds, time), lower is better.
    For time-based crossfit_benchmark exercises, RX always beats non-RX;
    within the same RX tier, lower time wins.
    """
    query = db.query(ResultEntry).filter(
        ResultEntry.exercise_type_id == exercise_type.id, ResultEntry.is_pr.is_(True)
    )
    if exclude_id is not None:
        query = query.filter(ResultEntry.id != exclude_id)
    best = query.order_by(ResultEntry.created_at.desc()).first()

    if best is None:
        return True

    is_time_based = exercise_type.result_unit in ("seconds", "time")
    is_crossfit = exercise_type.category == "crossfit_benchmark"

    if is_time_based and is_crossfit:
        # RX always beats non-RX
        if is_rx and not best.is_rx:
            return True
        if not is_rx and best.is_rx:
            return False
        # Same RX tier: lower time wins
        return value < best.value

    if is_time_based:
        return value < best.value
    return value > best.value


def create_result_entry(db: Session, data: ResultEntryCreate) -> ResultEntry:
    et = get_exercise_type(db, data.exercise_type_id)
    is_pr = _is_pr(db, et, data.value, is_rx=data.is_rx)
    entry = ResultEntry(
        exercise_type_id=data.exercise_type_id,
        value=data.value,
        display_value=data.display_value,
        recorded_date=data.recorded_date,
        is_pr=is_pr,
        is_rx=data.is_rx,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_result_entry(db: Session, entry_id: str) -> ResultEntry:
    entry = db.get(ResultEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Result entry not found")
    return entry


def list_result_entries(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
    exercise_type_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[ResultEntry], int]:
    query = db.query(ResultEntry)

    if exercise_type_id is not None:
        query = query.filter(ResultEntry.exercise_type_id == exercise_type_id)
    if date_from is not None:
        query = query.filter(ResultEntry.recorded_date >= date_from)
    if date_to is not None:
        query = query.filter(ResultEntry.recorded_date <= date_to)

    total = query.count()
    items = (
        query.order_by(ResultEntry.recorded_date.desc(), ResultEntry.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def update_result_entry(db: Session, entry_id: str, data: ResultEntryUpdate) -> ResultEntry:
    entry = get_result_entry(db, entry_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)

    # Recalculate PR if value or is_rx changed
    if "value" in update_data or "is_rx" in update_data:
        et = get_exercise_type(db, entry.exercise_type_id)
        entry.is_pr = _is_pr(db, et, entry.value, is_rx=entry.is_rx, exclude_id=entry_id)

    db.commit()
    db.refresh(entry)
    return entry


def delete_result_entry(db: Session, entry_id: str) -> None:
    entry = get_result_entry(db, entry_id)
    db.delete(entry)
    db.commit()


# ---------------------------------------------------------------------------
# PR History
# ---------------------------------------------------------------------------


def get_pr_history(db: Session, exercise_type_id: str) -> list[ResultEntry]:
    get_exercise_type(db, exercise_type_id)
    return (
        db.query(ResultEntry)
        .filter(ResultEntry.exercise_type_id == exercise_type_id, ResultEntry.is_pr.is_(True))
        .order_by(ResultEntry.recorded_date.asc())
        .all()
    )


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------


def get_result_trend(
    db: Session,
    exercise_type_id: str,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[ExerciseType, list[ResultEntry]]:
    et = get_exercise_type(db, exercise_type_id)
    query = db.query(ResultEntry).filter(ResultEntry.exercise_type_id == exercise_type_id)

    if date_from is not None:
        query = query.filter(ResultEntry.recorded_date >= date_from)
    if date_to is not None:
        query = query.filter(ResultEntry.recorded_date <= date_to)

    entries = query.order_by(ResultEntry.recorded_date.asc()).all()
    return et, entries
