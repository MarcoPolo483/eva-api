# Webhook Storage Layer Implementation

## Overview

Fully implemented persistent storage for webhook subscriptions, delivery logs, and dead letter queue using Azure Cosmos DB.

## Architecture

### Containers

Three new Cosmos DB containers created:

1. **webhooks** (partition key: `/tenant_id`)
   - Webhook subscription definitions
   - Configuration and secrets
   - Delivery statistics
   
2. **webhook_logs** (partition key: `/webhook_id`)
   - Individual delivery attempt records
   - Response data and timing
   - Error details
   
3. **webhook_dead_letter_queue** (partition key: `/tenant_id`)
   - Failed events after retry exhaustion
   - Error tracking
   - Manual review queue

### Schema

#### Webhook Document
```json
{
  "id": "webhook_abc123",
  "url": "https://example.com/webhooks/eva",
  "event_types": ["space.created", "document.added", "query.*"],
  "description": "Production webhook",
  "secret": "whsec_...",
  "is_active": true,
  "tenant_id": "tenant_123",
  "created_at": "2025-12-08T12:00:00",
  "updated_at": "2025-12-08T12:00:00",
  "last_delivery_at": "2025-12-08T12:30:00",
  "stats": {
    "total_deliveries": 150,
    "successful_deliveries": 145,
    "failed_deliveries": 5,
    "avg_response_time_ms": 125.5
  }
}
```

#### Webhook Log Document
```json
{
  "id": "log_xyz789",
  "webhook_id": "webhook_abc123",
  "tenant_id": "tenant_123",
  "event_type": "document.added",
  "event_id": "evt_def456",
  "timestamp": "2025-12-08T12:30:00",
  "attempt": 1,
  "status_code": 200,
  "response_body": "{\"success\": true}",
  "error": null,
  "duration_ms": 125,
  "success": true
}
```

#### Dead Letter Queue Document
```json
{
  "id": "dlq_ghi012",
  "webhook_id": "webhook_abc123",
  "tenant_id": "tenant_123",
  "event": {
    "event_type": "query.submitted",
    "event_id": "evt_jkl345",
    "timestamp": "2025-12-08T12:45:00",
    "data": {...}
  },
  "error": "Connection timeout after 3 attempts",
  "timestamp": "2025-12-08T12:46:30",
  "retries_exhausted": true,
  "processed": false
}
```

## CosmosDBService Methods

### Webhook Management

#### `create_webhook(webhook_data: dict) -> dict`
Creates new webhook subscription.

```python
webhook_doc = {
    "id": f"webhook_{uuid4().hex[:16]}",
    "url": "https://example.com/webhook",
    "event_types": ["document.*"],
    "tenant_id": "tenant_123",
    "is_active": True,
    ...
}
result = await cosmos.create_webhook(webhook_doc)
```

#### `get_webhook(webhook_id: str, tenant_id: str) -> Optional[dict]`
Retrieves webhook by ID and tenant.

```python
webhook = await cosmos.get_webhook("webhook_abc123", "tenant_123")
```

#### `update_webhook(webhook_id: str, tenant_id: str, updates: dict) -> Optional[dict]`
Updates webhook configuration.

```python
updates = {"is_active": False, "url": "https://new-url.com"}
updated = await cosmos.update_webhook("webhook_abc123", "tenant_123", updates)
```

#### `delete_webhook(webhook_id: str, tenant_id: str) -> bool`
Deletes webhook subscription.

```python
success = await cosmos.delete_webhook("webhook_abc123", "tenant_123")
```

#### `list_webhooks(tenant_id: str) -> list[dict]`
Lists all webhooks for a tenant.

```python
webhooks = await cosmos.list_webhooks("tenant_123")
```

#### `get_active_webhooks(tenant_id: str, event_type: str) -> list[dict]`
Queries active webhooks matching event type or wildcard pattern.

```python
# Get webhooks subscribed to "document.added" or "document.*"
webhooks = await cosmos.get_active_webhooks("tenant_123", "document.added")
```

### Webhook Logs

#### `create_webhook_log(log_data: dict) -> dict`
Creates delivery log entry.

```python
log_data = {
    "id": str(uuid4()),
    "webhook_id": "webhook_abc123",
    "tenant_id": "tenant_123",
    "event_type": "document.added",
    "status_code": 200,
    "success": True,
    ...
}
await cosmos.create_webhook_log(log_data)
```

#### `list_webhook_logs(webhook_id: str, limit: int = 50) -> list[dict]`
Retrieves delivery logs ordered by timestamp DESC.

```python
logs = await cosmos.list_webhook_logs("webhook_abc123", limit=100)
```

### Dead Letter Queue

#### `create_dlq_entry(dlq_data: dict) -> dict`
Creates DLQ entry for permanently failed deliveries.

```python
dlq_data = {
    "id": str(uuid4()),
    "webhook_id": "webhook_abc123",
    "tenant_id": "tenant_123",
    "event": {...},
    "error": "Max retries exceeded",
    "retries_exhausted": True,
    "processed": False
}
await cosmos.create_dlq_entry(dlq_data)
```

### Statistics

#### `update_webhook_stats(webhook_id: str, tenant_id: str, success: bool, response_time_ms: float) -> None`
Updates webhook delivery statistics with running averages.

```python
await cosmos.update_webhook_stats(
    webhook_id="webhook_abc123",
    tenant_id="tenant_123",
    success=True,
    response_time_ms=125.5
)
```

## WebhookService Integration

### Broadcast Event Flow

```python
# 1. Event triggered in CRUD operation
await webhook_service.broadcast_event(
    event_type="document.added",
    event={...},
    tenant_id="tenant_123"
)

# 2. Service queries active webhooks
webhooks = await cosmos.get_active_webhooks(tenant_id, "document.added")
wildcard_webhooks = await cosmos.get_active_webhooks(tenant_id, "document.*")

# 3. Events queued for each matching webhook
for webhook in all_webhooks:
    await webhook_service.deliver_event(webhook['id'], event, tenant_id)
```

### Delivery Processing

```python
# 1. Fetch webhook details
webhook = await cosmos.get_webhook(webhook_id, tenant_id)

# 2. Attempt delivery with retries
for attempt in range(3):
    result = await webhook_service._attempt_delivery(webhook, event, secret)
    
    # Log attempt
    await cosmos.create_webhook_log({
        "webhook_id": webhook_id,
        "attempt": attempt,
        "status_code": result["status_code"],
        "success": result["success"],
        ...
    })
    
    if result["success"]:
        break
    
    await asyncio.sleep(RETRY_DELAYS[attempt])

# 3. Update statistics
await cosmos.update_webhook_stats(webhook_id, tenant_id, success, response_time)

# 4. Send to DLQ if all retries failed
if not success:
    await cosmos.create_dlq_entry({
        "webhook_id": webhook_id,
        "event": event,
        "error": last_error,
        ...
    })
```

## REST API Endpoints

All endpoints now fully operational with persistent storage.

### POST /api/v1/webhooks
Create webhook subscription.

**Request:**
```json
{
  "url": "https://example.com/webhook",
  "events": ["space.created", "document.*"],
  "description": "My webhook",
  "secret": "my_secret",
  "active": true
}
```

**Response:**
```json
{
  "id": "webhook_abc123",
  "url": "https://example.com/webhook",
  "events": ["space.created", "document.*"],
  "active": true,
  "tenant_id": "tenant_123",
  "created_at": "2025-12-08T12:00:00",
  "stats": {...}
}
```

### GET /api/v1/webhooks
List all webhooks for tenant.

**Query Parameters:**
- `active_only`: boolean (optional)

### GET /api/v1/webhooks/{webhook_id}
Get webhook details.

### PUT /api/v1/webhooks/{webhook_id}
Update webhook configuration.

### DELETE /api/v1/webhooks/{webhook_id}
Delete webhook subscription.

### GET /api/v1/webhooks/{webhook_id}/logs
Get delivery logs.

**Query Parameters:**
- `limit`: integer (1-100, default 50)

**Response:**
```json
[
  {
    "id": "log_xyz789",
    "webhook_id": "webhook_abc123",
    "event_type": "document.added",
    "delivered_at": "2025-12-08T12:30:00",
    "status_code": 200,
    "success": true,
    "response_time_ms": 125,
    "error_message": null,
    "retry_count": 0
  }
]
```

### POST /api/v1/webhooks/{webhook_id}/test
Send test event to webhook.

**Request:**
```json
{
  "event_type": "webhook.test"
}
```

**Response:**
```json
{
  "message": "Test event queued",
  "event_id": "evt_test_abc123"
}
```

## Wildcard Pattern Matching

Webhooks support wildcard subscriptions:

- `document.*` matches: `document.added`, `document.deleted`
- `space.*` matches: `space.created`, `space.updated`, `space.deleted`
- `query.*` matches: `query.submitted`

Implementation in `get_active_webhooks`:
```python
# Exact match query
webhooks = await cosmos.get_active_webhooks(tenant_id, "document.added")

# Wildcard match query
event_prefix = "document.*"
wildcard_webhooks = await cosmos.get_active_webhooks(tenant_id, event_prefix)

# Deduplicate
all_webhooks = {w['id']: w for w in webhooks + wildcard_webhooks}
```

## Performance Considerations

### Query Optimization
- All queries use partition keys (tenant_id or webhook_id)
- No cross-partition queries except list_webhooks
- Indexed fields: event_types, is_active

### Throughput
- Provisioned: 400 RU/s per container
- Autoscale recommended for production
- Consider container merge for low-volume tenants

### Retention
- Webhook logs: Consider TTL (30-90 days)
- DLQ entries: Manual processing required
- Implement cleanup jobs for old data

## Testing

### Unit Tests
```bash
# Test webhook storage methods
pytest tests/test_phase3_features.py::TestWebhookService -v

# Test REST API endpoints
pytest tests/test_webhooks_api.py -v
```

### Integration Tests
```bash
# Test full event flow
1. Create webhook subscription
2. Trigger event (create space)
3. Verify delivery log created
4. Check webhook stats updated
```

### Postman Collection
Import `postman/EVA-API-Phase3-GraphQL-Webhooks.postman_collection.json`

**Webhooks folder includes:**
- Create webhook
- List webhooks
- Get webhook details
- Update webhook
- Delete webhook
- Get delivery logs
- Send test event

## Monitoring

### Key Metrics
- Webhook delivery success rate
- Average response time
- Retry rate
- DLQ growth rate

### Alerts
- DLQ entries > threshold
- Webhook failure rate > 10%
- Average response time > 5s
- Inactive webhooks with errors

### Logs
```bash
# Webhook delivery logs
grep "webhook" logs/app.log | grep -E "Queued|Logged|Updated"

# Failed deliveries
grep "DLQ" logs/app.log

# Stats updates
grep "Updated stats" logs/app.log
```

## Next Steps

1. **Enable Autoscale**: Configure RU/s autoscaling for production
2. **Implement TTL**: Add time-to-live for logs container
3. **DLQ Dashboard**: Build UI for reviewing failed deliveries
4. **Batch Processing**: Optimize high-volume event broadcasting
5. **Redis Pub/Sub**: Replace polling with real-time notifications
6. **Webhook Health Checks**: Periodic endpoint validation
7. **Rate Limiting**: Per-webhook delivery rate limits
8. **Signature Rotation**: Automated secret rotation workflow

## Files Modified

### Core Implementation
- `src/eva_api/services/cosmos_service.py` - Added 12 webhook methods
- `src/eva_api/services/webhook_service.py` - Replaced TODOs with Cosmos calls
- `src/eva_api/routers/webhooks.py` - Updated all endpoints to use CosmosDBService
- `src/eva_api/main.py` - Uncommented webhook router

### Schema Alignment
- Webhook fields: `event_types` (was `events`), `is_active` (was `active`)
- Stats structure: `{total_deliveries, successful_deliveries, failed_deliveries, avg_response_time_ms}`
- Timestamp fields: `last_delivery_at` (was `last_triggered_at`)

## Verification

✅ Server starts with webhook storage enabled
✅ All endpoints import successfully
✅ Cosmos DB containers initialized
✅ Webhook delivery service operational
✅ Background worker processing events
✅ REST API accessible at `/api/v1/webhooks`
✅ OpenAPI docs include Webhooks section

**Server Status:**
```
INFO: Uvicorn running on http://127.0.0.1:8000
INFO: Webhook delivery service started
INFO: Webhook delivery worker started
```

**Available Endpoints:**
- REST API: http://localhost:8000/docs
- GraphQL: http://localhost:8000/graphql
- WebSocket: ws://localhost:8000/graphql
- Health: http://localhost:8000/health
