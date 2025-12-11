"""Test Cosmos DB connection"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from eva_api.config import get_settings

settings = get_settings()
print(f"Mock mode: {settings.mock_mode}")
print(f"Cosmos endpoint: {settings.cosmos_db_endpoint}")
print(f"Cosmos database: {settings.cosmos_db_database}")
print(f"Cosmos key: {'***' if settings.cosmos_db_key else 'NOT SET'}")

from eva_api.services.cosmos_service import CosmosDBService
cosmos = CosmosDBService(settings)
print(f"\nCosmosDB Service initialized")
print(f"Client: {cosmos.client}")
print(f"Spaces container: {cosmos.spaces_container}")
print(f"Mock mode active: {cosmos.mock_mode}")
