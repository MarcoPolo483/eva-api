"""Authentication router for EVA API Platform.

Handles API key management and OAuth 2.0 token endpoints.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from eva_api.config import Settings, get_settings
from eva_api.dependencies import VerifiedJWTToken
from eva_api.models.auth import APIKeyCreate, APIKeyInfo, APIKeyResponse
from eva_api.services.api_key_service import APIKeyService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/api-keys",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create API Key",
    description="Create a new API key for programmatic access",
)
async def create_api_key(
    request: APIKeyCreate,
    token: VerifiedJWTToken,
    settings: Settings = Depends(get_settings),
) -> APIKeyResponse:
    """Create a new API key.

    Requires JWT authentication. The API key is only shown once.

    Args:
        request: API key creation request
        token: Verified JWT token (from dependency)
        settings: Application settings

    Returns:
        APIKeyResponse: Created API key
    """
    tenant_id = token.get("tenant_id", "")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not found in token",
        )

    api_key_service = APIKeyService(settings)
    return await api_key_service.create_api_key(tenant_id, request)


@router.get(
    "/api-keys",
    response_model=list[APIKeyInfo],
    status_code=status.HTTP_200_OK,
    summary="List API Keys",
    description="List all API keys for the authenticated tenant",
)
async def list_api_keys(
    token: VerifiedJWTToken,
    settings: Settings = Depends(get_settings),
) -> list[APIKeyInfo]:
    """List all API keys for the authenticated tenant.

    Args:
        token: Verified JWT token (from dependency)
        settings: Application settings

    Returns:
        list[APIKeyInfo]: List of API keys
    """
    tenant_id = token.get("tenant_id", "")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not found in token",
        )

    api_key_service = APIKeyService(settings)
    return await api_key_service.list_api_keys(tenant_id)


@router.get(
    "/api-keys/{key_id}",
    response_model=APIKeyInfo,
    status_code=status.HTTP_200_OK,
    summary="Get API Key",
    description="Get information about a specific API key",
)
async def get_api_key(
    key_id: str,
    token: VerifiedJWTToken,
    settings: Settings = Depends(get_settings),
) -> APIKeyInfo:
    """Get API key information.

    Args:
        key_id: API key ID
        token: Verified JWT token (from dependency)
        settings: Application settings

    Returns:
        APIKeyInfo: API key information

    Raises:
        HTTPException: If key not found
    """
    tenant_id = token.get("tenant_id", "")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not found in token",
        )

    api_key_service = APIKeyService(settings)
    key_info = await api_key_service.get_api_key(key_id, tenant_id)

    if not key_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found",
        )

    return key_info


@router.delete(
    "/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke API Key",
    description="Revoke an API key (cannot be undone)",
)
async def revoke_api_key(
    key_id: str,
    token: VerifiedJWTToken,
    settings: Settings = Depends(get_settings),
) -> None:
    """Revoke an API key.

    Args:
        key_id: API key ID
        token: Verified JWT token (from dependency)
        settings: Application settings

    Raises:
        HTTPException: If key not found
    """
    tenant_id = token.get("tenant_id", "")

    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID not found in token",
        )

    api_key_service = APIKeyService(settings)
    success = await api_key_service.revoke_api_key(key_id, tenant_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found",
        )
