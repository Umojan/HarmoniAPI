"""Tariff module exceptions."""

from src.core.exceptions import AppException


class TariffNotFoundException(AppException):
    """Raised when tariff is not found."""

    def __init__(self, tariff_id: str) -> None:
        super().__init__(
            message=f"Tariff not found: {tariff_id}",
            status_code=404,
            details={"tariff_id": tariff_id},
        )


class TariffAlreadyExistsException(AppException):
    """Raised when tariff with name already exists."""

    def __init__(self, name: str) -> None:
        super().__init__(
            message=f"Tariff with name '{name}' already exists",
            status_code=400,
            details={"name": name},
        )
