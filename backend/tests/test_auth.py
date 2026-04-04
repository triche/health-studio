"""Tests for authentication and API key management (Phase 7)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.models.user import User


# ---------------------------------------------------------------------------
# Helper: register + complete (mocked WebAuthn)
# ---------------------------------------------------------------------------
def _register_user(client, display_name="Test User"):
    """Begin + complete registration with mocked WebAuthn."""
    # Step 1: begin registration
    resp = client.post("/api/auth/register", json={"display_name": display_name})
    assert resp.status_code == 200
    data = resp.json()
    assert "options" in data

    # Step 2: complete registration with mock credential
    mock_verification = MagicMock()
    mock_verification.credential_id = b"\x01\x02\x03\x04"
    mock_verification.credential_public_key = b"\x05\x06\x07\x08"
    mock_verification.sign_count = 0

    with patch("app.services.auth.verify_registration_response", return_value=mock_verification):
        resp2 = client.post(
            "/api/auth/register/complete",
            json={
                "id": "AQIDBA",
                "rawId": "AQIDBA",
                "response": {
                    "attestationObject": "fake",
                    "clientDataJSON": "fake",
                },
                "type": "public-key",
            },
        )
    return resp2


def _login_user(client):
    """Begin + complete login with mocked WebAuthn."""
    resp = client.post("/api/auth/login")
    assert resp.status_code == 200
    data = resp.json()
    assert "options" in data

    mock_verification = MagicMock()
    mock_verification.new_sign_count = 1
    mock_verification.credential_id = b"\x01\x02\x03\x04"

    with patch("app.services.auth.verify_authentication_response", return_value=mock_verification):
        resp2 = client.post(
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
    return resp2


def _get_authed_client(client):
    """Register + login and return the client (cookies set automatically)."""
    _register_user(client)
    resp = _login_user(client)
    assert resp.status_code == 200
    return client


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
class TestRegistration:
    def test_register_creates_user(self, client, db):
        resp = _register_user(client)
        assert resp.status_code == 201
        user = db.query(User).first()
        assert user is not None
        assert user.display_name == "Test User"
        assert user.credential_id is not None

    def test_register_locks_after_first_user(self, client):
        _register_user(client)
        # Second registration attempt should fail at begin
        resp = client.post("/api/auth/register", json={"display_name": "Hacker"})
        assert resp.status_code == 403
        assert "already registered" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Login / Session
# ---------------------------------------------------------------------------
class TestLogin:
    def test_login_returns_session_cookie(self, client):
        _register_user(client)
        resp = _login_user(client)
        assert resp.status_code == 200
        cookies = resp.cookies
        assert "session" in cookies

    def test_login_fails_without_registered_user(self, client):
        resp = client.post("/api/auth/login")
        assert resp.status_code == 401

    def test_session_allows_access_to_protected_endpoint(self, client):
        _get_authed_client(client)
        resp = client.get("/api/journals")
        assert resp.status_code == 200

    def test_logout_invalidates_session(self, client):
        _get_authed_client(client)
        resp = client.post("/api/auth/logout")
        assert resp.status_code == 200
        # After logout, protected endpoints return 401
        resp = client.get("/api/journals")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Unauthenticated access to protected endpoints
# ---------------------------------------------------------------------------
class TestProtectedEndpoints:
    @pytest.mark.parametrize(
        "method,path",
        [
            ("GET", "/api/journals"),
            ("POST", "/api/journals"),
            ("GET", "/api/metric-types"),
            ("GET", "/api/metrics"),
            ("GET", "/api/exercise-types"),
            ("GET", "/api/results"),
            ("GET", "/api/goals"),
            ("GET", "/api/dashboard/summary"),
        ],
    )
    def test_unauthenticated_returns_401(self, client, method, path):
        resp = client.request(method, path, headers={"X-Requested-With": "HealthStudio"})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
class TestApiKeys:
    def test_create_api_key(self, client):
        _get_authed_client(client)
        resp = client.post(
            "/api/keys",
            json={"name": "Test Key"},
            headers={"X-Requested-With": "HealthStudio"},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "raw_key" in data
        assert data["name"] == "Test Key"
        assert "prefix" in data

    def test_list_api_keys(self, client):
        _get_authed_client(client)
        client.post(
            "/api/keys",
            json={"name": "Key 1"},
            headers={"X-Requested-With": "HealthStudio"},
        )
        resp = client.get("/api/keys")
        assert resp.status_code == 200
        keys = resp.json()
        assert len(keys) == 1
        # raw_key should NOT be in list response
        assert "raw_key" not in keys[0]

    def test_api_key_auth_on_protected_endpoint(self, client):
        _get_authed_client(client)
        resp = client.post(
            "/api/keys",
            json={"name": "Script Key"},
            headers={"X-Requested-With": "HealthStudio"},
        )
        raw_key = resp.json()["raw_key"]

        # New client without session cookie — use API key instead
        from starlette.testclient import TestClient

        from app.main import app

        fresh_client = TestClient(app, cookies={})
        resp = fresh_client.get(
            "/api/journals",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert resp.status_code == 200

    def test_revoke_api_key(self, client):
        _get_authed_client(client)
        resp = client.post(
            "/api/keys",
            json={"name": "Revoke Me"},
            headers={"X-Requested-With": "HealthStudio"},
        )
        key_id = resp.json()["id"]
        raw_key = resp.json()["raw_key"]

        # Revoke it
        resp = client.delete(
            f"/api/keys/{key_id}",
            headers={"X-Requested-With": "HealthStudio"},
        )
        assert resp.status_code == 204

        # Revoked key should no longer work
        from starlette.testclient import TestClient

        from app.main import app

        fresh_client = TestClient(app, cookies={})
        resp = fresh_client.get(
            "/api/journals",
            headers={"Authorization": f"Bearer {raw_key}"},
        )
        assert resp.status_code == 401

    def test_unauthenticated_cannot_create_api_key(self, client):
        resp = client.post(
            "/api/keys",
            json={"name": "Bad Key"},
            headers={"X-Requested-With": "HealthStudio"},
        )
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# CSRF — X-Requested-With header required on state-changing requests
# ---------------------------------------------------------------------------
class TestCSRF:
    def test_post_without_x_requested_with_returns_403(self, client):
        _get_authed_client(client)
        resp = client.post(
            "/api/journals",
            json={"title": "Test", "content": "", "entry_date": "2025-01-01"},
            headers={"Content-Type": "application/json"},
        )
        assert resp.status_code == 403

    def test_get_without_x_requested_with_succeeds(self, client):
        """GET requests should not require X-Requested-With."""
        _get_authed_client(client)
        resp = client.get("/api/journals")
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Auth status endpoint
# ---------------------------------------------------------------------------
class TestAuthStatus:
    def test_status_unauthenticated(self, client):
        resp = client.get("/api/auth/status")
        data = resp.json()
        assert data["authenticated"] is False

    def test_status_authenticated(self, client):
        _get_authed_client(client)
        resp = client.get("/api/auth/status")
        data = resp.json()
        assert data["authenticated"] is True

    def test_status_shows_registration_needed(self, client):
        resp = client.get("/api/auth/status")
        data = resp.json()
        assert data["registered"] is False

    def test_status_shows_registered(self, client):
        _register_user(client)
        resp = client.get("/api/auth/status")
        data = resp.json()
        assert data["registered"] is True


# ---------------------------------------------------------------------------
# Verify wrapper functions pass correct argument types to py_webauthn
# ---------------------------------------------------------------------------
class TestWebAuthnWrappers:
    def test_verify_registration_passes_bytes_challenge(self):
        """verify_registration_response must pass raw bytes as expected_challenge."""
        from app.services.auth import verify_registration_response

        challenge = b"\x01\x02\x03"
        credential = {"id": "fake", "rawId": "fake", "response": {}, "type": "public-key"}

        with patch("app.services.auth._verify_reg") as mock_verify:
            mock_verify.side_effect = Exception("stop here")
            with pytest.raises(Exception, match="stop here"):
                verify_registration_response(credential, challenge)
            _, kwargs = mock_verify.call_args
            assert isinstance(kwargs["expected_challenge"], bytes)
            assert kwargs["expected_challenge"] == challenge

    def test_verify_authentication_passes_bytes_challenge(self):
        """verify_authentication_response must pass raw bytes as expected_challenge."""
        from app.services.auth import verify_authentication_response

        challenge = b"\x01\x02\x03"
        credential = {"id": "fake", "rawId": "fake", "response": {}, "type": "public-key"}
        mock_user = MagicMock()
        mock_user.public_key = b"\x05\x06\x07\x08"
        mock_user.sign_count = 0

        with patch("app.services.auth._verify_auth") as mock_verify:
            mock_verify.side_effect = Exception("stop here")
            with pytest.raises(Exception, match="stop here"):
                verify_authentication_response(credential, challenge, mock_user)
            _, kwargs = mock_verify.call_args
            assert isinstance(kwargs["expected_challenge"], bytes)
            assert kwargs["expected_challenge"] == challenge
