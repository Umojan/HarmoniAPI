"""Auth module exceptions."""

from src.core.exceptions import AppException


class CodeExpiredException(AppException):
    """Raised when verification code has expired."""

    def __init__(self) -> None:
        """Initialize code expired exception."""
        super().__init__(
            message="Verification code has expired",
            status_code=400,
            details={"error_type": "verification_error"},
        )


class CodeInvalidException(AppException):
    """Raised when verification code is invalid."""

    def __init__(self) -> None:
        """Initialize code invalid exception."""
        super().__init__(
            message="Invalid verification code",
            status_code=400,
            details={"error_type": "verification_error"},
        )


class RateLimitExceededException(AppException):
    """Raised when rate limit for code requests is exceeded."""

    def __init__(self, retry_after_seconds: int) -> None:
        """Initialize rate limit exceeded exception.

        Args:
            retry_after_seconds: Seconds to wait before retrying
        """
        super().__init__(
            message=f"Rate limit exceeded. Please try again in {retry_after_seconds} seconds",
            status_code=429,
            details={
                "error_type": "rate_limit_error",
                "retry_after": retry_after_seconds,
            },
        )


class MaxAttemptsExceededException(AppException):
    """Raised when maximum verification attempts exceeded."""

    def __init__(self) -> None:
        """Initialize max attempts exceeded exception."""
        super().__init__(
            message="Maximum verification attempts exceeded. Please request a new code",
            status_code=400,
            details={"error_type": "verification_error"},
        )


class EmailAlreadyVerifiedException(AppException):
    """Raised when email is already verified (user exists)."""

    def __init__(self, email: str) -> None:
        """Initialize email already verified exception.

        Args:
            email: Email that is already verified
        """
        super().__init__(
            message="Email already verified",
            status_code=400,
            details={"error_type": "validation_error", "email": email},
        )


class EmailServiceException(AppException):
    """Raised when email service (Resend) fails."""

    def __init__(self, reason: str) -> None:
        """Initialize email service exception.

        Args:
            reason: Error reason from email service
        """
        super().__init__(
            message=f"Email service error: {reason}",
            status_code=503,
            details={"error_type": "email_service_error", "reason": reason},
        )
