"""Search router — global full-text search across all entity types."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.search import SearchResponse, SearchResult
from app.services.search import search, search_count

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search", response_model=SearchResponse)
def global_search(
    q: str = Query("", description="Search query"),
    types: str | None = Query(None, description="Comma-separated entity types to filter"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    offset: int = Query(0, ge=0, description="Result offset"),
    db: Session = Depends(get_db),  # noqa: B008
) -> SearchResponse:
    """Full-text search across journals, goals, metric types, and exercise types."""
    entity_types = [t.strip() for t in types.split(",") if t.strip()] if types else None

    results = search(db, q, entity_types=entity_types, limit=limit, offset=offset)
    total = search_count(db, q, entity_types=entity_types)

    return SearchResponse(
        query=q,
        results=[SearchResult(**r) for r in results],
        total=total,
    )
