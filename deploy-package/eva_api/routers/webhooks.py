"""Webhooks REST API Router - Phase 3.

CRUD operations for webhook subscriptions with:
- Event type filtering
- HMAC signature verification
- Delivery tracking and logs
- Test event delivery
- Retry configuration

Webhook events:
- space.created, space.updated, space.deleted
- document.added, document.processed, document.deleted
- query.submitted, query.completed, query.failed
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from azure.cosmos import exceptions as cosmos_exceptions
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, ConfigDict, HttpUrl

from eva_api.dependencies import verify_jwt_token, VerifiedJWTToken
from eva_api.models.auth import JWTClaims
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/webhooks",
    tags=["Webhooks"],
    responses={
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden"},
        404: {"description": "Not Found"},
        422: {"description": "Validation Error"},
    },
)


# ==================== Request/Response Models ====================


class WebhookCreate(BaseModel):
    """Request model for creating a webhook."""

    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="List of event types to subscribe to")
    description: Optional[str] = Field(None, description="Webhook description")
    secret: Optional[str] = Field(
        None, description="Secret for HMAC signature verification"
    )
    active: bool = Field(True, description="Whether webhook is active")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "url": "https://example.com/webhooks/eva",
                "events": ["document.added", "query.completed"],
                "description": "Production webhook for document processing",
                "secret": "whsec_abc123...",
                "active": True,
            }
        }
    )


class WebhookUpdate(BaseModel):
    """Request model for updating a webhook."""

    url: Optional[HttpUrl] = Field(None, description="Updated webhook URL")
    events: Optional[List[str]] = Field(None, description="Updated event types")
    description: Optional[str] = Field(None, description="Updated description")
    secret: Optional[str] = Field(None, description="Updated secret")
    active: Optional[bool] = Field(None, description="Updated active status")


class WebhookResponse(BaseModel):
    """Response model for a webhook."""

    id: str = Field(..., description="Webhook ID")
    url: str = Field(..., description="Webhook endpoint URL")
    events: List[str] = Field(..., description="Subscribed event types")
    description: Optional[str] = Field(None, description="Webhook description")
    active: bool = Field(..., description="Active status")
    tenant_id: str = Field(..., description="Owner tenant ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    last_triggered_at: Optional[datetime] = Field(None, description="Last trigger time")
    success_count: int = Field(0, description="Successful deliveries")
    failure_count: int = Field(0, description="Failed deliveries")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "webhook_abc123",
                "url": "https://example.com/webhooks/eva",
                "events": ["document.added", "query.completed"],
                "description": "Production webhook",
                "active": True,
                "tenant_id": "tenant_xyz",
                "created_at": "2025-12-08T12:00:00Z",
                "updated_at": "2025-12-08T12:00:00Z",
                "last_triggered_at": "2025-12-08T13:00:00Z",
                "success_count": 42,
                "failure_count": 3,
            }
        }
    )


class WebhookListResponse(BaseModel):
    """Response model for webhook list."""

    data: List[WebhookResponse]
    total: int


class WebhookLogResponse(BaseModel):
    """Response model for webhook delivery log."""

    id: str
    webhook_id: str
    event_type: str
    event_id: str
    delivered_at: datetime
    status_code: Optional[int]
    success: bool
    response_time_ms: float
    error_message: Optional[str]
    retry_count: int


class TestEventRequest(BaseModel):
    """Request model for test event."""

    event_type: str = Field("webhook.test", description="Event type to test")


# ==================== Dependency Functions ====================


async def get_cosmos_service() -> CosmosDBService:
    """Get Cosmos DB service instance."""
    settings = get_settings()
    return CosmosDBService(settings)


# ==================== API Endpoints ====================


@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create webhook subscription",
)
async def create_webhook(
    request: WebhookCreate,
    user: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> WebhookResponse:
    """Create a new webhook subscription."""
    try:
        webhook_id = f"webhook_{uuid4().hex[:16]}"
        now = datetime.utcnow().isoformat()

        webhook_doc = {
            "id": webhook_id,
            "url": str(request.url),
            "event_types": request.events,
            "description": request.description,
            "secret": request.secret,
            "is_active": request.active,
            "tenant_id": user.tenant_id,
            "created_at": now,
            "updated_at": now,
            "last_delivery_at": None,
            "stats": {
                "total_deliveries": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "avg_response_time_ms": 0.0
            }
        }

        created_item = await cosmos.create_webhook(webhook_doc)

        logger.info(f"Webhook created: {webhook_id} for tenant {user.tenant_id}")

        return _to_webhook_response(created_item)

    except Exception as e:
        logger.error(f"Error creating webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create webhook",
        )


@router.get(
    "",
    response_model=WebhookListResponse,
    summary="List webhook subscriptions",
)
async def list_webhooks(
    user: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
    active_only: bool = Query(False, description="Filter active webhooks only"),
) -> WebhookListResponse:
    """List all webhook subscriptions for the tenant."""
    try:
        webhooks = await cosmos.list_webhooks(user.tenant_id)
        
        if active_only:
            webhooks = [w for w in webhooks if w.get("is_active", False)]
        
        webhook_responses = [_to_webhook_response(w) for w in webhooks]

        return WebhookListResponse(data=webhook_responses, total=len(webhook_responses))

    except Exception as e:
        logger.error(f"Error listing webhooks: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list webhooks",
        )


@router.get(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Get webhook subscription",
)
async def get_webhook(
    webhook_id: str,
    user: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> WebhookResponse:
    """Get a specific webhook subscription."""
    try:
        item = await cosmos.get_webhook(webhook_id, user.tenant_id)
        
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        if item["tenant_id"] != user.tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        return _to_webhook_response(item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch webhook",
        )


@router.put(
    "/{webhook_id}",
    response_model=WebhookResponse,
    summary="Update webhook subscription",
)
async def update_webhook(
    webhook_id: str,
    request: WebhookUpdate,
    user: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> WebhookResponse:
    """Update a webhook subscription."""
    try:
        item = await cosmos.get_webhook(webhook_id, user.tenant_id)
        
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        if item["tenant_id"] != user.tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Prepare updates
        updates = {}
        if request.url is not None:
            updates["url"] = str(request.url)
        if request.events is not None:
            updates["event_types"] = request.events
        if request.description is not None:
            updates["description"] = request.description
        if request.secret is not None:
            updates["secret"] = request.secret
        if request.active is not None:
            updates["is_active"] = request.active

        updated_item = await cosmos.update_webhook(webhook_id, user.tenant_id, updates)
        
        if not updated_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        logger.info(f"Webhook updated: {webhook_id}")

        return _to_webhook_response(updated_item)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update webhook",
        )


@router.delete(
    "/{webhook_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete webhook subscription",
)
async def delete_webhook(
    webhook_id: str,
    user: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> None:
    """Delete a webhook subscription."""
    try:
        item = await cosmos.get_webhook(webhook_id, user.tenant_id)
        
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        if item["tenant_id"] != user.tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        success = await cosmos.delete_webhook(webhook_id, user.tenant_id)
        
        if not success:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        logger.info(f"Webhook deleted: {webhook_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete webhook",
        )


@router.get(
    "/{webhook_id}/logs",
    response_model=List[WebhookLogResponse],
    summary="Get webhook delivery logs",
)
async def get_webhook_logs(
    webhook_id: str,
    user: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
    limit: int = Query(50, ge=1, le=100),
) -> List[WebhookLogResponse]:
    """Get delivery logs for a webhook."""
    try:
        items = await cosmos.list_webhook_logs(webhook_id, limit=limit)
        
        logs = []
        for item in items:
            logs.append(
                WebhookLogResponse(
                    id=item["id"],
                    webhook_id=item["webhook_id"],
                    event_type=item["event_type"],
                    event_id=item["event_id"],
                    delivered_at=datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00")),
                    status_code=item.get("status_code"),
                    success=item["success"],
                    response_time_ms=item.get("duration_ms", 0),
                    error_message=item.get("error"),
                    retry_count=item.get("attempt", 0),
                )
            )

        return logs

    except Exception as e:
        logger.error(f"Error fetching webhook logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch webhook logs",
        )


@router.post(
    "/{webhook_id}/test",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Send test event to webhook",
)
async def test_webhook(
    webhook_id: str,
    request: TestEventRequest,
    user: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> dict:
    """Send a test event to the webhook endpoint."""
    from eva_api.services.webhook_service import get_webhook_service

    try:
        item = await cosmos.get_webhook(webhook_id, user.tenant_id)
        
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")

        if item["tenant_id"] != user.tenant_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Create test event
        test_event = {
            "event_type": request.event_type,
            "event_id": f"evt_test_{uuid4().hex[:16]}",
            "timestamp": datetime.utcnow().isoformat(),
            "tenant_id": user.tenant_id,
            "data": {
                "test": True,
                "message": "This is a test event from EVA API webhooks",
            },
        }

        # Deliver test event
        webhook_service = get_webhook_service()
        await webhook_service.deliver_event(webhook_id, test_event, user.tenant_id)

        logger.info(f"Test event sent to webhook {webhook_id}")

        return {
            "message": "Test event queued for delivery",
            "event_id": test_event["event_id"],
        }

    except cosmos_exceptions.CosmosResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Webhook not found")
    except Exception as e:
        logger.error(f"Failed to send test event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test event",
        )


# ==================== Helper Functions ====================


def _to_webhook_response(item: dict) -> WebhookResponse:
    """Convert Cosmos DB item to WebhookResponse."""
    stats = item.get("stats", {})
    return WebhookResponse(
        id=item["id"],
        url=item["url"],
        events=item.get("event_types", []),
        description=item.get("description"),
        active=item.get("is_active", True),
        tenant_id=item["tenant_id"],
        created_at=datetime.fromisoformat(item["created_at"].replace("Z", "+00:00")),
        updated_at=datetime.fromisoformat(item["updated_at"].replace("Z", "+00:00")),
        last_triggered_at=(
            datetime.fromisoformat(item["last_delivery_at"].replace("Z", "+00:00"))
            if item.get("last_delivery_at")
            else None
        ),
        success_count=stats.get("successful_deliveries", 0),
        failure_count=stats.get("failed_deliveries", 0),
    )
