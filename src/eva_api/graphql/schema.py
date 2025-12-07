"""
GraphQL schema definition using Strawberry.

Defines all GraphQL types, inputs, queries, mutations, and subscriptions.
"""

import strawberry
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


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
# Root Query Type
# ============================================================================

@strawberry.type
class QueryRoot:
    """Root query type for read operations."""
    
    # Spaces
    spaces: SpaceConnection = strawberry.field(
        description="List all spaces with pagination"
    )
    space: Optional[Space] = strawberry.field(
        description="Get a single space by ID"
    )
    
    # Documents
    documents: DocumentConnection = strawberry.field(
        description="List documents in a space"
    )
    document: Optional[Document] = strawberry.field(
        description="Get a single document by ID"
    )
    
    # Queries
    query_status: Optional[Query] = strawberry.field(
        description="Get query status and result"
    )


# ============================================================================
# Root Mutation Type
# ============================================================================

@strawberry.type
class Mutation:
    """Root mutation type for write operations."""
    
    # Spaces
    create_space: Space = strawberry.field(
        description="Create a new space"
    )
    update_space: Space = strawberry.field(
        description="Update an existing space"
    )
    delete_space: bool = strawberry.field(
        description="Delete a space"
    )
    
    # Documents
    delete_document: bool = strawberry.field(
        description="Delete a document"
    )
    
    # Queries
    submit_query: Query = strawberry.field(
        description="Submit a new query for processing"
    )
    cancel_query: bool = strawberry.field(
        description="Cancel a pending or processing query"
    )


# ============================================================================
# Root Subscription Type
# ============================================================================

@strawberry.type
class Subscription:
    """Root subscription type for real-time updates."""
    
    query_updates: Query = strawberry.field(
        description="Subscribe to query status updates"
    )


# ============================================================================
# Schema Definition
# ============================================================================

schema = strawberry.Schema(
    query=QueryRoot,
    mutation=Mutation,
    subscription=Subscription,
)
