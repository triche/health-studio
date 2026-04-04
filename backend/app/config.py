from __future__ import annotations

import os
from pathlib import Path

DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
MAX_BODY_SIZE: int = int(os.getenv("MAX_BODY_SIZE", str(1 * 1024 * 1024)))  # 1 MB

# Database
DATABASE_DIR: str = os.getenv("DATABASE_DIR", str(Path(__file__).resolve().parent.parent / "data"))
DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{DATABASE_DIR}/health_studio.db")
