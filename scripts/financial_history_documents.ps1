param(
    [ValidateSet('prepare','run','extract','verify')][string]$Action = 'prepare',
    [switch]$Network,
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) { $Python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $runnerArgs = @((Join-Path $PSScriptRoot 'financial_history_documents.py'), $Action)
    if ($Network) { $runnerArgs += '--network' }
    & $Python @runnerArgs
    $runnerExit = $LASTEXITCODE
} finally { Pop-Location }
exit $runnerExit
