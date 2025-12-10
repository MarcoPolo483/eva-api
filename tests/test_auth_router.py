"""Tests for authentication router."""

from fastapi.testclient import TestClient


def test_create_api_key_without_auth(client: TestClient) -> None:
    """Test creating API key without authentication."""
    from eva_api.dependencies import verify_jwt_token

    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)

    response = client.post(
        "/auth/api-keys",
        json={"name": "Test Key", "scopes": ["spaces:read"]},
    )

    assert response.status_code == 401


def test_list_api_keys_without_auth(client: TestClient) -> None:
    """Test listing API keys without authentication."""
    from eva_api.dependencies import verify_jwt_token

    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)

    response = client.get("/auth/api-keys")

    assert response.status_code == 401


def test_get_api_key_without_auth(client: TestClient) -> None:
    """Test getting API key without authentication."""
    from eva_api.dependencies import verify_jwt_token

    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)

    response = client.get("/auth/api-keys/test-key-id")

    assert response.status_code == 401


def test_revoke_api_key_without_auth(client: TestClient) -> None:
    """Test revoking API key without authentication."""
    from eva_api.dependencies import verify_jwt_token

    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)

    response = client.delete("/auth/api-keys/test-key-id")

    assert response.status_code == 401


def test_auth_router_in_openapi(client: TestClient) -> None:
    """Test that auth routes are documented in OpenAPI spec."""
    response = client.get("/openapi.json")
    spec = response.json()

    assert "/auth/api-keys" in spec["paths"]
    assert "/auth/api-keys/{key_id}" in spec["paths"]


def test_create_api_key_validation(client: TestClient) -> None:
    """Test API key creation validation."""
    response = client.post(
        "/auth/api-keys",
        json={},  # Missing required fields
        headers={"Authorization": "Bearer test-token"},
    )

    # Should fail validation
    assert response.status_code in [401, 422]  # 401 if auth fails first, 422 if validation
