# EVA API Platform - Complete Implementation Specification

**Last Updated**: 2025-12-07  
**Status**: Ready for Implementation  
**POD**: POD-F (Foundation)  
**Owner**: P04-LIB + P15-DVM  
**Type**: Backend Service + API Gateway

---

## 🎯 Vision

Build production-ready, enterprise-grade API Platform as the single entry point for all EVA Suite services, providing:

- **REST APIs** with OpenAPI 3.1 specification
- **GraphQL** endpoint with Apollo Server
- **Webhooks** for real-time event notifications
- **API Gateway** for routing, authentication, rate limiting
- **SDKs** for Python, Node.js, .NET
- **Developer Portal** with interactive docs and API key management

**Business Value**: Enable 50+ third-party integrations within 12 months, reduce custom integration effort by 70%, establish EVA as open platform for innovation, unlock ecosystem partnerships.

---

## 📋 Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Technical Stack](#technical-stack)
3. [Core Capabilities](#core-capabilities)
4. [API Endpoints](#api-endpoints)
5. [Authentication & Authorization](#authentication--authorization)
6. [Rate Limiting & Throttling](#rate-limiting--throttling)
7. [SDK Development](#sdk-development)
8. [Developer Portal](#developer-portal)
9. [Quality Gates](#quality-gates)
10. [Implementation Phases](#implementation-phases)
11. [References](#references)

---

## 🏗️ Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Developer Portal (React)                 │
│              (API Docs, Key Management, Analytics)           │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│                     API Gateway (FastAPI)                    │
│  ┌──────────┬──────────┬──────────┬────────────────────┐   │
│  │  Auth    │   Rate   │  Routing │    Observability   │   │
│  │  Layer   │  Limit   │  Layer   │    (OTel)          │   │
│  └──────────┴──────────┴──────────┴────────────────────┘   │
└───────┬─────────┬────────┬──────────┬────────────┬─────────┘
        │         │        │          │            │
    ┌───▼───┐ ┌──▼──┐ ┌───▼────┐ ┌──▼───┐   ┌───▼────┐
    │  RAG  │ │Auth │ │ Core   │ │ MCP  │   │  AI    │
    │Service│ │Svc  │ │Business│ │Server│   │Models  │
    └───────┘ └─────┘ └────────┘ └──────┘   └────────┘
```

### Reference Implementations

**OpenWebUI Backend** (Router Pattern):
- 24 modular routers (chats, users, files, etc.)
- FastAPI with dependency injection
- JWT authentication
- Pydantic models for validation

**PubSec Info Assistant** (Monolithic FastAPI):
- 904-line app.py with Azure services
- Azure AD authentication
- Blob storage + Cosmos DB
- OpenAI + Azure AI Search integration

### EVA API Approach

**Hybrid Pattern**: Best of both worlds
- **Modular routers** like OpenWebUI (maintainability)
- **Azure integrations** like PubSec (enterprise-grade)
- **Gateway layer** for cross-cutting concerns
- **OpenAPI** for API-first development

---

## 🛠️ Technical Stack

### Core Framework
- **Python**: 3.11+
- **FastAPI**: 0.110+ (async/await, Pydantic v2, OpenAPI 3.1)
- **Uvicorn**: ASGI server with auto-reload
- **Pydantic**: 2.x for request/response validation

### Authentication & Authorization
- **Azure AD B2C**: Citizen authentication
- **Microsoft Entra ID**: Employee authentication
- **OAuth 2.0**: Client credentials flow (M2M)
- **JWT**: Token validation with PyJWT
- **RBAC**: Role-based access control

### Data Storage
- **Azure Cosmos DB**: API keys, rate limits, webhook subscriptions, audit logs
- **Azure Blob Storage**: File uploads, SDK packages
- **Redis**: Rate limiting counters, session cache

### API Gateway
- **Azure API Management (APIM)**: Production gateway
- **FastAPI Middleware**: Development gateway
- **Rate Limiting**: Token bucket algorithm
- **Circuit Breaker**: Prevent cascading failures

### GraphQL
- **Strawberry**: Python GraphQL library (async)
- **DataLoader**: N+1 query optimization
- **Subscriptions**: WebSocket for real-time updates

### SDKs
- **Python**: Generated from OpenAPI (openapi-generator)
- **Node.js**: TypeScript SDK with axios
- **.NET**: C# SDK with HttpClient
- **CLI**: Typer for command-line interface

### Developer Portal
- **React**: 18+ with TypeScript
- **Swagger UI**: Interactive API docs
- **Redocly**: Enhanced API documentation
- **Analytics**: Usage charts with Recharts

### Testing
- **pytest**: Unit + integration tests
- **pytest-asyncio**: Async test support
- **httpx**: Async HTTP client for tests
- **Faker**: Test data generation
- **Coverage.py**: 100% coverage target

### Observability
- **OpenTelemetry**: Distributed tracing
- **Azure Monitor**: Application Insights
- **Prometheus**: Metrics export
- **Grafana**: Dashboards (optional)

### CI/CD
- **GitHub Actions**: Build, test, deploy
- **Docker**: Multi-stage builds
- **Azure Container Registry**: Image storage
- **Azure App Service**: Hosting (Linux containers)

---

## 🎯 Core Capabilities

### 1. REST API

**OpenAPI 3.1 Specification**
- Full CRUD operations on spaces, documents, queries
- Cursor-based pagination (scalable)
- Filtering + sorting + search
- Partial responses (field selection)
- Batch operations (bulk create/update)

**Endpoints**:
```
GET    /api/v1/spaces                    # List spaces
POST   /api/v1/spaces                    # Create space
GET    /api/v1/spaces/{id}               # Get space
PUT    /api/v1/spaces/{id}               # Update space
DELETE /api/v1/spaces/{id}               # Delete space
GET    /api/v1/spaces/{id}/documents     # List documents
POST   /api/v1/spaces/{id}/documents     # Upload document
POST   /api/v1/spaces/{id}/query         # Query space
GET    /api/v1/queries/{id}/status       # Query status
GET    /api/v1/queries/{id}/results      # Query results
```

**Response Format**:
```json
{
  "data": {...},
  "pagination": {
    "cursor": "eyJpZCI6MTIzfQ==",
    "has_next": true,
    "total": 1000
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2025-12-07T18:00:00Z"
  }
}
```

**Error Format**:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid space_id format",
    "details": [
      {
        "field": "space_id",
        "issue": "Must be UUID v4"
      }
    ]
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2025-12-07T18:00:00Z"
  }
}
```

### 2. GraphQL API

**Schema**:
```graphql
type Query {
  space(id: ID!): Space
  spaces(filter: SpaceFilter, page: PageInput): SpaceConnection!
  document(id: ID!): Document
  query(id: ID!): QueryResult
}

type Mutation {
  createSpace(input: CreateSpaceInput!): Space!
  updateSpace(id: ID!, input: UpdateSpaceInput!): Space!
  deleteSpace(id: ID!): Boolean!
  uploadDocument(spaceId: ID!, file: Upload!): Document!
  submitQuery(spaceId: ID!, input: QueryInput!): QueryResult!
}

type Subscription {
  documentAdded(spaceId: ID!): Document!
  queryCompleted(queryId: ID!): QueryResult!
}
```

**Apollo Server Configuration**:
- WebSocket support for subscriptions
- DataLoader for batch loading
- Query complexity analysis (prevent abuse)
- Persisted queries (performance)

### 3. Webhooks

**Event Types**:
- `space.created`
- `space.updated`
- `space.deleted`
- `document.added`
- `document.processed`
- `query.completed`
- `query.failed`

**Subscription Management**:
```
POST   /api/v1/webhooks              # Create subscription
GET    /api/v1/webhooks              # List subscriptions
GET    /api/v1/webhooks/{id}         # Get subscription
PUT    /api/v1/webhooks/{id}         # Update subscription
DELETE /api/v1/webhooks/{id}         # Delete subscription
GET    /api/v1/webhooks/{id}/logs    # Delivery logs
POST   /api/v1/webhooks/{id}/test    # Send test event
```

**Payload**:
```json
{
  "event_type": "document.added",
  "event_id": "evt_123",
  "timestamp": "2025-12-07T18:00:00Z",
  "tenant_id": "tenant_abc",
  "space_id": "space_xyz",
  "data": {
    "document_id": "doc_456",
    "filename": "report.pdf",
    "size_bytes": 102400
  }
}
```

**Delivery**:
- HMAC-SHA256 signature verification
- 3 retry attempts with exponential backoff (1s, 5s, 25s)
- Delivery logs (success, failed, response time)
- Dead letter queue for failed events

### 4. Authentication & Authorization

**OAuth 2.0 Flows**:
- **Authorization Code**: Web apps
- **Client Credentials**: M2M (APIs, SDKs)
- **Device Code**: CLI tools

**API Key Authentication**:
```
X-API-Key: sk_live_abc123...
```

**JWT Token**:
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Scopes**:
- `spaces:read` - Read spaces
- `spaces:write` - Create/update/delete spaces
- `documents:read` - Read documents
- `documents:write` - Upload documents
- `queries:execute` - Execute queries
- `webhooks:manage` - Manage webhooks
- `admin:all` - Full admin access

**Tenant Isolation**:
- Every API key/token tied to tenant_id
- Automatic tenant_id injection in queries
- Row-level security in Cosmos DB

### 5. Rate Limiting

**Tiers**:
| Tier       | Requests/min | Burst | Price    |
|------------|--------------|-------|----------|
| Free       | 60           | 10    | $0       |
| Basic      | 600          | 50    | $50/mo   |
| Pro        | 6,000        | 200   | $500/mo  |
| Enterprise | Unlimited    | N/A   | Custom   |

**Headers**:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 742
X-RateLimit-Reset: 1701975600
Retry-After: 30
```

**Algorithm**:
- Token bucket (sliding window)
- Per API key
- Per endpoint (finer control)
- Redis for distributed state

**429 Response**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You have exceeded 1000 requests per minute",
    "retry_after": 30
  }
}
```

### 6. SDK Development

**Python SDK** (`pip install eva-sdk`):
```python
from eva_sdk import EVAClient

client = EVAClient(api_key="sk_live_abc123")

# Spaces
spaces = client.spaces.list(page_size=20)
space = client.spaces.create(name="My Space")
space = client.spaces.get("space_xyz")
space.update(name="Updated Name")
space.delete()

# Documents
doc = space.documents.upload(file="report.pdf")
docs = space.documents.list()

# Queries
result = space.query("What is the revenue?")
print(result.answer)
```

**Node.js SDK** (`npm install @eva/sdk`):
```javascript
import { EVAClient } from '@eva/sdk';

const client = new EVAClient({ apiKey: 'sk_live_abc123' });

// Spaces
const spaces = await client.spaces.list({ pageSize: 20 });
const space = await client.spaces.create({ name: 'My Space' });
const space = await client.spaces.get('space_xyz');
await space.update({ name: 'Updated Name' });
await space.delete();

// Documents
const doc = await space.documents.upload({ file: 'report.pdf' });
const docs = await space.documents.list();

// Queries
const result = await space.query('What is the revenue?');
console.log(result.answer);
```

**.NET SDK** (`dotnet add package Eva.SDK`):
```csharp
using Eva.SDK;

var client = new EVAClient("sk_live_abc123");

// Spaces
var spaces = await client.Spaces.ListAsync(pageSize: 20);
var space = await client.Spaces.CreateAsync(new CreateSpaceRequest { Name = "My Space" });
var space = await client.Spaces.GetAsync("space_xyz");
await space.UpdateAsync(new UpdateSpaceRequest { Name = "Updated Name" });
await space.DeleteAsync();

// Documents
var doc = await space.Documents.UploadAsync("report.pdf");
var docs = await space.Documents.ListAsync();

// Queries
var result = await space.QueryAsync("What is the revenue?");
Console.WriteLine(result.Answer);
```

**CLI** (`pip install eva-cli`):
```bash
eva login
eva spaces list
eva spaces create --name "My Space"
eva documents upload space_xyz report.pdf
eva query space_xyz "What is the revenue?"
```

### 7. Developer Portal

**Features**:
- **Interactive Docs**: Swagger UI + Redocly
- **API Key Management**: Create, rotate, revoke keys
- **Usage Analytics**: Requests/day, latency, errors
- **Sandbox Environment**: Test without affecting production
- **Code Examples**: Python, Node.js, .NET, cURL
- **Webhook Testing**: Send test events
- **Changelog**: API versioning updates

**Pages**:
- `/docs` - API Reference
- `/console` - API Key Management
- `/analytics` - Usage Dashboard
- `/sandbox` - Test Environment
- `/examples` - Code Samples
- `/changelog` - Version History

**Tech Stack**:
- React 18 + TypeScript
- Swagger UI (embedded)
- Redocly API Reference
- Recharts for analytics
- Monaco Editor for code examples

---

## 🎯 Quality Gates

All gates must pass before deployment. **Non-negotiable**.

### 1. Test Coverage
- **Target**: 100% (no exceptions)
- **Framework**: pytest + pytest-asyncio
- **Tools**: Coverage.py
- **Command**: `pytest --cov=eva_api --cov-report=html`
- **Coverage Types**: Line, branch, path

### 2. API Contract Testing
- **OpenAPI Spec**: Valid 3.1 schema
- **Contract Tests**: Schemathesis
- **Breaking Changes**: Automated detection
- **Versioning**: Semantic (v1, v2, v3)

### 3. Performance
- **Latency**: p50 < 100ms, p95 < 500ms, p99 < 1s
- **Throughput**: 1000 req/s per instance
- **Load Testing**: Locust with 10k virtual users
- **Database**: Query optimization (indexes)

### 4. Security
- **OWASP Top 10**: All mitigated
- **Auth**: OAuth 2.0 + JWT validation
- **Input Validation**: Pydantic + JSON Schema
- **SQL Injection**: Parameterized queries only
- **Secrets**: Azure Key Vault (no hardcoded)
- **TLS**: 1.2+ enforced

### 5. Documentation
- **OpenAPI Spec**: Complete with examples
- **SDK Docs**: Docstrings + generated HTML
- **Developer Portal**: All features documented
- **Changelog**: Every API change logged
- **Migration Guides**: For breaking changes

### 6. Observability
- **Traces**: OpenTelemetry on 100% requests
- **Metrics**: Request count, latency, errors
- **Logs**: Structured JSON logs
- **Alerts**: Latency > 1s, Error rate > 1%
- **Dashboards**: Grafana (optional)

### 7. CI/CD
- **Build**: Docker multi-stage
- **Test**: All tests pass
- **Lint**: Ruff + mypy (type checking)
- **Security Scan**: Trivy + Bandit
- **Deploy**: Blue-green deployment

### 8. Accessibility
- **Developer Portal**: WCAG 2.2 AA minimum
- **Keyboard Navigation**: All interactive elements
- **Screen Readers**: ARIA labels
- **Contrast**: 4.5:1 minimum

### 9. Internationalization
- **API Errors**: Bilingual (EN/FR)
- **Developer Portal**: English primary, French available
- **Documentation**: Bilingual
- **Date/Time**: ISO 8601 (UTC)

### 10. Compliance
- **Audit Logs**: All API requests logged
- **Data Retention**: 90 days
- **GDPR**: Data export + deletion
- **Protected B**: Encryption at rest + transit

### 11. Reliability
- **Uptime**: 99.9% SLA
- **Failover**: Multi-region (optional)
- **Circuit Breaker**: Prevent cascading failures
- **Retries**: Exponential backoff with jitter

### 12. Developer Experience
- **Setup Time**: < 5 minutes
- **First API Call**: < 2 minutes
- **SDK Installation**: One command
- **Examples**: Working code for common tasks
- **Support**: GitHub Discussions

---

## 📅 Implementation Phases

### Phase 1: Foundation (Week 1-2)
**Goal**: Core API Gateway + Authentication

**Deliverables**:
1. FastAPI project structure (routers, models, middleware)
2. Azure AD B2C + Entra ID integration
3. JWT validation middleware
4. API key management (Cosmos DB)
5. OpenAPI spec generation
6. Basic health check endpoint
7. Docker container + CI/CD pipeline

**Tests**: 100% coverage on auth layer

**Evidence**: cURL examples hitting authenticated endpoints

---

### Phase 2: REST API (Week 3-4)
**Goal**: Full CRUD operations

**Deliverables**:
1. Spaces router (CRUD)
2. Documents router (upload, list, delete)
3. Queries router (submit, status, results)
4. Pagination (cursor-based)
5. Filtering + sorting
6. Error handling (standardized)
7. Rate limiting middleware (Redis)

**Tests**: 100% coverage on all routers

**Evidence**: Postman collection with 50+ requests

---

### Phase 3: GraphQL + Webhooks (Week 5-6)
**Goal**: Real-time capabilities

**Deliverables**:
1. Strawberry GraphQL schema
2. Apollo Server with subscriptions
3. DataLoader optimization
4. Webhook subscription CRUD
5. Event delivery system
6. HMAC signature verification
7. Delivery logs + retries

**Tests**: 100% coverage on GraphQL + webhooks

**Evidence**: WebSocket subscription working, webhook events delivered

---

### Phase 4: SDKs (Week 7-8)
**Goal**: Developer tools

**Deliverables**:
1. Python SDK (generated from OpenAPI)
2. Node.js SDK (TypeScript)
3. .NET SDK (C#)
4. CLI tool (Typer)
5. SDK documentation
6. PyPI, npm, NuGet publishing
7. GitHub releases

**Tests**: SDK integration tests

**Evidence**: `pip install eva-sdk` working, example scripts running

---

### Phase 5: Developer Portal (Week 9-10)
**Goal**: Self-service platform

**Deliverables**:
1. React frontend (TypeScript)
2. Swagger UI integration
3. API key management UI
4. Usage analytics dashboard
5. Sandbox environment
6. Code examples (interactive)
7. Azure App Service deployment

**Tests**: E2E tests with Playwright

**Evidence**: Portal accessible at https://developers.eva.ai

---

### Phase 6: Production Readiness (Week 11-12)
**Goal**: Enterprise-grade deployment

**Deliverables**:
1. Load testing (10k users, 1M requests)
2. Security audit (OWASP Top 10)
3. Multi-region failover
4. Monitoring dashboards
5. Incident response runbook
6. API versioning strategy
7. Migration guides

**Tests**: All 12 quality gates passing

**Evidence**: Production deployment successful, SLA met

---

## 🔗 References

### Documentation
- **OpenAPI Spec**: https://swagger.io/specification/
- **FastAPI**: https://fastapi.tiangolo.com/
- **Strawberry GraphQL**: https://strawberry.rocks/
- **OAuth 2.0**: https://oauth.net/2/
- **Azure AD B2C**: https://learn.microsoft.com/azure/active-directory-b2c/

### Code Repositories
- **OpenWebUI Backend**: (attached folder) `OpenWebUI/backend/open_webui/`
- **PubSec Info Assistant**: (attached folder) `PubSec-Info-Assistant/app/backend/`

### EVA Orchestrator Docs
- `docs/backlog/eva-api-platform-developers.md` (293 lines)
- `docs/EVA-2.0/archived-backlog/api-gateway-integration-layer.md` (522 lines)
- `docs/features/eva-sovereign-ui/README.md` (733 lines - template reference)

### Azure Resources
- Azure API Management
- Azure App Service
- Azure Cosmos DB
- Azure Blob Storage
- Azure Key Vault
- Azure Monitor

---

## ✅ Autonomous Implementation Model

**Marco will NOT be available for incremental approvals.**

### Principles
1. **Follow requirements TO THE LETTER** - No shortcuts, no approximations
2. **Apply ALL EVA principles** - Three Concepts Pattern, Complete SDLC, Execution Evidence Rule
3. **Achieve all 12 quality gates** - 100% pass rate required
4. **Reference implementations** - Use OpenWebUI + PubSec patterns
5. **Self-contained** - Complete documentation, no gaps

### Expected Outcome
**IF** requirements followed + principles applied **THEN** production-ready without friction.

### Final Review
**Binary decision**:
- ✅ All 12 gates pass → Ship to production
- ❌ Specific gates fail → List failures, agent fixes, resubmit

---

## 📊 Success Metrics

1. **API Availability**: 99.9% uptime
2. **Response Time**: p95 < 500ms
3. **Developer Adoption**: 50+ third-party integrations in 12 months
4. **SDK Downloads**: 1000+ per month
5. **API Calls**: 1M+ per day
6. **Error Rate**: < 0.1%
7. **Documentation**: < 5 support tickets per week
8. **Security**: Zero critical vulnerabilities

---

**END OF SPECIFICATION**

*Generated: 2025-12-07*  
*Source: eva-orchestrator*  
*Version: 1.0.0*
