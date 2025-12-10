"""Queries API endpoints.
"""

import logging
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from eva_api.dependencies import CurrentSettings, VerifiedAPIKey
from eva_api.models.base import ErrorResponse, SuccessResponse
from eva_api.models.queries import QueryRequest, QueryResponse, QueryResult
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.query_service import QueryService
from eva_api.services.webhook_service import get_webhook_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["queries"])


def get_cosmos_service(settings: CurrentSettings) -> CosmosDBService:
    """Dependency: Cosmos DB service."""
    return CosmosDBService(settings)


def get_blob_service(settings: CurrentSettings) -> BlobStorageService:
    """Dependency: Blob Storage service."""
    return BlobStorageService(settings)


def get_query_service(
    settings: CurrentSettings,
    cosmos: CosmosDBService = Depends(get_cosmos_service),
    blob: BlobStorageService = Depends(get_blob_service),
) -> QueryService:
    """Dependency: Query service with Azure integrations."""
    return QueryService(settings, cosmos_service=cosmos, blob_service=blob)


@router.post(
    "/queries",
    response_model=SuccessResponse[QueryResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def submit_query(
    query: QueryRequest,
    api_key: VerifiedAPIKey,
    background_tasks: BackgroundTasks,
    query_service: QueryService = Depends(get_query_service),
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> SuccessResponse[QueryResponse]:
    """
    Submit a new query for processing.

    Requires JWT authentication.
    Returns immediately with query ID and pending status.
    Use GET /queries/{id} to check status and GET /queries/{id}/result to retrieve answer.
    """
    try:
        # Verify space exists
        space = await cosmos.get_space(query.space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {query.space_id} not found",
            )

        user_id = "demo-user"  # API key auth doesn't have user context
        query_data = await query_service.submit_query(
            space_id=query.space_id,
            question=query.question,
            user_id=user_id,
            parameters=query.parameters,
        )

        query_response = QueryResponse(**query_data)
        logger.info(f"Query submitted: {query_response.id} by {user_id}")

        # Phase 3: Broadcast webhook event for query submission
        tenant_id = "demo-tenant"  # API key auth returns tenant_id in metadata
        background_tasks.add_task(
            _broadcast_query_event,
            event_type="query.submitted",
            query_id=str(query_response.id),
            space_id=str(query.space_id),
            query_data=query_response.model_dump(),
            tenant_id=tenant_id,
        )

        return SuccessResponse(
            data=query_response,
            message="Query submitted successfully. Use GET /queries/{id} to check status.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to submit query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit query",
        )


@router.get(
    "/queries/{query_id}",
    response_model=SuccessResponse[QueryResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Query not found"},
    },
)
async def get_query_status(
    query_id: UUID,
    api_key: VerifiedAPIKey,
    query_service: QueryService = Depends(get_query_service),
) -> SuccessResponse[QueryResponse]:
    """
    Get query processing status.

    Requires JWT authentication.
    """
    try:
        query_data = await query_service.get_query_status(query_id)
        if not query_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found",
            )

        query_response = QueryResponse(**query_data)
        return SuccessResponse(data=query_response, message="Query status retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query status {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query status",
        )


@router.get(
    "/queries/{query_id}/result",
    response_model=SuccessResponse[QueryResult],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Query not found"},
        425: {"model": ErrorResponse, "description": "Query not yet completed"},
    },
)
async def get_query_result(
    query_id: UUID,
    api_key: VerifiedAPIKey,
    query_service: QueryService = Depends(get_query_service),
) -> SuccessResponse[QueryResult]:
    """
    Get query result (answer and sources).

    Requires JWT authentication.
    Returns 425 Too Early if query is still processing.
    """
    try:
        # First get query status
        query = await query_service.get_query_status(query_id)
        if not query:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found",
            )

        # Check if query is completed
        from eva_api.models.queries import QueryStatus
        if query.get("status") in [QueryStatus.PENDING.value, QueryStatus.PROCESSING.value]:
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail=f"Query is still {query.get('status')}. Check back later.",
            )

        # If failed, return error in result
        if query.get("status") == QueryStatus.FAILED.value:
            result_response = QueryResult(
                id=query_id,
                status=QueryStatus.FAILED,
                answer=None,
                sources=None,
                error=query.get("error_message", "Query processing failed"),
                completed_at=query.get("updated_at"),
                metadata=None
            )
            return SuccessResponse(data=result_response, message="Query failed")

        # Get result
        result_dict = query.get("result", {})

        # Build QueryResult response
        result_response = QueryResult(
            id=query_id,
            status=QueryStatus.COMPLETED,
            answer=result_dict.get("answer", "No answer generated"),
            sources=result_dict.get("sources", []),
            error=None,
            completed_at=result_dict.get("generated_at") or query.get("updated_at"),
            metadata={
                "document_count": result_dict.get("document_count", 0),
                "confidence_score": result_dict.get("confidence_score"),
                "is_demo": result_dict.get("is_demo", False)
            }
        )

        return SuccessResponse(data=result_response, message="Query result retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query result {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query result",
        )


async def _broadcast_query_event(
    event_type: str,
    query_id: str,
    space_id: str,
    query_data: dict,
    tenant_id: str,
) -> None:
    """Broadcast query event to webhooks (Phase 3).

    Args:
        event_type: Event type (query.submitted, query.completed, query.failed)
        query_id: Query ID
        space_id: Parent space ID
        query_data: Query data payload
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
                "query_id": query_id,
                "space_id": space_id,
                "query": query_data,
            },
        }
        await webhook_service.broadcast_event(event_type, event, tenant_id)
    except Exception as e:
        logger.error(f"Failed to broadcast query event {event_type}: {e}")
