"""
Azure Cosmos DB service for managing spaces and metadata.
"""

import asyncio
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
        
        # Mock mode for testing
        self.mock_mode = settings.mock_mode
        
        try:
            # Initialize Cosmos client with timeout settings
            if not self.mock_mode:
                self.client = CosmosClient(
                    settings.cosmos_db_endpoint,
                    credential=settings.cosmos_db_key,
                    timeout=settings.azure_timeout,
                )
            else:
                self.client = None
            
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
            
            # Webhook containers (Phase 3)
            self.webhooks_container = self._ensure_container(
                "webhooks",
                partition_key="/tenant_id"
            )
            self.webhook_logs_container = self._ensure_container(
                "webhook_logs",
                partition_key="/webhook_id"
            )
            self.webhook_dlq_container = self._ensure_container(
                "webhook_dead_letter_queue",
                partition_key="/tenant_id"
            )
            
            logger.info(f"CosmosDBService initialized: {settings.cosmos_db_database}")
            
        except Exception as e:
            logger.warning(f"Cosmos DB initialization failed (will use placeholder): {e}")
            self.client = None
            self.database = None
            self.spaces_container = None
            self.documents_container = None
            self.queries_container = None
            self.webhooks_container = None
            self.webhook_logs_container = None
            self.webhook_dlq_container = None

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
        
        # Fast-fail in mock mode
        if self.mock_mode or not self.spaces_container:
            logger.debug(f"Mock mode: Created space {space_id}")
            return space
        
        try:
            self.spaces_container.create_item(body=space)
            logger.info(f"Created space in Cosmos DB: {space_id}")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create space in Cosmos DB: {e}")
            raise
        
        return space

    async def get_space(self, space_id: UUID) -> Optional[dict]:
        """Retrieve a space by ID."""
        # Fast-fail in mock mode
        if self.mock_mode or not self.spaces_container:
            logger.debug(f"Mock mode: Get space {space_id}")
            return {
                "id": str(space_id),
                "name": "Mock Space",
                "description": "Mock data",
                "metadata": {},
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "document_count": 0,
            }
            
        try:
            # Use query instead of read_item to avoid partition key issues
            def _query_space():
                query = "SELECT * FROM c WHERE c.id = @space_id"
                params = [{"name": "@space_id", "value": str(space_id)}]
                items = list(self.spaces_container.query_items(
                    query=query,
                    parameters=params,
                    enable_cross_partition_query=True
                ))
                return items[0] if items else None
            
            return await asyncio.to_thread(_query_space)
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
        # Fast-fail in mock mode
        if self.mock_mode or not self.spaces_container:
            logger.debug("Mock mode: List spaces")
            mock_spaces = [
                {
                    "id": str(uuid4()),
                    "name": f"Mock Space {i}",
                    "description": "Mock data",
                    "tenant_id": "mock-tenant",
                    "created_by": "mock-user",
                    "metadata": {},
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                    "document_count": 0,
                    "tags": [],
                }
                for i in range(min(limit, 5))
            ]
            return mock_spaces, None, False
        
        try:
            # Query all spaces across partitions
            # Cosmos SDK is synchronous - wrap in thread pool for async context
            query = "SELECT * FROM c"
            
            def _query_spaces():
                """Execute synchronous Cosmos query in thread pool."""
                items = list(self.spaces_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                return items[:limit] if limit else items
            
            # Run synchronous query in thread pool to avoid async/sync conflict
            import asyncio
            items_list = await asyncio.to_thread(_query_spaces)
            
            # For now, no pagination support with cross-partition queries
            next_cursor = None
            has_more = len(items_list) == limit if limit else False
            
            logger.info(f"Retrieved {len(items_list)} spaces from Cosmos DB")
            return items_list, next_cursor, has_more
            
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to list spaces - Cosmos error: {e.status_code} - {e.message}")
            return [], None, False
        except Exception as e:
            logger.error(f"Failed to list spaces - Unexpected error: {type(e).__name__}: {str(e)}")
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

    # ========================================
    # Webhook Management Methods (Phase 3)
    # ========================================

    async def create_webhook(self, webhook_data: dict) -> dict:
        """Create a new webhook subscription."""
        if self.mock_mode or not self.webhooks_container:
            logger.debug(f"Mock mode: Created webhook {webhook_data.get('id')}")
            return webhook_data
        
        try:
            self.webhooks_container.create_item(body=webhook_data)
            logger.info(f"Created webhook: {webhook_data['id']}")
            return webhook_data
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create webhook: {e}")
            raise

    async def get_webhook(self, webhook_id: str, tenant_id: str) -> Optional[dict]:
        """Retrieve a webhook by ID."""
        if self.mock_mode or not self.webhooks_container:
            logger.debug(f"Mock mode: Get webhook {webhook_id}")
            return None
        
        try:
            item = self.webhooks_container.read_item(
                item=webhook_id,
                partition_key=tenant_id
            )
            return item
        except exceptions.CosmosResourceNotFoundError:
            return None
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get webhook {webhook_id}: {e}")
            return None

    async def update_webhook(self, webhook_id: str, tenant_id: str, updates: dict) -> Optional[dict]:
        """Update a webhook subscription."""
        if self.mock_mode or not self.webhooks_container:
            logger.debug(f"Mock mode: Update webhook {webhook_id}")
            return updates
        
        try:
            webhook = await self.get_webhook(webhook_id, tenant_id)
            if not webhook:
                return None
            
            webhook.update(updates)
            webhook["updated_at"] = datetime.utcnow().isoformat()
            
            updated = self.webhooks_container.replace_item(
                item=webhook_id,
                body=webhook
            )
            logger.info(f"Updated webhook: {webhook_id}")
            return updated
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update webhook {webhook_id}: {e}")
            return None

    async def delete_webhook(self, webhook_id: str, tenant_id: str) -> bool:
        """Delete a webhook subscription."""
        if self.mock_mode or not self.webhooks_container:
            logger.debug(f"Mock mode: Delete webhook {webhook_id}")
            return True
        
        try:
            self.webhooks_container.delete_item(
                item=webhook_id,
                partition_key=tenant_id
            )
            logger.info(f"Deleted webhook: {webhook_id}")
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to delete webhook {webhook_id}: {e}")
            return False

    async def list_webhooks(self, tenant_id: str) -> list[dict]:
        """List all webhooks for a tenant."""
        if self.mock_mode or not self.webhooks_container:
            logger.debug(f"Mock mode: List webhooks for tenant {tenant_id}")
            return []
        
        try:
            query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id"
            items = self.webhooks_container.query_items(
                query=query,
                parameters=[{"name": "@tenant_id", "value": tenant_id}],
                enable_cross_partition_query=False
            )
            return list(items)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to list webhooks for tenant {tenant_id}: {e}")
            return []

    async def get_active_webhooks(self, tenant_id: str, event_type: str) -> list[dict]:
        """Get active webhooks matching an event type pattern."""
        if self.mock_mode or not self.webhooks_container:
            logger.debug(f"Mock mode: Get active webhooks for {event_type}")
            return []
        
        try:
            # Query for active webhooks with matching event patterns
            query = """
                SELECT * FROM c 
                WHERE c.tenant_id = @tenant_id 
                AND c.is_active = true
                AND ARRAY_CONTAINS(c.event_types, @event_type, true)
            """
            items = self.webhooks_container.query_items(
                query=query,
                parameters=[
                    {"name": "@tenant_id", "value": tenant_id},
                    {"name": "@event_type", "value": event_type}
                ],
                enable_cross_partition_query=False
            )
            return list(items)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get active webhooks: {e}")
            return []

    async def create_webhook_log(self, log_data: dict) -> dict:
        """Create a webhook delivery log entry."""
        if self.mock_mode or not self.webhook_logs_container:
            logger.debug(f"Mock mode: Created webhook log {log_data.get('id')}")
            return log_data
        
        try:
            self.webhook_logs_container.create_item(body=log_data)
            logger.debug(f"Created webhook log: {log_data['id']}")
            return log_data
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create webhook log: {e}")
            raise

    async def list_webhook_logs(
        self, webhook_id: str, limit: int = 50
    ) -> list[dict]:
        """List delivery logs for a webhook."""
        if self.mock_mode or not self.webhook_logs_container:
            logger.debug(f"Mock mode: List logs for webhook {webhook_id}")
            return []
        
        try:
            query = """
                SELECT TOP @limit * FROM c 
                WHERE c.webhook_id = @webhook_id 
                ORDER BY c.timestamp DESC
            """
            items = self.webhook_logs_container.query_items(
                query=query,
                parameters=[
                    {"name": "@webhook_id", "value": webhook_id},
                    {"name": "@limit", "value": limit}
                ],
                enable_cross_partition_query=False
            )
            return list(items)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to list webhook logs: {e}")
            return []

    async def create_dlq_entry(self, dlq_data: dict) -> dict:
        """Create a dead letter queue entry."""
        if self.mock_mode or not self.webhook_dlq_container:
            logger.debug(f"Mock mode: Created DLQ entry {dlq_data.get('id')}")
            return dlq_data
        
        try:
            self.webhook_dlq_container.create_item(body=dlq_data)
            logger.warning(f"Created DLQ entry: {dlq_data['id']}")
            return dlq_data
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create DLQ entry: {e}")
            raise

    async def update_webhook_stats(
        self, webhook_id: str, tenant_id: str, 
        success: bool, response_time_ms: float
    ) -> None:
        """Update webhook delivery statistics."""
        if self.mock_mode or not self.webhooks_container:
            return
        
        try:
            webhook = await self.get_webhook(webhook_id, tenant_id)
            if not webhook:
                return
            
            stats = webhook.get("stats", {
                "total_deliveries": 0,
                "successful_deliveries": 0,
                "failed_deliveries": 0,
                "avg_response_time_ms": 0.0
            })
            
            stats["total_deliveries"] += 1
            if success:
                stats["successful_deliveries"] += 1
            else:
                stats["failed_deliveries"] += 1
            
            # Update average response time
            total = stats["total_deliveries"]
            current_avg = stats["avg_response_time_ms"]
            stats["avg_response_time_ms"] = (
                (current_avg * (total - 1) + response_time_ms) / total
            )
            
            webhook["stats"] = stats
            webhook["last_delivery_at"] = datetime.utcnow().isoformat()
            
            await self.update_webhook(webhook_id, tenant_id, {"stats": stats, "last_delivery_at": webhook["last_delivery_at"]})
            
        except Exception as e:
            logger.error(f"Failed to update webhook stats: {e}")

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
