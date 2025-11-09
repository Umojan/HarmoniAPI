"""Tariff business logic and service layer."""

import json
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.modules.tariffs.exceptions import (
    TariffAlreadyExistsException,
    TariffNotFoundException,
)
from src.modules.tariffs.models import Tariff

logger = get_logger(__name__)


class TariffService:
    """Service for tariff CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize tariff service.

        Args:
            session: Async database session
        """
        self.session = session

    async def create_tariff(
        self,
        name: str,
        base_price: int,
        description: str | None = None,
        calories: int | None = None,
        features: list[str] | None = None,
    ) -> Tariff:
        """Create a new tariff.

        Args:
            name: Tariff name (must be unique)
            base_price: Price in minor currency units (cents)
            description: Optional description
            calories: Optional calorie amount
            features: Optional list of features

        Returns:
            Created tariff instance

        Raises:
            TariffAlreadyExistsException: If name already exists
        """
        # Check for existing tariff with same name
        existing = await self.get_tariff_by_name(name)
        if existing:
            raise TariffAlreadyExistsException(name)

        # Serialize features to JSON string
        features_json = json.dumps(features) if features else None

        tariff = Tariff(
            name=name,
            description=description,
            calories=calories,
            features=features_json,
            base_price=base_price,
        )

        try:
            self.session.add(tariff)
            await self.session.flush()
            logger.info(f"Tariff created: {name} (price: {base_price})")
            return tariff
        except IntegrityError:
            await self.session.rollback()
            raise TariffAlreadyExistsException(name)

    async def get_all_tariffs(self) -> list[Tariff]:
        """Get all tariffs.

        Returns:
            List of all tariff instances
        """
        stmt = select(Tariff).order_by(Tariff.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_tariff_by_id(self, tariff_id: uuid.UUID) -> Tariff | None:
        """Get tariff by ID.

        Args:
            tariff_id: Tariff UUID

        Returns:
            Tariff instance or None if not found
        """
        stmt = select(Tariff).where(Tariff.id == tariff_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_tariff_by_name(self, name: str) -> Tariff | None:
        """Get tariff by name.

        Args:
            name: Tariff name

        Returns:
            Tariff instance or None if not found
        """
        stmt = select(Tariff).where(Tariff.name == name)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def update_tariff(
        self,
        tariff_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        calories: int | None = None,
        features: list[str] | None = None,
        base_price: int | None = None,
    ) -> Tariff:
        """Update tariff fields.

        Args:
            tariff_id: Tariff UUID to update
            name: New name (optional)
            description: New description (optional)
            calories: New calorie amount (optional)
            features: New features list (optional)
            base_price: New price (optional)

        Returns:
            Updated tariff instance

        Raises:
            TariffNotFoundException: If tariff not found
            TariffAlreadyExistsException: If new name already exists
        """
        tariff = await self.get_tariff_by_id(tariff_id)
        if not tariff:
            raise TariffNotFoundException(str(tariff_id))

        # Check name uniqueness if changing
        if name and name != tariff.name:
            existing = await self.get_tariff_by_name(name)
            if existing:
                raise TariffAlreadyExistsException(name)
            tariff.name = name

        # Update fields if provided
        if description is not None:
            tariff.description = description
        if calories is not None:
            tariff.calories = calories
        if features is not None:
            tariff.features = json.dumps(features)
        if base_price is not None:
            tariff.base_price = base_price

        try:
            await self.session.flush()
            logger.info(f"Tariff updated: {tariff.name}")
            return tariff
        except IntegrityError:
            await self.session.rollback()
            raise TariffAlreadyExistsException(name or tariff.name)

    async def delete_tariff(self, tariff_id: uuid.UUID) -> None:
        """Delete tariff by ID (cascades to files).

        Args:
            tariff_id: Tariff UUID to delete

        Raises:
            TariffNotFoundException: If tariff not found
        """
        tariff = await self.get_tariff_by_id(tariff_id)
        if not tariff:
            raise TariffNotFoundException(str(tariff_id))

        # Delete associated files first
        await self._delete_associated_files(tariff_id)

        # Delete tariff (cascade will handle DB file records)
        await self.session.delete(tariff)
        await self.session.flush()

        logger.info(f"Tariff deleted: {tariff.name} ({tariff_id})")

    async def _delete_associated_files(self, tariff_id: uuid.UUID) -> None:
        """Delete all physical files associated with a tariff.

        Args:
            tariff_id: Tariff UUID
        """
        from pathlib import Path

        from src.core.settings import settings
        from src.modules.files.models import TariffFile

        # Get all files for tariff
        stmt = select(TariffFile).where(TariffFile.tariff_id == tariff_id)
        result = await self.session.execute(stmt)
        files = list(result.scalars().all())

        # Delete physical files
        upload_dir = Path(settings.upload_dir)
        for file_record in files:
            file_path = upload_dir / file_record.file_path
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted physical file: {file_path}")
            except Exception as e:
                logger.error(f"Error deleting file {file_path}: {e}")

        if files:
            logger.info(f"Deleted {len(files)} file(s) for tariff {tariff_id}")
