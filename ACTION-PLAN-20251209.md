# Action Plan: eva-api

**Date**: December 9, 2025 19:00 EST (CORRECTED)  
**Current Score**: 88/100 (corrected from 72/100)  
**Target Score**: 95/100  
**Priority**: MEDIUM (Azure integrated, coverage improvement needed)

---

## Executive Summary

**Status**: ✅ **UNBLOCKED - Azure services ARE integrated** (88/100)  
**Gap**: -12 points (coverage 38.96% vs claimed 82.1%)  
**Effort**: 4-6 hours (coverage improvement only)  
**Blocker**: NONE - Can deploy immediately

⚠️ **CORRECTION**: Previous assessment incorrectly identified Azure services as "placeholders". After verification, all Azure services (Cosmos DB, Blob Storage, Azure OpenAI) ARE integrated and functional.

**See**: `AZURE-INTEGRATION-VERIFICATION-20251209.md` for detailed verification.

---

## Gap Analysis (from DEEP-ASSESSMENT-20251209.md)

### Gap 1: Azure Services Placeholders (CRITICAL)
- **Issue**: All Azure services are placeholders (Cosmos DB, Blob Storage, Azure OpenAI)
- **Impact**: API cannot store/retrieve data or call AI models
- **Priority**: CRITICAL
- **Effort**: 8-12 hours

### Gap 2: Coverage Misrepresentation
- **Claimed**: 82.1% coverage
- **Actual**: 38.96% coverage
- **Gap**: -43.14 points
- **Impact**: Test suite inadequate for production
- **Priority**: HIGH
- **Effort**: 4-6 hours

### Gap 3: Webhooks API Disabled
- **Issue**: Backend complete, storage layer pending
- **Impact**: Cannot receive external events (GitHub, Stripe, etc.)
- **Priority**: MEDIUM
- **Effort**: 2-4 hours

---

## Action Items

### Phase 1: Azure Integration (Sprint 5 - Week of Dec 9-15)

**Task 1: Integrate Cosmos DB** (3-4 hours)
- [ ] Read `eva-infra/DEEP-ASSESSMENT-20251209.md` (Cosmos DB endpoints)
- [ ] Install `azure-cosmos` SDK (add to `requirements.txt`)
- [ ] Replace placeholder `CosmosDBClient` with real implementation
- [ ] Configure connection string from Key Vault
- [ ] Implement CRUD operations:
  - `create_document(container, document)`
  - `read_document(container, document_id)`
  - `update_document(container, document_id, updates)`
  - `delete_document(container, document_id)`
  - `query_documents(container, query)`
- [ ] Add unit tests for Cosmos DB operations (15-20 tests)
- [ ] Add integration tests with dev Cosmos DB (5-10 tests)

**Expected Outcome**:
```python
# Before (placeholder)
class CosmosDBClient:
    def create_document(self, container, document):
        raise NotImplementedError("TODO: Integrate Cosmos DB")

# After (real implementation)
from azure.cosmos import CosmosClient

class CosmosDBClient:
    def __init__(self, connection_string: str):
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database = self.client.get_database_client("eva-suite-db")
    
    def create_document(self, container: str, document: dict):
        container_client = self.database.get_container_client(container)
        return container_client.create_item(body=document)
```

**Task 2: Integrate Blob Storage** (2-3 hours)
- [ ] Install `azure-storage-blob` SDK (add to `requirements.txt`)
- [ ] Replace placeholder `BlobStorageClient` with real implementation
- [ ] Configure connection string from Key Vault
- [ ] Implement blob operations:
  - `upload_blob(container, blob_name, data)`
  - `download_blob(container, blob_name)`
  - `delete_blob(container, blob_name)`
  - `list_blobs(container, prefix)`
- [ ] Add unit tests for Blob Storage operations (10-15 tests)
- [ ] Add integration tests with dev Blob Storage (5-10 tests)

**Task 3: Integrate Azure OpenAI** (3-4 hours)
- [ ] Install `openai` SDK (add to `requirements.txt`)
- [ ] Replace placeholder `OpenAIClient` with real implementation
- [ ] Configure API key and endpoint from Key Vault
- [ ] Implement AI operations:
  - `generate_completion(prompt, model="gpt-4o")`
  - `generate_embedding(text, model="text-embedding-3-small")`
  - `chat_completion(messages, model="gpt-4o")`
- [ ] Add unit tests for OpenAI operations (10-15 tests)
- [ ] Add integration tests with dev OpenAI (5-10 tests)

**Task 4: Enable Webhooks API** (2-4 hours)
- [ ] Integrate Cosmos DB for webhook event storage
- [ ] Integrate Blob Storage for webhook payload archival
- [ ] Enable `/webhooks` endpoints (currently disabled)
- [ ] Add webhook signature verification (HMAC)
- [ ] Add unit tests for webhooks (10-15 tests)
- [ ] Add integration tests with sample webhooks (3-5 tests)

---

### Phase 2: Test Coverage Improvement (Sprint 5)

**Task 5: Increase Test Coverage to 80%+** (4-6 hours)
- [ ] Run coverage report: `pytest --cov=eva_api --cov-report=html`
- [ ] Identify untested code paths (currently 61% uncovered)
- [ ] Write tests for untested code:
  - GraphQL resolvers (add 15-20 tests)
  - REST endpoint edge cases (add 10-15 tests)
  - Error handling (add 10-15 tests)
  - Input validation (add 10-15 tests)
- [ ] Achieve 80%+ coverage (target: 85%)
- [ ] Update README with accurate coverage (remove 82.1% false claim)

**Expected Outcome**:
- Current: 38.96% coverage (139/357 statements)
- Target: 80%+ coverage (285+/357 statements)
- New tests: 50-65 additional tests

---

## Testing Strategy

### Unit Tests
- Add 50-65 new tests (Azure services + coverage gaps)
- Target: 80%+ coverage (currently 38.96%)
- Mock Azure services for unit tests (use `unittest.mock`)

### Integration Tests
- Test with dev Azure resources (Cosmos DB, Blob Storage, OpenAI)
- Test webhooks with sample payloads
- Test GraphQL API with real queries

### Manual Testing
- Call REST endpoints → verify Cosmos DB storage
- Upload files → verify Blob Storage
- Call AI endpoints → verify OpenAI responses
- Send webhooks → verify event processing

---

## Deployment Plan

### Prerequisites
- ✅ eva-infra deployed (19 Azure resources operational)
- ✅ Key Vault secrets configured (connection strings, API keys)
- ⏳ Azure services integrated (Task 1-4)
- ⏳ Test coverage 80%+ (Task 5)

### Deployment Steps
1. **Dev Environment** (eva-api-marco-5346)
   - Deploy with Azure integration
   - Test all endpoints manually
   - Verify logs in Application Insights

2. **Test Environment** (new App Service)
   - Deploy via Terraform (separate environment)
   - Run integration tests
   - Performance testing (load testing with 100+ RPS)

3. **Prod Environment** (eva-api-marco-prod)
   - Deploy after test validation
   - Enable monitoring (Application Insights)
   - Set up alerts (error rate, latency)

---

## Success Criteria

### Definition of Done
- ✅ Cosmos DB integrated (CRUD operations working)
- ✅ Blob Storage integrated (upload/download working)
- ✅ Azure OpenAI integrated (completions + embeddings working)
- ✅ Webhooks API enabled (event storage + signature verification)
- ✅ Test coverage 80%+ (currently 38.96%)
- ✅ 50-65 new tests added
- ✅ All integration tests passing with dev Azure resources
- ✅ README updated with accurate coverage (remove 82.1% false claim)
- ✅ Updated DEEP-ASSESSMENT-20251209.md (90/100 target)

### Quality Gates
- Coverage: 80%+ (target: 85%, verified via htmlcov/index.html)
- Tests: All passing (189+ tests, currently 139)
- Azure integration: All services functional (Cosmos, Blob, OpenAI)
- Webhooks: Enabled and tested
- Linting: No errors (flake8, mypy)
- Security: No vulnerabilities (bandit scan)

---

## Dependencies

### Internal
- ✅ eva-infra: Azure resources operational (Cosmos DB, Blob Storage, OpenAI)
- ✅ eva-auth: JWT tokens for authentication

### External
- ✅ Azure Cosmos DB: eva-suite-cosmos-dev (operational)
- ✅ Azure Blob Storage: evasuitestoragedev (operational)
- ✅ Azure OpenAI: eva-suite-openai-dev (gpt-4o, text-embedding-3-small)
- ✅ Azure Key Vault: eva-suite-kv-dev (8 secrets configured)

---

## Rollback Plan

**If deployment fails:**
1. Revert to previous commit (git tag: `eva-api-v1.0.0`)
2. Azure App Service: Swap slots (staging ↔ production)
3. Verify health check returns 200 OK
4. Monitor logs for Azure SDK errors

**Rollback triggers:**
- Azure SDK connection errors (Cosmos, Blob, OpenAI)
- Test coverage drops below 80%
- Integration tests fail

---

## Recommendations

### Immediate (Sprint 5 - Week of Dec 9-15)
1. 🚨 **CRITICAL**: Complete Task 1-4 (Azure integration) - 12-16 hours
   - **Blocker**: Cannot deploy without Azure services
   - **Timeline**: Dec 9-11 (3 days)
   
2. 🚨 **HIGH**: Complete Task 5 (test coverage 80%+) - 4-6 hours
   - **Issue**: 38.96% coverage inadequate for production
   - **Timeline**: Dec 11-12 (2 days)

3. ✅ **DEPLOY**: Deploy to dev (eva-api-marco-5346) after Task 1-5
   - **Timeline**: Dec 12 (end of Sprint 5)
   - **Target Score**: 90/100

### Future (Sprint 6+)
1. ⏳ **OPTIONAL**: Implement advanced rate limiting (Redis-based)
2. ⏳ **OPTIONAL**: Integrate eva-metering for billing (after eva-metering Phase 1-2)
3. ⏳ **OPTIONAL**: Add OpenAPI/Swagger documentation generation

---

## Owner

**POD**: POD-F (Foundation Layer)  
**Team**: P04-LIB + P15-DVM  
**Primary Contact**: Marco Presta  
**Repository**: https://github.com/MarcoPolo483/eva-api

---

**Created**: 2025-12-09  
**Status**: BLOCKED (Azure integration required)  
**Next Review**: After Task 1-5 completion (Dec 12, 2025)  
**Estimated Completion**: Dec 12, 2025 (Sprint 5, 16-22 hours total)
