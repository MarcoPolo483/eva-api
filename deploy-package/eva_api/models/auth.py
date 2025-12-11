"""Authentication models for EVA API Platform.

Pydantic models for authentication requests and responses.
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    """OAuth 2.0 token request."""
    
    grant_type: Literal["client_credentials", "authorization_code"] = Field(
        ..., description="OAuth 2.0 grant type"
    )
    client_id: str = Field(..., description="Client ID")
    client_secret: str = Field(..., description="Client secret")
    scope: str | None = Field(None, description="Requested scopes")
    code: str | None = Field(None, description="Authorization code (for authorization_code grant)")
    redirect_uri: str | None = Field(None, description="Redirect URI (for authorization_code grant)")


class TokenResponse(BaseModel):
    """OAuth 2.0 token response."""
    
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    scope: str | None = Field(None, description="Granted scopes")
    refresh_token: str | None = Field(None, description="Refresh token (if applicable)")


class APIKeyCreate(BaseModel):
    """Request to create a new API key."""
    
    name: str = Field(..., description="Friendly name for the API key", min_length=1, max_length=100)
    scopes: list[str] = Field(
        default_factory=list,
        description="Permissions granted to this API key",
    )
    expires_at: datetime | None = Field(None, description="Optional expiration date")


class APIKeyResponse(BaseModel):
    """API key response (only shown once on creation)."""
    
    id: str = Field(..., description="API key ID")
    key: str = Field(..., description="API key value (only shown once)")
    name: str = Field(..., description="Friendly name")
    scopes: list[str] = Field(..., description="Granted permissions")
    created_at: datetime = Field(..., description="Creation timestamp")
    expires_at: datetime | None = Field(None, description="Expiration timestamp")


class APIKeyInfo(BaseModel):
    """API key information (without the actual key value)."""
    
    id: str = Field(..., description="API key ID")
    name: str = Field(..., description="Friendly name")
    scopes: list[str] = Field(..., description="Granted permissions")
    created_at: datetime = Field(..., description="Creation timestamp")
    last_used_at: datetime | None = Field(None, description="Last usage timestamp")
    expires_at: datetime | None = Field(None, description="Expiration timestamp")
    is_active: bool = Field(..., description="Whether the key is active")


class JWTClaims(BaseModel):
    """JWT token claims."""
    
    sub: str = Field(..., description="Subject (user ID)")
    tenant_id: str = Field(..., description="Tenant ID")
    scopes: list[str] = Field(default_factory=list, description="Granted scopes")
    exp: int = Field(..., description="Expiration time (Unix timestamp)")
    iat: int = Field(..., description="Issued at time (Unix timestamp)")
    iss: str = Field(..., description="Issuer")
    aud: str = Field(..., description="Audience")
