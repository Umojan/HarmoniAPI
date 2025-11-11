"""Payment module exceptions."""

from src.core.exceptions import AppException


class PaymentNotFoundException(AppException):
    """Raised when payment is not found."""

    def __init__(self, payment_id: str) -> None:
        """Initialize payment not found exception.

        Args:
            payment_id: Payment ID that was not found
        """
        super().__init__(
            message=f"Payment not found: {payment_id}",
            status_code=404,
            details={"payment_id": payment_id},
        )


class UserNotVerifiedException(AppException):
    """Raised when user email is not verified."""

    def __init__(self, email: str) -> None:
        """Initialize user not verified exception.

        Args:
            email: Email that is not verified
        """
        super().__init__(
            message=f"Email not verified: {email}",
            status_code=400,
            details={
                "error_type": "verification_error",
                "email": email,
                "message": "Please verify your email before making a payment",
            },
        )


class TariffNotFoundException(AppException):
    """Raised when tariff is not found."""

    def __init__(self, tariff_id: str) -> None:
        """Initialize tariff not found exception.

        Args:
            tariff_id: Tariff ID that was not found
        """
        super().__init__(
            message=f"Tariff not found: {tariff_id}",
            status_code=404,
            details={"tariff_id": tariff_id},
        )


class StripeWebhookException(AppException):
    """Raised when Stripe webhook processing fails."""

    def __init__(self, reason: str, event_id: str | None = None) -> None:
        """Initialize Stripe webhook exception.

        Args:
            reason: Reason for webhook failure
            event_id: Stripe event ID (if available)
        """
        details = {"error_type": "webhook_error", "reason": reason}
        if event_id:
            details["event_id"] = event_id

        super().__init__(
            message=f"Webhook processing failed: {reason}",
            status_code=400,
            details=details,
        )
