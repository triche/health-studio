from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.metric import (
    MetricEntryCreate,
    MetricEntryListResponse,
    MetricEntryResponse,
    MetricEntryUpdate,
    MetricTypeCreate,
    MetricTypeResponse,
    MetricTypeUpdate,
    TrendPoint,
    TrendResponse,
)
from app.services import metric as metric_service

router = APIRouter(prefix="/api", tags=["metrics"])


# ---------------------------------------------------------------------------
# Metric Types
# ---------------------------------------------------------------------------


@router.get("/metric-types", response_model=list[MetricTypeResponse])
def list_metric_types(db: Session = Depends(get_db)):
    return metric_service.list_metric_types(db)


@router.post("/metric-types", response_model=MetricTypeResponse, status_code=201)
def create_metric_type(data: MetricTypeCreate, db: Session = Depends(get_db)):
    return metric_service.create_metric_type(db, data)


@router.put("/metric-types/{metric_type_id}", response_model=MetricTypeResponse)
def update_metric_type(metric_type_id: str, data: MetricTypeUpdate, db: Session = Depends(get_db)):
    return metric_service.update_metric_type(db, metric_type_id, data)


@router.delete("/metric-types/{metric_type_id}", status_code=204)
def delete_metric_type(metric_type_id: str, db: Session = Depends(get_db)):
    metric_service.delete_metric_type(db, metric_type_id)


# ---------------------------------------------------------------------------
# Trends (must be before parameterized /metrics/{entry_id})
# ---------------------------------------------------------------------------


@router.get("/metrics/trends/{metric_type_id}", response_model=TrendResponse)
def get_metric_trend(
    metric_type_id: str,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    mt, entries = metric_service.get_metric_trend(
        db, metric_type_id, date_from=date_from, date_to=date_to
    )
    return TrendResponse(
        metric_type_id=mt.id,
        metric_name=mt.name,
        unit=mt.unit,
        data=[TrendPoint(recorded_date=e.recorded_date, value=e.value) for e in entries],
    )


# ---------------------------------------------------------------------------
# Metric Entries
# ---------------------------------------------------------------------------


@router.get("/metrics", response_model=MetricEntryListResponse)
def list_metrics(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    metric_type_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
):
    items, total = metric_service.list_metric_entries(
        db,
        page=page,
        per_page=per_page,
        metric_type_id=metric_type_id,
        date_from=date_from,
        date_to=date_to,
    )
    return MetricEntryListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/metrics/{entry_id}", response_model=MetricEntryResponse)
def get_metric(entry_id: str, db: Session = Depends(get_db)):
    return metric_service.get_metric_entry(db, entry_id)


@router.post("/metrics", response_model=MetricEntryResponse, status_code=201)
def create_metric(data: MetricEntryCreate, db: Session = Depends(get_db)):
    return metric_service.create_metric_entry(db, data)


@router.put("/metrics/{entry_id}", response_model=MetricEntryResponse)
def update_metric(entry_id: str, data: MetricEntryUpdate, db: Session = Depends(get_db)):
    return metric_service.update_metric_entry(db, entry_id, data)


@router.delete("/metrics/{entry_id}", status_code=204)
def delete_metric(entry_id: str, db: Session = Depends(get_db)):
    metric_service.delete_metric_entry(db, entry_id)
