"""Dependency injection for FastAPI routes.

Provides reusable dependencies for authentication, database connections,
and other shared resources.
"""

import logging
from typing import Annotated, Any

import jwt
from fastapi import Depends, Header, HTTPException, status

from eva_api.config import Settings, get_settings
from eva_api.models.auth import JWTClaims
from eva_api.services.auth_service import AzureADService
from eva_api.services.api_key_service import APIKeyService

logger = logging.getLogger(__name__)


async def get_current_settings() -> Settings:
    """Get application settings.
    
    Returns:
        Settings: Application configuration
    """
    return get_settings()


async def get_api_key_service(
    settings: Settings = Depends(get_current_settings),
) -> APIKeyService:
    """Get API key service instance.
    
    Args:
        settings: Application settings
        
    Returns:
        APIKeyService: API key management service
    """
    return APIKeyService(settings)


async def verify_api_key(
    x_api_key: Annotated[str | None, Header()] = None,
    settings: Settings = Depends(get_current_settings),
    api_key_service: APIKeyService = Depends(get_api_key_service),
) -> dict[str, Any]:
    """Verify API key from request header.
    
    Validates API key against Cosmos DB and returns metadata.
    
    Args:
        x_api_key: API key from X-API-Key header
        settings: Application settings
        api_key_service: API key management service
        
    Returns:
        dict: API key metadata (tenant_id, scopes, name, key_id)
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Provide X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    # Allow demo API key for development
    if x_api_key != "demo-api-key" and not x_api_key.startswith(settings.api_key_prefix):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format",
        )
    
    # Allow demo API key for development (bypass database check)
    if x_api_key == "demo-api-key":
        return {
            "tenant_id": "demo-tenant",
            "key_id": "demo-key-id",
            "scopes": ["read", "write"],
            "name": "Demo API Key",
        }
    
    # Verify API key with Cosmos DB
    try:
        metadata = await api_key_service.verify_api_key(x_api_key)
        if not metadata:
            logger.warning("API key verification failed - key not found or invalid")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired API key",
                headers={"WWW-Authenticate": "ApiKey"},
            )
        
        logger.info(f"API key verified for tenant {metadata['tenant_id']}")
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API key verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify API key",
        )


async def get_azure_ad_service(
    settings: Settings = Depends(get_current_settings),
) -> AzureADService:
    """Get Azure AD service instance.
    
    Args:
        settings: Application settings
        
    Returns:
        AzureADService: Azure AD authentication service
    """
    return AzureADService(settings)


async def verify_jwt_token(
    authorization: Annotated[str | None, Header()] = None,
    azure_ad_service: AzureADService = Depends(get_azure_ad_service),
) -> JWTClaims:
    """Verify JWT token from Authorization header using Azure AD.
    
    Args:
        authorization: Bearer token from Authorization header
        azure_ad_service: Azure AD service for token verification
        
    Returns:
        JWTClaims: Validated and decoded token claims
        
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
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is empty",
        )
    
    try:
        # Verify JWT with full Azure AD validation
        claims = await azure_ad_service.verify_jwt_token(token)
        logger.info(f"Successfully authenticated user: {claims.sub}")
        return claims
        
    except jwt.ExpiredSignatureError:
        logger.warning("JWT verification failed: Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Token expired"'},
        )
    except jwt.InvalidIssuerError:
        logger.error("JWT verification failed: Invalid issuer")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token issuer is invalid",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid issuer"'},
        )
    except jwt.InvalidAudienceError:
        logger.error("JWT verification failed: Invalid audience")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token audience is invalid",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token", error_description="Invalid audience"'},
        )
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except Exception as e:
        logger.error(f"Unexpected error during JWT verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during authentication",
        )


# Type aliases for cleaner route signatures
CurrentSettings = Annotated[Settings, Depends(get_current_settings)]
VerifiedAPIKey = Annotated[str, Depends(verify_api_key)]
VerifiedJWTToken = Annotated[JWTClaims, Depends(verify_jwt_token)]
