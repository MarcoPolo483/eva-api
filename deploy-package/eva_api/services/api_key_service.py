"""API Key management service.

Handles CRUD operations for API keys stored in Azure Cosmos DB.
"""

import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Any

from azure.cosmos import CosmosClient, exceptions
from azure.cosmos.container import ContainerProxy

from eva_api.config import Settings
from eva_api.models.auth import APIKeyCreate, APIKeyInfo, APIKeyResponse

logger = logging.getLogger(__name__)


class APIKeyService:
    """Service for managing API keys in Cosmos DB."""
    
    def __init__(self, settings: Settings) -> None:
        """Initialize API key service.
        
        Args:
            settings: Application settings
        """
        self.settings = settings
        self._cosmos_client: CosmosClient | None = None
        self._container: ContainerProxy | None = None
    
    def _get_container(self) -> ContainerProxy:
        """Get or create Cosmos DB container (lazy initialization).
        
        Returns:
            ContainerProxy: Cosmos DB container for API keys
        """
        if self._container is None:
            if not self.settings.cosmos_db_endpoint or not self.settings.cosmos_db_key:
                raise ValueError("Cosmos DB credentials not configured")
            
            self._cosmos_client = CosmosClient(
                self.settings.cosmos_db_endpoint,
                self.settings.cosmos_db_key,
            )
            database = self._cosmos_client.get_database_client(self.settings.cosmos_db_database)
            self._container = database.get_container_client(self.settings.cosmos_db_container_api_keys)
            
            logger.info(f"Initialized Cosmos DB container: {self.settings.cosmos_db_container_api_keys}")
        
        return self._container
    
    def _hash_api_key(self, api_key: str) -> str:
        """Hash API key for secure storage.
        
        Args:
            api_key: Plain API key
            
        Returns:
            str: SHA-256 hash of API key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()
    
    def _generate_api_key(self) -> str:
        """Generate a secure API key.
        
        Returns:
            str: Generated API key with prefix
        """
        random_part = secrets.token_urlsafe(self.settings.api_key_length)
        return f"{self.settings.api_key_prefix}{random_part}"
    
    async def create_api_key(
        self,
        tenant_id: str,
        request: APIKeyCreate,
    ) -> APIKeyResponse:
        """Create a new API key and store in Cosmos DB.
        
        Args:
            tenant_id: Tenant ID that owns this key
            request: API key creation request
            
        Returns:
            APIKeyResponse: Created API key with value
            
        Raises:
            exceptions.CosmosHttpResponseError: If Cosmos DB operation fails
        """
        key_id = secrets.token_urlsafe(16)
        api_key = self._generate_api_key()
        api_key_hash = self._hash_api_key(api_key)
        now = datetime.now(timezone.utc)
        
        # Prepare document for Cosmos DB
        document = {
            "id": key_id,
            "key_hash": api_key_hash,
            "name": request.name,
            "tenant_id": tenant_id,
            "scopes": request.scopes,
            "is_active": True,
            "created_at": now.isoformat(),
            "expires_at": request.expires_at.isoformat() if request.expires_at else None,
            "last_used_at": None,
            "metadata": {},
        }
        
        try:
            container = self._get_container()
            container.create_item(body=document)
            logger.info(f"Created API key '{request.name}' (ID: {key_id}) for tenant {tenant_id}")
            
            return APIKeyResponse(
                id=key_id,
                key=api_key,  # Only returned on creation
                name=request.name,
                scopes=request.scopes,
                created_at=now,
                expires_at=request.expires_at,
            )
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create API key in Cosmos DB: {e}")
            raise
    
    async def get_api_key(self, key_id: str, tenant_id: str) -> APIKeyInfo | None:
        """Get API key information by ID.
        
        Args:
            key_id: API key ID
            tenant_id: Tenant ID for authorization
            
        Returns:
            APIKeyInfo | None: API key info or None if not found
        """
        try:
            container = self._get_container()
            
            # Query by ID with tenant authorization check
            query = "SELECT * FROM c WHERE c.id = @key_id AND c.tenant_id = @tenant_id"
            parameters = [
                {"name": "@key_id", "value": key_id},
                {"name": "@tenant_id", "value": tenant_id},
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            ))
            
            if not items:
                logger.warning(f"API key not found or unauthorized: {key_id} for tenant {tenant_id}")
                return None
            
            item = items[0]
            return APIKeyInfo(
                id=item["id"],
                name=item["name"],
                scopes=item["scopes"],
                is_active=item["is_active"],
                created_at=datetime.fromisoformat(item["created_at"]),
                expires_at=datetime.fromisoformat(item["expires_at"]) if item["expires_at"] else None,
                last_used_at=datetime.fromisoformat(item["last_used_at"]) if item["last_used_at"] else None,
            )
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get API key from Cosmos DB: {e}")
            return None
    
    async def list_api_keys(self, tenant_id: str) -> list[APIKeyInfo]:
        """List all API keys for a tenant.
        
        Args:
            tenant_id: Tenant ID
            
        Returns:
            list[APIKeyInfo]: List of API keys
        """
        try:
            container = self._get_container()
            
            # Query all keys for tenant
            query = "SELECT * FROM c WHERE c.tenant_id = @tenant_id"
            parameters = [{"name": "@tenant_id", "value": tenant_id}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            ))
            
            logger.info(f"Found {len(items)} API keys for tenant {tenant_id}")
            
            return [
                APIKeyInfo(
                    id=item["id"],
                    name=item["name"],
                    scopes=item["scopes"],
                    is_active=item["is_active"],
                    created_at=datetime.fromisoformat(item["created_at"]),
                    expires_at=datetime.fromisoformat(item["expires_at"]) if item["expires_at"] else None,
                    last_used_at=datetime.fromisoformat(item["last_used_at"]) if item["last_used_at"] else None,
                )
                for item in items
            ]
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to list API keys from Cosmos DB: {e}")
            return []
    
    async def revoke_api_key(self, key_id: str, tenant_id: str) -> bool:
        """Revoke an API key.
        
        Args:
            key_id: API key ID
            tenant_id: Tenant ID for authorization
            
        Returns:
            bool: True if revoked, False if not found
        """
        try:
            container = self._get_container()
            
            # Query to find the key
            query = "SELECT * FROM c WHERE c.id = @key_id AND c.tenant_id = @tenant_id"
            parameters = [
                {"name": "@key_id", "value": key_id},
                {"name": "@tenant_id", "value": tenant_id},
            ]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            ))
            
            if not items:
                logger.warning(f"API key not found or unauthorized: {key_id} for tenant {tenant_id}")
                return False
            
            # Update is_active to False
            item = items[0]
            item["is_active"] = False
            container.replace_item(item=item["id"], body=item)
            
            logger.info(f"Revoked API key {key_id} for tenant {tenant_id}")
            return True
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to revoke API key in Cosmos DB: {e}")
            return False
    
    async def verify_api_key(self, api_key: str) -> dict[str, Any] | None:
        """Verify an API key and return its metadata.
        
        Args:
            api_key: API key to verify
            
        Returns:
            dict | None: Key metadata if valid, None if invalid
        """
        try:
            container = self._get_container()
            api_key_hash = self._hash_api_key(api_key)
            now = datetime.now(timezone.utc)
            
            # Query by hashed key
            query = "SELECT * FROM c WHERE c.key_hash = @key_hash"
            parameters = [{"name": "@key_hash", "value": api_key_hash}]
            
            items = list(container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            ))
            
            if not items:
                logger.warning("API key not found")
                return None
            
            item = items[0]
            
            # Check if active
            if not item["is_active"]:
                logger.warning(f"API key {item['id']} is revoked")
                return None
            
            # Check expiration
            if item["expires_at"]:
                expires_at = datetime.fromisoformat(item["expires_at"])
                if expires_at < now:
                    logger.warning(f"API key {item['id']} has expired")
                    return None
            
            # Update last_used_at timestamp
            item["last_used_at"] = now.isoformat()
            container.replace_item(item=item["id"], body=item)
            
            logger.info(f"Verified API key {item['id']} for tenant {item['tenant_id']}")
            
            return {
                "key_id": item["id"],
                "tenant_id": item["tenant_id"],
                "scopes": item["scopes"],
                "name": item["name"],
            }
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to verify API key in Cosmos DB: {e}")
            return None
