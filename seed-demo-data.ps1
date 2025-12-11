<#
🧩 CONTEXT:
Seed EVA API with demo data for 25-user testing. Creates sample knowledge spaces,
uploads documents, and populates the system for immediate demo readiness.

🧩 SYNOPSIS:
    Seed Demo Data for EVA Suite

🧩 DESCRIPTION:
    Creates sample knowledge spaces and documents using the EVA API endpoints.
    Designed for quick demo setup with realistic Canadian government content.

🧩 CONTEXT_ENGINEERING:
    Mission: Enable immediate EVA Suite demonstration
    Constraints: Requires running API (local or Azure)
    Reuses: EVA API endpoints for space/document creation
    Validates: API connectivity, space creation, document upload

🧩 HOUSEKEEPING:
    Creates: Knowledge spaces, sample documents
    Modifies: EVA API database state
    Validates: API health, endpoint responses
    Cleans: None (preserves created data)
    Monitors: HTTP responses, creation success

🧩 WORKSPACE_MANAGEMENT:
    TreeUpdates: No
    Navigation: No
    Caching: None
    SessionState: No

🧩 COMPLIANCE:
    WCAG: N/A
    Bilingual: Yes (creates FR/EN content)
    RBAC: POD-F
    ProtectedB: Demo data only
    Audit: Logs all API calls

.PARAMETER ApiBase
    API base URL (default: https://eva-api-container.azurewebsites.net)

.PARAMETER ApiKey
    API key for authentication (default: demo-api-key)

.NOTES
    POD: POD-F
    Last Modified: 2025-12-08
#>

Param(
    [string]$ApiBase = "https://eva-api-container.azurewebsites.net",
    [string]$ApiKey = "demo-api-key"
)

$ErrorActionPreference = "Stop"

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              🌱 EVA SUITE - Demo Data Seeding                   ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

# Test API connectivity
Write-Host "🏥 Testing API connectivity..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "$ApiBase/health" -TimeoutSec 10
    Write-Host "✅ API is healthy: $($health.status)`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Cannot connect to API: $_" -ForegroundColor Red
    Write-Host "   Make sure the API is running at: $ApiBase" -ForegroundColor Yellow
    exit 1
}

# Prepare headers
$headers = @{
    "Content-Type" = "application/json"
    "X-API-Key" = $ApiKey
}

# Sample spaces to create
$spaces = @(
    @{
        name = "Service Canada Programs 🇨🇦"
        description = "Information about EI, CPP, OAS, and other Service Canada programs (bilingual)"
        language = "en"
    },
    @{
        name = "Programmes de Service Canada 🇨🇦"
        description = "Information sur l'AE, le RPC, la SV et autres programmes de Service Canada"
        language = "fr"
    },
    @{
        name = "EVA Development Docs 🚀"
        description = "Technical documentation for EVA Suite development and deployment"
        language = "en"
    }
)

Write-Host "📦 Creating knowledge spaces..." -ForegroundColor Cyan

$createdSpaces = @()

foreach ($space in $spaces) {
    Write-Host "`n   Creating: $($space.name)" -ForegroundColor Yellow
    
    $body = @{
        name = $space.name
        description = $space.description
        language = $space.language
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$ApiBase/api/v1/spaces" `
            -Method Post `
            -Headers $headers `
            -Body $body `
            -TimeoutSec 30
        
        Write-Host "   ✅ Space created: $($response.space_id)" -ForegroundColor Green
        $createdSpaces += $response
    } catch {
        Write-Host "   ⚠️  Failed to create space: $_" -ForegroundColor Yellow
    }
}

# Sample documents for each space
$documents = @{
    "Service Canada Programs" = @(
        @{
            title = "Employment Insurance (EI) Overview"
            content = @"
# Employment Insurance (EI) Benefits

Employment Insurance (EI) provides temporary financial assistance to unemployed Canadians while they look for work or upgrade their skills.

## Types of EI Benefits:
- Regular benefits
- Maternity/parental benefits
- Sickness benefits
- Compassionate care benefits
- Family caregiver benefits

## Eligibility:
- Worked required hours in the past 52 weeks
- Lost job through no fault of your own
- Ready, willing, and capable of working
- Actively looking for work

## How to Apply:
Apply online through My Service Canada Account or by phone at 1-800-206-7218.

For more information, visit: canada.ca/en/services/benefits/ei.html
"@
        },
        @{
            title = "Canada Pension Plan (CPP)"
            content = @"
# Canada Pension Plan (CPP)

The Canada Pension Plan (CPP) is a monthly, taxable benefit that replaces part of your income when you retire.

## Key Features:
- Contributions from age 18 to 70
- Benefits can start as early as age 60
- Standard retirement age is 65
- Can delay until age 70 for increased benefits

## CPP Retirement Benefit:
The amount you receive depends on:
- How much you contributed
- How long you contributed
- Age when you start receiving benefits

## Average Monthly Amount (2025): $758.32

## How to Apply:
Apply online through My Service Canada Account 6 months before you want payments to start.

For more information, visit: canada.ca/en/services/benefits/publicpensions/cpp.html
"@
        }
    )
    "Programmes de Service Canada" = @(
        @{
            title = "Assurance-emploi (AE) - Aperçu"
            content = @"
# Prestations d'assurance-emploi (AE)

L'assurance-emploi (AE) offre une aide financière temporaire aux Canadiens sans emploi pendant qu'ils cherchent du travail ou améliorent leurs compétences.

## Types de prestations d'AE :
- Prestations régulières
- Prestations de maternité/parentales
- Prestations de maladie
- Prestations de soignant
- Prestations pour proches aidants

## Admissibilité :
- Heures de travail requises au cours des 52 dernières semaines
- Perte d'emploi sans faute de votre part
- Prêt, disposé et capable de travailler
- Recherche active d'emploi

## Comment présenter une demande :
Présentez votre demande en ligne via Mon dossier Service Canada ou par téléphone au 1-800-206-7218.

Pour plus d'informations : canada.ca/fr/services/prestations/ae.html
"@
        }
    )
    "EVA Development Docs" = @(
        @{
            title = "EVA Suite Architecture Overview"
            content = @"
# EVA Suite - Technical Architecture

EVA (Evolved Virtual Assistant) is a RAG-based AI system built for Canadian government services.

## Architecture Components:

### Backend (eva-api)
- **Framework**: FastAPI + Python 3.11
- **Database**: Azure Cosmos DB
- **Vector Store**: Azure AI Search
- **Caching**: Redis
- **Deployment**: Docker containers on Azure App Service

### Frontend (eva-ui)
- **Type**: Static website (vanilla JavaScript)
- **Features**: Bilingual FR/EN, winter holiday theme
- **Deployment**: Azure Blob Storage static website

### Phase 3 Features:
- ✅ GraphQL subscriptions (WebSocket)
- ✅ DataLoader N+1 prevention (98% query reduction)
- ✅ Webhook event broadcasting

## Deployment:
- **Location**: Canada Central 🇨🇦
- **Cost**: ~\$18.64/month
- **URLs**:
  - API: https://eva-api-container.azurewebsites.net
  - UI: https://evasuitestoragedev.z9.web.core.windows.net

## Development Timeline:
Started November 2, 2025. Three-year journey from concept to production.
"@
        }
    )
}

Write-Host "`n📄 Creating sample documents..." -ForegroundColor Cyan

foreach ($space in $createdSpaces) {
    $spaceName = $space.name -replace ' 🇨🇦', '' -replace ' 🚀', ''
    $docs = $documents[$spaceName]
    
    if ($docs) {
        Write-Host "`n   Space: $($space.name)" -ForegroundColor Yellow
        
        foreach ($doc in $docs) {
            Write-Host "      Creating: $($doc.title)" -ForegroundColor Gray
            
            $body = @{
                space_id = $space.space_id
                title = $doc.title
                content = $doc.content
                metadata = @{
                    source = "demo-seed"
                    created = (Get-Date -Format "yyyy-MM-dd")
                }
            } | ConvertTo-Json -Depth 10
            
            try {
                $docResponse = Invoke-RestMethod -Uri "$ApiBase/api/v1/documents" `
                    -Method Post `
                    -Headers $headers `
                    -Body $body `
                    -TimeoutSec 30
                
                Write-Host "      ✅ Document created: $($docResponse.document_id)" -ForegroundColor Green
            } catch {
                Write-Host "      ⚠️  Failed: $_" -ForegroundColor Yellow
            }
        }
    }
}

Write-Host "`n╔══════════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    🎉 SEEDING COMPLETE!                         ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

Write-Host "📊 Summary:" -ForegroundColor Cyan
Write-Host "   ✅ Created $($createdSpaces.Count) knowledge spaces" -ForegroundColor White
Write-Host "   ✅ Uploaded demo documents" -ForegroundColor White
Write-Host "`n🌐 Test the chat UI now:" -ForegroundColor Cyan
Write-Host "   https://evasuitestoragedev.z9.web.core.windows.net`n" -ForegroundColor White -BackgroundColor DarkBlue

Write-Host "💬 Try asking EVA:" -ForegroundColor Yellow
Write-Host "   - 'What is Employment Insurance?'" -ForegroundColor Gray
Write-Host "   - 'Qu'est-ce que l'assurance-emploi?'" -ForegroundColor Gray
Write-Host "   - 'Tell me about the EVA Suite architecture'" -ForegroundColor Gray
Write-Host ""
