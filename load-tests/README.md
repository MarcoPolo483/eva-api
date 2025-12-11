# Load Testing for EVA API

Performance and load testing using Locust.

## 🎯 Test Scenarios

### 1. Mixed Workload (Default)
Simulates realistic API usage:
- **40%** Space operations (read-heavy)
- **30%** Document operations (balanced read/write)
- **20%** Query operations (write-heavy, AI processing)
- **10%** GraphQL operations

### 2. Health Check Baseline
Lightweight health endpoint testing for baseline performance measurement.

## 🚀 Running Tests

### Install Dependencies

```powershell
cd load-tests
pip install -r requirements.txt
```

### Set API Key

```powershell
$env:EVA_API_KEY = "your-api-key"
```

### Run Basic Load Test

```powershell
# Test against local dev server
locust -f locustfile.py --host http://localhost:8000

# Test against staging
locust -f locustfile.py --host https://eva-api-staging.azurewebsites.net

# Test against production
locust -f locustfile.py --host https://api.eva.ai
```

### Run Headless (CI/CD)

```powershell
# 100 users, 10 users/sec spawn rate, 5 minutes
locust -f locustfile.py \
    --host https://api.eva.ai \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --headless \
    --html report.html \
    --csv results
```

### Run Specific User Class

```powershell
# Only health checks
locust -f locustfile.py --host http://localhost:8000 HealthCheckUser

# Only API operations
locust -f locustfile.py --host http://localhost:8000 APIUser
```

## 📊 Test Targets

### Performance SLAs

| Metric | Target | Critical |
|--------|--------|----------|
| P50 Response Time | < 100ms | < 200ms |
| P95 Response Time | < 500ms | < 1000ms |
| P99 Response Time | < 1000ms | < 2000ms |
| Error Rate | < 0.1% | < 1% |
| RPS per instance | > 100 | > 50 |

### Load Profiles

#### Light Load (Development)
```powershell
locust -f locustfile.py --host http://localhost:8000 \
    --users 10 --spawn-rate 2 --run-time 2m --headless
```
- **Users**: 10 concurrent
- **Duration**: 2 minutes
- **Expected RPS**: 20-30
- **Purpose**: Local dev validation

#### Medium Load (Staging)
```powershell
locust -f locustfile.py --host https://eva-api-staging.azurewebsites.net \
    --users 100 --spawn-rate 10 --run-time 10m --headless
```
- **Users**: 100 concurrent
- **Duration**: 10 minutes
- **Expected RPS**: 150-200
- **Purpose**: Feature validation

#### Heavy Load (Production Simulation)
```powershell
locust -f locustfile.py --host https://api.eva.ai \
    --users 1000 --spawn-rate 50 --run-time 30m --headless
```
- **Users**: 1,000 concurrent
- **Duration**: 30 minutes
- **Expected RPS**: 800-1,200
- **Purpose**: Capacity planning

#### Stress Test (Breaking Point)
```powershell
locust -f locustfile.py --host https://api.eva.ai \
    --users 10000 --spawn-rate 100 --run-time 15m --headless
```
- **Users**: 10,000 concurrent
- **Duration**: 15 minutes
- **Expected RPS**: 5,000+
- **Purpose**: Find breaking point

## 📈 Analyzing Results

### Locust Web UI

When running without `--headless`, open http://localhost:8089 for:
- Real-time RPS and response time charts
- Error rate monitoring
- Request distribution
- User count control

### HTML Report

Generated with `--html report.html`:
```powershell
# Open in browser
Start-Process report.html
```

### CSV Data

Generated with `--csv results`:
- `results_stats.csv` - Aggregated statistics
- `results_stats_history.csv` - Time-series data
- `results_failures.csv` - Error details

### Key Metrics to Monitor

```powershell
# Example analysis with PowerShell
Import-Csv results_stats.csv | 
    Where-Object { $_.Type -eq 'GET' } |
    Sort-Object '50%' |
    Format-Table Name, 'Request Count', '50%', '95%', 'Average Response Time'
```

## 🔧 Advanced Scenarios

### Custom Task Weights

Edit `locustfile.py` to adjust workload distribution:

```python
class APIUser(HttpUser):
    tasks = {
        SpaceOperations: 60,    # Increase space ops
        DocumentOperations: 20, # Decrease docs
        QueryOperations: 10,    # Decrease queries
        GraphQLOperations: 10,  # Keep GraphQL same
    }
```

### Step Load Testing

```powershell
# Gradually increase load
locust -f locustfile.py --host https://api.eva.ai \
    --users 1000 \
    --spawn-rate 10 \
    --run-time 30m \
    --step-load \
    --step-users 100 \
    --step-time 5m
```

### Distributed Load Testing

```powershell
# Master node
locust -f locustfile.py --master --host https://api.eva.ai

# Worker nodes (run on multiple machines)
locust -f locustfile.py --worker --master-host=<master-ip>
```

## 📋 CI/CD Integration

### GitHub Actions Example

```yaml
name: Load Test

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM
  workflow_dispatch:

jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd load-tests
          pip install -r requirements.txt
      
      - name: Run load test
        env:
          EVA_API_KEY: ${{ secrets.EVA_API_KEY }}
        run: |
          cd load-tests
          locust -f locustfile.py \
            --host https://api.eva.ai \
            --users 100 \
            --spawn-rate 10 \
            --run-time 5m \
            --headless \
            --html report.html \
            --csv results
      
      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: load-test-results
          path: load-tests/report.html
      
      - name: Check SLA compliance
        run: |
          python load-tests/check_sla.py results_stats.csv
```

## 🎯 Test Coverage

### REST API Endpoints Tested
- ✅ `GET /api/v1/spaces` - List spaces
- ✅ `POST /api/v1/spaces` - Create space
- ✅ `GET /api/v1/spaces/{id}` - Get space
- ✅ `PATCH /api/v1/spaces/{id}` - Update space
- ✅ `GET /api/v1/spaces/{id}/documents` - List documents
- ✅ `POST /api/v1/spaces/{id}/documents` - Upload document
- ✅ `GET /api/v1/spaces/{id}/documents/{doc_id}` - Get document
- ✅ `GET /api/v1/spaces/{id}/documents/{doc_id}/download` - Download
- ✅ `POST /api/v1/spaces/{id}/queries` - Submit query
- ✅ `GET /api/v1/spaces/{id}/queries` - List queries
- ✅ `GET /health` - Health check
- ✅ `GET /metrics` - Metrics

### GraphQL Operations Tested
- ✅ Query: `spaces` - List spaces
- ✅ Mutation: `createSpace` - Create space

## ⚠️ Important Notes

1. **Rate Limiting**: Tests will hit rate limits. Adjust `wait_time` accordingly.
2. **Costs**: Query operations trigger Azure OpenAI calls ($$$). Monitor carefully.
3. **Cleanup**: Tests create data. Run cleanup scripts after testing.
4. **Production**: Always test staging first. Get approval before prod load tests.

## 🧹 Cleanup After Testing

```powershell
# Delete test spaces (PowerShell)
$apiKey = $env:EVA_API_KEY
$spaces = Invoke-RestMethod -Uri "https://api.eva.ai/api/v1/spaces?limit=1000" `
    -Headers @{ Authorization = "Bearer $apiKey" }

$spaces.items | 
    Where-Object { $_.name -like "*Load Test*" -or $_.name -like "*GraphQL Space*" } |
    ForEach-Object {
        Write-Host "Deleting space: $($_.name)"
        Invoke-RestMethod -Uri "https://api.eva.ai/api/v1/spaces/$($_.id)" `
            -Method DELETE `
            -Headers @{ Authorization = "Bearer $apiKey" }
    }
```

---

**Status**: NOT EXECUTED - REVIEW CAREFULLY  
**Last Updated**: 2025-12-07T22:00:00Z (2025-12-07 17:00:00 EST)
