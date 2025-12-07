"""
Azure Blob Storage service for document management.
"""

import logging
from datetime import datetime, timedelta
from typing import BinaryIO, Optional
from uuid import UUID, uuid4

from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas,
    ContentSettings
)
from azure.core.exceptions import ResourceNotFoundError

from eva_api.config import Settings

logger = logging.getLogger(__name__)


class BlobStorageService:
    """
    Service for interacting with Azure Blob Storage.
    
    Manages document uploads, downloads, and deletions.
    """

    def __init__(self, settings: Settings):
        """Initialize Blob Storage client."""
        self.settings = settings
        
        try:
            # Initialize Blob Storage client
            connection_string = (
                f"DefaultEndpointsProtocol=https;"
                f"AccountName={settings.azure_storage_account_name};"
                f"AccountKey={settings.azure_storage_account_key};"
                f"EndpointSuffix=core.windows.net"
            )
            
            self.client = BlobServiceClient.from_connection_string(connection_string)
            
            # Get/create container
            self.container_name = settings.azure_storage_container_documents
            self.container_client = self.client.get_container_client(self.container_name)
            
            # Create container if it doesn't exist
            try:
                self.container_client.create_container()
                logger.info(f"Created blob container: {self.container_name}")
            except Exception:
                pass  # Container already exists
            
            logger.info(f"BlobStorageService initialized: {self.container_name}")
            
        except Exception as e:
            logger.warning(f"Blob Storage initialization failed (will use placeholder): {e}")
            self.client = None
            self.container_client = None
            self.container_name = None

    async def upload_document(
        self,
        space_id: UUID,
        filename: str,
        content: BinaryIO,
        content_type: str,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Upload a document to blob storage.
        
        Returns:
            Document metadata including blob URL
        """
        doc_id = uuid4()
        now = datetime.utcnow()
        
        # Create blob name: space_id/doc_id/filename
        blob_name = f"{space_id}/{doc_id}/{filename}"
        
        if self.container_client:
            try:
                # Upload blob
                blob_client = self.container_client.get_blob_client(blob_name)
                
                # Read content and get size
                content_bytes = content.read()
                size_bytes = len(content_bytes)
                
                # Upload with content settings
                blob_client.upload_blob(
                    content_bytes,
                    content_settings=ContentSettings(content_type=content_type),
                    metadata=metadata or {}
                )
                
                # Get blob URL
                blob_url = blob_client.url
                
                logger.info(f"Uploaded document to blob storage: {doc_id}")
                
                return {
                    "id": str(doc_id),
                    "space_id": str(space_id),
                    "filename": filename,
                    "content_type": content_type,
                    "size_bytes": size_bytes,
                    "blob_url": blob_url,
                    "blob_name": blob_name,
                    "metadata": metadata or {},
                    "created_at": now.isoformat(),
                }
                
            except Exception as e:
                logger.error(f"Failed to upload document to blob storage: {e}")
                raise
        
        # Placeholder response if blob storage not available
        return {
            "id": str(doc_id),
            "space_id": str(space_id),
            "filename": filename,
            "content_type": content_type,
            "size_bytes": 0,
            "blob_url": f"https://placeholder.blob.core.windows.net/{space_id}/{doc_id}/{filename}",
            "blob_name": blob_name,
            "metadata": metadata or {},
            "created_at": now.isoformat(),
        }

    async def get_document(self, doc_id: UUID) -> Optional[dict]:
        """Retrieve document metadata (from Cosmos DB, not blob)."""
        # This is handled by CosmosDBService
        return None

    async def download_document(self, blob_name: str) -> bytes:
        """Download document content from blob storage."""
        if not self.container_client:
            return b""
        
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            downloader = blob_client.download_blob()
            return downloader.readall()
        except ResourceNotFoundError:
            logger.warning(f"Blob not found: {blob_name}")
            return b""
        except Exception as e:
            logger.error(f"Failed to download blob {blob_name}: {e}")
            return b""

    async def delete_document(self, blob_name: str) -> bool:
        """Delete a document from blob storage."""
        if not self.container_client:
            return False
        
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            blob_client.delete_blob()
            logger.info(f"Deleted blob: {blob_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Blob not found for deletion: {blob_name}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete blob {blob_name}: {e}")
            return False

    async def list_documents(
        self, space_id: UUID, cursor: Optional[str] = None, limit: int = 20
    ) -> tuple[list[dict], Optional[str], bool]:
        """
        List documents in a space (metadata from Cosmos DB).
        
        This method delegates to CosmosDBService for consistency.
        Returns:
            Tuple of (items, next_cursor, has_more)
        """
        # Blob Storage doesn't have good pagination for listing
        # Use Cosmos DB for document metadata instead
        return [], None, False

    async def generate_sas_url(
        self, blob_name: str, expiry_hours: int = 24, permissions: str = "r"
    ) -> str:
        """
        Generate a SAS URL for direct blob access.
        
        Args:
            blob_name: Name of the blob
            expiry_hours: Hours until SAS token expires
            permissions: Permissions string (r=read, w=write, d=delete)
        
        Returns:
            SAS URL for direct access
        """
        if not self.container_client or not self.client:
            return ""
        
        try:
            blob_client = self.container_client.get_blob_client(blob_name)
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=self.settings.azure_storage_account_name,
                container_name=self.container_name,
                blob_name=blob_name,
                account_key=self.settings.azure_storage_account_key,
                permission=BlobSasPermissions(read="r" in permissions, write="w" in permissions, delete="d" in permissions),
                expiry=datetime.utcnow() + timedelta(hours=expiry_hours)
            )
            
            # Build SAS URL
            sas_url = f"{blob_client.url}?{sas_token}"
            return sas_url
            
        except Exception as e:
            logger.error(f"Failed to generate SAS URL for {blob_name}: {e}")
            return ""
