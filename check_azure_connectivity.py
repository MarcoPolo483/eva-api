"""Check Azure connectivity and configuration."""
import sys
sys.path.insert(0, 'src')

from eva_api.config import get_settings

settings = get_settings()

print("\n" + "="*70)
print("AZURE CONFIGURATION CHECK")
print("="*70)

# Cosmos DB
print("\n[Cosmos DB]")
print(f"  Endpoint: {settings.cosmos_db_endpoint or 'NOT SET'}")
if settings.cosmos_db_key:
    print(f"  Key: ***{settings.cosmos_db_key[-4:]}")
else:
    print(f"  Key: NOT SET")
print(f"  Database: {settings.cosmos_db_database}")
print(f"  Container (API Keys): {settings.cosmos_db_container_api_keys}")

# Blob Storage
print("\n[Blob Storage]")
print(f"  Account Name: {settings.azure_storage_account_name or 'NOT SET'}")
if settings.azure_storage_account_key:
    print(f"  Account Key: ***{settings.azure_storage_account_key[-4:]}")
else:
    print(f"  Account Key: NOT SET")
print(f"  Container: {settings.azure_storage_container_documents}")
if settings.blob_storage_connection_string:
    print(f"  Connection String: Configured")
else:
    print(f"  Connection String: NOT SET")

# Azure AD
print("\n[Azure AD B2C]")
print(f"  Tenant ID: {settings.azure_ad_b2c_tenant_id or 'NOT SET'}")
print(f"  Client ID: {settings.azure_ad_b2c_client_id or 'NOT SET'}")
print(f"  Client Secret: {'***' + settings.azure_ad_b2c_client_secret[-4:] if settings.azure_ad_b2c_client_secret else 'NOT SET'}")

print("\n[Azure Entra ID]")
print(f"  Tenant ID: {settings.azure_entra_tenant_id or 'NOT SET'}")
print(f"  Client ID: {settings.azure_entra_client_id or 'NOT SET'}")
print(f"  Client Secret: {'***' + settings.azure_entra_client_secret[-4:] if settings.azure_entra_client_secret else 'NOT SET'}")

# JWT
print("\n[JWT Configuration]")
print(f"  Issuer: {settings.jwt_issuer or 'NOT SET'}")
print(f"  Audience: {settings.jwt_audience or 'NOT SET'}")
print(f"  Algorithm: {settings.jwt_algorithm}")

print("\n" + "="*70)
print("CONNECTIVITY TEST")
print("="*70)

# Test Cosmos DB
print("\n[Testing Cosmos DB...]")
try:
    from azure.cosmos import CosmosClient
    if settings.cosmos_db_endpoint and settings.cosmos_db_key:
        client = CosmosClient(settings.cosmos_db_endpoint, settings.cosmos_db_key)
        databases = list(client.list_databases())
        print(f"  Status: CONNECTED")
        print(f"  Databases: {len(databases)} found")
        for db in databases:
            print(f"    - {db['id']}")
    else:
        print(f"  Status: NOT CONFIGURED (missing credentials)")
except Exception as e:
    print(f"  Status: ERROR - {str(e)[:100]}")

# Test Blob Storage
print("\n[Testing Blob Storage...]")
try:
    from azure.storage.blob import BlobServiceClient
    if settings.blob_storage_connection_string:
        blob_service = BlobServiceClient.from_connection_string(settings.blob_storage_connection_string)
        containers = list(blob_service.list_containers(results_per_page=5))
        print(f"  Status: CONNECTED")
        print(f"  Containers: {len(containers)} found")
        for container in containers:
            print(f"    - {container['name']}")
    else:
        print(f"  Status: NOT CONFIGURED (missing credentials)")
except Exception as e:
    print(f"  Status: ERROR - {str(e)[:100]}")

print("\n" + "="*70)
