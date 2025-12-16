# EVA API Platform

**Enterprise-grade API gateway for EVA Suite**

[![CI Status](https://github.com/MarcoPolo483/eva-api/workflows/CI/badge.svg)](https://github.com/MarcoPolo483/eva-api/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

---

## 🎯 Overview

EVA API Platform provides a single entry point for all EVA Suite services with:

- **REST APIs** with OpenAPI 3.1 specification
- **GraphQL** endpoint with Apollo Server (Phase 3)
- **Webhooks** for real-time event notifications (Phase 3)
- **API Gateway** for routing, authentication, rate limiting
- **SDKs** for Python, Node.js, .NET (Phase 4)
- **Developer Portal** with interactive docs (Phase 5)

**Current Phase**: Phase 1 - Foundation ✅  
**Status**: Ready for Testing

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker (optional, for containerized deployment)
- Azure account (for production deployment)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MarcoPolo483/eva-api.git
   cd eva-api
   ```

2. **Create virtual environment**:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**:
   ```powershell
   # Copy example .env file
   Copy-Item .env.example .env
   # Edit .env with your Azure credentials
   ```

5. **Run the application**:
   ```powershell
   python -m eva_api.main
   ```

6. **Open your browser**:
   - API Docs (Swagger): http://localhost:8000/docs
   - API Docs (ReDoc): http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

---

## 📦 Project Structure

```
eva-api/
├── src/
│   └── eva_api/
│       ├── __init__.py
│       ├── main.py              # FastAPI application entry point
│       ├── config.py            # Application settings
│       ├── dependencies.py      # Dependency injection
│       ├── middleware/
│       │   ├── __init__.py
│       │   └── auth.py          # Authentication & rate limiting
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── health.py        # Health check endpoints
│       │   └── auth.py          # API key management
│       ├── models/
│       │   ├── __init__.py
│       │   ├── base.py          # Base Pydantic models
│       │   └── auth.py          # Authentication models
│       └── services/
│           ├── __init__.py
│           ├── auth_service.py  # Azure AD integration
│           └── api_key_service.py  # API key management
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── test_health.py
│   ├── test_main.py
│   ├── test_config.py
│   ├── test_dependencies.py
│   ├── test_middleware.py
│   ├── test_auth_service.py
│   ├── test_api_key_service.py
│   └── test_auth_router.py
├── docker/
│   ├── Dockerfile               # Multi-stage Docker build
│   └── docker-compose.yml       # Local development setup
├── .github/
│   └── workflows/
│       ├── ci.yml               # CI pipeline
│       └── cd.yml               # CD pipeline
├── docs/
│   └── SPECIFICATION.md         # Complete specification (723 lines)
├── requirements.txt             # Production dependencies
├── requirements-dev.txt         # Development dependencies
├── pyproject.toml               # Project metadata & tools
├── .dockerignore
├── .gitignore
├── ACTION-PLAN.md               # Implementation roadmap
└── README.md                    # This file
```

---

## 🔧 Development

### Running Tests

```powershell
# Run all tests with coverage
pytest --cov=eva_api --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v

# Run tests in watch mode (requires pytest-watch)
ptw
```

### Code Quality

```powershell
# Lint with ruff
ruff check src/ tests/

# Format code with black
black src/ tests/

# Type checking with mypy
mypy src/eva_api

# Run all quality checks
ruff check src/ tests/ && black src/ tests/ --check && mypy src/eva_api
```

### Docker Development

```powershell
# Build Docker image
docker build -f docker/Dockerfile -t eva-api:latest .

# Run with Docker Compose
docker-compose -f docker/docker-compose.yml up

# Stop services
docker-compose -f docker/docker-compose.yml down

# View logs
docker-compose -f docker/docker-compose.yml logs -f api
```

---

## 📚 API Documentation

### Health Endpoints

#### GET /health
Basic health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2025-12-07T19:00:00Z"
}
```

#### GET /health/ready
Detailed readiness check with component status.

**Response**:
```json
{
  "ready": true,
  "checks": {
    "api": "ok",
    "database": "not_configured",
    "redis": "not_configured"
  },
  "timestamp": "2025-12-07T19:00:00Z"
}
```

### Authentication Endpoints

#### POST /auth/api-keys
Create a new API key (requires JWT authentication).

**Request**:
```json
{
  "name": "My API Key",
  "scopes": ["spaces:read", "spaces:write"],
  "expires_at": "2026-12-07T00:00:00Z"
}
```

**Response**:
```json
{
  "id": "key_abc123",
  "key": "sk_live_xyz789...",
  "name": "My API Key",
  "scopes": ["spaces:read", "spaces:write"],
  "created_at": "2025-12-07T19:00:00Z",
  "expires_at": "2026-12-07T00:00:00Z"
}
```

#### GET /auth/api-keys
List all API keys for authenticated tenant.

#### GET /auth/api-keys/{key_id}
Get information about a specific API key.

#### DELETE /auth/api-keys/{key_id}
Revoke an API key.

---

## 🔐 Authentication

### API Key Authentication

Include API key in `X-API-Key` header:

```bash
curl -H "X-API-Key: sk_live_abc123..." https://api.eva.ai/api/v1/spaces
```

### JWT Authentication

Include Bearer token in `Authorization` header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." https://api.eva.ai/auth/api-keys
```

---

## 🌍 Environment Variables

Create a `.env` file in the project root:

```bash
# Application
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=INFO

# Azure AD B2C (Citizen Authentication)
AZURE_AD_B2C_TENANT_ID=your-tenant-id
AZURE_AD_B2C_CLIENT_ID=your-client-id
AZURE_AD_B2C_CLIENT_SECRET=your-client-secret
AZURE_AD_B2C_AUTHORITY=https://your-tenant.b2clogin.com/your-tenant/B2C_1_signin

# Azure Entra ID (Employee Authentication)
AZURE_ENTRA_TENANT_ID=your-tenant-id
AZURE_ENTRA_CLIENT_ID=your-client-id
AZURE_ENTRA_CLIENT_SECRET=your-client-secret

# Azure Cosmos DB
COSMOS_DB_ENDPOINT=https://your-account.documents.azure.com:443/
COSMOS_DB_KEY=your-cosmos-key
COSMOS_DB_DATABASE=eva_api

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_DEFAULT=60
```

---

## 📊 Phase 1 Status (Current)

### ✅ Completed

- [x] Project structure and Python package
- [x] FastAPI application with CORS & middleware
- [x] Pydantic settings with environment variables
- [x] Health check endpoints (`/health`, `/health/ready`)
- [x] Authentication middleware (request ID, timing)
- [x] Rate limiting middleware (placeholder)
- [x] Azure AD service integration (placeholder)
- [x] API key service (placeholder)
- [x] API key management routes
- [x] Dependency injection
- [x] Docker configuration (Dockerfile, docker-compose.yml)
- [x] CI/CD pipelines (GitHub Actions)
- [x] Comprehensive test suite (80%+ coverage)
- [x] OpenAPI spec generation
- [x] Documentation

### 🚧 Pending (Phase 1.5)

- [ ] Full Azure AD B2C + Entra ID integration
- [ ] JWT signature verification
- [ ] Cosmos DB connectivity
- [ ] API key storage in Cosmos DB
- [ ] API key verification logic
- [ ] Audit logging

### 📅 Upcoming Phases

- **Phase 2** (Week 3-4): REST API - Spaces, Documents, Queries
- **Phase 3** (Week 5-6): GraphQL + Webhooks
- **Phase 4** (Week 7-8): SDKs (Python, Node.js, .NET, CLI)
- **Phase 5** (Week 9-10): Developer Portal
- **Phase 6** (Week 11-12): Production Readiness

---

## 🧪 Testing

### Run Tests

```powershell
# All tests with coverage report
pytest --cov=eva_api --cov-report=html --cov-report=term-missing

# Open coverage report
Start-Process htmlcov/index.html
```

### Test Coverage

Current coverage: **80%+** (Phase 1 target)

Target: **100%** (Phase 2+)

---

## 🚢 Deployment

### Azure App Service

```bash
# Build and push to Azure Container Registry
az acr build --registry <your-acr> --image eva-api:latest .

# Deploy to App Service
az webapp create --resource-group <rg> --plan <plan> --name eva-api --deployment-container-image-name <your-acr>.azurecr.io/eva-api:latest
```

### GitHub Actions

CI/CD pipelines are configured in `.github/workflows/`:

- **CI**: Runs on every push/PR - tests, linting, security scans, Docker build
- **CD**: Deploys to staging (on merge to master) and production (on version tags)

---

## 📖 Additional Documentation

- **[SPECIFICATION.md](docs/SPECIFICATION.md)** - Complete 723-line specification
- **[ACTION-PLAN.md](ACTION-PLAN.md)** - Detailed implementation roadmap
- **[OpenAPI Spec](http://localhost:8000/openapi.json)** - Interactive API documentation
- **[Swagger UI](http://localhost:8000/docs)** - Try the API
- **[ReDoc](http://localhost:8000/redoc)** - Alternative API docs

---

## 🤝 Contributing

This is a proprietary project for EVA Suite. For internal contributors:

1. Read the specification: `docs/SPECIFICATION.md`
2. Follow the Three Concepts Pattern (Context Engineering, Workspace Management, Directory Mapping)
3. Ensure 100% test coverage for new code
4. Run all quality checks before committing
5. Update documentation as needed

---

## 📝 License

Proprietary - EVA Suite © 2025

---

## 📞 Support

- **GitHub Issues**: https://github.com/MarcoPolo483/eva-api/issues
- **Documentation**: https://developers.eva.ai (Phase 5)
- **Team**: POD-F (P04-LIB + P15-DVM)

---

## 🎉 Quick Commands Reference

```powershell
# Development
python -m eva_api.main                    # Run API server
pytest                                    # Run tests
ruff check src/ tests/                   # Lint code
mypy src/eva_api                         # Type check

# Docker
docker build -f docker/Dockerfile -t eva-api:latest .   # Build image
docker-compose -f docker/docker-compose.yml up          # Start services
docker-compose -f docker/docker-compose.yml down        # Stop services

# Quality
pytest --cov=eva_api --cov-report=html   # Test with coverage
ruff check --fix src/ tests/             # Auto-fix lint issues
black src/ tests/                        # Format code
```

---

**Built with ❤️ for EVA Suite**

<!-- Phase 3 enforcement system test -->
