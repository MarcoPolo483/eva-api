"""
Azure Cosmos DB service for managing spaces and metadata.
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.cosmos.container import ContainerProxy

from eva_api.config import Settings

logger = logging.getLogger(__name__)


class CosmosDBService:
    """
    Service for interacting with Azure Cosmos DB.
    
    Manages spaces, documents metadata, and query history.
    """

    def __init__(self, settings: Settings):
        """Initialize Cosmos DB client."""
        self.settings = settings
        
        try:
            # Initialize Cosmos client
            self.client = CosmosClient(
                settings.cosmos_db_endpoint,
                credential=settings.cosmos_db_key
            )
            
            # Get database (create if not exists)
            self.database = self.client.create_database_if_not_exists(
                id=settings.cosmos_db_database
            )
            
            # Get/create containers
            self.spaces_container = self._ensure_container(
                "spaces",
                partition_key="/id"
            )
            self.documents_container = self._ensure_container(
                "documents",
                partition_key="/space_id"
            )
            self.queries_container = self._ensure_container(
                "queries",
                partition_key="/space_id"
            )
            
            logger.info(f"CosmosDBService initialized: {settings.cosmos_db_database}")
            
        except Exception as e:
            logger.warning(f"Cosmos DB initialization failed (will use placeholder): {e}")
            self.client = None
            self.database = None
            self.spaces_container = None
            self.documents_container = None
            self.queries_container = None

    def _ensure_container(self, name: str, partition_key: str) -> Optional[ContainerProxy]:
        """Create container if it doesn't exist."""
        try:
            return self.database.create_container_if_not_exists(
                id=name,
                partition_key=PartitionKey(path=partition_key),
                offer_throughput=400  # RU/s
            )
        except Exception as e:
            logger.error(f"Failed to ensure container {name}: {e}")
            return None

    async def create_space(
        self, name: str, description: Optional[str] = None, metadata: Optional[dict] = None
    ) -> dict:
        """Create a new space."""
        space_id = uuid4()
        now = datetime.utcnow()
        
        space = {
            "id": str(space_id),
            "name": name,
            "description": description,
            "metadata": metadata or {},
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
            "document_count": 0,
        }
        
        if self.spaces_container:
            try:
                self.spaces_container.create_item(body=space)
                logger.info(f"Created space in Cosmos DB: {space_id}")
            except exceptions.CosmosHttpResponseError as e:
                logger.error(f"Failed to create space in Cosmos DB: {e}")
                raise
        
        return space

    async def get_space(self, space_id: UUID) -> Optional[dict]:
        """Retrieve a space by ID."""
        if not self.spaces_container:
            return None
            
        try:
            item = self.spaces_container.read_item(
                item=str(space_id),
                partition_key=str(space_id)
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get space {space_id}: {e}")
            return None

    async def list_spaces(
        self, cursor: Optional[str] = None, limit: int = 20
    ) -> tuple[list[dict], Optional[str], bool]:
        """
        List spaces with cursor-based pagination.
        
        Returns:
            Tuple of (items, next_cursor, has_more)
        """
        if not self.spaces_container:
            return [], None, False
        
        try:
            query = "SELECT * FROM c ORDER BY c.created_at DESC"
            items_list = []
            
            # Query with continuation token
            items = self.spaces_container.query_items(
                query=query,
                max_item_count=limit,
                continuation=cursor
            )
            
            # Fetch items
            response_headers = {}
            for item in items:
                items_list.append(item)
                if len(items_list) >= limit:
                    break
            
            # Get continuation token for next page
            next_cursor = items.response_headers.get("x-ms-continuation")
            has_more = next_cursor is not None
            
            return items_list, next_cursor, has_more
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to list spaces: {e}")
            return [], None, False

    async def update_space(
        self,
        space_id: UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> Optional[dict]:
        """Update an existing space."""
        if not self.spaces_container:
            return None
        
        try:
            # Read current space
            space = await self.get_space(space_id)
            if not space:
                return None
            
            # Update fields
            if name is not None:
                space["name"] = name
            if description is not None:
                space["description"] = description
            if metadata is not None:
                space["metadata"] = metadata
            space["updated_at"] = datetime.utcnow().isoformat()
            
            # Replace item
            updated = self.spaces_container.replace_item(
                item=str(space_id),
                body=space
            )
            logger.info(f"Updated space in Cosmos DB: {space_id}")
            return updated
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update space {space_id}: {e}")
            return None

    async def delete_space(self, space_id: UUID) -> bool:
        """Delete a space."""
        if not self.spaces_container:
            return False
        
        try:
            self.spaces_container.delete_item(
                item=str(space_id),
                partition_key=str(space_id)
            )
            logger.info(f"Deleted space from Cosmos DB: {space_id}")
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to delete space {space_id}: {e}")
            return False

    async def increment_document_count(self, space_id: UUID) -> None:
        """Increment the document count for a space."""
        if not self.spaces_container:
            return
        
        try:
            space = await self.get_space(space_id)
            if space:
                space["document_count"] = space.get("document_count", 0) + 1
                space["updated_at"] = datetime.utcnow().isoformat()
                self.spaces_container.replace_item(
                    item=str(space_id),
                    body=space
                )
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to increment document count for {space_id}: {e}")

    async def decrement_document_count(self, space_id: UUID) -> None:
        """Decrement the document count for a space."""
        if not self.spaces_container:
            return
        
        try:
            space = await self.get_space(space_id)
            if space and space.get("document_count", 0) > 0:
                space["document_count"] = space["document_count"] - 1
                space["updated_at"] = datetime.utcnow().isoformat()
                self.spaces_container.replace_item(
                    item=str(space_id),
                    body=space
                )
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to decrement document count for {space_id}: {e}")

    async def create_document_metadata(self, doc_metadata: dict) -> dict:
        """Store document metadata in Cosmos DB."""
        if not self.documents_container:
            return doc_metadata
        
        try:
            created = self.documents_container.create_item(body=doc_metadata)
            logger.info(f"Created document metadata: {doc_metadata['id']}")
            return created
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create document metadata: {e}")
            return doc_metadata

    async def get_document_metadata(self, doc_id: UUID, space_id: UUID) -> Optional[dict]:
        """Retrieve document metadata."""
        if not self.documents_container:
            return None
        
        try:
            item = self.documents_container.read_item(
                item=str(doc_id),
                partition_key=str(space_id)
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get document metadata {doc_id}: {e}")
            return None

    async def list_documents(
        self, space_id: UUID, cursor: Optional[str] = None, limit: int = 20
    ) -> tuple[list[dict], Optional[str], bool]:
        """List documents in a space."""
        if not self.documents_container:
            return [], None, False
        
        try:
            query = f"SELECT * FROM c WHERE c.space_id = '{space_id}' ORDER BY c.created_at DESC"
            items_list = []
            
            items = self.documents_container.query_items(
                query=query,
                max_item_count=limit,
                continuation=cursor
            )
            
            for item in items:
                items_list.append(item)
                if len(items_list) >= limit:
                    break
            
            next_cursor = items.response_headers.get("x-ms-continuation")
            has_more = next_cursor is not None
            
            return items_list, next_cursor, has_more
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to list documents for space {space_id}: {e}")
            return [], None, False

    async def delete_document_metadata(self, doc_id: UUID, space_id: UUID) -> bool:
        """Delete document metadata."""
        if not self.documents_container:
            return False
        
        try:
            self.documents_container.delete_item(
                item=str(doc_id),
                partition_key=str(space_id)
            )
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to delete document metadata {doc_id}: {e}")
            return False
