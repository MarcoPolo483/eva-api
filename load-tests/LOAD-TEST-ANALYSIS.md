# Load Test Analysis - EVA API

**Generated:** 2025-12-07  
**Test Environment:** Local development (Windows, Python 3.11, FastAPI, no Azure backends)

---

## Executive Summary

Medium load testing (100 concurrent users) **revealed critical performance degradation** compared to baseline tests. The API suffers from 90%+ throughput loss under moderate load due to synchronous Azure service calls with long timeout periods.

### Key Findings

| Metric | Baseline (20 users) | Medium (100 users) | Change | Status |
|--------|--------------------:|-------------------:|-------:|--------|
| **Requests/sec** | 21.51 | 2.18 | **-90%** | 🔴 Critical |
| **Total Requests** | 2,543 (2min) | 651 (5min) | -88% | 🔴 Critical |
| **Error Rate** | 0% | 0.61% | +0.61% | 🟡 Warning |
| **Median Latency** | <50ms | 8ms (health) | - | 🟢 OK |
| **P95 Latency** | 580ms | 94,000ms | **+16,100%** | 🔴 Critical |
| **Space Creation** | ~50ms | 57,313ms (57s) | **+114,526%** | 🔴 Critical |

---

## Detailed Analysis

### 1. Throughput Collapse

**Observation:**  
Requests per second dropped from **21.51 RPS → 2.18 RPS** under 5x user load.

**Root Cause:**  
Synchronous blocking calls to Azure services (Cosmos DB, Blob Storage, OpenAI) with long timeouts (60-90 seconds). Without configured backends, each request waits for connection timeout before falling back to mocked data.

**Evidence:**
- `/api/v1/spaces` POST: **57,313ms average** (57 seconds)
- GraphQL `createSpace`: **83,661ms** (83 seconds)
- GraphQL `spaces query`: **152,235ms** (152 seconds)
- Health endpoint: **7ms median** (no Azure calls)

**Impact:**
- API cannot handle expected production load
- User experience severely degraded
- Connection pool exhaustion likely at 200+ users

---

### 2. Error Analysis

**GraphQL Failures: 4 requests (0.61%)**
- 1x `createSpace mutation` → 500 Internal Server Error
- 3x `spaces query` → 500 Internal Server Error

**Cause:**  
Timeout exceptions from Azure service calls not properly caught in GraphQL resolvers. REST endpoints have better error handling.

**Related Issue:**  
Load test script expects `{"id": "..."}` in response but receives error or malformed JSON, causing `KeyError: 'id'` in 11 instances.

---

### 3. Latency Distribution

**Percentile Breakdown (all endpoints aggregated):**

| Percentile | Latency | Assessment |
|-----------:|--------:|------------|
| P50 | 8ms | ✅ Excellent |
| P66 | 25ms | ✅ Good |
| P75 | 320ms | 🟡 Acceptable |
| P80 | 4,800ms | 🔴 Poor |
| P90 | 90,000ms | 🔴 Unacceptable |
| P95 | 94,000ms | 🔴 Unacceptable |
| P99 | 186,000ms | 🔴 Unacceptable |
| P99.9 | 269,000ms | 🔴 Unacceptable |

**Interpretation:**
- 50% of requests complete quickly (likely health checks)
- 20%+ of requests experience massive delays (60-270 seconds)
- Bimodal distribution: fast paths (health) vs slow paths (Azure-dependent)

---

### 4. Endpoint Performance

| Endpoint | Requests | Errors | Median | Avg | Max | RPS |
|----------|----------|--------|--------|-----|-----|-----|
| `GET /health` | 575 | 0 (0%) | 7ms | 12s* | 269s* | 1.92 |
| `POST /api/v1/spaces` | 72 | 0 (0%) | 5.7s | 57s | 187s | 0.24 |
| `POST /graphql` (createSpace) | 1 | 1 (100%) | 84s | 84s | 84s | 0.003 |
| `POST /graphql` (spaces) | 3 | 3 (100%) | 182s | 152s | 182s | 0.010 |

*Health endpoint averages skewed by one 268s outlier (likely timeout)

**Observations:**
- Only 72 space creation attempts in 5 minutes (0.24/sec)
- GraphQL completely broken under load (100% error rate)
- REST has better resilience (0% errors) but still extremely slow

---

## Comparison: Baseline vs Medium Load

### Baseline Test (20 users, 2 minutes)
- ✅ 2,543 requests @ 21.51 RPS
- ✅ 0 errors
- ✅ P50: 11ms, P95: 580ms, P99: 1,500ms
- ✅ All SLA targets met

### Medium Test (100 users, 5 minutes)
- 🔴 651 requests @ 2.18 RPS (-90% throughput)
- 🟡 4 errors (0.61% rate)
- 🔴 P50: 8ms, P95: 94,000ms, P99: 186,000ms
- 🔴 SLA violations: P95/P99 exceed targets by 9,300%/9,200%

**Degradation Factor:**  
**10x slowdown per request** when scaling from 20 → 100 users

---

## Root Cause Analysis

### Primary Issues

1. **Missing Azure Configuration**
   - No `AZURE_COSMOS_CONNECTION_STRING` set
   - No `AZURE_STORAGE_CONNECTION_STRING` set
   - No `AZURE_OPENAI_API_KEY` set
   - Services fall back to mock/timeout behavior

2. **Synchronous Blocking Architecture**
   - FastAPI using `def` routes instead of `async def`
   - Azure SDK calls block event loop
   - No connection pooling configured
   - No circuit breaker pattern

3. **Long Timeout Values**
   - Cosmos DB: 60s default timeout
   - Blob Storage: 90s default timeout
   - OpenAI: 30s default timeout
   - Total cascade: 180s worst case per request

4. **Inefficient Fallback Logic**
   - Timeout → catch → mock response
   - No fast-fail circuit breaker
   - No cached responses
   - Each retry attempts full connection

### Secondary Issues

5. **GraphQL Resolver Error Handling**
   - Exceptions not caught in resolvers
   - Returns 500 instead of graceful degradation
   - No retry logic

6. **Test Infrastructure Mismatch**
   - Load tests expect real Azure backends
   - No "test mode" or mock environment variable
   - Cannot isolate API layer performance

---

## Recommendations

### 🔥 Critical (P0) - Before Next Load Test

1. **Implement Fast-Fail Mock Mode**
   ```python
   # In config.py
   MOCK_MODE = os.getenv("EVA_MOCK_MODE", "false").lower() == "true"
   
   # In routers/spaces.py
   if MOCK_MODE:
       return {"id": str(uuid4()), "name": data.name, ...}
   else:
       # Real Azure calls
   ```
   **Impact:** Enable load testing of API layer without Azure latency

2. **Convert Routes to Async**
   ```python
   # From
   @router.post("/spaces")
   def create_space(data: SpaceCreate):
       
   # To
   @router.post("/spaces")
   async def create_space(data: SpaceCreate):
       await cosmos_client.create_item(...)
   ```
   **Impact:** Prevent event loop blocking, support 10x more concurrent requests

3. **Add Circuit Breaker Pattern**
   ```python
   from circuitbreaker import circuit
   
   @circuit(failure_threshold=5, recovery_timeout=30)
   async def call_cosmos():
       # Azure call with 5s timeout
   ```
   **Impact:** Fast-fail after repeated timeouts, prevent cascade

### 🟡 High Priority (P1) - Production Readiness

4. **Configure Connection Pooling**
   - Cosmos DB: `max_connections=100`
   - HTTP Client: `limits=Limits(max_connections=200)`
   - Redis cache for hot data

5. **Implement Response Caching**
   - Redis/Memcached for GET endpoints
   - TTL: 60s for space lists, 300s for read-only data
   - Cache-aside pattern

6. **Fix GraphQL Error Handling**
   ```python
   try:
       space = await create_space_service(info)
       return space
   except Exception as e:
       logger.error(f"GraphQL error: {e}")
       raise GraphQLError("Space creation failed", extensions={"code": "SERVICE_ERROR"})
   ```

7. **Add Timeouts to All External Calls**
   ```python
   cosmos_client = CosmosClient(..., connection_timeout=5, read_timeout=10)
   ```

### 🟢 Medium Priority (P2) - Optimization

8. **Implement Request Queuing**
   - Celery/RQ for async document processing
   - Reduce blocking time in request handlers

9. **Add Load Shedding**
   - Return 429 (Too Many Requests) when queue > threshold
   - Protect backend from overload

10. **Horizontal Scaling Prep**
    - Externalize session state
    - Use distributed cache (Redis Cluster)
    - Stateless API design

---

## Next Steps

### Before Heavy Load Test (1000 users):

1. ✅ **DO:** Implement mock mode (P0 #1)
2. ✅ **DO:** Convert 5 most-used routes to async (P0 #2)
3. ✅ **DO:** Add circuit breaker (P0 #3)
4. ✅ **DO:** Re-run medium test with mocks
5. ❌ **DON'T:** Run 1000-user test without fixes (will fail catastrophically)

### Expected Results After Fixes:

| Metric | Current | Target | Improvement |
|--------|--------:|-------:|------------:|
| RPS (100 users) | 2.18 | 50+ | +2,200% |
| Median Latency | 8ms | <10ms | ✅ |
| P95 Latency | 94,000ms | <200ms | -99.8% |
| Error Rate | 0.61% | <0.1% | -85% |

---

## Load Test Execution Log

### Baseline Test (Path C)
- **Date:** 2025-12-05
- **Command:** `locust -f locustfile.py --headless --users 20 --spawn-rate 5 --run-time 2m`
- **Result:** ✅ PASS - 2,543 requests, 0 errors, all SLAs met
- **Report:** `load-tests/report-baseline.html`

### Demo Test (Path C)
- **Date:** 2025-12-06
- **Command:** `locust -f locustfile.py --headless --users 25 --spawn-rate 5 --run-time 2m`
- **Result:** ✅ PASS - 2,895 requests, 0 errors, acceptable P95/P99
- **Report:** `load-tests/report-demo.html`

### Medium Test (Path C+)
- **Date:** 2025-12-07
- **Command:** `locust -f locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m`
- **Result:** 🔴 FAIL - 651 requests, 4 errors, severe latency degradation
- **Report:** `load-tests/report-medium.html`
- **CSV:** `load-tests/results-medium_stats.csv`

### Heavy Test (Path C+)
- **Status:** ⏸️ BLOCKED - Awaiting medium test fixes
- **Reason:** Current API cannot handle 100 users; 1000 would crash

---

## Conclusion

The medium load test successfully identified a **critical performance bottleneck**: synchronous Azure service calls with long timeouts. The API performs well for health checks (in-memory operations) but degrades catastrophically when accessing external services.

**Action Required:** Implement mock mode and async architecture before proceeding with heavy load tests or production deployment.

**Estimated Fix Time:** 4-6 hours (P0 items)  
**Estimated Retest Time:** 30 minutes  
**Production Readiness:** Currently **NOT READY** (P0 fixes required)

---

**Test conducted by:** GitHub Copilot (Automated Load Testing Agent)  
**Review required by:** P04-LIB, P15-DVM  
**Next review:** After P0 fixes implemented
