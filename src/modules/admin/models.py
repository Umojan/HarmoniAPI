"""Admin model definition."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import Base
from src.db.mixin import BaseMixin


class Admin(Base, BaseMixin):
    """Admin user model for authentication and management access.

    Attributes:
        email: Unique admin email address
        hashed_password: Bcrypt-hashed password
        first_name: Optional first name
        last_name: Optional last name
        id: UUID primary key (from BaseMixin)
        created_at: Timestamp (from BaseMixin)
        updated_at: Timestamp (from BaseMixin)
    """

    __tablename__ = "admins"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(100))
    last_name: Mapped[str | None] = mapped_column(String(100))
