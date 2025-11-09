"""Calculator module exceptions."""

from src.core.exceptions import AppException


class CalculatorException(AppException):
    """Base exception for calculator module."""

    pass


class InvalidBiometricDataException(CalculatorException):
    """Exception raised when biometric data validation fails."""

    def __init__(self, field: str, message: str):
        """Initialize exception.

        Args:
            field: Field name that failed validation
            message: Human-readable error message
        """
        super().__init__(
            message=f"Invalid {field}: {message}",
            status_code=422,
            details={"field": field, "error": message},
        )
