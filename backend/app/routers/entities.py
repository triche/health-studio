from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.preview import (
    get_preview_exercise_type,
    get_preview_goal,
    get_preview_metric_type,
)

router = APIRouter(prefix="/api", tags=["entities"])

_PREVIEW_HANDLERS = {
    "goal": get_preview_goal,
    "metric_type": get_preview_metric_type,
    "exercise_type": get_preview_exercise_type,
}


@router.get("/entities/preview")
def entity_preview(
    type: str = Query(...),  # noqa: A002
    id: str = Query(...),  # noqa: A002
    db: Session = Depends(get_db),
):
    handler = _PREVIEW_HANDLERS.get(type)
    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported entity type: {type}",
        )
    return handler(db, id)
