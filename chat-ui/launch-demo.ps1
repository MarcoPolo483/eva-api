#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Launch EVA Chat UI Demo
.DESCRIPTION
    Starts the EVA API backend (if not running) and opens the chat UI in your browser.
    Perfect for quick demo testing with 25 users.
#>

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          🤖 EVA CHAT UI - Quick Demo Launcher                 ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if API is running
Write-Host "🔍 Checking EVA API server..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ API server is running" -ForegroundColor Green
} catch {
    Write-Host "❌ API server is not running" -ForegroundColor Red
    Write-Host "`nStarting API server in new terminal...`n" -ForegroundColor Yellow
    
    $apiPath = Join-Path $PSScriptRoot ".."
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$apiPath'; `$env:PYTHONPATH='src'; Write-Host '🚀 EVA API Server' -ForegroundColor Cyan; uvicorn eva_api.main:app --host 127.0.0.1 --port 8000"
    )
    
    Write-Host "Waiting for API to start..." -ForegroundColor Gray
    $retries = 0
    $maxRetries = 15
    $apiReady = $false
    
    while ($retries -lt $maxRetries -and -not $apiReady) {
        Start-Sleep -Seconds 2
        try {
            $null = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 1 -ErrorAction Stop
            $apiReady = $true
            Write-Host "✅ API server is ready!`n" -ForegroundColor Green
        } catch {
            $retries++
            Write-Host "." -NoNewline -ForegroundColor Gray
        }
    }
    
    if (-not $apiReady) {
        Write-Host "`n❌ API server failed to start. Please check the API terminal for errors." -ForegroundColor Red
        exit 1
    }
}

# Open chat UI directly in browser (no HTTP server needed for single file)
Write-Host "🌐 Opening EVA Chat UI in browser..." -ForegroundColor Green

$chatUIPath = Join-Path $PSScriptRoot "index.html"
$chatUIUrl = "file:///$($chatUIPath -replace '\\', '/')"

Start-Process $chatUIUrl

Write-Host "`n✅ Chat UI opened in your default browser`n" -ForegroundColor Green

Write-Host "📋 Quick Test Guide:" -ForegroundColor Cyan
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "  1️⃣  EVA greets: 'Hi! I'm EVA 👋'" -ForegroundColor White
Write-Host "  2️⃣  Shows your knowledge spaces from Cosmos DB" -ForegroundColor White
Write-Host "  3️⃣  Displays suggested questions" -ForegroundColor White
Write-Host "  4️⃣  Click any suggested question to test" -ForegroundColor White
Write-Host "  5️⃣  Or type 'Hi EVA' to get greeting again" -ForegroundColor White
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

Write-Host "`n⚠️  TROUBLESHOOTING:" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
Write-Host ""
Write-Host "  If you see CORS errors:" -ForegroundColor White
Write-Host "    • Close the browser tab" -ForegroundColor Gray
Write-Host "    • Use VS Code 'Live Server' extension instead" -ForegroundColor Gray
Write-Host "    • Right-click index.html → 'Open with Live Server'" -ForegroundColor Gray
Write-Host ""
Write-Host "  If 'No Knowledge Spaces Found':" -ForegroundColor White
Write-Host "    • Update API_KEY in index.html (line ~480)" -ForegroundColor Gray
Write-Host "    • Create a test space using the API" -ForegroundColor Gray
Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

Write-Host "`n📖 Full documentation: chat-ui/README.md`n" -ForegroundColor Cyan

# Keep terminal open
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
