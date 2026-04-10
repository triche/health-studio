"""Timeline router — unified chronological feed of all entity types."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.timeline import TimelineResponse
from app.services.timeline import get_timeline

router = APIRouter(prefix="/api", tags=["timeline"])


@router.get("/timeline", response_model=TimelineResponse)
def timeline(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    types: str | None = Query(
        None, description="Comma-separated entity types: journal,metric,result,goal"
    ),
    tag: str | None = Query(None, description="Filter by tag"),
    date_from: date | None = Query(None, description="Start date (inclusive)"),
    date_to: date | None = Query(None, description="End date (inclusive)"),
    db: Session = Depends(get_db),  # noqa: B008
) -> TimelineResponse:
    """Return a unified, chronological timeline of health data."""
    entity_types = [t.strip() for t in types.split(",") if t.strip()] if types else None

    result = get_timeline(
        db,
        page=page,
        per_page=per_page,
        types=entity_types,
        tag=tag,
        date_from=date_from,
        date_to=date_to,
    )

    return TimelineResponse(**result)
