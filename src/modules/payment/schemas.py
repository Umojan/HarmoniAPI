"""Payment request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class CreatePaymentIntentRequest(BaseModel):
    """Request schema for creating Stripe PaymentIntent."""

    email: EmailStr
    tariff_id: uuid.UUID


class PaymentIntentResponse(BaseModel):
    """Response schema for PaymentIntent creation."""

    payment_id: uuid.UUID
    client_secret: str
    amount: int
    currency: str
    status: str


class PaymentStatusResponse(BaseModel):
    """Response schema for payment status check."""

    payment_id: uuid.UUID = Field(..., alias="id")
    stripe_payment_intent_id: str
    user_id: uuid.UUID
    tariff_id: uuid.UUID | None
    amount: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "populate_by_name": True}


class StripeWebhookEvent(BaseModel):
    """Stripe webhook event schema (for documentation purposes)."""

    id: str = Field(..., description="Event ID from Stripe")
    type: str = Field(..., description="Event type (e.g., payment_intent.succeeded)")
    data: dict = Field(..., description="Event data containing PaymentIntent")
