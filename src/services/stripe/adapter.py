"""Stripe payment service adapter."""

import stripe

from src.core.logging import get_logger
from src.core.settings import settings

logger = get_logger(__name__)


class StripeAdapter:
    """Adapter for Stripe payment processing.

    Provides methods for creating PaymentIntents and verifying webhooks.
    Initialized as singleton with API key from settings.
    """

    def __init__(self) -> None:
        """Initialize Stripe adapter with API key."""
        stripe.api_key = settings.stripe_secret_key
        self.webhook_secret = settings.stripe_webhook_secret

    async def create_payment_intent(
        self,
        amount: int,
        currency: str,
        metadata: dict[str, str],
    ) -> stripe.PaymentIntent:
        """Create Stripe PaymentIntent.

        Args:
            amount: Payment amount in minor currency units (cents)
            currency: Currency code (e.g., 'usd')
            metadata: Metadata to attach to PaymentIntent (email, tariff_id, user info)

        Returns:
            Stripe PaymentIntent object

        Raises:
            stripe.error.StripeError: If PaymentIntent creation fails
        """
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,
                currency=currency,
                metadata=metadata,
                automatic_payment_methods={"enabled": True},
            )

            logger.info(
                f"PaymentIntent created: {payment_intent.id}",
                extra={
                    "payment_intent_id": payment_intent.id,
                    "amount": amount,
                    "currency": currency,
                    "metadata": metadata,
                },
            )

            return payment_intent

        except stripe.error.StripeError as e:
            logger.error(
                f"Failed to create PaymentIntent: {str(e)}",
                extra={"error_type": type(e).__name__, "metadata": metadata},
                exc_info=True,
            )
            raise

    def verify_webhook_signature(
        self,
        payload: bytes,
        sig_header: str,
    ) -> stripe.Event:
        """Verify Stripe webhook signature and construct event.

        Args:
            payload: Raw request body bytes
            sig_header: Stripe-Signature header value

        Returns:
            Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
        """
        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=self.webhook_secret,
            )

            logger.info(
                f"Webhook event verified: {event.type}",
                extra={
                    "event_id": event.id,
                    "event_type": event.type,
                },
            )

            return event

        except stripe.error.SignatureVerificationError as e:
            logger.error(
                f"Webhook signature verification failed: {str(e)}",
                exc_info=True,
            )
            raise

    def construct_event(
        self,
        payload: bytes,
        sig_header: str,
    ) -> stripe.Event:
        """Construct Stripe event from webhook payload (alias for verify_webhook_signature).

        Args:
            payload: Raw request body bytes
            sig_header: Stripe-Signature header value

        Returns:
            Stripe Event object

        Raises:
            stripe.error.SignatureVerificationError: If signature is invalid
        """
        return self.verify_webhook_signature(payload, sig_header)


# Singleton instance
stripe_adapter = StripeAdapter()
