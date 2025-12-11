<#
.SYNOPSIS
    Quick Cosmos DB container setup for serverless account
#>

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║          🗄️  CREATING COSMOS DB CONTAINERS (Serverless)         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

$account = "eva-suite-cosmos-dev"
$resourceGroup = "eva-suite-rg"
$database = "eva-platform"

# Container 1: spaces
Write-Host "📦 Creating 'spaces' container..." -ForegroundColor Yellow
az cosmosdb sql container create `
    --account-name $account `
    --resource-group $resourceGroup `
    --database-name $database `
    --name "spaces" `
    --partition-key-path "/id"

# Container 2: documents
Write-Host "`n📦 Creating 'documents' container..." -ForegroundColor Yellow
az cosmosdb sql container create `
    --account-name $account `
    --resource-group $resourceGroup `
    --database-name $database `
    --name "documents" `
    --partition-key-path "/space_id"

# Container 3: queries
Write-Host "`n📦 Creating 'queries' container..." -ForegroundColor Yellow
az cosmosdb sql container create `
    --account-name $account `
    --resource-group $resourceGroup `
    --database-name $database `
    --name "queries" `
    --partition-key-path "/space_id"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          ✅ SETUP COMPLETE!                                      ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "Verifying setup..." -ForegroundColor Cyan
az cosmosdb sql container list `
    --account-name $account `
    --resource-group $resourceGroup `
    --database-name $database `
    --query "[].{Name:name, PartitionKey:partitionKey.paths[0]}" `
    -o table

Write-Host "`n✨ Ready to test! Start your API server and try creating a space.`n" -ForegroundColor Green
