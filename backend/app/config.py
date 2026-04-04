from __future__ import annotations

import os

DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")
ALLOWED_ORIGINS: list[str] = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
MAX_BODY_SIZE: int = int(os.getenv("MAX_BODY_SIZE", str(1 * 1024 * 1024)))  # 1 MB
