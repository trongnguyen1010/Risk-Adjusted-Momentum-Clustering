param(
    [ValidateSet('doctor','plan','run','resume','report','verify')][string]$Action = 'doctor',
    [string]$Config = 'configs/data/financial_cafef_pilot5_execution_v1.json',
    [string]$Python = '',
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
    $runnerArgs = @((Join-Path $PSScriptRoot 'financial_cafef_pilot.py'), $Action, '--config', $Config)
    if ($Network) { $runnerArgs += '--network' }
    & $Python @runnerArgs
    $runnerExit = $LASTEXITCODE
} finally { Pop-Location }
exit $runnerExit
