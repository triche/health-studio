from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class MentionResponse(BaseModel):
    entity_type: str
    entity_id: str
    display_text: str

    model_config = {"from_attributes": True}


class BacklinkResponse(BaseModel):
    journal_id: str
    title: str
    entry_date: date
    snippet: str

    model_config = {"from_attributes": True}


class EntityNameItem(BaseModel):
    id: str
    name: str


class EntityNamesResponse(BaseModel):
    goals: list[EntityNameItem]
    metric_types: list[EntityNameItem]
    exercise_types: list[EntityNameItem]
