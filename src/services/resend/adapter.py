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
                "subject": "Код верификации KatBalance",
                "html": f"""
                    <html>
                        <body>
                            <h2>Добро пожаловать в KatBalance, {name}!</h2>
                            <p>Ваш код верификации:</p>
                            <h1 style="color: #4CAF50; letter-spacing: 5px;">{code}</h1>
                            <p>Этот код истекает через {settings.verification_code_ttl_minutes} минут.</p>
                            <p>Если вы не запрашивали этот код, просто проигнорируйте это письмо.</p>
                            <br>
                            <p>С уважением,<br>Команда KatBalance</p>
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
        download_links: list[dict[str, str]] | None = None,
    ) -> None:
        """Send payment success email with download links.

        Args:
            to_email: Recipient email address
            name: Recipient name
            tariff_name: Name of purchased tariff
            amount: Payment amount in minor currency units (cents)
            currency: Currency code (e.g., 'usd')
            download_links: Optional list of dicts with 'filename' and 'url' keys

        Raises:
            Exception: If email sending fails
        """
        try:
            # Format amount (convert from cents to dollars/euros/etc)
            formatted_amount = f"{amount / 100:.2f}"

            # Format download links
            links_html = ""
            if download_links:
                links_list = []
                for link in download_links:
                    links_list.append(
                        f"📄 <a href=\"{link['url']}\">{link['filename']}</a>"
                    )
                links_html = "<br>".join(links_list)
            else:
                links_html = "Материалы скоро будут доступны."

            subject = settings.payment_success_email_subject.format(
                tariff_name=tariff_name
            )
            body = settings.payment_success_email_body.format(
                name=name,
                tariff_name=tariff_name,
                amount=formatted_amount,
                currency=currency.upper(),
                download_links=links_html,
                max_downloads=settings.download_link_max_uses,
            )

            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [to_email],
                "subject": subject,
                "html": f"<html><body><div style='white-space: pre-line;'>{body}</div></body></html>",
            }

            # Run blocking Resend call in thread pool
            email_response = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(
                f"Payment success email sent to {to_email}",
                extra={
                    "email_id": email_response.get("id"),
                    "recipient": to_email,
                    "tariff": tariff_name,
                    "links_count": len(download_links) if download_links else 0,
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

    async def send_contact_form(
        self,
        name: str,
        email: str,
        phone: str,
        telegram: str | None,
        comment: str,
    ) -> None:
        """Send contact form notification to owner.

        Args:
            name: Client name
            email: Client email
            phone: Client phone number
            telegram: Optional Telegram nickname
            comment: Client comment/message

        Raises:
            Exception: If email sending fails
        """
        try:
            subject = settings.contact_form_email_subject.format(name=name)
            body = settings.contact_form_email_body.format(
                name=name,
                email=email,
                phone=phone,
                telegram=telegram or "Не указан",
                comment=comment,
            )

            params: resend.Emails.SendParams = {
                "from": self.from_email,
                "to": [settings.owner_email],
                "subject": subject,
                "html": f"<html><body><pre>{body}</pre></body></html>",
            }

            # Run blocking Resend call in thread pool
            email_response = await asyncio.to_thread(resend.Emails.send, params)
            logger.info(
                f"Contact form email sent to owner",
                extra={
                    "email_id": email_response.get("id"),
                    "client_email": email,
                    "client_name": name,
                },
            )

        except Exception as e:
            logger.error(
                f"Failed to send contact form email: {str(e)}",
                exc_info=True,
            )
            raise


# Singleton instance
resend_adapter = ResendAdapter()
