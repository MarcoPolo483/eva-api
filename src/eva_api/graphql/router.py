"""
GraphQL API router.

Integrates Strawberry GraphQL with FastAPI.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from strawberry.fastapi import GraphQLRouter as StrawberryGraphQLRouter

from eva_api.config import Settings
from eva_api.dependencies import CurrentSettings, VerifiedJWTToken
from eva_api.graphql.resolvers import GraphQLContext, attach_resolvers
from eva_api.graphql.schema import schema
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.query_service import QueryService

logger = logging.getLogger(__name__)

# Attach resolvers to schema
attach_resolvers()


async def get_context(
    request: Request,
    jwt_token: VerifiedJWTToken,
    settings: CurrentSettings,
) -> GraphQLContext:
    """
    Build GraphQL context for each request.
    
    Creates service instances and user context from JWT token.
    """
    # Initialize services
    cosmos = CosmosDBService(settings)
    blob = BlobStorageService(settings)
    query = QueryService(settings, cosmos_service=cosmos, blob_service=blob)
    
    # Extract user info from JWT
    user_id = jwt_token.get("sub", "unknown")
    tenant_id = jwt_token.get("tenant_id", "unknown")
    
    return GraphQLContext(
        cosmos_service=cosmos,
        blob_service=blob,
        query_service=query,
        user_id=user_id,
        tenant_id=tenant_id,
    )


# Create Strawberry GraphQL router
graphql_router = StrawberryGraphQLRouter(
    schema,
    context_getter=get_context,
)

# Create FastAPI router
router = APIRouter()

# Mount GraphQL endpoints
router.include_router(
    graphql_router,
    prefix="/graphql",
    tags=["graphql"],
)

logger.info("GraphQL router initialized at /graphql")
