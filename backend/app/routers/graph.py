"""Graph visualization router — interactive entity relationship graph."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.graph import GraphResponse
from app.services.graph import build_graph

router = APIRouter(prefix="/api", tags=["graph"])


@router.get("/graph", response_model=GraphResponse)
def graph(
    min_connections: int = Query(0, ge=0, description="Minimum connections to include a node"),
    include_orphans: bool = Query(False, description="Include nodes with no connections"),
    db: Session = Depends(get_db),  # noqa: B008
) -> GraphResponse:
    """Return a graph of entity connections for visualization."""
    result = build_graph(db, min_connections=min_connections, include_orphans=include_orphans)
    return GraphResponse(**result)
