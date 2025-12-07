# EVA API - TypeScript SDK Generation Script
#
# Generates a TypeScript/Node.js client SDK from the OpenAPI specification.
#
# Requirements:
#   npm install -g @openapitools/openapi-generator-cli
#
# Usage:
#   .\scripts\generate-typescript-sdk.ps1

Write-Host "📘 Generating TypeScript SDK..." -ForegroundColor Cyan

# Ensure API is running
Write-Host "Checking if API is running on http://localhost:8000..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -Method GET -ErrorAction Stop
    if ($response.StatusCode -ne 200) {
        Write-Host "❌ API is not responding. Please start the API first:" -ForegroundColor Red
        Write-Host "   uvicorn eva_api.main:app --reload" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ API is not running. Please start the API first:" -ForegroundColor Red
    Write-Host "   uvicorn eva_api.main:app --reload" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ API is running" -ForegroundColor Green

# Remove old SDK
if (Test-Path "sdks\typescript") {
    Write-Host "Removing old TypeScript SDK..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "sdks\typescript"
}

# Create output directory
New-Item -ItemType Directory -Force -Path "sdks\typescript" | Out-Null

# Generate SDK
Write-Host "Generating TypeScript SDK from OpenAPI spec..." -ForegroundColor Cyan
try {
    & openapi-generator-cli generate `
        -i "http://localhost:8000/openapi.json" `
        -g typescript-axios `
        -o "sdks\typescript" `
        --additional-properties=npmName=@eva/api-client,supportsES6=true,useSingleRequestParameter=true
    
    if ($LASTEXITCODE -ne 0) {
        throw "openapi-generator-cli failed"
    }
} catch {
    Write-Host "❌ Failed to generate TypeScript SDK: $_" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Cyan
Push-Location "sdks\typescript"
try {
    npm install
    if ($LASTEXITCODE -ne 0) {
        throw "npm install failed"
    }
} finally {
    Pop-Location
}

Write-Host "✅ TypeScript SDK generated successfully at sdks\typescript" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review generated code in sdks\typescript\src" -ForegroundColor White
Write-Host "  2. Build SDK: cd sdks\typescript && npm run build" -ForegroundColor White
Write-Host "  3. Run tests: cd sdks\typescript && npm test" -ForegroundColor White
Write-Host "  4. Publish: cd sdks\typescript && npm publish --access public" -ForegroundColor White
