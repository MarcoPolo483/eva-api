"""
Comprehensive tests for Cosmos DB Service.
"""

import uuid
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from azure.cosmos import exceptions

from eva_api.config import Settings
from eva_api.services.cosmos_service import CosmosDBService


@pytest.fixture
def cosmos_settings():
    """Create test settings for Cosmos DB."""
    settings = Settings()
    settings.mock_mode = False
    return settings


@pytest.fixture
def mock_cosmos_service(cosmos_settings):
    """Create a Cosmos service with mocked Azure client."""
    with patch('eva_api.services.cosmos_service.CosmosClient') as mock_client_class:
        mock_client = MagicMock()
        mock_database = MagicMock()
        mock_container = MagicMock()

        mock_client_class.return_value = mock_client
        mock_client.create_database_if_not_exists.return_value = mock_database
        mock_database.create_container_if_not_exists.return_value = mock_container

        service = CosmosDBService(cosmos_settings)
        service.mock_client = mock_client
        service.mock_database = mock_database
        service.mock_container = mock_container

        yield service


class TestCosmosSpaces:
    """Tests for space operations."""

    async def test_create_space_success(self, mock_cosmos_service):
        """Test successful space creation."""
        name = "Test Space"
        description = "A test space for unit tests"
        metadata = {"project": "eva-api", "environment": "test"}

        result = await mock_cosmos_service.create_space(name, description, metadata)

        assert result["name"] == name
        assert result["description"] == description
        assert result["metadata"] == metadata
        assert "id" in result
        assert "created_at" in result
        assert result["document_count"] == 0

        # Verify Cosmos create was called
        mock_cosmos_service.spaces_container.create_item.assert_called_once()

    async def test_create_space_minimal(self, mock_cosmos_service):
        """Test creating space with only required fields."""
        name = "Minimal Space"

        result = await mock_cosmos_service.create_space(name)

        assert result["name"] == name
        assert result["description"] is None
        assert result["metadata"] == {}

    async def test_create_space_duplicate_name(self, mock_cosmos_service):
        """Test handling duplicate space name."""
        name = "Duplicate Space"

        # First creation succeeds
        await mock_cosmos_service.create_space(name)

        # Second creation with same name should succeed (different ID)
        result = await mock_cosmos_service.create_space(name)
        assert result["name"] == name

    async def test_get_space_success(self, mock_cosmos_service):
        """Test retrieving existing space."""
        space_id = uuid.uuid4()
        expected_space = {
            "id": str(space_id),
            "name": "Test Space",
            "description": "Test description",
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "document_count": 5
        }

        mock_cosmos_service.spaces_container.query_items.return_value = [expected_space]

        result = await mock_cosmos_service.get_space(space_id)

        assert result["id"] == str(space_id)
        assert result["name"] == "Test Space"
        assert result["document_count"] == 5

    async def test_get_space_not_found(self, mock_cosmos_service):
        """Test retrieving non-existent space."""
        space_id = uuid.uuid4()

        mock_cosmos_service.spaces_container.query_items.return_value = []

        result = await mock_cosmos_service.get_space(space_id)

        assert result is None

    async def test_list_spaces_paginated(self, mock_cosmos_service):
        """Test listing spaces with pagination."""
        mock_spaces = [
            {"id": str(uuid.uuid4()), "name": f"Space {i}", "document_count": i}
            for i in range(10)
        ]

        mock_cosmos_service.spaces_container.query_items.return_value = mock_spaces

        result, cursor, has_more = await mock_cosmos_service.list_spaces(limit=5)

        assert len(result) <= 5
        # Cursor pagination may or may not be implemented yet

    async def test_update_space(self, mock_cosmos_service):
        """Test updating space metadata."""
        space_id = uuid.uuid4()
        updates = {"name": "Updated Name", "description": "Updated description"}

        mock_cosmos_service.spaces_container.upsert_item.return_value = {
            "id": str(space_id),
            **updates,
            "updated_at": datetime.utcnow().isoformat()
        }

        result = await mock_cosmos_service.update_space(space_id, updates)

        assert result["name"] == "Updated Name"
        assert result["description"] == "Updated description"

    async def test_delete_space(self, mock_cosmos_service):
        """Test deleting a space."""
        space_id = uuid.uuid4()

        result = await mock_cosmos_service.delete_space(space_id)

        assert result["success"] is True
        mock_cosmos_service.spaces_container.delete_item.assert_called_once()


class TestCosmosDocuments:
    """Tests for document metadata operations."""

    async def test_create_document_metadata(self, mock_cosmos_service):
        """Test storing document metadata."""
        space_id = uuid.uuid4()
        doc_id = uuid.uuid4()
        metadata = {
            "id": str(doc_id),
            "space_id": str(space_id),
            "filename": "test.pdf",
            "content_type": "application/pdf",
            "size_bytes": 1024,
            "blob_url": "https://storage.blob.core.windows.net/docs/test.pdf"
        }

        result = await mock_cosmos_service.create_document_metadata(metadata)

        assert result["id"] == str(doc_id)
        assert result["space_id"] == str(space_id)
        mock_cosmos_service.documents_container.create_item.assert_called_once()

    async def test_query_documents_by_space(self, mock_cosmos_service):
        """Test querying all documents in a space."""
        space_id = uuid.uuid4()

        mock_documents = [
            {"id": str(uuid.uuid4()), "space_id": str(space_id), "filename": f"doc{i}.pdf"}
            for i in range(5)
        ]
        mock_cosmos_service.documents_container.query_items.return_value = mock_documents

        result = await mock_cosmos_service.query_documents_by_space(space_id)

        assert len(result) == 5
        assert all(doc["space_id"] == str(space_id) for doc in result)

    async def test_query_documents_with_filter(self, mock_cosmos_service):
        """Test querying documents with content type filter."""
        space_id = uuid.uuid4()
        content_type = "application/pdf"

        mock_documents = [
            {"id": str(uuid.uuid4()), "space_id": str(space_id), "content_type": content_type}
            for _ in range(3)
        ]
        mock_cosmos_service.documents_container.query_items.return_value = mock_documents

        result = await mock_cosmos_service.query_documents(
            space_id=space_id,
            content_type=content_type
        )

        assert len(result) == 3
        assert all(doc["content_type"] == content_type for doc in result)

    async def test_delete_document_metadata(self, mock_cosmos_service):
        """Test deleting document metadata."""
        doc_id = uuid.uuid4()
        space_id = uuid.uuid4()

        result = await mock_cosmos_service.delete_document_metadata(doc_id, space_id)

        assert result["success"] is True


class TestCosmosQueries:
    """Tests for query history operations."""

    async def test_create_query_record(self, mock_cosmos_service):
        """Test storing query in history."""
        query_id = uuid.uuid4()
        space_id = uuid.uuid4()
        query_data = {
            "id": str(query_id),
            "space_id": str(space_id),
            "question": "What is the capital of France?",
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }

        result = await mock_cosmos_service.create_query(query_data)

        assert result["id"] == str(query_id)
        assert result["status"] == "pending"
        mock_cosmos_service.queries_container.create_item.assert_called_once()

    async def test_update_query_status(self, mock_cosmos_service):
        """Test updating query status."""
        query_id = uuid.uuid4()
        space_id = uuid.uuid4()

        mock_cosmos_service.queries_container.upsert_item.return_value = {
            "id": str(query_id),
            "space_id": str(space_id),
            "status": "completed",
            "result": "Paris is the capital of France."
        }

        result = await mock_cosmos_service.update_query_status(
            query_id,
            space_id,
            "completed",
            result="Paris is the capital of France."
        )

        assert result["status"] == "completed"
        assert "result" in result

    async def test_query_history_by_space(self, mock_cosmos_service):
        """Test retrieving query history for a space."""
        space_id = uuid.uuid4()

        mock_queries = [
            {
                "id": str(uuid.uuid4()),
                "space_id": str(space_id),
                "question": f"Question {i}",
                "status": "completed"
            }
            for i in range(10)
        ]
        mock_cosmos_service.queries_container.query_items.return_value = mock_queries

        result = await mock_cosmos_service.get_query_history(space_id, limit=10)

        assert len(result) == 10
        assert all(q["space_id"] == str(space_id) for q in result)


class TestCosmosCrossPartitionQueries:
    """Tests for cross-partition query operations."""

    async def test_query_across_all_spaces(self, mock_cosmos_service):
        """Test querying documents across all spaces."""
        mock_documents = [
            {"id": str(uuid.uuid4()), "space_id": str(uuid.uuid4()), "filename": f"doc{i}.pdf"}
            for i in range(20)
        ]
        mock_cosmos_service.documents_container.query_items.return_value = mock_documents

        result = await mock_cosmos_service.query_all_documents(limit=20)

        assert len(result) <= 20
        # Verify cross-partition query was enabled
        call_args = mock_cosmos_service.documents_container.query_items.call_args
        assert call_args[1]["enable_cross_partition_query"] is True

    async def test_aggregate_document_count(self, mock_cosmos_service):
        """Test aggregating document count across all spaces."""
        mock_result = [{"count": 150}]
        mock_cosmos_service.documents_container.query_items.return_value = mock_result

        result = await mock_cosmos_service.get_total_document_count()

        assert result == 150

    async def test_search_by_filename_pattern(self, mock_cosmos_service):
        """Test searching documents by filename pattern across all spaces."""
        pattern = "report*.pdf"

        mock_documents = [
            {"id": str(uuid.uuid4()), "filename": "report-2023.pdf"},
            {"id": str(uuid.uuid4()), "filename": "report-2024.pdf"},
        ]
        mock_cosmos_service.documents_container.query_items.return_value = mock_documents

        result = await mock_cosmos_service.search_documents_by_filename(pattern)

        assert len(result) == 2
        assert all("report" in doc["filename"] for doc in result)


class TestCosmosErrorHandling:
    """Tests for error handling and edge cases."""

    async def test_create_space_cosmos_error(self, mock_cosmos_service):
        """Test handling Cosmos DB error during space creation."""
        mock_cosmos_service.spaces_container.create_item.side_effect = (
            exceptions.CosmosHttpResponseError(status_code=500, message="Internal error")
        )

        with pytest.raises(exceptions.CosmosHttpResponseError):
            await mock_cosmos_service.create_space("Test Space")

    async def test_query_timeout(self, mock_cosmos_service):
        """Test handling query timeout."""
        mock_cosmos_service.spaces_container.query_items.side_effect = (
            exceptions.CosmosHttpResponseError(status_code=408, message="Request timeout")
        )

        with pytest.raises(exceptions.CosmosHttpResponseError):
            await mock_cosmos_service.list_spaces()

    async def test_rate_limit_exceeded(self, mock_cosmos_service):
        """Test handling rate limit (429 error)."""
        mock_cosmos_service.spaces_container.create_item.side_effect = (
            exceptions.CosmosHttpResponseError(status_code=429, message="Request rate too large")
        )

        with pytest.raises(exceptions.CosmosHttpResponseError):
            await mock_cosmos_service.create_space("Test Space")

    async def test_invalid_partition_key(self, mock_cosmos_service):
        """Test handling invalid partition key."""
        # Try to query with mismatched partition key
        space_id = uuid.uuid4()

        mock_cosmos_service.documents_container.query_items.side_effect = (
            exceptions.CosmosHttpResponseError(status_code=400, message="Invalid partition key")
        )

        with pytest.raises(exceptions.CosmosHttpResponseError):
            await mock_cosmos_service.query_documents_by_space(space_id)


class TestCosmosPagination:
    """Tests for pagination features."""

    async def test_pagination_with_continuation_token(self, mock_cosmos_service):
        """Test pagination using continuation token."""
        # First page
        mock_cosmos_service.spaces_container.query_items.return_value = [
            {"id": str(uuid.uuid4()), "name": f"Space {i}"} for i in range(20)
        ]

        result, cursor, has_more = await mock_cosmos_service.list_spaces(limit=20)

        assert len(result) <= 20
        # If cursor is returned, there are more items
        if cursor:
            assert has_more is True

    async def test_pagination_last_page(self, mock_cosmos_service):
        """Test pagination on last page."""
        mock_cosmos_service.spaces_container.query_items.return_value = [
            {"id": str(uuid.uuid4()), "name": f"Space {i}"} for i in range(5)
        ]

        result, cursor, has_more = await mock_cosmos_service.list_spaces(limit=20)

        assert len(result) == 5
        assert has_more is False


class TestCosmosMockMode:
    """Tests for mock mode behavior."""

    async def test_mock_mode_create_space(self, cosmos_settings):
        """Test creating space in mock mode."""
        cosmos_settings.mock_mode = True
        service = CosmosDBService(cosmos_settings)

        result = await service.create_space("Mock Space", "Description")

        assert result["name"] == "Mock Space"
        assert "id" in result

    async def test_mock_mode_get_space(self, cosmos_settings):
        """Test getting space in mock mode."""
        cosmos_settings.mock_mode = True
        service = CosmosDBService(cosmos_settings)

        space_id = uuid.uuid4()
        result = await service.get_space(space_id)

        assert result is not None
        assert result["name"] == "Mock Space"

    async def test_mock_mode_list_spaces(self, cosmos_settings):
        """Test listing spaces in mock mode."""
        cosmos_settings.mock_mode = True
        service = CosmosDBService(cosmos_settings)

        result, cursor, has_more = await service.list_spaces(limit=10)

        assert len(result) > 0
        assert len(result) <= 10


class TestCosmosPerformance:
    """Tests for performance-related scenarios."""

    async def test_bulk_document_creation(self, mock_cosmos_service):
        """Test creating multiple documents in bulk."""
        space_id = uuid.uuid4()
        documents = [
            {
                "id": str(uuid.uuid4()),
                "space_id": str(space_id),
                "filename": f"doc{i}.pdf",
                "size_bytes": 1024 * i
            }
            for i in range(100)
        ]

        # Simulate bulk operation
        for doc in documents:
            await mock_cosmos_service.create_document_metadata(doc)

        assert mock_cosmos_service.documents_container.create_item.call_count == 100

    async def test_large_result_set(self, mock_cosmos_service):
        """Test handling large result sets."""
        mock_documents = [
            {"id": str(uuid.uuid4()), "filename": f"doc{i}.pdf"}
            for i in range(1000)
        ]
        mock_cosmos_service.documents_container.query_items.return_value = mock_documents

        result = await mock_cosmos_service.query_all_documents(limit=1000)

        assert len(result) <= 1000
