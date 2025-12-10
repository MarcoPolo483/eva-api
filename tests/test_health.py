"""Tests for health check endpoints."""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test basic health check endpoint.

    Args:
        client: Test client fixture
    """
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data


def test_health_check_structure(client: TestClient) -> None:
    """Test health check response structure.

    Args:
        client: Test client fixture
    """
    response = client.get("/health")
    data = response.json()

    # Verify all required fields present
    assert "status" in data
    assert "version" in data
    assert "timestamp" in data

    # Verify data types
    assert isinstance(data["status"], str)
    assert isinstance(data["version"], str)
    assert isinstance(data["timestamp"], str)


def test_readiness_check(client: TestClient) -> None:
    """Test readiness check endpoint.

    Args:
        client: Test client fixture
    """
    response = client.get("/health/ready")

    assert response.status_code == 200
    data = response.json()

    assert "ready" in data
    assert "checks" in data
    assert "timestamp" in data


def test_readiness_check_structure(client: TestClient) -> None:
    """Test readiness check response structure.

    Args:
        client: Test client fixture
    """
    response = client.get("/health/ready")
    data = response.json()

    # Verify all required fields
    assert "ready" in data
    assert "checks" in data
    assert "timestamp" in data

    # Verify data types
    assert isinstance(data["ready"], bool)
    assert isinstance(data["checks"], dict)
    assert isinstance(data["timestamp"], str)

    # Verify checks structure
    checks = data["checks"]
    assert "api" in checks
    assert "database" in checks
    assert "redis" in checks


def test_readiness_check_contains_api(client: TestClient) -> None:
    """Test that readiness check includes API status.

    Args:
        client: Test client fixture
    """
    response = client.get("/health/ready")
    data = response.json()

    assert data["checks"]["api"] == "ok"


def test_health_endpoint_accepts_only_get(client: TestClient) -> None:
    """Test that health endpoint only accepts GET requests.

    Args:
        client: Test client fixture
    """
    response = client.post("/health")
    assert response.status_code == 405  # Method Not Allowed


def test_readiness_endpoint_accepts_only_get(client: TestClient) -> None:
    """Test that readiness endpoint only accepts GET requests.

    Args:
        client: Test client fixture
    """
    response = client.post("/health/ready")
    assert response.status_code == 405  # Method Not Allowed


def test_health_check_response_headers(client: TestClient) -> None:
    """Test that health check includes proper response headers.

    Args:
        client: Test client fixture
    """
    response = client.get("/health")

    # Should have request ID from middleware
    assert "x-request-id" in response.headers
    assert "x-process-time" in response.headers


def test_readiness_check_response_headers(client: TestClient) -> None:
    """Test that readiness check includes proper response headers.

    Args:
        client: Test client fixture
    """
    response = client.get("/health/ready")

    # Should have request ID from middleware
    assert "x-request-id" in response.headers
    assert "x-process-time" in response.headers
