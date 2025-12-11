#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Production Readiness Validation Script for EVA API

.DESCRIPTION
    Validates all requirements for production deployment:
    - Environment configuration
    - Azure service connectivity
    - Security settings
    - Test suite execution
    - Performance benchmarks
    - Documentation completeness

.EXAMPLE
    .\validate-production-readiness.ps1
#>

param(
    [switch]$SkipTests,
    [switch]$SkipAzureConnectivity,
    [switch]$Verbose
)

$ErrorActionPreference = "Continue"
$script:ValidationErrors = @()
$script:ValidationWarnings = @()
$script:ValidationPassed = 0
$script:ValidationTotal = 0

function Write-ValidationHeader {
    param([string]$Title)
    Write-Host "`n╔════════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  $Title" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan
}

function Test-Validation {
    param(
        [string]$Name,
        [scriptblock]$Test,
        [bool]$Critical = $true
    )
    
    $script:ValidationTotal++
    Write-Host "▶ $Name..." -NoNewline
    
    try {
        $result = & $Test
        if ($result -eq $true -or $result -eq $null) {
            Write-Host " ✅" -ForegroundColor Green
            $script:ValidationPassed++
            return $true
        } else {
            throw "Validation failed"
        }
    } catch {
        if ($Critical) {
            Write-Host " ❌ CRITICAL" -ForegroundColor Red
            $script:ValidationErrors += "CRITICAL: $Name - $($_.Exception.Message)"
        } else {
            Write-Host " ⚠️  WARNING" -ForegroundColor Yellow
            $script:ValidationWarnings += "WARNING: $Name - $($_.Exception.Message)"
        }
        return $false
    }
}

# ==================== Environment Configuration ====================
Write-ValidationHeader "1. Environment Configuration"

Test-Validation ".env.production exists" {
    Test-Path ".env.production"
}

Test-Validation ".env.production has no placeholder values" {
    $content = Get-Content ".env.production" -Raw
    if ($content -match "REPLACE-WITH-") {
        throw "Found placeholder values. Update all REPLACE-WITH-* values."
    }
    return $true
} -Critical $false

Test-Validation "Required environment variables defined" {
    $required = @(
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_KEY",
        "COSMOS_DB_ENDPOINT",
        "COSMOS_DB_KEY",
        "AZURE_STORAGE_ACCOUNT_NAME",
        "AZURE_STORAGE_ACCOUNT_KEY",
        "REDIS_HOST",
        "JWT_SECRET_KEY"
    )
    
    $content = Get-Content ".env.production" -Raw
    foreach ($var in $required) {
        if ($content -notmatch "$var=.+") {
            throw "Missing or empty: $var"
        }
    }
    return $true
}

Test-Validation "DEBUG mode is disabled" {
    $content = Get-Content ".env.production" -Raw
    if ($content -notmatch "DEBUG=false") {
        throw "DEBUG should be false in production"
    }
    return $true
}

Test-Validation "Mock mode is disabled" {
    $content = Get-Content ".env.production" -Raw
    if ($content -notmatch "EVA_MOCK_MODE=false") {
        throw "EVA_MOCK_MODE should be false in production"
    }
    return $true
}

# ==================== Python Dependencies ====================
Write-ValidationHeader "2. Python Dependencies"

Test-Validation "Python 3.11+ installed" {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[1-9]") {
        return $true
    }
    throw "Python 3.11+ required, found: $pythonVersion"
}

Test-Validation "Required packages installed" {
    $required = @("fastapi", "uvicorn", "azure-cosmos", "redis", "strawberry-graphql")
    $installed = pip list --format=freeze 2>$null
    
    foreach ($pkg in $required) {
        if ($installed -notmatch $pkg) {
            throw "Missing package: $pkg"
        }
    }
    return $true
}

# ==================== Code Quality ====================
Write-ValidationHeader "3. Code Quality"

Test-Validation "App imports successfully" {
    $env:PYTHONPATH = "src"
    $result = python -c "from eva_api.main import app; print('OK')" 2>&1
    if ($result -match "OK") {
        return $true
    }
    throw "App import failed: $result"
}

if (-not $SkipTests) {
    Test-Validation "All Phase 3 tests pass" {
        $result = pytest tests/test_phase3_features.py -v --tb=short 2>&1
        if ($result -match "22 passed") {
            return $true
        }
        throw "Some tests failed"
    }
    
    Test-Validation "All Phase 2 tests pass" {
        $result = pytest tests/test_phase2_features.py -v --tb=short 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
        throw "Some tests failed"
    } -Critical $false
}

# ==================== Azure Connectivity ====================
if (-not $SkipAzureConnectivity) {
    Write-ValidationHeader "4. Azure Service Connectivity"
    
    Test-Validation "Cosmos DB connectivity" {
        python -c @"
from azure.cosmos import CosmosClient
import os
from dotenv import load_dotenv
load_dotenv('.env.production')
client = CosmosClient(os.getenv('COSMOS_DB_ENDPOINT'), os.getenv('COSMOS_DB_KEY'))
print('OK')
"@ 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    }
    
    Test-Validation "Blob Storage connectivity" {
        python -c @"
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv
load_dotenv('.env.production')
connection_string = f"DefaultEndpointsProtocol=https;AccountName={os.getenv('AZURE_STORAGE_ACCOUNT_NAME')};AccountKey={os.getenv('AZURE_STORAGE_ACCOUNT_KEY')};EndpointSuffix=core.windows.net"
client = BlobServiceClient.from_connection_string(connection_string)
list(client.list_containers(max_results=1))
print('OK')
"@ 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    }
    
    Test-Validation "Redis connectivity" {
        python -c @"
import redis
import os
from dotenv import load_dotenv
load_dotenv('.env.production')
client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true'
)
client.ping()
print('OK')
"@ 2>&1 | Out-Null
        return $LASTEXITCODE -eq 0
    }
}

# ==================== Security Configuration ====================
Write-ValidationHeader "5. Security Configuration"

Test-Validation "JWT secret is strong (32+ chars)" {
    $content = Get-Content ".env.production" -Raw
    if ($content -match "JWT_SECRET_KEY=([^\r\n]+)") {
        $secret = $matches[1]
        if ($secret.Length -ge 32 -and $secret -notmatch "REPLACE") {
            return $true
        }
    }
    throw "JWT_SECRET_KEY must be 32+ characters"
}

Test-Validation "API key salt is strong (32+ chars)" {
    $content = Get-Content ".env.production" -Raw
    if ($content -match "API_KEY_SALT=([^\r\n]+)") {
        $salt = $matches[1]
        if ($salt.Length -ge 32 -and $salt -notmatch "REPLACE") {
            return $true
        }
    }
    throw "API_KEY_SALT must be 32+ characters"
}

Test-Validation "CORS origins configured" {
    $content = Get-Content ".env.production" -Raw
    if ($content -match 'CORS_ORIGINS=\[.+\]') {
        return $true
    }
    throw "CORS_ORIGINS not properly configured"
} -Critical $false

Test-Validation "Rate limiting enabled" {
    $content = Get-Content ".env.production" -Raw
    if ($content -match "RATE_LIMIT_ENABLED=true") {
        return $true
    }
    throw "Rate limiting should be enabled"
} -Critical $false

# ==================== Documentation ====================
Write-ValidationHeader "6. Documentation Completeness"

$requiredDocs = @(
    "docs/WEBHOOK-STORAGE-IMPLEMENTATION.md",
    "docs/PRODUCTION-DEPLOYMENT-CHECKLIST.md",
    "docs/INTEGRATION-TESTING-GUIDE.md",
    "docs/PHASE-4-PLANNING.md",
    "PHASE-3-COMPLETION.md",
    "README.md"
)

foreach ($doc in $requiredDocs) {
    Test-Validation "Documentation: $doc" {
        Test-Path $doc
    } -Critical $false
}

# ==================== Feature Verification ====================
Write-ValidationHeader "7. Phase 3 Features"

Test-Validation "GraphQL endpoint configured" {
    $mainContent = Get-Content "src/eva_api/main.py" -Raw
    return $mainContent -match "graphql_app" -and $mainContent -match "/graphql"
}

Test-Validation "Webhook router enabled" {
    $mainContent = Get-Content "src/eva_api/main.py" -Raw
    return $mainContent -match "webhooks.router"
}

Test-Validation "WebSocket support enabled" {
    $mainContent = Get-Content "src/eva_api/main.py" -Raw
    return $mainContent -match "websockets"
}

Test-Validation "DataLoader optimization present" {
    Test-Path "src/eva_api/graphql/dataloaders.py"
}

Test-Validation "Webhook storage layer implemented" {
    $cosmosContent = Get-Content "src/eva_api/services/cosmos_service.py" -Raw
    return $cosmosContent -match "create_webhook" -and $cosmosContent -match "webhook_logs"
}

# ==================== Results Summary ====================
Write-ValidationHeader "VALIDATION SUMMARY"

$passRate = [math]::Round(($script:ValidationPassed / $script:ValidationTotal) * 100, 1)
$totalChecks = $script:ValidationTotal

Write-Host "Total Checks: $totalChecks" -ForegroundColor Cyan
Write-Host "Passed: $script:ValidationPassed" -ForegroundColor Green
Write-Host "Failed: $($script:ValidationErrors.Count)" -ForegroundColor Red
Write-Host "Warnings: $($script:ValidationWarnings.Count)" -ForegroundColor Yellow
Write-Host "Pass Rate: $passRate%`n" -ForegroundColor $(if ($passRate -ge 90) { "Green" } elseif ($passRate -ge 75) { "Yellow" } else { "Red" })

if ($script:ValidationErrors.Count -gt 0) {
    Write-Host "❌ CRITICAL ERRORS:`n" -ForegroundColor Red
    foreach ($error in $script:ValidationErrors) {
        Write-Host "   • $error" -ForegroundColor Red
    }
    Write-Host ""
}

if ($script:ValidationWarnings.Count -gt 0) {
    Write-Host "⚠️  WARNINGS:`n" -ForegroundColor Yellow
    foreach ($warning in $script:ValidationWarnings) {
        Write-Host "   • $warning" -ForegroundColor Yellow
    }
    Write-Host ""
}

if ($script:ValidationErrors.Count -eq 0) {
    Write-Host "✅ PRODUCTION READY" -ForegroundColor Green
    Write-Host "   System passes all critical validation checks." -ForegroundColor Gray
    Write-Host "   Review warnings and proceed with deployment.`n" -ForegroundColor Gray
    exit 0
} else {
    Write-Host "❌ NOT PRODUCTION READY" -ForegroundColor Red
    Write-Host "   Fix critical errors before deploying.`n" -ForegroundColor Gray
    exit 1
}
