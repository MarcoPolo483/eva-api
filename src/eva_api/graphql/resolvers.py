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

class GraphQLContext:
    """Context object passed to all resolvers."""
    
    def __init__(
        self,
        cosmos_service: CosmosDBService,
        blob_service: BlobStorageService,
        query_service: QueryService,
        user_id: str,
        tenant_id: str,
    ):
        self.cosmos = cosmos_service
        self.blob = blob_service
        self.query = query_service
        self.user_id = user_id
        self.tenant_id = tenant_id


# ============================================================================
# Space Resolvers
# ============================================================================

@strawberry.field
async def spaces(
    info: Info,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> SpaceConnection:
    """List all spaces with pagination."""
    ctx: GraphQLContext = info.context
    
    items_raw, next_cursor, has_more = await ctx.cosmos.list_spaces(
        limit=limit,
        continuation_token=cursor,
    )
    
    items = [Space(**item) for item in items_raw]
    
    return SpaceConnection(
        items=items,
        cursor=next_cursor,
        has_more=has_more,
        total_count=len(items),  # Note: This is page count, not total
    )


@strawberry.field
async def space(info: Info, id: UUID) -> Optional[Space]:
    """Get a single space by ID."""
    ctx: GraphQLContext = info.context
    
    space_data = await ctx.cosmos.get_space(id)
    if not space_data:
        return None
    
    return Space(**space_data)


@strawberry.mutation
async def create_space(
    info: Info,
    input: CreateSpaceInput,
) -> Space:
    """Create a new space."""
    ctx: GraphQLContext = info.context
    
    space_data = await ctx.cosmos.create_space(
        name=input.name,
        description=input.description,
        tenant_id=ctx.tenant_id,
        created_by=ctx.user_id,
        metadata=input.metadata,
        tags=input.tags,
    )
    
    logger.info(f"Created space {space_data['id']} via GraphQL")
    return Space(**space_data)


@strawberry.mutation
async def update_space(
    info: Info,
    id: UUID,
    input: UpdateSpaceInput,
) -> Space:
    """Update an existing space."""
    ctx: GraphQLContext = info.context
    
    updates = {}
    if input.name is not None:
        updates["name"] = input.name
    if input.description is not None:
        updates["description"] = input.description
    if input.metadata is not None:
        updates["metadata"] = input.metadata
    if input.tags is not None:
        updates["tags"] = input.tags
    
    space_data = await ctx.cosmos.update_space(id, **updates)
    if not space_data:
        raise ValueError(f"Space {id} not found")
    
    logger.info(f"Updated space {id} via GraphQL")
    return Space(**space_data)


@strawberry.mutation
async def delete_space(info: Info, id: UUID) -> bool:
    """Delete a space."""
    ctx: GraphQLContext = info.context
    
    success = await ctx.cosmos.delete_space(id)
    
    if success:
        logger.info(f"Deleted space {id} via GraphQL")
    
    return success


# ============================================================================
# Document Resolvers
# ============================================================================

@strawberry.field
async def documents(
    info: Info,
    space_id: UUID,
    limit: int = 20,
    cursor: Optional[str] = None,
) -> DocumentConnection:
    """List documents in a space."""
    ctx: GraphQLContext = info.context
    
    items_raw, next_cursor, has_more = await ctx.cosmos.list_documents(
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


@strawberry.field
async def document(
    info: Info,
    id: UUID,
    space_id: UUID,
) -> Optional[Document]:
    """Get a single document by ID."""
    ctx: GraphQLContext = info.context
    
    doc_data = await ctx.cosmos.get_document_metadata(id, space_id)
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
    ctx: GraphQLContext = info.context
    
    # Get document metadata to find blob_name
    doc_data = await ctx.cosmos.get_document_metadata(id, space_id)
    if not doc_data:
        return False
    
    blob_name = doc_data.get("blob_name")
    
    # Delete from blob storage
    if blob_name:
        await ctx.blob.delete_document(blob_name)
    
    # Delete metadata from Cosmos DB
    await ctx.cosmos.delete_document_metadata(id, space_id)
    
    # Decrement space document count
    await ctx.cosmos.decrement_document_count(space_id)
    
    logger.info(f"Deleted document {id} via GraphQL")
    return True


# ============================================================================
# Query Resolvers
# ============================================================================

@strawberry.field
async def query_status(info: Info, id: UUID) -> Optional[Query]:
    """Get query status and result."""
    ctx: GraphQLContext = info.context
    
    query_data = await ctx.query.get_query_status(id)
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


@strawberry.mutation
async def submit_query(
    info: Info,
    input: SubmitQueryInput,
) -> Query:
    """Submit a new query for processing."""
    ctx: GraphQLContext = info.context
    
    query_data = await ctx.query.submit_query(
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


@strawberry.mutation
async def cancel_query(info: Info, id: UUID) -> bool:
    """Cancel a pending or processing query."""
    ctx: GraphQLContext = info.context
    
    success = await ctx.query.cancel_query(id)
    
    if success:
        logger.info(f"Cancelled query {id} via GraphQL")
    
    return success


# ============================================================================
# Subscription Resolvers
# ============================================================================

@strawberry.subscription
async def query_updates(
    info: Info,
    id: UUID,
) -> AsyncGenerator[Query, None]:
    """Subscribe to query status updates."""
    ctx: GraphQLContext = info.context
    
    # Poll for updates every 2 seconds
    # In production, use Redis Pub/Sub or Azure Service Bus for real-time events
    while True:
        query_data = await ctx.query.get_query_status(id)
        
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
    
    # Subscription resolvers
    Subscription.query_updates = query_updates
