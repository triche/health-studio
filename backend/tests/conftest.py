from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

# Ensure DEBUG is off for tests by default
os.environ.setdefault("DEBUG", "false")

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    return TestClient(app)
