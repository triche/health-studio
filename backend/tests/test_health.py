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
    from starlette.testclient import TestClient

    from app.main import app

    @app.get("/api/_test_error")
    async def _raise_error():
        raise RuntimeError("boom")

    with TestClient(app, raise_server_exceptions=False) as c:
        response = c.get("/api/_test_error")
    assert response.status_code == 500
    body = response.json()
    assert "traceback" not in body
    assert body["detail"] == "Internal server error"
