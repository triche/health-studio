from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.goal import (
    GoalCreate,
    GoalListResponse,
    GoalResponse,
    GoalUpdate,
)
from app.services import dashboard as dashboard_service
from app.services import goal as goal_service

router = APIRouter(prefix="/api", tags=["goals"])


# ---------------------------------------------------------------------------
# Goals CRUD
# ---------------------------------------------------------------------------


@router.get("/goals", response_model=GoalListResponse)
def list_goals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = goal_service.list_goals(
        db, page=page, per_page=per_page, goal_status=status, tag=tag
    )
    return GoalListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/goals/{goal_id}", response_model=GoalResponse)
def get_goal(goal_id: str, db: Session = Depends(get_db)):
    return goal_service.get_goal(db, goal_id)


@router.post("/goals", response_model=GoalResponse, status_code=201)
def create_goal(data: GoalCreate, db: Session = Depends(get_db)):
    return goal_service.create_goal(db, data)


@router.put("/goals/{goal_id}", response_model=GoalResponse)
def update_goal(goal_id: str, data: GoalUpdate, db: Session = Depends(get_db)):
    return goal_service.update_goal(db, goal_id, data)


@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: str, db: Session = Depends(get_db)):
    goal_service.delete_goal(db, goal_id)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db)):
    return dashboard_service.get_summary(db)
