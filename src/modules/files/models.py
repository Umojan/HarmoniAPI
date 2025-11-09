"""Tariff file model definition."""

import uuid

from sqlalchemy import ForeignKey, String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.base import Base
from src.db.mixin import BaseMixin


class TariffFile(Base, BaseMixin):
    """File attachment model for tariff PDFs.

    Attributes:
        tariff_id: Foreign key to tariffs table
        filename: Original uploaded filename
        file_path: Relative path to file in uploads directory
        file_size: File size in bytes
        id: UUID primary key (from BaseMixin)
        created_at: Timestamp (from BaseMixin)
        updated_at: Timestamp (from BaseMixin)
    """

    __tablename__ = "tariff_files"

    tariff_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tariffs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Relationship to tariff (optional, for eager loading)
    # tariff: Mapped["Tariff"] = relationship("Tariff", back_populates="files")
