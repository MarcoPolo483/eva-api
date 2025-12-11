# GraphQL WebSocket Subscriptions - Testing Guide

This guide shows how to test GraphQL subscriptions via WebSocket connections.

## Prerequisites

```bash
# Install wscat (WebSocket client)
npm install -g wscat
```

## Connection Setup

### 1. Connect to WebSocket Endpoint

```bash
wscat -c "ws://localhost:8000/graphql" -s graphql-ws
```

### 2. Initialize Connection

Send connection initialization message:

```json
{"type":"connection_init"}
```

You should receive:

```json
{"type":"connection_ack"}
```

## Available Subscriptions

### 1. Document Added Subscription

Subscribe to document upload events in a specific space:

```json
{
  "id": "1",
  "type": "subscribe",
  "payload": {
    "query": "subscription DocumentAdded($spaceId: UUID!) { documentAdded(spaceId: $spaceId) { id filename size contentType uploadedAt } }",
    "variables": {
      "spaceId": "YOUR_SPACE_ID"
    }
  }
}
```

**Trigger Event:**
Upload a document to the space via REST API:

```bash
curl -X POST http://localhost:8000/api/v1/spaces/YOUR_SPACE_ID/documents \
  -H "Authorization: Bearer YOUR_JWT" \
  -F "file=@test.pdf"
```

**Expected Response:**

```json
{
  "id": "1",
  "type": "next",
  "payload": {
    "data": {
      "documentAdded": {
        "id": "doc-123",
        "filename": "test.pdf",
        "size": 1024,
        "contentType": "application/pdf",
        "uploadedAt": "2025-12-08T12:00:00Z"
      }
    }
  }
}
```

---

### 2. Query Completed Subscription

Subscribe to query completion notifications:

```json
{
  "id": "2",
  "type": "subscribe",
  "payload": {
    "query": "subscription QueryCompleted($queryId: UUID!) { queryCompleted(queryId: $queryId) { id question answer status completedAt } }",
    "variables": {
      "queryId": "YOUR_QUERY_ID"
    }
  }
}
```

**Trigger Event:**
The query processing service updates the query status to "completed".

**Expected Response:**

```json
{
  "id": "2",
  "type": "next",
  "payload": {
    "data": {
      "queryCompleted": {
        "id": "query-123",
        "question": "What is EVA?",
        "answer": "EVA is an AI-powered platform...",
        "status": "completed",
        "completedAt": "2025-12-08T12:05:00Z"
      }
    }
  }
}
```

---

### 3. Space Events Subscription

Subscribe to all space events (created, updated, deleted) for a tenant:

```json
{
  "id": "3",
  "type": "subscribe",
  "payload": {
    "query": "subscription SpaceEvents($tenantId: String!) { spaceEvents(tenantId: $tenantId) { eventType timestamp space { id name description } } }",
    "variables": {
      "tenantId": "YOUR_TENANT_ID"
    }
  }
}
```

**Trigger Event:**
Create, update, or delete a space via REST API:

```bash
# Create space
curl -X POST http://localhost:8000/api/v1/spaces \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"name": "New Space", "description": "Test"}'

# Update space
curl -X PUT http://localhost:8000/api/v1/spaces/SPACE_ID \
  -H "Authorization: Bearer YOUR_JWT" \
  -H "Content-Type: application/json" \
  -d '{"name": "Updated Space"}'

# Delete space
curl -X DELETE http://localhost:8000/api/v1/spaces/SPACE_ID \
  -H "Authorization: Bearer YOUR_JWT"
```

**Expected Response:**

```json
{
  "id": "3",
  "type": "next",
  "payload": {
    "data": {
      "spaceEvents": {
        "eventType": "CREATED",
        "timestamp": "2025-12-08T12:00:00Z",
        "space": {
          "id": "space-123",
          "name": "New Space",
          "description": "Test"
        }
      }
    }
  }
}
```

---

### 4. Query Updates Subscription

Subscribe to real-time query updates:

```json
{
  "id": "4",
  "type": "subscribe",
  "payload": {
    "query": "subscription QueryUpdates($spaceId: UUID!) { queryUpdates(spaceId: $spaceId) { id question status answer progress createdAt } }",
    "variables": {
      "spaceId": "YOUR_SPACE_ID"
    }
  }
}
```

**Expected Response:**

```json
{
  "id": "4",
  "type": "next",
  "payload": {
    "data": {
      "queryUpdates": {
        "id": "query-123",
        "question": "What is EVA?",
        "status": "processing",
        "answer": null,
        "progress": 50,
        "createdAt": "2025-12-08T12:00:00Z"
      }
    }
  }
}
```

---

## Subscription Lifecycle

### Unsubscribe from Subscription

```json
{
  "id": "1",
  "type": "complete"
}
```

### Close Connection

```json
{
  "type": "connection_terminate"
}
```

Or press `Ctrl+C` in wscat.

---

## GraphQL Playground Alternative

You can also test subscriptions using the GraphQL Playground:

1. Open browser: `http://localhost:8000/graphql`
2. Write your subscription query in the left panel
3. Add variables in the bottom panel
4. Click the "Play" button
5. Watch real-time updates in the right panel

**Example:**

```graphql
subscription {
  documentAdded(spaceId: "YOUR_SPACE_ID") {
    id
    filename
    size
    contentType
    uploadedAt
  }
}
```

---

## Troubleshooting

### Connection Refused

- Ensure server is running: `uvicorn eva_api.main:app --host 127.0.0.1 --port 8000`
- Check WebSocket endpoint: `ws://localhost:8000/graphql`

### No Events Received

- Verify Redis is connected (check server logs)
- Ensure you're triggering events correctly (check REST API responses)
- Confirm subscription variables match the triggered event

### Authentication Required

Some subscriptions may require authentication. Include Authorization header in connection params:

```json
{
  "type": "connection_init",
  "payload": {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
  }
}
```

---

## Performance Notes

- **DataLoader**: All GraphQL queries use DataLoader to prevent N+1 queries
- **Redis Pub/Sub**: Subscriptions use Redis for real-time event broadcasting
- **Connection Limits**: Default limit is 100 concurrent WebSocket connections
- **Polling Interval**: Subscriptions poll every 5 seconds when Redis is unavailable

---

## Event Broadcasting Status

✅ **Active**: Webhook events are broadcast from all CRUD operations  
⏸️ **Pending**: Redis Pub/Sub integration for subscriptions (currently polling-based)  
⏸️ **Pending**: Webhook delivery requires Cosmos DB storage setup

Check server logs to see event broadcasting:

```bash
# Watch server logs
tail -f logs/app.log | grep -E "Broadcast|webhook"
```

Example log output:

```
2025-12-08 12:00:00 - eva_api.routers.spaces - INFO - Broadcast space.created - webhook storage pending
2025-12-08 12:01:00 - eva_api.routers.documents - INFO - Broadcast document.added - webhook storage pending
```
