"""Admin module exceptions."""

from src.core.exceptions import AppException


class InvalidCredentialsException(AppException):
    """Raised when login credentials are invalid."""

    def __init__(self) -> None:
        """Initialize invalid credentials exception."""
        super().__init__(
            message="Invalid credentials",
            status_code=401,
            details={"error_type": "authentication_error"},
        )


class AdminNotFoundException(AppException):
    """Raised when admin is not found."""

    def __init__(self, admin_id: str | None = None) -> None:
        """Initialize admin not found exception.

        Args:
            admin_id: Optional admin ID for error details
        """
        super().__init__(
            message="Admin not found",
            status_code=401,
            details={"error_type": "authentication_error", "admin_id": admin_id},
        )


class AdminAlreadyExistsException(AppException):
    """Raised when attempting to create admin with existing email."""

    def __init__(self, email: str) -> None:
        """Initialize admin already exists exception.

        Args:
            email: Email that already exists
        """
        super().__init__(
            message="Email already registered",
            status_code=400,
            details={"error_type": "validation_error", "email": email},
        )


class NotAuthenticatedException(AppException):
    """Raised when authentication is required but not provided."""

    def __init__(self) -> None:
        """Initialize not authenticated exception."""
        super().__init__(
            message="Not authenticated",
            status_code=401,
            details={"error_type": "authentication_error"},
        )


class InvalidTokenException(AppException):
    """Raised when JWT token is invalid or expired."""

    def __init__(self) -> None:
        """Initialize invalid token exception."""
        super().__init__(
            message="Invalid token",
            status_code=401,
            details={"error_type": "authentication_error"},
        )
