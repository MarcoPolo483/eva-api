"""
Integration tests for Cosmos DB service.

Tests actual operations against Azure Cosmos DB.
"""

from uuid import uuid4

import pytest

from eva_api.services.cosmos_service import CosmosDBService


@pytest.mark.integration
@pytest.mark.cosmos
@pytest.mark.asyncio
async def test_cosmos_create_and_get_space(cosmos_service: CosmosDBService):
    """Test creating and retrieving a space from Cosmos DB."""
    # Create space
    space_id = uuid4()
    space_data = await cosmos_service.create_space(
        name=f"Integration Test Space {space_id}",
        description="Test space for integration testing",
        tenant_id="test-tenant",
        created_by="integration-test",
        metadata={"test": True},
        tags=["integration", "test"],
    )

    assert space_data is not None
    assert space_data["name"].startswith("Integration Test Space")
    assert space_data["tenant_id"] == "test-tenant"
    assert space_data["document_count"] == 0

    # Retrieve space
    retrieved = await cosmos_service.get_space(uuid4(space_data["id"]))
    assert retrieved is not None
    assert retrieved["id"] == space_data["id"]
    assert retrieved["name"] == space_data["name"]

    # Clean up
    await cosmos_service.delete_space(uuid4(space_data["id"]))


@pytest.mark.integration
@pytest.mark.cosmos
@pytest.mark.asyncio
async def test_cosmos_list_spaces_pagination(cosmos_service: CosmosDBService):
    """Test listing spaces with pagination."""
    # Create multiple test spaces
    space_ids = []
    for i in range(3):
        space_data = await cosmos_service.create_space(
            name=f"Pagination Test Space {i}",
            description=f"Test space {i}",
            tenant_id="test-tenant",
            created_by="integration-test",
        )
        space_ids.append(space_data["id"])

    try:
        # List with limit
        spaces, cursor, has_more = await cosmos_service.list_spaces(limit=2)
        assert len(spaces) >= 2

        # If there are more, test pagination
        if has_more and cursor:
            more_spaces, next_cursor, _ = await cosmos_service.list_spaces(
                limit=2,
                continuation_token=cursor
            )
            assert len(more_spaces) >= 1
            # Ensure no duplicates
            first_ids = {s["id"] for s in spaces}
            second_ids = {s["id"] for s in more_spaces}
            assert len(first_ids & second_ids) == 0
    finally:
        # Clean up
        for space_id in space_ids:
            await cosmos_service.delete_space(uuid4(space_id))


@pytest.mark.integration
@pytest.mark.cosmos
@pytest.mark.asyncio
async def test_cosmos_update_space(cosmos_service: CosmosDBService):
    """Test updating a space."""
    # Create space
    space_data = await cosmos_service.create_space(
        name="Original Name",
        description="Original description",
        tenant_id="test-tenant",
        created_by="integration-test",
    )
    space_id = uuid4(space_data["id"])

    try:
        # Update space
        updated = await cosmos_service.update_space(
            space_id,
            name="Updated Name",
            description="Updated description",
            tags=["updated"],
        )

        assert updated is not None
        assert updated["name"] == "Updated Name"
        assert updated["description"] == "Updated description"
        assert "updated" in updated["tags"]
    finally:
        # Clean up
        await cosmos_service.delete_space(space_id)


@pytest.mark.integration
@pytest.mark.cosmos
@pytest.mark.asyncio
async def test_cosmos_document_count(cosmos_service: CosmosDBService):
    """Test atomic document count operations."""
    # Create space
    space_data = await cosmos_service.create_space(
        name="Document Count Test",
        description="Test document counting",
        tenant_id="test-tenant",
        created_by="integration-test",
    )
    space_id = uuid4(space_data["id"])

    try:
        # Increment count
        await cosmos_service.increment_document_count(space_id)
        space = await cosmos_service.get_space(space_id)
        assert space["document_count"] == 1

        # Increment again
        await cosmos_service.increment_document_count(space_id)
        space = await cosmos_service.get_space(space_id)
        assert space["document_count"] == 2

        # Decrement
        await cosmos_service.decrement_document_count(space_id)
        space = await cosmos_service.get_space(space_id)
        assert space["document_count"] == 1
    finally:
        # Clean up
        await cosmos_service.delete_space(space_id)


@pytest.mark.integration
@pytest.mark.cosmos
@pytest.mark.asyncio
async def test_cosmos_document_metadata(cosmos_service: CosmosDBService):
    """Test document metadata operations."""
    # Create space first
    space_data = await cosmos_service.create_space(
        name="Doc Metadata Test",
        description="Test document metadata",
        tenant_id="test-tenant",
        created_by="integration-test",
    )
    space_id = uuid4(space_data["id"])

    try:
        # Create document metadata
        doc_id = uuid4()
        doc_data = await cosmos_service.create_document_metadata(
            doc_id=doc_id,
            space_id=space_id,
            filename="test.pdf",
            content_type="application/pdf",
            size_bytes=1024,
            blob_url="https://test.blob.core.windows.net/test",
            blob_name="test/test.pdf",
            created_by="integration-test",
        )

        assert doc_data is not None
        assert doc_data["filename"] == "test.pdf"
        assert doc_data["size_bytes"] == 1024

        # Retrieve document metadata
        retrieved = await cosmos_service.get_document_metadata(doc_id, space_id)
        assert retrieved is not None
        assert retrieved["id"] == str(doc_id)

        # List documents in space
        docs, _, _ = await cosmos_service.list_documents(space_id, limit=10)
        assert len(docs) >= 1
        assert any(d["id"] == str(doc_id) for d in docs)

        # Delete document metadata
        await cosmos_service.delete_document_metadata(doc_id, space_id)
        retrieved = await cosmos_service.get_document_metadata(doc_id, space_id)
        assert retrieved is None
    finally:
        # Clean up
        await cosmos_service.delete_space(space_id)
