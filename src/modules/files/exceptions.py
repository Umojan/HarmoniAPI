"""File module exceptions."""

from src.core.exceptions import AppException


class FileNotFoundException(AppException):
    """Raised when file is not found."""

    def __init__(self, file_id: str) -> None:
        super().__init__(
            message=f"File not found: {file_id}",
            status_code=404,
            details={"file_id": file_id},
        )


class InvalidFileTypeException(AppException):
    """Raised when uploaded file is not a PDF."""

    def __init__(self, content_type: str) -> None:
        super().__init__(
            message=f"Invalid file type: {content_type}. Only PDF files are allowed.",
            status_code=400,
            details={"content_type": content_type, "allowed": "application/pdf"},
        )


class FileSizeExceededException(AppException):
    """Raised when uploaded file exceeds size limit."""

    def __init__(self, file_size: int, max_size: int) -> None:
        super().__init__(
            message=f"File size {file_size} bytes exceeds maximum allowed size {max_size} bytes",
            status_code=413,
            details={
                "file_size_bytes": file_size,
                "max_size_bytes": max_size,
                "file_size_mb": round(file_size / (1024 * 1024), 2),
                "max_size_mb": round(max_size / (1024 * 1024), 2),
            },
        )


class TariffNotFoundException(AppException):
    """Raised when tariff is not found for file upload."""

    def __init__(self, tariff_id: str) -> None:
        super().__init__(
            message=f"Tariff not found: {tariff_id}",
            status_code=404,
            details={"tariff_id": tariff_id},
        )
