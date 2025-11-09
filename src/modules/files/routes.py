"""File storage routes."""

import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_admin
from src.core.logging import get_logger
from src.db.engine import get_session
from src.modules.admin.models import Admin
from src.modules.files.schemas import FileListResponse, FileUploadResponse
from src.modules.files.service import FileService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/tariffs/{tariff_id}/files",
    response_model=FileUploadResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def upload_file(
    tariff_id: uuid.UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> FileUploadResponse:
    """Upload PDF file for a tariff (admin-only).

    Args:
        tariff_id: Tariff UUID
        file: PDF file to upload
        session: Database session
        current_admin: Current authenticated admin

    Returns:
        Uploaded file metadata

    Raises:
        TariffNotFoundException: If tariff not found (404)
        InvalidFileTypeException: If file is not PDF (400)
        FileSizeExceededException: If file exceeds size limit (413)
    """
    file_service = FileService(session)
    uploaded_file = await file_service.upload_file(tariff_id, file)

    logger.info(
        f"Admin {current_admin.email} uploaded file {uploaded_file.filename} to tariff {tariff_id}"
    )
    return FileUploadResponse.model_validate(uploaded_file)


@router.get(
    "/tariffs/{tariff_id}/files",
    response_model=list[FileListResponse],
    status_code=status.HTTP_200_OK,
)
async def get_tariff_files(
    tariff_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[FileListResponse]:
    """Get all files for a tariff.

    Args:
        tariff_id: Tariff UUID
        session: Database session

    Returns:
        List of file metadata
    """
    file_service = FileService(session)
    files = await file_service.get_files_by_tariff(tariff_id)
    return [FileListResponse.model_validate(f) for f in files]


@router.get(
    "/files/{file_id}",
    response_model=FileUploadResponse,
    status_code=status.HTTP_200_OK,
)
async def get_file_by_id(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> FileUploadResponse:
    """Get file metadata by ID.

    Args:
        file_id: File UUID
        session: Database session

    Returns:
        File metadata

    Raises:
        FileNotFoundException: If file not found (404)
    """
    file_service = FileService(session)
    file_record = await file_service.get_file_by_id(file_id)

    if not file_record:
        from src.modules.files.exceptions import FileNotFoundException

        raise FileNotFoundException(str(file_id))

    return FileUploadResponse.model_validate(file_record)


@router.delete(
    "/files/{file_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_file(
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> None:
    """Delete file by ID (admin-only).

    Args:
        file_id: File UUID
        session: Database session
        current_admin: Current authenticated admin

    Raises:
        FileNotFoundException: If file not found (404)
    """
    file_service = FileService(session)
    await file_service.delete_file(file_id)

    logger.info(f"Admin {current_admin.email} deleted file {file_id}")
