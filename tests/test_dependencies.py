"""Tests for authentication dependencies."""

import pytest
from fastapi import HTTPException

from eva_api.dependencies import verify_api_key, verify_jwt_token


@pytest.mark.asyncio
async def test_verify_api_key_missing(test_settings) -> None:
    """Test API key verification with missing key."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key=None, settings=test_settings)

    assert exc_info.value.status_code == 401
    assert "API key required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_invalid_format(test_settings) -> None:
    """Test API key verification with invalid format."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(x_api_key="invalid_key", settings=test_settings)

    assert exc_info.value.status_code == 401
    assert "Invalid API key format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_valid_format(test_settings) -> None:
    """Test API key verification with valid format."""
    api_key = "sk_test_1234567890"
    result = await verify_api_key(x_api_key=api_key, settings=test_settings)

    assert result == api_key


@pytest.mark.asyncio
async def test_verify_jwt_token_missing() -> None:
    """Test JWT token verification with missing token."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(authorization=None)

    assert exc_info.value.status_code == 401
    assert "Authorization required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_jwt_token_invalid_format() -> None:
    """Test JWT token verification with invalid format."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(authorization="InvalidFormat token")

    assert exc_info.value.status_code == 401
    assert "Invalid authorization format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_jwt_token_empty_token() -> None:
    """Test JWT token verification with empty token."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_jwt_token(authorization="Bearer ")

    assert exc_info.value.status_code == 401
    assert "Token is empty" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_jwt_token_valid_format() -> None:
    """Test JWT token verification with valid format."""
    token = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.token"
    result = await verify_jwt_token(authorization=token)

    assert isinstance(result, dict)
    assert "sub" in result
    assert "tenant_id" in result
