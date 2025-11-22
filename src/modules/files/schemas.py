"""File request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FileUploadResponse(BaseModel):
    """File upload response schema."""

    id: uuid.UUID
    tariff_id: uuid.UUID
    filename: str
    file_path: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class FileListResponse(BaseModel):
    """File list response schema."""

    id: uuid.UUID
    tariff_id: uuid.UUID
    filename: str
    file_size: int
    created_at: datetime

    model_config = {"from_attributes": True}


class DownloadLinkResponse(BaseModel):
    """Download link response schema."""

    download_uuid: uuid.UUID
    file_id: uuid.UUID
    filename: str
    downloads_remaining: int
    download_url: str

    model_config = {"from_attributes": True}
