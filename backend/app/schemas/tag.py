"""Schemas for entity tags."""

from __future__ import annotations

from pydantic import BaseModel


class TagCount(BaseModel):
    tag: str
    count: int


class TagEntity(BaseModel):
    entity_type: str
    entity_id: str
    title: str


class TagEntitiesResponse(BaseModel):
    tag: str
    entities: list[TagEntity]
