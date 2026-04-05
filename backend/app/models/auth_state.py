"""SQLite-backed auth state — sessions, challenges, and rate limits."""

from __future__ import annotations

from sqlalchemy import Float, Integer, LargeBinary, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class AuthSession(Base):
    __tablename__ = "auth_sessions"

    token: Mapped[str] = mapped_column(Text, primary_key=True)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    last_seen: Mapped[float] = mapped_column(Float, nullable=False)


class AuthChallenge(Base):
    __tablename__ = "auth_challenges"

    challenge_hex: Mapped[str] = mapped_column(Text, primary_key=True)
    challenge: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    created_at: Mapped[float] = mapped_column(Float, nullable=False)
    display_name: Mapped[str | None] = mapped_column(Text, nullable=True)


class AuthRateLimit(Base):
    __tablename__ = "auth_rate_limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ip: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    attempted_at: Mapped[float] = mapped_column(Float, nullable=False)
