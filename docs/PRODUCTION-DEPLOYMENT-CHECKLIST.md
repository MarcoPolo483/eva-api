# Production Deployment Checklist

## Environment Configuration

### Required Environment Variables

Create `.env.production` file:

```bash
# Application
EVA_API_VERSION=1.0.0
ENVIRONMENT=production
DEBUG=false

# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com
AZURE_OPENAI_KEY=your-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure Cosmos DB
COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-key
COSMOS_DB_DATABASE=eva-api-prod

# Azure Blob Storage
BLOB_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...
BLOB_STORAGE_CONTAINER=eva-documents-prod

# Redis
REDIS_HOST=your-redis-cache.redis.cache.windows.net
REDIS_PORT=6380
REDIS_PASSWORD=your-redis-key
REDIS_SSL=true
REDIS_DB=0

# Security
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60
API_KEY_SALT=your-salt-here-min-32-chars

# CORS
CORS_ORIGINS=["https://your-frontend-domain.com", "https://www.your-domain.com"]

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=100/minute
RATE_LIMIT_AUTHENTICATED=1000/minute

# Timeouts
AZURE_TIMEOUT=30
HTTP_TIMEOUT=10

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Terraform Variables

Update `terraform/environments/prod/terraform.tfvars`:

```hcl
environment = "prod"
location    = "eastus"

# App Service
app_service_sku = {
  tier = "PremiumV3"
  size = "P1v3"
}

# Cosmos DB
cosmos_db_throughput = 1000  # RU/s
cosmos_db_enable_free_tier = false
cosmos_db_backup_policy = {
  type                = "Continuous"
  retention_hours     = 720  # 30 days
}

# Redis Cache
redis_sku = {
  family = "P"
  capacity = 1
}
redis_enable_non_ssl_port = false

# Storage Account
storage_account_tier = "Standard"
storage_account_replication = "GRS"  # Geo-redundant
```

## Redis Pub/Sub Configuration

### Enable Redis for Subscriptions

Update `src/eva_api/services/redis_service.py`:

```python
async def publish_event(self, channel: str, message: dict) -> None:
    """Publish event to Redis channel."""
    if self.redis_client:
        await self.redis_client.publish(
            channel, 
            json.dumps(message)
        )

async def subscribe_to_channel(self, channel: str) -> AsyncIterator[dict]:
    """Subscribe to Redis channel for real-time events."""
    if not self.redis_client:
        return
    
    pubsub = self.redis_client.pubsub()
    await pubsub.subscribe(channel)
    
    try:
        async for message in pubsub.listen():
            if message["type"] == "message":
                yield json.loads(message["data"])
    finally:
        await pubsub.unsubscribe(channel)
```

### Update GraphQL Subscription Resolvers

Replace polling with Redis Pub/Sub in `src/eva_api/graphql/resolvers.py`:

```python
@strawberry.subscription
async def document_added(info: Info, space_id: UUID) -> AsyncGenerator[Document, None]:
    """Subscribe to document upload events (Redis Pub/Sub)."""
    redis = get_redis_service()
    channel = f"space:{space_id}:documents"
    
    try:
        async for message in redis.subscribe_to_channel(channel):
            if message.get("event_type") == "document.added":
                yield message["document"]
    except asyncio.CancelledError:
        logger.info(f"Subscription cancelled for space {space_id}")

@strawberry.subscription
async def space_events(info: Info, tenant_id: str) -> AsyncGenerator[SpaceEvent, None]:
    """Subscribe to space events (Redis Pub/Sub)."""
    redis = get_redis_service()
    channel = f"tenant:{tenant_id}:spaces"
    
    try:
        async for message in redis.subscribe_to_channel(channel):
            yield SpaceEvent(
                event_type=SpaceEventType[message["event_type"].upper()],
                timestamp=message["timestamp"],
                space=message["space"]
            )
    except asyncio.CancelledError:
        logger.info(f"Subscription cancelled for tenant {tenant_id}")
```

### Publish Events from CRUD Operations

Update `src/eva_api/routers/spaces.py`:

```python
async def _broadcast_space_event(background_tasks, event_type, tenant_id, space_data):
    """Broadcast space event via webhook AND Redis."""
    from eva_api.services.webhook_service import get_webhook_service
    from eva_api.services.redis_service import get_redis_service
    
    event = {
        "event_type": f"space.{event_type}",
        "event_id": f"evt_{uuid4().hex[:16]}",
        "timestamp": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "data": {"space": space_data},
        "space": space_data  # For GraphQL subscription
    }
    
    # Webhook broadcast (async background)
    webhook_service = get_webhook_service()
    background_tasks.add_task(
        webhook_service.broadcast_event,
        event_type=event["event_type"],
        event=event,
        tenant_id=tenant_id
    )
    
    # Redis Pub/Sub (real-time subscriptions)
    redis = get_redis_service()
    await redis.publish_event(f"tenant:{tenant_id}:spaces", event)
    
    logger.info(f"Broadcast {event['event_type']} via webhook + Redis")
```

## Application Insights Integration

### Install SDK

```bash
pip install opencensus-ext-azure
```

### Add to `requirements.txt`:

```
opencensus-ext-azure==1.1.9
```

### Configure Telemetry

Create `src/eva_api/services/telemetry_service.py`:

```python
"""Application Insights telemetry service."""

import logging
from typing import Optional

from opencensus.ext.azure.log_exporter import AzureLogHandler
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace import config_integration
from opencensus.trace.samplers import ProbabilitySampler
from opencensus.trace.tracer import Tracer

from eva_api.config import Settings

logger = logging.getLogger(__name__)


class TelemetryService:
    """Azure Application Insights telemetry service."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.tracer: Optional[Tracer] = None
        
        if settings.appinsights_connection_string:
            self._setup_logging()
            self._setup_tracing()
    
    def _setup_logging(self):
        """Configure Azure Log Handler."""
        try:
            handler = AzureLogHandler(
                connection_string=self.settings.appinsights_connection_string
            )
            handler.setLevel(logging.INFO)
            logging.getLogger().addHandler(handler)
            logger.info("Application Insights logging configured")
        except Exception as e:
            logger.warning(f"Failed to setup Application Insights logging: {e}")
    
    def _setup_tracing(self):
        """Configure distributed tracing."""
        try:
            config_integration.trace_integrations(['httpx', 'requests'])
            
            exporter = AzureExporter(
                connection_string=self.settings.appinsights_connection_string
            )
            
            self.tracer = Tracer(
                exporter=exporter,
                sampler=ProbabilitySampler(1.0)  # 100% sampling in prod
            )
            logger.info("Application Insights tracing configured")
        except Exception as e:
            logger.warning(f"Failed to setup Application Insights tracing: {e}")


# Singleton instance
_telemetry_service: Optional[TelemetryService] = None


def initialize_telemetry(settings: Settings) -> TelemetryService:
    """Initialize telemetry service."""
    global _telemetry_service
    _telemetry_service = TelemetryService(settings)
    return _telemetry_service


def get_telemetry_service() -> Optional[TelemetryService]:
    """Get telemetry service instance."""
    return _telemetry_service
```

### Add to `main.py` lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan manager."""
    settings = get_settings()
    logger.info(f"Starting EVA API Platform v{settings.version}")
    
    # Initialize telemetry
    from eva_api.services.telemetry_service import initialize_telemetry
    initialize_telemetry(settings)
    logger.info("Application Insights initialized")
    
    # ... rest of startup
```

### Add Config Setting

Update `src/eva_api/config.py`:

```python
class Settings(BaseSettings):
    # ... existing settings
    
    # Application Insights
    appinsights_connection_string: Optional[str] = Field(
        None,
        env="APPINSIGHTS_CONNECTION_STRING",
        description="Azure Application Insights connection string"
    )
```

## Security Review

### JWT Configuration

#### Token Expiration
```python
# config.py
jwt_expiration_minutes: int = Field(60, env="JWT_EXPIRATION_MINUTES")
```

#### Refresh Token Flow
Create `src/eva_api/routers/auth.py` endpoint:

```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_token: str,
    azure_ad_service: AzureADService = Depends(get_azure_ad_service),
) -> TokenResponse:
    """Refresh access token."""
    try:
        # Verify refresh token
        claims = await azure_ad_service.verify_token(refresh_token)
        
        # Generate new access token
        new_token = await azure_ad_service.generate_token(claims["sub"])
        
        return TokenResponse(
            access_token=new_token,
            token_type="Bearer",
            expires_in=3600
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
```

### API Key Rotation

Create `scripts/rotate_api_keys.py`:

```python
"""Rotate API keys for a tenant."""

import asyncio
import sys
from datetime import datetime, timedelta

from eva_api.config import get_settings
from eva_api.services.cosmos_service import CosmosDBService


async def rotate_api_keys(tenant_id: str, grace_period_days: int = 7):
    """
    Rotate API keys with grace period.
    
    Args:
        tenant_id: Tenant ID
        grace_period_days: Days to keep old key active
    """
    settings = get_settings()
    cosmos = CosmosDBService(settings)
    
    # Generate new API key
    new_key = await cosmos.create_api_key(
        tenant_id=tenant_id,
        name=f"Rotated key {datetime.utcnow().isoformat()}",
        description="Auto-generated during rotation"
    )
    
    # Schedule old keys for deactivation
    expiry_date = datetime.utcnow() + timedelta(days=grace_period_days)
    
    old_keys = await cosmos.list_api_keys(tenant_id)
    for old_key in old_keys:
        if old_key["id"] != new_key["id"]:
            await cosmos.update_api_key(
                key_id=old_key["id"],
                tenant_id=tenant_id,
                updates={"expires_at": expiry_date.isoformat()}
            )
    
    print(f"✅ New API key generated: {new_key['key']}")
    print(f"⏰ Old keys will expire on: {expiry_date.isoformat()}")
    print(f"📋 Grace period: {grace_period_days} days")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python rotate_api_keys.py <tenant_id> [grace_period_days]")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    grace_period = int(sys.argv[2]) if len(sys.argv) > 2 else 7
    
    asyncio.run(rotate_api_keys(tenant_id, grace_period))
```

### CORS Configuration

#### Production Settings

```python
# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Specific domains only
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
    max_age=600,  # 10 minutes
)
```

#### Environment-Specific CORS

```python
# config.py
cors_origins: List[str] = Field(
    ["http://localhost:3000"],  # Dev default
    env="CORS_ORIGINS",
    description="Allowed CORS origins (JSON array)"
)

@validator("cors_origins", pre=True)
def parse_cors_origins(cls, v):
    if isinstance(v, str):
        return json.loads(v)
    return v
```

### Rate Limiting Review

#### Tiered Rate Limits

Update `src/eva_api/middleware/auth.py`:

```python
class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware with tiered limits."""
    
    TIER_LIMITS = {
        "free": "100/hour",
        "basic": "1000/hour",
        "pro": "10000/hour",
        "enterprise": "unlimited"
    }
    
    async def dispatch(self, request: Request, call_next):
        # Get user tier from JWT claims
        auth_header = request.headers.get("Authorization")
        if auth_header:
            claims = await verify_jwt_token(auth_header.replace("Bearer ", ""))
            tier = claims.get("tier", "free")
            limit = self.TIER_LIMITS.get(tier, "100/hour")
        else:
            limit = "50/hour"  # Anonymous
        
        # Apply limit
        limiter = request.app.state.limiter
        await limiter.apply(request, limit)
        
        return await call_next(request)
```

## Load Testing

### Locust Configuration

Update `load-tests/locustfile.py`:

```python
from locust import HttpUser, task, between, events
import jwt
import time

class EVAAPIUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Generate JWT token for authenticated requests."""
        self.token = self._generate_test_token()
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def _generate_test_token(self):
        """Generate test JWT token."""
        payload = {
            "sub": "test_user",
            "tenant_id": "test_tenant",
            "tier": "pro",
            "exp": int(time.time()) + 3600
        }
        return jwt.encode(payload, "test_secret", algorithm="HS256")
    
    @task(3)
    def list_spaces(self):
        """List spaces (common operation)."""
        self.client.get("/api/v1/spaces", headers=self.headers)
    
    @task(2)
    def get_space(self):
        """Get specific space."""
        self.client.get(
            "/api/v1/spaces/550e8400-e29b-41d4-a716-446655440000",
            headers=self.headers
        )
    
    @task(1)
    def create_space(self):
        """Create new space."""
        self.client.post(
            "/api/v1/spaces",
            json={
                "name": f"Test Space {time.time()}",
                "description": "Load test space"
            },
            headers=self.headers
        )
    
    @task(2)
    def graphql_query(self):
        """Execute GraphQL query."""
        self.client.post(
            "/graphql",
            json={
                "query": """
                    query {
                        spaces {
                            id
                            name
                            documentCount
                        }
                    }
                """
            },
            headers=self.headers
        )
```

### Run Load Tests

```bash
# Development baseline
locust -f load-tests/locustfile.py \
    --headless \
    --users 10 \
    --spawn-rate 1 \
    --run-time 5m \
    --host http://localhost:8000 \
    --html load-tests/report-dev-10users.html

# Production simulation
locust -f load-tests/locustfile.py \
    --headless \
    --users 100 \
    --spawn-rate 10 \
    --run-time 30m \
    --host https://api.eva-suite.ai \
    --html load-tests/report-prod-100users.html
```

### Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Response Time (p50) | < 200ms | < 500ms |
| Response Time (p95) | < 1s | < 3s |
| Response Time (p99) | < 2s | < 5s |
| Error Rate | < 0.1% | < 1% |
| Throughput | > 100 req/s | > 50 req/s |
| WebSocket Connections | > 1000 concurrent | > 500 concurrent |

## Health Checks

### Enhanced Health Endpoint

Update `src/eva_api/routers/health.py`:

```python
@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    cosmos: CosmosDBService = Depends(get_cosmos_service),
    redis: RedisService = Depends(get_redis_service),
) -> DetailedHealthResponse:
    """Detailed health check for monitoring."""
    checks = {
        "api": "healthy",
        "cosmos_db": "unknown",
        "redis": "unknown",
        "blob_storage": "unknown",
        "webhook_service": "unknown"
    }
    
    # Check Cosmos DB
    try:
        await cosmos.database.read()
        checks["cosmos_db"] = "healthy"
    except Exception as e:
        checks["cosmos_db"] = f"unhealthy: {str(e)}"
    
    # Check Redis
    try:
        await redis.redis_client.ping()
        checks["redis"] = "healthy"
    except Exception as e:
        checks["redis"] = f"unhealthy: {str(e)}"
    
    # Check Blob Storage
    try:
        blob_service = get_blob_service()
        await blob_service.list_containers(max_results=1)
        checks["blob_storage"] = "healthy"
    except Exception as e:
        checks["blob_storage"] = f"unhealthy: {str(e)}"
    
    # Check Webhook Service
    webhook_service = get_webhook_service()
    if webhook_service and webhook_service._running:
        checks["webhook_service"] = "healthy"
    else:
        checks["webhook_service"] = "unhealthy: not running"
    
    overall_status = "healthy" if all(
        v == "healthy" for v in checks.values()
    ) else "degraded"
    
    return DetailedHealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        checks=checks
    )
```

## Monitoring Dashboard

### Azure Dashboard Configuration

Create `azure/dashboards/eva-api-production.json`:

```json
{
  "lenses": {
    "0": {
      "order": 0,
      "parts": {
        "0": {
          "position": {"x": 0, "y": 0, "colSpan": 6, "rowSpan": 4},
          "metadata": {
            "type": "Extension/Microsoft_Azure_Monitoring/PartType/MetricsChartPart",
            "settings": {
              "title": "API Response Time",
              "metrics": [
                {
                  "resourceId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Web/sites/eva-api-prod",
                  "name": "ResponseTime",
                  "aggregationType": "Percentile",
                  "percentiles": [50, 95, 99]
                }
              ]
            }
          }
        },
        "1": {
          "position": {"x": 6, "y": 0, "colSpan": 6, "rowSpan": 4},
          "metadata": {
            "type": "Extension/Microsoft_Azure_Monitoring/PartType/MetricsChartPart",
            "settings": {
              "title": "Request Rate",
              "metrics": [
                {
                  "resourceId": "/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.Web/sites/eva-api-prod",
                  "name": "Requests",
                  "aggregationType": "Count"
                }
              ]
            }
          }
        }
      }
    }
  }
}
```

## Deployment Checklist

### Pre-Deployment

- [ ] Update version number in `config.py`
- [ ] Review and update `.env.production`
- [ ] Run full test suite: `pytest tests/ -v`
- [ ] Run security scan: `bandit -r src/`
- [ ] Update Terraform variables
- [ ] Review CORS origins
- [ ] Verify rate limits
- [ ] Check API key rotation schedule

### Deployment

- [ ] Apply Terraform changes: `terraform apply -var-file=environments/prod/terraform.tfvars`
- [ ] Deploy application code
- [ ] Run database migrations (if any)
- [ ] Verify Cosmos DB containers created
- [ ] Test Redis connectivity
- [ ] Verify Application Insights logging
- [ ] Check webhook service started
- [ ] Test health endpoints

### Post-Deployment

- [ ] Run smoke tests
- [ ] Monitor Application Insights for errors
- [ ] Check response times < targets
- [ ] Verify WebSocket connections working
- [ ] Test webhook delivery
- [ ] Monitor DLQ for failed webhooks
- [ ] Check GraphQL subscriptions
- [ ] Review first 1000 requests

### Rollback Plan

```bash
# Revert to previous version
terraform apply -var="app_version=1.0.0"

# Or manual rollback in Azure Portal:
# App Service > Deployment Center > Deployment History > Redeploy
```

## Monitoring Alerts

### Azure Monitor Alert Rules

```bash
# Create alert rules
az monitor metrics alert create \
  --name "eva-api-high-error-rate" \
  --resource-group eva-api-prod-rg \
  --scopes "/subscriptions/{sub}/resourceGroups/eva-api-prod-rg/providers/Microsoft.Web/sites/eva-api-prod" \
  --condition "avg Http5xx > 10" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-ids "/subscriptions/{sub}/resourceGroups/eva-api-prod-rg/providers/microsoft.insights/actionGroups/eva-ops-team"

az monitor metrics alert create \
  --name "eva-api-high-response-time" \
  --resource-group eva-api-prod-rg \
  --scopes "/subscriptions/{sub}/resourceGroups/eva-api-prod-rg/providers/Microsoft.Web/sites/eva-api-prod" \
  --condition "avg ResponseTime > 3000" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action-group-ids "/subscriptions/{sub}/resourceGroups/eva-api-prod-rg/providers/microsoft.insights/actionGroups/eva-ops-team"
```

## Files to Create/Update

### New Files
- `.env.production` - Production environment variables
- `src/eva_api/services/telemetry_service.py` - Application Insights integration
- `scripts/rotate_api_keys.py` - API key rotation script
- `azure/dashboards/eva-api-production.json` - Monitoring dashboard
- `docs/PRODUCTION-RUNBOOK.md` - Operations runbook

### Update Files
- `src/eva_api/services/redis_service.py` - Add Pub/Sub methods
- `src/eva_api/graphql/resolvers.py` - Replace polling with Redis
- `src/eva_api/routers/spaces.py` - Add Redis event publishing
- `src/eva_api/routers/documents.py` - Add Redis event publishing
- `src/eva_api/routers/queries.py` - Add Redis event publishing
- `src/eva_api/config.py` - Add Application Insights settings
- `src/eva_api/main.py` - Initialize telemetry
- `load-tests/locustfile.py` - Enhanced load testing
- `terraform/environments/prod/terraform.tfvars` - Production config
- `requirements.txt` - Add opencensus-ext-azure

## Status: READY FOR REVIEW

All documentation and implementation plans created. Next steps:
1. Review configuration values
2. Apply changes systematically
3. Test in staging environment
4. Deploy to production
