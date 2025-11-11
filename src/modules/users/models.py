"""User model definition."""

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.mixin import BaseMixin


class User(Base, BaseMixin):
    """User model for registered platform users.

    Users register through email verification (no password).
    Stores minimal information required for payment and communication.

    Attributes:
        name: User's first name
        surname: User's last name
        email: Unique email address (verified)
        is_verified: Email verification status
        id: UUID primary key (from BaseMixin)
        created_at: Timestamp (from BaseMixin)
        updated_at: Timestamp (from BaseMixin)
    """

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
