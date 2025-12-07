"""
Queries API endpoints.
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from eva_api.dependencies import CurrentSettings, VerifiedJWTToken, verify_jwt_token
from eva_api.models.base import ErrorResponse, SuccessResponse
from eva_api.models.queries import QueryRequest, QueryResponse, QueryResult
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.query_service import QueryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/queries", tags=["queries"])


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
    "",
    response_model=SuccessResponse[QueryResponse],
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def submit_query(
    query: QueryRequest,
    jwt_token: VerifiedJWTToken,
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
        
        user_id = jwt_token.get("sub", "unknown")
        query_data = await query_service.submit_query(
            space_id=query.space_id,
            question=query.question,
            user_id=user_id,
            parameters=query.parameters,
        )
        
        query_response = QueryResponse(**query_data)
        logger.info(f"Query submitted: {query_response.id} by {user_id}")
        
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
    "/{query_id}",
    response_model=SuccessResponse[QueryResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Query not found"},
    },
)
async def get_query_status(
    query_id: UUID,
    jwt_token: VerifiedJWTToken,
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
    "/{query_id}/result",
    response_model=SuccessResponse[QueryResult],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Query not found"},
        425: {"model": ErrorResponse, "description": "Query not yet completed"},
    },
)
async def get_query_result(
    query_id: UUID,
    jwt_token: VerifiedJWTToken,
    query_service: QueryService = Depends(get_query_service),
) -> SuccessResponse[QueryResult]:
    """
    Get query result (answer and sources).
    
    Requires JWT authentication.
    Returns 425 Too Early if query is still processing.
    """
    try:
        result_data = await query_service.get_query_result(query_id)
        if not result_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Query {query_id} not found",
            )
        
        # Check if query is completed
        from eva_api.models.queries import QueryStatus
        if result_data.get("status") in [QueryStatus.PENDING.value, QueryStatus.PROCESSING.value]:
            raise HTTPException(
                status_code=status.HTTP_425_TOO_EARLY,
                detail=f"Query is still {result_data.get('status')}. Check back later.",
            )
        
        result_response = QueryResult(**result_data)
        return SuccessResponse(data=result_response, message="Query result retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get query result {query_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve query result",
        )
