"""
Integration tests for Blob Storage service.

Tests actual operations against Azure Blob Storage.
"""

from io import BytesIO
from uuid import uuid4

import pytest

from eva_api.services.blob_service import BlobStorageService


@pytest.mark.integration
@pytest.mark.blob
@pytest.mark.asyncio
async def test_blob_upload_and_download(blob_service: BlobStorageService):
    """Test uploading and downloading a blob."""
    space_id = uuid4()
    doc_id = uuid4()
    filename = "test-document.txt"
    content = b"This is test content for integration testing."

    # Upload
    doc_data = await blob_service.upload_document(
        space_id=space_id,
        filename=filename,
        content=BytesIO(content),
        content_type="text/plain",
        metadata={"test": "true"},
    )

    assert doc_data is not None
    assert doc_data["filename"] == filename
    assert doc_data["content_type"] == "text/plain"
    assert doc_data["size_bytes"] == len(content)
    assert "blob_url" in doc_data

    blob_name = doc_data["blob_name"]

    try:
        # Download
        downloaded = await blob_service.download_document(blob_name)
        assert downloaded == content
    finally:
        # Clean up
        await blob_service.delete_document(blob_name)


@pytest.mark.integration
@pytest.mark.blob
@pytest.mark.asyncio
async def test_blob_generate_sas_url(blob_service: BlobStorageService):
    """Test SAS URL generation."""
    space_id = uuid4()
    doc_id = uuid4()
    filename = "sas-test.txt"
    content = b"SAS URL test content"

    # Upload
    doc_data = await blob_service.upload_document(
        space_id=space_id,
        filename=filename,
        content=BytesIO(content),
        content_type="text/plain",
    )

    blob_name = doc_data["blob_name"]

    try:
        # Generate SAS URL
        sas_url = await blob_service.generate_sas_url(
            blob_name=blob_name,
            expiry_hours=1,
            permissions="r",
        )

        assert sas_url is not None
        assert "sig=" in sas_url  # SAS token present
        assert blob_name in sas_url
    finally:
        # Clean up
        await blob_service.delete_document(blob_name)


@pytest.mark.integration
@pytest.mark.blob
@pytest.mark.asyncio
async def test_blob_delete(blob_service: BlobStorageService):
    """Test blob deletion."""
    space_id = uuid4()
    filename = "delete-test.txt"
    content = b"Content to be deleted"

    # Upload
    doc_data = await blob_service.upload_document(
        space_id=space_id,
        filename=filename,
        content=BytesIO(content),
        content_type="text/plain",
    )

    blob_name = doc_data["blob_name"]

    # Verify exists
    downloaded = await blob_service.download_document(blob_name)
    assert downloaded is not None

    # Delete
    await blob_service.delete_document(blob_name)

    # Verify deleted
    downloaded = await blob_service.download_document(blob_name)
    assert downloaded is None


@pytest.mark.integration
@pytest.mark.blob
@pytest.mark.asyncio
async def test_blob_hierarchical_naming(blob_service: BlobStorageService):
    """Test hierarchical blob naming convention."""
    space_id = uuid4()
    doc_id = uuid4()
    filename = "hierarchical-test.pdf"
    content = b"PDF content"

    # Upload with specific IDs
    doc_data = await blob_service.upload_document(
        space_id=space_id,
        filename=filename,
        content=BytesIO(content),
        content_type="application/pdf",
    )

    blob_name = doc_data["blob_name"]

    try:
        # Verify naming structure: {space_id}/{doc_id}/{filename}
        assert str(space_id) in blob_name
        assert filename in blob_name
        parts = blob_name.split("/")
        assert len(parts) == 3  # space_id/doc_id/filename
    finally:
        # Clean up
        await blob_service.delete_document(blob_name)
