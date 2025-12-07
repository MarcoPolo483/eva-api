"""Dependency injection for FastAPI routes.

Provides reusable dependencies for authentication, database connections,
and other shared resources.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from eva_api.config import Settings, get_settings


async def get_current_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings: Application configuration
    """
    return get_settings()


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_current_settings),
) -> str:
    """Verify API key from request header.
    
    Args:
        x_api_key: API key from X-API-Key header
        settings: Application settings
        
    Returns:
        str: Validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if not x_api_key.startswith(settings.api_key_prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )
    
    # TODO: Verify API key against Cosmos DB in Phase 1.5
    # For now, just validate format
    
    return x_api_key


async def verify_jwt_token(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    """Verify JWT token from Authorization header.
    
    Args:
        authorization: Bearer token from Authorization header
        
    Returns:
        dict: Decoded token claims
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization required. Provide Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format. Use 'Bearer <token>'",
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    # TODO: Verify JWT signature against Azure AD in Phase 1.4
    # For now, just validate format
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is empty",
        )
    
    return {"sub": "placeholder", "tenant_id": "placeholder"}


# Type aliases for cleaner route signatures
CurrentSettings = Annotated[Settings, Depends(get_current_settings)]
VerifiedAPIKey = Annotated[str, Depends(verify_api_key)]
VerifiedJWTToken = Annotated[dict[str, str], Depends(verify_jwt_token)]
