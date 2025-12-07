# EVA API - Generate All Client SDKs
#
# Generates Python, TypeScript, and .NET client SDKs from the OpenAPI specification.
#
# Usage:
#   .\scripts\generate-sdks.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  EVA API - SDK Generation" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure API is running
Write-Host "Checking if API is running..." -ForegroundColor Yellow
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
Write-Host ""

$sdks = @("Python", "TypeScript", ".NET")
$scripts = @("generate-python-sdk.ps1", "generate-typescript-sdk.ps1", "generate-dotnet-sdk.ps1")
$failed = @()

for ($i = 0; $i -lt $sdks.Length; $i++) {
    $sdk = $sdks[$i]
    $script = $scripts[$i]
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host " Generating $sdk SDK" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    try {
        & ".\scripts\$script"
        if ($LASTEXITCODE -ne 0) {
            throw "$sdk SDK generation failed"
        }
    } catch {
        Write-Host "❌ $sdk SDK generation failed: $_" -ForegroundColor Red
        $failed += $sdk
    }
    
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " SDK Generation Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

if ($failed.Length -eq 0) {
    Write-Host "✅ All SDKs generated successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Generated SDKs:" -ForegroundColor Yellow
    Write-Host "  • Python: sdks\python\eva_api_client" -ForegroundColor White
    Write-Host "  • TypeScript: sdks\typescript\src" -ForegroundColor White
    Write-Host "  • .NET: sdks\dotnet\src\Eva.ApiClient" -ForegroundColor White
} else {
    Write-Host "⚠️  Some SDKs failed to generate:" -ForegroundColor Yellow
    foreach ($sdk in $failed) {
        Write-Host "  • $sdk" -ForegroundColor Red
    }
    exit 1
}
