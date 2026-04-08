from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status
from sqlalchemy import func

from app.models.metric import MetricEntry, MetricType
from app.services.search import index_entity, remove_from_index
from app.services.tags import delete_entity_tags, get_tags, sync_tags

if TYPE_CHECKING:
    from datetime import date

    from sqlalchemy.orm import Session

    from app.schemas.metric import (
        MetricEntryCreate,
        MetricEntryUpdate,
        MetricTypeCreate,
        MetricTypeUpdate,
    )


# ---------------------------------------------------------------------------
# Metric Types
# ---------------------------------------------------------------------------


def _attach_tags(db: Session, mt: MetricType) -> MetricType:
    """Attach tags list to metric type for serialization."""
    mt.tags = get_tags(db, "metric_type", mt.id)  # type: ignore[attr-defined]
    return mt


def create_metric_type(db: Session, data: MetricTypeCreate) -> MetricType:
    existing = db.query(MetricType).filter(func.lower(MetricType.name) == data.name.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Metric type '{data.name}' already exists",
        )
    mt = MetricType(name=data.name, unit=data.unit)
    db.add(mt)
    db.flush()
    if data.tags is not None:
        sync_tags(db, "metric_type", mt.id, data.tags)
    extra_parts = [data.unit or ""]
    if data.tags:
        extra_parts.extend(data.tags)
    index_entity(db, "metric_type", mt.id, data.name, "", " ".join(extra_parts))
    db.commit()
    db.refresh(mt)
    return _attach_tags(db, mt)


def get_metric_type(db: Session, metric_type_id: str) -> MetricType:
    mt = db.get(MetricType, metric_type_id)
    if mt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric type not found")
    return _attach_tags(db, mt)


def list_metric_types(db: Session, *, tag: str | None = None) -> list[MetricType]:
    from app.models.tag import EntityTag

    query = db.query(MetricType)
    if tag is not None:
        query = query.filter(
            MetricType.id.in_(
                db.query(EntityTag.entity_id).filter(
                    EntityTag.entity_type == "metric_type",
                    EntityTag.tag == tag.strip().lower(),
                )
            )
        )
    return [_attach_tags(db, mt) for mt in query.order_by(MetricType.name).all()]


def update_metric_type(db: Session, metric_type_id: str, data: MetricTypeUpdate) -> MetricType:
    mt = db.get(MetricType, metric_type_id)
    if mt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric type not found")
    update_data = data.model_dump(exclude_unset=True)
    tags = update_data.pop("tags", None)
    if "name" in update_data:
        existing = (
            db.query(MetricType)
            .filter(func.lower(MetricType.name) == update_data["name"].lower())
            .filter(MetricType.id != metric_type_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Metric type '{update_data['name']}' already exists",
            )
    for key, value in update_data.items():
        setattr(mt, key, value)
    if tags is not None:
        sync_tags(db, "metric_type", mt.id, tags)
    tag_list = get_tags(db, "metric_type", mt.id)
    extra_parts = [mt.unit or ""]
    extra_parts.extend(tag_list)
    index_entity(db, "metric_type", mt.id, mt.name, "", " ".join(extra_parts))
    db.commit()
    db.refresh(mt)
    return _attach_tags(db, mt)


def delete_metric_type(db: Session, metric_type_id: str) -> None:
    mt = db.get(MetricType, metric_type_id)
    if mt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric type not found")
    remove_from_index(db, "metric_type", mt.id)
    delete_entity_tags(db, "metric_type", mt.id)
    db.delete(mt)
    db.commit()


# ---------------------------------------------------------------------------
# Metric Entries
# ---------------------------------------------------------------------------


def create_metric_entry(db: Session, data: MetricEntryCreate) -> MetricEntry:
    # Validate metric type exists
    get_metric_type(db, data.metric_type_id)
    entry = MetricEntry(
        metric_type_id=data.metric_type_id,
        value=data.value,
        recorded_date=data.recorded_date,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_metric_entry(db: Session, entry_id: str) -> MetricEntry:
    entry = db.get(MetricEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric entry not found")
    return entry


def list_metric_entries(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
    metric_type_id: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[MetricEntry], int]:
    query = db.query(MetricEntry)

    if metric_type_id is not None:
        query = query.filter(MetricEntry.metric_type_id == metric_type_id)
    if date_from is not None:
        query = query.filter(MetricEntry.recorded_date >= date_from)
    if date_to is not None:
        query = query.filter(MetricEntry.recorded_date <= date_to)

    total = query.count()
    items = (
        query.order_by(MetricEntry.recorded_date.desc(), MetricEntry.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def update_metric_entry(db: Session, entry_id: str, data: MetricEntryUpdate) -> MetricEntry:
    entry = get_metric_entry(db, entry_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_metric_entry(db: Session, entry_id: str) -> None:
    entry = get_metric_entry(db, entry_id)
    db.delete(entry)
    db.commit()


# ---------------------------------------------------------------------------
# Trends
# ---------------------------------------------------------------------------


def get_metric_trend(
    db: Session,
    metric_type_id: str,
    *,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[MetricType, list[MetricEntry]]:
    mt = get_metric_type(db, metric_type_id)
    query = db.query(MetricEntry).filter(MetricEntry.metric_type_id == metric_type_id)

    if date_from is not None:
        query = query.filter(MetricEntry.recorded_date >= date_from)
    if date_to is not None:
        query = query.filter(MetricEntry.recorded_date <= date_to)

    entries = query.order_by(MetricEntry.recorded_date.asc()).all()
    return mt, entries
