"""Payment business logic and service layer."""

import json
import uuid
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.settings import settings
from src.modules.files.models import TariffFile
from src.modules.payment.exceptions import (
    PaymentNotFoundException,
    TariffNotFoundException,
    UserNotVerifiedException,
)
from src.modules.payment.models import Payment
from src.modules.tariffs.models import Tariff
from src.modules.users.models import User
from src.services.resend.adapter import resend_adapter
from src.services.stripe.adapter import stripe_adapter

logger = get_logger(__name__)


class PaymentService:
    """Service for payment processing and Stripe integration.

    Handles PaymentIntent creation, webhook processing, and email notifications.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize payment service.

        Args:
            session: Async database session
        """
        self.session = session

    async def _get_tariff_name(self, tariff_id: uuid.UUID | None) -> str:
        """Get tariff name by ID.

        Args:
            tariff_id: Tariff UUID

        Returns:
            Tariff name or "Unknown Tariff" if not found
        """
        if not tariff_id:
            return "Unknown Tariff"

        stmt = select(Tariff).where(Tariff.id == tariff_id)
        result = await self.session.execute(stmt)
        tariff = result.scalar_one_or_none()
        return tariff.name if tariff else "Unknown Tariff"

    async def create_payment_intent(
        self,
        email: str,
        tariff_id: uuid.UUID,
    ) -> tuple[Payment, str]:
        """Create Stripe PaymentIntent and Payment record.

        Args:
            email: User email (must be verified)
            tariff_id: Tariff UUID to purchase

        Returns:
            Tuple of (Payment record, client_secret for frontend)

        Raises:
            UserNotVerifiedException: If email not verified
            TariffNotFoundException: If tariff not found
        """
        # Verify user exists and is verified
        stmt = select(User).where(User.email == email, User.is_verified == True)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise UserNotVerifiedException(email)

        # Get tariff
        stmt = select(Tariff).where(Tariff.id == tariff_id)
        result = await self.session.execute(stmt)
        tariff = result.scalar_one_or_none()

        if not tariff:
            raise TariffNotFoundException(str(tariff_id))

        # Prepare metadata for Stripe
        metadata = {
            "email": email,
            "user_id": str(user.id),
            "tariff_id": str(tariff_id),
            "tariff_name": tariff.name,
        }

        # Create PaymentIntent via Stripe
        payment_intent = await stripe_adapter.create_payment_intent(
            amount=tariff.base_price,
            currency="usd",
            metadata=metadata,
        )

        # Create Payment record
        payment = Payment(
            stripe_payment_intent_id=payment_intent.id,
            user_id=user.id,
            tariff_id=tariff_id,
            amount=tariff.base_price,
            currency="usd",
            status=payment_intent.status,
            payment_metadata=json.dumps(metadata),
        )

        self.session.add(payment)
        await self.session.flush()

        logger.info(
            f"Payment created for user {email}: {payment_intent.id}",
            extra={
                "payment_id": str(payment.id),
                "payment_intent_id": payment_intent.id,
                "amount": tariff.base_price,
                "tariff_name": tariff.name,
            },
        )

        return payment, payment_intent.client_secret

    async def get_payment_status(self, payment_id: uuid.UUID) -> Payment:
        """Get payment by ID.

        Args:
            payment_id: Payment UUID

        Returns:
            Payment record

        Raises:
            PaymentNotFoundException: If payment not found
        """
        stmt = select(Payment).where(Payment.id == payment_id)
        result = await self.session.execute(stmt)
        payment = result.scalar_one_or_none()

        if not payment:
            raise PaymentNotFoundException(str(payment_id))

        return payment

    async def handle_webhook_event(
        self,
        event_type: str,
        payment_intent_data: dict,
    ) -> None:
        """Handle Stripe webhook event.

        Args:
            event_type: Stripe event type (e.g., 'payment_intent.succeeded')
            payment_intent_data: PaymentIntent data from Stripe event
        """
        payment_intent_id = payment_intent_data.get("id")
        status = payment_intent_data.get("status")

        if not payment_intent_id:
            logger.error("Missing payment_intent_id in webhook data")
            return

        # Find payment record
        stmt = select(Payment).where(
            Payment.stripe_payment_intent_id == payment_intent_id
        )
        result = await self.session.execute(stmt)
        payment = result.scalar_one_or_none()

        if not payment:
            logger.warning(f"Payment not found for PaymentIntent: {payment_intent_id}")
            return

        # Update payment status
        old_status = payment.status
        payment.status = status
        await self.session.flush()

        logger.info(
            f"Payment status updated: {old_status} -> {status}",
            extra={
                "payment_id": str(payment.id),
                "payment_intent_id": payment_intent_id,
                "event_type": event_type,
            },
        )

        # Send email based on status
        if status == "succeeded":
            await self.send_success_email(payment)
        elif status in ["failed", "canceled"]:
            await self.send_failure_email(payment)

    async def send_success_email(self, payment: Payment) -> None:
        """Send success email with tariff PDFs.

        Args:
            payment: Payment record with succeeded status
        """
        # Get user
        stmt = select(User).where(User.id == payment.user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User not found for payment: {payment.id}")
            return

        # Get tariff name
        tariff_name = await self._get_tariff_name(payment.tariff_id)

        # Get tariff files (PDFs to attach)
        pdf_paths: list[str] = []
        if payment.tariff_id:
            stmt = select(TariffFile).where(TariffFile.tariff_id == payment.tariff_id)
            result = await self.session.execute(stmt)
            files = list(result.scalars().all())

            # Build absolute paths
            upload_dir = Path(settings.upload_dir)
            for file_record in files:
                file_path = upload_dir / file_record.file_path
                if file_path.exists():
                    pdf_paths.append(str(file_path))
                else:
                    logger.warning(f"PDF file not found: {file_path}")

        # Send email via Resend
        try:
            await resend_adapter.send_payment_success(
                to_email=user.email,
                name=user.name,
                tariff_name=tariff_name,
                amount=payment.amount,
                currency=payment.currency,
                pdf_paths=pdf_paths if pdf_paths else None,
            )

            logger.info(
                f"Success email sent to {user.email}",
                extra={
                    "payment_id": str(payment.id),
                    "pdf_count": len(pdf_paths),
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to send success email: {str(e)}",
                exc_info=True,
                extra={
                    "payment_id": str(payment.id),
                    "user_email": user.email,
                },
            )

    async def send_failure_email(self, payment: Payment) -> None:
        """Send failure email notification.

        Args:
            payment: Payment record with failed/canceled status
        """
        # Get user
        stmt = select(User).where(User.id == payment.user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            logger.error(f"User not found for payment: {payment.id}")
            return

        # Get tariff name
        tariff_name = await self._get_tariff_name(payment.tariff_id)

        # Send email via Resend
        try:
            await resend_adapter.send_payment_failure(
                to_email=user.email,
                name=user.name,
                tariff_name=tariff_name,
                reason=f"Payment {payment.status}",
            )

            logger.info(
                f"Failure email sent to {user.email}",
                extra={
                    "payment_id": str(payment.id),
                    "status": payment.status,
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to send failure email: {str(e)}",
                exc_info=True,
                extra={
                    "payment_id": str(payment.id),
                    "user_email": user.email,
                },
            )
