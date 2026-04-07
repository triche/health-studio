from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.mention import (
    BacklinkResponse,
    EntityNamesResponse,
    MentionResponse,
)
from app.services import journal as journal_service
from app.services import mentions as mention_service

router = APIRouter(prefix="/api", tags=["mentions"])


# ---------------------------------------------------------------------------
# Entity names (for autocomplete)
# ---------------------------------------------------------------------------


@router.get("/entities/names", response_model=EntityNamesResponse)
def entity_names(db: Session = Depends(get_db)):
    return mention_service.get_entity_names(db)


# ---------------------------------------------------------------------------
# Journal mentions
# ---------------------------------------------------------------------------


@router.get("/journals/{journal_id}/mentions", response_model=list[MentionResponse])
def journal_mentions(journal_id: str, db: Session = Depends(get_db)):
    # Validate journal exists
    journal_service.get_journal(db, journal_id)
    return mention_service.get_journal_mentions(db, journal_id)


# ---------------------------------------------------------------------------
# Backlinks
# ---------------------------------------------------------------------------


@router.get("/goals/{goal_id}/backlinks", response_model=list[BacklinkResponse])
def goal_backlinks(goal_id: str, db: Session = Depends(get_db)):
    return mention_service.get_backlinks(db, "goal", goal_id)


@router.get("/metric-types/{metric_type_id}/backlinks", response_model=list[BacklinkResponse])
def metric_type_backlinks(metric_type_id: str, db: Session = Depends(get_db)):
    return mention_service.get_backlinks(db, "metric_type", metric_type_id)


@router.get("/exercise-types/{exercise_type_id}/backlinks", response_model=list[BacklinkResponse])
def exercise_type_backlinks(exercise_type_id: str, db: Session = Depends(get_db)):
    return mention_service.get_backlinks(db, "exercise_type", exercise_type_id)
