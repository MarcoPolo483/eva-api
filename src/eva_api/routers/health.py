"""Health check router for EVA API Platform.

Provides endpoints for monitoring service health and readiness.
"""

import uuid
from datetime import datetime

from fastapi import APIRouter, status

from eva_api.config import get_settings
from eva_api.models.base import HealthReadiness, HealthStatus

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthStatus,
    status_code=status.HTTP_200_OK,
    summary="Health Check",
    description="Returns the current health status of the API",
    response_description="Health status information",
)
async def health_check() -> HealthStatus:
    """Basic health check endpoint.
    
    Returns:
        HealthStatus: Current health status
    """
    settings = get_settings()
    
    return HealthStatus(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/health/ready",
    response_model=HealthReadiness,
    status_code=status.HTTP_200_OK,
    summary="Readiness Check",
    description="Returns detailed readiness status including dependency checks",
    response_description="Readiness status with component checks",
)
async def readiness_check() -> HealthReadiness:
    """Detailed readiness check endpoint.
    
    Checks connectivity to:
    - Database (TODO: Phase 1.5)
    - Redis (TODO: Phase 2.4)
    - Azure services (TODO: Phase 1.5)
    
    Returns:
        HealthReadiness: Detailed readiness status
    """
    checks: dict[str, str] = {}
    all_ready = True
    
    # Basic checks (always pass for now)
    checks["api"] = "ok"
    
    # TODO: Phase 1.5 - Add Cosmos DB connectivity check
    # try:
    #     await cosmos_client.ping()
    #     checks["database"] = "ok"
    # except Exception as e:
    #     checks["database"] = f"error: {str(e)}"
    #     all_ready = False
    
    # TODO: Phase 2.4 - Add Redis connectivity check
    # try:
    #     await redis_client.ping()
    #     checks["redis"] = "ok"
    # except Exception as e:
    #     checks["redis"] = f"error: {str(e)}"
    #     all_ready = False
    
    # Placeholder checks for Phase 1
    checks["database"] = "not_configured"
    checks["redis"] = "not_configured"
    
    return HealthReadiness(
        ready=all_ready,
        checks=checks,
        timestamp=datetime.utcnow(),
    )
