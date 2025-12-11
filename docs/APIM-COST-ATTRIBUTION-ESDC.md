# APIM Cost Attribution Strategy for ESDC EVA Domain Assistant

> ⚠️ **IMPLEMENTATION STATUS** (Updated: 2025-12-08T23:50:00Z)  
> **Deployment:** ❌ APIM NOT DEPLOYED - Documentation Only  
> **Current Cost Tracking:** See [FINOPS-EVA-RAG-COST-ESTIMATE.md](../../../eva-orchestrator/FINOPS-EVA-RAG-COST-ESTIMATE.md)  
> **Backend Costs (Without APIM):** $100.30/month (Azure AI Search $75, Cosmos DB $5-10, Redis $16, Blob <$1)  
> **APIM Cost:** $0 for Consumption tier (<1M calls/month)  
> **Dashboard:** `"apim": "not-started"` ([PRIORITY-0-CENTRAL-COMMAND-DASHBOARD.md](../../../eva-orchestrator/PRIORITY-0-CENTRAL-COMMAND-DASHBOARD.md))  
> **Next Step:** Deploy APIM per [APIM-DEMO-SANDBOX-SETUP.md](./APIM-DEMO-SANDBOX-SETUP.md) (2-3 hours)

**Document Version**: 1.0  
**Date**: December 8, 2025  
**Context**: ESDC has 15,000 users across 15 departments using EVA Domain Assistant (based on Microsoft Information Assistant) with zero cost visibility or control.

---

## Executive Summary

### Current Problem

**ESDC EVA Domain Assistant**:
- ✅ 15,000 active users
- ✅ 15 different departments/clients
- ❌ **No cost visibility** - Unknown which department costs what
- ❌ **No usage control** - Cannot limit or throttle
- ❌ **No chargeback** - Cannot bill departments fairly
- ❌ **No accountability** - Departments overuse without consequences

**Result**: Uncontrolled Azure infrastructure costs with no way to allocate expenses to consuming departments.

### Solution: Azure API Management (APIM)

**APIM Consumption Tier provides**:
- ✅ Per-department usage tracking
- ✅ Automated cost attribution
- ✅ Usage quotas and rate limiting
- ✅ Chargeback automation
- ✅ Self-service portal for departments
- ✅ Cost: ~$50-100/month for 1.5M calls

**ROI**: Immediate cost recovery through fair billing + 10-20% savings from usage accountability.

---

## Current Architecture (No Control)

```
┌──────────────────────────────────────────────────────────────┐
│                ESDC Departments (15 Total)                    │
└──────────────────────────────────────────────────────────────┘
    │
    │  All departments share same endpoint
    │  No differentiation, no tracking
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│              EVA Domain Assistant (Info Assistant)            │
│  - /rag/answer (RAG query)                                   │
│  - /doc/summarize (document summary)                         │
│  - /doc/compare (document comparison)                        │
│  - /doc/extract (entity extraction)                          │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│                    Azure Services                             │
│  - Azure OpenAI (GPT-4) - $$$ Unknown allocation            │
│  - Cosmos DB (documents) - $$$ Unknown allocation           │
│  - Blob Storage (files) - $$$ Unknown allocation            │
│  - Cognitive Search - $$$ Unknown allocation                │
└──────────────────────────────────────────────────────────────┘

Total Monthly Cost: ~$10,000-$15,000?
Cost per Department: UNKNOWN ❌
```

**Problems**:
1. All costs lumped into single IT budget
2. No visibility into which department drives costs
3. Heavy users subsidized by light users (unfair)
4. No incentive to optimize usage
5. Cannot enforce quotas or limits
6. Budget overruns with no accountability

---

## Target Architecture (APIM Control)

```
┌──────────────────────────────────────────────────────────────────┐
│              Azure API Management (Consumption Tier)              │
│  - Cost Attribution                                              │
│  - Usage Quotas                                                  │
│  - Rate Limiting                                                 │
│  - Analytics Dashboard                                           │
└──────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  Justice Dept    │  │Immigration Dept  │  │  IT Services     │
│  Subscription 1  │  │  Subscription 2  │  │  Subscription 15 │
│  Key: xxx-001    │  │  Key: xxx-002    │  │  Key: xxx-015    │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│  2,000 users     │  │  1,500 users     │  │  500 users       │
│  150K calls/mo   │  │  120K calls/mo   │  │  45K calls/mo    │
│  Quota: 200K/mo  │  │  Quota: 150K/mo  │  │  Quota: 50K/mo   │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│  OpenAI: $300    │  │  OpenAI: $240    │  │  OpenAI: $90     │
│  Cosmos: $50     │  │  Cosmos: $40     │  │  Cosmos: $15     │
│  Storage: $20    │  │  Storage: $16    │  │  Storage: $6     │
│  Search: $30     │  │  Search: $24     │  │  Search: $9      │
│  APIM: $10       │  │  APIM: $8        │  │  APIM: $3        │
├──────────────────┤  ├──────────────────┤  ├──────────────────┤
│  TOTAL: $410/mo  │  │  TOTAL: $328/mo  │  │  TOTAL: $123/mo  │
└──────────────────┘  └──────────────────┘  └──────────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              EVA Domain Assistant Backend (Unchanged)             │
│  /rag/answer | /doc/summarize | /doc/compare | /doc/extract     │
└──────────────────────────────────────────────────────────────────┘
```

**Benefits**:
1. ✅ Each department gets unique API key
2. ✅ All usage tracked per department
3. ✅ Costs automatically attributed
4. ✅ Fair chargeback billing
5. ✅ Quotas prevent overruns
6. ✅ Self-service management

---

## APIM Features for ESDC Use Case

### 1. Per-Department Subscriptions

Each of the 15 departments gets:
- **Unique API Key**: Department-specific authentication
- **Usage Quota**: Monthly call limit (e.g., 100K calls/month)
- **Rate Limit**: Requests per second (e.g., 50 req/sec)
- **Cost Tracking**: All costs attributed to subscription

**Example**:
```json
{
  "subscriptionId": "justice-dept-001",
  "displayName": "ESDC - Justice Department",
  "scope": "/products/eva-domain-assistant",
  "state": "active",
  "primaryKey": "xxx-justice-001",
  "quota": {
    "callLimit": 200000,
    "renewalPeriod": "P1M"
  },
  "rateLimit": {
    "calls": 50,
    "renewalPeriod": "PT1S"
  }
}
```

### 2. Product Tiers (Usage-Based Pricing)

**Tier Structure**:

| Tier | Users | Quota/Month | Rate Limit | Monthly Cost |
|------|-------|-------------|------------|--------------|
| **Small** | < 500 | 50,000 calls | 20 req/sec | ~$150 |
| **Medium** | 500-1500 | 150,000 calls | 50 req/sec | ~$350 |
| **Large** | 1500-3000 | 300,000 calls | 100 req/sec | ~$650 |
| **Enterprise** | 3000+ | 500,000 calls | 200 req/sec | ~$1,000 |

**Example Department Assignment**:
- Justice (2,000 users) → **Large tier** → $650/month
- Immigration (1,500 users) → **Medium tier** → $350/month
- IT Services (500 users) → **Small tier** → $150/month

### 3. Usage Tracking & Analytics

**Metrics Captured per Department**:
- Total API calls
- Calls per endpoint (/rag/answer, /doc/summarize, etc.)
- Request/response payload sizes
- Latency (response time)
- Error rates
- OpenAI token consumption
- Cosmos DB RU consumption

**Analytics Dashboard**:
```
Department: Justice
Period: November 2025

API Call Breakdown:
  /rag/answer:      85,000 calls (57%)
  /doc/summarize:   45,000 calls (30%)
  /doc/compare:     15,000 calls (10%)
  /doc/extract:      5,000 calls (3%)
  Total:           150,000 calls

Resource Consumption:
  OpenAI tokens:    15M tokens ($300)
  Cosmos DB RUs:    500K RUs ($50)
  Blob Storage:     100 GB ($20)
  Search Queries:   50K queries ($30)
  
Total Cost: $400
Quota Utilization: 75% (150K of 200K)
```

### 4. Cost Attribution Model

**Formula for Department Chargeback**:

```
Department Cost = 
  (OpenAI tokens used × OpenAI rate) +
  (Cosmos DB RUs used × Cosmos rate) +
  (Blob Storage GB × Storage rate) +
  (Search queries × Search rate) +
  (APIM overhead)
```

**Example Calculation (Justice Department)**:
```
OpenAI:    15M tokens × $0.02/1K    = $300
Cosmos DB: 500K RUs × $0.0001/RU    = $50
Storage:   100 GB × $0.20/GB        = $20
Search:    50K queries × $0.0006    = $30
APIM:      150K calls × $0.000067   = $10
─────────────────────────────────────────
Total:                              = $410
```

### 5. Quota Enforcement

**Soft Limits (Warnings)**:
- 80% quota: Email warning to department admin
- 90% quota: Dashboard warning banner
- 95% quota: Daily alert emails

**Hard Limits (Throttling)**:
- 100% quota: Return HTTP 429 (Too Many Requests)
- 110% overage: Allow 10% burst for critical needs
- Overage rate: Charge premium (e.g., $0.05/10K vs $0.04/10K)

**Example Policy**:
```xml
<policies>
    <inbound>
        <base />
        <!-- Check subscription quota -->
        <quota-by-key 
            calls="200000" 
            renewal-period="2592000" 
            counter-key="@(context.Subscription.Id)" />
        
        <!-- Rate limiting -->
        <rate-limit-by-key 
            calls="50" 
            renewal-period="1" 
            counter-key="@(context.Subscription.Id)" />
    </inbound>
</policies>
```

### 6. Self-Service Developer Portal

**Department Administrators Can**:
- View real-time usage dashboard
- Download monthly reports
- Regenerate API keys
- Request quota increases
- View billing history
- Set up usage alerts
- Manage team members

**Portal Features**:
```
Dashboard View (Justice Department):
┌─────────────────────────────────────────────────┐
│  Justice Department - EVA Domain Assistant      │
├─────────────────────────────────────────────────┤
│  Current Period: Dec 1-31, 2025                 │
│                                                  │
│  Usage: 95,000 / 200,000 calls (47.5%)         │
│  [████████████████░░░░░░░░░░░░░░░░░░░░]        │
│                                                  │
│  Projected Cost: $280 (on track)                │
│  Rate Limit: 45 req/sec avg (90% of 50)        │
│  Errors: 0.2% (good)                            │
│                                                  │
│  [View Detailed Reports] [Request Increase]     │
└─────────────────────────────────────────────────┘
```

---

## Information Assistant API Endpoints

### Core API Operations (From MS Info Assistant)

Based on the Microsoft Information Assistant reference architecture, EVA Domain Assistant exposes these endpoints:

#### 1. RAG Query (`/rag/answer`)
**Purpose**: Natural language question answering over documents  
**Method**: POST  
**Request**:
```json
{
  "question": "What are the eligibility requirements for EI benefits?",
  "conversation_id": "conv-12345",
  "context": {
    "filters": ["department:employment", "year:2024"]
  }
}
```
**Response**:
```json
{
  "answer": "To be eligible for EI benefits, you must have...",
  "citations": [
    {"document": "EI-Policy-2024.pdf", "page": 12},
    {"document": "Benefits-Guide.pdf", "page": 5}
  ],
  "confidence": 0.87,
  "tokens_used": 1250
}
```
**Typical Usage**: 60-70% of all API calls  
**Cost Driver**: High OpenAI token consumption

#### 2. Document Summarization (`/doc/summarize`)
**Purpose**: Generate summaries of uploaded documents  
**Method**: POST  
**Request**:
```json
{
  "document_id": "doc-67890",
  "summary_length": "medium",
  "focus_areas": ["key_points", "action_items"]
}
```
**Response**:
```json
{
  "summary": "This policy document outlines...",
  "key_points": [
    "Eligibility criteria updated",
    "New processing timeline: 28 days"
  ],
  "word_count": 250,
  "tokens_used": 850
}
```
**Typical Usage**: 20-30% of API calls  
**Cost Driver**: Moderate OpenAI token usage

#### 3. Document Comparison (`/doc/compare`)
**Purpose**: Compare two documents for differences  
**Method**: POST  
**Request**:
```json
{
  "document_a": "policy-2023.pdf",
  "document_b": "policy-2024.pdf",
  "comparison_type": "detailed"
}
```
**Response**:
```json
{
  "differences": [
    {
      "section": "Section 3.2",
      "change_type": "modified",
      "old_text": "Processing time: 35 days",
      "new_text": "Processing time: 28 days"
    }
  ],
  "similarity_score": 0.92,
  "tokens_used": 2100
}
```
**Typical Usage**: 5-10% of API calls  
**Cost Driver**: High token usage (both documents)

#### 4. Entity Extraction (`/doc/extract`)
**Purpose**: Extract entities (people, dates, amounts) from documents  
**Method**: POST  
**Request**:
```json
{
  "document_id": "doc-45678",
  "entity_types": ["person", "date", "amount", "organization"]
}
```
**Response**:
```json
{
  "entities": {
    "persons": ["John Smith", "Jane Doe"],
    "dates": ["2024-01-15", "2024-03-30"],
    "amounts": ["$1,250", "$45,000"],
    "organizations": ["Service Canada", "ESDC"]
  },
  "tokens_used": 950
}
```
**Typical Usage**: 3-5% of API calls  
**Cost Driver**: Moderate token usage

### Usage Patterns by Department Type

**Policy/Legal Departments** (Justice, Immigration):
- High `/rag/answer` usage (research-heavy)
- Moderate `/doc/compare` (policy versions)
- Lower `/doc/summarize`

**Operational Departments** (Service Canada):
- High `/doc/summarize` (quick reviews)
- Moderate `/rag/answer` (procedure lookups)
- High `/doc/extract` (form processing)

**IT/Admin Departments**:
- Balanced usage across all endpoints
- Lower overall volume

---

## Cost Breakdown by API Endpoint

### Typical Costs per 1,000 API Calls

| Endpoint | Avg Tokens/Call | OpenAI Cost | Cosmos DB | Storage | Search | Total |
|----------|-----------------|-------------|-----------|---------|--------|-------|
| `/rag/answer` | 1,500 | $0.030 | $0.005 | $0.002 | $0.010 | $0.047 |
| `/doc/summarize` | 1,000 | $0.020 | $0.003 | $0.001 | $0.005 | $0.029 |
| `/doc/compare` | 2,500 | $0.050 | $0.008 | $0.003 | $0.015 | $0.076 |
| `/doc/extract` | 1,200 | $0.024 | $0.004 | $0.002 | $0.008 | $0.038 |

**Example: Justice Department (150K calls/month)**:
```
Endpoint Distribution:
  /rag/answer:    85K calls × $0.047 = $3,995
  /doc/summarize: 45K calls × $0.029 = $1,305
  /doc/compare:   15K calls × $0.076 = $1,140
  /doc/extract:    5K calls × $0.038 =   $190
  ─────────────────────────────────────────────
  APIM overhead:                        $10
  Total:                              $6,640/month
```

---

## Implementation Plan

### Phase 1: APIM Deployment (Week 1)

**Objective**: Deploy APIM and configure basic routing

**Tasks**:
1. Create APIM instance (Consumption tier)
2. Import EVA Domain Assistant API definition
3. Configure backend (existing EVA DA endpoints)
4. Test basic routing (health check)

**Deliverables**:
- APIM instance running
- EVA DA accessible through APIM
- Health endpoint validated

**Commands**:
```bash
# Create APIM instance
az apim create \
  --name esdc-eva-apim \
  --resource-group eva-rg \
  --publisher-name "ESDC IT" \
  --publisher-email admin@esdc.gc.ca \
  --sku-name Consumption

# Import API definition
az apim api import \
  --resource-group eva-rg \
  --service-name esdc-eva-apim \
  --path /eva \
  --specification-path eva-domain-assistant-openapi.json \
  --specification-format OpenApiJson
```

### Phase 2: Subscription Setup (Week 1-2)

**Objective**: Create 15 department subscriptions with API keys

**Tasks**:
1. Create APIM Product ("EVA Domain Assistant")
2. Define product tiers (Small/Medium/Large/Enterprise)
3. Create 15 subscriptions (one per department)
4. Generate and distribute API keys securely

**Deliverables**:
- 15 department subscriptions active
- API keys distributed to department admins
- Documentation for API key usage

**Example Product Definition**:
```json
{
  "displayName": "EVA Domain Assistant - Enterprise",
  "description": "Enterprise tier for large departments (1500+ users)",
  "approvalRequired": false,
  "subscriptionRequired": true,
  "state": "published",
  "quota": {
    "calls": 300000,
    "renewalPeriod": "P1M"
  }
}
```

### Phase 3: Usage Policies (Week 2)

**Objective**: Configure rate limiting, quotas, and cost attribution

**Tasks**:
1. Implement per-subscription rate limiting
2. Configure monthly quotas per tier
3. Add cost attribution headers
4. Set up usage analytics collection

**Deliverables**:
- Rate limits enforced (prevent DoS)
- Quotas prevent overruns
- Usage data flowing to analytics

**Policy Configuration**:
```xml
<policies>
    <inbound>
        <base />
        <!-- Authentication -->
        <validate-jwt header-name="Authorization" failed-validation-httpcode="401">
            <openid-config url="https://login.microsoftonline.com/..." />
        </validate-jwt>
        
        <!-- Rate limiting (50 req/sec per subscription) -->
        <rate-limit-by-key 
            calls="50" 
            renewal-period="1" 
            counter-key="@(context.Subscription.Id)" />
        
        <!-- Monthly quota (200K calls) -->
        <quota-by-key 
            calls="200000" 
            renewal-period="2592000" 
            counter-key="@(context.Subscription.Id)" />
        
        <!-- Add cost attribution headers -->
        <set-header name="X-Department-ID" exists-action="override">
            <value>@(context.Subscription.Name)</value>
        </set-header>
        <set-header name="X-Subscription-Key" exists-action="override">
            <value>@(context.Subscription.Id)</value>
        </set-header>
    </inbound>
    
    <backend>
        <base />
    </backend>
    
    <outbound>
        <base />
        <!-- Add usage metrics to response headers -->
        <set-header name="X-Quota-Remaining" exists-action="override">
            <value>@(context.Response.Headers.GetValueOrDefault("X-Rate-Limit-Remaining", "unknown"))</value>
        </set-header>
    </outbound>
    
    <on-error>
        <base />
    </on-error>
</policies>
```

### Phase 4: Analytics & Reporting (Week 3)

**Objective**: Enable cost tracking and chargeback reporting

**Tasks**:
1. Configure Application Insights integration
2. Create custom analytics queries
3. Build Power BI dashboard
4. Set up automated monthly reports

**Deliverables**:
- Real-time usage dashboard
- Monthly cost reports per department
- Budget alerts configured

**Analytics Query (KQL)**:
```kql
ApiManagementGatewayLogs
| where TimeGenerated > ago(30d)
| extend Department = tostring(parse_json(Properties).SubscriptionName)
| extend Endpoint = tostring(parse_json(Properties).ApiId)
| summarize 
    TotalCalls = count(),
    AvgLatency = avg(DurationMs),
    ErrorRate = countif(ResponseCode >= 400) * 100.0 / count()
    by Department, Endpoint
| order by TotalCalls desc
```

### Phase 5: Self-Service Portal (Week 3-4)

**Objective**: Enable department self-service management

**Tasks**:
1. Deploy APIM Developer Portal
2. Configure Azure AD authentication
3. Customize portal branding (ESDC)
4. Create user documentation

**Deliverables**:
- Developer portal accessible at https://eva-portal.esdc.gc.ca
- Department admins can log in
- Self-service API key management
- Usage dashboards available

**Portal Customization**:
- ESDC branding (logo, colors)
- Department-specific dashboards
- API documentation (OpenAPI/Swagger)
- Interactive API testing console

### Phase 6: Chargeback Automation (Week 4)

**Objective**: Automate monthly billing process

**Tasks**:
1. Create cost calculation logic
2. Generate monthly invoices automatically
3. Integrate with ESDC financial systems
4. Set up approval workflows

**Deliverables**:
- Automated monthly invoice generation
- Cost allocation to department budgets
- Financial system integration
- Audit trail for all charges

**Invoice Generation Script**:
```python
def generate_monthly_invoice(subscription_id, period):
    """Generate invoice for department subscription."""
    
    # Query usage metrics
    usage = get_usage_metrics(subscription_id, period)
    
    # Calculate costs
    costs = {
        'openai': usage['tokens'] * OPENAI_RATE,
        'cosmos_db': usage['ru_consumed'] * COSMOS_RATE,
        'storage': usage['storage_gb'] * STORAGE_RATE,
        'search': usage['search_queries'] * SEARCH_RATE,
        'apim': usage['api_calls'] * APIM_RATE
    }
    
    # Generate invoice
    invoice = {
        'subscription_id': subscription_id,
        'department': get_department_name(subscription_id),
        'period': period,
        'usage_summary': usage,
        'cost_breakdown': costs,
        'total': sum(costs.values()),
        'generated_at': datetime.utcnow()
    }
    
    # Send to financial system
    submit_invoice(invoice)
    
    # Email department admin
    send_invoice_email(invoice)
    
    return invoice
```

---

## Cost/Benefit Analysis

### Current State (No APIM)

**Monthly Costs** (estimated):
- Azure OpenAI: $6,000
- Cosmos DB: $1,500
- Blob Storage: $500
- Cognitive Search: $800
- Other services: $500
- **Total: ~$9,300/month**

**Problems**:
- ❌ Cannot allocate costs to departments
- ❌ No usage control (departments can overuse)
- ❌ Manual tracking effort: 2-3 days/month
- ❌ No accountability or chargeback
- ❌ Budget overruns with no early warning

### With APIM

**Monthly Costs**:
- APIM Consumption tier: ~$75 (for 1.5M calls)
- Existing Azure services: ~$9,300
- **Total: ~$9,375/month**

**Additional Cost**: $75/month (~0.8% increase)

**Benefits**:
- ✅ **Full cost visibility** - Know exactly what each department costs
- ✅ **Fair chargeback** - Departments pay their actual usage
- ✅ **Usage control** - Quotas prevent overruns
- ✅ **Accountability** - Departments optimize usage when charged
- ✅ **Automated billing** - Zero manual tracking effort
- ✅ **Budget alerts** - Early warning at 80% quota
- ✅ **Self-service** - Departments manage themselves

**Expected Savings**:
- 10-20% reduction in waste (departments more careful)
- Savings: $930-$1,860/month
- **Net benefit: $855-$1,785/month** after APIM cost

**ROI**: 1,140% - 2,380% return on APIM investment

### 3-Year TCO Comparison

| Metric | Without APIM | With APIM | Savings |
|--------|--------------|-----------|---------|
| Azure Services | $335,000 | $335,000 | $0 |
| APIM Cost | $0 | $2,700 | -$2,700 |
| Manual Tracking | $36,000 | $0 | +$36,000 |
| Waste Reduction (15%) | $0 | -$50,000 | +$50,000 |
| **Total** | **$371,000** | **$287,700** | **$83,300** |

**3-Year Savings: $83,300 (22% reduction)**

---

## Risk Assessment

### Implementation Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Department resistance to quotas | Medium | Medium | Start with generous quotas, adjust based on usage patterns |
| API key management complexity | Low | Low | Use Azure AD integration, automated key rotation |
| Performance impact (latency) | Low | Low | APIM adds <5ms latency, negligible for use case |
| Migration downtime | Low | High | Blue-green deployment, run both systems in parallel |
| Cost underestimation | Medium | Medium | Start with 3-month pilot, adjust quotas based on actual data |

### Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| APIM service outage | Low | High | 99.95% SLA, automatic failover to backend |
| Quota exhaustion (critical need) | Medium | High | 10% burst allowance, emergency override process |
| Billing disputes | Medium | Medium | Detailed audit logs, transparent usage reports |
| Department budget overruns | Low | Medium | Proactive alerts at 80%, 90%, 95% quota |

---

## Success Metrics

### Key Performance Indicators (KPIs)

**Cost Management**:
- ✅ 100% cost attribution to departments (vs 0% today)
- ✅ 15-20% reduction in wasted usage
- ✅ Zero unbudgeted cost overruns
- ✅ Monthly chargeback accuracy >99%

**Usage Control**:
- ✅ <5% of departments exceed quotas
- ✅ Zero unauthorized access incidents
- ✅ <1% API error rate
- ✅ Average latency <200ms (p95)

**Operational Efficiency**:
- ✅ Zero manual tracking effort (vs 2-3 days/month)
- ✅ Automated invoicing for all 15 departments
- ✅ Self-service portal usage >80%
- ✅ Department satisfaction score >4/5

**Business Value**:
- ✅ ROI >1,000% within 12 months
- ✅ Fair cost allocation across departments
- ✅ Budget predictability (±5% variance)
- ✅ Usage transparency and accountability

---

## Next Steps

### Immediate Actions (This Week)

1. **Approval**: Present this plan to ESDC IT leadership
2. **Budget**: Allocate $75/month for APIM Consumption tier
3. **Stakeholders**: Identify department admin contacts (15)
4. **Pilot**: Select 2-3 departments for pilot (Week 1-2)

### Short-Term (Weeks 1-4)

1. **Week 1**: Deploy APIM, basic routing, health checks
2. **Week 2**: Create 15 subscriptions, distribute API keys
3. **Week 3**: Configure quotas, analytics, reporting
4. **Week 4**: Enable self-service portal, chargeback automation

### Medium-Term (Months 2-3)

1. **Month 2**: Full production rollout (all 15 departments)
2. **Month 2**: Monitor usage, adjust quotas based on actual data
3. **Month 3**: First automated billing cycle, collect feedback

### Long-Term (Months 4-12)

1. **Quarterly**: Review cost allocation, optimize quotas
2. **Annually**: Expand to other EVA Suite services (EVA Chat, etc.)
3. **Ongoing**: Continuous improvement based on department feedback

---

## Conclusion

**Azure API Management solves ESDC's critical cost control problem**:

✅ **Problem**: No visibility into which departments drive $9,300/month in Azure costs  
✅ **Solution**: APIM provides per-department tracking and automated chargeback  

✅ **Problem**: Cannot limit or control department usage  
✅ **Solution**: APIM enforces quotas and rate limits per subscription  

✅ **Problem**: Unfair cost allocation (heavy users subsidized)  
✅ **Solution**: Each department pays exactly for what they use  

✅ **Problem**: Manual tracking effort (2-3 days/month)  
✅ **Solution**: Fully automated usage analytics and billing  

**Cost**: $75/month for APIM  
**Benefit**: $850-$1,800/month in savings + operational efficiency  
**ROI**: 1,100-2,400% return on investment  

**Recommendation**: Proceed with APIM implementation immediately. The cost is negligible compared to the benefits, and the 4-week implementation timeline ensures rapid time-to-value.

---

**Document Owner**: Marco Presta + GitHub Copilot  
**Approvers**: ESDC IT Leadership, Finance Department  
**Implementation Lead**: EVA Suite Development Team  
**Timeline**: 4 weeks (pilot), 12 weeks (full rollout)
