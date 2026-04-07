from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Index, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(UTC)


class EntityMention(Base):
    __tablename__ = "entity_mentions"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    journal_id: Mapped[str] = mapped_column(
        Text, ForeignKey("journal_entries.id", ondelete="CASCADE"), nullable=False
    )
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    entity_id: Mapped[str] = mapped_column(Text, nullable=False)
    display_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    __table_args__ = (
        UniqueConstraint(
            "journal_id", "entity_type", "entity_id", name="uq_mention_journal_entity"
        ),
        Index("ix_entity_mentions_journal_id", "journal_id"),
        Index("ix_entity_mentions_entity", "entity_type", "entity_id"),
    )
