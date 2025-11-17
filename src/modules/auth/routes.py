"""Auth routes for email verification."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.db.engine import get_session
from src.modules.auth.schemas import (
    CheckEmailResponse,
    ContactFormRequest,
    ContactFormResponse,
    SendVerificationCodeRequest,
    VerificationResponse,
    VerifyCodeRequest,
)
from src.modules.auth.service import AuthService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/send-verification-code",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def send_verification_code(
    request_data: SendVerificationCodeRequest,
    session: AsyncSession = Depends(get_session),
) -> VerificationResponse:
    """Send verification code to email address.

    Args:
        request_data: User details and email
        session: Database session

    Returns:
        Verification response with message

    Raises:
        RateLimitExceededException: If rate limit exceeded (429)
        EmailServiceException: If email service fails (503)
    """
    auth_service = AuthService(session)

    await auth_service.send_verification_code(
        name=request_data.name,
        surname=request_data.surname,
        email=request_data.email,
    )

    await session.commit()

    return VerificationResponse(
        message="Verification code sent successfully",
        email=request_data.email,
        verified=False,
    )


@router.post(
    "/verify-code",
    response_model=VerificationResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_code(
    request_data: VerifyCodeRequest,
    session: AsyncSession = Depends(get_session),
) -> VerificationResponse:
    """Verify code and mark user as verified.

    Args:
        request_data: Verification code
        session: Database session

    Returns:
        Verification response confirming verification

    Raises:
        CodeExpiredException: If code has expired (400)
        CodeInvalidException: If code doesn't match (400)
        MaxAttemptsExceededException: If too many attempts (400)
    """
    auth_service = AuthService(session)

    user = await auth_service.verify_code(code=request_data.code)

    await session.commit()

    return VerificationResponse(
        message="Email verified successfully",
        email=user.email,
        verified=True,
    )


@router.get(
    "/check-email/{email}",
    response_model=CheckEmailResponse,
    status_code=status.HTTP_200_OK,
)
async def check_email(
    email: str,
    session: AsyncSession = Depends(get_session),
) -> CheckEmailResponse:
    """Check if email is already verified.

    Frontend uses this to determine if user needs verification or can proceed directly to payment.

    Args:
        email: Email address to check
        session: Database session

    Returns:
        CheckEmailResponse with is_verified flag
    """
    from src.modules.users.service import UserService

    user_service = UserService(session)
    user = await user_service.get_user_by_email(email)

    return CheckEmailResponse(
        email=email,
        is_verified=user is not None and user.is_verified,
    )


@router.post(
    "/contact-form",
    response_model=ContactFormResponse,
    status_code=status.HTTP_200_OK,
)
async def submit_contact_form(
    request_data: ContactFormRequest,
) -> ContactFormResponse:
    """Submit contact form for individual consultation request.

    Sends email notification to owner with client details.

    Args:
        request_data: Contact form data (name, email, phone, telegram, comment)

    Returns:
        ContactFormResponse confirming submission

    Raises:
        EmailServiceException: If email service fails (503)
    """
    from src.modules.auth.exceptions import EmailServiceException
    from src.services.resend.adapter import resend_adapter

    try:
        await resend_adapter.send_contact_form(
            name=request_data.name,
            email=request_data.email,
            phone=request_data.phone,
            telegram=request_data.telegram,
            comment=request_data.comment,
        )

        logger.info(
            f"Contact form submitted: {request_data.email}",
            extra={"client_name": request_data.name},
        )

        return ContactFormResponse(
            message="Ваша заявка успешно отправлена. Мы свяжемся с вами в ближайшее время!",
            email=request_data.email,
        )

    except Exception as e:
        logger.error(f"Failed to process contact form: {str(e)}", exc_info=True)
        raise EmailServiceException(reason=str(e))
