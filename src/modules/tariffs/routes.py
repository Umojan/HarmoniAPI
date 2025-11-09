"""Tariff management routes."""

import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_admin
from src.core.logging import get_logger
from src.db.engine import get_session
from src.modules.admin.models import Admin
from src.modules.tariffs.schemas import (
    TariffCreateRequest,
    TariffResponse,
    TariffUpdateRequest,
)
from src.modules.tariffs.service import TariffService

logger = get_logger(__name__)

router = APIRouter()


@router.post(
    "/tariffs",
    response_model=TariffResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_admin)],
)
async def create_tariff(
    tariff_data: TariffCreateRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> TariffResponse:
    """Create new tariff (admin-only).

    Args:
        tariff_data: Tariff creation data
        session: Database session
        current_admin: Current authenticated admin

    Returns:
        Created tariff

    Raises:
        TariffAlreadyExistsException: If name already exists (400)
    """
    tariff_service = TariffService(session)
    tariff = await tariff_service.create_tariff(
        name=tariff_data.name,
        description=tariff_data.description,
        calories=tariff_data.calories,
        features=tariff_data.features,
        base_price=tariff_data.base_price,
    )

    logger.info(f"Admin {current_admin.email} created tariff: {tariff.name}")

    # Convert features from JSON string back to list for response
    import json
    response_data = {
        "id": tariff.id,
        "name": tariff.name,
        "description": tariff.description,
        "calories": tariff.calories,
        "features": json.loads(tariff.features) if tariff.features else None,
        "base_price": tariff.base_price,
        "created_at": tariff.created_at,
        "updated_at": tariff.updated_at,
    }

    return TariffResponse(**response_data)


@router.get(
    "/tariffs",
    response_model=list[TariffResponse],
    status_code=status.HTTP_200_OK,
)
async def get_all_tariffs(
    session: AsyncSession = Depends(get_session),
) -> list[TariffResponse]:
    """Get all tariffs.

    Args:
        session: Database session

    Returns:
        List of all tariffs
    """
    tariff_service = TariffService(session)
    tariffs = await tariff_service.get_all_tariffs()

    # Convert features from JSON strings back to lists
    import json
    responses = []
    for tariff in tariffs:
        response_data = {
            "id": tariff.id,
            "name": tariff.name,
            "description": tariff.description,
            "calories": tariff.calories,
            "features": json.loads(tariff.features) if tariff.features else None,
            "base_price": tariff.base_price,
            "created_at": tariff.created_at,
            "updated_at": tariff.updated_at,
        }
        responses.append(TariffResponse(**response_data))

    return responses


@router.get(
    "/tariffs/{tariff_id}",
    response_model=TariffResponse,
    status_code=status.HTTP_200_OK,
)
async def get_tariff_by_id(
    tariff_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> TariffResponse:
    """Get tariff by ID.

    Args:
        tariff_id: Tariff UUID
        session: Database session

    Returns:
        Tariff details

    Raises:
        TariffNotFoundException: If tariff not found (404)
    """
    tariff_service = TariffService(session)
    tariff = await tariff_service.get_tariff_by_id(tariff_id)

    if not tariff:
        from src.modules.tariffs.exceptions import TariffNotFoundException
        raise TariffNotFoundException(str(tariff_id))

    import json
    response_data = {
        "id": tariff.id,
        "name": tariff.name,
        "description": tariff.description,
        "calories": tariff.calories,
        "features": json.loads(tariff.features) if tariff.features else None,
        "base_price": tariff.base_price,
        "created_at": tariff.created_at,
        "updated_at": tariff.updated_at,
    }

    return TariffResponse(**response_data)


@router.patch(
    "/tariffs/{tariff_id}",
    response_model=TariffResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_current_admin)],
)
async def update_tariff(
    tariff_id: uuid.UUID,
    update_data: TariffUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> TariffResponse:
    """Update tariff by ID (admin-only).

    Args:
        tariff_id: Tariff UUID to update
        update_data: Fields to update
        session: Database session
        current_admin: Current authenticated admin

    Returns:
        Updated tariff

    Raises:
        TariffNotFoundException: If tariff not found (404)
        TariffAlreadyExistsException: If new name already exists (400)
    """
    tariff_service = TariffService(session)
    updated_tariff = await tariff_service.update_tariff(
        tariff_id=tariff_id,
        name=update_data.name,
        description=update_data.description,
        calories=update_data.calories,
        features=update_data.features,
        base_price=update_data.base_price,
    )

    logger.info(
        f"Admin {current_admin.email} updated tariff: {updated_tariff.name}"
    )

    import json
    response_data = {
        "id": updated_tariff.id,
        "name": updated_tariff.name,
        "description": updated_tariff.description,
        "calories": updated_tariff.calories,
        "features": json.loads(updated_tariff.features) if updated_tariff.features else None,
        "base_price": updated_tariff.base_price,
        "created_at": updated_tariff.created_at,
        "updated_at": updated_tariff.updated_at,
    }

    return TariffResponse(**response_data)


@router.delete(
    "/tariffs/{tariff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(get_current_admin)],
)
async def delete_tariff(
    tariff_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
    current_admin: Admin = Depends(get_current_admin),
) -> None:
    """Delete tariff by ID (admin-only).

    Args:
        tariff_id: Tariff UUID to delete
        session: Database session
        current_admin: Current authenticated admin

    Raises:
        TariffNotFoundException: If tariff not found (404)
    """
    tariff_service = TariffService(session)
    await tariff_service.delete_tariff(tariff_id)

    logger.info(f"Admin {current_admin.email} deleted tariff: {tariff_id}")
