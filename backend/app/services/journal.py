from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException, status

from app.models.journal import JournalEntry

if TYPE_CHECKING:
    from datetime import date

    from sqlalchemy.orm import Session

    from app.schemas.journal import JournalCreate, JournalUpdate


def create_journal(db: Session, data: JournalCreate) -> JournalEntry:
    entry = JournalEntry(
        title=data.title,
        content=data.content,
        entry_date=data.entry_date,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_journal(db: Session, journal_id: str) -> JournalEntry:
    entry = db.get(JournalEntry, journal_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Journal entry not found")
    return entry


def list_journals(
    db: Session,
    *,
    page: int = 1,
    per_page: int = 20,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[JournalEntry], int]:
    query = db.query(JournalEntry)

    if date_from is not None:
        query = query.filter(JournalEntry.entry_date >= date_from)
    if date_to is not None:
        query = query.filter(JournalEntry.entry_date <= date_to)

    total = query.count()
    items = (
        query.order_by(JournalEntry.entry_date.desc(), JournalEntry.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )
    return items, total


def update_journal(db: Session, journal_id: str, data: JournalUpdate) -> JournalEntry:
    entry = get_journal(db, journal_id)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry


def delete_journal(db: Session, journal_id: str) -> None:
    entry = get_journal(db, journal_id)
    db.delete(entry)
    db.commit()
