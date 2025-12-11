"""
Pydantic models for Document resources.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Response model for a document."""

    id: UUID = Field(..., description="Document unique identifier")
    space_id: UUID = Field(..., description="Parent space identifier")
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type")
    size_bytes: int = Field(..., description="File size in bytes")
    blob_url: str = Field(..., description="Azure Blob Storage URL")
    metadata: Optional[dict] = Field(None, description="Custom metadata")
    created_at: datetime = Field(..., description="Upload timestamp")
    created_by: str = Field(..., description="User who uploaded document")

    class Config:
        from_attributes = True


class DocumentListResponse(BaseModel):
    """Response model for paginated document list."""

    items: list[DocumentResponse] = Field(..., description="List of documents")
    cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_more: bool = Field(False, description="Whether more items exist")
