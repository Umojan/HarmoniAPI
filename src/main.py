"""FastAPI application entrypoint."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import AppException
from src.core.logging import get_logger, setup_logging
from src.core.settings import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events.

    Code before yield runs on startup.
    Code after yield runs on shutdown.
    """
    # Startup
    logger.info("Application startup: initializing resources...")

    # Ensure first admin exists
    from src.db.engine import async_session_factory
    from src.modules.admin.service import AdminService

    async with async_session_factory() as session:
        try:
            admin_service = AdminService(session)
            await admin_service.ensure_first_admin(
                email=settings.first_admin_email,
                password=settings.first_admin_password,
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Failed to ensure first admin: {e}", exc_info=True)
            raise

    yield  # Application is running and handling requests

    # Shutdown
    logger.info("Application shutdown: cleaning up resources...")
    # TODO: Close database connections, cleanup resources


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance."""

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )

    # CORS middleware - allow all origins (for development)
    # NOTE: In production, replace ["*"] with explicit frontend origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,  # Must be False when using allow_origins=["*"]
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Exception Handlers

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        """Handle custom application exceptions."""
        logger.warning(
            f"AppException: {exc.message}",
            extra={
                "status_code": exc.status_code,
                "details": exc.details,
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle ValueError as 400 Bad Request."""
        logger.warning(
            f"ValueError: {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
            },
        )
        return JSONResponse(
            status_code=400,
            content={
                "message": str(exc),
                "details": {"error_type": "validation_error"},
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions as 500 Internal Server Error."""
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
            extra={
                "path": request.url.path,
                "method": request.method,
                "error_type": type(exc).__name__,
            },
            exc_info=True,
        )
        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error",
                "details": {"error_type": "internal_error"},
            },
        )

    # Include routers
    from src.modules.admin.routes import router as admin_router

    app.include_router(admin_router, prefix="/auth", tags=["auth"])

    return app


app = create_app()


async def main() -> None:
    """Run the FastAPI application with uvicorn."""
    import uvicorn

    setup_logging(level="DEBUG" if settings.debug else "INFO")

    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database: {settings.database_url.split('@')[1] if '@' in settings.database_url else 'local'}")

    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=8123,
        log_level="debug" if settings.debug else "info",
        reload=settings.debug,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as exc:
        logger.error(f"Application error: {exc}", exc_info=True)
