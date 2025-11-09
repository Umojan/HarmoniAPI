"""Tariff model definition."""

from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixin import BaseMixin


class Tariff(Base, BaseMixin):
    """Tariff plan model for nutrition offerings.

    Attributes:
        name: Tariff plan name (e.g., Fit Start, Balance, Energy)
        description: Detailed description of the tariff
        calories: Target daily calorie amount
        features: JSON-serialized list of features/highlights
        base_price: Price in minor currency units (e.g., cents)
        id: UUID primary key (from BaseMixin)
        created_at: Timestamp (from BaseMixin)
        updated_at: Timestamp (from BaseMixin)
    """

    __tablename__ = "tariffs"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    calories: Mapped[int | None] = mapped_column(Integer)
    features: Mapped[str | None] = mapped_column(Text)  # JSON as text
    base_price: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship to files (optional, for eager loading)
    # files: Mapped[list["TariffFile"]] = relationship("TariffFile", back_populates="tariff", cascade="all, delete-orphan")
