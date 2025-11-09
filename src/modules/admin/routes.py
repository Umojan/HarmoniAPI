"""Admin authentication and CRUD routes."""

import uuid

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_admin
from src.core.logging import get_logger
from src.db.engine import get_session
from src.modules.admin.models import Admin
from src.modules.admin.schemas import (
    AdminResponse,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UpdateAdminRequest,
)
from src.modules.admin.service import AdminService

logger = get_logger(__name__)

router = APIRouter()


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Admin login endpoint (OAuth2 password flow).

    Args:
        form_data: OAuth2 password form (username=email, password)
        session: Database session

    Returns:
        Access token response

    Raises:
        InvalidCredentialsException: If credentials are invalid (401)
    """
    admin_service = AdminService(session)
    access_token = await admin_service.authenticate(
        email=form_data.username,  # OAuth2 uses 'username' field
        password=form_data.password,
    )

    return TokenResponse(access_token=access_token)


@router.post("/login/json", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login_json(
    login_data: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenResponse:
    """Admin login endpoint (JSON body alternative).

    Args:
        login_data: Login credentials
        session: Database session

    Returns:
        Access token response

    Raises:
        InvalidCredentialsException: If credentials are invalid (401)
    """
    admin_service = AdminService(session)
    access_token = await admin_service.authenticate(
        email=login_data.email,
        password=login_data.password,
    )

    return TokenResponse(access_token=access_token)


@router.post(
    "/register",
    response_model=AdminResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def register_admin(
    register_data: RegisterRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> AdminResponse:
    """Register a new admin (admin-only endpoint).

    Args:
        register_data: New admin details
        session: Database session
        current_admin: Current authenticated admin (dependency)

    Returns:
        Created admin response

    Raises:
        AdminAlreadyExistsException: If email already exists (400)
        NotAuthenticatedException: If no token provided (401)
        InvalidTokenException: If token is invalid (401)
    """
    admin_service = AdminService(session)
    new_admin = await admin_service.create_admin(
        email=register_data.email,
        password=register_data.password,
        first_name=register_data.first_name,
        last_name=register_data.last_name,
    )

    logger.info(f"Admin {current_admin.email} created new admin: {new_admin.email}")
    return AdminResponse.model_validate(new_admin)


@router.get(
    "/admins",
    response_model=list[AdminResponse],
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def get_all_admins(
    session: AsyncSession = Depends(get_session),
) -> list[AdminResponse]:
    """Get all admins (admin-only endpoint).

    Args:
        session: Database session

    Returns:
        List of all admins
    """
    admin_service = AdminService(session)
    admins = await admin_service.get_all_admins()
    return [AdminResponse.model_validate(admin) for admin in admins]


@router.get(
    "/admins/{admin_id}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def get_admin_by_id(
    admin_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> AdminResponse:
    """Get admin by ID (admin-only endpoint).

    Args:
        admin_id: Admin UUID
        session: Database session

    Returns:
        Admin details

    Raises:
        AdminNotFoundException: If admin not found (401)
    """
    admin_service = AdminService(session)
    admin = await admin_service.get_admin_by_id(admin_id)
    if not admin:
        from src.modules.admin.exceptions import AdminNotFoundException
        raise AdminNotFoundException(str(admin_id))
    return AdminResponse.model_validate(admin)


@router.get(
    "/admins/email/{email}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def get_admin_by_email(
    email: str,
    session: AsyncSession = Depends(get_session),
) -> AdminResponse:
    """Get admin by email (admin-only endpoint).

    Args:
        email: Admin email
        session: Database session

    Returns:
        Admin details

    Raises:
        AdminNotFoundException: If admin not found (401)
    """
    admin_service = AdminService(session)
    admin = await admin_service.get_admin_by_email(email)
    if not admin:
        from src.modules.admin.exceptions import AdminNotFoundException
        raise AdminNotFoundException(email)
    return AdminResponse.model_validate(admin)


@router.patch(
    "/admins/{admin_id}",
    response_model=AdminResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def update_admin(
    admin_id: uuid.UUID,
    update_data: UpdateAdminRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> AdminResponse:
    """Update admin by ID (admin-only endpoint).

    Args:
        admin_id: Admin UUID to update
        update_data: Fields to update
        session: Database session
        current_admin: Current authenticated admin

    Returns:
        Updated admin details

    Raises:
        AdminNotFoundException: If admin not found (401)
        AdminAlreadyExistsException: If new email already exists (400)
    """
    admin_service = AdminService(session)
    updated_admin = await admin_service.update_admin(
        admin_id=admin_id,
        email=update_data.email,
        password=update_data.password,
        first_name=update_data.first_name,
        last_name=update_data.last_name,
    )

    logger.info(f"Admin {current_admin.email} updated admin: {updated_admin.email}")
    return AdminResponse.model_validate(updated_admin)


@router.delete(
    "/admins/{admin_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_admin(
    admin_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> None:
    """Delete admin by ID (admin-only endpoint).

    Args:
        admin_id: Admin UUID to delete
        session: Database session
        current_admin: Current authenticated admin

    Raises:
        AdminNotFoundException: If admin not found (401)
    """
    admin_service = AdminService(session)
    await admin_service.delete_admin(admin_id)
    logger.info(f"Admin {current_admin.email} deleted admin: {admin_id}")
