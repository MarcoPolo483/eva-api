# POD-I: Azure AI Search Infrastructure Setup
**Role:** POD-I (Infrastructure)  
**Priority:** High (Blocking)  
**Estimated Effort:** 8 hours  
**Dependencies:** None (can start immediately)

---

## 🎯 Objective
Provision and configure Azure AI Search service with vector index to enable semantic search for EVA RAG system.

## 📊 Context
Current EVA API uses mock responses. To enable production RAG, we need:
- Azure AI Search service in Canada Central
- Vector index with 1536-dimension embeddings
- Hybrid search (keyword + vector)
- Multi-tenant isolation via space_id filtering

**Current Infrastructure:**
- ✅ Cosmos DB: eva-suite-cosmos-dev
- ✅ Blob Storage: evasuitestoragedev
- ✅ App Service: eva-api-marco-prod
- 🔴 AI Search: NOT CREATED

---

## 🔧 Technical Requirements

### Input
- Azure subscription: PayAsYouGo Subs 1
- Resource group: eva-suite-rg
- Location: canadacentral

### Output
- Azure AI Search service (Standard tier)
- Vector index: `knowledge-index`
- Connection credentials in Key Vault
- Environment variables updated in App Service

### Constraints
- Budget: ~$250/month for Standard tier
- Region: Canada Central (data residency)
- Protected B ready (private endpoints later)

---

## 📝 Implementation Steps

### 1. Create Azure AI Search Service
```powershell
# PowerShell script
$resourceGroup = "eva-suite-rg"
$searchService = "eva-search-prod"
$location = "canadacentral"

az search service create `
    --name $searchService `
    --resource-group $resourceGroup `
    --location $location `
    --sku Standard `
    --partition-count 1 `
    --replica-count 1 `
    --public-network-access Enabled

# Get admin key
$adminKey = az search admin-key show `
    --service-name $searchService `
    --resource-group $resourceGroup `
    --query primaryKey `
    --output tsv

Write-Host "✅ Search service created: https://$searchService.search.windows.net"
Write-Host "🔑 Admin key: $adminKey"
```

**Validation:**
```powershell
# Test service accessibility
Invoke-WebRequest -Uri "https://$searchService.search.windows.net?api-version=2023-11-01" `
    -Headers @{"api-key"=$adminKey} `
    -Method GET
# Expected: 200 OK with service metadata
```

### 2. Create Vector Search Index
```powershell
# Create index schema
$indexSchema = @{
    name = "knowledge-index"
    fields = @(
        @{name="id"; type="Edm.String"; key=$true; searchable=$false},
        @{name="space_id"; type="Edm.String"; filterable=$true; searchable=$false},
        @{name="document_id"; type="Edm.String"; filterable=$true; searchable=$false},
        @{name="chunk_id"; type="Edm.String"; searchable=$false},
        @{name="content"; type="Edm.String"; searchable=$true; analyzer="standard.lucene"},
        @{name="embedding"; type="Collection(Edm.Single)"; searchable=$true; 
          vectorSearchDimensions=1536; vectorSearchProfileName="vector-profile"},
        @{name="title"; type="Edm.String"; searchable=$true; facetable=$true},
        @{name="page_number"; type="Edm.Int32"; filterable=$true; sortable=$true},
        @{name="document_name"; type="Edm.String"; searchable=$true; filterable=$true},
        @{name="created_at"; type="Edm.DateTimeOffset"; filterable=$true; sortable=$true}
    )
    vectorSearch = @{
        profiles = @(
            @{
                name = "vector-profile"
                algorithm = "hnsw-algorithm"
            }
        )
        algorithms = @(
            @{
                name = "hnsw-algorithm"
                kind = "hnsw"
                hnswParameters = @{
                    m = 4
                    efConstruction = 400
                    efSearch = 500
                    metric = "cosine"
                }
            }
        )
    }
    semantic = @{
        configurations = @(
            @{
                name = "semantic-config"
                prioritizedFields = @{
                    titleField = @{fieldName="title"}
                    contentFields = @(@{fieldName="content"})
                }
            }
        )
    }
} | ConvertTo-Json -Depth 10

# Create index
Invoke-WebRequest `
    -Uri "https://$searchService.search.windows.net/indexes?api-version=2023-11-01" `
    -Method POST `
    -Headers @{
        "api-key"=$adminKey
        "Content-Type"="application/json"
    } `
    -Body $indexSchema

Write-Host "✅ Vector index 'knowledge-index' created"
```

**Validation:**
```powershell
# List indexes
az search index list --service-name $searchService --resource-group $resourceGroup
# Expected: knowledge-index with 10 fields including embedding vector
```

### 3. Store Credentials in Key Vault
```powershell
# Add to existing Key Vault (or create new)
$keyVaultName = "eva-suite-keyvault"

az keyvault secret set `
    --vault-name $keyVaultName `
    --name "AZURE-SEARCH-ENDPOINT" `
    --value "https://$searchService.search.windows.net"

az keyvault secret set `
    --vault-name $keyVaultName `
    --name "AZURE-SEARCH-KEY" `
    --value $adminKey

Write-Host "✅ Credentials stored in Key Vault"
```

### 4. Update App Service Configuration
```powershell
# Add environment variables to eva-api-marco-prod
az webapp config appsettings set `
    --name eva-api-marco-prod `
    --resource-group eva-suite-rg `
    --settings `
        AZURE_SEARCH_ENDPOINT="https://$searchService.search.windows.net" `
        AZURE_SEARCH_KEY="$adminKey" `
        AZURE_SEARCH_INDEX_NAME="knowledge-index" `
        RAG_TOP_K_RESULTS="10" `
        RAG_SCORE_THRESHOLD="0.7"

Write-Host "✅ App Service environment variables updated"
```

### 5. Configure Monitoring & Alerts
```powershell
# Enable diagnostic logs
az monitor diagnostic-settings create `
    --name "search-diagnostics" `
    --resource "/subscriptions/.../resourceGroups/eva-suite-rg/providers/Microsoft.Search/searchServices/$searchService" `
    --logs '[{"category":"OperationLogs","enabled":true}]' `
    --metrics '[{"category":"AllMetrics","enabled":true}]' `
    --workspace "/subscriptions/.../resourceGroups/eva-suite-rg/providers/Microsoft.OperationalInsights/workspaces/eva-logs"

# Create cost alert
az monitor metrics alert create `
    --name "search-high-queries" `
    --resource-group eva-suite-rg `
    --scopes "/subscriptions/.../resourceGroups/eva-suite-rg/providers/Microsoft.Search/searchServices/$searchService" `
    --condition "total SearchQueriesPerSecond > 10" `
    --description "Alert when search QPS exceeds 10"

Write-Host "✅ Monitoring configured"
```

---

## ✅ Acceptance Criteria
- [ ] Azure AI Search service created in canadacentral
- [ ] Service accessible via HTTPS with admin key
- [ ] Index `knowledge-index` exists with 10 fields
- [ ] Vector field configured: 1536 dimensions, HNSW algorithm
- [ ] Hybrid search enabled (keyword + semantic + vector)
- [ ] Credentials stored in Key Vault
- [ ] App Service environment variables updated
- [ ] Diagnostic logging enabled
- [ ] Cost alert configured (<$300/month threshold)
- [ ] README.md updated with connection details

---

## 🧪 Validation Commands

### Test Service Health
```powershell
# Get service statistics
$endpoint = "https://eva-search-prod.search.windows.net"
$stats = Invoke-WebRequest `
    -Uri "$endpoint/servicestats?api-version=2023-11-01" `
    -Headers @{"api-key"=$adminKey} | ConvertFrom-Json

Write-Host "Document Count: $($stats.counters.documentCount)"
Write-Host "Index Count: $($stats.counters.indexesCount)"
```

### Test Vector Search (Empty Index)
```powershell
# Sample vector search query
$searchQuery = @{
    search = "*"
    vectorQueries = @(
        @{
            vector = @(0.1) * 1536  # Dummy 1536-dim vector
            k = 10
            fields = "embedding"
        }
    )
    select = "id,title,content"
    top = 10
} | ConvertTo-Json -Depth 5

Invoke-WebRequest `
    -Uri "$endpoint/indexes/knowledge-index/docs/search?api-version=2023-11-01" `
    -Method POST `
    -Headers @{"api-key"=$adminKey; "Content-Type"="application/json"} `
    -Body $searchQuery
# Expected: 200 OK with empty results (no documents yet)
```

---

## 📚 Resources

**Azure Documentation:**
- [AI Search Overview](https://learn.microsoft.com/azure/search/search-what-is-azure-search)
- [Vector Search Guide](https://learn.microsoft.com/azure/search/vector-search-overview)
- [Index Schema Reference](https://learn.microsoft.com/rest/api/searchservice/create-index)

**Code References:**
- Assessment: `RAG-PRODUCTION-IMPLEMENTATION-ASSESSMENT.md`
- Config: `src/eva_api/config.py` (add AZURE_SEARCH_* settings)

**Azure Portal:**
- Search service: https://portal.azure.com/#@/resource/subscriptions/.../resourceGroups/eva-suite-rg/providers/Microsoft.Search/searchServices/eva-search-prod

---

## 🚨 Risks & Mitigation

**Risk:** Standard tier costs ~$250/month  
**Impact:** High (budget)  
**Mitigation:** Start with Basic tier ($75/month), upgrade if needed. Monitor query volume.

**Risk:** Index schema changes require reindexing  
**Impact:** Medium (downtime)  
**Mitigation:** Version index names (knowledge-index-v1), use aliases for zero-downtime migration.

**Risk:** HNSW parameters tuned incorrectly  
**Impact:** Low (search quality)  
**Mitigation:** Use default parameters initially (m=4, efConstruction=400), tune based on benchmarks.

**Risk:** Cross-region latency if documents outside Canada  
**Impact:** Low (performance)  
**Mitigation:** All Azure resources already in canadacentral, data residency compliant.

---

## 📊 Cost Breakdown

**Azure AI Search - Standard Tier:**
- Base: $250.56/month
- 1 partition (25GB storage)
- 1 replica (high availability)
- Included: 1000 QPS, unlimited documents

**Optimization Options:**
- Basic tier: $75.14/month (sufficient for <1000 queries/day)
- Free tier: $0/month (50MB storage, 3 indexes max) - only for dev/test

**Recommendation:** Start with Basic tier, monitor usage for 1 month, upgrade if needed.

---

**Created:** December 9, 2025  
**Assigned To:** POD-I (Infrastructure Team)  
**Status:** 📋 Ready for Implementation  
**Estimated Time:** 8 hours (including testing)
