"""Direct Cosmos DB test - bypasses API"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from dotenv import load_dotenv
load_dotenv()

from eva_api.config import get_settings
from eva_api.services.cosmos_service import CosmosDBService

settings = get_settings()
print(f"Settings loaded:")
print(f"  Mock mode: {settings.mock_mode}")
print(f"  Cosmos endpoint: {settings.cosmos_db_endpoint}")
print(f"  Database: {settings.cosmos_db_database}")

cosmos = CosmosDBService(settings)
print(f"\nCosmos Service:")
print(f"  Mock mode: {cosmos.mock_mode}")
print(f"  Client: {cosmos.client is not None}")
print(f"  Spaces container: {cosmos.spaces_container is not None}")

# Try to list spaces directly
print(f"\n=== Direct Query Test ===")
if cosmos.spaces_container:
    query = "SELECT * FROM c"
    items = list(cosmos.spaces_container.query_items(query=query, enable_cross_partition_query=True))
    print(f"Found {len(items)} items in database")
    for item in items[:3]:
        print(f"  - {item.get('name', 'NO NAME')} (id: {item.get('id', 'NO ID')[:8]}...)")
else:
    print("ERROR: Spaces container is None!")
