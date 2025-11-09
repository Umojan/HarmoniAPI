"""Tariff request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TariffCreateRequest(BaseModel):
    """Tariff creation request schema."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    calories: int | None = Field(None, ge=0)
    features: list[str] | None = None
    base_price: int = Field(..., gt=0, description="Price in minor currency units (cents)")


class TariffUpdateRequest(BaseModel):
    """Tariff update request schema (all fields optional)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    calories: int | None = Field(None, ge=0)
    features: list[str] | None = None
    base_price: int | None = Field(None, gt=0, description="Price in minor currency units (cents)")


class TariffResponse(BaseModel):
    """Tariff response schema."""

    id: uuid.UUID
    name: str
    description: str | None
    calories: int | None
    features: list[str] | None
    base_price: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
