"""Resend email service adapter."""

import asyncio
from pathlib import Path

import resend
from resend.exceptions import ResendError

from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class ResendAdapter:
    """Adapter for Resend email service.

    Provides methods for sending verification codes and payment notifications.
    Initialized as singleton with API key from settings.
    """

    def __init__(self) -> None:
        """Initialize Resend adapter with API key."""
        resend.api_key = settings.resend_api_key
        self.from_email = settings.resend_from_email

    async def send_verification_code(
        self,
        to_email: str,
        name: str,
        code: str,
    ) -> None:
        """Send email verification code.

        Args:
            to_email: Recipient email address
            name: Recipient name
            code: 6-digit verification code

        Raises:
            EmailServiceException: If email sending fails
        """
        from src.modules.auth.exceptions import EmailServiceException

        try:
            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": "Your Harmoni Verification Code",
                "html": f"""
                    <html>
                        <body>
                            <h2>Welcome to Harmoni, {name}!</h2>
                            <p>Your verification code is:</p>
                            <h1 style="color: #4CAF50; letter-spacing: 5px;">{code}</h1>
                            <p>This code will expire in {settings.verification_code_ttl_minutes} minutes.</p>
                            <p>If you didn't request this code, please ignore this email.</p>
                            <br>
                            <p>Best regards,<br>Harmoni Team</p>
                        </body>
                    </html>
                """,
            }

            # Run blocking Resend call in thread pool
            email_response = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(
                f"Verification code sent to {to_email}",
                extra={"email_id": email_response.get("id"), "recipient": to_email},
            )

        except Exception as e:
            logger.error(
                f"Failed to send verification email to {to_email}: {str(e)}",
                exc_info=True,
            )
            raise EmailServiceException(reason=str(e))

    async def send_payment_success(
        self,
        to_email: str,
        name: str,
        tariff_name: str,
        amount: int,
        currency: str,
        pdf_paths: list[str] | None = None,
    ) -> None:
        """Send payment success email with optional PDF attachments.

        Args:
            to_email: Recipient email address
            name: Recipient name
            tariff_name: Name of purchased tariff
            amount: Payment amount in minor currency units (cents)
            currency: Currency code (e.g., 'usd')
            pdf_paths: Optional list of absolute paths to PDF files to attach

        Raises:
            Exception: If email sending fails
        """
        try:
            # Format amount (convert from cents to dollars/euros/etc)
            formatted_amount = f"{amount / 100:.2f}"

            subject = settings.payment_success_email_subject.format(
                tariff_name=tariff_name
            )
            body = settings.payment_success_email_body.format(
                name=name,
                tariff_name=tariff_name,
                amount=formatted_amount,
                currency=currency.upper(),
            )

            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": f"<html><body><pre>{body}</pre></body></html>",
            }

            # Attach PDFs if provided
            if pdf_paths:
                attachments = []
                for pdf_path in pdf_paths:
                    path = Path(pdf_path)
                    if path.exists():
                        with open(pdf_path, "rb") as f:
                            attachments.append({
                                "filename": path.name,
                                "content": list(f.read()),  # Convert bytes to list of ints
                            })
                    else:
                        logger.warning(f"PDF file not found: {pdf_path}")

                if attachments:
                    params["attachments"] = attachments

            # Run blocking Resend call in thread pool
            email_response = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(
                f"Payment success email sent to {to_email}",
                extra={
                    "email_id": email_response.get("id"),
                    "recipient": to_email,
                    "tariff": tariff_name,
                    "attachments_count": len(pdf_paths) if pdf_paths else 0,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to send payment success email to {to_email}: {str(e)}",
                exc_info=True,
            )
            raise

    async def send_payment_failure(
        self,
        to_email: str,
        name: str,
        tariff_name: str,
        reason: str,
    ) -> None:
        """Send payment failure notification email.

        Args:
            to_email: Recipient email address
            name: Recipient name
            tariff_name: Name of tariff user attempted to purchase
            reason: Failure reason/error message

        Raises:
            Exception: If email sending fails
        """
        try:
            subject = settings.payment_failure_email_subject.format(
                tariff_name=tariff_name
            )
            body = settings.payment_failure_email_body.format(
                name=name,
                tariff_name=tariff_name,
                reason=reason,
            )

            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": f"<html><body><pre>{body}</pre></body></html>",
            }

            # Run blocking Resend call in thread pool
            email_response = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(
                f"Payment failure email sent to {to_email}",
                extra={
                    "email_id": email_response.get("id"),
                    "recipient": to_email,
                    "tariff": tariff_name,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to send payment failure email to {to_email}: {str(e)}",
                exc_info=True,
            )
            raise


# Singleton instance
resend_adapter = ResendAdapter()
