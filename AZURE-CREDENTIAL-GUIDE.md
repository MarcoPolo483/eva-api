# Azure Credential Setup Guide
**Status**: Blocking Task #1 for Production Readiness  
**Estimated Time**: 10-15 minutes  
**Current Progress**: Configuration validation ready, awaiting credentials

---

## 🎯 What You Need

Three Azure services with their credentials:
1. **Cosmos DB** - NoSQL database for spaces/documents/queries
2. **Blob Storage** - File storage for document uploads
3. **Azure OpenAI** - GPT-4 + embeddings for RAG queries

---

## 📋 Step-by-Step Instructions

### 1. Azure Cosmos DB Credentials

**Navigate to:**
```
Azure Portal (portal.azure.com)
→ Search "Cosmos DB" 
→ Select your account (or create new)
→ Settings → Keys (left sidebar)
```

**Copy these values:**
- **URI**: `https://your-account.documents.azure.com:443/`
- **PRIMARY KEY**: Long string (60+ chars)

**Paste into `.env`:**
```ini
AZURE_COSMOS_ENDPOINT=https://your-account.documents.azure.com:443/
AZURE_COSMOS_KEY=<paste-primary-key-here>
```

**Database/Container Setup:**
If you don't have a database yet:
```
Data Explorer → New Database
  Name: eva-platform
  
Create Containers:
  1. spaces (partition key: /id)
  2. documents (partition key: /id)
  3. queries (partition key: /id)
```

---

### 2. Azure Blob Storage Credentials

**Navigate to:**
```
Azure Portal
→ Search "Storage accounts"
→ Select your account (or create new)
→ Security + networking → Access keys (left sidebar)
```

**Copy:**
- **Connection string** under `key1` (starts with `DefaultEndpointsProtocol=https...`)

**Paste into `.env`:**
```ini
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
```

**Container Setup:**
If you don't have a container yet:
```
Data storage → Containers → + Container
  Name: eva-documents
  Public access: Private
```

---

### 3. Azure OpenAI Credentials

**Navigate to:**
```
Azure Portal
→ Search "Azure OpenAI"
→ Select your resource (or create new)
→ Resource Management → Keys and Endpoint (left sidebar)
```

**Copy these values:**
- **Endpoint**: `https://your-resource.openai.azure.com/`
- **KEY 1**: Your API key

**Paste into `.env`:**
```ini
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=<paste-key1-here>
```

**Deployment Setup:**
If you don't have deployments yet:
```
Model deployments → Create new deployment
  
Deployment 1:
  Model: gpt-4
  Deployment name: gpt-4
  
Deployment 2:
  Model: text-embedding-ada-002
  Deployment name: text-embedding-ada-002
```

Update `.env` if using different names:
```ini
AZURE_OPENAI_DEPLOYMENT=gpt-4
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-ada-002
```

---

## ✅ Validation Checklist

After updating `.env`, verify each credential:

```powershell
# 1. Validate configuration
.\test-azure-integration.ps1 -Stage config

# Expected output:
#   ✅ AZURE_COSMOS_ENDPOINT
#   ✅ AZURE_COSMOS_KEY
#   ✅ AZURE_STORAGE_CONNECTION_STRING
#   ✅ AZURE_OPENAI_ENDPOINT
#   ✅ AZURE_OPENAI_KEY
#   ✅ Config loads successfully
```

If any ❌ appears, double-check:
- No extra spaces around `=`
- Full connection string copied (very long)
- Keys not expired or regenerated
- Correct endpoints with `https://`

---

## 🚀 Next Steps After Credentials Added

Once all ✅ appear:

```powershell
# Option 1: Run all stages (recommended, 6-8 hours)
.\test-azure-integration.ps1 -Stage all

# Option 2: Run stages individually
.\test-azure-integration.ps1 -Stage integration  # 30 min
.\test-azure-integration.ps1 -Stage loadtest     # 1 hour
.\test-azure-integration.ps1 -Stage analyze      # 30 min
.\test-azure-integration.ps1 -Stage security     # 1 hour
```

This will complete:
- ✅ Task #1: Configure Azure credentials
- ✅ Task #2: Run integration tests
- ✅ Task #3: Load test with real Azure (50 users)
- ✅ Task #4: Analyze and tune performance
- ✅ Task #5: Security audit

---

## 🔐 Security Note

**Never commit `.env` to Git!**

The `.gitignore` already excludes `.env`, but verify:
```powershell
git status  # .env should NOT appear
```

For production deployment:
- Use Azure Key Vault for secrets
- Set environment variables in Azure App Service
- Rotate keys regularly (90 days recommended)

---

## 💡 Alternative: Don't Have Azure Services Yet?

If you need to create resources first:

1. **Create Resource Group:**
   ```
   Azure Portal → Resource groups → Create
   Name: eva-platform-rg
   Region: East US (or nearest)
   ```

2. **Create Cosmos DB:**
   ```
   Create a resource → Cosmos DB → Create
   API: Core (SQL)
   Resource group: eva-platform-rg
   Account name: eva-cosmos-<unique>
   ```

3. **Create Storage Account:**
   ```
   Create a resource → Storage account
   Resource group: eva-platform-rg
   Storage account name: evastorage<unique>
   ```

4. **Create Azure OpenAI:**
   ```
   Create a resource → Azure OpenAI
   Resource group: eva-platform-rg
   Name: eva-openai-<unique>
   Region: East US (check GPT-4 availability)
   ```

**Total setup time**: ~15-20 minutes for all resources

---

## 📊 Expected Results After Full Test

**Integration Tests:**
- ✅ All pytest tests pass
- ✅ Real Cosmos DB CRUD operations work
- ✅ Blob Storage upload/download successful
- ✅ OpenAI embeddings/completions succeed

**Load Test (50 users, 5 min):**
- ✅ 15-25 RPS throughput
- ✅ P95 latency < 2000ms
- ✅ Error rate < 1%
- ✅ No connection pool exhaustion

**Security Audit:**
- ✅ No critical vulnerabilities
- ✅ Dependencies up to date
- ✅ Code scan passed

This achieves **90% production-ready** status (beta-grade deployment).

---

## 🆘 Troubleshooting

**"Connection timed out"**
→ Check firewall rules: Cosmos DB → Networking → Allow access from Azure Portal + your IP

**"Unauthorized"**
→ Verify keys not regenerated: Go back to Keys page, copy fresh key

**"Container not found"**
→ Create containers in Data Explorer with exact names from `.env`

**"Deployment not found"**
→ Check deployment names match exactly (case-sensitive)

---

**Current Status**: ⏸️ Waiting for Azure credentials  
**Next Action**: Add credentials to `.env` → Run `.\test-azure-integration.ps1 -Stage config`
