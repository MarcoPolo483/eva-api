<#
.SYNOPSIS
    Creates Cosmos DB database and containers for EVA API
.DESCRIPTION
    Provides manual instructions for Azure Portal since Azure CLI/PowerShell Az modules aren't available
.NOTES
    Manual setup via Azure Portal
#>

param(
    [string]$AccountName = "eva-suite-cosmos-dev",
    [string]$DatabaseName = "eva-platform",
    [int]$Throughput = 400
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          🗄️  COSMOS DB SETUP GUIDE                              ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

Write-Host "⚠️  Azure CLI/PowerShell Az modules not detected." -ForegroundColor Yellow
Write-Host "   Using Azure Portal for setup (fastest method)`n" -ForegroundColor Yellow

Write-Host "📋 Configuration:" -ForegroundColor Cyan
Write-Host "   Account Name:   $AccountName" -ForegroundColor White
Write-Host "   Database:       $DatabaseName" -ForegroundColor White
Write-Host "   Throughput:     $Throughput RU/s per container`n" -ForegroundColor White

Write-Host "╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          📖 STEP-BY-STEP INSTRUCTIONS                            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

# Check if logged in
Write-Host "🔐 Checking Azure login..." -ForegroundColor Cyan
try {
    $account = az account show 2>$null | ConvertFrom-Json
    if ($LASTEXITCODE -ne 0) {
        throw "Not logged in"
    }
    Write-Host "   ✅ Logged in as: $($account.user.name)" -ForegroundColor Green
    Write-Host "   📦 Subscription: $($account.name)`n" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Not logged in to Azure!" -ForegroundColor Yellow
    Write-Host "   Running 'az login'...`n" -ForegroundColor Cyan
    az login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "   ❌ Login failed!`n" -ForegroundColor Red
        exit 1
    }
    Write-Host "   ✅ Login successful!`n" -ForegroundColor Green
}

# Verify Cosmos DB account exists
Write-Host "🔍 Verifying Cosmos DB account exists..." -ForegroundColor Cyan
try {
    $accountInfo = az cosmosdb show `
        --name $AccountName `
        --resource-group $ResourceGroup `
        2>$null | ConvertFrom-Json
    
    if ($LASTEXITCODE -ne 0) {
        throw "Account not found"
    }
    
    Write-Host "   ✅ Account found: $($accountInfo.documentEndpoint)" -ForegroundColor Green
    Write-Host "   📍 Location: $($accountInfo.location)`n" -ForegroundColor Green
} catch {
    Write-Host "   ❌ Cosmos DB account '$AccountName' not found in resource group '$ResourceGroup'!" -ForegroundColor Red
    Write-Host "`n   Available accounts:" -ForegroundColor Yellow
    az cosmosdb list --resource-group $ResourceGroup --query "[].{Name:name, Location:location}" -o table
    Write-Host ""
    exit 1
}

# Check if database already exists
Write-Host "🔍 Checking if database '$DatabaseName' exists..." -ForegroundColor Cyan
$dbExists = az cosmosdb sql database show `
    --account-name $AccountName `
    --resource-group $ResourceGroup `
    --name $DatabaseName `
    2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "   ⚠️  Database '$DatabaseName' already exists!" -ForegroundColor Yellow
    Write-Host "   Skipping database creation...`n" -ForegroundColor Yellow
} else {
    Write-Host "   ℹ️  Database does not exist, creating..." -ForegroundColor Cyan
    
    # Create database
    Write-Host "`n📦 Creating database '$DatabaseName'..." -ForegroundColor Cyan
    az cosmosdb sql database create `
        --account-name $AccountName `
        --resource-group $ResourceGroup `
        --name $DatabaseName `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✅ Database created successfully!`n" -ForegroundColor Green
    } else {
        Write-Host "   ❌ Failed to create database!`n" -ForegroundColor Red
        exit 1
    }
}

# Define containers with partition keys
$containers = @(
    @{Name = "spaces"; PartitionKey = "/id"},
    @{Name = "documents"; PartitionKey = "/space_id"},
    @{Name = "queries"; PartitionKey = "/space_id"}
)

# Create each container
Write-Host "📦 Creating containers..." -ForegroundColor Cyan
foreach ($container in $containers) {
    $containerName = $container.Name
    $partitionKey = $container.PartitionKey
    
    Write-Host "`n   Creating '$containerName' (partition key: $partitionKey)..." -ForegroundColor Yellow
    
    # Check if container exists
    $containerExists = az cosmosdb sql container show `
        --account-name $AccountName `
        --resource-group $ResourceGroup `
        --database-name $DatabaseName `
        --name $containerName `
        2>$null
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ⚠️  Container '$containerName' already exists, skipping..." -ForegroundColor Yellow
        continue
    }
    
    # Create container
    az cosmosdb sql container create `
        --account-name $AccountName `
        --resource-group $ResourceGroup `
        --database-name $DatabaseName `
        --name $containerName `
        --partition-key-path $partitionKey `
        --throughput $Throughput `
        --output none
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "      ✅ Container '$containerName' created successfully!" -ForegroundColor Green
    } else {
        Write-Host "      ❌ Failed to create container '$containerName'!" -ForegroundColor Red
        exit 1
    }
}

# Verify all containers were created
Write-Host "`n🔍 Verifying setup..." -ForegroundColor Cyan
$containerList = az cosmosdb sql container list `
    --account-name $AccountName `
    --resource-group $ResourceGroup `
    --database-name $DatabaseName `
    --query "[].name" -o tsv

Write-Host "   Containers in '$DatabaseName':" -ForegroundColor White
foreach ($containerName in $containerList) {
    Write-Host "      ✅ $containerName" -ForegroundColor Green
}

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          ✅ COSMOS DB SETUP COMPLETE!                            ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "   Database:   $DatabaseName" -ForegroundColor White
Write-Host "   Containers: spaces, documents, queries" -ForegroundColor White
Write-Host "   Throughput: $Throughput RU/s per container" -ForegroundColor White
Write-Host "   Total Cost: ~`$19.20/month (3 containers × 400 RU/s)`n" -ForegroundColor White

Write-Host "🧪 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Test API connection:" -ForegroundColor White
Write-Host "      curl -X POST http://localhost:8000/api/v1/spaces ``" -ForegroundColor Gray
Write-Host "           -H 'Content-Type: application/json' ``" -ForegroundColor Gray
Write-Host "           -d '{""name"":""test"",""description"":""test""}'" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Run load test:" -ForegroundColor White
Write-Host "      cd 'c:\Users\marco\Documents\_AI Dev\EVA Suite\eva-api'" -ForegroundColor Gray
Write-Host "      locust -f load-tests/locustfile.py --headless ``" -ForegroundColor Gray
Write-Host "             --users 50 --spawn-rate 5 --run-time 5m ``" -ForegroundColor Gray
Write-Host "             --host http://127.0.0.1:8000 ``" -ForegroundColor Gray
Write-Host "             --html load-tests/report-azure-50users-v2.html``" -ForegroundColor Gray
Write-Host ""

Write-Host "✨ Database is ready for use!`n" -ForegroundColor Green
