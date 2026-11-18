param(
    [ValidateSet('Status','Continue','Offline')][string]$Mode = 'Status',
    [string]$Python = 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$outputRoot = Join-Path $projectRoot 'data/financial/history_dstock_recovery_v4'
$state = Get-Content -LiteralPath (Join-Path $outputRoot 'pipeline-status.json') -Raw | ConvertFrom-Json
$config = Get-Content -LiteralPath (Join-Path $projectRoot 'configs/experiments/financial_dstock_recovery_v4.json') -Raw | ConvertFrom-Json
$refPath = Join-Path $outputRoot 'latest-result.json'
$summary = $null
if (Test-Path -LiteralPath $refPath) {
    $ref = Get-Content -LiteralPath $refPath -Raw | ConvertFrom-Json
    $summary = Get-Content -LiteralPath (Join-Path $projectRoot ($ref.path + '/summary.json')) -Raw | ConvertFrom-Json
}
if ($Mode -eq 'Status') {
    $allCasesReviewed = $summary -and $summary.processed_cases -ge 1647
    [pscustomobject]@{
        Phase = $(if ($allCasesReviewed) {'ALL_REMAINING_API_CASES_REVIEWED'} else {$state.phase})
        StageCandidates = $state.stage_limit
        StageCasesCompleted = $(if ($allCasesReviewed) {1647} else {$state.stage_completed})
        StageCasesTargeted = $(if ($allCasesReviewed) {1647} else {$state.stage_targets})
        StagePercent = $(if ($allCasesReviewed) {100} else {$state.stage_percent})
        Full10AtLastSeal = $(if ($summary) {$summary.full10_after} else {1002})
        NewCasesAtLastSeal = $(if ($summary) {$summary.processed_cases} else {0})
        TotalFreshCases = 1647
        LastCheckpointUpdatedUtc = $state.updated_at
        LogPath = (Join-Path $outputRoot 'worker.log')
    }
    return
}
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {throw 'Python runtime not found.'}
$env:PYTHONIOENCODING = 'utf-8'
if ($Mode -eq 'Continue') {
    if ([DateTimeOffset]::UtcNow.ToUnixTimeSeconds() -ge $config.authorization_deadline) {throw 'Network window expired; do not reset counters or deadline.'}
    if (($summary -and $summary.processed_cases -ge 1647) -or $state.phase -eq 'ALL_REMAINING_API_CASES_REVIEWED') {throw 'All fresh API cases were already attempted; use Status or Offline.'}
    & $Python (Join-Path $PSScriptRoot 'financial_dstock_remaining_campaign.py')
} else {
    if ($state.phase -eq 'ACQUISITION_QA') {throw 'Acquisition is active; use Status and avoid starting a second worker.'}
    & $Python (Join-Path $PSScriptRoot 'financial_dstock_recovery_v4.py') --config configs/experiments/financial_dstock_recovery_v4.json --limit 360
}
if ($LASTEXITCODE -ne 0) {throw "DStock remaining process exited with code $LASTEXITCODE."}
