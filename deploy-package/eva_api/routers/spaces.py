"""Spaces API endpoints.
"""

import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status

from eva_api.dependencies import CurrentSettings, VerifiedAPIKey, VerifiedJWTToken, verify_jwt_token
from eva_api.models.base import ErrorResponse, SuccessResponse
from eva_api.models.spaces import SpaceCreate, SpaceListResponse, SpaceResponse, SpaceUpdate
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.webhook_service import get_webhook_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/spaces", tags=["spaces"])


def get_cosmos_service(
    settings: CurrentSettings,
) -> CosmosDBService:
    """Dependency: Cosmos DB service."""
    return CosmosDBService(settings)


@router.post(
    "",
    response_model=SuccessResponse[SpaceResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        400: {"model": ErrorResponse, "description": "Bad Request"},
    },
)
async def create_space(
    space: SpaceCreate,
    api_key: VerifiedAPIKey,
    background_tasks: BackgroundTasks,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> SuccessResponse[SpaceResponse]:
    """
    Create a new space.
    
    Requires API key authentication.
    """
    try:
        space_data = await cosmos.create_space(
            name=space.name,
            description=space.description,
            metadata=space.metadata,
        )
        space_response = SpaceResponse(**space_data)
        
        logger.info(f"Space created: {space_response.id} by demo-user")
        
        # Phase 3: Broadcast webhook event
        tenant_id = "demo-tenant"
        background_tasks.add_task(
            _broadcast_space_event,
            event_type="space.created",
            space_id=str(space_response.id),
            space_data=space_response.model_dump(),
            tenant_id=tenant_id,
        )
        
        return SuccessResponse(data=space_response, message="Space created successfully")
    except Exception as e:
        logger.error(f"Failed to create space: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create space",
        )


@router.get(
    "",
    response_model=SuccessResponse[SpaceListResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def list_spaces(
    api_key: VerifiedAPIKey,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> SuccessResponse[SpaceListResponse]:
    """
    List all spaces with cursor-based pagination.
    
    Requires API key authentication.
    """
    try:
        items, next_cursor, has_more = await cosmos.list_spaces(cursor=cursor, limit=limit)
        spaces = [SpaceResponse(**item) for item in items]
        
        response = SpaceListResponse(items=spaces, cursor=next_cursor, has_more=has_more)
        return SuccessResponse(data=response, message="Spaces retrieved successfully")
    except Exception as e:
        logger.error(f"Failed to list spaces: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list spaces",
        )


@router.get(
    "/{space_id}",
    response_model=SuccessResponse[SpaceResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def get_space(
    space_id: UUID,
    jwt_token: VerifiedJWTToken,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> SuccessResponse[SpaceResponse]:
    """
    Get a specific space by ID.
    
    Requires JWT authentication.
    """
    try:
        space_data = await cosmos.get_space(space_id)
        if not space_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found",
            )
        
        space_response = SpaceResponse(**space_data)
        return SuccessResponse(data=space_response, message="Space retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve space",
        )


@router.put(
    "/{space_id}",
    response_model=SuccessResponse[SpaceResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def update_space(
    space_id: UUID,
    space: SpaceUpdate,
    jwt_token: VerifiedJWTToken,
    background_tasks: BackgroundTasks,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> SuccessResponse[SpaceResponse]:
    """
    Update an existing space.
    
    Requires JWT authentication.
    """
    try:
        space_data = await cosmos.update_space(
            space_id=space_id,
            name=space.name,
            description=space.description,
            metadata=space.metadata,
        )
        if not space_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found",
            )
        
        space_response = SpaceResponse(**space_data)
        logger.info(f"Space updated: {space_id} by {jwt_token.get('sub')}")
        
        # Phase 3: Broadcast webhook event
        tenant_id = jwt_token.get("tenant_id", "default")
        background_tasks.add_task(
            _broadcast_space_event,
            event_type="space.updated",
            space_id=str(space_id),
            space_data=space_response.model_dump(),
            tenant_id=tenant_id,
        )
        
        return SuccessResponse(data=space_response, message="Space updated successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update space",
        )


@router.delete(
    "/{space_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def delete_space(
    space_id: UUID,
    jwt_token: VerifiedJWTToken,
    background_tasks: BackgroundTasks,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> None:
    """
    Delete a space.
    
    Requires JWT authentication.
    """
    try:
        success = await cosmos.delete_space(space_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found",
            )
        
        logger.info(f"Space deleted: {space_id} by {jwt_token.get('sub')}")
        
        # Phase 3: Broadcast webhook event
        tenant_id = jwt_token.get("tenant_id", "default")
        background_tasks.add_task(
            _broadcast_space_event,
            event_type="space.deleted",
            space_id=str(space_id),
            space_data={"id": str(space_id)},
            tenant_id=tenant_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete space",
        )


async def _broadcast_space_event(
    event_type: str,
    space_id: str,
    space_data: dict,
    tenant_id: str,
) -> None:
    """Broadcast space event to webhooks (Phase 3).
    
    Args:
        event_type: Event type (space.created, space.updated, space.deleted)
        space_id: Space ID
        space_data: Space data payload
        tenant_id: Tenant ID
    """
    try:
        webhook_service = get_webhook_service()
        event = {
            "event_type": event_type,
            "event_id": f"evt_{uuid4().hex[:16]}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "tenant_id": tenant_id,
            "data": {
                "space_id": space_id,
                "space": space_data,
            },
        }
        await webhook_service.broadcast_event(event_type, event, tenant_id)
    except Exception as e:
        logger.error(f"Failed to broadcast space event {event_type}: {e}")
