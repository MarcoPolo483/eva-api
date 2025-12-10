"""Tests for API key service."""

import pytest

from eva_api.models.auth import APIKeyCreate
from eva_api.services.api_key_service import APIKeyService


@pytest.mark.asyncio
async def test_generate_api_key_format(test_settings) -> None:
    """Test that generated API keys have correct format."""
    service = APIKeyService(test_settings)
    api_key = service._generate_api_key()

    assert api_key.startswith(test_settings.api_key_prefix)
    assert len(api_key) > len(test_settings.api_key_prefix)


@pytest.mark.asyncio
async def test_generate_api_key_uniqueness(test_settings) -> None:
    """Test that generated API keys are unique."""
    service = APIKeyService(test_settings)
    key1 = service._generate_api_key()
    key2 = service._generate_api_key()

    assert key1 != key2


@pytest.mark.asyncio
async def test_create_api_key(test_settings) -> None:
    """Test creating an API key."""
    service = APIKeyService(test_settings)
    request = APIKeyCreate(
        name="Test Key",
        scopes=["spaces:read", "spaces:write"],
    )

    result = await service.create_api_key("test-tenant", request)

    assert result.name == "Test Key"
    assert result.scopes == ["spaces:read", "spaces:write"]
    assert result.key.startswith(test_settings.api_key_prefix)
    assert result.id is not None
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_create_api_key_with_expiration(test_settings) -> None:
    """Test creating an API key with expiration."""
    from datetime import datetime, timedelta

    service = APIKeyService(test_settings)
    expires_at = datetime.utcnow() + timedelta(days=30)
    request = APIKeyCreate(
        name="Expiring Key",
        scopes=["spaces:read"],
        expires_at=expires_at,
    )

    result = await service.create_api_key("test-tenant", request)

    assert result.expires_at == expires_at


@pytest.mark.asyncio
async def test_get_api_key_not_found(test_settings) -> None:
    """Test getting non-existent API key."""
    service = APIKeyService(test_settings)
    result = await service.get_api_key("nonexistent", "test-tenant")

    assert result is None


@pytest.mark.asyncio
async def test_list_api_keys_empty(test_settings) -> None:
    """Test listing API keys when none exist."""
    service = APIKeyService(test_settings)
    result = await service.list_api_keys("test-tenant")

    assert result == []


@pytest.mark.asyncio
async def test_revoke_api_key_not_found(test_settings) -> None:
    """Test revoking non-existent API key."""
    service = APIKeyService(test_settings)
    result = await service.revoke_api_key("nonexistent", "test-tenant")

    assert result is False


@pytest.mark.asyncio
async def test_verify_api_key_not_implemented(test_settings) -> None:
    """Test that verify_api_key returns None (not yet implemented)."""
    service = APIKeyService(test_settings)
    result = await service.verify_api_key("sk_test_123")

    assert result is None
