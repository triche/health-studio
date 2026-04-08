from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


class JournalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    content: str = ""
    entry_date: date
    tags: list[str] | None = None


class JournalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = None
    entry_date: date | None = None
    tags: list[str] | None = None


class JournalResponse(BaseModel):
    id: str
    title: str
    content: str
    entry_date: date
    tags: list[str] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JournalListResponse(BaseModel):
    items: list[JournalResponse]
    total: int
    page: int
    per_page: int
