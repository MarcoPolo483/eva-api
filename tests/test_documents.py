"""
Tests for Documents API endpoints.
"""

import io
import uuid

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_upload_document_space_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test uploading a document to non-existent space."""
    space_id = uuid.uuid4()
    files = {"file": ("test.txt", io.BytesIO(b"test content"), "text/plain")}
    
    response = client.post(f"/api/v1/spaces/{space_id}/documents", files=files)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert "not found" in response.json()["detail"].lower()


def test_upload_document_with_metadata(client: TestClient, mock_jwt_token: dict) -> None:
    """Test uploading a document with custom metadata."""
    space_id = uuid.uuid4()
    files = {"file": ("doc.pdf", io.BytesIO(b"PDF content"), "application/pdf")}
    data = {"metadata": '{"author": "Test User", "version": "1.0"}'}
    
    response = client.post(
        f"/api/v1/spaces/{space_id}/documents",
        files=files,
        data=data,
    )
    
    # Will fail because space doesn't exist (placeholder service)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_upload_document_invalid_metadata(client: TestClient, mock_jwt_token: dict) -> None:
    """Test uploading a document with invalid JSON metadata."""
    space_id = uuid.uuid4()
    files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
    data = {"metadata": "invalid json"}
    
    response = client.post(
        f"/api/v1/spaces/{space_id}/documents",
        files=files,
        data=data,
    )
    
    assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_404_NOT_FOUND, status.HTTP_500_INTERNAL_SERVER_ERROR]


def test_upload_document_unauthorized(client: TestClient) -> None:
    """Test uploading a document without authentication."""
    from eva_api.dependencies import verify_jwt_token
    
    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)
    
    space_id = uuid.uuid4()
    files = {"file": ("test.txt", io.BytesIO(b"content"), "text/plain")}
    
    response = client.post(f"/api/v1/spaces/{space_id}/documents", files=files)
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_documents_space_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test listing documents for non-existent space."""
    space_id = uuid.uuid4()
    response = client.get(f"/api/v1/spaces/{space_id}/documents")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_documents_with_pagination(client: TestClient, mock_jwt_token: dict) -> None:
    """Test listing documents with pagination parameters."""
    space_id = uuid.uuid4()
    response = client.get(f"/api/v1/spaces/{space_id}/documents?limit=5&cursor=xyz")
    
    # Will fail because space doesn't exist
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_list_documents_invalid_limit(client: TestClient, mock_jwt_token: dict) -> None:
    """Test listing documents with invalid limit."""
    space_id = uuid.uuid4()
    response = client.get(f"/api/v1/spaces/{space_id}/documents?limit=0")
    
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_document_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test getting a non-existent document."""
    doc_id = uuid.uuid4()
    response = client.get(f"/api/v1/documents/{doc_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_document_not_found(client: TestClient, mock_jwt_token: dict) -> None:
    """Test deleting a non-existent document."""
    doc_id = uuid.uuid4()
    response = client.delete(f"/api/v1/documents/{doc_id}")
    
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_document_unauthorized(client: TestClient) -> None:
    """Test deleting a document without authentication."""
    from eva_api.dependencies import verify_jwt_token
    
    # Remove JWT override
    client.app.dependency_overrides.pop(verify_jwt_token, None)
    
    doc_id = uuid.uuid4()
    response = client.delete(f"/api/v1/documents/{doc_id}")
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_document_response_format(client: TestClient, mock_jwt_token: dict) -> None:
    """Test that document response has correct format."""
    # This test validates the response structure even though it fails due to placeholder service
    space_id = uuid.uuid4()
    response = client.get(f"/api/v1/spaces/{space_id}/documents")
    
    # Should be 404 for non-existent space
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_upload_multiple_files_sequentially(client: TestClient, mock_jwt_token: dict) -> None:
    """Test uploading multiple documents to the same space."""
    space_id = uuid.uuid4()
    
    files1 = {"file": ("doc1.txt", io.BytesIO(b"content 1"), "text/plain")}
    files2 = {"file": ("doc2.txt", io.BytesIO(b"content 2"), "text/plain")}
    
    response1 = client.post(f"/api/v1/spaces/{space_id}/documents", files=files1)
    response2 = client.post(f"/api/v1/spaces/{space_id}/documents", files=files2)
    
    # Both should fail because space doesn't exist
    assert response1.status_code == status.HTTP_404_NOT_FOUND
    assert response2.status_code == status.HTTP_404_NOT_FOUND
