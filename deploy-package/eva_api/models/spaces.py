"""
Pydantic models for Space resources.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SpaceCreate(BaseModel):
    """Request model for creating a new space."""

    name: str = Field(..., min_length=1, max_length=255, description="Space name")
    description: Optional[str] = Field(
        None, max_length=1000, description="Space description"
    )
    metadata: Optional[dict] = Field(None, description="Custom metadata")


class SpaceUpdate(BaseModel):
    """Request model for updating an existing space."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="Space name"
    )
    description: Optional[str] = Field(
        None, max_length=1000, description="Space description"
    )
    metadata: Optional[dict] = Field(None, description="Custom metadata")


class SpaceResponse(BaseModel):
    """Response model for a space."""

    id: UUID = Field(..., description="Space unique identifier")
    name: str = Field(..., description="Space name")
    description: Optional[str] = Field(None, description="Space description")
    metadata: Optional[dict] = Field(None, description="Custom metadata")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    document_count: int = Field(0, description="Number of documents in space")

    class Config:
        from_attributes = True


class SpaceListResponse(BaseModel):
    """Response model for paginated space list."""

    items: list[SpaceResponse] = Field(..., description="List of spaces")
    cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_more: bool = Field(False, description="Whether more items exist")
