param(
    [ValidateSet('doctor','plan','run','verify','feedback')][string]$Action = 'doctor',
    [string]$Config = 'configs/data/financial_crawl_50_trial_v1.json',
    [string]$Output,
    [string]$Run,
    [string]$ResumeFrom,
    [switch]$ExecuteNetwork,
    [string]$Python
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$candidates = @()
if ($Python) { $candidates += $Python }
else {
    $candidates += (Join-Path $projectRoot '.venv\Scripts\python.exe')
    $command = Get-Command python -ErrorAction SilentlyContinue
    if ($command) { $candidates += $command.Source }
}
$selectedPython = $null
foreach ($candidate in $candidates) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    try { $probe = & $candidate -c 'import sys; print(sys.version_info >= (3,11))' 2>&1 }
    catch { continue }
    if ($LASTEXITCODE -eq 0 -and ($probe -join '').Trim() -eq 'True') {
        $selectedPython = $candidate
        break
    }
}
if (-not $selectedPython) {
    Write-Error 'Need Python >=3.11. Create .venv or pass -Python a working python.exe.'
    exit 3
}
$arguments = @((Join-Path $PSScriptRoot 'crawl_financial_trial.py'), $Action)
if ($Action -in @('verify','feedback')) {
    if (-not $Run) { throw '-Run is required' }
    $arguments += @('--run', $Run)
} else { $arguments += @('--config', $Config) }
if ($Action -eq 'run') {
    if (-not $Output) {
        $Output = 'data/financial/crawl_50_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff')
    }
    $arguments += @('--output', $Output)
    if ($ResumeFrom) { $arguments += @('--resume-from', $ResumeFrom) }
    if ($ExecuteNetwork) { $arguments += '--execute-network' }
    Write-Host ('Output: ' + $Output)
    Write-Host 'Keep this path for verify, feedback, or resume. Exit 2 means partial; exit 4 means hard-stop.'
}
if ($Action -eq 'feedback') {
    if (-not $Output) {
        $Output = 'artifacts/financial_crawler/feedback_50_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.zip'
    }
    $arguments += @('--output', $Output)
}
& $selectedPython @arguments
exit $LASTEXITCODE
