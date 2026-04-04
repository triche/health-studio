"""Authentication service — WebAuthn, sessions, and API keys."""

from __future__ import annotations

import secrets
import time
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import bcrypt
from fastapi import HTTPException, status
from webauthn import generate_authentication_options, generate_registration_options
from webauthn import verify_authentication_response as _verify_auth
from webauthn import verify_registration_response as _verify_reg
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from app.config import (
    CHALLENGE_TTL,
    RP_ID,
    RP_NAME,
    RP_ORIGIN,
    SESSION_ABSOLUTE_TIMEOUT,
    SESSION_IDLE_TIMEOUT,
)
from app.models.api_key import ApiKey
from app.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

# ---------------------------------------------------------------------------
# In-memory stores (single-process deployment)
# ---------------------------------------------------------------------------

# challenge_store: {challenge_bytes_hex: {"challenge": bytes, "created_at": float}}
_challenge_store: dict[str, dict] = {}

# session_store: {token: {"created_at": float, "last_seen": float}}
_session_store: dict[str, dict] = {}

# rate_limit_store: {ip: [timestamp, ...]}
_rate_limit_store: dict[str, list[float]] = {}

RATE_LIMIT_MAX = 5
RATE_LIMIT_WINDOW = 60  # seconds


# ---------------------------------------------------------------------------
# Challenge helpers
# ---------------------------------------------------------------------------
def _store_challenge(challenge: bytes, **extra: object) -> None:
    key = challenge.hex()
    _challenge_store[key] = {"challenge": challenge, "created_at": time.time(), **extra}


def _pop_challenge(challenge: bytes) -> bytes | None:
    key = challenge.hex()
    entry = _challenge_store.pop(key, None)
    if entry is None:
        return None
    if time.time() - entry["created_at"] > CHALLENGE_TTL:
        return None
    return entry["challenge"]


def clear_challenges() -> None:
    """For testing only."""
    _challenge_store.clear()


# ---------------------------------------------------------------------------
# Session helpers
# ---------------------------------------------------------------------------
def create_session() -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    _session_store[token] = {"created_at": now, "last_seen": now}
    return token


def validate_session(token: str | None) -> bool:
    if not token:
        return False
    session = _session_store.get(token)
    if session is None:
        return False
    now = time.time()
    if now - session["last_seen"] > SESSION_IDLE_TIMEOUT:
        _session_store.pop(token, None)
        return False
    if now - session["created_at"] > SESSION_ABSOLUTE_TIMEOUT:
        _session_store.pop(token, None)
        return False
    session["last_seen"] = now
    return True


def delete_session(token: str | None) -> None:
    if token:
        _session_store.pop(token, None)


def clear_sessions() -> None:
    """For testing only."""
    _session_store.clear()


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------
def check_rate_limit(ip: str) -> None:
    now = time.time()
    timestamps = _rate_limit_store.get(ip, [])
    timestamps = [t for t in timestamps if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed attempts. Try again later.",
        )
    _rate_limit_store[ip] = timestamps


def record_failed_attempt(ip: str) -> None:
    now = time.time()
    timestamps = _rate_limit_store.setdefault(ip, [])
    timestamps.append(now)


def clear_rate_limits() -> None:
    """For testing only."""
    _rate_limit_store.clear()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
def get_user(db: Session) -> User | None:
    return db.query(User).first()


def is_registered(db: Session) -> bool:
    user = get_user(db)
    return user is not None and user.credential_id is not None


def begin_registration(db: Session, display_name: str) -> dict:
    if is_registered(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A user is already registered. Only one user is allowed.",
        )

    options = generate_registration_options(
        rp_id=RP_ID,
        rp_name=RP_NAME,
        user_name=display_name,
        user_display_name=display_name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.PREFERRED,
        ),
    )

    _store_challenge(options.challenge, display_name=display_name)

    # Serialize to JSON-compatible dict
    from webauthn.helpers import options_to_json

    return {"options": options_to_json(options)}


def complete_registration(db: Session, credential: dict) -> User:
    # Find the stored challenge
    challenge = None
    display_name = "User"
    for _key, entry in list(_challenge_store.items()):
        if time.time() - entry["created_at"] <= CHALLENGE_TTL:
            challenge = entry["challenge"]
            display_name = entry.get("display_name", "User")
            break

    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid registration challenge found. Please restart registration.",
        )

    if is_registered(db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="A user is already registered. Only one user is allowed.",
        )

    verification = verify_registration_response(credential, challenge)

    # Pop the used challenge
    _pop_challenge(challenge)

    user = db.query(User).first()
    if user is None:
        user = User(display_name=display_name)
        db.add(user)
    else:
        user.display_name = display_name

    user.credential_id = verification.credential_id
    user.public_key = verification.credential_public_key
    user.sign_count = verification.sign_count

    db.commit()
    db.refresh(user)
    return user


def verify_registration_response(credential: dict, challenge: bytes):
    """Wrapper around py_webauthn for easier mocking in tests."""
    return _verify_reg(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=RP_ORIGIN,
    )


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def begin_authentication(db: Session) -> dict:
    user = get_user(db)
    if user is None or user.credential_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No registered user found. Please register first.",
        )

    options = generate_authentication_options(
        rp_id=RP_ID,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=user.credential_id),
        ],
        user_verification=UserVerificationRequirement.PREFERRED,
    )

    _store_challenge(options.challenge)

    from webauthn.helpers import options_to_json

    return {"options": options_to_json(options)}


def complete_authentication(db: Session, credential: dict) -> str:
    user = get_user(db)
    if user is None or user.credential_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No registered user found.",
        )

    # Find the stored challenge
    challenge = None
    for _key, entry in list(_challenge_store.items()):
        if time.time() - entry["created_at"] <= CHALLENGE_TTL:
            challenge = entry["challenge"]
            break

    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid authentication challenge found. Please restart login.",
        )

    verification = verify_authentication_response(credential, challenge, user)

    # Pop the used challenge
    _pop_challenge(challenge)

    # Update sign count
    user.sign_count = verification.new_sign_count
    db.commit()

    # Create session
    return create_session()


def verify_authentication_response(credential: dict, challenge: bytes, user: User):
    """Wrapper around py_webauthn for easier mocking in tests."""
    return _verify_auth(
        credential=credential,
        expected_challenge=challenge,
        expected_rp_id=RP_ID,
        expected_origin=RP_ORIGIN,
        credential_public_key=user.public_key,
        credential_current_sign_count=user.sign_count,
    )


# ---------------------------------------------------------------------------
# API Keys
# ---------------------------------------------------------------------------
def create_api_key(db: Session, name: str) -> tuple[ApiKey, str]:
    raw_key = secrets.token_urlsafe(32)
    prefix = raw_key[:8]
    key_hash = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt()).decode()

    api_key = ApiKey(
        name=name,
        key_hash=key_hash,
        prefix=prefix,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return api_key, raw_key


def list_api_keys(db: Session) -> list[ApiKey]:
    return db.query(ApiKey).filter(ApiKey.revoked.is_(False)).all()


def validate_api_key(db: Session, raw_key: str) -> ApiKey | None:
    prefix = raw_key[:8]
    candidates = db.query(ApiKey).filter(ApiKey.prefix == prefix, ApiKey.revoked.is_(False)).all()
    for candidate in candidates:
        if bcrypt.checkpw(raw_key.encode(), candidate.key_hash.encode()):
            candidate.last_used_at = datetime.now(UTC)
            db.commit()
            return candidate
    return None


def revoke_api_key(db: Session, key_id: str) -> None:
    api_key = db.get(ApiKey, key_id)
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )
    api_key.revoked = True
    db.commit()
