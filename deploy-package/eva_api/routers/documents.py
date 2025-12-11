"""Documents API endpoints.
"""

import logging
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile, status

from eva_api.dependencies import CurrentSettings, VerifiedJWTToken, verify_jwt_token
from eva_api.models.base import ErrorResponse, SuccessResponse
from eva_api.models.documents import DocumentListResponse, DocumentResponse
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.webhook_service import get_webhook_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["documents"])


def get_blob_service(settings: CurrentSettings) -> BlobStorageService:
    """Dependency: Blob Storage service."""
    return BlobStorageService(settings)


def get_cosmos_service(settings: CurrentSettings) -> CosmosDBService:
    """Dependency: Cosmos DB service."""
    return CosmosDBService(settings)


@router.post(
    "/spaces/{space_id}/documents",
    response_model=SuccessResponse[DocumentResponse],
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Space not found"},
        413: {"model": ErrorResponse, "description": "File too large"},
    },
)
async def upload_document(
    space_id: UUID,
    file: Annotated[UploadFile, File(description="Document file to upload")],
    jwt_token: VerifiedJWTToken,
    background_tasks: BackgroundTasks,
    metadata: Annotated[str | None, Form(description="JSON metadata")] = None,
    blob_service: BlobStorageService = Depends(get_blob_service),
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> SuccessResponse[DocumentResponse]:
    """Upload a document to a space.
    
    Requires JWT authentication.
    Max file size: 100 MB (configurable via settings).
    """
    try:
        # Verify space exists
        space = await cosmos.get_space(space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found",
            )
        
        # Parse metadata if provided
        import json
        metadata_dict = json.loads(metadata) if metadata else {}
        
        # Upload to blob storage
        content = await file.read()
        from io import BytesIO
        content_stream = BytesIO(content)
        
        doc_data = await blob_service.upload_document(
            space_id=space_id,
            filename=file.filename or "unnamed",
            content=content_stream,
            content_type=file.content_type or "application/octet-stream",
            metadata=metadata_dict,
        )
        
        # Add user info
        doc_data["created_by"] = jwt_token.get("sub", "unknown")
        
        # Increment document count
        await cosmos.increment_document_count(space_id)
        
        doc_response = DocumentResponse(**doc_data)
        logger.info(f"Document uploaded: {doc_response.id} to space {space_id}")
        
        # Phase 3: Broadcast webhook event
        tenant_id = jwt_token.get("tenant_id", "default")
        background_tasks.add_task(
            _broadcast_document_event,
            event_type="document.added",
            document_id=str(doc_response.id),
            space_id=str(space_id),
            document_data=doc_response.model_dump(),
            tenant_id=tenant_id,
        )
        
        return SuccessResponse(data=doc_response, message="Document uploaded successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload document",
        )


@router.get(
    "/spaces/{space_id}/documents",
    response_model=SuccessResponse[DocumentListResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Space not found"},
    },
)
async def list_documents(
    space_id: UUID,
    jwt_token: VerifiedJWTToken,
    cursor: Annotated[str | None, Query(description="Pagination cursor")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20,
    blob_service: BlobStorageService = Depends(get_blob_service),
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> SuccessResponse[DocumentListResponse]:
    """
    List documents in a space with cursor-based pagination.
    
    Requires JWT authentication.
    """
    try:
        # Verify space exists
        space = await cosmos.get_space(space_id)
        if not space:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Space {space_id} not found",
            )
        
        items, next_cursor, has_more = await blob_service.list_documents(
            space_id=space_id, cursor=cursor, limit=limit
        )
        documents = [DocumentResponse(**item) for item in items]
        
        response = DocumentListResponse(items=documents, cursor=next_cursor, has_more=has_more)
        return SuccessResponse(data=response, message="Documents retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents for space {space_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        )


@router.get(
    "/documents/{doc_id}",
    response_model=SuccessResponse[DocumentResponse],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def get_document(
    doc_id: UUID,
    jwt_token: VerifiedJWTToken,
    blob_service: BlobStorageService = Depends(get_blob_service),
) -> SuccessResponse[DocumentResponse]:
    """
    Get document metadata by ID.
    
    Requires JWT authentication.
    """
    try:
        doc_data = await blob_service.get_document(doc_id)
        if not doc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )
        
        doc_response = DocumentResponse(**doc_data)
        return SuccessResponse(data=doc_response, message="Document retrieved successfully")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document",
        )


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
        404: {"model": ErrorResponse, "description": "Document not found"},
    },
)
async def delete_document(
    doc_id: UUID,
    jwt_token: VerifiedJWTToken,
    background_tasks: BackgroundTasks,
    blob_service: BlobStorageService = Depends(get_blob_service),
    cosmos: CosmosDBService = Depends(get_cosmos_service),
) -> None:
    """
    Delete a document.
    
    Requires JWT authentication.
    """
    try:
        # Get document metadata first
        doc_data = await blob_service.get_document(doc_id)
        if not doc_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {doc_id} not found",
            )
        
        # Delete from blob storage
        success = await blob_service.delete_document(doc_data["blob_url"])
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete document from storage",
            )
        
        # Decrement document count
        from uuid import UUID as UUIDType
        space_id = UUIDType(doc_data["space_id"])
        await cosmos.decrement_document_count(space_id)
        
        logger.info(f"Document deleted: {doc_id} by {jwt_token.get('sub')}")
        
        # Phase 3: Broadcast webhook event
        tenant_id = jwt_token.get("tenant_id", "default")
        background_tasks.add_task(
            _broadcast_document_event,
            event_type="document.deleted",
            document_id=str(doc_id),
            space_id=doc_data["space_id"],
            document_data={"id": str(doc_id), "filename": doc_data.get("filename")},
            tenant_id=tenant_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete document {doc_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        )


async def _broadcast_document_event(
    event_type: str,
    document_id: str,
    space_id: str,
    document_data: dict,
    tenant_id: str,
) -> None:
    """Broadcast document event to webhooks (Phase 3).
    
    Args:
        event_type: Event type (document.added, document.deleted)
        document_id: Document ID
        space_id: Parent space ID
        document_data: Document data payload
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
                "document_id": document_id,
                "space_id": space_id,
                "document": document_data,
            },
        }
        await webhook_service.broadcast_event(event_type, event, tenant_id)
    except Exception as e:
        logger.error(f"Failed to broadcast document event {event_type}: {e}")
