# EPIC-001: Improve eva-api Test Coverage to 80%+

**Epic ID**: EPIC-001
**Status**: Draft
**Priority**: P1 (High)
**Business Value**: High
**Estimated Story Points**: 58 points
**Target Completion**: Sprint 1-2 (2-4 weeks)

## Business Context

eva-api currently has 52.92% test coverage with 113 passing tests. While Azure services (Cosmos DB, Blob Storage, Azure OpenAI) are fully integrated and functional, the low coverage creates risk for production deployment and limits confidence in future changes.

**Business Impact**:
- ✅ Critical paths ARE covered (auth, documents, health checks)
- ⚠️ Service layer has gaps (Cosmos 39%, Query 19%, GraphQL 17%)
- ⚠️ Cannot confidently refactor or extend without breaking changes
- ✅ Foundation is solid - need to build on it incrementally

**User Impact**:
- Faster feature delivery with confidence
- Fewer production bugs
- Easier onboarding for new developers
- Better documentation through tests

## Problem Statement

The eva-api codebase has comprehensive test files but many tests fail due to:
1. **Implementation gaps**: 90+ service methods called by tests don't exist yet
2. **Test infrastructure**: Authentication fixtures and config mismatches
3. **Architectural issues**: Webhook service event loop management
4. **Integration gaps**: External service testing incomplete

This prevents us from achieving 80%+ coverage target and reduces deployment confidence.

## Success Criteria

- [ ] Test coverage reaches 80%+ (currently 52.92%)
- [ ] All P0 and P1 tests passing (currently 113/208)
- [ ] No test configuration errors (currently 27 errors)
- [ ] Integration tests functional (currently failing)
- [ ] CI/CD pipeline enforces coverage standards
- [ ] Deployed to Azure App Service (dev environment)

## User Stories

### Story 1: Fix Test Infrastructure (Quick Wins)
**ID**: STORY-001
**Priority**: P0
**Points**: 8
**As a** developer
**I want** all test fixtures and configurations working correctly
**So that** existing tests can execute and provide accurate coverage data

**Acceptance Criteria**:
- [ ] Authentication test fixtures properly inject JWT tokens into headers
- [ ] GraphQL integration test imports fixed (`get_settings()` instead of `settings`)
- [ ] Azure OpenAI test configuration uses correct field names
- [ ] All configuration errors resolved (0 of 27 remaining)
- [ ] Coverage increases to ~68% with existing tests

**Tasks**:
- [ ] Fix authentication fixture in `conftest.py` - 1h
- [ ] Update all endpoint tests to use fixed auth - 1h
- [ ] Fix GraphQL integration import - 15min
- [ ] Fix Azure OpenAI config field names - 30min
- [ ] Run full test suite and verify 68%+ coverage - 15min

**Technical Notes**:
```python
# Current issue:
@pytest.fixture
def mock_jwt_token():
    return "Bearer ..."  # Token created but not used

# Fix:
@pytest.fixture
def auth_headers(mock_jwt_token):
    return {"Authorization": mock_jwt_token}

# Usage:
def test_endpoint(client, auth_headers):
    response = client.post("/api/v1/spaces", headers=auth_headers, ...)
```

---

### Story 2: Implement Missing Blob Storage Methods
**ID**: STORY-002
**Priority**: P1
**Points**: 8
**As a** API consumer
**I want** complete Blob Storage operations (streaming, batch, SAS URLs)
**So that** I can efficiently manage documents in Azure Blob Storage

**Acceptance Criteria**:
- [ ] `download_document_streaming()` implemented with async iterator
- [ ] `delete_documents_batch()` implemented for bulk operations
- [ ] `generate_download_url()` implemented with SAS token generation
- [ ] `generate_upload_url()` implemented with write permissions
- [ ] 12 blob storage tests passing (currently 6/20)
- [ ] Blob service coverage increases to 95%+ (currently 83%)

**Tasks**:
- [ ] Implement streaming download method - 1.5h
- [ ] Implement batch delete method - 1h
- [ ] Implement SAS URL generation (download) - 1h
- [ ] Implement SAS URL generation (upload) - 30min
- [ ] Update tests to verify new methods - 1h

**Technical Approach**:
```python
async def download_document_streaming(
    self, space_id: str, document_id: str
) -> AsyncIterator[bytes]:
    """Stream document content in chunks."""
    blob_client = self._get_blob_client(space_id, document_id)
    stream = await blob_client.download_blob()
    async for chunk in stream.chunks():
        yield chunk
```

---

### Story 3: Implement Missing Cosmos DB Methods
**ID**: STORY-003
**Priority**: P1
**Points**: 13
**As a** API consumer
**I want** complete Cosmos DB operations (spaces, documents, queries)
**So that** I can fully manage multi-tenant data with proper isolation

**Acceptance Criteria**:
- [ ] Space management: `update_space()`, `delete_space()` implemented
- [ ] Document metadata: `create_document_metadata()`, `delete_document_metadata()` implemented
- [ ] Document queries: `query_documents_by_space()`, `query_documents()` implemented
- [ ] Query management: `create_query()`, `update_query_status()`, `get_query_history()` implemented
- [ ] Cross-partition: `query_all_documents()`, `get_total_document_count()`, `search_documents_by_filename()` implemented
- [ ] 16 Cosmos DB tests passing (currently 3/30)
- [ ] Cosmos service coverage increases to 70%+ (currently 39%)

**Tasks**:
- [ ] Implement space update/delete operations - 2h
- [ ] Implement document metadata CRUD - 2h
- [ ] Implement document query methods - 2h
- [ ] Implement query lifecycle management - 1.5h
- [ ] Implement cross-partition query methods - 1.5h
- [ ] Update tests and verify coverage - 1h

**Technical Approach**:
```python
async def update_space(
    self, space_id: str, updates: Dict[str, Any]
) -> Dict[str, Any]:
    """Update space metadata."""
    space = await self.get_space(space_id)
    space.update(updates)
    space["updated_at"] = datetime.utcnow().isoformat()
    
    await self.spaces_container.upsert_item(space)
    return space
```

**Dependencies**:
- Depends on: HPK container implementation (exists)
- Blocks: STORY-005 (integration tests need these methods)

---

### Story 4: Implement Query Service Enhancements
**ID**: STORY-004
**Priority**: P2
**Points**: 5
**As a** API consumer
**I want** advanced query capabilities (token estimation, retry logic)
**So that** I can optimize costs and handle OpenAI rate limits gracefully

**Acceptance Criteria**:
- [ ] `estimate_tokens()` implemented using tiktoken
- [ ] `_call_openai_with_retry()` implemented with exponential backoff
- [ ] Token tracking and limits enforced
- [ ] 5 query service tests passing (currently 0/27)
- [ ] Query service coverage increases to 40%+ (currently 19%)

**Tasks**:
- [ ] Implement token estimation with tiktoken - 1.5h
- [ ] Implement retry logic with exponential backoff - 1.5h
- [ ] Add token limit enforcement - 1h
- [ ] Update tests and verify - 1h

**Technical Approach**:
```python
async def estimate_tokens(self, text: str) -> int:
    """Estimate token count for text."""
    import tiktoken
    encoding = tiktoken.encoding_for_model("gpt-4")
    return len(encoding.encode(text))

async def _call_openai_with_retry(
    self, messages: List[Dict], max_retries: int = 3
) -> Dict:
    """Call OpenAI with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            return await self._call_openai(messages)
        except RateLimitError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                raise
```

---

### Story 5: Fix Webhook Service Architecture
**ID**: STORY-005
**Priority**: P2
**Points**: 8
**As a** developer
**I want** webhook delivery service properly managing asyncio lifecycle
**So that** we don't have runtime errors polluting logs and risking production stability

**Acceptance Criteria**:
- [ ] Webhook delivery worker doesn't error on event loop binding
- [ ] Queue properly initialized per event loop
- [ ] No RuntimeError in test logs
- [ ] Webhook service coverage increases to 60%+ (currently 45%)
- [ ] Production deployment validated without errors

**Tasks**:
- [ ] Analyze webhook service lifecycle - 1h
- [ ] Refactor delivery worker event loop management - 3h
- [ ] Add proper queue initialization per loop - 2h
- [ ] Test with multiple TestClient instances - 1h
- [ ] Validate in production-like environment - 1h

**Technical Approach**:
```python
class WebhookService:
    def __init__(self):
        self._delivery_queue: Optional[asyncio.Queue] = None
        self._current_loop: Optional[asyncio.AbstractEventLoop] = None
    
    async def _ensure_queue(self):
        """Ensure queue is bound to current event loop."""
        current_loop = asyncio.get_running_loop()
        if self._current_loop != current_loop:
            self._delivery_queue = asyncio.Queue()
            self._current_loop = current_loop
        return self._delivery_queue
```

**Dependencies**:
- Depends on: None (can be done in parallel)
- Blocks: Production deployment confidence

---

### Story 6: Integration Testing Infrastructure
**ID**: STORY-006
**Priority**: P2
**Points**: 8
**As a** developer
**I want** comprehensive integration tests against real Azure services
**So that** we catch integration issues before production

**Acceptance Criteria**:
- [ ] Integration tests use proper Azure connection strings (dev environment)
- [ ] Blob integration tests passing (currently 0/4)
- [ ] GraphQL integration tests passing (currently 0/6)
- [ ] Integration test coverage separate from unit test coverage
- [ ] CI/CD can run integration tests in isolated environment

**Tasks**:
- [ ] Set up integration test environment variables - 1h
- [ ] Fix blob integration tests with real Azure config - 2h
- [ ] Fix GraphQL integration tests - 2h
- [ ] Add integration test job to CI/CD - 2h
- [ ] Validate end-to-end flows - 1h

**Technical Approach**:
```python
# integration/conftest.py
@pytest.fixture(scope="session")
def integration_settings():
    """Use real Azure settings for integration tests."""
    return Settings(
        mock_mode=False,
        cosmos_endpoint=os.getenv("AZURE_COSMOS_ENDPOINT"),
        cosmos_key=os.getenv("AZURE_COSMOS_KEY"),
        # ... real credentials
    )
```

---

## Dependencies

### Story Dependencies
```
STORY-001 (Quick Wins) - No dependencies, can start immediately
   ↓
STORY-002 (Blob Methods) - Can start in parallel
STORY-003 (Cosmos Methods) - Can start in parallel
STORY-004 (Query Methods) - Can start in parallel
   ↓
STORY-005 (Webhook Refactor) - Can start in parallel
STORY-006 (Integration Tests) - Depends on STORY-002, STORY-003
```

### External Dependencies
- Azure subscription and credentials (available)
- Test environment provisioned (available)
- P07 (Testing Agent) availability
- P09 (QA Engineer) for validation
- P11 (DevOps Engineer) for deployment

---

## Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Implementing methods introduces bugs | High | Medium | TDD approach, extensive testing, code review |
| Integration tests slow down CI/CD | Medium | High | Run in separate job, use test doubles for unit tests |
| Webhook refactor breaks production | High | Low | Deploy to dev first, monitor closely, have rollback plan |
| Coverage target not reached | Medium | Low | Prioritize P0/P1 work, defer P2 if needed |
| Team capacity insufficient | Medium | Medium | Focus on Quick Wins first, deliver incrementally |

---

## Technical Notes

### Coverage Milestones
- **Current**: 52.92% (113 passing tests)
- **After STORY-001**: ~68% (+16% from fixing fixtures)
- **After STORY-002/003**: ~78% (+10% from implementations)
- **After STORY-004/005/006**: ~88% (+10% from enhancements)

### Deployment Strategy
**Recommended**: Option A - Deploy now, improve incrementally
- Deploy at 52.92% coverage to dev environment
- Critical paths are covered (auth, documents, spaces)
- Implement improvements in production with real traffic
- Monitor and validate each increment

**Alternative**: Option B - Quick Wins first
- Complete STORY-001 (4 hours)
- Deploy at 68% coverage
- Continue with remaining stories post-deployment

---

## Sprint Planning

### Sprint 1 (Week 1-2): Foundation
- **Goal**: Fix test infrastructure and implement Blob/Cosmos methods
- **Stories**: STORY-001, STORY-002, STORY-003
- **Points**: 29 points
- **Deliverable**: 78% coverage, deployed to dev

### Sprint 2 (Week 3-4): Enhancement
- **Goal**: Add query enhancements and fix architectural issues
- **Stories**: STORY-004, STORY-005, STORY-006
- **Points**: 21 points
- **Deliverable**: 88% coverage, production-ready

---

## Related Documentation

- **Assessment**: `docs/assessments/TEST-COVERAGE-PROBLEM-ASSESSMENT.md`
- **Coverage Report**: `htmlcov/index.html` (generated after test runs)
- **Test Files**: `eva-api/tests/`
- **Service Files**: `eva-api/src/eva_api/services/`

---

**Epic Status**: 📋 Ready for Sprint Planning
**Next Step**: SM to create sprint backlog and assign to agents
**Estimated Duration**: 2-4 weeks (2 sprints)
**Success Probability**: High (work is well-defined and achievable)
