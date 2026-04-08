"""Entity tag service — add, remove, sync, and query tags on any entity."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import func

from app.models.goal import Goal
from app.models.journal import JournalEntry
from app.models.metric import MetricType
from app.models.result import ExerciseType
from app.models.tag import EntityTag

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# Map entity_type to (Model, title_column)
_ENTITY_MODELS: dict[str, tuple[type, str]] = {
    "goal": (Goal, "title"),
    "journal": (JournalEntry, "title"),
    "metric_type": (MetricType, "name"),
    "exercise_type": (ExerciseType, "name"),
}


def add_tag(db: Session, entity_type: str, entity_id: str, tag: str) -> EntityTag:
    """Add a tag to an entity. Normalizes to lowercase/trimmed. No-op if already exists."""
    normalized = tag.strip().lower()
    existing = (
        db.query(EntityTag)
        .filter(
            EntityTag.entity_type == entity_type,
            EntityTag.entity_id == entity_id,
            EntityTag.tag == normalized,
        )
        .first()
    )
    if existing:
        return existing
    entity_tag = EntityTag(entity_type=entity_type, entity_id=entity_id, tag=normalized)
    db.add(entity_tag)
    db.flush()
    return entity_tag


def remove_tag(db: Session, entity_type: str, entity_id: str, tag: str) -> None:
    """Remove a tag from an entity."""
    normalized = tag.strip().lower()
    existing = (
        db.query(EntityTag)
        .filter(
            EntityTag.entity_type == entity_type,
            EntityTag.entity_id == entity_id,
            EntityTag.tag == normalized,
        )
        .first()
    )
    if existing:
        db.delete(existing)
        db.flush()


def get_tags(db: Session, entity_type: str, entity_id: str) -> list[str]:
    """Get all tags for an entity."""
    rows = (
        db.query(EntityTag.tag)
        .filter(
            EntityTag.entity_type == entity_type,
            EntityTag.entity_id == entity_id,
        )
        .order_by(EntityTag.tag)
        .all()
    )
    return [r[0] for r in rows]


def list_all_tags(db: Session) -> list[dict[str, Any]]:
    """Get all unique tags with usage counts, sorted by count desc."""
    rows = (
        db.query(EntityTag.tag, func.count(EntityTag.id).label("count"))
        .group_by(EntityTag.tag)
        .order_by(func.count(EntityTag.id).desc(), EntityTag.tag)
        .all()
    )
    return [{"tag": row[0], "count": row[1]} for row in rows]


def get_entities_by_tag(
    db: Session, tag: str, entity_type: str | None = None
) -> list[dict[str, Any]]:
    """Get all entities with a given tag, optionally filtered by type."""
    normalized = tag.strip().lower()
    query = db.query(EntityTag).filter(EntityTag.tag == normalized)
    if entity_type:
        query = query.filter(EntityTag.entity_type == entity_type)
    tag_rows = query.all()

    results: list[dict[str, Any]] = []
    for row in tag_rows:
        model_info = _ENTITY_MODELS.get(row.entity_type)
        title = ""
        if model_info:
            model_cls, title_col = model_info
            entity = db.get(model_cls, row.entity_id)
            if entity:
                title = getattr(entity, title_col, "")
        results.append(
            {
                "entity_type": row.entity_type,
                "entity_id": row.entity_id,
                "title": title,
            }
        )
    return results


def sync_tags(db: Session, entity_type: str, entity_id: str, tags: list[str]) -> None:
    """Set the exact tag list for an entity — adds new, removes missing."""
    desired = {t.strip().lower() for t in tags if t.strip()}
    current = set(get_tags(db, entity_type, entity_id))

    for tag in desired - current:
        add_tag(db, entity_type, entity_id, tag)
    for tag in current - desired:
        remove_tag(db, entity_type, entity_id, tag)


def delete_entity_tags(db: Session, entity_type: str, entity_id: str) -> None:
    """Remove all tags for an entity (used on entity deletion)."""
    db.query(EntityTag).filter(
        EntityTag.entity_type == entity_type,
        EntityTag.entity_id == entity_id,
    ).delete()
    db.flush()
