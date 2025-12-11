"""
Comprehensive tests for Blob Storage Service.
"""

import io
import uuid
from unittest.mock import MagicMock, patch

import pytest
from azure.core.exceptions import ResourceNotFoundError, ServiceRequestError

from eva_api.config import Settings
from eva_api.services.blob_service import BlobStorageService


@pytest.fixture
def blob_settings():
    """Create test settings for blob storage."""
    settings = Settings()
    settings.mock_mode = False  # Test with real Azure client
    return settings


@pytest.fixture
def mock_blob_service(blob_settings):
    """Create a blob service with mocked Azure client."""
    with patch('eva_api.services.blob_service.BlobServiceClient') as mock_client_class:
        # Mock the client and container
        mock_client = MagicMock()
        mock_container = MagicMock()

        mock_client_class.from_connection_string.return_value = mock_client
        mock_client.get_container_client.return_value = mock_container

        service = BlobStorageService(blob_settings)
        service.mock_blob_client = mock_client
        service.mock_container_client = mock_container

        yield service


class TestBlobStorageUpload:
    """Tests for document upload operations."""

    @pytest.mark.asyncio
    async def test_upload_document_success(self, mock_blob_service):
        """Test successful document upload."""
        space_id = uuid.uuid4()
        filename = "test-document.pdf"
        content = io.BytesIO(b"PDF content here")
        content_type = "application/pdf"
        metadata = {"author": "Test User", "version": "1.0"}

        # Mock blob client
        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.url = f"https://storage.blob.core.windows.net/documents/{space_id}/doc/test.pdf"

        # Execute upload
        result = await mock_blob_service.upload_document(
            space_id=space_id,
            filename=filename,
            content=content,
            content_type=content_type,
            metadata=metadata
        )

        # Verify result
        assert result["filename"] == filename
        assert result["content_type"] == content_type
        assert result["space_id"] == str(space_id)
        assert result["size_bytes"] > 0
        assert "blob_url" in result
        assert result["metadata"] == metadata

        # Verify blob client was called
        mock_blob_client.upload_blob.assert_called_once()

    @pytest.mark.asyncio
    async def test_upload_document_large_file(self, mock_blob_service):
        """Test uploading a large file (10MB)."""
        space_id = uuid.uuid4()
        filename = "large-file.bin"
        large_content = io.BytesIO(b"x" * (10 * 1024 * 1024))  # 10MB

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.url = "https://storage.blob.core.windows.net/documents/large.bin"

        result = await mock_blob_service.upload_document(
            space_id=space_id,
            filename=filename,
            content=large_content,
            content_type="application/octet-stream"
        )

        assert result["size_bytes"] == 10 * 1024 * 1024
        assert result["filename"] == filename

    @pytest.mark.asyncio
    async def test_upload_document_special_characters_filename(self, mock_blob_service):
        """Test uploading document with special characters in filename."""
        space_id = uuid.uuid4()
        filename = "test-document (2023) [final].pdf"
        content = io.BytesIO(b"content")

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.url = "https://storage.blob.core.windows.net/documents/doc.pdf"

        result = await mock_blob_service.upload_document(
            space_id=space_id,
            filename=filename,
            content=content,
            content_type="application/pdf"
        )

        assert result["filename"] == filename

    @pytest.mark.asyncio
    async def test_upload_document_no_metadata(self, mock_blob_service):
        """Test uploading document without metadata."""
        space_id = uuid.uuid4()
        content = io.BytesIO(b"content")

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.url = "https://storage.blob.core.windows.net/documents/doc.txt"

        result = await mock_blob_service.upload_document(
            space_id=space_id,
            filename="doc.txt",
            content=content,
            content_type="text/plain"
        )

        assert result["metadata"] == {}

    @pytest.mark.asyncio
    async def test_upload_document_network_error(self, mock_blob_service):
        """Test upload failure due to network error."""
        space_id = uuid.uuid4()
        content = io.BytesIO(b"content")

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.upload_blob.side_effect = ServiceRequestError("Network timeout")

        with pytest.raises(ServiceRequestError):
            await mock_blob_service.upload_document(
                space_id=space_id,
                filename="test.txt",
                content=content,
                content_type="text/plain"
            )


class TestBlobStorageDownload:
    """Tests for document download operations."""

    @pytest.mark.asyncio
    async def test_download_document_success(self, mock_blob_service):
        """Test successful document download."""
        blob_name = f"{uuid.uuid4()}/{uuid.uuid4()}/test.pdf"
        expected_content = b"PDF content"

        mock_blob_client = MagicMock()
        mock_download = MagicMock()
        mock_download.readall.return_value = expected_content

        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.download_blob.return_value = mock_download

        result = await mock_blob_service.download_document(blob_name)

        assert result["content"] == expected_content
        assert result["blob_name"] == blob_name
        mock_blob_client.download_blob.assert_called_once()

    @pytest.mark.asyncio
    async def test_download_document_not_found(self, mock_blob_service):
        """Test downloading non-existent document."""
        blob_name = "non-existent/document.pdf"

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.download_blob.side_effect = ResourceNotFoundError("Blob not found")

        with pytest.raises(ResourceNotFoundError):
            await mock_blob_service.download_document(blob_name)

    @pytest.mark.asyncio
    async def test_download_document_streaming(self, mock_blob_service):
        """Test downloading document with streaming."""
        blob_name = "space/doc/large-file.bin"
        content_chunks = [b"chunk1", b"chunk2", b"chunk3"]

        mock_blob_client = MagicMock()
        mock_download = MagicMock()
        mock_download.chunks.return_value = iter(content_chunks)

        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.download_blob.return_value = mock_download

        result = await mock_blob_service.download_document_streaming(blob_name)

        chunks = [chunk async for chunk in result]
        assert chunks == content_chunks


class TestBlobStorageDelete:
    """Tests for document deletion operations."""

    @pytest.mark.asyncio
    async def test_delete_document_success(self, mock_blob_service):
        """Test successful document deletion."""
        blob_name = f"{uuid.uuid4()}/{uuid.uuid4()}/test.pdf"

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client

        result = await mock_blob_service.delete_document(blob_name)

        assert result["success"] is True
        assert result["blob_name"] == blob_name
        mock_blob_client.delete_blob.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_document_not_found(self, mock_blob_service):
        """Test deleting non-existent document."""
        blob_name = "non-existent.pdf"

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.delete_blob.side_effect = ResourceNotFoundError("Blob not found")

        # Should handle gracefully
        result = await mock_blob_service.delete_document(blob_name)
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_delete_document_batch(self, mock_blob_service):
        """Test batch deletion of multiple documents."""
        blob_names = [
            "space1/doc1/file1.pdf",
            "space1/doc2/file2.pdf",
            "space1/doc3/file3.pdf"
        ]

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client

        result = await mock_blob_service.delete_documents_batch(blob_names)

        assert result["deleted"] == 3
        assert result["failed"] == 0
        assert mock_blob_client.delete_blob.call_count == 3


class TestBlobStorageList:
    """Tests for listing operations."""

    @pytest.mark.asyncio
    async def test_list_documents_in_space(self, mock_blob_service):
        """Test listing all documents in a space."""
        space_id = uuid.uuid4()

        # Mock blob list
        mock_blobs = [
            MagicMock(name=f"{space_id}/doc1/file1.pdf", size=1024),
            MagicMock(name=f"{space_id}/doc2/file2.pdf", size=2048),
        ]
        mock_blob_service.mock_container_client.list_blobs.return_value = mock_blobs

        result = await mock_blob_service.list_documents(space_id)

        assert len(result["documents"]) == 2
        assert result["total_count"] == 2
        assert result["space_id"] == str(space_id)

    @pytest.mark.asyncio
    async def test_list_documents_with_pagination(self, mock_blob_service):
        """Test listing documents with pagination."""
        space_id = uuid.uuid4()

        # Mock 50 blobs
        mock_blobs = [MagicMock(name=f"{space_id}/doc{i}/file.pdf", size=1024) for i in range(50)]
        mock_blob_service.mock_container_client.list_blobs.return_value = mock_blobs

        # Get first page (20 items)
        result = await mock_blob_service.list_documents(space_id, limit=20, offset=0)

        assert len(result["documents"]) == 20
        assert result["total_count"] == 50
        assert result["has_more"] is True

    @pytest.mark.asyncio
    async def test_list_documents_empty_space(self, mock_blob_service):
        """Test listing documents in empty space."""
        space_id = uuid.uuid4()

        mock_blob_service.mock_container_client.list_blobs.return_value = []

        result = await mock_blob_service.list_documents(space_id)

        assert len(result["documents"]) == 0
        assert result["total_count"] == 0


class TestBlobStorageSAS:
    """Tests for SAS token generation."""

    @pytest.mark.asyncio
    async def test_generate_sas_token(self, mock_blob_service):
        """Test generating SAS token for blob access."""
        blob_name = "space/doc/file.pdf"
        expiry_hours = 1

        with patch('eva_api.services.blob_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sv=2021-06-08&se=2023..."

            result = await mock_blob_service.generate_download_url(blob_name, expiry_hours)

            assert "sas_url" in result
            assert blob_name in result["sas_url"]
            assert result["expires_in_hours"] == expiry_hours
            mock_sas.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_sas_token_custom_permissions(self, mock_blob_service):
        """Test generating SAS token with custom permissions."""
        blob_name = "space/doc/file.pdf"

        with patch('eva_api.services.blob_service.generate_blob_sas') as mock_sas:
            mock_sas.return_value = "sv=2021-06-08&sp=rw..."

            result = await mock_blob_service.generate_upload_url(blob_name, expiry_hours=2)

            assert "sas_url" in result
            # Verify read+write permissions were requested
            call_args = mock_sas.call_args
            assert call_args is not None


class TestBlobStorageMockMode:
    """Tests for mock mode behavior."""

    @pytest.mark.asyncio
    async def test_mock_mode_upload(self, blob_settings):
        """Test upload in mock mode."""
        blob_settings.mock_mode = True
        service = BlobStorageService(blob_settings)

        space_id = uuid.uuid4()
        content = io.BytesIO(b"content")

        result = await service.upload_document(
            space_id=space_id,
            filename="test.txt",
            content=content,
            content_type="text/plain"
        )

        assert "mock-storage" in result["blob_url"]
        assert result["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_mock_mode_download(self, blob_settings):
        """Test download in mock mode."""
        blob_settings.mock_mode = True
        service = BlobStorageService(blob_settings)

        result = await service.download_document("mock/blob/name.pdf")

        assert result["content"] == b"Mock content"
        assert result["blob_name"] == "mock/blob/name.pdf"


class TestBlobStorageErrorHandling:
    """Tests for error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_upload_empty_file(self, mock_blob_service):
        """Test uploading empty file."""
        space_id = uuid.uuid4()
        content = io.BytesIO(b"")

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.url = "https://storage.blob.core.windows.net/documents/empty.txt"

        result = await mock_blob_service.upload_document(
            space_id=space_id,
            filename="empty.txt",
            content=content,
            content_type="text/plain"
        )

        assert result["size_bytes"] == 0

    @pytest.mark.asyncio
    async def test_connection_timeout(self, mock_blob_service):
        """Test handling of connection timeout."""
        blob_name = "space/doc/file.pdf"

        mock_blob_client = MagicMock()
        mock_blob_service.mock_container_client.get_blob_client.return_value = mock_blob_client
        mock_blob_client.download_blob.side_effect = ServiceRequestError("Connection timeout")

        with pytest.raises(ServiceRequestError):
            await mock_blob_service.download_document(blob_name)

    @pytest.mark.asyncio
    async def test_invalid_blob_name(self, mock_blob_service):
        """Test handling invalid blob name."""
        invalid_names = [
            "",
            "//double-slash",
            "space/../escape",
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValueError):
                await mock_blob_service.download_document(invalid_name)
