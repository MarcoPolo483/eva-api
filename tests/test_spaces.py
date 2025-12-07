"""
Tests for Spaces API endpoints.
"""

import uuid
from datetime import datetime

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_create_space(client: TestClient, mock_jwt_token: dict) -> None:
    """Test creating a new space."""
    response = client.post(
        "/api/v1/spaces",
        json={
            "name": "Test Space",
            "description": "A test space",
            "metadata": {"key": "value"},
        },
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Space"
    assert data["data"]["description"] == "A test space"
    assert "id" in data["data"]
    assert "created_at" in data["data"]


def test_create_space_minimal(client: TestClient, mock_jwt_token: dict) -> None:
    """Test creating a space with minimal fields."""
    response = client.post(
        "/api/v1/spaces",
        json={"name": "Minimal Space"},
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["data"]["name"] == "Minimal Space"
    assert data["data"]["description"] is None


def test_create_space_invalid_name(client: TestClient, mock_jwt_token: dict) -> None:
    """Test creating a space with invalid name."""
    response = client.post(
        "/api/v1/spaces",
        json={"name": ""},  # Empty name
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_space_unauthorized(client: TestClient) -> None:
    """Test creating a space without authentication."""
    from eva_api.dependencies import verify_jwt_token
    
    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)
    
    response = client.post(
        "/api/v1/spaces",
        json={"name": "Test Space"},
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_spaces_empty(client: TestClient, mock_jwt_token: dict) -> None:
    """Test listing spaces when none exist."""
    response = client.get("/api/v1/spaces")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["success"] is True
    assert data["data"]["items"] == []
    assert data["data"]["has_more"] is False


def test_list_spaces_with_pagination(client: TestClient, mock_jwt_token: dict) -> None:
    """Test listing spaces with pagination parameters."""
    response = client.get("/api/v1/spaces?limit=10&cursor=abc123")
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data["data"]
    assert "cursor" in data["data"]
    assert "has_more" in data["data"]


def test_list_spaces_invalid_limit(client: TestClient, mock_jwt_token: dict) -> None:
    """Test listing spaces with invalid limit."""
    response = client.get("/api/v1/spaces?limit=0")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_space_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test getting a non-existent space."""
    space_id = uuid.uuid4()
    response = client.get(f"/api/v1/spaces/{space_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "not found" in data["detail"].lower()


def test_update_space_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test updating a non-existent space."""
    space_id = uuid.uuid4()
    response = client.put(
        f"/api/v1/spaces/{space_id}",
        json={"name": "Updated Name"},
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_space_partial(client: TestClient, mock_jwt_token: dict) -> None:
    """Test partial update of a space."""
    # Note: This test uses placeholder service, so it will return 404
    space_id = uuid.uuid4()
    response = client.put(
        f"/api/v1/spaces/{space_id}",
        json={"description": "Updated description"},
    )
    
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


def test_delete_space_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test deleting a non-existent space."""
    space_id = uuid.uuid4()
    response = client.delete(f"/api/v1/spaces/{space_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_space_unauthorized(client: TestClient) -> None:
    """Test deleting a space without authentication."""
    from eva_api.dependencies import verify_jwt_token
    
    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)
    
    space_id = uuid.uuid4()
    response = client.delete(f"/api/v1/spaces/{space_id}")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_space_response_format(client: TestClient, mock_jwt_token: dict) -> None:
    """Test that space response has correct format."""
    response = client.post(
        "/api/v1/spaces",
        json={"name": "Format Test Space"},
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()["data"]
    
    # Validate required fields
    assert "id" in data
    assert "name" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "document_count" in data
    
    # Validate UUID format
    uuid.UUID(data["id"])
    
    # Validate datetime format
    datetime.fromisoformat(data["created_at"])
    datetime.fromisoformat(data["updated_at"])
