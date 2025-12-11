# Integration Testing

Integration tests for EVA API with actual Azure services.

## 🔧 Prerequisites

### Azure Resources Required

1. **Azure Cosmos DB**
   - NoSQL API account
   - Database: `eva-api`
   - Containers: `spaces`, `documents`, `queries`

2. **Azure Blob Storage**
   - Storage account with blob service
   - Container: `documents`

3. **Azure OpenAI**
   - GPT-4 or GPT-3.5-turbo deployment
   - Embedding model deployment (optional)

### Environment Variables

Set these before running integration tests:

```powershell
$env:COSMOS_DB_ENDPOINT = "https://<account>.documents.azure.com:443/"
$env:COSMOS_DB_KEY = "<your-key>"
$env:AZURE_STORAGE_ACCOUNT_NAME = "<account-name>"
$env:AZURE_STORAGE_ACCOUNT_KEY = "<your-key>"
$env:AZURE_OPENAI_ENDPOINT = "https://<resource>.openai.azure.com/"
$env:AZURE_OPENAI_KEY = "<your-key>"
$env:AZURE_OPENAI_DEPLOYMENT_NAME = "gpt-4"
```

## 🚀 Running Tests

### Run All Integration Tests

```powershell
pytest tests/integration/ -v -m integration
```

### Run Specific Service Tests

```powershell
# Cosmos DB only
pytest tests/integration/test_cosmos_integration.py -v

# Blob Storage only
pytest tests/integration/test_blob_integration.py -v

# Query Service (Azure OpenAI) only
pytest tests/integration/test_query_integration.py -v

# GraphQL full stack
pytest tests/integration/test_graphql_integration.py -v
```

### Run with Markers

```powershell
# Only Cosmos tests
pytest tests/integration/ -m cosmos -v

# Only Blob Storage tests
pytest tests/integration/ -m blob -v

# Only Azure OpenAI tests
pytest tests/integration/ -m openai -v
```

## 📋 Test Coverage

### Cosmos DB Service (test_cosmos_integration.py)
- ✅ Create and retrieve spaces
- ✅ List spaces with pagination
- ✅ Update space metadata
- ✅ Atomic document count operations
- ✅ Document metadata CRUD
- ✅ Partition key handling

### Blob Storage Service (test_blob_integration.py)
- ✅ Upload and download documents
- ✅ Generate SAS URLs with expiry
- ✅ Delete documents
- ✅ Hierarchical blob naming
- ✅ Content type handling
- ✅ Metadata storage

### Query Service (test_query_integration.py)
- ✅ Full RAG pipeline (retrieve → context → OpenAI → store)
- ✅ Query status tracking
- ✅ Context building from multiple documents
- ✅ Error handling with no documents
- ✅ Background task processing

### GraphQL API (test_graphql_integration.py)
- ✅ Space creation via mutations
- ✅ Space querying with filters
- ✅ Pagination with cursors
- ✅ Space updates
- ✅ Query submission
- ✅ Subscription definition
- ✅ Error handling

## 🔒 CI/CD Integration

### GitHub Actions Setup

Add secrets to GitHub repository:

```yaml
AZURE_CREDENTIALS: <service-principal-json>
COSMOS_DB_ENDPOINT: https://...
COSMOS_DB_KEY: <key>
AZURE_STORAGE_ACCOUNT_NAME: <name>
AZURE_STORAGE_ACCOUNT_KEY: <key>
AZURE_OPENAI_ENDPOINT: https://...
AZURE_OPENAI_KEY: <key>
```

### Workflow Example

```yaml
- name: Run Integration Tests
  env:
    COSMOS_DB_ENDPOINT: ${{ secrets.COSMOS_DB_ENDPOINT }}
    COSMOS_DB_KEY: ${{ secrets.COSMOS_DB_KEY }}
    AZURE_STORAGE_ACCOUNT_NAME: ${{ secrets.AZURE_STORAGE_ACCOUNT_NAME }}
    AZURE_STORAGE_ACCOUNT_KEY: ${{ secrets.AZURE_STORAGE_ACCOUNT_KEY }}
    AZURE_OPENAI_ENDPOINT: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    AZURE_OPENAI_KEY: ${{ secrets.AZURE_OPENAI_KEY }}
  run: |
    pytest tests/integration/ -v -m integration --cov=src/eva_api
```

## 📊 Expected Results

When all Azure services are configured:

```
tests/integration/test_cosmos_integration.py::test_cosmos_create_and_get_space PASSED
tests/integration/test_cosmos_integration.py::test_cosmos_list_spaces_pagination PASSED
tests/integration/test_cosmos_integration.py::test_cosmos_update_space PASSED
tests/integration/test_cosmos_integration.py::test_cosmos_document_count PASSED
tests/integration/test_cosmos_integration.py::test_cosmos_document_metadata PASSED
tests/integration/test_blob_integration.py::test_blob_upload_and_download PASSED
tests/integration/test_blob_integration.py::test_blob_generate_sas_url PASSED
tests/integration/test_blob_integration.py::test_blob_delete PASSED
tests/integration/test_blob_integration.py::test_blob_hierarchical_naming PASSED
tests/integration/test_query_integration.py::test_query_rag_pipeline PASSED
tests/integration/test_query_integration.py::test_query_status_tracking PASSED
tests/integration/test_query_integration.py::test_query_context_building PASSED
tests/integration/test_query_integration.py::test_query_error_handling PASSED
tests/integration/test_graphql_integration.py::test_graphql_create_and_query_space PASSED
tests/integration/test_graphql_integration.py::test_graphql_list_spaces_pagination PASSED
tests/integration/test_graphql_integration.py::test_graphql_update_space PASSED
tests/integration/test_graphql_integration.py::test_graphql_query_submission PASSED
tests/integration/test_graphql_integration.py::test_graphql_subscription_connection PASSED
tests/integration/test_graphql_integration.py::test_graphql_error_handling PASSED

======= 19 passed in X.XXs =======
```

## ⚠️ Without Azure Credentials

Tests will be skipped with message:

```
SKIPPED [19] tests/integration/conftest.py:XX: Cosmos DB credentials not configured
```

This is expected behavior. Integration tests require actual Azure resources.

## 🧹 Cleanup

Tests automatically clean up created resources (spaces, documents, blobs) in `finally` blocks. If tests fail, you may need to manually clean up:

```powershell
# List test spaces
az cosmosdb sql container query \
  --account-name <account> \
  --database-name eva-api \
  --container-name spaces \
  --query "SELECT * FROM c WHERE c.name LIKE '%Test%'"

# Delete test blobs
az storage blob list \
  --account-name <account> \
  --container-name documents \
  --prefix "test-"
```

## 📈 Coverage Impact

Running integration tests increases coverage to **~85%** by exercising:
- Azure SDK client initialization
- Network I/O with actual services
- Background task execution
- GraphQL context injection
- Error paths with real failures

---

**Status**: NOT EXECUTED - REVIEW CAREFULLY  
**Last Updated**: 2025-12-07T21:55:00Z (2025-12-07 16:55:00 EST)
