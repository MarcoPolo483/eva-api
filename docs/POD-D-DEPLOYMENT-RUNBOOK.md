# POD-D: Production Deployment and Monitoring Runbook
**Role:** POD-D (Deployment)  
**Priority:** High  
**Estimated Effort:** 2-3 days  
**Dependencies:** POD-I (infrastructure), POD-L (code), POD-T (tests passing)  
**Source:** RAG-PRODUCTION-IMPLEMENTATION-ASSESSMENT.md

---

## 🎯 Objective

Deploy production RAG implementation to Azure with zero downtime, comprehensive monitoring, and rollback procedures. Ensure all Azure resources are properly configured and operational before enabling production traffic.

**Success Criteria:** Production deployment complete with <1 minute downtime, all health checks green, monitoring dashboards operational, rollback tested and documented.

---

## 📊 Context

Current production environment (`eva-api-marco-prod`) runs demo RAG with `EVA_MOCK_MODE=true`. Transitioning to production RAG requires:
1. Azure AI Search service provisioned (POD-I)
2. Azure Function for document ingestion deployed (POD-L)
3. App Service updated with new code (POD-L)
4. Environment variables configured
5. Documents re-indexed in new search service
6. Monitoring and alerts configured
7. Rollback plan validated

**Deployment Strategy:** Blue-Green deployment using staging slot to minimize downtime.

---

## 🔧 Technical Requirements

### Input (from Previous PODs)
- **POD-I:** Azure AI Search service `eva-search-canadacentral`, index `knowledge-index`
- **POD-L:** Updated `query_service.py` with production logic, Azure Function code
- **POD-T:** Test report confirming all tests pass, performance benchmarks

### Output
1. **Production Deployment**
   - App Service: `eva-api-marco-prod` running production code
   - Function App: `eva-document-ingestion` deployed and enabled
   - Environment variables: All production settings configured

2. **Monitoring Setup**
   - Application Insights dashboards
   - Log Analytics queries for errors
   - Alerts for failures and performance degradation

3. **Documentation**
   - Deployment checklist
   - Rollback procedures
   - Runbook for common operations

### Constraints
- Zero data loss (existing Cosmos DB data preserved)
- <1 minute downtime window
- All secrets stored in Azure Key Vault (no plaintext credentials)
- Rollback plan must be validated before production deployment
- Cost monitoring enabled (budget alert at $400/month)

---

## 📝 Deployment Steps

### Phase 1: Pre-Deployment Validation (30 minutes)

#### Step 1.1: Verify POD-I Infrastructure

**Checklist:**
```powershell
# Verify Azure AI Search service
az search service show `
  --name eva-search-canadacentral `
  --resource-group eva-suite-rg `
  --query "status" -o tsv

# Expected: "running"

# Verify search index exists
$searchKey = az search admin-key show `
  --resource-group eva-suite-rg `
  --service-name eva-search-canadacentral `
  --query primaryKey -o tsv

$indexCheck = Invoke-RestMethod `
  -Uri "https://eva-search-canadacentral.search.windows.net/indexes/knowledge-index?api-version=2023-11-01" `
  -Headers @{"api-key"=$searchKey}

Write-Host "Index: $($indexCheck.name), Fields: $($indexCheck.fields.Count)" -ForegroundColor Green

# Expected: "Index: knowledge-index, Fields: 10"

# Verify Function App deployed
az functionapp show `
  --name eva-document-ingestion `
  --resource-group eva-suite-rg `
  --query "state" -o tsv

# Expected: "Running"
```

**Sign-off:** ✅ POD-I infrastructure operational

---

#### Step 1.2: Verify POD-L Code Changes

**Checklist:**
```powershell
# Check latest commit includes POD-L changes
cd "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api"
git log --oneline -5

# Expected: Recent commit with "POD-L RAG implementation"

# Verify key files updated
git diff origin/main --name-only | Select-String "query_service.py|config.py|requirements.txt"

# Expected: All 3 files modified

# Verify Azure Function code exists
Test-Path ".\functions\document-ingestion\__init__.py"
Test-Path ".\functions\document-ingestion\function.json"
Test-Path ".\functions\document-ingestion\requirements.txt"

# Expected: All True
```

**Sign-off:** ✅ POD-L code ready for deployment

---

#### Step 1.3: Verify POD-T Tests Passed

**Checklist:**
```powershell
# Run full test suite locally
pytest tests/ -v --cov=src/eva_api --cov-report=html

# Expected: All tests pass, coverage >80%

# Check CI/CD pipeline status
# Navigate to GitHub Actions and verify latest run is green
```

**Sign-off:** ✅ POD-T tests passed

---

### Phase 2: Staging Deployment (1 hour)

#### Step 2.1: Create Staging Slot

**PowerShell:**
```powershell
# Create staging slot for blue-green deployment
az webapp deployment slot create `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging

# Copy production settings to staging
az webapp config appsettings list `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  -o json | Out-File staging-settings.json

az webapp config appsettings set `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging `
  --settings @staging-settings.json
```

**Validation:**
```powershell
# Check staging slot created
az webapp deployment slot list `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --query "[].name" -o tsv

# Expected: staging
```

---

#### Step 2.2: Deploy Code to Staging Slot

**PowerShell:**
```powershell
# Build deployment package
cd "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api"

# Create deployment ZIP
Compress-Archive -Path "src\*","requirements.txt","startup.py" -DestinationPath deploy.zip -Force

# Deploy to staging slot
az webapp deployment source config-zip `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging `
  --src deploy.zip

# Wait for deployment to complete
Start-Sleep -Seconds 60

# Restart staging slot
az webapp restart `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging

Write-Host "Waiting for app to restart..." -ForegroundColor Yellow
Start-Sleep -Seconds 30
```

**Validation:**
```powershell
# Check staging health endpoint
Invoke-WebRequest `
  -Uri "https://eva-api-marco-prod-staging.azurewebsites.net/health" `
  -UseBasicParsing | Select-Object StatusCode

# Expected: StatusCode : 200
```

---

#### Step 2.3: Update Staging Environment Variables

**PowerShell:**
```powershell
# Get secrets from Key Vault (if configured)
$searchKey = az keyvault secret show `
  --vault-name eva-keyvault-prod `
  --name azure-search-key `
  --query value -o tsv

# If Key Vault not set up, get from search service directly
if (-not $searchKey) {
    $searchKey = az search admin-key show `
      --resource-group eva-suite-rg `
      --service-name eva-search-canadacentral `
      --query primaryKey -o tsv
}

# Update staging slot settings
az webapp config appsettings set `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging `
  --settings `
    "AZURE_SEARCH_ENDPOINT=https://eva-search-canadacentral.search.windows.net" `
    "AZURE_SEARCH_KEY=$searchKey" `
    "AZURE_SEARCH_INDEX_NAME=knowledge-index" `
    "AZURE_SEARCH_TOP_K=10" `
    "AZURE_SEARCH_SCORE_THRESHOLD=0.7" `
    "EVA_MOCK_MODE=false"

# Restart to apply settings
az webapp restart `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging

Start-Sleep -Seconds 30
```

**Validation:**
```powershell
# Check environment variables set
az webapp config appsettings list `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging `
  --query "[?name=='EVA_MOCK_MODE'].value" -o tsv

# Expected: false
```

---

#### Step 2.4: Test Staging Deployment

**Smoke Tests:**
```powershell
# Test 1: Health check
$stagingUrl = "https://eva-api-marco-prod-staging.azurewebsites.net"

Invoke-WebRequest -Uri "$stagingUrl/health" -UseBasicParsing | Select-Object StatusCode
# Expected: 200

# Test 2: Spaces endpoint
$spaces = Invoke-RestMethod `
  -Uri "$stagingUrl/api/v1/spaces" `
  -Headers @{"X-API-Key"="demo-api-key"}

Write-Host "Spaces: $($spaces.Count)" -ForegroundColor Green
# Expected: 15 spaces

# Test 3: Submit query (production RAG)
$query = @{
    space_id = ($spaces[0].id)
    question = "What is this space about?"
    language = "en"
} | ConvertTo-Json

$response = Invoke-RestMethod `
  -Uri "$stagingUrl/api/v1/queries" `
  -Method POST `
  -Headers @{"X-API-Key"="demo-api-key"} `
  -ContentType "application/json" `
  -Body $query

$queryId = $response.query_id
Write-Host "Query ID: $queryId" -ForegroundColor Green

# Wait for processing
Start-Sleep -Seconds 10

# Test 4: Get result
$result = Invoke-RestMethod `
  -Uri "$stagingUrl/api/v1/queries/$queryId/result" `
  -Headers @{"X-API-Key"="demo-api-key"}

Write-Host "Status: $($result.status)" -ForegroundColor Green
Write-Host "Answer: $($result.answer.Substring(0, [Math]::Min(100, $result.answer.Length)))..." -ForegroundColor Cyan
Write-Host "Sources: $($result.sources.Count)" -ForegroundColor Green

# Validate production RAG (not mock)
if ($result.answer -notlike "*démonstration*" -and $result.sources.Count -gt 0) {
    Write-Host "✅ Production RAG working in staging" -ForegroundColor Green
} else {
    Write-Host "❌ Staging may still be using mock mode" -ForegroundColor Red
}
```

**Sign-off:** ✅ Staging deployment validated

---

### Phase 3: Production Deployment (15 minutes)

#### Step 3.1: Notify Stakeholders

**Notification Template:**
```
Subject: EVA Production Deployment - RAG Implementation

Hi Team,

We will be deploying the production RAG implementation today at [TIME].

Expected downtime: <1 minute
Changes:
- Azure AI Search integration for document retrieval
- Azure OpenAI GPT-4 for answer generation
- Bilingual response support (EN/FR)
- Improved citation accuracy

Rollback plan validated and ready if needed.

Status updates: [SLACK CHANNEL or EMAIL]

Thanks,
Marco & EVA Team
```

---

#### Step 3.2: Swap Staging to Production

**PowerShell:**
```powershell
# Record timestamp
$deploymentTime = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "Starting production swap at $deploymentTime" -ForegroundColor Yellow

# Swap staging slot to production (blue-green deployment)
az webapp deployment slot swap `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging `
  --target-slot production

Write-Host "Swap initiated, waiting for completion..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# Verify swap completed
$productionState = az webapp show `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --query "state" -o tsv

Write-Host "Production state: $productionState" -ForegroundColor Green
```

**Downtime Window:** Typically 30-45 seconds

---

#### Step 3.3: Validate Production Deployment

**Smoke Tests (Run Immediately):**
```powershell
$prodUrl = "https://eva-api-marco-prod.azurewebsites.net"

# Test 1: Health check
$healthStart = Get-Date
$healthResponse = Invoke-WebRequest -Uri "$prodUrl/health" -UseBasicParsing
$healthTime = (Get-Date) - $healthStart

Write-Host "Health check: $($healthResponse.StatusCode) (${healthTime.TotalMilliseconds}ms)" -ForegroundColor Green

# Test 2: Query endpoint
$queryBody = @{
    space_id = "test-space-id"
    question = "Test production deployment"
    language = "en"
} | ConvertTo-Json

$queryStart = Get-Date
$queryResponse = Invoke-RestMethod `
  -Uri "$prodUrl/api/v1/queries" `
  -Method POST `
  -Headers @{"X-API-Key"="demo-api-key"} `
  -ContentType "application/json" `
  -Body $queryBody

$queryTime = (Get-Date) - $queryStart

if ($queryResponse.query_id) {
    Write-Host "✅ Query submitted: $($queryResponse.query_id) (${queryTime.TotalMilliseconds}ms)" -ForegroundColor Green
} else {
    Write-Host "❌ Query submission failed" -ForegroundColor Red
}

# Test 3: Frontend connectivity
$frontendUrl = "https://evasuitestoragedev.z9.web.core.windows.net"
$frontendResponse = Invoke-WebRequest -Uri $frontendUrl -UseBasicParsing

if ($frontendResponse.StatusCode -eq 200) {
    Write-Host "✅ Frontend accessible" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend issue" -ForegroundColor Red
}
```

**Expected Results:**
- Health check: 200 OK (<500ms)
- Query submission: 202 Accepted (<1000ms)
- Frontend: 200 OK

**Sign-off:** ✅ Production deployment successful

---

### Phase 4: Document Re-Indexing (2-4 hours)

#### Step 4.1: Trigger Document Re-Indexing

**PowerShell:**
```powershell
# List all existing documents in Cosmos DB
$cosmosEndpoint = $env:COSMOS_DB_ENDPOINT
$cosmosKey = $env:COSMOS_DB_KEY

# Use Azure CLI to query documents
az cosmosdb sql query `
  --account-name eva-suite-cosmos-dev `
  --database-name eva-core `
  --container-name documents `
  --query-string "SELECT c.id, c.space_id, c.blob_path FROM c" `
  -o json | Out-File documents-to-reindex.json

$documents = Get-Content documents-to-reindex.json | ConvertFrom-Json

Write-Host "Found $($documents.Count) documents to re-index" -ForegroundColor Yellow

# Trigger re-indexing by copying blobs (triggers Function)
$storageAccount = "evasuitestoragedev"

foreach ($doc in $documents) {
    Write-Host "Re-indexing: $($doc.id) in space $($doc.space_id)" -ForegroundColor Cyan
    
    # Copy blob to trigger ingestion function
    az storage blob copy start `
      --account-name $storageAccount `
      --destination-container "spaces" `
      --destination-blob "$($doc.space_id)/documents/$($doc.id)-reindex.pdf" `
      --source-container "spaces" `
      --source-blob "$($doc.blob_path)" `
      --auth-mode login
    
    Start-Sleep -Seconds 2  # Rate limit
}

Write-Host "Re-indexing triggered for $($documents.Count) documents" -ForegroundColor Green
Write-Host "Monitor Azure Function logs for progress" -ForegroundColor Yellow
```

---

#### Step 4.2: Monitor Re-Indexing Progress

**PowerShell:**
```powershell
# Check Azure Function execution logs
az functionapp log deployment list `
  --name eva-document-ingestion `
  --resource-group eva-suite-rg `
  --query "[0].{status:status, message:message, timestamp:timestamp}"

# Check search index document count
$searchKey = az search admin-key show `
  --resource-group eva-suite-rg `
  --service-name eva-search-canadacentral `
  --query primaryKey -o tsv

$stats = Invoke-RestMethod `
  -Uri "https://eva-search-canadacentral.search.windows.net/indexes/knowledge-index/stats?api-version=2023-11-01" `
  -Headers @{"api-key"=$searchKey}

Write-Host "Search Index - Documents: $($stats.documentCount), Storage: $($stats.storageSize) bytes" -ForegroundColor Green

# Expected: documentCount increases over time as indexing progresses
```

**Monitor every 15 minutes until complete.**

---

### Phase 5: Monitoring and Alerts Setup (1 hour)

#### Step 5.1: Configure Application Insights

**PowerShell:**
```powershell
# Get Application Insights resource
$appInsightsId = az monitor app-insights component show `
  --app eva-api-insights `
  --resource-group eva-suite-rg `
  --query "id" -o tsv

# Create alert rule for query failures
az monitor metrics alert create `
  --name "RAG Query Failures" `
  --resource-group eva-suite-rg `
  --scopes $appInsightsId `
  --condition "count requests/failed > 10" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action-group "eva-alerts" `
  --description "Alert when >10 RAG queries fail in 5 minutes"

# Create alert rule for slow response times
az monitor metrics alert create `
  --name "RAG Slow Response" `
  --resource-group eva-suite-rg `
  --scopes $appInsightsId `
  --condition "avg requests/duration > 5000" `
  --window-size 5m `
  --evaluation-frequency 1m `
  --action-group "eva-alerts" `
  --description "Alert when avg response time >5 seconds"
```

---

#### Step 5.2: Create Custom Dashboard

**Azure Portal Steps:**
1. Navigate to: https://portal.azure.com/#dashboard
2. Click **+ New dashboard** → Name: "EVA RAG Production"
3. Add tiles:
   - **Application Insights:** Request rate, response time, failed requests
   - **Azure AI Search:** Query rate, index size, throttling
   - **Function App:** Executions, errors, duration
   - **Cosmos DB:** Request units, latency, storage
4. Save dashboard

**Custom Kusto Queries:**
```kql
// Query processing time distribution
requests
| where name contains "queries"
| summarize 
    p50 = percentile(duration, 50),
    p95 = percentile(duration, 95),
    p99 = percentile(duration, 99)
  by bin(timestamp, 1h)
| render timechart

// Top error messages
exceptions
| where outerMessage contains "query" or outerMessage contains "search"
| summarize count() by outerMessage
| top 10 by count_

// Function execution success rate
traces
| where message contains "document" and message contains "ingestion"
| extend success = iff(message contains "success", 1, 0)
| summarize 
    total = count(),
    successful = sum(success),
    failed = sum(1 - success)
  by bin(timestamp, 10m)
| extend success_rate = successful * 100.0 / total
| render timechart
```

---

#### Step 5.3: Configure Cost Alerts

**PowerShell:**
```powershell
# Create budget alert at $400/month threshold
az consumption budget create `
  --budget-name "EVA RAG Production Budget" `
  --amount 400 `
  --time-grain Monthly `
  --start-date (Get-Date -Format "yyyy-MM-01") `
  --end-date (Get-Date).AddYears(1).ToString("yyyy-MM-dd") `
  --resource-group eva-suite-rg `
  --notifications @{
      "Threshold80"=@{
          "enabled"=$true;
          "operator"="GreaterThan";
          "threshold"=80;
          "contactEmails"=@("marco.presta@example.com")
      };
      "Threshold100"=@{
          "enabled"=$true;
          "operator"="GreaterThan";
          "threshold"=100;
          "contactEmails"=@("marco.presta@example.com")
      }
  }
```

---

### Phase 6: Post-Deployment Validation (30 minutes)

#### Step 6.1: Run Full Smoke Test Suite

**PowerShell Script:**
```powershell
# test-production-rag.ps1
$baseUrl = "https://eva-api-marco-prod.azurewebsites.net"
$apiKey = "demo-api-key"

Write-Host "=== EVA Production RAG Smoke Tests ===" -ForegroundColor Cyan

# Test 1: Health Check
Write-Host "`n[Test 1] Health Check" -ForegroundColor Yellow
$health = Invoke-WebRequest -Uri "$baseUrl/health" -UseBasicParsing
if ($health.StatusCode -eq 200) {
    Write-Host "✅ PASS" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: Status $($health.StatusCode)" -ForegroundColor Red
}

# Test 2: List Spaces
Write-Host "`n[Test 2] List Spaces" -ForegroundColor Yellow
$spaces = Invoke-RestMethod -Uri "$baseUrl/api/v1/spaces" -Headers @{"X-API-Key"=$apiKey}
if ($spaces.Count -ge 15) {
    Write-Host "✅ PASS: $($spaces.Count) spaces" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: Only $($spaces.Count) spaces" -ForegroundColor Red
}

# Test 3: English Query
Write-Host "`n[Test 3] English Query" -ForegroundColor Yellow
$enQuery = @{space_id=$spaces[0].id; question="What is this about?"; language="en"} | ConvertTo-Json
$enResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/queries" -Method POST -Headers @{"X-API-Key"=$apiKey} -ContentType "application/json" -Body $enQuery
Start-Sleep -Seconds 10
$enResult = Invoke-RestMethod -Uri "$baseUrl/api/v1/queries/$($enResponse.query_id)/result" -Headers @{"X-API-Key"=$apiKey}
if ($enResult.status -eq "completed" -and $enResult.sources.Count -gt 0) {
    Write-Host "✅ PASS: Answer generated with $($enResult.sources.Count) sources" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: Status $($enResult.status), Sources $($enResult.sources.Count)" -ForegroundColor Red
}

# Test 4: French Query
Write-Host "`n[Test 4] French Query" -ForegroundColor Yellow
$frQuery = @{space_id=$spaces[0].id; question="Qu'est-ce que c'est?"; language="fr"} | ConvertTo-Json
$frResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/queries" -Method POST -Headers @{"X-API-Key"=$apiKey} -ContentType "application/json" -Body $frQuery
Start-Sleep -Seconds 10
$frResult = Invoke-RestMethod -Uri "$baseUrl/api/v1/queries/$($frResponse.query_id)/result" -Headers @{"X-API-Key"=$apiKey}
$hasFrenchChars = $frResult.answer -match "[àâäéèêëïîôùûüÿœæç]"
if ($frResult.status -eq "completed" -and $hasFrenchChars) {
    Write-Host "✅ PASS: French answer generated" -ForegroundColor Green
} else {
    Write-Host "❌ FAIL: Not French or failed" -ForegroundColor Red
}

Write-Host "`n=== Tests Complete ===" -ForegroundColor Cyan
```

**Run:**
```powershell
.\test-production-rag.ps1
```

**Expected:** All 4 tests PASS

---

## 🔄 Rollback Procedures

### When to Rollback
- Critical errors in production (500 errors >10% of requests)
- Query processing failures >50%
- Response times >10 seconds consistently
- Data loss or corruption detected

### Rollback Steps (5 minutes)

**PowerShell:**
```powershell
Write-Host "⚠️ INITIATING ROLLBACK ⚠️" -ForegroundColor Red

# Swap production back to previous version (staging now has old prod code)
az webapp deployment slot swap `
  --name eva-api-marco-prod `
  --resource-group eva-suite-rg `
  --slot staging `
  --target-slot production

Write-Host "Waiting for rollback to complete..." -ForegroundColor Yellow
Start-Sleep -Seconds 45

# Verify health
$health = Invoke-WebRequest -Uri "https://eva-api-marco-prod.azurewebsites.net/health" -UseBasicParsing
if ($health.StatusCode -eq 200) {
    Write-Host "✅ Rollback successful, production restored" -ForegroundColor Green
} else {
    Write-Host "❌ Rollback failed, manual intervention required" -ForegroundColor Red
}

# Notify team
Write-Host "Send notification to team about rollback" -ForegroundColor Yellow
```

**Post-Rollback:**
1. Notify stakeholders immediately
2. Investigate root cause in staging environment
3. Fix issues and re-test before next deployment attempt
4. Update runbook with lessons learned

---

## ✅ Acceptance Criteria

- [ ] Staging deployment successful and validated
- [ ] Production swap completed in <1 minute
- [ ] All smoke tests pass (health, spaces, EN query, FR query)
- [ ] Document re-indexing in progress (monitored)
- [ ] Application Insights dashboards configured
- [ ] Alerts configured (failures, slow response, cost)
- [ ] Rollback procedure validated (tested in staging)
- [ ] Documentation updated (README, runbook)

---

## 📚 Resources

- [Azure App Service Deployment Slots](https://learn.microsoft.com/azure/app-service/deploy-staging-slots)
- [Application Insights Kusto Queries](https://learn.microsoft.com/azure/azure-monitor/logs/query-basics)
- [Azure Cost Management](https://learn.microsoft.com/azure/cost-management-billing/)

---

## 🚨 Risks & Mitigation

**Risk 1: Swap Takes Longer Than Expected**  
**Impact:** High - Extended downtime  
**Mitigation:** Use staging slot for instant rollback, monitor swap progress

**Risk 2: Document Re-Indexing Failures**  
**Impact:** Medium - Some documents not searchable  
**Mitigation:** Monitor Function logs, retry failed documents manually

**Risk 3: High Azure OpenAI Costs**  
**Impact:** Medium - Budget overrun  
**Mitigation:** Cost alerts at 80% and 100%, usage monitoring dashboard

**Risk 4: Production Query Failures**  
**Impact:** High - User impact  
**Mitigation:** Rollback plan validated, alerts trigger immediately

---

## 📞 Support Contacts

**Production Issues:**
- Marco Presta: marco.presta@example.com
- On-call rotation: [LINK TO PAGERDUTY]

**Azure Support:**
- Portal: https://portal.azure.com/#blade/Microsoft_Azure_Support/HelpAndSupportBlade
- Phone: 1-800-XXX-XXXX

**Escalation Path:**
1. Check Application Insights for errors
2. Review Function App logs
3. Test in staging slot
4. Rollback if critical
5. Escalate to Azure support if infrastructure issue

---

## 📋 Post-Deployment Checklist

- [ ] Production deployment completed successfully
- [ ] Smoke tests pass (4/4 tests)
- [ ] Monitoring dashboards show green
- [ ] Alerts configured and tested
- [ ] Documentation updated (README, API docs)
- [ ] Team notified of successful deployment
- [ ] Stakeholders informed
- [ ] GitHub Issue marked as complete
- [ ] Sprint retrospective scheduled

---

**Created:** December 9, 2025  
**Assigned To:** POD-D (Deployment)  
**Status:** 📋 Ready for Execution  
**Estimated Completion:** 2-3 business days  
**Blocked By:** POD-T (Tests must pass first)  
**Deployment Window:** [DATE/TIME TBD]
