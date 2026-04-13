from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class TrendPoint(BaseModel):
    date: date
    value: float


class PreviewGoal(BaseModel):
    entity_type: str = "goal"
    entity_id: str
    title: str
    status: str
    progress: float
    target_value: float
    current_value: float
    deadline: date | None


class PreviewMetricType(BaseModel):
    entity_type: str = "metric_type"
    entity_id: str
    title: str
    unit: str
    latest_value: float | None
    latest_date: date | None
    trend: list[TrendPoint]


class PreviewExerciseType(BaseModel):
    entity_type: str = "exercise_type"
    entity_id: str
    title: str
    category: str
    result_unit: str
    pr_value: float | None
    pr_date: date | None
    recent_results: list[TrendPoint]
