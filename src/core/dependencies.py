"""FastAPI dependencies for authentication and authorization."""

import uuid

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.security import decode_access_token
from src.db.engine import get_session
from src.modules.admin.exceptions import (
    AdminNotFoundException,
    InvalidTokenException,
    NotAuthenticatedException,
)
from src.modules.admin.models import Admin
from src.modules.admin.service import AdminService

logger = get_logger(__name__)

# OAuth2 scheme for Swagger UI (displays "Authorize" button)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_admin(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
) -> Admin:
    """Dependency to get current authenticated admin.

    Extracts JWT from Authorization header, validates it, and returns admin.

    Args:
        token: JWT token from OAuth2 scheme
        session: Database session

    Returns:
        Authenticated admin instance

    Raises:
        NotAuthenticatedException: If no token provided
        InvalidTokenException: If token is invalid or expired
        AdminNotFoundException: If admin not found in database
    """
    if not token:
        raise NotAuthenticatedException()

    # Decode JWT token
    payload = decode_access_token(token)
    if not payload:
        logger.warning("Invalid or expired token")
        raise InvalidTokenException()

    # Extract admin ID from token subject
    admin_id_str = payload.get("sub")
    if not admin_id_str:
        logger.warning("Token missing 'sub' claim")
        raise InvalidTokenException()

    try:
        admin_id = uuid.UUID(admin_id_str)
    except ValueError:
        logger.warning(f"Invalid admin ID format in token: {admin_id_str}")
        raise InvalidTokenException()

    # Fetch admin from database
    admin_service = AdminService(session)
    admin = await admin_service.get_admin_by_id(admin_id)

    if not admin:
        logger.warning(f"Admin not found for ID: {admin_id}")
        raise AdminNotFoundException(str(admin_id))

    return admin
