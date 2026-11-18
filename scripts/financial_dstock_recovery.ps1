param(
    [ValidateSet('Status', 'Offline', 'Continue')]
    [string]$Mode = 'Status',
    [int]$Limit = 0,
    [string]$Python = 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$configPath = Join-Path $projectRoot 'configs/experiments/financial_dstock_recovery_v3.json'
$config = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$outputRoot = Join-Path $projectRoot $config.output_root
$statePath = Join-Path $outputRoot 'pipeline-status.json'
$state = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
$latest = Get-Content -LiteralPath (Join-Path $outputRoot 'latest-result.json') -Raw | ConvertFrom-Json
$summary = Get-Content -LiteralPath (Join-Path $projectRoot ($latest.path + '/summary.json')) -Raw | ConvertFrom-Json
$cashResultRefPath = Join-Path $projectRoot 'artifacts/reports/financial-dstock-gap-recovery-v1/cash-result-ref.json'
$hasCashReview = Test-Path -LiteralPath $cashResultRefPath -PathType Leaf
if ($hasCashReview) {
    $latest = Get-Content -LiteralPath $cashResultRefPath -Raw | ConvertFrom-Json
    $summary = Get-Content -LiteralPath (Join-Path $projectRoot ($latest.path + '/summary.json')) -Raw | ConvertFrom-Json
}
if ($Mode -eq 'Status') {
    [pscustomobject]@{
        Phase = $state.phase
        StageCandidates = $state.stage_limit
        CasesCompleted = $(if ($null -ne $state.stage_completed) { $state.stage_completed } else { $summary.processed_cases })
        CasesTargeted = $(if ($null -ne $state.stage_targets) { $state.stage_targets } else { $summary.processed_cases })
        StagePercent = $(if ($null -ne $state.stage_percent) { $state.stage_percent } else { 100 })
        Full10AtLastSeal = $summary.full10_after
        ReferenceRowsAtLastSeal = $summary.rows_after
        QAStatus = $summary.status
        ResultPath = (Join-Path $projectRoot $latest.path)
        LatestSymbols = ($state.latest_symbols -join ', ')
        UpdatedUtc = $state.updated_at
        LogPath = (Join-Path $outputRoot 'worker.log')
    }
    return
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Python runtime not found.' }
if ($Mode -eq 'Continue') {
    if ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -ge $config.authorization_deadline) {
        throw 'The authorized one-hour network window has expired; counters and deadline are retained.'
    }
    if ($summary.full10_after -gt 1000) { throw 'The coverage stop target was already reached. Use Status or Offline.' }
    $env:PYTHONIOENCODING = 'utf-8'
    & $Python (Join-Path $PSScriptRoot 'financial_dstock_campaign.py')
} else {
    if ($hasCashReview) {
        $env:PYTHONIOENCODING = 'utf-8'
        & $Python (Join-Path $PSScriptRoot 'financial_dstock_cash_review.py')
        if ($LASTEXITCODE -ne 0) { throw "Cash review exited with code $LASTEXITCODE." }
        return
    }
    if ($Limit -eq 0) { $Limit = [int]$summary.stage_limit }
    if ($Limit -lt 1 -or $Limit -gt 960) { throw 'Limit must be between 1 and 960.' }
    $env:PYTHONIOENCODING = 'utf-8'
    & $Python (Join-Path $PSScriptRoot 'financial_dstock_recovery_v3.py') --config configs/experiments/financial_dstock_recovery_v3.json --limit $Limit
}
if ($LASTEXITCODE -ne 0) { throw "DStock process exited with code $LASTEXITCODE." }
