"""
GraphQL resolvers implementation.

Implements query, mutation, and subscription resolvers using existing services.
"""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, Optional
from uuid import UUID

import strawberry
from strawberry.types import Info

from eva_api.graphql.schema import (
    CreateSpaceInput,
    Document,
    DocumentConnection,
    Query,
    QueryResult,
    QueryStatus,
    Space,
    SpaceConnection,
    SubmitQueryInput,
    UpdateSpaceInput,
)
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.query_service import QueryService

logger = logging.getLogger(__name__)


# ============================================================================
# Context Setup
# ============================================================================

class GraphQLContext(dict):
    """Context object passed to all resolvers."""
    
    def __init__(
        self,
        cosmos_service: CosmosDBService,
        blob_service: BlobStorageService,
        query_service: QueryService,
        user_id: str,
        tenant_id: str,
    ):
        super().__init__()
        # Store as both dict keys and attributes for compatibility
        self["cosmos"] = cosmos_service
        self["blob"] = blob_service
        self["query"] = query_service
        self["user_id"] = user_id
        self["tenant_id"] = tenant_id
        self.cosmos = cosmos_service
        self.blob = blob_service
        self.query = query_service
        self.user_id = user_id
        self.tenant_id = tenant_id


# ============================================================================
# Space Resolvers
# ============================================================================

async def spaces(
    info: Info,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> SpaceConnection:
    """List all spaces with pagination."""
    try:
        ctx = info.context
        
        items_raw, next_cursor, has_more = await ctx["cosmos"].list_spaces(
            limit=limit,
            cursor=cursor,
        )
        
        items = [Space(**item) for item in items_raw]
        
        return SpaceConnection(
            items=items,
            cursor=next_cursor,
            has_more=has_more,
            total_count=len(items),  # Add total_count
        )
    except Exception as e:
        logger.error(f"Error fetching spaces: {e}", exc_info=True)
        raise Exception(f"Failed to fetch spaces: {str(e)}")


async def space(info: Info, id: UUID) -> Optional[Space]:
    """Get a single space by ID."""
    ctx = info.context
    
    space_data = await ctx["cosmos"].get_space(id)
    if not space_data:
        return None
    
    return Space(**space_data)


@strawberry.mutation
async def create_space(
    info: Info,
    input: CreateSpaceInput,
) -> Space:
    """Create a new space."""
    try:
        ctx = info.context
        
        space_data = await ctx["cosmos"].create_space(
            name=input.name,
            description=input.description,
            tenant_id=ctx.tenant_id,
            created_by=ctx.user_id,
            metadata=input.metadata,
            tags=input.tags,
        )
        
        logger.info(f"Created space {space_data['id']} via GraphQL")
        return Space(**space_data)
    except Exception as e:
        logger.error(f"Error creating space: {e}", exc_info=True)
        raise Exception(f"Failed to create space: {str(e)}")


@strawberry.mutation
async def update_space(
    info: Info,
    id: UUID,
    input: UpdateSpaceInput,
) -> Space:
    """Update an existing space."""
    ctx = info.context
    
    updates = {}
    if input.name is not None:
        updates["name"] = input.name
    if input.description is not None:
        updates["description"] = input.description
    if input.metadata is not None:
        updates["metadata"] = input.metadata
    if input.tags is not None:
        updates["tags"] = input.tags
    
    space_data = await ctx["cosmos"].update_space(id, **updates)
    if not space_data:
        raise ValueError(f"Space {id} not found")
    
    logger.info(f"Updated space {id} via GraphQL")
    return Space(**space_data)


async def delete_space(info: Info, id: UUID) -> bool:
    """Delete a space."""
    ctx = info.context
    
    success = await ctx["cosmos"].delete_space(id)
    
    if success:
        logger.info(f"Deleted space {id} via GraphQL")
    
    return success


# ============================================================================
# Document Resolvers
# ============================================================================

async def documents(
    info: Info,
    space_id: UUID,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> DocumentConnection:
    """List documents in a space."""
    ctx = info.context
    
    items_raw, next_cursor, has_more = await ctx["cosmos"].list_documents(
        space_id=space_id,
        limit=limit,
        continuation_token=cursor,
    )
    
    items = [Document(**item) for item in items_raw]
    
    return DocumentConnection(
        items=items,
        cursor=next_cursor,
        has_more=has_more,
        total_count=len(items),
    )


async def document(
    info: Info,
    id: UUID,
) -> Optional[Document]:
    """Get a single document by ID."""
    ctx = info.context
    
    # Note: space_id would be needed for proper lookup, using None for now
    doc_data = await ctx["cosmos"].get_document_metadata(id, None)
    if not doc_data:
        return None
    
    return Document(**doc_data)


@strawberry.mutation
async def delete_document(
    info: Info,
    id: UUID,
    space_id: UUID,
) -> bool:
    """Delete a document."""
    ctx = info.context
    
    # Get document metadata to find blob_name
    doc_data = await ctx["cosmos"].get_document_metadata(id, space_id)
    if not doc_data:
        return False
    
    blob_name = doc_data.get("blob_name")
    
    # Delete from blob storage
    if blob_name:
        await ctx["blob"].delete_document(blob_name)
    
    # Delete metadata from Cosmos DB
    await ctx["cosmos"].delete_document_metadata(id, space_id)
    
    # Decrement space document count
    await ctx["cosmos"].decrement_document_count(space_id)
    
    logger.info(f"Deleted document {id} via GraphQL")
    return True


# ============================================================================
# Query Resolvers
# ============================================================================

async def query_status(info: Info, id: UUID) -> Optional[Query]:
    """Get query status and result."""
    ctx = info.context
    
    query_data = await ctx["query"].get_query_status(id)
    if not query_data:
        return None
    
    # Convert result dict to QueryResult if present
    result = None
    if query_data.get("result"):
        result_data = query_data["result"]
        result = QueryResult(
            answer=result_data["answer"],
            sources=[UUID(s) for s in result_data["sources"]],
            document_count=result_data["document_count"],
            generated_at=datetime.fromisoformat(result_data["generated_at"]),
        )
    
    return Query(
        id=UUID(query_data["id"]),
        space_id=UUID(query_data["space_id"]),
        question=query_data["question"],
        status=QueryStatus(query_data["status"]),
        created_by=query_data["created_by"],
        created_at=datetime.fromisoformat(query_data["created_at"]),
        updated_at=datetime.fromisoformat(query_data["updated_at"]),
        parameters=query_data.get("parameters"),
        result=result,
        error_message=query_data.get("error_message"),
    )


async def submit_query(
    info: Info,
    input: SubmitQueryInput,
) -> Query:
    """Submit a new query for processing."""
    ctx = info.context
    
    query_data = await ctx["query"].submit_query(
        space_id=input.space_id,
        question=input.question,
        user_id=ctx.user_id,
        parameters=input.parameters,
    )
    
    logger.info(f"Submitted query {query_data['id']} via GraphQL")
    
    return Query(
        id=UUID(query_data["id"]),
        space_id=UUID(query_data["space_id"]),
        question=query_data["question"],
        status=QueryStatus(query_data["status"]),
        created_by=query_data["created_by"],
        created_at=datetime.fromisoformat(query_data["created_at"]),
        updated_at=datetime.fromisoformat(query_data["updated_at"]),
        parameters=query_data.get("parameters"),
        result=None,
        error_message=None,
    )


async def cancel_query(info: Info, id: UUID) -> bool:
    """Cancel a pending or processing query."""
    ctx = info.context
    
    success = await ctx["query"].cancel_query(id)
    
    if success:
        logger.info(f"Cancelled query {id} via GraphQL")
    
    return success


# ============================================================================
# Subscription Resolvers (Phase 3 - Real-time Events)
# ============================================================================

async def query_updates(
    info: Info,
    id: UUID,
) -> AsyncGenerator[Query, None]:
    """Subscribe to query status updates for a specific query.
    
    Polls query status every 2 seconds and emits updates until completion.
    In production, use Redis Pub/Sub or Azure Service Bus for true real-time.
    """
    ctx = info.context
    
    # Poll for updates every 2 seconds
    while True:
        query_data = await ctx["query"].get_query_status(id)
        
        if not query_data:
            break
        
        # Convert to Query type
        result = None
        if query_data.get("result"):
            result_data = query_data["result"]
            result = QueryResult(
                answer=result_data["answer"],
                sources=[UUID(s) for s in result_data["sources"]],
                document_count=result_data["document_count"],
                generated_at=datetime.fromisoformat(result_data["generated_at"]),
            )
        
        query_obj = Query(
            id=UUID(query_data["id"]),
            space_id=UUID(query_data["space_id"]),
            question=query_data["question"],
            status=QueryStatus(query_data["status"]),
            created_by=query_data["created_by"],
            created_at=datetime.fromisoformat(query_data["created_at"]),
            updated_at=datetime.fromisoformat(query_data["updated_at"]),
            parameters=query_data.get("parameters"),
            result=result,
            error_message=query_data.get("error_message"),
        )
        
        yield query_obj
        
        # Stop if query is in terminal state
        if query_data["status"] in ("completed", "failed"):
            break
        
        # Wait before polling again
        await asyncio.sleep(2)


async def document_added(
    info: Info,
    space_id: UUID,
) -> AsyncGenerator[Document, None]:
    """Subscribe to document upload events in a space.
    
    Phase 3: Real-time document monitoring
    Uses Redis Pub/Sub pattern for event broadcasting
    """
    from eva_api.services.redis_service import get_redis_service
    
    ctx = info.context
    redis_service = get_redis_service()
    
    if not redis_service.is_connected:
        logger.warning("Redis not available for subscriptions")
        return
    
    # Subscribe to document events for this space
    channel = f"space:{space_id}:document:added"
    
    try:
        # Note: This requires redis-py pubsub implementation
        # For now, polling fallback
        last_check = datetime.utcnow()
        
        while True:
            # Query for recent documents (last 5 seconds)
            # In production: Use Redis Pub/Sub or Azure Event Grid
            await asyncio.sleep(5)
            
            # Placeholder: Would emit document objects when detected
            # Real implementation needs event system integration
            logger.debug(f"Checking for new documents in space {space_id}")
            
    except asyncio.CancelledError:
        logger.info(f"Subscription cancelled for space {space_id}")
        raise


async def query_completed(
    info: Info,
    space_id: UUID,
) -> AsyncGenerator[Query, None]:
    """Subscribe to query completion events in a space.
    
    Phase 3: Real-time query result notifications
    Emits when queries finish processing (success or failure)
    """
    from eva_api.services.redis_service import get_redis_service
    
    ctx = info.context
    redis_service = get_redis_service()
    
    if not redis_service.is_connected:
        logger.warning("Redis not available for subscriptions")
        return
    
    channel = f"space:{space_id}:query:completed"
    
    try:
        while True:
            await asyncio.sleep(5)
            # Placeholder: Would emit Query objects from event stream
            logger.debug(f"Checking for completed queries in space {space_id}")
            
    except asyncio.CancelledError:
        logger.info(f"Subscription cancelled for space {space_id}")
        raise


async def space_events(
    info: Info,
) -> AsyncGenerator["SpaceEvent", None]:
    """Subscribe to all space lifecycle events for tenant.
    
    Phase 3: Admin dashboard real-time updates
    Emits: created, updated, deleted events
    """
    from eva_api.graphql.schema import SpaceEvent, SpaceEventType
    from eva_api.services.redis_service import get_redis_service
    
    ctx = info.context
    tenant_id = ctx["tenant_id"]
    redis_service = get_redis_service()
    
    if not redis_service.is_connected:
        logger.warning("Redis not available for subscriptions")
        return
    
    channel = f"tenant:{tenant_id}:space:events"
    
    try:
        while True:
            await asyncio.sleep(5)
            # Placeholder: Would emit SpaceEvent objects from event stream
            logger.debug(f"Checking for space events for tenant {tenant_id}")
            
    except asyncio.CancelledError:
        logger.info(f"Subscription cancelled for tenant {tenant_id}")
        raise


# ============================================================================
# Attach Resolvers to Schema
# ============================================================================

def attach_resolvers():
    """Attach resolver functions to schema types."""
    from eva_api.graphql.schema import Mutation, QueryRoot, Subscription
    
    # Query resolvers
    QueryRoot.spaces = spaces
    QueryRoot.space = space
    QueryRoot.documents = documents
    QueryRoot.document = document
    QueryRoot.query_status = query_status
    
    # Mutation resolvers
    Mutation.create_space = create_space
    Mutation.update_space = update_space
    Mutation.delete_space = delete_space
    Mutation.delete_document = delete_document
    Mutation.submit_query = submit_query
    Mutation.cancel_query = cancel_query
    
    # Subscription resolvers (Phase 3)
    Subscription.query_updates = query_updates
    Subscription.document_added = document_added
    Subscription.query_completed = query_completed
    Subscription.space_events = space_events
