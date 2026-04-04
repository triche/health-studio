from __future__ import annotations

import contextlib
import traceback

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import ALLOWED_ORIGINS, DEBUG, MAX_BODY_SIZE
from app.database import get_db
from app.routers import goals, journals, metrics, results
from app.routers.auth import keys_router
from app.routers.auth import router as auth_router
from app.services import auth as auth_service

app = FastAPI(title="Health Studio", version="0.1.0")
app.include_router(auth_router)
app.include_router(keys_router)
app.include_router(journals.router)
app.include_router(metrics.router)
app.include_router(results.router)
app.include_router(goals.router)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request body size limit middleware
# ---------------------------------------------------------------------------
@app.middleware("http")
async def limit_body_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_BODY_SIZE:
        return JSONResponse(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            content={"detail": "Request body too large"},
        )
    response = await call_next(request)
    return response


# ---------------------------------------------------------------------------
# Auth middleware — protect all /api/* except auth endpoints and health check
# ---------------------------------------------------------------------------
# Paths that do not require authentication
_PUBLIC_PATHS = frozenset(
    {
        "/api/health",
        "/api/auth/status",
        "/api/auth/register",
        "/api/auth/register/complete",
        "/api/auth/login",
        "/api/auth/login/complete",
        "/api/auth/logout",
    }
)

# HTTP methods that mutate state (require X-Requested-With header)
_STATE_CHANGING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path

    # Skip non-API routes
    if not path.startswith("/api/"):
        return await call_next(request)

    # Skip public endpoints
    if path in _PUBLIC_PATHS:
        return await call_next(request)

    # CSRF check: state-changing requests must have X-Requested-With
    if request.method in _STATE_CHANGING_METHODS and not request.headers.get("x-requested-with"):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Missing X-Requested-With header"},
        )

    # Check session cookie
    session_token = request.cookies.get("session")
    if auth_service.validate_session(session_token):
        return await call_next(request)

    # Check API key in Authorization header
    auth_header = request.headers.get("authorization", "")
    if auth_header.startswith("Bearer "):
        raw_key = auth_header[7:]
        # Use dependency override if set (for testing), otherwise use real get_db
        db_factory = app.dependency_overrides.get(get_db, get_db)
        db_gen = db_factory()
        db = next(db_gen)
        try:
            api_key = auth_service.validate_api_key(db, raw_key)
            if api_key is not None:
                return await call_next(request)
        finally:
            with contextlib.suppress(StopIteration):
                next(db_gen)

    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": "Authentication required"},
    )


# ---------------------------------------------------------------------------
# Generic exception handler — hide stack traces when DEBUG=false
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    if DEBUG:
        tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc), "traceback": tb},
        )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
