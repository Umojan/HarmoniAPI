"""Admin request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    """Admin login request schema."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """OAuth2 token response schema."""

    access_token: str
    token_type: str = "bearer"


class RegisterRequest(BaseModel):
    """Admin registration request schema."""

    email: EmailStr
    password: str = Field(..., min_length=1)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class AdminResponse(BaseModel):
    """Admin response schema (excludes password hash)."""

    id: uuid.UUID
    email: str
    first_name: str | None
    last_name: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UpdateAdminRequest(BaseModel):
    """Admin update request schema (all fields optional)."""

    email: EmailStr | None = None
    password: str | None = Field(None, min_length=1)
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
