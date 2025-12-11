"""
GraphQL schema definition using Strawberry.

Defines all GraphQL types, inputs, queries, mutations, and subscriptions.
"""

from collections.abc import AsyncGenerator
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

import strawberry

# Avoid circular imports by using TYPE_CHECKING
if TYPE_CHECKING:
    pass


# ============================================================================
# Space Types
# ============================================================================

@strawberry.type
class Space:
    """GraphQL type for Space."""

    id: UUID
    name: str
    description: Optional[str]
    tenant_id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    document_count: int
    metadata: Optional[strawberry.scalars.JSON] = None
    tags: list[str] = strawberry.field(default_factory=list)


@strawberry.input
class CreateSpaceInput:
    """Input for creating a space."""

    name: str
    description: Optional[str] = None
    metadata: Optional[strawberry.scalars.JSON] = None
    tags: list[str] = strawberry.field(default_factory=list)


@strawberry.input
class UpdateSpaceInput:
    """Input for updating a space."""

    name: Optional[str] = None
    description: Optional[str] = None
    metadata: Optional[strawberry.scalars.JSON] = None
    tags: Optional[list[str]] = None


@strawberry.type
class SpaceConnection:
    """Paginated list of spaces."""

    items: list[Space]
    cursor: Optional[str]
    has_more: bool
    total_count: int


# ============================================================================
# Document Types
# ============================================================================

@strawberry.type
class Document:
    """GraphQL type for Document."""

    id: UUID
    space_id: UUID
    filename: str
    content_type: str
    size_bytes: int
    blob_url: str
    blob_name: str
    created_by: str
    created_at: datetime
    metadata: Optional[strawberry.scalars.JSON] = None


@strawberry.type
class DocumentConnection:
    """Paginated list of documents."""

    items: list[Document]
    cursor: Optional[str]
    has_more: bool
    total_count: int


# ============================================================================
# Query Types
# ============================================================================

@strawberry.enum
class QueryStatus(Enum):
    """Status of a query."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@strawberry.type
class QueryResult:
    """Result of a completed query."""

    answer: str
    sources: list[UUID]
    document_count: int
    generated_at: datetime


@strawberry.type
class Query:
    """GraphQL type for Query."""

    id: UUID
    space_id: UUID
    question: str
    status: QueryStatus
    created_by: str
    created_at: datetime
    updated_at: datetime
    parameters: Optional[strawberry.scalars.JSON] = None
    result: Optional[QueryResult] = None
    error_message: Optional[str] = None


@strawberry.input
class SubmitQueryInput:
    """Input for submitting a query."""

    space_id: UUID
    question: str
    parameters: Optional[strawberry.scalars.JSON] = None


# ============================================================================
# Query Root
# ============================================================================

@strawberry.type
class QueryRoot:
    """Root query type for read operations."""

    # Lazy import to avoid circular dependency - import inside class body
    @strawberry.field(description="List all spaces with pagination")
    async def spaces(self, info: strawberry.types.Info, limit: int = 20, cursor: Optional[str] = None) -> "SpaceConnection":
        from eva_api.graphql.resolvers import spaces as _spaces
        return await _spaces(info, limit, cursor)

    @strawberry.field(description="Get a single space by ID")
    async def space(self, info: strawberry.types.Info, id: UUID) -> Optional["Space"]:
        from eva_api.graphql.resolvers import space as _space
        return await _space(info, id)

    @strawberry.field(description="List documents in a space")
    async def documents(self, info: strawberry.types.Info, space_id: UUID, limit: int = 20, cursor: Optional[str] = None) -> "DocumentConnection":
        from eva_api.graphql.resolvers import documents as _documents
        return await _documents(info, space_id, limit, cursor)

    @strawberry.field(description="Get a single document by ID")
    async def document(self, info: strawberry.types.Info, id: UUID) -> Optional["Document"]:
        from eva_api.graphql.resolvers import document as _document
        return await _document(info, id)

    @strawberry.field(description="Get query status and result")
    async def query_status(self, info: strawberry.types.Info, id: UUID) -> Optional["Query"]:
        from eva_api.graphql.resolvers import query_status as _query_status
        return await _query_status(info, id)


# ============================================================================
# Root Mutation Type
# ============================================================================

@strawberry.type
class Mutation:
    """Root mutation type for write operations."""

    @strawberry.field(description="Create a new space")
    async def create_space(self, info: strawberry.types.Info, input: "CreateSpaceInput") -> "Space":
        from eva_api.graphql.resolvers import create_space as _create_space
        return await _create_space(info, input)

    @strawberry.field(description="Update an existing space")
    async def update_space(self, info: strawberry.types.Info, id: UUID, input: "UpdateSpaceInput") -> "Space":
        from eva_api.graphql.resolvers import update_space as _update_space
        return await _update_space(info, id, input)

    @strawberry.field(description="Delete a space")
    async def delete_space(self, info: strawberry.types.Info, id: UUID) -> bool:
        from eva_api.graphql.resolvers import delete_space as _delete_space
        return await _delete_space(info, id)

    @strawberry.field(description="Delete a document")
    async def delete_document(self, info: strawberry.types.Info, id: UUID) -> bool:
        from eva_api.graphql.resolvers import delete_document as _delete_document
        return await _delete_document(info, id)

    @strawberry.field(description="Submit a new query for processing")
    async def submit_query(self, info: strawberry.types.Info, input: "SubmitQueryInput") -> "Query":
        from eva_api.graphql.resolvers import submit_query as _submit_query
        return await _submit_query(info, input)

    @strawberry.field(description="Cancel a pending or processing query")
    async def cancel_query(self, info: strawberry.types.Info, id: UUID) -> bool:
        from eva_api.graphql.resolvers import cancel_query as _cancel_query
        return await _cancel_query(info, id)


# ============================================================================
# Event Types for Subscriptions (Phase 3)
# ============================================================================

@strawberry.enum
class SpaceEventType(Enum):
    """Type of space event."""
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


@strawberry.type
class SpaceEvent:
    """Event emitted when space changes occur."""

    event_type: SpaceEventType
    space: Optional[Space]  # None for deleted events
    space_id: UUID
    tenant_id: str
    timestamp: datetime


# ============================================================================
# Root Subscription Type (Phase 3 - Real-time Events)
# ============================================================================

@strawberry.type
class Subscription:
    """Root subscription type for real-time updates.

    Phase 3 subscriptions for webhooks and real-time notifications:
    - Document events (added, processed, deleted)
    - Query events (submitted, completed, failed)
    - Space events (created, updated, deleted)
    """

    @strawberry.field(description="Subscribe to query status updates for a specific query")
    async def query_updates(self, info: strawberry.types.Info, id: UUID) -> AsyncGenerator[Query, None]:
        """Real-time updates for a specific query as it progresses."""
        from eva_api.graphql.resolvers import query_updates as _query_updates
        async for update in _query_updates(info, id):
            yield update

    @strawberry.field(description="Subscribe to all document events in a space")
    async def document_added(self, info: strawberry.types.Info, space_id: UUID) -> AsyncGenerator[Document, None]:
        """Real-time notification when documents are added to a space.

        Emits: Document object when uploaded and processed
        Use case: Live document feed, file monitoring
        """
        from eva_api.graphql.resolvers import document_added as _document_added
        async for document in _document_added(info, space_id):
            yield document

    @strawberry.field(description="Subscribe to query completion events in a space")
    async def query_completed(self, info: strawberry.types.Info, space_id: UUID) -> AsyncGenerator[Query, None]:
        """Real-time notification when queries complete in a space.

        Emits: Query object when processing finishes (success or failure)
        Use case: Live query dashboard, analytics feed
        """
        from eva_api.graphql.resolvers import query_completed as _query_completed
        async for query in _query_completed(info, space_id):
            yield query

    @strawberry.field(description="Subscribe to all space events for tenant")
    async def space_events(self, info: strawberry.types.Info) -> AsyncGenerator[SpaceEvent, None]:
        """Real-time notification of space lifecycle events.

        Emits: SpaceEvent (created, updated, deleted)
        Use case: Admin dashboard, audit logging
        """
        from eva_api.graphql.resolvers import space_events as _space_events
        async for event in _space_events(info):
            yield event


# ============================================================================
# Schema Definition
# ============================================================================

schema = strawberry.Schema(
    query=QueryRoot,
    mutation=Mutation,
    subscription=Subscription,
)
