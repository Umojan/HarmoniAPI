"""Auth business logic and service layer."""

import random
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.settings import settings
from src.modules.auth.exceptions import (
    CodeExpiredException,
    CodeInvalidException,
    EmailAlreadyVerifiedException,
    MaxAttemptsExceededException,
    RateLimitExceededException,
)
from src.modules.auth.models import EmailVerification
from src.modules.users.models import User
from src.services.resend.adapter import resend_adapter

logger = get_logger(__name__)


class AuthService:
    """Service for email verification and user registration operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize auth service.

        Args:
            session: Async database session
        """
        self.session = session

    def generate_verification_code(self) -> str:
        """Generate random 6-digit verification code.

        Returns:
            6-digit numeric code as string
        """
        code_length = settings.verification_code_length
        code = "".join([str(random.randint(0, 9)) for _ in range(code_length)])
        return code

    async def send_verification_code(
        self,
        name: str,
        surname: str,
        email: str,
    ) -> None:
        """Send verification code to email address.

        Creates unverified user and sends code. For repeat purchases, use check_user_verified() first.

        Args:
            name: User's first name
            surname: User's last name
            email: Email address to verify

        Raises:
            EmailAlreadyVerifiedException: If user already verified
            RateLimitExceededException: If rate limit exceeded
        """
        from src.modules.users.service import UserService

        user_service = UserService(self.session)

        # Check if user already exists
        existing_user = await user_service.get_user_by_email(email)

        if existing_user and existing_user.is_verified:
            raise EmailAlreadyVerifiedException(email)

        # Check rate limit - find most recent verification request
        stmt = (
            select(EmailVerification)
            .where(EmailVerification.email == email)
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        last_verification = result.scalar_one_or_none()

        if last_verification:
            time_since_last = datetime.now(timezone.utc) - last_verification.created_at
            rate_limit_seconds = settings.verification_rate_limit_seconds

            if time_since_last.total_seconds() < rate_limit_seconds:
                retry_after = rate_limit_seconds - int(time_since_last.total_seconds())
                logger.warning(
                    f"Rate limit exceeded for email: {email}",
                    extra={"retry_after": retry_after},
                )
                raise RateLimitExceededException(retry_after)

        # Create unverified user if doesn't exist
        if not existing_user:
            await user_service.create_user(
                name=name,
                surname=surname,
                email=email,
                is_verified=False,
            )

        # Generate new code
        code = self.generate_verification_code()
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.verification_code_ttl_minutes
        )

        # Create verification record
        verification = EmailVerification(
            email=email,
            code=code,
            expires_at=expires_at,
            attempts=0,
        )

        self.session.add(verification)
        await self.session.flush()

        # Send email via Resend
        try:
            await resend_adapter.send_verification_code(
                to_email=email,
                name=name,
                code=code,
            )
            logger.info(
                f"Verification code sent to {email}",
                extra={"verification_id": str(verification.id)},
            )
        except Exception as e:
            # Rollback verification record if email fails
            await self.session.rollback()
            logger.error(f"Failed to send verification email: {str(e)}")
            raise

    async def verify_code(self, code: str) -> User:
        """Verify code and mark user as verified.

        Args:
            code: 6-digit verification code

        Returns:
            Verified User instance

        Raises:
            CodeExpiredException: If code has expired
            CodeInvalidException: If code doesn't match or not found
            MaxAttemptsExceededException: If too many attempts
        """
        from src.modules.users.service import UserService

        user_service = UserService(self.session)

        # Find most recent unverified code matching this code
        stmt = (
            select(EmailVerification)
            .where(
                EmailVerification.code == code,
                EmailVerification.verified_at.is_(None),
            )
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        verification = result.scalar_one_or_none()

        if not verification:
            raise CodeInvalidException()

        # Check expiration
        if datetime.now(timezone.utc) > verification.expires_at:
            logger.warning(f"Expired verification code: {code}")
            raise CodeExpiredException()

        # Check max attempts
        if verification.attempts >= settings.verification_max_attempts:
            logger.warning(f"Max attempts exceeded for code: {code}")
            raise MaxAttemptsExceededException()

        # Increment attempts
        verification.attempts += 1
        await self.session.flush()

        # Mark verification as completed
        verification.verified_at = datetime.now(timezone.utc)

        # Verify user via UserService
        user = await user_service.verify_user(verification.email)

        logger.info(
            f"User verified: {user.email}",
            extra={"user_id": str(user.id)},
        )

        return user

    async def cleanup_expired_verifications(self) -> int:
        """Delete expired verification records.

        Returns:
            Number of deleted records
        """
        stmt = delete(EmailVerification).where(
            EmailVerification.expires_at < datetime.now(timezone.utc),
            EmailVerification.verified_at.is_(None),
        )

        result = await self.session.execute(stmt)
        deleted_count = result.rowcount or 0

        if deleted_count > 0:
            await self.session.flush()
            logger.info(f"Cleaned up {deleted_count} expired verification records")

        return deleted_count
