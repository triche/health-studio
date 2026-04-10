"""Schemas for the unified timeline."""

from __future__ import annotations

from pydantic import BaseModel


class TimelineItem(BaseModel):
    type: str
    id: str
    title: str
    summary: str
    date: str
    tags: list[str]
    metadata: dict

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    items: list[TimelineItem]
    total: int
    page: int
    per_page: int
