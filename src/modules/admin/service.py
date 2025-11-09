"""Admin business logic and service layer."""

import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.security import (
    create_access_token,
    get_password_hash,
    verify_password,
)
from src.core.settings import settings
from src.modules.admin.exceptions import (
    AdminAlreadyExistsException,
    AdminNotFoundException,
    InvalidCredentialsException,
)
from src.modules.admin.models import Admin

logger = get_logger(__name__)


class AdminService:
    """Service for admin authentication and management operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize admin service.

        Args:
            session: Async database session
        """
        self.session = session

    async def authenticate(self, email: str, password: str) -> str:
        """Authenticate admin and return JWT token.

        Args:
            email: Admin email
            password: Plain text password

        Returns:
            JWT access token

        Raises:
            InvalidCredentialsException: If credentials are invalid
        """
        admin = await self.get_admin_by_email(email)
        if not admin or not verify_password(password, admin.hashed_password):
            logger.warning(f"Failed login attempt for email: {email}")
            raise InvalidCredentialsException()

        # Create access token with admin ID as subject
        access_token = create_access_token(
            data={"sub": str(admin.id)},
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        logger.info(f"Admin logged in: {email}")
        return access_token

    async def create_admin(
        self,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> Admin:
        """Create a new admin account.

        Args:
            email: Admin email (must be unique)
            password: Plain text password
            first_name: Optional first name
            last_name: Optional last name

        Returns:
            Created admin instance

        Raises:
            AdminAlreadyExistsException: If email already exists
        """
        # Check if admin with email already exists
        existing_admin = await self.get_admin_by_email(email)
        if existing_admin:
            raise AdminAlreadyExistsException(email)

        # Create new admin with hashed password
        admin = Admin(
            email=email,
            hashed_password=get_password_hash(password),
            first_name=first_name,
            last_name=last_name,
        )

        try:
            self.session.add(admin)
            await self.session.flush()
            logger.info(f"Admin created: {email}")
            return admin
        except IntegrityError:
            await self.session.rollback()
            raise AdminAlreadyExistsException(email)

    async def get_admin_by_id(self, admin_id: uuid.UUID) -> Admin | None:
        """Get admin by ID.

        Args:
            admin_id: Admin UUID

        Returns:
            Admin instance or None if not found
        """
        stmt = select(Admin).where(Admin.id == admin_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_admin_by_email(self, email: str) -> Admin | None:
        """Get admin by email.

        Args:
            email: Admin email

        Returns:
            Admin instance or None if not found
        """
        stmt = select(Admin).where(Admin.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def ensure_first_admin(self, email: str, password: str) -> None:
        """Ensure first admin exists, create if database is empty.

        Args:
            email: First admin email
            password: First admin password

        Raises:
            ValueError: If email or password is empty
        """
        if not email or not password:
            raise ValueError("FIRST_ADMIN_EMAIL and FIRST_ADMIN_PASSWORD must be set")

        # Check if any admins exist
        stmt = select(Admin).limit(1)
        result = await self.session.execute(stmt)
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            logger.info("Admin(s) already exist, skipping first admin creation")
            return

        # Create first admin
        await self.create_admin(email=email, password=password)
        logger.info(f"First admin created: {email}")

    async def get_all_admins(self) -> list[Admin]:
        """Get all admins.

        Returns:
            List of all admin instances
        """
        stmt = select(Admin).order_by(Admin.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update_admin(
        self,
        admin_id: uuid.UUID,
        email: str | None = None,
        password: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> Admin:
        """Update admin fields.

        Args:
            admin_id: Admin UUID to update
            email: New email (optional)
            password: New password (optional, will be hashed)
            first_name: New first name (optional)
            last_name: New last name (optional)

        Returns:
            Updated admin instance

        Raises:
            AdminNotFoundException: If admin not found
            AdminAlreadyExistsException: If new email already exists
        """
        admin = await self.get_admin_by_id(admin_id)
        if not admin:
            raise AdminNotFoundException(str(admin_id))

        # Check email uniqueness if changing
        if email and email != admin.email:
            existing = await self.get_admin_by_email(email)
            if existing:
                raise AdminAlreadyExistsException(email)
            admin.email = email

        # Update password if provided
        if password:
            admin.hashed_password = get_password_hash(password)

        # Update name fields if provided
        if first_name is not None:
            admin.first_name = first_name
        if last_name is not None:
            admin.last_name = last_name

        try:
            await self.session.flush()
            logger.info(f"Admin updated: {admin.email}")
            return admin
        except IntegrityError:
            await self.session.rollback()
            raise AdminAlreadyExistsException(email or admin.email)

    async def delete_admin(self, admin_id: uuid.UUID) -> None:
        """Delete admin by ID.

        Args:
            admin_id: Admin UUID to delete

        Raises:
            AdminNotFoundException: If admin not found
        """
        admin = await self.get_admin_by_id(admin_id)
        if not admin:
            raise AdminNotFoundException(str(admin_id))

        await self.session.delete(admin)
        await self.session.flush()
        logger.info(f"Admin deleted: {admin.email}")
