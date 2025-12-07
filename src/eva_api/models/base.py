"""Base Pydantic models for EVA API.

Common models and response structures used across the API.
"""

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class HealthStatus(BaseModel):
    """Health check status response."""
    
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class HealthReadiness(BaseModel):
    """Detailed readiness check response."""
    
    ready: bool = Field(..., description="Whether the service is ready")
    checks: dict[str, str] = Field(default_factory=dict, description="Individual component checks")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class ErrorDetail(BaseModel):
    """Error detail for validation errors."""
    
    field: str = Field(..., description="Field that caused the error")
    issue: str = Field(..., description="Description of the issue")


class ErrorResponse(BaseModel):
    """Standardized error response."""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: list[ErrorDetail] | None = Field(None, description="Additional error details")


class MetaInfo(BaseModel):
    """Metadata about the API response."""
    
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


class PaginationInfo(BaseModel):
    """Pagination metadata."""
    
    cursor: str | None = Field(None, description="Cursor for next page")
    has_next: bool = Field(..., description="Whether more results are available")
    total: int | None = Field(None, description="Total number of results (if available)")


T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Generic success response wrapper."""
    
    success: bool = Field(True, description="Success indicator")
    data: T = Field(..., description="Response data")
    message: str | None = Field(None, description="Success message")
    meta: MetaInfo | None = Field(None, description="Response metadata")


class ErrorResponseWrapper(BaseModel):
    """Error response wrapper."""
    
    error: ErrorResponse = Field(..., description="Error information")
    meta: MetaInfo = Field(..., description="Response metadata")
