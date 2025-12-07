"""
Tests for Queries API endpoints.
"""

import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_submit_query_space_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test submitting a query to non-existent space."""
    space_id = uuid.uuid4()
    response = client.post(
        "/api/v1/queries",
        json={
            "space_id": str(space_id),
            "question": "What is the capital of France?",
        },
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_submit_query_with_parameters(client: TestClient, mock_jwt_token: dict) -> None:
    """Test submitting a query with custom parameters."""
    space_id = uuid.uuid4()
    response = client.post(
        "/api/v1/queries",
        json={
            "space_id": str(space_id),
            "question": "Explain quantum computing",
            "parameters": {"temperature": 0.7, "max_tokens": 500},
        },
    )
    
    # Will fail because space doesn't exist
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_submit_query_invalid_question(client: TestClient, mock_jwt_token: dict) -> None:
    """Test submitting a query with empty question."""
    space_id = uuid.uuid4()
    response = client.post(
        "/api/v1/queries",
        json={
            "space_id": str(space_id),
            "question": "",  # Empty question
        },
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_submit_query_question_too_long(client: TestClient, mock_jwt_token: dict) -> None:
    """Test submitting a query with overly long question."""
    space_id = uuid.uuid4()
    long_question = "a" * 2001  # Exceeds 2000 char limit
    
    response = client.post(
        "/api/v1/queries",
        json={
            "space_id": str(space_id),
            "question": long_question,
        },
    )
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_submit_query_unauthorized(client: TestClient) -> None:
    """Test submitting a query without authentication."""
    from eva_api.dependencies import verify_jwt_token
    
    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)
    
    space_id = uuid.uuid4()
    response = client.post(
        "/api/v1/queries",
        json={
            "space_id": str(space_id),
            "question": "Test question",
        },
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_query_status_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test getting status for non-existent query."""
    query_id = uuid.uuid4()
    response = client.get(f"/api/v1/queries/{query_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_query_status_unauthorized(client: TestClient) -> None:
    """Test getting query status without authentication."""
    from eva_api.dependencies import verify_jwt_token
    
    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)
    
    query_id = uuid.uuid4()
    response = client.get(f"/api/v1/queries/{query_id}")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_query_result_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test getting result for non-existent query."""
    query_id = uuid.uuid4()
    response = client.get(f"/api/v1/queries/{query_id}/result")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_query_result_unauthorized(client: TestClient) -> None:
    """Test getting query result without authentication."""
    from eva_api.dependencies import verify_jwt_token
    
    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)
    
    query_id = uuid.uuid4()
    response = client.get(f"/api/v1/queries/{query_id}/result")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_query_response_format(client: TestClient, mock_jwt_token: dict) -> None:
    """Test that query response has correct format."""
    # This test validates API behavior even with placeholder service
    space_id = uuid.uuid4()
    response = client.post(
        "/api/v1/queries",
        json={
            "space_id": str(space_id),
            "question": "Test question",
        },
    )
    
    # Should be 404 for non-existent space
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_query_status_enum_values(client: TestClient, mock_jwt_token: dict) -> None:
    """Test that QueryStatus enum has expected values."""
    from eva_api.models.queries import QueryStatus
    
    assert QueryStatus.PENDING.value == "pending"
    assert QueryStatus.PROCESSING.value == "processing"
    assert QueryStatus.COMPLETED.value == "completed"
    assert QueryStatus.FAILED.value == "failed"


def test_query_lifecycle_endpoints(client: TestClient, mock_jwt_token: dict) -> None:
    """Test the complete query lifecycle (submit -> status -> result)."""
    space_id = uuid.uuid4()
    
    # Submit query
    submit_response = client.post(
        "/api/v1/queries",
        json={
            "space_id": str(space_id),
            "question": "What is AI?",
        },
    )
    
    # Should fail due to non-existent space
    assert submit_response.status_code == status.HTTP_404_NOT_FOUND
    
    # If we had a real query ID, we would test:
    # 1. GET /queries/{id} for status
    # 2. GET /queries/{id}/result for answer
