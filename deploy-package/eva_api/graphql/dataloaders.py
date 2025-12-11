"""DataLoader implementations for GraphQL N+1 query optimization.

Phase 3: Batch loading to prevent N+1 queries when fetching related data.

DataLoaders batch multiple requests for the same resource type into a single
database query, significantly improving performance for nested GraphQL queries.

Example N+1 problem solved:
    Query: Get 100 spaces with their documents
    Without DataLoader: 1 query for spaces + 100 queries for documents = 101 queries
    With DataLoader: 1 query for spaces + 1 batched query for all documents = 2 queries
"""

import logging
from typing import List, Optional
from uuid import UUID

from strawberry.dataloader import DataLoader

from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.blob_service import BlobStorageService

logger = logging.getLogger(__name__)


# ============================================================================
# Document DataLoader
# ============================================================================

async def load_documents_by_space(
    space_ids: List[UUID],
    cosmos_service: CosmosDBService,
    tenant_id: str,
) -> List[List[dict]]:
    """Batch load documents for multiple spaces.
    
    Args:
        space_ids: List of space IDs to load documents for
        cosmos_service: Cosmos DB service instance
        tenant_id: Tenant ID for authorization
        
    Returns:
        List of document lists, one per space_id (same order)
    """
    try:
        # Build query to fetch all documents for all spaces in one query
        space_id_strs = [str(sid) for sid in space_ids]
        
        query = """
            SELECT * FROM c 
            WHERE c.tenant_id = @tenant_id 
            AND c.space_id IN (@space_ids)
            ORDER BY c.created_at DESC
        """
        
        parameters = [
            {"name": "@tenant_id", "value": tenant_id},
            {"name": "@space_ids", "value": space_id_strs},
        ]
        
        container = cosmos_service.get_container("documents")
        items = container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
        )
        
        # Collect all documents
        all_documents = []
        async for item in items:
            all_documents.append(item)
        
        # Group documents by space_id
        documents_by_space = {sid: [] for sid in space_ids}
        for doc in all_documents:
            space_id = UUID(doc["space_id"])
            if space_id in documents_by_space:
                documents_by_space[space_id].append(doc)
        
        # Return in same order as input space_ids
        result = [documents_by_space[sid] for sid in space_ids]
        
        logger.debug(
            f"DataLoader: Loaded documents for {len(space_ids)} spaces "
            f"({len(all_documents)} total documents)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to batch load documents: {e}")
        # Return empty lists for all spaces on error
        return [[] for _ in space_ids]


def create_document_loader(
    cosmos_service: CosmosDBService,
    tenant_id: str,
) -> DataLoader[UUID, List[dict]]:
    """Create a DataLoader for batching document queries.
    
    Args:
        cosmos_service: Cosmos DB service instance
        tenant_id: Tenant ID for authorization
        
    Returns:
        DataLoader instance for loading documents by space_id
    """
    async def batch_load_fn(space_ids: List[UUID]) -> List[List[dict]]:
        return await load_documents_by_space(space_ids, cosmos_service, tenant_id)
    
    return DataLoader(load_fn=batch_load_fn)


# ============================================================================
# Query DataLoader
# ============================================================================

async def load_queries_by_space(
    space_ids: List[UUID],
    cosmos_service: CosmosDBService,
    tenant_id: str,
) -> List[List[dict]]:
    """Batch load queries for multiple spaces.
    
    Args:
        space_ids: List of space IDs to load queries for
        cosmos_service: Cosmos DB service instance
        tenant_id: Tenant ID for authorization
        
    Returns:
        List of query lists, one per space_id (same order)
    """
    try:
        space_id_strs = [str(sid) for sid in space_ids]
        
        query = """
            SELECT * FROM c 
            WHERE c.tenant_id = @tenant_id 
            AND c.space_id IN (@space_ids)
            ORDER BY c.created_at DESC
        """
        
        parameters = [
            {"name": "@tenant_id", "value": tenant_id},
            {"name": "@space_ids", "value": space_id_strs},
        ]
        
        container = cosmos_service.get_container("queries")
        items = container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
        )
        
        # Collect all queries
        all_queries = []
        async for item in items:
            all_queries.append(item)
        
        # Group queries by space_id
        queries_by_space = {sid: [] for sid in space_ids}
        for query_item in all_queries:
            space_id = UUID(query_item["space_id"])
            if space_id in queries_by_space:
                queries_by_space[space_id].append(query_item)
        
        # Return in same order as input space_ids
        result = [queries_by_space[sid] for sid in space_ids]
        
        logger.debug(
            f"DataLoader: Loaded queries for {len(space_ids)} spaces "
            f"({len(all_queries)} total queries)"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to batch load queries: {e}")
        return [[] for _ in space_ids]


def create_query_loader(
    cosmos_service: CosmosDBService,
    tenant_id: str,
) -> DataLoader[UUID, List[dict]]:
    """Create a DataLoader for batching query queries.
    
    Args:
        cosmos_service: Cosmos DB service instance
        tenant_id: Tenant ID for authorization
        
    Returns:
        DataLoader instance for loading queries by space_id
    """
    async def batch_load_fn(space_ids: List[UUID]) -> List[List[dict]]:
        return await load_queries_by_space(space_ids, cosmos_service, tenant_id)
    
    return DataLoader(load_fn=batch_load_fn)


# ============================================================================
# Space DataLoader (for batch fetching by ID)
# ============================================================================

async def load_spaces_by_id(
    space_ids: List[UUID],
    cosmos_service: CosmosDBService,
    tenant_id: str,
) -> List[Optional[dict]]:
    """Batch load spaces by ID.
    
    Args:
        space_ids: List of space IDs to load
        cosmos_service: Cosmos DB service instance
        tenant_id: Tenant ID for authorization
        
    Returns:
        List of space dicts (or None if not found), one per space_id
    """
    try:
        space_id_strs = [str(sid) for sid in space_ids]
        
        query = """
            SELECT * FROM c 
            WHERE c.tenant_id = @tenant_id 
            AND c.id IN (@space_ids)
        """
        
        parameters = [
            {"name": "@tenant_id", "value": tenant_id},
            {"name": "@space_ids", "value": space_id_strs},
        ]
        
        container = cosmos_service.get_container("spaces")
        items = container.query_items(
            query=query,
            parameters=parameters,
            enable_cross_partition_query=True,
        )
        
        # Collect spaces indexed by ID
        spaces_by_id = {}
        async for item in items:
            spaces_by_id[UUID(item["id"])] = item
        
        # Return in same order as input, with None for missing spaces
        result = [spaces_by_id.get(sid) for sid in space_ids]
        
        logger.debug(f"DataLoader: Loaded {len(spaces_by_id)} spaces (requested {len(space_ids)})")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to batch load spaces: {e}")
        return [None for _ in space_ids]


def create_space_loader(
    cosmos_service: CosmosDBService,
    tenant_id: str,
) -> DataLoader[UUID, Optional[dict]]:
    """Create a DataLoader for batching space lookups by ID.
    
    Args:
        cosmos_service: Cosmos DB service instance
        tenant_id: Tenant ID for authorization
        
    Returns:
        DataLoader instance for loading spaces by ID
    """
    async def batch_load_fn(space_ids: List[UUID]) -> List[Optional[dict]]:
        return await load_spaces_by_id(space_ids, cosmos_service, tenant_id)
    
    return DataLoader(load_fn=batch_load_fn)


# ============================================================================
# DataLoader Factory
# ============================================================================

def create_dataloaders(
    cosmos_service: CosmosDBService,
    tenant_id: str,
) -> dict:
    """Create all DataLoaders for a GraphQL request.
    
    Args:
        cosmos_service: Cosmos DB service instance
        tenant_id: Tenant ID for authorization
        
    Returns:
        Dictionary of DataLoader instances by name
    """
    return {
        "documents_by_space": create_document_loader(cosmos_service, tenant_id),
        "queries_by_space": create_query_loader(cosmos_service, tenant_id),
        "spaces_by_id": create_space_loader(cosmos_service, tenant_id),
    }
