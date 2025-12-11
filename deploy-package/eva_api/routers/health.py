"""Health check router for EVA API Platform.

Provides endpoints for monitoring service health and readiness.
Phase 2.4 - Redis health check included.
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, status

from eva_api.config import get_settings
from eva_api.models.base import HealthReadiness, HealthStatus
from eva_api.services.redis_service import get_redis_service

# Azure services for health checks
from azure.cosmos import CosmosClient, exceptions as cosmos_exceptions
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError

router = APIRouter()
logger = logging.getLogger(__name__)


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
    - Cosmos DB database
    - Azure Blob Storage
    
    Returns:
        HealthReadiness: Detailed readiness status
    """
    settings = get_settings()
    checks: dict[str, str] = {}
    all_ready = True
    
    # Basic API check
    checks["api"] = "ok"
    
    # Cosmos DB connectivity check
    try:
        if settings.cosmos_db_endpoint and settings.cosmos_db_key:
            cosmos_client = CosmosClient(
                settings.cosmos_db_endpoint,
                settings.cosmos_db_key,
            )
            # Test connectivity by listing databases
            list(cosmos_client.list_databases())
            checks["cosmos_db"] = "ok"
            logger.debug("Cosmos DB health check passed")
        else:
            checks["cosmos_db"] = "not_configured"
            logger.warning("Cosmos DB credentials not configured")
    except cosmos_exceptions.CosmosHttpResponseError as e:
        checks["cosmos_db"] = f"error: {e.status_code} - {e.message}"
        all_ready = False
        logger.error(f"Cosmos DB health check failed: {e}")
    except Exception as e:
        checks["cosmos_db"] = f"error: {str(e)}"
        all_ready = False
        logger.error(f"Cosmos DB health check failed: {e}")
    
    # Azure Blob Storage connectivity check
    try:
        if settings.blob_storage_connection_string:
            blob_service = BlobServiceClient.from_connection_string(
                settings.blob_storage_connection_string
            )
            # Test connectivity by listing containers (limit to 1 for performance)
            list(blob_service.list_containers(results_per_page=1))
            checks["blob_storage"] = "ok"
            logger.debug("Blob Storage health check passed")
        else:
            checks["blob_storage"] = "not_configured"
            logger.warning("Blob Storage connection string not configured")
    except AzureError as e:
        checks["blob_storage"] = f"error: {str(e)}"
        all_ready = False
        logger.error(f"Blob Storage health check failed: {e}")
    except Exception as e:
        checks["blob_storage"] = f"error: {str(e)}"
        all_ready = False
        logger.error(f"Blob Storage health check failed: {e}")
    
    # Redis check (Phase 2.4)
    try:
        redis_service = get_redis_service()
        if redis_service.is_connected:
            redis_health = await redis_service.health_check()
            if redis_health["status"] == "healthy":
                checks["redis"] = "ok"
                logger.debug(f"Redis health check passed (latency: {redis_health.get('latency_ms')}ms)")
            else:
                checks["redis"] = f"error: {redis_health.get('message', 'unhealthy')}"
                all_ready = False
                logger.error(f"Redis health check failed: {redis_health.get('message')}")
        else:
            checks["redis"] = "not_connected"
            logger.warning("Redis not connected")
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"
        logger.error(f"Redis health check failed: {e}")
        # Don't fail overall readiness if Redis is down (fail open for rate limiting)
    
    return HealthReadiness(
        ready=all_ready,
        checks=checks,
        timestamp=datetime.utcnow(),
    )
