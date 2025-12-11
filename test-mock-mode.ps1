#!/usr/bin/env pwsh
# Quick test to verify mock mode works

$ErrorActionPreference = "Stop"

Write-Host "`n🧪 EVA API Mock Mode Verification`n" -ForegroundColor Cyan

# Kill any existing servers
Get-Process | Where-Object { $_.ProcessName -eq 'python' -or $_.ProcessName -eq 'uvicorn' } | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

cd "$PSScriptRoot"

Write-Host "Starting server with mock mode..." -ForegroundColor Yellow
$env:PYTHONPATH = "src"
$env:EVA_MOCK_MODE = "true"

# Start server in background job
$job = Start-Job -ScriptBlock {
    param($workDir)
    Set-Location $workDir
    $env:PYTHONPATH = "src"
    $env:EVA_MOCK_MODE = "true"
    & uvicorn eva_api.main:app --host 127.0.0.1 --port 8000 --log-level warning
} -ArgumentList $PWD

Start-Sleep -Seconds 5

try {
    Write-Host "Testing health endpoint..." -ForegroundColor Yellow
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5
    Write-Host "✅ Server is up: $($health.status)" -ForegroundColor Green
    
    Write-Host "`nTesting space creation speed..." -ForegroundColor Yellow
    $startTime = Get-Date
    $body = @{
        name = "Load Test Space"
        description = "Testing mock mode"
    } | ConvertTo-Json
    
    $space = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/spaces" -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 5
    $duration = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Host "✅ Space created in $([math]::Round($duration, 0))ms" -ForegroundColor Green
    Write-Host "   ID: $($space.id)" -ForegroundColor Gray
    
    if ($duration -lt 1000) {
        Write-Host "`n✅ MOCK MODE WORKING! Ready for load test." -ForegroundColor Green
        Write-Host "`nTo run load test:" -ForegroundColor Cyan
        Write-Host "  locust -f load-tests/locustfile.py --headless --users 100 --spawn-rate 10 --run-time 5m --host http://127.0.0.1:8000`n" -ForegroundColor White
    } else {
        Write-Host "`n⚠️  Response slow ($duration ms)" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "❌ Test failed: $_" -ForegroundColor Red
} finally {
    Write-Host "`nStopping server..." -ForegroundColor Gray
    Stop-Job -Job $job -ErrorAction SilentlyContinue
    Remove-Job -Job $job -Force -ErrorAction SilentlyContinue
    Get-Process | Where-Object { $_.ProcessName -eq 'python' -or $_.ProcessName -eq 'uvicorn' } | Stop-Process -Force -ErrorAction SilentlyContinue
}

Write-Host "Done.`n" -ForegroundColor Gray
