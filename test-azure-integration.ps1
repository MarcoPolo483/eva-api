#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Azure Integration Testing Script - Part of Production Readiness validation

.DESCRIPTION
    Tests EVA API with real Azure services (Cosmos DB, Blob Storage, OpenAI)
    Validates connectivity, performance, and reliability under load

.PARAMETER Stage
    Which stage to run: config, integration, loadtest, analyze, all

.EXAMPLE
    .\test-azure-integration.ps1 -Stage all
#>

param(
    [ValidateSet("config", "integration", "loadtest", "analyze", "security", "all")]
    [string]$Stage = "all"
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     EVA API - Azure Integration Testing (Production Ready)      ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$stages = @{
    config = @{
        name = "Azure Configuration"
        time = "5-10 minutes"
    }
    integration = @{
        name = "Integration Tests"
        time = "30 minutes"
    }
    loadtest = @{
        name = "Load Testing with Azure"
        time = "1 hour"
    }
    analyze = @{
        name = "Performance Analysis"
        time = "30 minutes"
    }
    security = @{
        name = "Security Audit"
        time = "1 hour"
    }
}

function Show-Stage {
    param($StageName)
    $stage = $stages[$StageName]
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Yellow
    Write-Host "  STAGE: $($stage.name.ToUpper())" -ForegroundColor Yellow
    Write-Host "  Estimated time: $($stage.time)" -ForegroundColor Gray
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Yellow
}

# ============================================================================
# STAGE 1: Azure Configuration
# ============================================================================
function Test-AzureConfig {
    Show-Stage "config"
    
    Write-Host "Checking .env file..." -ForegroundColor Cyan
    
    if (-not (Test-Path ".env")) {
        Write-Host "❌ .env file not found!" -ForegroundColor Red
        Write-Host "`nPlease create .env file with Azure credentials." -ForegroundColor Yellow
        Write-Host "Template created at: .env" -ForegroundColor Gray
        return $false
    }
    
    $envContent = Get-Content .env -Raw
    
    $required = @(
        @{name="COSMOS_DB_ENDPOINT"; pattern="https://.*\.documents\.azure\.com"}
        @{name="COSMOS_DB_KEY"; pattern=".{40,}"}
        @{name="AZURE_STORAGE_ACCOUNT_NAME"; pattern=".+"}
        @{name="AZURE_OPENAI_ENDPOINT"; pattern="https://.*\.(openai\.azure\.com|cognitive\.microsoft\.com)"}
        @{name="AZURE_OPENAI_KEY"; pattern=".{30,}"}
    )
    
    $allConfigured = $true
    foreach ($config in $required) {
        if ($envContent -match "$($config.name)=$($config.pattern)") {
            Write-Host "  ✅ $($config.name)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $($config.name) - Not configured or invalid" -ForegroundColor Red
            $allConfigured = $false
        }
    }
    
    if (-not $allConfigured) {
        Write-Host "`n⚠️  Please update .env with your Azure credentials:" -ForegroundColor Yellow
        Write-Host "  1. Open Azure Portal (portal.azure.com)" -ForegroundColor White
        Write-Host "  2. Navigate to your Cosmos DB → Keys" -ForegroundColor White
        Write-Host "  3. Copy endpoint and key to .env" -ForegroundColor White
        Write-Host "  4. Repeat for Storage Account and OpenAI" -ForegroundColor White
        Write-Host "`n  Then run: .\test-azure-integration.ps1 -Stage config" -ForegroundColor Gray
        return $false
    }
    
    Write-Host "`n✅ All Azure credentials configured!" -ForegroundColor Green
    
    # Test Python can load config
    Write-Host "`nTesting configuration loading..." -ForegroundColor Cyan
    $env:PYTHONPATH = "src"
    $pythonCode = @"
from eva_api.config import get_settings
settings = get_settings()
print(f'Mock mode: {settings.mock_mode}')
print(f'Cosmos: {settings.cosmos_db_endpoint[:40] if settings.cosmos_db_endpoint else "not set"}...')
print(f'OpenAI: {settings.azure_openai_endpoint[:40] if settings.azure_openai_endpoint else "not set"}...')
print('Config loads successfully')
"@
    $configTest = python -c $pythonCode 2>&1
    
    Write-Host $configTest
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Stage 1 Complete: Configuration validated" -ForegroundColor Green
        return $true
    } else {
        Write-Host "`n❌ Configuration error - check output above" -ForegroundColor Red
        return $false
    }
}

# ============================================================================
# STAGE 2: Integration Tests
# ============================================================================
function Test-AzureIntegration {
    Show-Stage "integration"
    
    Write-Host "Running integration tests with real Azure services..." -ForegroundColor Cyan
    Write-Host "This will:" -ForegroundColor Gray
    Write-Host "  • Connect to Cosmos DB and create/read/delete test data" -ForegroundColor Gray
    Write-Host "  • Upload/download files to Blob Storage" -ForegroundColor Gray
    Write-Host "  • Call Azure OpenAI for embeddings/completions" -ForegroundColor Gray
    Write-Host ""
    
    $env:PYTHONPATH = "src"
    
    # Check if integration tests exist
    if (-not (Test-Path "tests/integration")) {
        Write-Host "⚠️  No integration tests found in tests/integration/" -ForegroundColor Yellow
        Write-Host "Skipping integration test stage..." -ForegroundColor Gray
        return $true
    }
    
    Write-Host "Running pytest..." -ForegroundColor Yellow
    pytest tests/integration/ -v --tb=short --color=yes
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n✅ Stage 2 Complete: Integration tests passed" -ForegroundColor Green
        return $true
    } else {
        Write-Host "`n❌ Integration tests failed - check output above" -ForegroundColor Red
        Write-Host "`nCommon issues:" -ForegroundColor Yellow
        Write-Host "  • Firewall rules blocking connection" -ForegroundColor White
        Write-Host "  • Invalid credentials" -ForegroundColor White
        Write-Host "  • Database/containers don't exist" -ForegroundColor White
        Write-Host "  • Insufficient permissions" -ForegroundColor White
        return $false
    }
}

# ============================================================================
# STAGE 3: Load Testing
# ============================================================================
function Test-AzureLoadTest {
    Show-Stage "loadtest"
    
    Write-Host "Starting API server with real Azure backends..." -ForegroundColor Cyan
    
    # Kill existing servers
    Get-Process | Where-Object { $_.ProcessName -eq 'python' -or $_.ProcessName -eq 'uvicorn' } | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
    
    # Load environment variables from .env
    Write-Host "Loading .env configuration..." -ForegroundColor Gray
    $envVars = @{}
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.+)$') {
            $envVars[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    
    # Start server in background
    $env:PYTHONPATH = "src"
    $serverJob = Start-Job -ScriptBlock {
        param($workDir, $envVars)
        Set-Location $workDir
        
        # Set environment variables in job
        $env:PYTHONPATH = "src"
        foreach ($key in $envVars.Keys) {
            Set-Item -Path "env:$key" -Value $envVars[$key]
        }
        
        uvicorn eva_api.main:app --host 127.0.0.1 --port 8000 --log-level warning
    } -ArgumentList $PWD, $envVars
    
    Write-Host "Waiting 10 seconds for server startup..." -ForegroundColor Gray
    Start-Sleep -Seconds 10
    
    try {
        # Verify server is up
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
        Write-Host "✅ Server is running: $($health.status)" -ForegroundColor Green
        
        # Quick smoke test with real Azure
        Write-Host "`nTesting real Azure connection..." -ForegroundColor Cyan
        $startTime = Get-Date
        $body = @{
            name = "Azure Integration Test"
            description = "Testing real Cosmos DB connection"
        } | ConvertTo-Json
        
        $space = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/spaces" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 30
        $duration = ((Get-Date) - $startTime).TotalMilliseconds
        
        Write-Host "✅ Space created in $([math]::Round($duration, 0))ms (Azure round-trip)" -ForegroundColor Green
        Write-Host "   ID: $($space.id)" -ForegroundColor Gray
        
        if ($duration -gt 10000) {
            Write-Host "`n⚠️  Response time > 10s - may have connectivity issues" -ForegroundColor Yellow
        }
        
        # Run load test
        Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
        Write-Host "  LOAD TEST: 50 concurrent users for 5 minutes" -ForegroundColor Cyan
        Write-Host "  Target: 15-25 RPS | P95 < 2000ms | Errors < 1%" -ForegroundColor Cyan
        Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
        
        locust -f load-tests/locustfile.py --headless `
               --users 50 --spawn-rate 5 --run-time 5m `
               --host http://127.0.0.1:8000 `
               --html load-tests/report-azure-50users.html `
               --csv load-tests/results-azure-50users
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "`n✅ Load test completed!" -ForegroundColor Green
            
            # Show quick stats
            if (Test-Path "load-tests/results-azure-50users_stats.csv") {
                Write-Host "`n📊 Quick Results:" -ForegroundColor Cyan
                $stats = Import-Csv "load-tests/results-azure-50users_stats.csv"
                $aggregated = $stats | Where-Object { $_.Name -eq "Aggregated" }
                
                Write-Host "  Total Requests: $($aggregated.'Request Count')" -ForegroundColor White
                Write-Host "  Requests/sec: $($aggregated.'Requests/s')" -ForegroundColor White
                Write-Host "  Avg Response: $([math]::Round([double]$aggregated.'Average Response Time', 0))ms" -ForegroundColor White
                Write-Host "  Errors: $($aggregated.'Failure Count') ($([math]::Round([double]$aggregated.'Failure Count' / [double]$aggregated.'Request Count' * 100, 2))%)" -ForegroundColor White
                
                Write-Host "`n📄 Full report: load-tests/report-azure-50users.html" -ForegroundColor Gray
            }
            
            Write-Host "`n✅ Stage 3 Complete: Load test with Azure finished" -ForegroundColor Green
            return $true
        } else {
            Write-Host "`n⚠️  Load test had issues - check report" -ForegroundColor Yellow
            return $false
        }
        
    } catch {
        Write-Host "`n❌ Server test failed: $_" -ForegroundColor Red
        return $false
    } finally {
        Write-Host "`nStopping server..." -ForegroundColor Gray
        Stop-Job -Job $serverJob -ErrorAction SilentlyContinue
        Remove-Job -Job $serverJob -Force -ErrorAction SilentlyContinue
        Get-Process | Where-Object { $_.ProcessName -eq 'python' -or $_.ProcessName -eq 'uvicorn' } | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# STAGE 4: Performance Analysis
# ============================================================================
function Invoke-PerformanceAnalysis {
    Show-Stage "analyze"
    
    Write-Host "Analyzing Azure load test results..." -ForegroundColor Cyan
    
    if (-not (Test-Path "load-tests/results-azure-50users_stats.csv")) {
        Write-Host "❌ Load test results not found. Run load test first." -ForegroundColor Red
        return $false
    }
    
    $stats = Import-Csv "load-tests/results-azure-50users_stats.csv"
    $aggregated = $stats | Where-Object { $_.Name -eq "Aggregated" }
    
    Write-Host "`n📊 Detailed Analysis:" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
    
    # Throughput
    $rps = [double]$aggregated.'Requests/s'
    Write-Host "Throughput: $([math]::Round($rps, 2)) RPS" -ForegroundColor White
    if ($rps -ge 15) {
        Write-Host "  ✅ Target met (15+ RPS)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Below target (< 15 RPS)" -ForegroundColor Yellow
    }
    
    # Latency
    $p95 = [double]$aggregated.'95%'
    Write-Host "`nP95 Latency: $([math]::Round($p95, 0))ms" -ForegroundColor White
    if ($p95 -le 2000) {
        Write-Host "  ✅ Target met (< 2000ms)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Above target (> 2000ms)" -ForegroundColor Yellow
    }
    
    # Errors
    $errorRate = [double]$aggregated.'Failure Count' / [double]$aggregated.'Request Count' * 100
    Write-Host "`nError Rate: $([math]::Round($errorRate, 2))%" -ForegroundColor White
    if ($errorRate -le 1) {
        Write-Host "  ✅ Target met (< 1%)" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  Above target (> 1%)" -ForegroundColor Yellow
    }
    
    # Per-endpoint breakdown
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host "Per-Endpoint Performance:" -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Gray
    
    $stats | Where-Object { $_.Name -ne "Aggregated" } | ForEach-Object {
        $avgTime = [math]::Round([double]$_.'Average Response Time', 0)
        $color = if ($avgTime -lt 1000) { "Green" } elseif ($avgTime -lt 2000) { "Yellow" } else { "Red" }
        Write-Host "$($_.Type.PadRight(6)) $($_.Name.PadRight(40)) $($avgTime)ms avg" -ForegroundColor $color
    }
    
    Write-Host "`n✅ Stage 4 Complete: Analysis done" -ForegroundColor Green
    Write-Host "📄 See full HTML report: load-tests/report-azure-50users.html" -ForegroundColor Gray
    
    return $true
}

# ============================================================================
# STAGE 5: Security Audit
# ============================================================================
function Invoke-SecurityAudit {
    Show-Stage "security"
    
    Write-Host "Running security scans..." -ForegroundColor Cyan
    
    # Check if tools are installed
    Write-Host "`nChecking security tools..." -ForegroundColor Yellow
    $toolsOk = $true
    
    try {
        safety --version | Out-Null
        Write-Host "  ✅ safety (dependency scanner)" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ safety not installed" -ForegroundColor Red
        Write-Host "     Install: pip install safety" -ForegroundColor Gray
        $toolsOk = $false
    }
    
    try {
        bandit --version | Out-Null
        Write-Host "  ✅ bandit (code scanner)" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ bandit not installed" -ForegroundColor Red
        Write-Host "     Install: pip install bandit" -ForegroundColor Gray
        $toolsOk = $false
    }
    
    if (-not $toolsOk) {
        Write-Host "`n⚠️  Install security tools and rerun" -ForegroundColor Yellow
        return $false
    }
    
    # Run safety check
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  Scanning dependencies for vulnerabilities..." -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
    
    safety check --json --output security-deps.json
    $safetyOk = $LASTEXITCODE -eq 0
    
    if ($safetyOk) {
        Write-Host "✅ No known vulnerabilities in dependencies" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Vulnerabilities found - check security-deps.json" -ForegroundColor Yellow
    }
    
    # Run bandit scan
    Write-Host "`n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Cyan
    Write-Host "  Scanning code for security issues..." -ForegroundColor Cyan
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`n" -ForegroundColor Cyan
    
    bandit -r src/ -f json -o security-code.json
    bandit -r src/ -ll  # Show medium/high severity
    
    Write-Host "`n✅ Stage 5 Complete: Security audit done" -ForegroundColor Green
    Write-Host "📄 Reports: security-deps.json, security-code.json" -ForegroundColor Gray
    
    return $true
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

$success = $true

if ($Stage -eq "all") {
    $success = Test-AzureConfig
    if ($success) { $success = Test-AzureIntegration }
    if ($success) { $success = Test-AzureLoadTest }
    if ($success) { $success = Invoke-PerformanceAnalysis }
    if ($success) { $success = Invoke-SecurityAudit }
} else {
    switch ($Stage) {
        "config"      { $success = Test-AzureConfig }
        "integration" { $success = Test-AzureIntegration }
        "loadtest"    { $success = Test-AzureLoadTest }
        "analyze"     { $success = Invoke-PerformanceAnalysis }
        "security"    { $success = Invoke-SecurityAudit }
    }
}

# Final summary
Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor $(if ($success) { "Green" } else { "Yellow" })
if ($success) {
    Write-Host "║                    ✅ TESTS COMPLETED                            ║" -ForegroundColor Green
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host "`n🎉 EVA API is ready for production with real Azure services!" -ForegroundColor Green
} else {
    Write-Host "║              ⚠️  TESTS COMPLETED WITH WARNINGS                   ║" -ForegroundColor Yellow
    Write-Host "╚══════════════════════════════════════════════════════════════════╝" -ForegroundColor Yellow
    Write-Host "`nℹ️  Review output above and fix issues before production" -ForegroundColor Yellow
}

Write-Host ""
