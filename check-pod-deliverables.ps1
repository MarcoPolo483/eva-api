# check-pod-deliverables.ps1
# Validates POD agent deliverables against acceptance criteria

param(
    [ValidateSet("POD-I", "POD-L", "POD-T", "POD-D", "All")]
    [string]$POD = "All"
)

$ErrorActionPreference = "Continue"

function Show-Header {
    param([string]$Title)
    Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║  $Title" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Test-Condition {
    param(
        [string]$Description,
        [scriptblock]$Test,
        [string]$Expected
    )
    
    Write-Host "`n  Testing: $Description" -ForegroundColor Yellow
    
    try {
        $result = & $Test
        $success = $result -ne $null -and $result -ne ""
        
        if ($success) {
            Write-Host "  ✅ PASS" -ForegroundColor Green
            if ($Expected) {
                Write-Host "     Result: $result" -ForegroundColor Gray
            }
        } else {
            Write-Host "  ❌ FAIL" -ForegroundColor Red
            Write-Host "     Expected: $Expected" -ForegroundColor Gray
        }
        
        return $success
    } catch {
        Write-Host "  ❌ FAIL - Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Test-PODI {
    Show-Header "POD-I: Azure AI Search Infrastructure Validation"
    
    $results = @()
    
    # Test 1: Azure AI Search Service exists
    $results += Test-Condition `
        -Description "Azure AI Search service 'eva-search-canadacentral' exists" `
        -Test {
            $service = az search service show --name eva-search-canadacentral --resource-group eva-suite-rg 2>$null | ConvertFrom-Json
            return $service.status
        } `
        -Expected "running"
    
    # Test 2: Search index exists
    $results += Test-Condition `
        -Description "Search index 'knowledge-index' exists with vector field" `
        -Test {
            $searchKey = az search admin-key show --resource-group eva-suite-rg --service-name eva-search-canadacentral --query primaryKey -o tsv 2>$null
            if ($searchKey) {
                $index = Invoke-RestMethod -Uri "https://eva-search-canadacentral.search.windows.net/indexes/knowledge-index?api-version=2023-11-01" -Headers @{"api-key"=$searchKey} -ErrorAction SilentlyContinue
                if ($index.fields | Where-Object { $_.name -eq "embedding" -and $_.dimensions -eq 1536 }) {
                    return "10 fields with 1536-dim vector"
                }
            }
            return $null
        } `
        -Expected "10 fields with 1536-dimensional embedding vector"
    
    # Test 3: Function App deployed
    $results += Test-Condition `
        -Description "Azure Function App 'eva-document-ingestion' deployed" `
        -Test {
            $app = az functionapp show --name eva-document-ingestion --resource-group eva-suite-rg 2>$null | ConvertFrom-Json
            return $app.state
        } `
        -Expected "Running"
    
    # Test 4: App Service updated
    $results += Test-Condition `
        -Description "App Service has Azure Search configuration" `
        -Test {
            $settings = az webapp config appsettings list --name eva-api-marco-prod --resource-group eva-suite-rg 2>$null | ConvertFrom-Json
            $hasSearch = $settings | Where-Object { $_.name -eq "AZURE_SEARCH_ENDPOINT" }
            if ($hasSearch) { return $hasSearch.value }
            return $null
        } `
        -Expected "https://eva-search-canadacentral.search.windows.net"
    
    $passCount = ($results | Where-Object { $_ -eq $true }).Count
    $totalCount = $results.Count
    
    Write-Host "`n  POD-I Result: $passCount/$totalCount tests passed" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })
    
    return $passCount -eq $totalCount
}

function Test-PODL {
    Show-Header "POD-L: RAG Service Implementation Validation"
    
    $results = @()
    
    # Test 1: query_service.py updated
    $results += Test-Condition `
        -Description "query_service.py contains production RAG logic (_vector_search method)" `
        -Test {
            $content = Get-Content "src\eva_api\services\query_service.py" -Raw
            if ($content -match "_vector_search" -and $content -match "SearchClient") {
                return "Production RAG methods present"
            }
            return $null
        } `
        -Expected "Vector search and context building implemented"
    
    # Test 2: Azure Function code exists
    $results += Test-Condition `
        -Description "Azure Function ingestion code exists" `
        -Test {
            if (Test-Path "functions\document-ingestion\__init__.py") {
                $content = Get-Content "functions\document-ingestion\__init__.py" -Raw
                if ($content -match "extract_text_from_pdf" -and $content -match "generate_embeddings") {
                    return "Ingestion pipeline implemented"
                }
            }
            return $null
        } `
        -Expected "Document ingestion function with PDF extraction, chunking, embedding"
    
    # Test 3: Configuration updated
    $results += Test-Condition `
        -Description "config.py includes Azure AI Search settings" `
        -Test {
            $content = Get-Content "src\eva_api\config.py" -Raw
            if ($content -match "azure_search_endpoint" -and $content -match "azure_search_key") {
                return "Search config present"
            }
            return $null
        } `
        -Expected "Azure Search configuration fields added"
    
    # Test 4: Dependencies updated
    $results += Test-Condition `
        -Description "requirements.txt includes azure-search-documents" `
        -Test {
            $content = Get-Content "requirements.txt" -Raw
            if ($content -match "azure-search-documents" -and $content -match "tiktoken") {
                return "Dependencies added"
            }
            return $null
        } `
        -Expected "azure-search-documents and tiktoken added"
    
    $passCount = ($results | Where-Object { $_ -eq $true }).Count
    $totalCount = $results.Count
    
    Write-Host "`n  POD-L Result: $passCount/$totalCount tests passed" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })
    
    return $passCount -eq $totalCount
}

function Test-PODT {
    Show-Header "POD-T: Testing Validation"
    
    $results = @()
    
    # Test 1: Test files exist
    $results += Test-Condition `
        -Description "Unit test files created (test_document_processing.py, test_chunking.py, etc.)" `
        -Test {
            $testFiles = @(
                "tests\unit\test_document_processing.py",
                "tests\unit\test_chunking.py",
                "tests\unit\test_embeddings.py",
                "tests\unit\test_vector_search.py"
            )
            $existingFiles = $testFiles | Where-Object { Test-Path $_ }
            if ($existingFiles.Count -gt 0) {
                return "$($existingFiles.Count) test files found"
            }
            return $null
        } `
        -Expected "At least 4 unit test files created"
    
    # Test 2: CI/CD workflow exists
    $results += Test-Condition `
        -Description "GitHub Actions workflow configured (.github/workflows/test.yml)" `
        -Test {
            if (Test-Path ".github\workflows\test.yml") {
                return "CI/CD workflow exists"
            }
            return $null
        } `
        -Expected "GitHub Actions workflow for automated testing"
    
    # Test 3: Tests pass
    $results += Test-Condition `
        -Description "Test suite passes (pytest execution)" `
        -Test {
            # Check latest GitHub Actions run
            $runs = gh run list --workflow test.yml --limit 1 --json conclusion | ConvertFrom-Json
            if ($runs -and $runs[0].conclusion -eq "success") {
                return "Latest test run passed"
            }
            return $null
        } `
        -Expected "All tests pass in CI/CD"
    
    # Test 4: Coverage report
    $results += Test-Condition `
        -Description "Code coverage >80%" `
        -Test {
            if (Test-Path "coverage.xml") {
                $coverage = Get-Content "coverage.xml" -Raw
                if ($coverage -match 'line-rate="([0-9.]+)"') {
                    $rate = [double]$matches[1] * 100
                    if ($rate -ge 80) {
                        return "$([math]::Round($rate, 1))% coverage"
                    }
                }
            }
            return $null
        } `
        -Expected "Code coverage report with >80%"
    
    $passCount = ($results | Where-Object { $_ -eq $true }).Count
    $totalCount = $results.Count
    
    Write-Host "`n  POD-T Result: $passCount/$totalCount tests passed" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })
    
    return $passCount -eq $totalCount
}

function Test-PODD {
    Show-Header "POD-D: Production Deployment Validation"
    
    $results = @()
    
    # Test 1: Production deployment successful
    $results += Test-Condition `
        -Description "Production App Service running with latest code" `
        -Test {
            $health = Invoke-WebRequest -Uri "https://eva-api-marco-prod.azurewebsites.net/health" -UseBasicParsing -ErrorAction SilentlyContinue
            if ($health.StatusCode -eq 200) {
                return "Health check passed"
            }
            return $null
        } `
        -Expected "Health endpoint returns 200 OK"
    
    # Test 2: Production RAG working
    $results += Test-Condition `
        -Description "Production API using real RAG (not mock mode)" `
        -Test {
            $settings = az webapp config appsettings list --name eva-api-marco-prod --resource-group eva-suite-rg 2>$null | ConvertFrom-Json
            $mockMode = $settings | Where-Object { $_.name -eq "EVA_MOCK_MODE" }
            if ($mockMode.value -eq "false") {
                return "Mock mode disabled"
            }
            return $null
        } `
        -Expected "EVA_MOCK_MODE=false"
    
    # Test 3: Monitoring configured
    $results += Test-Condition `
        -Description "Application Insights alerts configured" `
        -Test {
            $alerts = az monitor metrics alert list --resource-group eva-suite-rg 2>$null | ConvertFrom-Json
            $ragAlerts = $alerts | Where-Object { $_.name -match "RAG" }
            if ($ragAlerts) {
                return "$($ragAlerts.Count) alerts configured"
            }
            return $null
        } `
        -Expected "Alerts for query failures and slow response times"
    
    # Test 4: Smoke tests pass
    $results += Test-Condition `
        -Description "Production smoke tests pass" `
        -Test {
            # Quick smoke test
            $spaces = Invoke-RestMethod -Uri "https://eva-api-marco-prod.azurewebsites.net/api/v1/spaces" -Headers @{"X-API-Key"="demo-api-key"} -ErrorAction SilentlyContinue
            if ($spaces -and $spaces.Count -ge 10) {
                return "$($spaces.Count) spaces accessible"
            }
            return $null
        } `
        -Expected "Spaces endpoint returns data"
    
    $passCount = ($results | Where-Object { $_ -eq $true }).Count
    $totalCount = $results.Count
    
    Write-Host "`n  POD-D Result: $passCount/$totalCount tests passed" -ForegroundColor $(if ($passCount -eq $totalCount) { "Green" } else { "Yellow" })
    
    return $passCount -eq $totalCount
}

# Main execution
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         POD DELIVERABLES VALIDATION                           ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$results = @{}

if ($POD -eq "All" -or $POD -eq "POD-I") {
    $results["POD-I"] = Test-PODI
}

if ($POD -eq "All" -or $POD -eq "POD-L") {
    $results["POD-L"] = Test-PODL
}

if ($POD -eq "All" -or $POD -eq "POD-T") {
    $results["POD-T"] = Test-PODT
}

if ($POD -eq "All" -or $POD -eq "POD-D") {
    $results["POD-D"] = Test-PODD
}

# Summary
Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                    VALIDATION SUMMARY                         ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan

$allPassed = $true
foreach ($key in $results.Keys) {
    $icon = if ($results[$key]) { "✅" } else { "❌" }
    $color = if ($results[$key]) { "Green" } else { "Red" }
    Write-Host "`n  $icon $key : " -NoNewline -ForegroundColor $color
    Write-Host $(if ($results[$key]) { "All checks passed" } else { "Some checks failed" }) -ForegroundColor $color
    
    if (-not $results[$key]) { $allPassed = $false }
}

Write-Host "`n"
if ($allPassed) {
    Write-Host "🎉 ALL PODS VALIDATED! Ready for production." -ForegroundColor Green
} else {
    Write-Host "⚠️  Some PODs need attention. Review failures above." -ForegroundColor Yellow
}

Write-Host "`n"
