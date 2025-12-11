"""
GraphQL API router with WebSocket support for subscriptions.

Integrates Strawberry GraphQL with FastAPI, including:
- Query and Mutation endpoints (HTTP)
- Subscription endpoints (WebSocket) for real-time updates
- JWT authentication for both HTTP and WebSocket connections

Phase 3: WebSocket support for GraphQL subscriptions
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Request, WebSocket
from strawberry.fastapi import GraphQLRouter as StrawberryGraphQLRouter
import jwt

from eva_api.config import Settings
from eva_api.dependencies import CurrentSettings, VerifiedJWTToken, get_azure_ad_service
from eva_api.graphql.resolvers import GraphQLContext
from eva_api.graphql.schema import schema
from eva_api.graphql.dataloaders import create_dataloaders
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.query_service import QueryService
from eva_api.services.auth_service import AzureADService

logger = logging.getLogger(__name__)


async def get_context(
    request: Request,
    settings: CurrentSettings,
) -> GraphQLContext:
    """
    Build GraphQL context for each request.
    
    Creates service instances and user context from JWT token.
    Verifies JWT using Azure AD service for authenticated requests.
    """
    try:
        # Extract and verify JWT token
        authorization = request.headers.get("authorization", "")
        
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            try:
                # Verify JWT with Azure AD service
                azure_ad = await get_azure_ad_service(settings)
                claims = await azure_ad.verify_jwt_token(token)
                user_id = claims.sub
                tenant_id = claims.tenant_id
                logger.debug(f"GraphQL request authenticated: user={user_id}, tenant={tenant_id}")
            except jwt.ExpiredSignatureError:
                logger.warning("GraphQL request with expired JWT token")
                user_id = "anonymous"
                tenant_id = "default"
            except jwt.InvalidTokenError as e:
                logger.warning(f"GraphQL request with invalid JWT token: {e}")
                user_id = "anonymous"
                tenant_id = "default"
            except Exception as e:
                logger.error(f"Failed to verify JWT token: {e}")
                user_id = "anonymous"
                tenant_id = "default"
        else:
            # Allow introspection and anonymous queries without auth
            user_id = "anonymous"
            tenant_id = "default"
            logger.debug("GraphQL request without authentication")
        
        # Initialize services
        cosmos = CosmosDBService(settings)
        blob = BlobStorageService(settings)
        query = QueryService(settings, cosmos_service=cosmos, blob_service=blob)
        
        # Phase 3: Create DataLoaders for N+1 query optimization
        dataloaders = create_dataloaders(cosmos, tenant_id)
        
        # Return plain dict instead of custom class
        return {
            "cosmos": cosmos,
            "blob": blob,
            "query": query,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "dataloaders": dataloaders,  # Phase 3: DataLoader support
        }
    except Exception as e:
        logger.error(f"Failed to create GraphQL context: {e}", exc_info=True)
        raise


# Create Strawberry GraphQL router with context getter and WebSocket support
# Phase 3: Enable subscriptions for real-time updates
graphql_router = StrawberryGraphQLRouter(
    schema,
    context_getter=get_context,
    subscription_protocols=[
        "graphql-transport-ws",  # Modern GraphQL over WebSocket protocol
        "graphql-ws",            # Legacy protocol for compatibility
    ],
)

# Export as FastAPI router (Strawberry router IS a FastAPI router)
router = graphql_router

logger.info("GraphQL router initialized with WebSocket support for subscriptions")
