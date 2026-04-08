from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.journal import JournalCreate, JournalListResponse, JournalResponse, JournalUpdate
from app.services import journal as journal_service

router = APIRouter(prefix="/api/journals", tags=["journals"])


@router.post("", response_model=JournalResponse, status_code=201)
def create_journal(data: JournalCreate, db: Session = Depends(get_db)):
    return journal_service.create_journal(db, data)


@router.get("", response_model=JournalListResponse)
def list_journals(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    date_from: date | None = None,
    date_to: date | None = None,
    tag: str | None = None,
    db: Session = Depends(get_db),
):
    items, total = journal_service.list_journals(
        db, page=page, per_page=per_page, date_from=date_from, date_to=date_to, tag=tag
    )
    return JournalListResponse(items=items, total=total, page=page, per_page=per_page)


@router.get("/{journal_id}", response_model=JournalResponse)
def get_journal(journal_id: str, db: Session = Depends(get_db)):
    return journal_service.get_journal(db, journal_id)


@router.put("/{journal_id}", response_model=JournalResponse)
def update_journal(journal_id: str, data: JournalUpdate, db: Session = Depends(get_db)):
    return journal_service.update_journal(db, journal_id, data)


@router.delete("/{journal_id}", status_code=204)
def delete_journal(journal_id: str, db: Session = Depends(get_db)):
    journal_service.delete_journal(db, journal_id)
