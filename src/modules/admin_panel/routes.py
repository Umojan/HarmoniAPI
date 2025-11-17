"""Admin panel web interface routes."""

import json
import uuid
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, Request, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import get_logger
from src.core.security import create_access_token, verify_password, decode_access_token
from src.core.settings import settings
from src.db.engine import get_session
from src.modules.admin.models import Admin
from src.modules.admin.service import AdminService
from src.modules.files.models import TariffFile
from src.modules.files.service import FileService
from src.modules.tariffs.models import Tariff
from src.modules.tariffs.service import TariffService

logger = get_logger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# Helper to get current admin from cookie
async def get_admin_from_cookie(
    request: Request,
    session: AsyncSession = Depends(get_session)
) -> Admin | None:
    """Get admin from session cookie."""
    token = request.cookies.get("admin_token")
    if not token:
        return None

    try:
        # Decode token
        payload = decode_access_token(token)
        if not payload:
            return None

        admin_id_str = payload.get("sub")
        if not admin_id_str:
            return None

        # Get admin from database
        admin_service = AdminService(session)
        admin = await admin_service.get_admin_by_id(uuid.UUID(admin_id_str))
        return admin
    except Exception:
        return None


# Login Page
@router.get("/admin/login", response_class=HTMLResponse, name="admin_login_page")
async def admin_login_page(request: Request):
    """Render admin login page."""
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request}
    )


# Login Handler
@router.post("/admin/login", name="admin_login")
async def admin_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_session)
):
    """Handle admin login."""
    admin_service = AdminService(session)

    try:
        # Authenticate admin
        admin = await admin_service.get_admin_by_email(email)
        if not admin or not verify_password(password, admin.hashed_password):
            return templates.TemplateResponse(
                "admin/login.html",
                {
                    "request": request,
                    "error": "Неверный email или пароль",
                    "email": email
                }
            )

        # Create access token
        token = create_access_token(
            data={"sub": str(admin.id)},
            expires_delta=timedelta(hours=24)
        )

        # Redirect to dashboard with cookie
        response = RedirectResponse(url="/admin/dashboard", status_code=302)
        response.set_cookie(
            key="admin_token",
            value=token,
            httponly=True,
            max_age=86400,  # 24 hours
            samesite="lax"
        )

        logger.info(f"Admin logged in: {email}")
        return response

    except Exception as e:
        logger.error(f"Login error: {e}")
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": "Произошла ошибка. Пожалуйста, попробуйте снова.",
                "email": email
            }
        )


# Logout
@router.get("/admin/logout", name="admin_logout")
async def admin_logout():
    """Logout admin."""
    response = RedirectResponse(url="/admin/login", status_code=302)
    response.delete_cookie("admin_token")
    return response


# Dashboard
@router.get("/admin/dashboard", response_class=HTMLResponse, name="admin_dashboard")
async def admin_dashboard(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Render admin dashboard."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    # Get stats
    tariff_count = await session.scalar(select(func.count(Tariff.id)))
    file_count = await session.scalar(select(func.count(TariffFile.id)))
    total_size = await session.scalar(select(func.sum(TariffFile.file_size))) or 0
    admin_count = await session.scalar(select(func.count(Admin.id)))

    return templates.TemplateResponse(
        "admin/dashboard.html",
        {
            "request": request,
            "current_admin": current_admin,
            "active_page": "dashboard",
            "stats": {
                "total_tariffs": tariff_count or 0,
                "total_files": file_count or 0,
                "total_file_size": total_size,
                "total_admins": admin_count or 0
            }
        }
    )


# Tariffs List
@router.get("/admin/tariffs", response_class=HTMLResponse, name="admin_tariffs")
async def admin_tariffs(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Render tariffs list page."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    # Get all tariffs with file count
    stmt = select(
        Tariff,
        func.count(TariffFile.id).label("file_count")
    ).outerjoin(
        TariffFile, Tariff.id == TariffFile.tariff_id
    ).group_by(Tariff.id).order_by(Tariff.created_at.desc())

    result = await session.execute(stmt)
    tariffs_data = result.all()

    tariffs = []
    for tariff, file_count in tariffs_data:
        tariff_dict = {
            "id": tariff.id,
            "name": tariff.name,
            "description": tariff.description,
            "calories": tariff.calories,
            "base_price": tariff.base_price,
            "created_at": tariff.created_at,
            "file_count": file_count
        }
        tariffs.append(type('Tariff', (), tariff_dict)())

    return templates.TemplateResponse(
        "admin/tariffs.html",
        {
            "request": request,
            "current_admin": current_admin,
            "active_page": "tariffs",
            "tariffs": tariffs
        }
    )


# Create Tariff Page
@router.get("/admin/tariffs/create", response_class=HTMLResponse, name="admin_create_tariff")
async def admin_create_tariff_page(
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Render create tariff page."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    return templates.TemplateResponse(
        "admin/tariff_form.html",
        {
            "request": request,
            "current_admin": current_admin,
            "active_page": "tariffs",
            "tariff": None
        }
    )


# Create Tariff Handler
@router.post("/admin/tariffs/create", name="admin_create_tariff")
async def admin_create_tariff(
    request: Request,
    name: str = Form(...),
    description: str = Form(None),
    calories: int = Form(None),
    base_price: int = Form(...),
    features: list[str] = Form([]),
    session: AsyncSession = Depends(get_session)
):
    """Handle tariff creation."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    tariff_service = TariffService(session)

    try:
        await tariff_service.create_tariff(
            name=name,
            description=description or None,
            calories=calories if calories else None,
            features=features if features else None,
            base_price=base_price
        )
        await session.commit()

        logger.info(f"Admin {current_admin.email} created tariff: {name}")
        return RedirectResponse(url="/admin/tariffs", status_code=302)

    except Exception as e:
        await session.rollback()
        logger.error(f"Error creating tariff: {e}")
        return templates.TemplateResponse(
            "admin/tariff_form.html",
            {
                "request": request,
                "current_admin": current_admin,
                "active_page": "tariffs",
                "tariff": None,
                "error": str(e)
            }
        )


# Edit Tariff Page
@router.get("/admin/tariffs/{tariff_id}/edit", response_class=HTMLResponse, name="admin_edit_tariff")
async def admin_edit_tariff_page(
    request: Request,
    tariff_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """Render edit tariff page."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    tariff_service = TariffService(session)
    tariff = await tariff_service.get_tariff_by_id(tariff_id)

    if not tariff:
        return RedirectResponse(url="/admin/tariffs", status_code=302)

    # Parse features from JSON
    features = json.loads(tariff.features) if tariff.features else []

    tariff_obj = type('Tariff', (), {
        "id": tariff.id,
        "name": tariff.name,
        "description": tariff.description,
        "calories": tariff.calories,
        "base_price": tariff.base_price,
        "features": features
    })()

    return templates.TemplateResponse(
        "admin/tariff_form.html",
        {
            "request": request,
            "current_admin": current_admin,
            "active_page": "tariffs",
            "tariff": tariff_obj
        }
    )


# Edit Tariff Handler
@router.post("/admin/tariffs/{tariff_id}/edit", name="admin_edit_tariff")
async def admin_edit_tariff(
    request: Request,
    tariff_id: uuid.UUID,
    name: str = Form(...),
    description: str = Form(None),
    calories: int = Form(None),
    base_price: int = Form(...),
    features: list[str] = Form([]),
    session: AsyncSession = Depends(get_session)
):
    """Handle tariff update."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    tariff_service = TariffService(session)

    try:
        await tariff_service.update_tariff(
            tariff_id=tariff_id,
            name=name,
            description=description or None,
            calories=calories if calories else None,
            features=features if features else None,
            base_price=base_price
        )
        await session.commit()

        logger.info(f"Admin {current_admin.email} updated tariff: {tariff_id}")
        return RedirectResponse(url="/admin/tariffs", status_code=302)

    except Exception as e:
        await session.rollback()
        logger.error(f"Error updating tariff: {e}")
        return RedirectResponse(url="/admin/tariffs", status_code=302)


# Delete Tariff
@router.post("/admin/tariffs/{tariff_id}/delete", name="admin_delete_tariff")
async def admin_delete_tariff(
    tariff_id: uuid.UUID,
    request: Request,
    session: AsyncSession = Depends(get_session)
):
    """Delete tariff."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    tariff_service = TariffService(session)

    try:
        await tariff_service.delete_tariff(tariff_id)
        await session.commit()
        logger.info(f"Admin {current_admin.email} deleted tariff: {tariff_id}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting tariff: {e}")

    return RedirectResponse(url="/admin/tariffs", status_code=302)


# Tariff Files Page
@router.get("/admin/tariffs/{tariff_id}/files", response_class=HTMLResponse, name="admin_tariff_files")
async def admin_tariff_files(
    request: Request,
    tariff_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """Render tariff files page."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    tariff_service = TariffService(session)
    file_service = FileService(session)

    tariff = await tariff_service.get_tariff_by_id(tariff_id)
    if not tariff:
        return RedirectResponse(url="/admin/tariffs", status_code=302)

    files = await file_service.get_files_by_tariff(tariff_id)

    return templates.TemplateResponse(
        "admin/tariff_files.html",
        {
            "request": request,
            "current_admin": current_admin,
            "active_page": "tariffs",
            "tariff": tariff,
            "files": files
        }
    )


# Upload File
@router.post("/admin/tariffs/{tariff_id}/files/upload", name="admin_upload_file")
async def admin_upload_file(
    request: Request,
    tariff_id: uuid.UUID,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session)
):
    """Handle file upload."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    file_service = FileService(session)

    try:
        await file_service.upload_file(tariff_id, file)
        await session.commit()
        logger.info(f"Admin {current_admin.email} uploaded file to tariff {tariff_id}")
    except Exception as e:
        await session.rollback()
        logger.error(f"Error uploading file: {e}")

    return RedirectResponse(url=f"/admin/tariffs/{tariff_id}/files", status_code=302)


# Delete File
@router.post("/admin/files/{file_id}/delete", name="admin_delete_file")
async def admin_delete_file(
    request: Request,
    file_id: uuid.UUID,
    session: AsyncSession = Depends(get_session)
):
    """Delete file."""
    current_admin = await get_admin_from_cookie(request, session)
    if not current_admin:
        return RedirectResponse(url="/admin/login", status_code=302)

    file_service = FileService(session)

    try:
        # Get tariff_id before deletion
        file_record = await file_service.get_file_by_id(file_id)
        tariff_id = file_record.tariff_id if file_record else None

        await file_service.delete_file(file_id)
        await session.commit()
        logger.info(f"Admin {current_admin.email} deleted file: {file_id}")

        if tariff_id:
            return RedirectResponse(url=f"/admin/tariffs/{tariff_id}/files", status_code=302)
    except Exception as e:
        await session.rollback()
        logger.error(f"Error deleting file: {e}")

    return RedirectResponse(url="/admin/tariffs", status_code=302)
