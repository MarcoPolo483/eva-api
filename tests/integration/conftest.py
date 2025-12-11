"""
Integration tests configuration and fixtures.

These tests require actual Azure credentials and services.
Set environment variables before running:
- COSMOS_DB_ENDPOINT
- COSMOS_DB_KEY
- AZURE_STORAGE_ACCOUNT_NAME
- AZURE_STORAGE_ACCOUNT_KEY
- AZURE_OPENAI_ENDPOINT
- AZURE_OPENAI_KEY
"""

import os

import pytest

from eva_api.config import Settings
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.query_service import QueryService


@pytest.fixture(scope="session")
def integration_settings() -> Settings:
    """Create settings from environment variables for integration tests."""
    return Settings(
        environment="development",  # Use development for integration tests
        cosmos_db_endpoint=os.getenv("COSMOS_DB_ENDPOINT", ""),
        cosmos_db_key=os.getenv("COSMOS_DB_KEY", ""),
        azure_storage_account_name=os.getenv("AZURE_STORAGE_ACCOUNT_NAME", ""),
        azure_storage_account_key=os.getenv("AZURE_STORAGE_ACCOUNT_KEY", ""),
        azure_openai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
        azure_openai_key=os.getenv("AZURE_OPENAI_KEY", ""),
    )


@pytest.fixture
def cosmos_service(integration_settings: Settings) -> CosmosDBService:
    """Create Cosmos DB service with real credentials."""
    service = CosmosDBService(integration_settings)
    if not service.client:
        pytest.skip("Cosmos DB credentials not configured")
    return service


@pytest.fixture
def blob_service(integration_settings: Settings) -> BlobStorageService:
    """Create Blob Storage service with real credentials."""
    service = BlobStorageService(integration_settings)
    if not service.client:
        pytest.skip("Blob Storage credentials not configured")
    return service


@pytest.fixture
def query_service(
    integration_settings: Settings,
    cosmos_service: CosmosDBService,
    blob_service: BlobStorageService,
) -> QueryService:
    """Create Query service with real services."""
    service = QueryService(
        integration_settings,
        cosmos_service=cosmos_service,
        blob_service=blob_service,
    )
    if not service.openai_client:
        pytest.skip("Azure OpenAI credentials not configured")
    return service


def pytest_configure(config):
    """Register custom markers for integration tests."""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test requiring Azure credentials"
    )
    config.addinivalue_line(
        "markers", "cosmos: mark test as requiring Cosmos DB"
    )
    config.addinivalue_line(
        "markers", "blob: mark test as requiring Blob Storage"
    )
    config.addinivalue_line(
        "markers", "openai: mark test as requiring Azure OpenAI"
    )
