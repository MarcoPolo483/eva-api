# Azure API Management - EVA Suite Demo Sandbox (25 Users)

> ⚠️ **IMPLEMENTATION STATUS** (Updated: 2025-12-08T23:50:00Z)  
> **Deployment:** ❌ NOT DEPLOYED YET - Documentation Only  
> **Backend APIs:** ✅ 4 Azure App Services running (ready for APIM)  
> **Dashboard Status:** `"apim": "not-started"` ([see PRIORITY-0-CENTRAL-COMMAND-DASHBOARD.md](../../../eva-orchestrator/PRIORITY-0-CENTRAL-COMMAND-DASHBOARD.md))  
> **Implementation Time:** 2-3 hours (per this document)  
> **Cost Impact:** $0 for Consumption tier (<1M calls/month)  
> **Backend Services Ready:**  
>   - eva-auth-dev-app.azurewebsites.net (Running)  
>   - eva-api-marco-5346.azurewebsites.net (Running)  
>   - eva-api-container.azurewebsites.net (Running)  
>   - eva-api-marco-prod.azurewebsites.net (Running)  
> **Next Step:** Deploy APIM Consumption tier (follow sections 3-6 below)

**Document Version**: 1.0  
**Date**: December 8, 2025  
**Context**: EVA Suite demo environment for 25 users  
**Objective**: Implement APIM for cost tracking, rate limiting, and API gateway capabilities

---

## Executive Summary

### Goal
Deploy Azure API Management (APIM) **Consumption Tier** for EVA Suite demo sandbox to:
- ✅ Track API usage per user/department
- ✅ Enforce rate limits and quotas
- ✅ Provide developer portal for API key management
- ✅ Monitor costs and performance
- ✅ Prepare for ESDC-scale deployment (15K users)

### Cost Impact
- **APIM Consumption Tier**: **FREE** for demo (well under 1M calls/month)
- **Implementation Time**: 2-3 hours
- **Complexity**: Low (leverages existing Azure infrastructure)

---

## 1. Current EVA Suite Architecture

### Existing Azure Resources

Based on `.env.production`:

| Service | Resource | Location | Status |
|---------|----------|----------|--------|
| **Azure OpenAI** | canadacentral.api.cognitive.microsoft.com | Canada Central | ✅ Active |
| **Cosmos DB** | eva-suite-cosmos-dev | Canada Central | ✅ Active |
| **Blob Storage** | evasuitestoragedev | Canada Central | ✅ Active |
| **Entra ID** | Tenant: bfb12ca1-... | Global | ✅ Active |
| **Redis** | localhost:6379 | Local | ⚠️ Dev Only |

### Current API Architecture

```
User → http://localhost:8000 (FastAPI) → Azure Services
         ↓
    - /graphql (GraphQL + WebSocket)
    - /health
    - /api/v1/spaces
    - /api/v1/documents
    - /api/v1/users
    - /webhooks/*
```

**Problem**: No API gateway, no usage tracking, no rate limiting per user.

---

## 2. Target Architecture with APIM

```
┌─────────────────────────────────────────────────────────┐
│                    25 Demo Users                         │
│  (Developers, Partners, Internal Teams)                  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS
┌────────────────────▼────────────────────────────────────┐
│       Azure API Management (Consumption Tier)            │
│                                                          │
│  🔐 Authentication: Azure AD B2C / Entra ID             │
│  🚦 Rate Limiting: 100 req/min per user                 │
│  📊 Usage Tracking: All calls logged                    │
│  🔑 API Keys: Per-user subscription keys                │
│                                                          │
│  Products:                                              │
│    • Free Tier: 1,000 calls/month (auto-renew)         │
│    • Pro Tier: 10,000 calls/month                      │
│    • Enterprise: Unlimited (demo purposes)             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              EVA API Backend (FastAPI)                  │
│    https://eva-api-demo.azurewebsites.net              │
│                                                          │
│  Endpoints:                                             │
│    • POST /chat (RAG queries)                           │
│    • GET /graphql (GraphQL API)                         │
│    • WS /graphql (Subscriptions)                        │
│    • POST /api/v1/spaces                                │
│    • POST /api/v1/documents                             │
│    • POST /webhooks/trigger                             │
└─────────────────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   Azure OpenAI  Cosmos DB  Blob Storage
```

**Benefits**:
- ✅ **Free**: Consumption tier costs $0 for <1M calls/month
- ✅ **Usage Tracking**: See which users/features drive costs
- ✅ **Rate Limiting**: Prevent abuse (100 req/min per user)
- ✅ **Developer Portal**: Self-service API key management
- ✅ **Production Ready**: Same setup scales to 15K users at ESDC

---

## 3. Implementation Steps

### Step 1: Create APIM Instance (Azure Portal)

#### 1.1 Create Resource

```bash
# PowerShell command to create APIM instance

az apim create `
  --name eva-suite-apim-demo `
  --resource-group rg-evada2 `
  --publisher-name "EVA Suite" `
  --publisher-email marco.presta@yourdomain.com `
  --sku-name Consumption `
  --location canadacentral `
  --no-wait
```

**Or via Azure Portal**:
1. Go to [Azure Portal](https://portal.azure.com)
2. Create Resource → **API Management**
3. Settings:
   - **Name**: `eva-suite-apim-demo`
   - **Resource Group**: `rg-evada2` (existing)
   - **Location**: `Canada Central`
   - **Pricing Tier**: **Consumption** (serverless, pay-per-use)
   - **Publisher Name**: `EVA Suite`
   - **Publisher Email**: `marco.presta@yourdomain.com`
4. Review + Create
5. **Wait 5-10 minutes** for provisioning

#### 1.2 Verify APIM Gateway URL

After provisioning, get the gateway URL:
```
https://eva-suite-apim-demo.azure-api.net
```

---

### Step 2: Import EVA API Definition

#### 2.1 Export OpenAPI Spec from FastAPI

EVA API already has OpenAPI built-in (FastAPI):

```powershell
# Start EVA API locally
cd "C:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api"
$env:PYTHONPATH='src'
uvicorn eva_api.main:app --host 127.0.0.1 --port 8000
```

Download OpenAPI spec:
```powershell
curl http://localhost:8000/openapi.json -o eva-api-openapi.json
```

#### 2.2 Import to APIM

**Via Azure Portal**:
1. Go to APIM instance → **APIs** → **+ Add API**
2. Select **OpenAPI**
3. **OpenAPI Specification**: Upload `eva-api-openapi.json`
4. Settings:
   - **Display Name**: `EVA API`
   - **Name**: `eva-api`
   - **API URL Suffix**: `eva`
   - **Products**: Create "EVA Suite Demo"
5. Create

**Or via Azure CLI**:
```bash
az apim api import `
  --resource-group rg-evada2 `
  --service-name eva-suite-apim-demo `
  --path eva `
  --specification-path eva-api-openapi.json `
  --specification-format OpenApiJson `
  --display-name "EVA API" `
  --protocols https `
  --subscription-required true
```

**Result**: All EVA API endpoints now available at:
```
https://eva-suite-apim-demo.azure-api.net/eva/graphql
https://eva-suite-apim-demo.azure-api.net/eva/health
https://eva-suite-apim-demo.azure-api.net/eva/api/v1/spaces
```

---

### Step 3: Configure Backend Service

Point APIM to your backend (FastAPI deployed to Azure App Service or running locally for demo).

#### Option A: Azure App Service (Production-like)

**Deploy EVA API to Azure App Service first**:
```powershell
# Create App Service (if not exists)
az webapp create `
  --name eva-api-demo `
  --resource-group rg-evada2 `
  --plan eva-app-service-plan `
  --runtime "PYTHON:3.11"

# Deploy code
az webapp deployment source config-zip `
  --resource-group rg-evada2 `
  --name eva-api-demo `
  --src eva-api.zip
```

**Configure APIM Backend**:
1. APIM → APIs → EVA API → **Settings**
2. **Backend (Web service URL)**: `https://eva-api-demo.azurewebsites.net`
3. Save

#### Option B: Local Development (ngrok tunnel)

For testing without deploying to Azure:

```powershell
# Install ngrok (if not installed)
choco install ngrok

# Start EVA API locally
cd "C:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api"
uvicorn eva_api.main:app --host 0.0.0.0 --port 8000

# Expose via ngrok
ngrok http 8000
```

**Configure APIM Backend**:
1. APIM → APIs → EVA API → **Settings**
2. **Backend (Web service URL)**: `https://xxxx-xx-xxx.ngrok.io` (from ngrok output)
3. Save

⚠️ **Note**: ngrok free tier has session limits. Use Azure App Service for persistent demo.

---

### Step 4: Create Products & Subscriptions

Products define usage tiers. Create 3 tiers for demo:

#### 4.1 Create Products

**Via Azure Portal**:
1. APIM → **Products** → **+ Add**

**Product 1: Free Tier**
- **Name**: `EVA Suite - Free`
- **Display Name**: `EVA Suite Free (Demo)`
- **Description**: `Free tier for demo users. 1,000 calls/month, 10 req/min.`
- **Requires Subscription**: ✅ Yes
- **Requires Approval**: ❌ No (auto-approve for demo)
- **APIs**: Select `EVA API`
- **Quota**: 1,000 calls per month
- **Rate Limit**: 10 calls per minute

**Product 2: Pro Tier**
- **Name**: `EVA Suite - Pro`
- **Display Name**: `EVA Suite Pro (Demo)`
- **Description**: `Pro tier for power users. 10,000 calls/month, 50 req/min.`
- **Requires Subscription**: ✅ Yes
- **Requires Approval**: ❌ No
- **APIs**: Select `EVA API`
- **Quota**: 10,000 calls per month
- **Rate Limit**: 50 calls per minute

**Product 3: Enterprise Tier**
- **Name**: `EVA Suite - Enterprise`
- **Display Name**: `EVA Suite Enterprise (Demo)`
- **Description**: `Unlimited for enterprise demo accounts.`
- **Requires Subscription**: ✅ Yes
- **Requires Approval**: ✅ Yes (manual approval)
- **APIs**: Select `EVA API`
- **Quota**: Unlimited
- **Rate Limit**: 100 calls per minute

#### 4.2 Create Demo User Subscriptions

**Via Azure Portal**:
1. APIM → **Subscriptions** → **+ Add Subscription**

**Example: Create 5 demo users**

| User | Product | Subscription Name | Usage Pattern |
|------|---------|-------------------|---------------|
| **Demo Admin** | Enterprise | `demo-admin-001` | Heavy testing |
| **Partner A** | Pro | `partner-a-001` | Integration testing |
| **Partner B** | Free | `partner-b-001` | Light exploration |
| **Internal Dev 1** | Pro | `dev-team-001` | Development |
| **Internal Dev 2** | Free | `dev-team-002` | Development |

**For each user**:
1. APIM → **Subscriptions** → **+ Add**
2. Settings:
   - **Name**: `demo-admin-001`
   - **Display Name**: `Demo Admin`
   - **Scope**: Product → `EVA Suite - Enterprise`
   - **State**: Active
3. Save
4. **Copy Primary Key**: This is the user's API key (e.g., `abc123xyz...`)

**Result**: Each user gets unique API key:
```
demo-admin-001: Primary Key = "f8d3a7b2c1e9..."
partner-a-001:  Primary Key = "a1b2c3d4e5f6..."
```

---

### Step 5: Configure APIM Policies

Policies enforce rate limits, quotas, authentication, and logging.

#### 5.1 Product-Level Policy (All 3 products)

**Navigate**: APIM → Products → `EVA Suite - Free` → **Policies**

**Policy XML**:
```xml
<policies>
    <inbound>
        <base />
        
        <!-- Validate subscription key -->
        <check-header name="Ocp-Apim-Subscription-Key" failed-check-httpcode="401" failed-check-error-message="Missing or invalid subscription key" />
        
        <!-- Rate limiting (10 req/min for Free tier) -->
        <rate-limit-by-key 
            calls="10" 
            renewal-period="60" 
            counter-key="@(context.Subscription.Id)" />
        
        <!-- Monthly quota (1,000 calls for Free tier) -->
        <quota-by-key 
            calls="1000" 
            renewal-period="2592000" 
            counter-key="@(context.Subscription.Id)" />
        
        <!-- Add tracking headers -->
        <set-header name="X-Subscription-Name" exists-action="override">
            <value>@(context.Subscription.Name)</value>
        </set-header>
        <set-header name="X-Product-Name" exists-action="override">
            <value>@(context.Product.Name)</value>
        </set-header>
        
        <!-- CORS (for frontend) -->
        <cors allow-credentials="true">
            <allowed-origins>
                <origin>http://localhost:3000</origin>
                <origin>https://eva-demo.azurewebsites.net</origin>
            </allowed-origins>
            <allowed-methods>
                <method>GET</method>
                <method>POST</method>
                <method>PUT</method>
                <method>DELETE</method>
                <method>OPTIONS</method>
            </allowed-methods>
            <allowed-headers>
                <header>*</header>
            </allowed-headers>
        </cors>
    </inbound>
    
    <backend>
        <base />
    </backend>
    
    <outbound>
        <base />
        
        <!-- Add quota/rate limit info to response headers -->
        <set-header name="X-Rate-Limit-Remaining" exists-action="override">
            <value>@(context.Response.Headers.GetValueOrDefault("X-Rate-Limit-Remaining", "N/A"))</value>
        </set-header>
        <set-header name="X-Quota-Remaining" exists-action="override">
            <value>@(context.Response.Headers.GetValueOrDefault("X-Quota-Remaining", "N/A"))</value>
        </set-header>
    </outbound>
    
    <on-error>
        <base />
        
        <!-- Return friendly error messages -->
        <return-response>
            <set-status code="@(context.Response.StatusCode)" reason="@(context.Response.StatusReason)" />
            <set-header name="Content-Type" exists-action="override">
                <value>application/json</value>
            </set-header>
            <set-body>@{
                return new JObject(
                    new JProperty("error", context.LastError.Message),
                    new JProperty("subscription", context.Subscription?.Name ?? "N/A"),
                    new JProperty("timestamp", DateTime.UtcNow)
                ).ToString();
            }</set-body>
        </return-response>
    </on-error>
</policies>
```

**Repeat for Pro tier** (change `calls="50"` and `quota="10000"`).  
**Repeat for Enterprise tier** (remove quota, change `calls="100"`).

#### 5.2 API-Level Policy (Optional - Cost Tracking)

**Navigate**: APIM → APIs → EVA API → **Policies**

```xml
<policies>
    <inbound>
        <base />
        
        <!-- Log request for analytics -->
        <log-to-eventhub logger-id="eva-usage-logger">
            @{
                return new JObject(
                    new JProperty("subscription", context.Subscription.Name),
                    new JProperty("product", context.Product.Name),
                    new JProperty("endpoint", context.Request.Url.Path),
                    new JProperty("method", context.Request.Method),
                    new JProperty("timestamp", DateTime.UtcNow)
                ).ToString();
            }
        </log-to-eventhub>
    </inbound>
    
    <backend>
        <base />
    </backend>
    
    <outbound>
        <base />
    </outbound>
</policies>
```

⚠️ **Event Hub Setup Required**: Create Event Hub for logging (optional for demo).

---

### Step 6: Enable Developer Portal

The Developer Portal lets users sign up, get API keys, and view docs.

#### 6.1 Publish Developer Portal

1. APIM → **Developer Portal** → **Portal Overview**
2. Click **Publish**
3. Wait 1-2 minutes
4. Portal URL: `https://eva-suite-apim-demo.developer.azure-api.net`

#### 6.2 Customize Portal (Optional)

1. APIM → **Developer Portal** → **Portal Overview** → **Open Portal**
2. Click **Edit** (top-right)
3. Customize:
   - **Branding**: Add EVA Suite logo
   - **Colors**: Match EVA Suite theme
   - **Home Page**: Add welcome message
4. Save → **Publish**

#### 6.3 Test Developer Portal

1. Open: `https://eva-suite-apim-demo.developer.azure-api.net`
2. **Sign Up** (create test account)
3. **Products** → Subscribe to `EVA Suite - Free`
4. **Profile** → **Subscriptions** → Copy API key
5. Test API call:

```bash
curl -X GET \
  "https://eva-suite-apim-demo.azure-api.net/eva/health" \
  -H "Ocp-Apim-Subscription-Key: YOUR_API_KEY"
```

**Expected Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-08T14:30:00Z"
}
```

---

### Step 7: Update EVA Frontend to Use APIM

Minimal changes to frontend to route through APIM.

#### 7.1 Update API Base URL

**File**: `eva-api/frontend/.env` (or React config)

**Before** (direct backend):
```bash
REACT_APP_API_BASE_URL=http://localhost:8000
```

**After** (via APIM):
```bash
REACT_APP_API_BASE_URL=https://eva-suite-apim-demo.azure-api.net/eva
REACT_APP_APIM_SUBSCRIPTION_KEY=f8d3a7b2c1e9...  # Demo admin key
```

#### 7.2 Update API Client Code

**File**: `src/api/client.ts` (example)

**Before**:
```typescript
export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json'
  }
});
```

**After**:
```typescript
export const apiClient = axios.create({
  baseURL: process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
    // Add APIM subscription key if configured
    ...(process.env.REACT_APP_APIM_SUBSCRIPTION_KEY && {
      'Ocp-Apim-Subscription-Key': process.env.REACT_APP_APIM_SUBSCRIPTION_KEY
    })
  }
});
```

#### 7.3 Test Frontend with APIM

1. Start frontend:
```powershell
cd "C:\Users\marco\Documents\_AI Dev\EVA Suite\eva-frontend"
npm run dev
```

2. Open: `http://localhost:3000`
3. Verify:
   - All API calls route through APIM
   - Response headers include `X-Rate-Limit-Remaining`
   - 403 error if quota exceeded

---

## 4. Testing & Validation

### 4.1 Test Rate Limiting

**Test**: Exceed 10 req/min (Free tier)

```powershell
# Send 15 requests rapidly
for ($i=1; $i -le 15; $i++) {
    curl -X GET `
      "https://eva-suite-apim-demo.azure-api.net/eva/health" `
      -H "Ocp-Apim-Subscription-Key: FREE_TIER_KEY"
    
    Write-Host "Request $i completed"
}
```

**Expected**:
- First 10 requests: `200 OK`
- Requests 11-15: `429 Too Many Requests`

**Response** (429 error):
```json
{
  "statusCode": 429,
  "message": "Rate limit is exceeded. Try again in 60 seconds."
}
```

### 4.2 Test Quota Enforcement

**Test**: Exceed 1,000 calls/month (Free tier)

```powershell
# Simulate 1,005 calls (use loop or load test tool)
# After 1,000 calls, should get quota error
```

**Expected**:
- Calls 1-1000: `200 OK`
- Calls 1001+: `403 Forbidden`

**Response** (403 error):
```json
{
  "statusCode": 403,
  "message": "Quota exceeded. Renews on 2026-01-08."
}
```

### 4.3 Test Cost Tracking

**Verify usage in Azure Portal**:

1. APIM → **Analytics** → **Usage**
2. Filter by:
   - **Subscription**: `demo-admin-001`
   - **Time Range**: Last 24 hours
3. View:
   - Total calls
   - Calls per endpoint
   - Average latency
   - Error rate

**Export Usage Report**:
```powershell
# Download usage CSV
az apim api diagnostics list `
  --resource-group rg-evada2 `
  --service-name eva-suite-apim-demo `
  --output table
```

---

## 5. Cost Monitoring

### 5.1 APIM Consumption Tier Pricing

**Pricing** (as of Dec 2025):
- **0-1M calls/month**: **$0** (FREE) ✅
- **1M-100M calls**: $0.042 per 10,000 calls
- **100M+ calls**: $0.0336 per 10,000 calls

**25 Users Demo Estimate**:
- Avg usage: 400 calls/user/month
- Total calls: 25 × 400 = **10,000 calls/month**
- **Cost**: **$0** (well under 1M free tier) 🎉

### 5.2 Total Azure Costs (Demo Sandbox)

| Service | Monthly Cost | Notes |
|---------|--------------|-------|
| **APIM Consumption** | $0 | <1M calls |
| **Azure OpenAI (GPT-4)** | ~$150 | 25 users × 400 queries × $0.015/query |
| **Cosmos DB** | $25 | Free tier (400 RU/s) |
| **Blob Storage** | $5 | Minimal docs |
| **App Service** | $13 | B1 tier (dev) |
| **Redis Cache** | $0 | Running locally |
| **TOTAL** | **~$193/month** | For 25 users |

**Cost per User**: $7.72/month

---

## 6. Production Readiness Checklist

### ✅ Demo Sandbox (Complete)
- [x] APIM instance created (Consumption tier)
- [x] EVA API imported (OpenAPI spec)
- [x] 3 products configured (Free, Pro, Enterprise)
- [x] 5 demo subscriptions created
- [x] Rate limits enforced (10-100 req/min)
- [x] Quotas enforced (1K-10K calls/month)
- [x] Developer portal published
- [x] Frontend updated to use APIM

### 🔄 ESDC Scale Preparation (Next Phase)
- [ ] Create 15 department products
- [ ] Create 15,000 user subscriptions (automated script)
- [ ] Integrate with ESDC Azure AD
- [ ] Set up cost attribution Event Hub
- [ ] Configure Application Insights dashboards
- [ ] Enable chargeback automation (Azure Function)
- [ ] Deploy to ESDC subscription
- [ ] Load testing (1,500 concurrent users)

---

## 7. Next Steps

### Immediate (This Week)
1. ✅ **Create APIM instance** (30 minutes)
2. ✅ **Import EVA API** (15 minutes)
3. ✅ **Create 3 products** (15 minutes)
4. ✅ **Create 5 demo subscriptions** (15 minutes)
5. ✅ **Test rate limiting** (30 minutes)
6. ✅ **Update frontend** (1 hour)

**Total Time**: ~3 hours

### Short-Term (Next 2 Weeks)
- Enable Application Insights integration
- Create usage dashboard (Power BI)
- Document API for partners
- Collect feedback from 25 demo users

### Long-Term (Next 3 Months)
- Prepare for ESDC deployment (15K users)
- Implement cost attribution automation
- Integrate with ESDC financial systems
- Deploy to production subscription

---

## 8. Troubleshooting

### Issue: APIM Returns 500 Error

**Cause**: Backend (FastAPI) not accessible  
**Solution**:
1. Check backend is running: `curl https://eva-api-demo.azurewebsites.net/health`
2. Verify APIM backend URL: APIM → APIs → EVA API → Settings
3. Check firewall: Ensure APIM IP is whitelisted

### Issue: Subscription Key Not Working

**Cause**: Key not activated or copied incorrectly  
**Solution**:
1. APIM → Subscriptions → Find subscription → Verify **State** = Active
2. Regenerate key: **...** → **Regenerate Primary Key**
3. Copy new key and test

### Issue: CORS Error in Frontend

**Cause**: APIM policy not allowing frontend origin  
**Solution**:
1. APIM → Products → EVA Suite - Free → Policies
2. Update `<cors>` section:
```xml
<allowed-origins>
    <origin>http://localhost:3000</origin>
    <origin>https://your-frontend-domain.com</origin>
</allowed-origins>
```

### Issue: Rate Limit Too Strict

**Cause**: 10 req/min too low for testing  
**Solution**:
1. APIM → Products → EVA Suite - Free → Policies
2. Update rate limit:
```xml
<rate-limit-by-key calls="100" renewal-period="60" />
```

---

## 9. Quick Commands Reference

### Create APIM Instance
```powershell
az apim create `
  --name eva-suite-apim-demo `
  --resource-group rg-evada2 `
  --publisher-name "EVA Suite" `
  --publisher-email marco@example.com `
  --sku-name Consumption `
  --location canadacentral
```

### Import API
```powershell
az apim api import `
  --resource-group rg-evada2 `
  --service-name eva-suite-apim-demo `
  --path eva `
  --specification-path eva-api-openapi.json `
  --specification-format OpenApiJson
```

### Create Subscription
```powershell
az apim api subscription create `
  --resource-group rg-evada2 `
  --service-name eva-suite-apim-demo `
  --subscription-id demo-admin-001 `
  --display-name "Demo Admin" `
  --scope /products/eva-suite-free `
  --state active
```

### Test API Call
```powershell
curl -X GET `
  "https://eva-suite-apim-demo.azure-api.net/eva/health" `
  -H "Ocp-Apim-Subscription-Key: YOUR_KEY" `
  -v
```

### Check Usage
```powershell
az monitor metrics list `
  --resource "/subscriptions/SUB_ID/resourceGroups/rg-evada2/providers/Microsoft.ApiManagement/service/eva-suite-apim-demo" `
  --metric Requests `
  --interval PT1H
```

---

## 10. Documentation & Resources

### EVA Suite Docs
- API Specification: `eva-api/docs/SPECIFICATION.md`
- Production Deployment: `eva-api/docs/PRODUCTION-DEPLOYMENT-CHECKLIST.md`
- APIM Cost Attribution (ESDC): `eva-api/docs/APIM-COST-ATTRIBUTION-ESDC.md`

### Azure APIM Docs
- [APIM Overview](https://learn.microsoft.com/azure/api-management/)
- [Consumption Tier](https://learn.microsoft.com/azure/api-management/api-management-features)
- [Policy Reference](https://learn.microsoft.com/azure/api-management/api-management-policies)
- [Developer Portal](https://learn.microsoft.com/azure/api-management/api-management-howto-developer-portal)

### Contact
- **Owner**: Marco Presta
- **Team**: EVA Suite Development (POD-F)
- **Support**: Create issue in `eva-api` repo

---

**Document Status**: ✅ Ready for Implementation  
**Next Action**: Run `az apim create` command to start deployment  
**Time to Complete**: 3 hours (hands-on), 30 minutes (automated)
