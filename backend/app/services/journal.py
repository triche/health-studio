from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.models.journal import JournalEntry
from app.services.mentions import sync_mentions
from app.services.search import index_entity, remove_from_index
from app.services.tags import delete_entity_tags, get_tags, sync_tags

if TYPE_CHECKING:
    from datetime import date

    from sqlalchemy.orm import Session

    from app.schemas.journal import JournalCreate, JournalUpdate


def _attach_tags(db: Session, entry: JournalEntry) -> JournalEntry:
    """Attach tags list to journal entry for serialization."""
    entry.tags = get_tags(db, "journal", entry.id)  # type: ignore[attr-defined]
    return entry


def create_journal(db: Session, data: JournalCreate) -> JournalEntry:
    entry = JournalEntry(
        title=data.title,
        content=data.content,
        entry_date=data.entry_date,
    )
    db.add(entry)
    db.flush()
    sync_mentions(db, entry.id, data.content)
    if data.tags is not None:
        sync_tags(db, "journal", entry.id, data.tags)
    extra_parts = [str(data.entry_date)]
    if data.tags:
        extra_parts.extend(data.tags)
    index_entity(db, "journal", entry.id, data.title, data.content, " ".join(extra_parts))
    db.commit()
    db.refresh(entry)
    return _attach_tags(db, entry)


def get_journal(db: Session, journal_id: str) -> JournalEntry:
    entry = db.get(JournalEntry, journal_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return _attach_tags(db, entry)


def list_journals(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
    tag: str | None = None,
) -> tuple[list[JournalEntry], int]:
    from app.models.tag import EntityTag

    query = db.query(JournalEntry)

    if date_from is not None:
        query = query.filter(JournalEntry.entry_date >= date_from)
    if date_to is not None:
        query = query.filter(JournalEntry.entry_date <= date_to)
    if tag is not None:
        query = query.filter(
            JournalEntry.id.in_(
                db.query(EntityTag.entity_id).filter(
                    EntityTag.entity_type == "journal",
                    EntityTag.tag == tag.strip().lower(),
                )
            )
        )

    total = query.count()
    items = (
        query.order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return [_attach_tags(db, i) for i in items], total


def update_journal(db: Session, journal_id: str, data: JournalUpdate) -> JournalEntry:
    entry = db.get(JournalEntry, journal_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    update_data = data.model_dump(exclude_unset=True)
    tags = update_data.pop("tags", None)
    for key, value in update_data.items():
        setattr(entry, key, value)
    # Re-sync mentions if content changed
    if "content" in update_data:
        sync_mentions(db, entry.id, entry.content)
    if tags is not None:
        sync_tags(db, "journal", entry.id, tags)
    tag_list = get_tags(db, "journal", entry.id)
    extra_parts = [str(entry.entry_date)]
    extra_parts.extend(tag_list)
    index_entity(db, "journal", entry.id, entry.title, entry.content, " ".join(extra_parts))
    db.commit()
    db.refresh(entry)
    return _attach_tags(db, entry)


def delete_journal(db: Session, journal_id: str) -> None:
    entry = db.get(JournalEntry, journal_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    remove_from_index(db, "journal", entry.id)
    delete_entity_tags(db, "journal", entry.id)
    db.delete(entry)
    db.commit()
