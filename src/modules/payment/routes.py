"""Payment and Stripe webhook routes."""

import uuid
from pathlib import Path

import stripe
from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.settings import settings
from src.db.engine import get_session
from src.modules.payment.exceptions import StripeWebhookException
from src.modules.payment.schemas import (
    CreatePaymentIntentRequest,
    PaymentIntentResponse,
    PaymentStatusResponse,
)
from src.modules.payment.service import PaymentService
from src.services.stripe.adapter import stripe_adapter

logger = get_logger(__name__)

router = APIRouter()
html_router = APIRouter()  # Separate router for HTML pages

# Setup Jinja2 templates
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


@router.post(
    "/stripe/payment-intent",
    response_model=PaymentIntentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_payment_intent(
    request_data: CreatePaymentIntentRequest,
    session: AsyncSession = Depends(get_session),
) -> PaymentIntentResponse:
    """Create Stripe PaymentIntent for tariff purchase.

    User must have verified email before creating payment.

    Args:
        request_data: Email and tariff ID
        session: Database session

    Returns:
        PaymentIntent response with client_secret

    Raises:
        UserNotVerifiedException: If email not verified (400)
        TariffNotFoundException: If tariff not found (404)
    """
    payment_service = PaymentService(session)

    payment, client_secret = await payment_service.create_payment_intent(
        email=request_data.email,
        tariff_id=request_data.tariff_id,
    )

    await session.commit()

    return PaymentIntentResponse(
        payment_id=payment.id,
        client_secret=client_secret,
        amount=payment.amount,
        currency=payment.currency,
        status=payment.status,
    )


@router.post(
    "/stripe/webhook",
    status_code=status.HTTP_200_OK,
)
async def stripe_webhook(
    request: Request,
    session: AsyncSession = Depends(get_session),
    stripe_signature: str = Header(..., alias="Stripe-Signature"),
) -> dict[str, str]:
    """Handle Stripe webhook events with signature verification.

    Processes payment_intent.succeeded, payment_intent.payment_failed,
    and other PaymentIntent lifecycle events.

    Args:
        request: FastAPI request with raw body
        session: Database session
        stripe_signature: Stripe signature header

    Returns:
        Success acknowledgment

    Raises:
        StripeWebhookException: If signature verification fails (400)
    """
    # Get raw body for signature verification
    payload = await request.body()

    # Verify webhook signature
    try:
        event = stripe_adapter.verify_webhook_signature(
            payload=payload,
            sig_header=stripe_signature,
        )
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Webhook signature verification failed: {str(e)}")
        raise StripeWebhookException(
            reason="Invalid signature",
            event_id=None,
        )

    # Handle event (Stripe guarantees idempotency via event.id)
    payment_service = PaymentService(session)
    event_type = event.type

    logger.info(
        f"Processing webhook event: {event_type}",
        extra={
            "event_id": event.id,
            "event_type": event_type,
        },
    )

    # Process PaymentIntent events
    if event_type.startswith("payment_intent."):
        payment_intent_data = event.data.object

        await payment_service.handle_webhook_event(
            event_type=event_type,
            payment_intent_data=payment_intent_data,
        )

        await session.commit()

        logger.info(
            f"Webhook event processed successfully: {event_type}",
            extra={"event_id": event.id},
        )
    else:
        logger.info(f"Unhandled webhook event type: {event_type}")

    return {"status": "success"}


@router.get(
    "/stripe/payment/{payment_id}/status",
    response_model=PaymentStatusResponse,
    status_code=status.HTTP_200_OK,
)
async def get_payment_status(
    payment_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> PaymentStatusResponse:
    """Get payment status by ID.

    Args:
        payment_id: Payment UUID
        session: Database session

    Returns:
        Payment details

    Raises:
        PaymentNotFoundException: If payment not found (404)
    """
    payment_service = PaymentService(session)
    payment = await payment_service.get_payment_status(payment_id)

    return PaymentStatusResponse.model_validate(payment)


# ============================================================================
# HTML Page Routes
# ============================================================================


@html_router.get("/payment/checkout", response_class=HTMLResponse)
async def checkout_page(
    request: Request,
    tariff_id: str | None = None,
) -> HTMLResponse:
    """Render checkout page.

    Args:
        request: FastAPI request
        tariff_id: Optional tariff ID from query params

    Returns:
        Rendered checkout.html
    """
    return templates.TemplateResponse(
        "checkout.html",
        {
            "request": request,
            "stripe_public_key": settings.stripe_public_key,
            "tariff_id": tariff_id or "",
        },
    )


@html_router.get("/payment/success", response_class=HTMLResponse)
async def success_page(
    request: Request,
    email: str | None = None,
) -> HTMLResponse:
    """Render payment success page.

    Args:
        request: FastAPI request
        email: User email (optional, from query params)

    Returns:
        Rendered success.html
    """
    return templates.TemplateResponse(
        "success.html",
        {
            "request": request,
            "email": email or "your email",
        },
    )


@html_router.get("/payment/error", response_class=HTMLResponse)
async def error_page(
    request: Request,
    reason: str | None = None,
    tariff_id: str | None = None,
) -> HTMLResponse:
    """Render payment error page.

    Args:
        request: FastAPI request
        reason: Error reason (optional)
        tariff_id: Tariff ID to retry payment (optional)

    Returns:
        Rendered error.html
    """
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "reason": reason,
            "tariff_id": tariff_id,
        },
    )
