from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

# --- Goals ---


class GoalCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = ""
    plan: str = ""
    target_type: str = Field(min_length=1, max_length=50)
    target_id: str
    target_value: float
    start_value: float | None = None
    lower_is_better: bool = False
    status: str = "active"
    deadline: date | None = None


class GoalUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    plan: str | None = None
    target_type: str | None = Field(default=None, min_length=1, max_length=50)
    target_id: str | None = None
    target_value: float | None = None
    start_value: float | None = None
    lower_is_better: bool | None = None
    status: str | None = None
    deadline: date | None = None


class GoalResponse(BaseModel):
    id: str
    title: str
    description: str
    plan: str
    target_type: str
    target_id: str
    target_value: float
    start_value: float | None
    current_value: float
    lower_is_better: bool
    status: str
    deadline: date | None
    progress: float
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class GoalListResponse(BaseModel):
    items: list[GoalResponse]
    total: int
    page: int
    per_page: int
