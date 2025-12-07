"""
Pydantic models for Query resources.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class QueryStatus(str, Enum):
    """Query processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class QueryRequest(BaseModel):
    """Request model for submitting a query."""

    space_id: UUID = Field(..., description="Space to query")
    question: str = Field(
        ..., min_length=1, max_length=2000, description="Natural language question"
    )
    parameters: Optional[dict] = Field(
        None, description="Additional query parameters (e.g., temperature, max_tokens)"
    )


class QueryResponse(BaseModel):
    """Response model for a query."""

    id: UUID = Field(..., description="Query unique identifier")
    space_id: UUID = Field(..., description="Parent space identifier")
    question: str = Field(..., description="Original question")
    status: QueryStatus = Field(..., description="Current processing status")
    created_at: datetime = Field(..., description="Submission timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    created_by: str = Field(..., description="User who submitted query")

    class Config:
        from_attributes = True


class QueryResult(BaseModel):
    """Response model for query result."""

    id: UUID = Field(..., description="Query unique identifier")
    status: QueryStatus = Field(..., description="Processing status")
    answer: Optional[str] = Field(None, description="Generated answer")
    sources: Optional[list[dict]] = Field(None, description="Source documents used")
    metadata: Optional[dict] = Field(None, description="Processing metadata")
    error: Optional[str] = Field(None, description="Error message if failed")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")
