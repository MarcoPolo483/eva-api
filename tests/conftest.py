"""Pytest configuration and fixtures for EVA API tests."""

import pytest
from fastapi.testclient import TestClient

from eva_api.config import Settings, get_settings
from eva_api.main import create_application


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with safe defaults.
    
    Returns:
        Settings: Test configuration
    """
    return Settings(
        environment="development",
        debug=True,
        log_level="DEBUG",
        azure_ad_b2c_tenant_id="test-tenant",
        azure_ad_b2c_client_id="test-client",
        azure_ad_b2c_client_secret="test-secret",
        azure_ad_b2c_authority="https://test.b2clogin.com/test/B2C_1_signin",
        azure_entra_tenant_id="test-tenant",
        azure_entra_client_id="test-client",
        azure_entra_client_secret="test-secret",
        cosmos_db_endpoint="https://test.documents.azure.com:443/",
        cosmos_db_key="test-key",
        redis_host="localhost",
        redis_port=6379,
        rate_limit_enabled=False,  # Disable for tests
    )


@pytest.fixture
def app(test_settings: Settings):
    """Create FastAPI application for testing.
    
    Args:
        test_settings: Test settings
        
    Returns:
        FastAPI: Application instance
    """
    from eva_api.dependencies import verify_jwt_token
    
    # Override settings dependency
    application = create_application()
    application.dependency_overrides[get_settings] = lambda: test_settings
    
    # Override JWT verification for tests
    def mock_verify_jwt_token():
        return {"sub": "test-user", "tenant_id": "test-tenant"}
    
    application.dependency_overrides[verify_jwt_token] = mock_verify_jwt_token
    
    return application


@pytest.fixture
def client(app) -> TestClient:
    """Create test client.
    
    Args:
        app: FastAPI application
        
    Returns:
        TestClient: Test client instance
    """
    # Pass app as positional argument (compatible with both old and new Starlette)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_jwt_token() -> str:
    """Create mock JWT token for testing.
    
    Returns:
        str: Mock JWT token
    """
    # This is a placeholder token for testing
    # In real tests, we would generate valid JWT tokens
    return "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXIiLCJ0ZW5hbnRfaWQiOiJ0ZXN0LXRlbmFudCJ9.test"


@pytest.fixture
def mock_api_key() -> str:
    """Create mock API key for testing.
    
    Returns:
        str: Mock API key
    """
    return "sk_test_1234567890abcdef"
