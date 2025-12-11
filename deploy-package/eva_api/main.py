"""EVA API Platform - Main Application Entry Point.

FastAPI application with CORS, middleware, and route registration.
Phase 2 - Redis rate limiting, REST API routers.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from eva_api.config import get_settings
from eva_api.graphql import router as graphql
from eva_api.middleware.auth import AuthenticationMiddleware, RateLimitMiddleware
from eva_api.routers import auth, documents, health, queries, sessions, spaces, webhooks
from eva_api.services.redis_service import get_redis_service
from eva_api.services.webhook_service import start_webhook_service, stop_webhook_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.
    
    Handles startup and shutdown events including Redis connection.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # Database connections (Cosmos DB, Blob Storage) are lazy-initialized
    # in their respective services when first accessed
    
    # Phase 2.4 - Initialize Redis connection for rate limiting
    redis_service = get_redis_service()
    try:
        await redis_service.connect()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Rate limiting will be bypassed.")
    
    # Phase 3 - Initialize webhook delivery service
    try:
        await start_webhook_service()
        logger.info("Webhook delivery service started")
    except Exception as e:
        logger.warning(f"Webhook service startup failed: {e}")
    
    yield
    
    logger.info("Shutting down EVA API Platform")
    
    # Phase 3 - Stop webhook delivery service
    try:
        await stop_webhook_service()
        logger.info("Webhook delivery service stopped")
    except Exception as e:
        logger.error(f"Error stopping webhook service: {e}")
    
    # Phase 2.4 - Close Redis connection gracefully
    try:
        await redis_service.disconnect()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.error(f"Error closing Redis connection: {e}")


def create_application() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Enterprise-grade API gateway for EVA Suite. "
            "Provides REST APIs and GraphQL endpoints for knowledge spaces, "
            "document management, and AI-powered queries. "
            "Phase 2 includes rate limiting, full CRUD operations, and pagination."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
        contact={
            "name": "EVA API Support",
            "email": "support@eva-suite.ai",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=[
            {"name": "Health", "description": "Health and readiness checks"},
            {"name": "Authentication", "description": "JWT and API key authentication"},
            {"name": "Spaces", "description": "Knowledge space management (CRUD)"},
            {"name": "Documents", "description": "Document upload and management"},
            {"name": "Queries", "description": "AI-powered query submission and results"},
            {"name": "GraphQL", "description": "GraphQL API for flexible queries"},
            {"name": "Webhooks", "description": "Webhook subscription and event delivery (Phase 3)"},
            {"name": "Sessions", "description": "User session management with capacity limits (25-user demo)"},
        ],
    )
    
    # Add rate limiter to app state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
    )
    
    # GZip Compression
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Authentication and rate limiting middleware
    app.add_middleware(AuthenticationMiddleware)
    app.add_middleware(RateLimitMiddleware)
    
    # Register routers
    app.include_router(health.router, tags=["Health"])
    app.include_router(auth.router, tags=["Authentication"])
    app.include_router(spaces.router, tags=["Spaces"])
    app.include_router(documents.router, tags=["Documents"])
    app.include_router(queries.router, tags=["Queries"])
    app.include_router(sessions.router, tags=["Sessions"])
    app.include_router(webhooks.router, prefix="/api/v1", tags=["Webhooks"])
    app.include_router(graphql.router, prefix="/graphql", tags=["GraphQL"])
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc: Exception) -> JSONResponse:
        """Handle uncaught exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                },
                "meta": {
                    "request_id": getattr(request.state, "request_id", "unknown"),
                },
            },
        )
    
    logger.info("FastAPI application created successfully")
    return app


# Create application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "eva_api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
