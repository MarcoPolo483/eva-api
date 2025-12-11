#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run medium load test with mock mode enabled for fast API testing

.DESCRIPTION
    Starts API server with EVA_MOCK_MODE=true, runs 100-user load test,
    validates performance improvements, and generates comparison report

.EXAMPLE
    .\run-mock-load-test.ps1
#>

param(
    [int]$Users = 100,
    [int]$SpawnRate = 10,
    [string]$Duration = "5m"
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     EVA API - Mock Mode Load Test ($Users users)               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if API server is already running
try {
    $null = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "⚠️  API server already running on port 8000" -ForegroundColor Yellow
    Write-Host "   Assuming it's in mock mode. If not, stop it and rerun this script.`n" -ForegroundColor Yellow
    $serverStarted = $false
} catch {
    Write-Host "🚀 Starting API server in MOCK MODE..." -ForegroundColor Green
    
    # Start server in new window with mock mode
    $serverProcess = Start-Process pwsh -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$PSScriptRoot'; `$env:PYTHONPATH='src'; `$env:EVA_MOCK_MODE='true'; `$env:EVA_AZURE_TIMEOUT='5'; Write-Host '🎭 Mock Mode Enabled - Fast Responses' -ForegroundColor Magenta; uvicorn eva_api.main:app --host 127.0.0.1 --port 8000 --log-level warning"
    ) -WindowStyle Minimized -PassThru
    
    Write-Host "   Server PID: $($serverProcess.Id)" -ForegroundColor Gray
    Write-Host "   Waiting 5 seconds for startup...`n" -ForegroundColor Gray
    Start-Sleep -Seconds 5
    
    # Verify server is responding
    try {
        $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
        Write-Host "✅ Server ready: $($response.status)`n" -ForegroundColor Green
    } catch {
        Write-Host "❌ Server failed to start!" -ForegroundColor Red
        exit 1
    }
    
    $serverStarted = $true
}

# Run load test
Write-Host "🔥 Running Locust load test..." -ForegroundColor Yellow
Write-Host "   Users: $Users concurrent" -ForegroundColor Gray
Write-Host "   Spawn rate: $SpawnRate users/sec" -ForegroundColor Gray
Write-Host "   Duration: $Duration`n" -ForegroundColor Gray

$locustCmd = "locust -f load-tests/locustfile.py --headless --users $Users --spawn-rate $SpawnRate --run-time $Duration --host http://127.0.0.1:8000 --html load-tests/report-mock-medium.html --csv load-tests/results-mock-medium"

try {
    Invoke-Expression $locustCmd
    $testSuccess = $LASTEXITCODE -eq 0
} catch {
    Write-Host "`n❌ Load test failed!" -ForegroundColor Red
    $testSuccess = $false
}

Write-Host ""

# Check SLA if test succeeded
if ($testSuccess) {
    Write-Host "✅ Load test completed - checking SLAs...`n" -ForegroundColor Green
    
    if (Test-Path "load-tests/results-mock-medium_stats.csv") {
        python load-tests/check_sla.py load-tests/results-mock-medium_stats.csv
        $slaPass = $LASTEXITCODE -eq 0
    } else {
        Write-Host "⚠️  Stats CSV not found, skipping SLA check" -ForegroundColor Yellow
        $slaPass = $false
    }
} else {
    Write-Host "⚠️  Skipping SLA check due to test failure`n" -ForegroundColor Yellow
    $slaPass = $false
}

# Generate comparison report
if (Test-Path "load-tests/results-mock-medium_stats.csv") {
    Write-Host "`n📊 Generating comparison report..." -ForegroundColor Cyan
    
    # Read mock results
    $mockStats = Import-Csv "load-tests/results-mock-medium_stats.csv"
    $mockAgg = $mockStats | Where-Object { $_.Name -eq "Aggregated" }
    
    # Read original results if available
    if (Test-Path "load-tests/results-medium_stats.csv") {
        $origStats = Import-Csv "load-tests/results-medium_stats.csv"
        $origAgg = $origStats | Where-Object { $_.Name -eq "Aggregated" }
        
        Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Yellow
        Write-Host "║                Performance Comparison Report                     ║" -ForegroundColor Yellow
        Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Yellow
        
        Write-Host "Metric                    Original         Mock Mode        Improvement" -ForegroundColor Cyan
        Write-Host "─────────────────────────────────────────────────────────────────────"
        
        # Requests
        $origReqs = [int]$origAgg.'Request Count'
        $mockReqs = [int]$mockAgg.'Request Count'
        $reqImprovement = (($mockReqs - $origReqs) / $origReqs * 100)
        Write-Host ("Total Requests            {0,7}          {1,7}          {2,6:F1}%" -f $origReqs, $mockReqs, $reqImprovement)
        
        # RPS
        $origRPS = [decimal]$origAgg.'Requests/s'
        $mockRPS = [decimal]$mockAgg.'Requests/s'
        $rpsImprovement = (($mockRPS - $origRPS) / $origRPS * 100)
        Write-Host ("Requests/sec              {0,7:F2}          {1,7:F2}          {2,6:F1}%" -f $origRPS, $mockRPS, $rpsImprovement)
        
        # Median latency
        $origP50 = [decimal]$origAgg.'Median Response Time'
        $mockP50 = [decimal]$mockAgg.'Median Response Time'
        $p50Improvement = (($origP50 - $mockP50) / $origP50 * 100)
        Write-Host ("Median Latency (ms)       {0,7:F0}          {1,7:F0}          {2,6:F1}%" -f $origP50, $mockP50, $p50Improvement)
        
        # Avg latency
        $origAvg = [decimal]$origAgg.'Average Response Time'
        $mockAvg = [decimal]$mockAgg.'Average Response Time'
        $avgImprovement = (($origAvg - $mockAvg) / $origAvg * 100)
        Write-Host ("Average Latency (ms)      {0,7:F0}          {1,7:F0}          {2,6:F1}%" -f $origAvg, $mockAvg, $avgImprovement)
        
        # Errors
        $origErrors = [int]$origAgg.'Failure Count'
        $mockErrors = [int]$mockAgg.'Failure Count'
        Write-Host ("Errors                    {0,7}          {1,7}          {2,6}" -f $origErrors, $mockErrors, $(if ($origErrors -gt 0) { "-$($origErrors - $mockErrors)" } else { "✅" }))
        
        Write-Host "─────────────────────────────────────────────────────────────────────`n"
        
        if ($rpsImprovement -gt 500) {
            Write-Host "🎉 EXCELLENT: {0:F0}x throughput improvement!" -ForegroundColor Green -f ($mockRPS / $origRPS)
        } elseif ($rpsImprovement -gt 200) {
            Write-Host "✅ GOOD: {0:F0}x throughput improvement" -ForegroundColor Green -f ($mockRPS / $origRPS)
        } else {
            Write-Host "⚠️  Improvement less than expected (target: 10x+)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n📊 Mock Mode Results:" -ForegroundColor Cyan
        Write-Host "   Total Requests: $($mockAgg.'Request Count')"
        Write-Host "   Requests/sec: $($mockAgg.'Requests/s')"
        Write-Host "   Median Latency: $($mockAgg.'Median Response Time')ms"
        Write-Host "   Average Latency: $($mockAgg.'Average Response Time')ms"
        Write-Host "   Errors: $($mockAgg.'Failure Count')"
    }
}

# Cleanup
if ($serverStarted -and $serverProcess) {
    Write-Host "`n🛑 Stopping test server..." -ForegroundColor Yellow
    Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "   Server stopped`n" -ForegroundColor Gray
}

# Summary
Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
if ($testSuccess -and $slaPass) {
    Write-Host "║  ✅ Test PASSED - Mock mode significantly improved performance  ║" -ForegroundColor Green
} elseif ($testSuccess) {
    Write-Host "║  ⚠️  Test completed but SLA violations detected                 ║" -ForegroundColor Yellow
} else {
    Write-Host "║  ❌ Test FAILED - Check logs above                              ║" -ForegroundColor Red
}
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📄 Reports generated:" -ForegroundColor Cyan
Write-Host "   • load-tests/report-mock-medium.html" -ForegroundColor Gray
Write-Host "   • load-tests/results-mock-medium_stats.csv`n" -ForegroundColor Gray

exit $(if ($testSuccess) { 0 } else { 1 })
