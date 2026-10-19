param(
    [ValidateSet('acquire','run','verify')][string]$Action = 'run',
    [string]$Config = 'configs/data/financial_pilot5_completion_v1.json',
    [string]$Review = '',
    [string]$Output = '',
    [string]$Python = '',
    [switch]$Network
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) {
    $Python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
    if (-not (Test-Path -LiteralPath $Python)) { $Python = Join-Path $repoRoot '.venv\Scripts\python.exe' }
}
Push-Location $repoRoot
try {
    $runnerArgs = @((Join-Path $PSScriptRoot 'financial_pilot_completion.py'), $Action, '--config', $Config)
    if ($Review) { $runnerArgs += @('--review', $Review) }
    if ($Output) { $runnerArgs += @('--output', $Output) }
    if ($Network) { $runnerArgs += '--network' }
    & $Python @runnerArgs
    $runnerExit = $LASTEXITCODE
} finally { Pop-Location }
exit $runnerExit
