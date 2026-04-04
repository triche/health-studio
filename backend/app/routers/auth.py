"""Auth and API key routers."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.auth import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse,
    AuthStatusResponse,
    RegisterBegin,
)
from app.services import auth as auth_service

router = APIRouter(prefix="/api/auth", tags=["auth"])
keys_router = APIRouter(prefix="/api/keys", tags=["api_keys"])


# ---------------------------------------------------------------------------
# Auth status (public — no auth required)
# ---------------------------------------------------------------------------
@router.get("/status", response_model=AuthStatusResponse)
def auth_status(request: Request, db: Session = Depends(get_db)):
    registered = auth_service.is_registered(db)
    session_token = request.cookies.get("session")
    authenticated = auth_service.validate_session(session_token)
    return AuthStatusResponse(registered=registered, authenticated=authenticated)


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
@router.post("/register")
def begin_register(data: RegisterBegin, db: Session = Depends(get_db)):
    return auth_service.begin_registration(db, data.display_name)


@router.post("/register/complete", status_code=201)
def complete_register(request: Request, credential: dict, db: Session = Depends(get_db)):
    user = auth_service.complete_registration(db, credential)
    return {"id": user.id, "display_name": user.display_name}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------
@router.post("/login")
def begin_login(request: Request, db: Session = Depends(get_db)):
    auth_service.check_rate_limit(request.client.host if request.client else "unknown")
    return auth_service.begin_authentication(db)


@router.post("/login/complete")
def complete_login(
    request: Request,
    credential: dict,
    response: Response,
    db: Session = Depends(get_db),
):
    client_ip = request.client.host if request.client else "unknown"
    auth_service.check_rate_limit(client_ip)
    try:
        session_token = auth_service.complete_authentication(db, credential)
    except Exception:
        auth_service.record_failed_attempt(client_ip)
        raise
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        samesite="strict",
        path="/api",
        secure=False,  # Set to True in production with HTTPS
    )
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------
@router.post("/logout")
def logout(request: Request, response: Response):
    session_token = request.cookies.get("session")
    auth_service.delete_session(session_token)
    response.delete_cookie(key="session", path="/api")
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# API Keys (require session auth — enforced by middleware)
# ---------------------------------------------------------------------------
@keys_router.post("", response_model=ApiKeyCreatedResponse, status_code=201)
def create_api_key(data: ApiKeyCreate, db: Session = Depends(get_db)):
    api_key, raw_key = auth_service.create_api_key(db, data.name)
    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        prefix=api_key.prefix,
        raw_key=raw_key,
        created_at=api_key.created_at,
    )


@keys_router.get("", response_model=list[ApiKeyResponse])
def list_api_keys(db: Session = Depends(get_db)):
    return auth_service.list_api_keys(db)


@keys_router.delete("/{key_id}", status_code=204)
def revoke_api_key(key_id: str, db: Session = Depends(get_db)):
    auth_service.revoke_api_key(db, key_id)
