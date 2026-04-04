from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

if TYPE_CHECKING:
    from collections.abc import Generator

    from sqlalchemy.orm import Session

from app.config import DATABASE_URL


class Base(DeclarativeBase):
    pass


def _ensure_db_dir(url: str) -> None:
    if url.startswith("sqlite:///"):
        db_path = url.replace("sqlite:///", "", 1)
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


_ensure_db_dir(DATABASE_URL)

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
