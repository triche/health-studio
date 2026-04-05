from __future__ import annotations


def test_health_returns_ok(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_cors_disallowed_origin_rejected(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://evil.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") != "http://evil.example.com"


def test_cors_allowed_origin(client):
    response = client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_body_too_large_returns_413(client):
    oversized = b"x" * (1024 * 1024 + 1)
    response = client.post(
        "/api/health",
        content=oversized,
        headers={"Content-Length": str(len(oversized)), "Content-Type": "application/octet-stream"},
    )
    assert response.status_code == 413


def test_error_no_stacktrace_when_debug_off():
    """When DEBUG=false, a 500 error should not contain a traceback."""
    from unittest.mock import MagicMock, patch

    from starlette.testclient import TestClient

    from app.main import app

    @app.get("/api/_test_error")
    async def _raise_error():
        raise RuntimeError("boom")

    c = TestClient(app, raise_server_exceptions=False)
    # Register + login to get past auth middleware
    c.post("/api/auth/register", json={"display_name": "Test User"})
    mock_reg = MagicMock()
    mock_reg.credential_id = b"\x01\x02\x03\x04"
    mock_reg.credential_public_key = b"\x05\x06\x07\x08"
    mock_reg.sign_count = 0
    with patch("app.services.auth.verify_registration_response", return_value=mock_reg):
        c.post(
            "/api/auth/register/complete",
            json={
                "id": "AQIDBA",
                "rawId": "AQIDBA",
                "response": {"attestationObject": "fake", "clientDataJSON": "fake"},
                "type": "public-key",
            },
        )
    c.post("/api/auth/login")
    mock_auth = MagicMock()
    mock_auth.new_sign_count = 1
    mock_auth.credential_id = b"\x01\x02\x03\x04"
    with patch("app.services.auth.verify_authentication_response", return_value=mock_auth):
        c.post(
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

    response = c.get("/api/_test_error")
    assert response.status_code == 500
    body = response.json()
    assert "traceback" not in body
    assert body["detail"] == "Internal server error"


def test_reset_endpoint_not_available_when_testing_false(client):
    """The /api/test/reset endpoint should not exist when TESTING=false."""
    response = client.post("/api/test/reset")
    # Should get 401/403/404/405 — but NOT 200
    assert response.status_code in (401, 403, 404, 405)


def test_reset_endpoint_available_when_testing_true():
    """The /api/test/reset endpoint works when TESTING=true."""
    import importlib
    import os

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from starlette.testclient import TestClient

    # Rebuild app with TESTING=true
    os.environ["TESTING"] = "true"
    try:
        import app.config as cfg

        importlib.reload(cfg)
        assert cfg.TESTING is True

        import app.main as main_mod

        importlib.reload(main_mod)
        test_app = main_mod.app

        from app.database import Base, get_db

        engine = create_engine(
            "sqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False)  # noqa: N806
        Base.metadata.create_all(bind=engine)

        def override_db():
            db = Session()
            try:
                yield db
            finally:
                db.close()

        test_app.dependency_overrides[get_db] = override_db

        c = TestClient(test_app)
        response = c.post("/api/test/reset")
        assert response.status_code == 200
        assert response.json() == {"status": "reset"}
    finally:
        os.environ["TESTING"] = "false"
        importlib.reload(cfg)
        importlib.reload(main_mod)
