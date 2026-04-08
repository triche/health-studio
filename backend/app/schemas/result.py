from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

# --- Exercise Types ---


class ExerciseTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=100)
    result_unit: str = Field(min_length=1, max_length=50)
    tags: list[str] | None = None


class ExerciseTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    result_unit: str | None = Field(default=None, min_length=1, max_length=50)
    tags: list[str] | None = None


class ExerciseTypeResponse(BaseModel):
    id: str
    name: str
    category: str
    result_unit: str
    tags: list[str] = []
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Result Entries ---


class ResultEntryCreate(BaseModel):
    exercise_type_id: str
    value: float
    recorded_date: date
    display_value: str | None = None
    is_rx: bool = False
    notes: str | None = None


class ResultEntryUpdate(BaseModel):
    value: float | None = None
    recorded_date: date | None = None
    display_value: str | None = None
    is_rx: bool | None = None
    notes: str | None = None


class ResultEntryResponse(BaseModel):
    id: str
    exercise_type_id: str
    value: float
    display_value: str | None
    recorded_date: date
    is_pr: bool
    is_rx: bool
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ResultEntryListResponse(BaseModel):
    items: list[ResultEntryResponse]
    total: int
    page: int
    per_page: int


# --- Trend ---


class ResultTrendPoint(BaseModel):
    recorded_date: date
    value: float
    is_pr: bool
    is_rx: bool


class ResultTrendResponse(BaseModel):
    exercise_type_id: str
    exercise_name: str
    result_unit: str
    data: list[ResultTrendPoint]
