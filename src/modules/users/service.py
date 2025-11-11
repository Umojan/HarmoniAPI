"""User business logic and service layer."""

import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.modules.users.exceptions import (
    UserAlreadyExistsException,
    UserNotFoundException,
)
from src.modules.users.models import User

logger = get_logger(__name__)


class UserService:
    """Service for user CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize user service.

        Args:
            session: Async database session
        """
        self.session = session

    async def create_user(
        self,
        name: str,
        surname: str,
        email: str,
        is_verified: bool = False,
    ) -> User:
        """Create a new user.

        Args:
            name: User's first name
            surname: User's last name
            email: Email address
            is_verified: Verification status (default False)

        Returns:
            Created user instance

        Raises:
            UserAlreadyExistsException: If email already exists
        """
        user = User(
            name=name,
            surname=surname,
            email=email,
            is_verified=is_verified,
        )

        try:
            self.session.add(user)
            await self.session.flush()
            logger.info(f"User created: {email} (verified={is_verified})")
            return user
        except IntegrityError:
            raise UserAlreadyExistsException(email)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email address.

        Args:
            email: Email address to search for

        Returns:
            User instance or None if not found
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: uuid.UUID) -> User | None:
        """Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User instance or None if not found
        """
        stmt = select(User).where(User.id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def verify_user(self, email: str) -> User:
        """Mark user as verified.

        Args:
            email: Email address to verify

        Returns:
            Verified user instance

        Raises:
            UserNotFoundException: If user not found
        """
        user = await self.get_user_by_email(email)
        if not user:
            raise UserNotFoundException(email)

        user.is_verified = True
        await self.session.flush()
        logger.info(f"User verified: {email}")
        return user

    async def update_user(
        self,
        user_id: uuid.UUID,
        name: str | None = None,
        surname: str | None = None,
        email: str | None = None,
    ) -> User:
        """Update user fields.

        Args:
            user_id: User UUID to update
            name: New name (optional)
            surname: New surname (optional)
            email: New email (optional)

        Returns:
            Updated user instance

        Raises:
            UserNotFoundException: If user not found
            UserAlreadyExistsException: If new email already exists
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))

        # Check email uniqueness if changing
        if email and email != user.email:
            # TODO: When email is changed, user should go through verification process again
            # Set is_verified=False and send new verification code via AuthService
            existing = await self.get_user_by_email(email)
            if existing:
                raise UserAlreadyExistsException(email)
            user.email = email

        # Update fields if provided
        if name is not None:
            user.name = name
        if surname is not None:
            user.surname = surname

        try:
            await self.session.flush()
            logger.info(f"User updated: {user.email} ({user_id})")
            return user
        except IntegrityError:
            await self.session.rollback()
            raise UserAlreadyExistsException(email or user.email)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        """Delete user by ID.

        Args:
            user_id: User UUID to delete

        Raises:
            UserNotFoundException: If user not found
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise UserNotFoundException(str(user_id))

        await self.session.delete(user)
        await self.session.flush()

        logger.info(f"User deleted: {user.email} ({user_id})")
