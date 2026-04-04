from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure DEBUG is off for tests by default
os.environ.setdefault("DEBUG", "false")

from app.database import Base  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402, F401 — register all models
    ApiKey,
    ExerciseType,
    Goal,
    JournalEntry,
    MetricEntry,
    MetricType,
    ResultEntry,
    User,
)


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def db():
    """Provide a clean in-memory SQLite database session for each test."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    test_session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
