"""HTTP client wrapper for the Health Studio API.

Sends API key via Authorization header, never in query params.
Always includes X-Requested-With header for CSRF protection on mutations.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    from collections.abc import Generator

from health_studio_cli.config import read_config


@contextmanager
def get_client() -> Generator[httpx.Client, None, None]:
    """Create a configured httpx client for API calls."""
    config = read_config()
    base_url = config["base_url"]
    api_key = config["api_key"]

    headers = {
        "Authorization": f"Bearer {api_key}",
        "X-Requested-With": "HealthStudio",
        "Content-Type": "application/json",
    }

    with httpx.Client(base_url=base_url, headers=headers, timeout=30.0) as client:
        yield client
