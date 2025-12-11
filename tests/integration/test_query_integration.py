"""
Integration tests for Query service with Azure OpenAI.

Tests RAG pattern and full query processing pipeline.
"""

import asyncio
from io import BytesIO
from uuid import uuid4

import pytest

from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.query_service import QueryService


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.asyncio
async def test_query_rag_pipeline(
    query_service: QueryService,
    cosmos_service: CosmosDBService,
    blob_service: BlobStorageService,
):
    """Test full RAG pipeline: document upload → embedding → query → answer."""
    # Create space
    space_data = await cosmos_service.create_space(
        name="RAG Test Space",
        description="Integration test for RAG",
        tenant_id="test-tenant",
        created_by="integration-test",
    )
    space_id = uuid4(space_data["id"])

    try:
        # Upload test document
        doc_content = b"""
        The EVA Suite is a powerful AI platform.
        It includes document management, query processing, and GraphQL APIs.
        EVA uses Azure OpenAI for natural language understanding.
        """

        doc_data = await blob_service.upload_document(
            space_id=space_id,
            filename="eva-info.txt",
            content=BytesIO(doc_content),
            content_type="text/plain",
        )

        doc_id = uuid4(doc_data["doc_id"])

        # Create document metadata
        await cosmos_service.create_document_metadata(
            doc_id=doc_id,
            space_id=space_id,
            filename="eva-info.txt",
            content_type="text/plain",
            size_bytes=len(doc_content),
            blob_url=doc_data["blob_url"],
            blob_name=doc_data["blob_name"],
            created_by="integration-test",
        )

        # Process query
        query_id = await query_service.process_query(
            space_id=space_id,
            query_text="What is the EVA Suite?",
            created_by="integration-test",
        )

        assert query_id is not None

        # Wait for processing (background task)
        await asyncio.sleep(3)

        # Check query status
        query_data = await cosmos_service.container_queries.read_item(
            item=str(query_id),
            partition_key=str(space_id),
        )

        assert query_data is not None
        assert query_data["query_text"] == "What is the EVA Suite?"
        assert query_data["status"] in ["completed", "processing"]

        if query_data["status"] == "completed":
            assert "answer" in query_data
            assert len(query_data["answer"]) > 0
            # Verify answer contains relevant info
            answer_lower = query_data["answer"].lower()
            assert "eva" in answer_lower or "platform" in answer_lower

    finally:
        # Clean up
        await cosmos_service.delete_space(space_id)


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.asyncio
async def test_query_status_tracking(
    query_service: QueryService,
    cosmos_service: CosmosDBService,
):
    """Test query status updates during processing."""
    # Create space
    space_data = await cosmos_service.create_space(
        name="Status Test Space",
        description="Test status tracking",
        tenant_id="test-tenant",
        created_by="integration-test",
    )
    space_id = uuid4(space_data["id"])

    try:
        # Submit query
        query_id = await query_service.process_query(
            space_id=space_id,
            query_text="Test query for status tracking",
            created_by="integration-test",
        )

        # Check initial status
        query_data = await cosmos_service.container_queries.read_item(
            item=str(query_id),
            partition_key=str(space_id),
        )

        assert query_data["status"] in ["pending", "processing", "completed"]

        # Wait and check again
        await asyncio.sleep(2)
        query_data = await cosmos_service.container_queries.read_item(
            item=str(query_id),
            partition_key=str(space_id),
        )

        # Status should progress
        assert query_data["status"] in ["processing", "completed"]

    finally:
        # Clean up
        await cosmos_service.delete_space(space_id)


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.asyncio
async def test_query_context_building(
    query_service: QueryService,
    cosmos_service: CosmosDBService,
    blob_service: BlobStorageService,
):
    """Test retrieval and context building for queries."""
    # Create space
    space_data = await cosmos_service.create_space(
        name="Context Test Space",
        description="Test context building",
        tenant_id="test-tenant",
        created_by="integration-test",
    )
    space_id = uuid4(space_data["id"])

    try:
        # Upload multiple documents
        docs = [
            ("Python is a programming language.", "python.txt"),
            ("FastAPI is a modern web framework.", "fastapi.txt"),
            ("Azure provides cloud services.", "azure.txt"),
        ]

        for content, filename in docs:
            doc_data = await blob_service.upload_document(
                space_id=space_id,
                filename=filename,
                content=BytesIO(content.encode()),
                content_type="text/plain",
            )

            await cosmos_service.create_document_metadata(
                doc_id=uuid4(doc_data["doc_id"]),
                space_id=space_id,
                filename=filename,
                content_type="text/plain",
                size_bytes=len(content),
                blob_url=doc_data["blob_url"],
                blob_name=doc_data["blob_name"],
                created_by="integration-test",
            )

        # Query about specific topic
        query_id = await query_service.process_query(
            space_id=space_id,
            query_text="What is FastAPI?",
            created_by="integration-test",
        )

        await asyncio.sleep(3)

        # Check that context was built
        query_data = await cosmos_service.container_queries.read_item(
            item=str(query_id),
            partition_key=str(space_id),
        )

        if query_data["status"] == "completed":
            # Answer should reference FastAPI
            assert "fastapi" in query_data["answer"].lower() or "framework" in query_data["answer"].lower()

    finally:
        # Clean up
        await cosmos_service.delete_space(space_id)


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.asyncio
async def test_query_error_handling(
    query_service: QueryService,
    cosmos_service: CosmosDBService,
):
    """Test error handling in query processing."""
    # Create space
    space_data = await cosmos_service.create_space(
        name="Error Test Space",
        description="Test error handling",
        tenant_id="test-tenant",
        created_by="integration-test",
    )
    space_id = uuid4(space_data["id"])

    try:
        # Query with no documents (should handle gracefully)
        query_id = await query_service.process_query(
            space_id=space_id,
            query_text="Query with no documents",
            created_by="integration-test",
        )

        await asyncio.sleep(2)

        # Should complete even with no documents
        query_data = await cosmos_service.container_queries.read_item(
            item=str(query_id),
            partition_key=str(space_id),
        )

        # Status should be completed or failed (not stuck in processing)
        assert query_data["status"] in ["completed", "failed"]

    finally:
        # Clean up
        await cosmos_service.delete_space(space_id)
