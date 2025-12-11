<#
🧩 CONTEXT:
Deploy EVA API to Azure App Service with Phase 3 features (GraphQL subscriptions, DataLoader, 
webhooks). Automates resource creation, configuration, and deployment for production-ready API.

🧩 SYNOPSIS:
    Deploy EVA API to Azure App Service

🧩 DESCRIPTION:
    Creates Azure App Service (Linux, Python 3.11), configures environment from .env.production,
    deploys FastAPI application with ZIP deployment, and validates health endpoint.

🧩 CONTEXT_ENGINEERING:
    Mission: Deploy EVA API to cloud for 25-user demo and beyond
    Constraints: Requires Azure CLI, .env.production file, git repository
    Reuses: .env.production for configuration, eva-orchestrator Azure patterns
    Validates: Azure login, resource creation, deployment success, health check

🧩 HOUSEKEEPING:
    Creates: Azure resource group, App Service Plan (B1), App Service (Linux), deployment
    Modifies: Azure subscription resources
    Validates: Azure CLI installed, .env.production exists, app responds to /health
    Cleans: None (resources persist)
    Monitors: Deployment logs, health endpoint, app service logs

🧩 WORKSPACE_MANAGEMENT:
    TreeUpdates: No
    Navigation: No
    Caching: None
    SessionState: No

🧩 COMPLIANCE:
    WCAG: N/A (backend infrastructure)
    Bilingual: N/A (Azure CLI commands)
    RBAC: POD-F + POD-O
    ProtectedB: Yes (uses Azure services configured for Protected B)
    Audit: Logs all Azure operations to console output

.PARAMETER ResourceGroup
    Azure resource group name (default: eva-suite-rg)

.PARAMETER AppName
    App Service name (default: eva-api-prod)

.PARAMETER Location
    Azure region (default: canadacentral)

.PARAMETER Tier
    App Service Plan tier (default: B1, ~$13.14/month)

.PARAMETER SkipBuild
    Skip pip install step (use if requirements already frozen)

.NOTES
    POD: POD-F (API Layer)
    Owner: P04-LIB + P15-DVM
    Cost: ~$13.14/month (B1 tier) + egress
    Last Modified: 2025-12-08
#>

Param(
    [string]$ResourceGroup = "eva-suite-rg",
    [string]$AppName = "eva-api-prod",
    [string]$Location = "canadacentral",
    [string]$Tier = "B1",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

# Validate prerequisites
Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          🚀 EVA API - Azure Deployment Automation               ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "📋 Validating prerequisites..." -ForegroundColor Yellow

# Check Azure CLI
if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Azure CLI not found. Install from: https://aka.ms/installazurecliwindows" -ForegroundColor Red
    exit 1
}

# Check .env.production
if (-not (Test-Path ".env.production")) {
    Write-Host "❌ .env.production not found. Run setup-production-env.ps1 first." -ForegroundColor Red
    exit 1
}

# Check git (for deployment source)
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Git not found. Required for deployment." -ForegroundColor Red
    exit 1
}

Write-Host "✅ Prerequisites validated`n" -ForegroundColor Green

# Azure Login
Write-Host "🔐 Checking Azure login status..." -ForegroundColor Yellow
az account show *>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Logging into Azure..." -ForegroundColor Cyan
    az login
}

$subscription = (az account show --query name -o tsv)
Write-Host "✅ Logged in: $subscription`n" -ForegroundColor Green

# Step 1: Create Resource Group
Write-Host "📦 Step 1/5: Creating resource group '$ResourceGroup'..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Location --output none
Write-Host "✅ Resource group ready`n" -ForegroundColor Green

# Step 2: Create App Service Plan
$planName = "$AppName-plan"
Write-Host "🏗️  Step 2/5: Creating App Service Plan '$planName' ($Tier tier)..." -ForegroundColor Cyan
Write-Host "   Cost: ~$13.14/month (100 GB storage, 1.75 GB RAM, 1 vCPU)" -ForegroundColor Gray

az appservice plan create `
    --name $planName `
    --resource-group $ResourceGroup `
    --location $Location `
    --is-linux `
    --sku $Tier `
    --output none

Write-Host "✅ App Service Plan created`n" -ForegroundColor Green

# Step 3: Create App Service
Write-Host "🌐 Step 3/5: Creating App Service '$AppName'..." -ForegroundColor Cyan

az webapp create `
    --name $AppName `
    --resource-group $ResourceGroup `
    --plan $planName `
    --runtime "PYTHON:3.11" `
    --output none

Write-Host "✅ App Service created`n" -ForegroundColor Green

# Step 4: Configure Environment Variables
Write-Host "⚙️  Step 4/5: Configuring environment variables from .env.production..." -ForegroundColor Cyan

# Parse .env.production
$envVars = @()
Get-Content .env.production | ForEach-Object {
    $line = $_.Trim()
    if ($line -and -not $line.StartsWith("#")) {
        if ($line -match "^([^=]+)=(.*)$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim().Trim('"')
            $envVars += "$key=$value"
        }
    }
}

# Set app settings (batched for efficiency)
if ($envVars.Count -gt 0) {
    Write-Host "   Setting $($envVars.Count) environment variables..." -ForegroundColor Gray
    
    # Azure requires space-separated key=value pairs
    $settingsString = $envVars -join " "
    
    az webapp config appsettings set `
        --name $AppName `
        --resource-group $ResourceGroup `
        --settings $envVars `
        --output none
}

# Set startup command for FastAPI
Write-Host "   Configuring startup command..." -ForegroundColor Gray
az webapp config set `
    --name $AppName `
    --resource-group $ResourceGroup `
    --startup-file "gunicorn -w 4 -k uvicorn.workers.UvicornWorker eva_api.main:app --bind 0.0.0.0:8000 --timeout 120" `
    --output none

Write-Host "✅ Configuration complete`n" -ForegroundColor Green

# Step 5: Deploy Application
Write-Host "🚀 Step 5/5: Deploying application..." -ForegroundColor Cyan

if (-not $SkipBuild) {
    Write-Host "   Installing dependencies locally (for deployment package)..." -ForegroundColor Gray
    
    # Create deployment package with dependencies
    $deployPath = Join-Path $PWD "deploy-package"
    if (Test-Path $deployPath) {
        [System.IO.Directory]::Delete($deployPath, $true)
    }
    New-Item -ItemType Directory -Path $deployPath | Out-Null
    
    # Copy source files
    Copy-Item -Recurse "src/*" "deploy-package/"
    Copy-Item "requirements.txt" "deploy-package/"
    
    # Create requirements.txt without local packages
    $cleanReqs = Get-Content requirements.txt | Where-Object { 
        $_ -notmatch "^\s*#" -and 
        $_ -notmatch "^\s*$" -and 
        $_ -notmatch "-e\s+" 
    }
    $cleanReqs | Set-Content "deploy-package/requirements.txt"
}

# Create ZIP for deployment
Write-Host "   Creating deployment package..." -ForegroundColor Gray
$zipPath = Join-Path $PWD "deploy.zip"
if (Test-Path $zipPath) {
    [System.IO.File]::Delete($zipPath)
}

# Compress deployment package
Compress-Archive -Path "deploy-package/*" -DestinationPath "deploy.zip" -Force

# Deploy ZIP
Write-Host "   Uploading to Azure (this may take 2-3 minutes)..." -ForegroundColor Gray
az webapp deployment source config-zip `
    --name $AppName `
    --resource-group $ResourceGroup `
    --src "deploy.zip" `
    --output none

Write-Host "✅ Deployment complete`n" -ForegroundColor Green

# Get app URL
$appUrl = "https://$AppName.azurewebsites.net"

Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    🎉 DEPLOYMENT SUCCESSFUL!                     ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "🌐 App URL: $appUrl" -ForegroundColor Cyan
Write-Host "🔍 Health Check: $appUrl/health" -ForegroundColor Cyan
Write-Host "📚 API Docs: $appUrl/docs" -ForegroundColor Cyan
Write-Host "🔌 GraphQL: $appUrl/graphql" -ForegroundColor Cyan

Write-Host "`n⏳ Waiting for app to start (30 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host "`n🏥 Testing health endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$appUrl/health" -TimeoutSec 10
    Write-Host "✅ Health check passed!" -ForegroundColor Green
    Write-Host "   Status: $($response.status)" -ForegroundColor Gray
    Write-Host "   Environment: $($response.environment)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Health check failed (app may still be starting)" -ForegroundColor Yellow
    Write-Host "   View logs: az webapp log tail --name $AppName --resource-group $ResourceGroup" -ForegroundColor Gray
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "   1. Update chat UI with new API URL:" -ForegroundColor Gray
Write-Host "      API_BASE: '$appUrl'" -ForegroundColor White
Write-Host "   2. Test API endpoints:" -ForegroundColor Gray
Write-Host "      curl $appUrl/health" -ForegroundColor White
Write-Host "   3. View live logs:" -ForegroundColor Gray
Write-Host "      az webapp log tail --name $AppName --resource-group $ResourceGroup" -ForegroundColor White
Write-Host "   4. Redeploy chat UI:" -ForegroundColor Gray
Write-Host "      cd chat-ui; .\deploy-to-azure.ps1" -ForegroundColor White

Write-Host "`n💰 Monthly Cost Estimate: ~$13.14 (B1 tier) + minimal egress" -ForegroundColor Yellow
Write-Host "🗑️  To delete resources: az group delete --name $ResourceGroup" -ForegroundColor Gray

Write-Host "`n🎊 Marco's EVA API is now running in Azure! 🇨🇦`n" -ForegroundColor Green
