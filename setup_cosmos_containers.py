"""Setup Cosmos DB containers for EVA API."""
import sys
sys.path.insert(0, 'src')

from azure.cosmos import CosmosClient, PartitionKey
from eva_api.config import get_settings

def setup_cosmos_containers():
    """Create required Cosmos DB containers."""
    settings = get_settings()
    
    print("\n" + "="*70)
    print("COSMOS DB CONTAINER SETUP")
    print("="*70)
    
    # Initialize client
    print(f"\nConnecting to: {settings.cosmos_db_endpoint}")
    client = CosmosClient(settings.cosmos_db_endpoint, settings.cosmos_db_key)
    
    # Get database
    database_name = settings.cosmos_db_database
    print(f"Using database: {database_name}")
    database = client.get_database_client(database_name)
    
    # Container configurations for serverless account (no throughput parameter)
    containers = [
        {
            "id": "api_keys",
            "partition_key": PartitionKey(path="/tenant_id"),
            "description": "API key storage with tenant-based partitioning"
        },
        {
            "id": "spaces",
            "partition_key": PartitionKey(path="/tenant_id"),
            "description": "Workspace spaces for multi-tenancy"
        },
        {
            "id": "queries",
            "partition_key": PartitionKey(path="/space_id"),
            "description": "Query execution tracking"
        }
    ]
    
    print("\nCreating containers...")
    for container_config in containers:
        container_id = container_config["id"]
        partition_key = container_config["partition_key"]
        description = container_config["description"]
        
        try:
            # Try to get existing container
            container = database.get_container_client(container_id)
            container.read()
            print(f"  [EXISTS] {container_id} - {description}")
        except Exception:
            # Container doesn't exist, create it (without throughput for serverless)
            try:
                database.create_container(
                    id=container_id,
                    partition_key=partition_key
                )
                print(f"  [CREATED] {container_id} - {description}")
            except Exception as e:
                print(f"  [ERROR] {container_id} - {str(e)[:100]}")
    
    print("\n" + "="*70)
    print("CONTAINER SETUP COMPLETE")
    print("="*70)
    
    # Verify containers
    print("\nVerifying containers in database...")
    containers_list = list(database.list_containers())
    for container in containers_list:
        print(f"  - {container['id']}")
    
    print(f"\nTotal containers: {len(containers_list)}")

if __name__ == "__main__":
    try:
        setup_cosmos_containers()
        print("\n✓ Setup completed successfully!")
    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
