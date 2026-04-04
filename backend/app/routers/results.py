from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.result import (
    ExerciseTypeCreate,
    ExerciseTypeResponse,
    ExerciseTypeUpdate,
    ResultEntryCreate,
    ResultEntryListResponse,
    ResultEntryResponse,
    ResultEntryUpdate,
    ResultTrendPoint,
    ResultTrendResponse,
)
from app.services import result as result_service

router = APIRouter(prefix="/api", tags=["results"])


# ---------------------------------------------------------------------------
# Exercise Types
# ---------------------------------------------------------------------------


@router.get("/exercise-types", response_model=list[ExerciseTypeResponse])
def list_exercise_types(db: Session = Depends(get_db)):
    return result_service.list_exercise_types(db)


@router.post("/exercise-types", response_model=ExerciseTypeResponse, status_code=201)
def create_exercise_type(data: ExerciseTypeCreate, db: Session = Depends(get_db)):
    return result_service.create_exercise_type(db, data)


@router.put("/exercise-types/{exercise_type_id}", response_model=ExerciseTypeResponse)
def update_exercise_type(
    exercise_type_id: str, data: ExerciseTypeUpdate, db: Session = Depends(get_db)
):
    return result_service.update_exercise_type(db, exercise_type_id, data)


@router.delete("/exercise-types/{exercise_type_id}", status_code=204)
def delete_exercise_type(exercise_type_id: str, db: Session = Depends(get_db)):
    result_service.delete_exercise_type(db, exercise_type_id)


# ---------------------------------------------------------------------------
# PR History & Trends (must be before parameterized /results/{entry_id})
# ---------------------------------------------------------------------------


@router.get("/results/prs/{exercise_type_id}", response_model=list[ResultEntryResponse])
def get_pr_history(exercise_type_id: str, db: Session = Depends(get_db)):
    return result_service.get_pr_history(db, exercise_type_id)


@router.get("/results/trends/{exercise_type_id}", response_model=ResultTrendResponse)
def get_result_trend(
    exercise_type_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    et, entries = result_service.get_result_trend(
        db, exercise_type_id, date_from=date_from, date_to=date_to
    )
    return ResultTrendResponse(
        exercise_type_id=et.id,
        exercise_name=et.name,
        result_unit=et.result_unit,
        data=[
            ResultTrendPoint(
                recorded_date=e.recorded_date, value=e.value, is_pr=e.is_pr, is_rx=e.is_rx
            )
            for e in entries
        ],
    )


# ---------------------------------------------------------------------------
# Result Entries
# ---------------------------------------------------------------------------


@router.get("/results", response_model=ResultEntryListResponse)
def list_results(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    exercise_type_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    items, total = result_service.list_result_entries(
        db,
        page=page,
        per_page=per_page,
        exercise_type_id=exercise_type_id,
        date_from=date_from,
        date_to=date_to,
    )
    return ResultEntryListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/results/{entry_id}", response_model=ResultEntryResponse)
def get_result(entry_id: str, db: Session = Depends(get_db)):
    return result_service.get_result_entry(db, entry_id)


@router.post("/results", response_model=ResultEntryResponse, status_code=201)
def create_result(data: ResultEntryCreate, db: Session = Depends(get_db)):
    return result_service.create_result_entry(db, data)


@router.put("/results/{entry_id}", response_model=ResultEntryResponse)
def update_result(entry_id: str, data: ResultEntryUpdate, db: Session = Depends(get_db)):
    return result_service.update_result_entry(db, entry_id, data)


@router.delete("/results/{entry_id}", status_code=204)
def delete_result(entry_id: str, db: Session = Depends(get_db)):
    result_service.delete_result_entry(db, entry_id)
