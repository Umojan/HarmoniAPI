"""User module exceptions."""

from src.core.exceptions import AppException


class UserNotFoundException(AppException):
    """Raised when user is not found."""

    def __init__(self, identifier: str) -> None:
        """Initialize user not found exception.

        Args:
            identifier: User ID or email that was not found
        """
        super().__init__(
            message=f"User not found: {identifier}",
            status_code=404,
            details={"identifier": identifier},
        )


class UserAlreadyExistsException(AppException):
    """Raised when user with email already exists."""

    def __init__(self, email: str) -> None:
        """Initialize user already exists exception.

        Args:
            email: Email that already exists
        """
        super().__init__(
            message=f"User with email '{email}' already exists",
            status_code=400,
            details={"email": email},
        )
