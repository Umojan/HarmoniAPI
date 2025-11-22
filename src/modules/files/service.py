"""File storage business logic and service layer."""

import os
import uuid
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.settings import settings
from src.modules.files.exceptions import (
    FileNotFoundException,
    FileSizeExceededException,
    InvalidFileTypeException,
    TariffNotFoundException,
)
from src.modules.files.models import TariffFile

logger = get_logger(__name__)


class FileService:
    """Service for PDF file upload, retrieval, and deletion."""

    ALLOWED_MIME_TYPE = "application/pdf"

    def __init__(self, session: AsyncSession) -> None:
        """Initialize file service.

        Args:
            session: Async database session
        """
        self.session = session
        self.max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
        self.upload_dir = Path(settings.upload_dir)

    async def upload_file(
        self, tariff_id: uuid.UUID, file: UploadFile
    ) -> TariffFile:
        """Upload PDF file for a tariff.

        Args:
            tariff_id: Tariff UUID
            file: Uploaded file

        Returns:
            Created file record

        Raises:
            TariffNotFoundException: If tariff doesn't exist
            InvalidFileTypeException: If file is not PDF
            FileSizeExceededException: If file exceeds size limit
        """
        # Verify tariff exists
        await self._verify_tariff_exists(tariff_id)

        # Validate file type
        if file.content_type != self.ALLOWED_MIME_TYPE:
            raise InvalidFileTypeException(file.content_type or "unknown")

        # Read file content
        content = await file.read()
        file_size = len(content)

        # Validate file size
        if file_size > self.max_size_bytes:
            raise FileSizeExceededException(file_size, self.max_size_bytes)

        # Generate unique filename
        file_extension = Path(file.filename or "file.pdf").suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Create tariff-specific directory
        tariff_dir = self.upload_dir / "tariffs" / str(tariff_id)
        tariff_dir.mkdir(parents=True, exist_ok=True)

        # Write file to disk
        file_path = tariff_dir / unique_filename
        relative_path = str(file_path.relative_to(self.upload_dir))

        with open(file_path, "wb") as f:
            f.write(content)

        # Create database record
        tariff_file = TariffFile(
            tariff_id=tariff_id,
            filename=file.filename or unique_filename,
            file_path=relative_path,
            file_size=file_size,
        )

        self.session.add(tariff_file)
        await self.session.flush()

        logger.info(
            f"File uploaded: {tariff_file.filename} ({file_size} bytes) for tariff {tariff_id}"
        )
        return tariff_file

    async def get_files_by_tariff(self, tariff_id: uuid.UUID) -> list[TariffFile]:
        """Get all files for a tariff.

        Args:
            tariff_id: Tariff UUID

        Returns:
            List of file records
        """
        stmt = (
            select(TariffFile)
            .where(TariffFile.tariff_id == tariff_id)
            .order_by(TariffFile.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_file_by_id(self, file_id: uuid.UUID) -> TariffFile | None:
        """Get file by ID.

        Args:
            file_id: File UUID

        Returns:
            File record or None if not found
        """
        stmt = select(TariffFile).where(TariffFile.id == file_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_file(self, file_id: uuid.UUID) -> None:
        """Delete file by ID.

        Args:
            file_id: File UUID

        Raises:
            FileNotFoundException: If file not found
        """
        file_record = await self.get_file_by_id(file_id)
        if not file_record:
            raise FileNotFoundException(str(file_id))

        # Delete physical file
        file_path = self.upload_dir / file_record.file_path
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Physical file deleted: {file_path}")
            else:
                logger.warning(
                    f"Physical file not found during deletion: {file_path}"
                )
        except Exception as e:
            logger.error(f"Error deleting physical file {file_path}: {e}")

        # Delete database record
        await self.session.delete(file_record)
        await self.session.flush()

        logger.info(f"File record deleted: {file_id}")

    async def create_download_link(
        self, file_id: uuid.UUID, user_email: str
    ) -> "DownloadLink":
        """Create a secure download link for a file.

        Args:
            file_id: File UUID
            user_email: Email of user who purchased the file

        Returns:
            Created download link record

        Raises:
            FileNotFoundException: If file not found
        """
        from src.modules.files.models import DownloadLink

        # Verify file exists
        file_record = await self.get_file_by_id(file_id)
        if not file_record:
            raise FileNotFoundException(str(file_id))

        # Create download link
        download_link = DownloadLink(
            download_uuid=uuid.uuid4(),
            file_id=file_id,
            user_email=user_email,
            downloads_count=0,
            max_downloads=settings.download_link_max_uses,
        )

        self.session.add(download_link)
        await self.session.flush()

        logger.info(
            f"Download link created: {download_link.download_uuid} for file {file_id}"
        )
        return download_link

    async def get_download_link_by_uuid(
        self, download_uuid: uuid.UUID
    ) -> "DownloadLink | None":
        """Get download link by UUID.

        Args:
            download_uuid: Download link UUID

        Returns:
            Download link record or None
        """
        from src.modules.files.models import DownloadLink

        stmt = select(DownloadLink).where(DownloadLink.download_uuid == download_uuid)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def increment_download_count(self, download_uuid: uuid.UUID) -> None:
        """Increment download count for a link.

        Args:
            download_uuid: Download link UUID
        """
        from src.modules.files.models import DownloadLink

        stmt = select(DownloadLink).where(DownloadLink.download_uuid == download_uuid)
        result = await self.session.execute(stmt)
        link = result.scalar_one_or_none()

        if link:
            link.downloads_count += 1
            await self.session.flush()
            logger.info(
                f"Download count incremented: {download_uuid} (count: {link.downloads_count})"
            )

    async def _verify_tariff_exists(self, tariff_id: uuid.UUID) -> None:
        """Verify that tariff exists.

        Args:
            tariff_id: Tariff UUID

        Raises:
            TariffNotFoundException: If tariff doesn't exist
        """
        from src.modules.tariffs.models import Tariff

        stmt = select(Tariff).where(Tariff.id == tariff_id)
        result = await self.session.execute(stmt)
        tariff = result.scalar_one_or_none()

        if not tariff:
            raise TariffNotFoundException(str(tariff_id))
