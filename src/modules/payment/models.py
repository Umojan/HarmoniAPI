"""Payment model definition."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.mixin import BaseMixin


class Payment(Base, BaseMixin):
    """Payment model for tracking Stripe payment transactions.

    Stores complete payment information including Stripe PaymentIntent data,
    user reference, tariff reference, and payment status lifecycle.

    Attributes:
        stripe_payment_intent_id: Unique Stripe PaymentIntent ID
        user_id: Foreign key to users table
        tariff_id: Foreign key to tariffs table (nullable for custom amounts)
        amount: Payment amount in minor currency units (cents)
        currency: ISO 4217 currency code (e.g., 'usd')
        status: Stripe PaymentIntent status (requires_payment_method, requires_action,
                processing, requires_capture, succeeded, canceled, failed)
        payment_metadata: JSON metadata from Stripe (tariff details, user info)
        id: UUID primary key (from BaseMixin)
        created_at: Timestamp (from BaseMixin)
        updated_at: Timestamp (from BaseMixin)
    """

    __tablename__ = "payments"

    stripe_payment_intent_id: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tariff_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("tariffs.id", ondelete="SET NULL"),
        index=True,
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="usd")
    status: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    payment_metadata: Mapped[str | None] = mapped_column(Text)  # JSON as text
