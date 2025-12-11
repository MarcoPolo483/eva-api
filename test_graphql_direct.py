"""Direct test of Strawberry GraphQL execution."""
import sys
sys.path.insert(0, 'src')

import asyncio
from eva_api.graphql.schema import schema
from eva_api.graphql.resolvers import GraphQLContext
from eva_api.config import get_settings
from eva_api.services.cosmos_service import CosmosDBService
from eva_api.services.blob_service import BlobStorageService
from eva_api.services.query_service import QueryService


async def test():
    settings = get_settings()
    
    # Create context
    cosmos = CosmosDBService(settings)
    blob = BlobStorageService(settings)
    query = QueryService(settings, cosmos_service=cosmos, blob_service=blob)
    
    context = GraphQLContext(
        cosmos_service=cosmos,
        blob_service=blob,
        query_service=query,
        user_id="test",
        tenant_id="test",
    )
    
    # Execute query
    query_str = "{ spaces(limit: 2) { items { name } } }"
    
    try:
        result = await schema.execute(query_str, context_value=context)
        
        if result.errors:
            print(f"❌ GraphQL Errors:")
            for error in result.errors:
                print(f"   {error}")
                if hasattr(error, '__traceback__'):
                    import traceback
                    traceback.print_tb(error.__traceback__)
        else:
            print(f"✅ Success: {result.data}")
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test())
