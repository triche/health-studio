"""Tags router — browse all tags and entities by tag."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.tag import TagCount, TagEntitiesResponse, TagEntity
from app.services import tags as tag_service

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("", response_model=list[TagCount])
def list_tags(db: Session = Depends(get_db)):
    """Get all unique tags with usage counts."""
    return [TagCount(**t) for t in tag_service.list_all_tags(db)]


@router.get("/{tag}", response_model=TagEntitiesResponse)
def get_entities_by_tag(
    tag: str,
    type: str | None = Query(None, description="Filter by entity type"),  # noqa: A002
    db: Session = Depends(get_db),  # noqa: B008
):
    """Get all entities with a given tag."""
    entities = tag_service.get_entities_by_tag(db, tag, entity_type=type)
    return TagEntitiesResponse(
        tag=tag,
        entities=[TagEntity(**e) for e in entities],
    )
