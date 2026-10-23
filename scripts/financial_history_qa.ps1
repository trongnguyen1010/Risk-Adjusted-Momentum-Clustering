param(
    [ValidateSet('run','verify')][string]$Action = 'run',
    [string]$Config = 'configs/data/financial_history_qa_v1.json',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) {
    $Python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
}
$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot
try {
    & $Python (Join-Path $PSScriptRoot 'financial_history_qa.py') $Action '--config' $Config
    $runnerExit = $LASTEXITCODE
} finally { Pop-Location }
exit $runnerExit
