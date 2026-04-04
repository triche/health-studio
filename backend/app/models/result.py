from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class ExerciseType(Base):
    __tablename__ = "exercise_types"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    category: Mapped[str] = mapped_column(Text, nullable=False)
    result_unit: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    results: Mapped[list[ResultEntry]] = relationship(back_populates="exercise_type")


class ResultEntry(Base):
    __tablename__ = "result_entries"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    exercise_type_id: Mapped[str] = mapped_column(
        Text, ForeignKey("exercise_types.id"), nullable=False
    )
    value: Mapped[float] = mapped_column(Float, nullable=False)
    display_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_pr: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rx: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    exercise_type: Mapped[ExerciseType] = relationship(back_populates="results")
