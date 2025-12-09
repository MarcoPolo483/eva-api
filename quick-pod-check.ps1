# quick-pod-check.ps1
# Fast status check for POD agents (30 seconds)

$ErrorActionPreference = "SilentlyContinue"

Write-Host "`n⚡ QUICK POD STATUS CHECK" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════" -ForegroundColor DarkGray

# 1. GitHub Issues
Write-Host "`n📋 GitHub Issues:" -ForegroundColor Yellow
$issues = gh issue list --assignee "@me" --search "is:open [POD-" --json number,title 2>$null | ConvertFrom-Json
if ($issues) {
    Write-Host "   Open: $($issues.Count)" -ForegroundColor White
    $issues | ForEach-Object { Write-Host "   • #$($_.number): $($_.title)" -ForegroundColor Gray }
} else {
    Write-Host "   ✅ All POD issues closed!" -ForegroundColor Green
}

# 2. Recent Activity
Write-Host "`n🔄 Recent Activity (24h):" -ForegroundColor Yellow
$commits = git log --oneline --since="1 day ago" -5 2>$null
if ($commits) {
    $commits | ForEach-Object { Write-Host "   📝 $_" -ForegroundColor Gray }
} else {
    Write-Host "   No recent commits" -ForegroundColor Gray
}

# 3. Azure Resources
Write-Host "`n☁️  Azure Resources:" -ForegroundColor Yellow
$searchExists = az search service show --name eva-search-canadacentral --resource-group eva-suite-rg 2>$null
$functionExists = az functionapp show --name eva-document-ingestion --resource-group eva-suite-rg 2>$null

Write-Host "   Azure AI Search: " -NoNewline
Write-Host $(if ($searchExists) { "✅ Deployed" } else { "⏳ Pending" }) -ForegroundColor $(if ($searchExists) { "Green" } else { "Yellow" })

Write-Host "   Function App: " -NoNewline
Write-Host $(if ($functionExists) { "✅ Deployed" } else { "⏳ Pending" }) -ForegroundColor $(if ($functionExists) { "Green" } else { "Yellow" })

# 4. Production Status
Write-Host "`n🚀 Production:" -ForegroundColor Yellow
$health = Invoke-WebRequest -Uri "https://eva-api-marco-prod.azurewebsites.net/health" -UseBasicParsing 2>$null
Write-Host "   Health Check: " -NoNewline
Write-Host $(if ($health.StatusCode -eq 200) { "✅ OK" } else { "❌ Failed" }) -ForegroundColor $(if ($health.StatusCode -eq 200) { "Green" } else { "Red" })

# Summary
Write-Host "`n═══════════════════════════════════════════════" -ForegroundColor DarkGray
$timestamp = Get-Date -Format "HH:mm:ss"
Write-Host "⏱️  Checked at $timestamp" -ForegroundColor Cyan
Write-Host "`nFor detailed monitoring, run: .\monitor-pod-status.ps1" -ForegroundColor Gray
Write-Host "For validation checks, run: .\check-pod-deliverables.ps1`n" -ForegroundColor Gray
