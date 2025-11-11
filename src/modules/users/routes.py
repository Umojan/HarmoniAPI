"""User management routes."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_admin
from src.core.logging import get_logger
from src.db.engine import get_session
from src.modules.admin.models import Admin
from src.modules.users.schemas import UserResponse, UserUpdateRequest
from src.modules.users.service import UserService

logger = get_logger(__name__)

router = APIRouter()


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def get_user_by_id(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> UserResponse:
    """Get user by ID (admin-only).

    Args:
        user_id: User UUID
        session: Database session
        current_admin: Current authenticated admin

    Returns:
        User details

    Raises:
        UserNotFoundException: If user not found (404)
    """
    user_service = UserService(session)
    user = await user_service.get_user_by_id(user_id)

    if not user:
        from src.modules.users.exceptions import UserNotFoundException

        raise UserNotFoundException(str(user_id))

    return UserResponse.model_validate(user)


@router.get(
    "/users/email/{email}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def get_user_by_email(
    email: str,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> UserResponse:
    """Get user by email (admin-only).

    Args:
        email: User email address
        session: Database session
        current_admin: Current authenticated admin

    Returns:
        User details

    Raises:
        UserNotFoundException: If user not found (404)
    """
    user_service = UserService(session)
    user = await user_service.get_user_by_email(email)

    if not user:
        from src.modules.users.exceptions import UserNotFoundException

        raise UserNotFoundException(email)

    return UserResponse.model_validate(user)


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def update_user(
    user_id: uuid.UUID,
    update_data: UserUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> UserResponse:
    """Update user by ID (admin-only).

    Args:
        user_id: User UUID to update
        update_data: Fields to update
        session: Database session
        current_admin: Current authenticated admin

    Returns:
        Updated user

    Raises:
        UserNotFoundException: If user not found (404)
        UserAlreadyExistsException: If new email already exists (400)
    """
    user_service = UserService(session)
    updated_user = await user_service.update_user(
        user_id=user_id,
        name=update_data.name,
        surname=update_data.surname,
        email=update_data.email,
    )

    await session.commit()

    logger.info(
        f"Admin {current_admin.email} updated user: {updated_user.email} ({user_id})"
    )

    return UserResponse.model_validate(updated_user)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> None:
    """Delete user by ID (admin-only).

    Args:
        user_id: User UUID to delete
        session: Database session
        current_admin: Current authenticated admin

    Raises:
        UserNotFoundException: If user not found (404)
    """
    user_service = UserService(session)
    await user_service.delete_user(user_id)

    await session.commit()

    logger.info(f"Admin {current_admin.email} deleted user: {user_id}")
