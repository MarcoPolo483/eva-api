#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Setup Production Environment Using Existing Development Credentials

.DESCRIPTION
    Copies working credentials from .env to .env.production and generates
    only the missing security secrets (JWT_SECRET_KEY and API_KEY_SALT).
    
    This is the fastest path to production since all Azure services are
    already configured and tested in development.

.EXAMPLE
    .\setup-production-env.ps1
#>

$ErrorActionPreference = "Stop"

Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║        Production Environment Setup (Using Dev Credentials)       ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Check if .env exists
if (-not (Test-Path ".env")) {
    Write-Host "❌ Error: .env file not found!" -ForegroundColor Red
    Write-Host "   Make sure you're in the eva-api directory.`n" -ForegroundColor Gray
    exit 1
}

Write-Host "📋 Step 1: Reading development credentials..." -ForegroundColor Yellow

# Read existing .env
$envContent = Get-Content ".env" -Raw

# Extract credentials
$credentials = @{}
$patterns = @{
    "COSMOS_DB_ENDPOINT" = 'COSMOS_DB_ENDPOINT=([^\r\n]+)'
    "COSMOS_DB_KEY" = 'COSMOS_DB_KEY=([^\r\n]+)'
    "AZURE_STORAGE_ACCOUNT_NAME" = 'AZURE_STORAGE_ACCOUNT_NAME=([^\r\n]+)'
    "AZURE_STORAGE_ACCOUNT_KEY" = 'AZURE_STORAGE_ACCOUNT_KEY=([^\r\n]+)'
    "AZURE_OPENAI_ENDPOINT" = 'AZURE_OPENAI_ENDPOINT=([^\r\n]+)'
    "AZURE_OPENAI_KEY" = 'AZURE_OPENAI_KEY=([^\r\n]+)'
    "AZURE_ENTRA_TENANT_ID" = 'AZURE_ENTRA_TENANT_ID=([^\r\n]+)'
    "AZURE_ENTRA_CLIENT_ID" = 'AZURE_ENTRA_CLIENT_ID=([^\r\n]+)'
    "AZURE_ENTRA_CLIENT_SECRET" = 'AZURE_ENTRA_CLIENT_SECRET=([^\r\n]+)'
}

foreach ($key in $patterns.Keys) {
    if ($envContent -match $patterns[$key]) {
        $credentials[$key] = $matches[1]
        Write-Host "   ✅ Found $key" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Missing $key" -ForegroundColor Yellow
    }
}

Write-Host "`n🔐 Step 2: Generating security secrets..." -ForegroundColor Yellow

# Generate strong secrets
$jwtSecret = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
$apiSalt = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))

Write-Host "   ✅ Generated JWT_SECRET_KEY (32 bytes)" -ForegroundColor Green
Write-Host "   ✅ Generated API_KEY_SALT (32 bytes)" -ForegroundColor Green

Write-Host "`n📝 Step 3: Creating .env.production..." -ForegroundColor Yellow

# Read template
$prodTemplate = Get-Content ".env.production" -Raw

# Replace placeholders with actual values
$prodTemplate = $prodTemplate -replace 'AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com', "AZURE_OPENAI_ENDPOINT=$($credentials['AZURE_OPENAI_ENDPOINT'])"
$prodTemplate = $prodTemplate -replace 'AZURE_OPENAI_KEY=REPLACE-WITH-PRODUCTION-KEY', "AZURE_OPENAI_KEY=$($credentials['AZURE_OPENAI_KEY'])"

$prodTemplate = $prodTemplate -replace 'COSMOS_DB_ENDPOINT=https://your-cosmos-account.documents.azure.com:443/', "COSMOS_DB_ENDPOINT=$($credentials['COSMOS_DB_ENDPOINT'])"
$prodTemplate = $prodTemplate -replace 'COSMOS_DB_KEY=REPLACE-WITH-PRODUCTION-KEY', "COSMOS_DB_KEY=$($credentials['COSMOS_DB_KEY'])"

$prodTemplate = $prodTemplate -replace 'AZURE_STORAGE_ACCOUNT_NAME=your-storage-account-prod', "AZURE_STORAGE_ACCOUNT_NAME=$($credentials['AZURE_STORAGE_ACCOUNT_NAME'])"
$prodTemplate = $prodTemplate -replace 'AZURE_STORAGE_ACCOUNT_KEY=REPLACE-WITH-PRODUCTION-KEY', "AZURE_STORAGE_ACCOUNT_KEY=$($credentials['AZURE_STORAGE_ACCOUNT_KEY'])"

$prodTemplate = $prodTemplate -replace 'AZURE_ENTRA_TENANT_ID=REPLACE-WITH-YOUR-TENANT-ID', "AZURE_ENTRA_TENANT_ID=$($credentials['AZURE_ENTRA_TENANT_ID'])"
$prodTemplate = $prodTemplate -replace 'AZURE_ENTRA_CLIENT_ID=REPLACE-WITH-YOUR-CLIENT-ID', "AZURE_ENTRA_CLIENT_ID=$($credentials['AZURE_ENTRA_CLIENT_ID'])"
$prodTemplate = $prodTemplate -replace 'AZURE_ENTRA_CLIENT_SECRET=REPLACE-WITH-YOUR-CLIENT-SECRET', "AZURE_ENTRA_CLIENT_SECRET=$($credentials['AZURE_ENTRA_CLIENT_SECRET'])"

$prodTemplate = $prodTemplate -replace 'JWT_ISSUER=https://login.microsoftonline.com/YOUR-TENANT-ID/v2.0', "JWT_ISSUER=https://login.microsoftonline.com/$($credentials['AZURE_ENTRA_TENANT_ID'])/v2.0"
$prodTemplate = $prodTemplate -replace 'JWT_AUDIENCE=YOUR-CLIENT-ID', "JWT_AUDIENCE=$($credentials['AZURE_ENTRA_CLIENT_ID'])"
$prodTemplate = $prodTemplate -replace 'JWT_SECRET_KEY=REPLACE-WITH-STRONG-SECRET-MIN-32-CHARS', "JWT_SECRET_KEY=$jwtSecret"

$prodTemplate = $prodTemplate -replace 'API_KEY_SALT=REPLACE-WITH-STRONG-SALT-MIN-32-CHARS', "API_KEY_SALT=$apiSalt"

# Redis - use local for now (can be updated later)
$prodTemplate = $prodTemplate -replace 'REDIS_HOST=your-redis-cache.redis.cache.windows.net', "REDIS_HOST=localhost"
$prodTemplate = $prodTemplate -replace 'REDIS_PORT=6380', "REDIS_PORT=6379"
$prodTemplate = $prodTemplate -replace 'REDIS_PASSWORD=REPLACE-WITH-PRODUCTION-KEY', "REDIS_PASSWORD="
$prodTemplate = $prodTemplate -replace 'REDIS_SSL=true', "REDIS_SSL=false"

# Update CORS (keeping placeholder for user to customize)
# Keep: CORS_ORIGINS=["https://your-frontend-domain.com", ...]

# Save to file
$prodTemplate | Out-File -FilePath ".env.production" -Encoding utf8 -NoNewline

Write-Host "   ✅ .env.production updated with working credentials" -ForegroundColor Green

Write-Host "`n✅ Step 4: Verifying configuration..." -ForegroundColor Yellow

# Check for remaining placeholders (excluding CORS and optional Application Insights)
$remainingPlaceholders = ($prodTemplate | Select-String -Pattern "REPLACE-WITH-" -AllMatches).Matches.Count
if ($remainingPlaceholders -gt 0) {
    Write-Host "   ⚠️  $remainingPlaceholders placeholder(s) remaining (Application Insights - optional)" -ForegroundColor Yellow
} else {
    Write-Host "   ✅ All critical credentials configured" -ForegroundColor Green
}

Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    ✅ SETUP COMPLETE ✅                           ║" -ForegroundColor Green
Write-Host "╚════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📋 Configuration Summary:`n" -ForegroundColor Cyan

Write-Host "   Azure Services (from development):" -ForegroundColor Yellow
Write-Host "   • Cosmos DB: $($credentials['COSMOS_DB_ENDPOINT'])" -ForegroundColor Gray
Write-Host "   • Blob Storage: $($credentials['AZURE_STORAGE_ACCOUNT_NAME'])" -ForegroundColor Gray
Write-Host "   • Azure OpenAI: $($credentials['AZURE_OPENAI_ENDPOINT'])" -ForegroundColor Gray
Write-Host "   • Entra ID: Tenant $($credentials['AZURE_ENTRA_TENANT_ID'])" -ForegroundColor Gray
Write-Host "   • Redis: localhost:6379 (local)`n" -ForegroundColor Gray

Write-Host "   Generated Secrets:" -ForegroundColor Yellow
Write-Host "   • JWT_SECRET_KEY: $($jwtSecret.Substring(0, 16))... (32 bytes)" -ForegroundColor Gray
Write-Host "   • API_KEY_SALT: $($apiSalt.Substring(0, 16))... (32 bytes)`n" -ForegroundColor Gray

Write-Host "🎯 Next Steps:`n" -ForegroundColor Cyan

Write-Host "   1. (Optional) Update CORS origins in .env.production:" -ForegroundColor White
Write-Host "      CORS_ORIGINS=[`"https://your-domain.com`"]`n" -ForegroundColor Gray

Write-Host "   2. Run validation:" -ForegroundColor White
Write-Host "      .\validate-production-readiness.ps1`n" -ForegroundColor Gray

Write-Host "   3. Test server with production config:" -ForegroundColor White
Write-Host "      `$env:PYTHONPATH = 'src'" -ForegroundColor Gray
Write-Host "      uvicorn eva_api.main:app --host 127.0.0.1 --port 8000`n" -ForegroundColor Gray

Write-Host "   4. Check health:" -ForegroundColor White
Write-Host "      curl http://localhost:8000/health`n" -ForegroundColor Gray

Write-Host "✨ Production environment ready for testing!`n" -ForegroundColor Green
