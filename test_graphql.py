"""Test GraphQL endpoint to see actual error."""
import sys
sys.path.insert(0, 'src')

import asyncio
from eva_api.config import get_settings
from eva_api.graphql.router import get_context
from fastapi import Request

async def test_graphql():
    settings = get_settings()
    
    # Mock request
    request = Request(scope={
        'type': 'http',
        'headers': [],
    })
    
    # Mock JWT token (what verify_jwt_token returns)
    jwt_token = {"sub": "placeholder", "tenant_id": "placeholder"}
    
    try:
        context = await get_context(request, jwt_token, settings)
        print(f"✅ Context created successfully: {context}")
        
        # Try to list spaces (use correct attribute name)
        items, cursor, has_more = await context.cosmos.list_spaces(limit=5)
        print(f"✅ Spaces retrieved: {len(items)} items")
        for item in items:
            print(f"   - {item['name']}")
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_graphql())
