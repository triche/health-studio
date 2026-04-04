from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    display_name: Mapped[str] = mapped_column(Text, nullable=False, default="")
    credential_id: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    public_key: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    sign_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
