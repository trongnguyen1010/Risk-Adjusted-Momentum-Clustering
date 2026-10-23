param(
    [ValidateSet('doctor','plan','regression','run','resume','qa','report','verify')][string]$Action = 'doctor',
    [string]$Config = 'configs/data/financial_history_pit_v1.json',
    [string]$Python = '',
    [ValidateRange(0,1600)][int]$MaxNetworkRequests = 25,
    [switch]$Network
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
    $bundledPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (Test-Path -LiteralPath $bundledPython) { $Python = $bundledPython }
    else { $Python = Join-Path $repoRoot '.venv\Scripts\python.exe' }
}
Push-Location $repoRoot
try {
    $runnerArgs = @((Join-Path $PSScriptRoot 'financial_history_pit.py'), $Action, '--config', $Config,
        '--max-network-requests', $MaxNetworkRequests)
    if ($Network) { $runnerArgs += '--network' }
    & $Python @runnerArgs
    $runnerExit = $LASTEXITCODE
} finally { Pop-Location }
exit $runnerExit
