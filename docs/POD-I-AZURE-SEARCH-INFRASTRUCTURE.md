# POD-I: Azure AI Search Infrastructure Setup
**Role:** POD-I (Infrastructure)  
**Priority:** High  
**Estimated Effort:** 2-3 days  
**Dependencies:** None (blocks POD-L)  
**Source:** RAG-PRODUCTION-IMPLEMENTATION-ASSESSMENT.md

---

## 🎯 Objective

Provision and configure Azure AI Search service with vector capabilities to enable semantic search for EVA RAG system. Set up Azure Function App for automated document ingestion pipeline.

**Success Criteria:** Azure AI Search index accepting documents with embeddings, Function App triggering on blob uploads.

---

## 📊 Context

Current EVA demo uses Cosmos DB for document metadata but has no vector search capability. Documents are uploaded to Blob Storage but not indexed for retrieval. This blocks production RAG implementation.

**Current Architecture:**
```
User → Upload Doc → Blob Storage → [NOTHING HAPPENS]
                                        ↓
                                   Cosmos DB (metadata only)
```

**Target Architecture:**
```
User → Upload Doc → Blob Storage → Function Trigger
                                        ↓
                                   Extract + Chunk + Embed
                                        ↓
                                   Azure AI Search (vector index)
                                        ↓
                                   Cosmos DB (status update)
```

---

## 🔧 Technical Requirements

### Input
- Existing Azure subscription: `PayAsYouGo Subs 1`
- Resource group: `eva-suite-rg` (Canada Central)
- Blob Storage account: `evasuitestoragedev`
- Azure OpenAI endpoint: `canadacentral.api.cognitive.microsoft.com`

### Output
1. **Azure AI Search Service**
   - Name: `eva-search-canadacentral`
   - SKU: Standard (1 partition, 1 replica)
   - Index: `knowledge-index` with vector field
   
2. **Azure Function App**
   - Name: `eva-document-ingestion`
   - Runtime: Python 3.11
   - Plan: Consumption (serverless)
   - Trigger: Blob Storage events

3. **Updated Environment Variables**
   - `AZURE_SEARCH_ENDPOINT`
   - `AZURE_SEARCH_KEY`
   - `AZURE_SEARCH_INDEX_NAME`

### Constraints
- Must use Canada Central region (data residency)
- Standard tier required for vector search
- Function must complete within 10 minutes (Azure timeout)
- Cost target: <$300/month

---

## 📝 Implementation Steps

### Step 1: Create Azure AI Search Service

**Azure CLI:**
```powershell
# Login and set subscription
az login
az account set --subscription "PayAsYouGo Subs 1"

# Create AI Search service
az search service create `
  --name eva-search-canadacentral `
  --resource-group eva-suite-rg `
  --location canadacentral `
  --sku standard `
  --partition-count 1 `
  --replica-count 1

# Get admin key
$searchKey = az search admin-key show `
  --resource-group eva-suite-rg `
  --service-name eva-search-canadacentral `
  --query primaryKey -o tsv

Write-Host "Search Key: $searchKey" -ForegroundColor Green
```

**Validation:**
```powershell
# Test service connectivity
Invoke-WebRequest `
  -Uri "https://eva-search-canadacentral.search.windows.net/?api-version=2023-11-01" `
  -Headers @{"api-key"=$searchKey} `
  -UseBasicParsing | Select-Object StatusCode
```

Expected: `StatusCode: 200`

---

### Step 2: Create Search Index with Vector Field

**Index Schema (JSON):**
```json
{
  "name": "knowledge-index",
  "fields": [
    {
      "name": "id",
      "type": "Edm.String",
      "key": true,
      "searchable": false,
      "filterable": false,
      "sortable": false
    },
    {
      "name": "space_id",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "sortable": false,
      "facetable": false
    },
    {
      "name": "document_id",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "sortable": false
    },
    {
      "name": "chunk_id",
      "type": "Edm.String",
      "searchable": false,
      "filterable": false
    },
    {
      "name": "title",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "sortable": false,
      "analyzer": "standard.lucene"
    },
    {
      "name": "content",
      "type": "Edm.String",
      "searchable": true,
      "filterable": false,
      "sortable": false,
      "analyzer": "standard.lucene"
    },
    {
      "name": "embedding",
      "type": "Collection(Edm.Single)",
      "searchable": true,
      "filterable": false,
      "sortable": false,
      "dimensions": 1536,
      "vectorSearchProfile": "eva-vector-profile"
    },
    {
      "name": "page_number",
      "type": "Edm.Int32",
      "searchable": false,
      "filterable": true,
      "sortable": true
    },
    {
      "name": "language",
      "type": "Edm.String",
      "searchable": false,
      "filterable": true,
      "facetable": true
    },
    {
      "name": "created_at",
      "type": "Edm.DateTimeOffset",
      "searchable": false,
      "filterable": true,
      "sortable": true
    }
  ],
  "vectorSearch": {
    "algorithms": [
      {
        "name": "eva-hnsw-algorithm",
        "kind": "hnsw",
        "hnswParameters": {
          "m": 4,
          "efConstruction": 400,
          "efSearch": 500,
          "metric": "cosine"
        }
      }
    ],
    "profiles": [
      {
        "name": "eva-vector-profile",
        "algorithm": "eva-hnsw-algorithm"
      }
    ]
  },
  "semantic": {
    "configurations": [
      {
        "name": "eva-semantic-config",
        "prioritizedFields": {
          "titleField": {"fieldName": "title"},
          "contentFields": [{"fieldName": "content"}]
        }
      }
    ]
  }
}
```

**Create Index:**
```powershell
# Save schema to file
$schema = Get-Content .\search-index-schema.json -Raw

# Create index
$headers = @{
    "api-key" = $searchKey
    "Content-Type" = "application/json"
}

Invoke-RestMethod `
  -Uri "https://eva-search-canadacentral.search.windows.net/indexes?api-version=2023-11-01" `
  -Method POST `
  -Headers $headers `
  -Body $schema
```

**Validation:**
```powershell
# List indexes
Invoke-RestMethod `
  -Uri "https://eva-search-canadacentral.search.windows.net/indexes?api-version=2023-11-01" `
  -Headers @{"api-key"=$searchKey} `
  | Select-Object -ExpandProperty value `
  | Select-Object name, fields
```

Expected: `knowledge-index` with 10 fields including `embedding`

---

### Step 3: Create Azure Function App

**PowerShell:**
```powershell
# Create storage account for function (if not exists)
az storage account create `
  --name evafunctionsstorage `
  --resource-group eva-suite-rg `
  --location canadacentral `
  --sku Standard_LRS

# Create Function App
az functionapp create `
  --name eva-document-ingestion `
  --resource-group eva-suite-rg `
  --storage-account evafunctionsstorage `
  --runtime python `
  --runtime-version 3.11 `
  --functions-version 4 `
  --os-type Linux `
  --consumption-plan-location canadacentral

# Configure app settings
az functionapp config appsettings set `
  --name eva-document-ingestion `
  --resource-group eva-suite-rg `
  --settings `
    "AZURE_SEARCH_ENDPOINT=https://eva-search-canadacentral.search.windows.net" `
    "AZURE_SEARCH_KEY=$searchKey" `
    "AZURE_SEARCH_INDEX_NAME=knowledge-index" `
    "AZURE_OPENAI_ENDPOINT=https://canadacentral.api.cognitive.microsoft.com/" `
    "AZURE_OPENAI_KEY=$env:AZURE_OPENAI_KEY" `
    "COSMOS_DB_ENDPOINT=$env:COSMOS_DB_ENDPOINT" `
    "COSMOS_DB_KEY=$env:COSMOS_DB_KEY" `
    "COSMOS_DB_DATABASE=eva-core" `
    "BLOB_STORAGE_CONNECTION_STRING=$env:AZURE_STORAGE_CONNECTION_STRING"
```

**Validation:**
```powershell
# Check function app status
az functionapp show `
  --name eva-document-ingestion `
  --resource-group eva-suite-rg `
  --query state -o tsv
```

Expected: `Running`

---

### Step 4: Configure Blob Storage Event Grid

**Create Event Subscription:**
```powershell
# Get function app resource ID
$functionAppId = az functionapp show `
  --name eva-document-ingestion `
  --resource-group eva-suite-rg `
  --query id -o tsv

# Get storage account ID
$storageId = az storage account show `
  --name evasuitestoragedev `
  --resource-group eva-suite-rg `
  --query id -o tsv

# Create event subscription (will be configured after function deployment)
# This will be done after POD-L deploys the function code
Write-Host "Event Grid subscription will be configured after function deployment" -ForegroundColor Yellow
```

---

### Step 5: Update App Service Environment Variables

**Update eva-api-marco-prod:**
```powershell
# Add search configuration
az webapp config appsettings set `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --settings `
    "AZURE_SEARCH_ENDPOINT=https://eva-search-canadacentral.search.windows.net" `
    "AZURE_SEARCH_KEY=$searchKey" `
    "AZURE_SEARCH_INDEX_NAME=knowledge-index" `
    "EVA_MOCK_MODE=false"

# Restart app
az webapp restart `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg

Write-Host "Waiting for restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Verify health
Invoke-WebRequest `
  -Uri "https://eva-api-marco-prod.azurewebsites.net/health" `
  -UseBasicParsing | Select-Object StatusCode
```

Expected: `StatusCode: 200`

---

### Step 6: Store Secrets in Azure Key Vault (Optional but Recommended)

**Create Key Vault:**
```powershell
# Create Key Vault
az keyvault create `
  --name eva-keyvault-prod `
  --resource-group eva-suite-rg `
  --location canadacentral

# Add secrets
az keyvault secret set `
  --vault-name eva-keyvault-prod `
  --name "azure-search-key" `
  --value $searchKey

# Grant access to App Service
$appServicePrincipal = az webapp identity assign `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --query principalId -o tsv

az keyvault set-policy `
  --name eva-keyvault-prod `
  --object-id $appServicePrincipal `
  --secret-permissions get list
```

---

## ✅ Acceptance Criteria

- [ ] Azure AI Search service created in `canadacentral`
- [ ] `knowledge-index` exists with vector field (1536 dimensions)
- [ ] Index accepts test document with embedding (validate with sample upload)
- [ ] Azure Function App deployed and running
- [ ] Function App has all required environment variables
- [ ] App Service (eva-api-marco-prod) updated with search endpoint
- [ ] Health check returns 200 after configuration
- [ ] Cost estimate verified: <$300/month (Standard tier + Function consumption)

---

## 🧪 Validation

**Test 1: Index Health Check**
```powershell
# Check index stats
Invoke-RestMethod `
  -Uri "https://eva-search-canadacentral.search.windows.net/indexes/knowledge-index/stats?api-version=2023-11-01" `
  -Headers @{"api-key"=$searchKey}
```

Expected output:
```json
{
  "documentCount": 0,
  "storageSize": 0
}
```

**Test 2: Upload Test Document**
```powershell
# Sample document with embedding
$testDoc = @{
    value = @(
        @{
            "@search.action" = "upload"
            id = "test-doc-1"
            space_id = "test-space"
            document_id = "test-doc"
            chunk_id = "chunk-1"
            title = "Test Document"
            content = "This is a test document for validation"
            embedding = @(1..1536 | ForEach-Object { [Math]::Round((Get-Random -Minimum -1.0 -Maximum 1.0), 4) })
            page_number = 1
            language = "en"
            created_at = (Get-Date).ToString("o")
        }
    )
} | ConvertTo-Json -Depth 10

# Upload
Invoke-RestMethod `
  -Uri "https://eva-search-canadacentral.search.windows.net/indexes/knowledge-index/docs/index?api-version=2023-11-01" `
  -Method POST `
  -Headers @{"api-key"=$searchKey; "Content-Type"="application/json"} `
  -Body $testDoc

# Wait for indexing
Start-Sleep -Seconds 5

# Query to verify
Invoke-RestMethod `
  -Uri "https://eva-search-canadacentral.search.windows.net/indexes/knowledge-index/docs/test-doc-1?api-version=2023-11-01" `
  -Headers @{"api-key"=$searchKey}
```

Expected: Document returned with all fields

**Test 3: Function App Connectivity**
```powershell
# Check function app
Invoke-WebRequest `
  -Uri "https://eva-document-ingestion.azurewebsites.net" `
  -UseBasicParsing | Select-Object StatusCode
```

Expected: `StatusCode: 200` or `204` (no functions deployed yet is OK)

---

## 📚 Resources

### Azure Documentation
- [Azure AI Search Vector Search](https://learn.microsoft.com/azure/search/vector-search-overview)
- [Create Search Index](https://learn.microsoft.com/rest/api/searchservice/create-index)
- [Azure Functions Python Guide](https://learn.microsoft.com/azure/azure-functions/functions-reference-python)
- [Blob Trigger for Functions](https://learn.microsoft.com/azure/azure-functions/functions-bindings-storage-blob-trigger)

### Cost Calculators
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/)
- [AI Search Pricing](https://azure.microsoft.com/pricing/details/search/)

### Portal URLs
- [Azure Search Service](https://portal.azure.com/#blade/HubsExtension/BrowseResourceBlade/resourceType/Microsoft.Search%2FsearchServices)
- [Function Apps](https://portal.azure.com/#blade/HubsExtension/BrowseResource/resourceType/Microsoft.Web%2Fsites/kind/functionapp)
- [Resource Group](https://portal.azure.com/#@/resource/subscriptions/c59ee575-eb2a-4b51-a865-4b618f9add0a/resourceGroups/eva-suite-rg/overview)

---

## 🚨 Risks & Mitigation

**Risk 1: Index Creation Fails**  
**Impact:** High - Blocks entire RAG implementation  
**Mitigation:** Use Azure Portal UI as fallback, validate JSON schema with online validator first

**Risk 2: Standard Tier Cost**  
**Impact:** Medium - $250/month for Standard tier  
**Mitigation:** Start with Standard, monitor usage, downgrade to Basic if search volume <5 queries/sec

**Risk 3: Function App Cold Start**  
**Impact:** Low - First document takes 10-20s to process  
**Mitigation:** Use "Always On" for Function App (~$20/month) or accept cold start delay

**Risk 4: Vector Dimension Mismatch**  
**Impact:** High - Documents won't upload if embedding size wrong  
**Mitigation:** Validate embedding model returns 1536 dimensions (text-embedding-3-small default)

**Risk 5: Region Availability**  
**Impact:** High - Vector search not available in all regions  
**Mitigation:** Canada Central confirmed supported, fallback to East US if needed

---

## 📞 Handoff to POD-L

Once infrastructure is provisioned, POD-L will need:

1. **Search Service Endpoint:** `https://eva-search-canadacentral.search.windows.net`
2. **Search API Key:** (stored in Key Vault or environment variable)
3. **Index Name:** `knowledge-index`
4. **Function App Name:** `eva-document-ingestion`
5. **Function App URL:** `https://eva-document-ingestion.azurewebsites.net`

POD-L will implement:
- Python function code for blob trigger
- Document chunking logic
- Embedding generation
- Search index upload

---

**Created:** December 9, 2025  
**Assigned To:** POD-I (Infrastructure)  
**Status:** 📋 Ready for Implementation  
**Estimated Completion:** 2-3 business days  
**Blocks:** POD-L, POD-T, POD-D
