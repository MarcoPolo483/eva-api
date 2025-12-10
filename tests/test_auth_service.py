"""Tests for Azure AD authentication service."""

import pytest

from eva_api.services.auth_service import AzureADService


def test_azure_ad_service_initialization(test_settings) -> None:
    """Test Azure AD service initialization."""
    service = AzureADService(test_settings)

    assert service.settings == test_settings


def test_azure_ad_service_b2c_credential(test_settings) -> None:
    """Test Azure AD B2C credential property."""
    service = AzureADService(test_settings)

    credential = service.b2c_credential
    assert credential is not None

    # Verify cached
    assert service.b2c_credential is credential


def test_azure_ad_service_entra_credential(test_settings) -> None:
    """Test Azure Entra ID credential property."""
    service = AzureADService(test_settings)

    credential = service.entra_credential
    assert credential is not None

    # Verify cached
    assert service.entra_credential is credential


@pytest.mark.asyncio
async def test_get_access_token_placeholder(test_settings) -> None:
    """Test get_access_token returns placeholder (not yet implemented)."""
    service = AzureADService(test_settings)

    result = await service.get_access_token(
        grant_type="client_credentials",
        client_id="test-client",
        client_secret="test-secret",
        scope="test-scope",
    )

    assert result["access_token"] == "placeholder_token"
    assert result["token_type"] == "Bearer"
    assert result["expires_in"] == 3600


@pytest.mark.asyncio
async def test_verify_jwt_token_placeholder(test_settings) -> None:
    """Test verify_jwt_token with mock token."""
    service = AzureADService(test_settings)

    # Create a simple JWT for testing (no signature verification in Phase 1)
    import jwt
    token_data = {
        "sub": "test-user",
        "tid": "test-tenant",
        "scp": "spaces:read spaces:write",
        "exp": 9999999999,
        "iat": 1234567890,
        "iss": "https://test.b2clogin.com",
        "aud": "test-audience",
    }
    token = jwt.encode(token_data, "secret", algorithm="HS256")

    claims = await service.verify_jwt_token(token)

    assert claims.sub == "test-user"
    assert claims.tenant_id == "test-tenant"
    assert "spaces:read" in claims.scopes
    assert "spaces:write" in claims.scopes
