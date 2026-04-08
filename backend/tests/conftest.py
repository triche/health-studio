from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure DEBUG is off for tests by default
os.environ.setdefault("DEBUG", "false")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402, F401 — register all models
    ApiKey,
    AuthChallenge,
    AuthRateLimit,
    AuthSession,
    EntityMention,
    EntityTag,
    ExerciseType,
    Goal,
    JournalEntry,
    MetricEntry,
    MetricType,
    ResultEntry,
    User,
)

TEST_ENGINE = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autocommit=False, autoflush=False)


def _create_fts5_tables(engine):
    """Create FTS5 virtual tables that aren't managed by SQLAlchemy metadata."""
    with engine.connect() as conn:
        conn.execute(
            __import__("sqlalchemy").text(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    entity_type,
                    entity_id UNINDEXED,
                    title,
                    body,
                    extra,
                    tokenize='porter unicode61'
                )
                """
            )
        )
        conn.commit()


def _drop_fts5_tables(engine):
    """Drop FTS5 virtual tables."""
    with engine.connect() as conn:
        conn.execute(__import__("sqlalchemy").text("DROP TABLE IF EXISTS search_index"))
        conn.commit()


@pytest.fixture(autouse=True)
def _setup_db():
    """Create and drop all tables around every test."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    _create_fts5_tables(TEST_ENGINE)
    yield
    _drop_fts5_tables(TEST_ENGINE)
    Base.metadata.drop_all(bind=TEST_ENGINE)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


def _do_register_and_login(test_client: TestClient) -> None:
    """Register a user and log in, setting the session cookie on the client."""
    # Begin registration
    test_client.post("/api/auth/register", json={"display_name": "Test User"})

    # Complete registration with mock
    mock_reg = MagicMock()
    mock_reg.credential_id = b"\x01\x02\x03\x04"
    mock_reg.credential_public_key = b"\x05\x06\x07\x08"
    mock_reg.sign_count = 0

    with patch("app.services.auth.verify_registration_response", return_value=mock_reg):
        test_client.post(
            "/api/auth/register/complete",
            json={
                "id": "AQIDBA",
                "rawId": "AQIDBA",
                "response": {"attestationObject": "fake", "clientDataJSON": "fake"},
                "type": "public-key",
            },
        )

    # Begin login
    test_client.post("/api/auth/login")

    # Complete login with mock
    mock_auth = MagicMock()
    mock_auth.new_sign_count = 1
    mock_auth.credential_id = b"\x01\x02\x03\x04"

    with patch("app.services.auth.verify_authentication_response", return_value=mock_auth):
        test_client.post(
            "/api/auth/login/complete",
            json={
                "id": "AQIDBA",
                "rawId": "AQIDBA",
                "response": {
                    "authenticatorData": "fake",
                    "clientDataJSON": "fake",
                    "signature": "fake",
                },
                "type": "public-key",
            },
        )


@pytest.fixture()
def client():
    return TestClient(app)


@pytest.fixture()
def authed_client():
    """A TestClient with a valid session cookie (registered + logged in).

    Also sets X-Requested-With header by default so state-changing requests
    pass the CSRF check (matching what the frontend does).
    """
    c = TestClient(app, headers={"X-Requested-With": "HealthStudio"})
    _do_register_and_login(c)
    return c


@pytest.fixture()
def db():
    """Provide a clean in-memory SQLite database session for each test."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
