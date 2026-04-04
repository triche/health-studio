from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterBegin(BaseModel):
    display_name: str = Field(default="User", min_length=1, max_length=200)


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    prefix: str
    created_at: datetime
    last_used_at: datetime | None

    model_config = {"from_attributes": True}


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    prefix: str
    raw_key: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthStatusResponse(BaseModel):
    registered: bool
    authenticated: bool
