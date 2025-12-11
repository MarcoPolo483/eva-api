#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy EVA Chat UI to Azure Blob Storage (Static Website)
.DESCRIPTION
    Fastest deployment option - 2 minutes to get live URL.
    Uploads chat UI to your existing Azure Storage account.
#>

param(
    [string]$StorageAccount = "evasuitestoragedev",
    [string]$ResourceGroup = "rg-evada2"
)

Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     🚀 EVA CHAT UI - Azure Blob Storage Deployment           ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Step 1: Check Azure CLI
Write-Host "📋 Step 1: Checking prerequisites..." -ForegroundColor Yellow
try {
    $azVersion = az version --output json 2>$null | ConvertFrom-Json
    Write-Host "   ✅ Azure CLI installed: $($azVersion.'azure-cli')" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Azure CLI not found" -ForegroundColor Red
    Write-Host "`n   Install with: winget install Microsoft.AzureCLI`n" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check Azure login
Write-Host "`n📋 Step 2: Checking Azure login..." -ForegroundColor Yellow
try {
    $account = az account show 2>$null | ConvertFrom-Json
    Write-Host "   ✅ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "   ✅ Subscription: $($account.name)" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Not logged in to Azure" -ForegroundColor Red
    Write-Host "`n   Running: az login...`n" -ForegroundColor Yellow
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n   ❌ Azure login failed`n" -ForegroundColor Red
        exit 1
    }
}

# Step 3: Enable static website hosting
Write-Host "`n📋 Step 3: Enabling static website hosting..." -ForegroundColor Yellow
try {
    az storage blob service-properties update `
        --account-name $StorageAccount `
        --static-website `
        --index-document index.html `
        --404-document index.html `
        2>$null | Out-Null
    
    Write-Host "   ✅ Static website hosting enabled" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Static hosting may already be enabled (this is OK)" -ForegroundColor Yellow
}

# Step 4: Upload chat UI files
Write-Host "`n📋 Step 4: Uploading chat UI to Azure..." -ForegroundColor Yellow
$chatUIPath = $PSScriptRoot

if (-not (Test-Path "$chatUIPath\index.html")) {
    Write-Host "   ❌ index.html not found in $chatUIPath" -ForegroundColor Red
    exit 1
}

try {
    # Upload HTML file
    az storage blob upload `
        --account-name $StorageAccount `
        --container-name '$web' `
        --name index.html `
        --file "$chatUIPath\index.html" `
        --content-type "text/html" `
        --overwrite `
        2>$null | Out-Null
    
    Write-Host "   ✅ index.html uploaded" -ForegroundColor Green
    
    # Upload README if exists
    if (Test-Path "$chatUIPath\README.md") {
        az storage blob upload `
            --account-name $StorageAccount `
            --container-name '$web' `
            --name README.md `
            --file "$chatUIPath\README.md" `
            --content-type "text/markdown" `
            --overwrite `
            2>$null | Out-Null
        Write-Host "   ✅ README.md uploaded" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Upload failed: $_" -ForegroundColor Red
    exit 1
}

# Step 5: Get public URL
Write-Host "`n📋 Step 5: Getting public URL..." -ForegroundColor Yellow
try {
    $storageInfo = az storage account show `
        --name $StorageAccount `
        --resource-group $ResourceGroup `
        --query "{web:primaryEndpoints.web}" `
        --output json | ConvertFrom-Json
    
    $publicUrl = $storageInfo.web.TrimEnd('/')
    
    Write-Host "`n╔════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║                  ✅ DEPLOYMENT SUCCESSFUL!                    ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green
    
    Write-Host "🌐 Your EVA Chat UI is now live at:" -ForegroundColor Cyan
    Write-Host "`n   $publicUrl`n" -ForegroundColor White -BackgroundColor DarkBlue
    
    Write-Host "📋 Next Steps:" -ForegroundColor Yellow
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  1️⃣  Test the chat UI:" -ForegroundColor White
    Write-Host "     Start-Process '$publicUrl'" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  2️⃣  Update API CORS to allow this URL:" -ForegroundColor White
    Write-Host "     Add to .env.production:" -ForegroundColor Gray
    Write-Host "     ALLOWED_ORIGINS=http://localhost:8000,$publicUrl" -ForegroundColor Gray
    Write-Host ""
    Write-Host "  3️⃣  Restart your API server with production config" -ForegroundColor White
    Write-Host ""
    Write-Host "  4️⃣  Update API_KEY in the deployed index.html:" -ForegroundColor White
    Write-Host "     (For now, it uses 'demo-api-key')" -ForegroundColor Gray
    Write-Host ""
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray
    
    Write-Host "`n⚠️  IMPORTANT: The chat UI points to http://127.0.0.1:8000" -ForegroundColor Yellow
    Write-Host "   This works for local testing, but for production:" -ForegroundColor Yellow
    Write-Host "   • Deploy your API to Azure App Service" -ForegroundColor Gray
    Write-Host "   • Update API_BASE in index.html to production URL" -ForegroundColor Gray
    Write-Host "   • Re-run this script to deploy updated version`n" -ForegroundColor Gray
    
    # Open browser
    Write-Host "🌐 Opening chat UI in browser..." -ForegroundColor Green
    Start-Process $publicUrl
    
} catch {
    Write-Host "   ❌ Failed to get URL: $_" -ForegroundColor Red
    Write-Host "   Try manually: https://$StorageAccount.z9.web.core.windows.net" -ForegroundColor Yellow
}

Write-Host "`n✅ Deployment complete!`n" -ForegroundColor Green
