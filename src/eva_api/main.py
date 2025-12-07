"""EVA API Platform - Main Application Entry Point.

FastAPI application with CORS, middleware, and route registration.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse

from eva_api.config import get_settings
from eva_api.graphql import router as graphql
from eva_api.middleware.auth import AuthenticationMiddleware, RateLimitMiddleware
from eva_api.routers import auth, documents, health, queries, spaces

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager.
    
    Handles startup and shutdown events.
    """
    settings = get_settings()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    # TODO: Initialize database connections in Phase 1.5
    # TODO: Initialize Redis connection in Phase 2.4
    
    yield
    
    logger.info("Shutting down EVA API Platform")
    # TODO: Close database connections
    # TODO: Close Redis connection


def create_application() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise-grade API gateway for EVA Suite",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        debug=settings.debug,
    )
    
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
    app.include_router(graphql.router, tags=["GraphQL"])
    
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
