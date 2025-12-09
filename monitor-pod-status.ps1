# monitor-pod-status.ps1
# POD Agent Execution Monitoring Dashboard
# Tracks GitHub Issues, commits, PRs, and Azure resources

param(
    [switch]$Continuous,
    [int]$IntervalSeconds = 300  # 5 minutes default
)

$ErrorActionPreference = "SilentlyContinue"

function Show-Header {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          POD AGENT MONITORING DASHBOARD                      ║" -ForegroundColor Cyan
    Write-Host "║          Timestamp: $timestamp                    ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
}

function Get-PODIssueStatus {
    Write-Host "`n[1] GitHub Issues Status" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    
    $issues = gh issue list --assignee "@me" --json number,title,state,comments,updatedAt | ConvertFrom-Json
    $podIssues = $issues | Where-Object { $_.title -match "^\[POD-[ILTD]\]" } | Sort-Object number
    
    foreach ($issue in $podIssues) {
        $stateIcon = if ($issue.state -eq "CLOSED") { "✅" } else { "🔄" }
        $stateColor = if ($issue.state -eq "CLOSED") { "Green" } else { "Yellow" }
        
        Write-Host "`n  $stateIcon Issue #$($issue.number): " -NoNewline -ForegroundColor $stateColor
        Write-Host $issue.title -ForegroundColor White
        Write-Host "     State: $($issue.state) | Comments: $($issue.comments.totalCount) | Updated: $($issue.updatedAt)" -ForegroundColor DarkGray
    }
    
    $closedCount = ($podIssues | Where-Object { $_.state -eq "CLOSED" }).Count
    $totalCount = $podIssues.Count
    $progress = if ($totalCount -gt 0) { [math]::Round(($closedCount / $totalCount) * 100, 0) } else { 0 }
    
    Write-Host "`n  Progress: $closedCount/$totalCount completed ($progress%)" -ForegroundColor Cyan
    
    return @{
        Total = $totalCount
        Closed = $closedCount
        Open = $totalCount - $closedCount
        Progress = $progress
    }
}

function Get-RecentCommits {
    Write-Host "`n[2] Recent Commits (POD-related)" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    
    $commits = git log --oneline --grep="POD-[ILTD]" --since="1 day ago" -10
    
    if ($commits) {
        $commits | ForEach-Object {
            Write-Host "  📝 $_" -ForegroundColor White
        }
    } else {
        Write-Host "  No POD-related commits in last 24 hours" -ForegroundColor DarkGray
    }
}

function Get-PullRequests {
    Write-Host "`n[3] Pull Requests" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    
    $prs = gh pr list --json number,title,state,author,createdAt | ConvertFrom-Json
    $podPRs = $prs | Where-Object { $_.title -match "POD-[ILTD]" }
    
    if ($podPRs) {
        foreach ($pr in $podPRs) {
            $stateIcon = switch ($pr.state) {
                "OPEN" { "🔄" }
                "MERGED" { "✅" }
                "CLOSED" { "❌" }
            }
            Write-Host "  $stateIcon PR #$($pr.number): $($pr.title)" -ForegroundColor White
            Write-Host "     Author: $($pr.author.login) | Created: $($pr.createdAt)" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  No POD-related pull requests" -ForegroundColor DarkGray
    }
}

function Get-AzureResources {
    Write-Host "`n[4] Azure Resources (POD-I Infrastructure)" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    
    # Check Azure AI Search
    $searchService = az search service show --name eva-search-canadacentral --resource-group eva-suite-rg 2>$null | ConvertFrom-Json
    if ($searchService) {
        Write-Host "  ✅ Azure AI Search: " -NoNewline -ForegroundColor Green
        Write-Host "$($searchService.name) (Status: $($searchService.status))" -ForegroundColor White
    } else {
        Write-Host "  ⏳ Azure AI Search: Not provisioned yet" -ForegroundColor Yellow
    }
    
    # Check Function App
    $functionApp = az functionapp show --name eva-document-ingestion --resource-group eva-suite-rg 2>$null | ConvertFrom-Json
    if ($functionApp) {
        Write-Host "  ✅ Function App: " -NoNewline -ForegroundColor Green
        Write-Host "$($functionApp.name) (State: $($functionApp.state))" -ForegroundColor White
    } else {
        Write-Host "  ⏳ Function App: Not deployed yet" -ForegroundColor Yellow
    }
}

function Get-TestResults {
    Write-Host "`n[5] CI/CD Test Runs (POD-T Validation)" -ForegroundColor Yellow
    Write-Host "─────────────────────────────────────────────────────────" -ForegroundColor DarkGray
    
    $runs = gh run list --limit 5 --json databaseId,displayTitle,conclusion,createdAt | ConvertFrom-Json
    
    if ($runs) {
        foreach ($run in $runs) {
            $icon = switch ($run.conclusion) {
                "success" { "✅" }
                "failure" { "❌" }
                "cancelled" { "⏸️" }
                default { "🔄" }
            }
            Write-Host "  $icon Run #$($run.databaseId): $($run.displayTitle)" -ForegroundColor White
            Write-Host "     Result: $($run.conclusion) | Created: $($run.createdAt)" -ForegroundColor DarkGray
        }
    } else {
        Write-Host "  No recent workflow runs" -ForegroundColor DarkGray
    }
}

function Show-Summary {
    param($IssueStatus)
    
    Write-Host "`n╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║                        SUMMARY                                ║" -ForegroundColor Cyan
    Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
    
    $status = if ($IssueStatus.Progress -eq 100) {
        "🎉 ALL POD AGENTS COMPLETED! Ready for final integration."
        $color = "Green"
    } elseif ($IssueStatus.Closed -gt 0) {
        "⚙️  Work in progress: $($IssueStatus.Open) PODs still active"
        $color = "Yellow"
    } else {
        "🚀 PODs launched, waiting for first completion..."
        $color = "Cyan"
    }
    
    Write-Host "`n  $status" -ForegroundColor $color
    
    Write-Host "`n  Next Steps:" -ForegroundColor White
    if ($IssueStatus.Progress -eq 100) {
        Write-Host "    • Run final integration tests" -ForegroundColor Gray
        Write-Host "    • Deploy to production (eva-api-marco-prod)" -ForegroundColor Gray
        Write-Host "    • Update documentation and notify stakeholders" -ForegroundColor Gray
    } else {
        Write-Host "    • Monitor GitHub Issues for updates" -ForegroundColor Gray
        Write-Host "    • Review comments and answer questions" -ForegroundColor Gray
        Write-Host "    • Validate deliverables as they're completed" -ForegroundColor Gray
    }
}

# Main execution
do {
    Clear-Host
    Show-Header
    
    $issueStatus = Get-PODIssueStatus
    Get-RecentCommits
    Get-PullRequests
    Get-AzureResources
    Get-TestResults
    Show-Summary -IssueStatus $issueStatus
    
    if ($Continuous) {
        Write-Host "`n⏱️  Next refresh in $IntervalSeconds seconds (Ctrl+C to stop)..." -ForegroundColor DarkGray
        Start-Sleep -Seconds $IntervalSeconds
    }
    
} while ($Continuous)

Write-Host "`n✅ Monitoring complete`n" -ForegroundColor Green
