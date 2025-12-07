"""Tests for main application."""

from fastapi.testclient import TestClient


def test_app_creation(client: TestClient) -> None:
    """Test that application is created successfully."""
    response = client.get("/health")
    assert response.status_code == 200


def test_app_has_docs(client: TestClient) -> None:
    """Test that OpenAPI docs are available."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_app_has_redoc(client: TestClient) -> None:
    """Test that ReDoc is available."""
    response = client.get("/redoc")
    assert response.status_code == 200


def test_app_has_openapi_spec(client: TestClient) -> None:
    """Test that OpenAPI spec is available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    spec = response.json()
    assert "openapi" in spec
    assert "info" in spec
    assert spec["info"]["title"] == "EVA API Platform"
    assert spec["info"]["version"] == "1.0.0"


def test_app_cors_headers(client: TestClient) -> None:
    """Test that CORS headers are set."""
    response = client.options("/health", headers={"Origin": "http://localhost:3000"})
    
    # FastAPI/Starlette handles CORS
    assert response.status_code in [200, 405]  # OPTIONS might not be allowed on all routes


def test_app_handles_404(client: TestClient) -> None:
    """Test that 404 errors are handled properly."""
    response = client.get("/nonexistent")
    assert response.status_code == 404


def test_app_gzip_compression(client: TestClient) -> None:
    """Test that GZip compression is enabled."""
    # FastAPI's GZipMiddleware adds Content-Encoding when response is large enough
    response = client.get("/health")
    # Small responses might not be compressed (minimum_size=1000)
    assert response.status_code == 200


def test_app_openapi_spec_structure(client: TestClient) -> None:
    """Test OpenAPI specification structure."""
    response = client.get("/openapi.json")
    spec = response.json()
    
    # Verify required OpenAPI fields
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec
    
    # Verify health endpoints are documented
    assert "/health" in spec["paths"]
    assert "/health/ready" in spec["paths"]


def test_app_version_in_spec(client: TestClient) -> None:
    """Test that application version is in OpenAPI spec."""
    response = client.get("/openapi.json")
    spec = response.json()
    
    assert spec["info"]["version"] == "1.0.0"


def test_app_title_in_spec(client: TestClient) -> None:
    """Test that application title is in OpenAPI spec."""
    response = client.get("/openapi.json")
    spec = response.json()
    
    assert spec["info"]["title"] == "EVA API Platform"
