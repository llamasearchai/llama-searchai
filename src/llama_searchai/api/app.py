"""
FastAPI application for LlamaSearch AI.

This module defines the main FastAPI application with all routes and middleware.
"""

from fastapi import Depends, FastAPI, HTTPException, Request, Security, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security.api_key import APIKeyHeader
from llamasearchai.config import settings
from llamasearchai.models.common import ErrorResponse, HealthResponse
from loguru import logger

# Import all route modules
from .routes import (
    backup,
    embed,
    monitor,
    notify,
    personalize,
    recommend,
    scheduler,
    search,
    vector,
)

# Create global API key security scheme
api_key_header = APIKeyHeader(name=settings.API_KEY_HEADER, auto_error=False)


def get_api_key(
    api_key_header: str = Security(api_key_header),
) -> str:
    """
    Validate the API key.

    Args:
        api_key_header: API key from the request header.

    Returns:
        The validated API key.

    Raises:
        HTTPException: If the API key is invalid.
    """
    # In a real application, validate the API key against a database or external service
    # For now, just check if it's provided
    if not api_key_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key_header


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application.
    """
    # Create FastAPI app with metadata
    app = FastAPI(
        title="LlamaSearch AI API",
        description="Unified API for LlamaSearch AI services",
        version=settings.VERSION if hasattr(settings, "VERSION") else "0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.DEBUG,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[origin for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal Server Error",
                detail=str(exc) if settings.DEBUG else "An unexpected error occurred",
                code="internal_error",
            ).dict(),
        )

    # Health check endpoint
    @app.get(
        "/health",
        response_model=HealthResponse,
        summary="Health Check",
        description="Check the health of the API",
        tags=["System"],
    )
    async def health_check():
        """
        Perform a health check.

        Returns:
            Health check response.
        """
        # In a real application, check the health of dependent services
        return HealthResponse(status="ok", version=app.version)

    # API key validation endpoint
    @app.get(
        "/api/v1/validate",
        summary="Validate API Key",
        description="Validate the provided API key",
        tags=["System"],
        dependencies=[Depends(get_api_key)],
    )
    async def validate_api_key():
        """
        Validate the API key.

        Returns:
            Validation result.
        """
        return {"valid": True}

    # Include all route modules based on feature flags
    if settings.FEATURES.get("metasearch", True):
        app.include_router(
            search.router,
            prefix="/api/v1",
            tags=["Search"],
        )

    if settings.FEATURES.get("vector", True):
        app.include_router(
            vector.router,
            prefix="/api/v1/vector",
            tags=["Vector"],
        )
        app.include_router(
            embed.router,
            prefix="/api/v1",
            tags=["Vector"],
        )

    if settings.FEATURES.get("personalization", True):
        app.include_router(
            personalize.router,
            prefix="/api/v1",
            tags=["Personalization"],
        )
        app.include_router(
            recommend.router,
            prefix="/api/v1",
            tags=["Personalization"],
        )

    if settings.FEATURES.get("monitor", True):
        app.include_router(
            monitor.router,
            prefix="/api/v1/monitor",
            tags=["Monitoring"],
        )

    if settings.FEATURES.get("backup", True):
        app.include_router(
            backup.router,
            prefix="/api/v1/backup",
            tags=["Backup"],
        )

    if settings.FEATURES.get("scheduler", True):
        app.include_router(
            scheduler.router,
            prefix="/api/v1/scheduler",
            tags=["Scheduler"],
        )

    if settings.FEATURES.get("notifications", True):
        app.include_router(
            notify.router,
            prefix="/api/v1/notifications",
            tags=["Notifications"],
        )

    return app


# Create a default app instance
app = create_app()
