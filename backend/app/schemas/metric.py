from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field

# --- Metric Types ---


class MetricTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    unit: str = Field(min_length=1, max_length=50)


class MetricTypeUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    unit: str | None = Field(default=None, min_length=1, max_length=50)


class MetricTypeResponse(BaseModel):
    id: str
    name: str
    unit: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Metric Entries ---


class MetricEntryCreate(BaseModel):
    metric_type_id: str
    value: float
    recorded_date: date
    notes: str | None = None


class MetricEntryUpdate(BaseModel):
    value: float | None = None
    recorded_date: date | None = None
    notes: str | None = None


class MetricEntryResponse(BaseModel):
    id: str
    metric_type_id: str
    value: float
    recorded_date: date
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MetricEntryListResponse(BaseModel):
    items: list[MetricEntryResponse]
    total: int
    page: int
    per_page: int


# --- Trend ---


class TrendPoint(BaseModel):
    recorded_date: date
    value: float


class TrendResponse(BaseModel):
    metric_type_id: str
    metric_name: str
    unit: str
    data: list[TrendPoint]
