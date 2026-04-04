from __future__ import annotations

import os
from pathlib import Path

DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
MAX_BODY_SIZE: int = int(os.getenv("MAX_BODY_SIZE", str(1 * 1024 * 1024)))  # 1 MB

# Database
DATABASE_DIR: str = os.getenv("DATABASE_DIR", str(Path(__file__).resolve().parent.parent / "data"))
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/health_studio.db")

# WebAuthn
RP_ID: str = os.getenv("RP_ID", "localhost")
RP_NAME: str = os.getenv("RP_NAME", "Health Studio")
RP_ORIGIN: str = os.getenv("RP_ORIGIN", "http://localhost:3000")

# Session
SESSION_IDLE_TIMEOUT: int = int(os.getenv("SESSION_IDLE_TIMEOUT", str(24 * 60 * 60)))  # 24h
_7_DAYS = 7 * 24 * 60 * 60
SESSION_ABSOLUTE_TIMEOUT: int = int(os.getenv("SESSION_ABSOLUTE_TIMEOUT", str(_7_DAYS)))
CHALLENGE_TTL: int = int(os.getenv("CHALLENGE_TTL", str(5 * 60)))  # 5 min
