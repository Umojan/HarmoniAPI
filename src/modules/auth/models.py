"""Email verification model definition."""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.mixin import BaseMixin


class EmailVerification(Base, BaseMixin):
    """Email verification model for temporary verification codes.

    Stores 6-digit verification codes with expiration and attempt tracking.
    Records are temporary and should be cleaned up after verification or expiration.

    Attributes:
        email: Email address being verified
        code: 6-digit numeric verification code
        expires_at: Expiration timestamp (TTL: 10 minutes)
        verified_at: Verification completion timestamp (NULL if not verified)
        attempts: Number of verification attempts (max 5)
        id: UUID primary key (from BaseMixin)
        created_at: Timestamp (from BaseMixin)
        updated_at: Timestamp (from BaseMixin)
    """

    __tablename__ = "email_verifications"

    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
