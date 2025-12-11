# ============================================================================
# Deploy EVA Chat UI to Azure with Session Management
# ============================================================================

param(
    [switch]$TestLocal
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║  🚀 EVA Enterprise Virtual Assistant - Azure Deployment        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$chatUIPath = "c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api\chat-ui"
$storageAccount = "evasuitestoragedev"
$container = "`$web"

# ============================================================================
# Test Locally First
# ============================================================================

if ($TestLocal) {
    Write-Host "🧪 Testing locally first...`n" -ForegroundColor Yellow
    
    # Check if demo-data.json exists
    if (-not (Test-Path "$chatUIPath\demo-data.json")) {
        Write-Host "❌ demo-data.json not found!" -ForegroundColor Red
        Write-Host "   Run bootstrap-production.ps1 first`n" -ForegroundColor Yellow
        exit 1
    }
    
    # Start local test
    Write-Host "✅ Files ready for testing" -ForegroundColor Green
    Write-Host "   - index.html ($(( Get-Item "$chatUIPath\index.html").Length) bytes)" -ForegroundColor Gray
    Write-Host "   - demo-data.json ($(( Get-Item "$chatUIPath\demo-data.json").Length) bytes)`n" -ForegroundColor Gray
    
    Write-Host "🌐 Opening in browser...`n" -ForegroundColor Cyan
    Start-Process "file:///$chatUIPath/index.html"
    
    Write-Host "✅ Test the following:" -ForegroundColor Green
    Write-Host "   1. Page loads without spinner" -ForegroundColor White
    Write-Host "   2. Green light shows 'Connected (1/25 users)'" -ForegroundColor White
    Write-Host "   3. 6 suggested questions appear" -ForegroundColor White
    Write-Host "   4. Clicking question sends to Azure API`n" -ForegroundColor White
    
    Write-Host "👉 If everything works, run without -TestLocal to deploy to Azure`n" -ForegroundColor Yellow
    exit 0
}

# ============================================================================
# Deploy to Azure
# ============================================================================

Write-Host "📦 Deploying to Azure Blob Storage...`n" -ForegroundColor Cyan

# Check Azure CLI
try {
    az account show | Out-Null
} catch {
    Write-Host "❌ Not logged into Azure!" -ForegroundColor Red
    Write-Host "   Run: az login`n" -ForegroundColor Yellow
    exit 1
}

# Upload files
Write-Host "📤 Uploading index.html..." -ForegroundColor Yellow
az storage blob upload `
    --account-name $storageAccount `
    --container-name $container `
    --name "index.html" `
    --file "$chatUIPath\index.html" `
    --content-type "text/html" `
    --overwrite `
    --only-show-errors

Write-Host "✅ index.html uploaded" -ForegroundColor Green

Write-Host "📤 Uploading demo-data.json..." -ForegroundColor Yellow
az storage blob upload `
    --account-name $storageAccount `
    --container-name $container `
    --name "demo-data.json" `
    --file "$chatUIPath\demo-data.json" `
    --content-type "application/json" `
    --overwrite `
    --only-show-errors

Write-Host "✅ demo-data.json uploaded`n" -ForegroundColor Green

# ============================================================================
# Deployment Summary
# ============================================================================

$url = "https://$storageAccount.z9.web.core.windows.net"

Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ DEPLOYMENT SUCCESSFUL                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "🌐 Live URL:" -ForegroundColor Cyan
Write-Host "   $url`n" -ForegroundColor White

Write-Host "🎯 Features Enabled:" -ForegroundColor Cyan
Write-Host "   ✅ 25-user capacity tracking" -ForegroundColor Green
Write-Host "   ✅ Real-time connection status" -ForegroundColor Green
Write-Host "   ✅ Automatic session cleanup (30 min)" -ForegroundColor Green
Write-Host "   ✅ Demo data with suggested questions" -ForegroundColor Green
Write-Host "   ✅ Bilingual FR/EN support" -ForegroundColor Green
Write-Host "   ✅ Holiday theme with snowflakes`n" -ForegroundColor Green

Write-Host "📊 Test Scenarios:" -ForegroundColor Cyan
Write-Host "   1. Open in browser: $url" -ForegroundColor White
Write-Host "   2. Check green light: 'Connected (1/25 users)'" -ForegroundColor White
Write-Host "   3. Open 5 more tabs → count should increase to 6/25" -ForegroundColor White
Write-Host "   4. Close tabs → count should decrease" -ForegroundColor White
Write-Host "   5. Wait 30 min idle → session expires automatically`n" -ForegroundColor White

Write-Host "🔍 Monitoring:" -ForegroundColor Cyan
Write-Host "   API Health: https://eva-api-container.azurewebsites.net/health" -ForegroundColor White
Write-Host "   Session Status: https://eva-api-container.azurewebsites.net/api/v1/sessions/status`n" -ForegroundColor White

Write-Host "✅ Ready for 25-user demo!`n" -ForegroundColor Green
