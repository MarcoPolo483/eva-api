# EVA API - Python SDK Generation Script
#
# Generates a Python client SDK from the OpenAPI specification.
#
# Requirements:
#   pip install openapi-python-client
#
# Usage:
#   .\scripts\generate-python-sdk.ps1

Write-Host "🐍 Generating Python SDK..." -ForegroundColor Cyan

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
if (Test-Path "sdks\python") {
    Write-Host "Removing old Python SDK..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "sdks\python"
}

# Generate SDK
Write-Host "Generating Python SDK from OpenAPI spec..." -ForegroundColor Cyan
try {
    & openapi-python-client generate `
        --url "http://localhost:8000/openapi.json" `
        --output-path "sdks\python" `
        --config "scripts\python-sdk-config.yml"
    
    if ($LASTEXITCODE -ne 0) {
        throw "openapi-python-client failed"
    }
} catch {
    Write-Host "❌ Failed to generate Python SDK: $_" -ForegroundColor Red
    exit 1
}

# Install SDK locally for testing
Write-Host "Installing SDK locally for testing..." -ForegroundColor Cyan
Push-Location "sdks\python"
try {
    pip install -e .
    if ($LASTEXITCODE -ne 0) {
        throw "pip install failed"
    }
} finally {
    Pop-Location
}

Write-Host "✅ Python SDK generated successfully at sdks\python" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Review generated code in sdks\python\eva_api_client" -ForegroundColor White
Write-Host "  2. Run tests: cd sdks\python && pytest" -ForegroundColor White
Write-Host "  3. Build package: cd sdks\python && python setup.py sdist bdist_wheel" -ForegroundColor White
Write-Host "  4. Publish: twine upload dist/*" -ForegroundColor White
