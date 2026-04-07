"""Schemas for global search."""

from __future__ import annotations

from pydantic import BaseModel


class SearchResult(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    snippet: str
    rank: float

    model_config = {"from_attributes": True}


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int
