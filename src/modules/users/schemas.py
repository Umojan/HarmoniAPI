"""User request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserUpdateRequest(BaseModel):
    """User update request schema (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=100)
    surname: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None


class UserResponse(BaseModel):
    """User response schema."""

    id: uuid.UUID
    name: str
    surname: str
    email: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
