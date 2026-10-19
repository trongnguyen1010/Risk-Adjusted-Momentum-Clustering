param(
    [ValidateSet('plan','acquire','probe-ssi','review','verify')][string]$Action = 'plan',
    [string]$Config = 'configs/data/financial_provider_validation_v1.json',
    [string]$Output = '',
    [string]$Python = '',
    [switch]$Network
)
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not $Python) { $Python = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' }
Push-Location $repoRoot
try {
    $runnerArgs = @((Join-Path $PSScriptRoot 'financial_provider_validation.py'),$Action,'--config',$Config)
    if ($Network) { $runnerArgs += '--network' }
    if ($Output) { $runnerArgs += @('--output',$Output) }
    & $Python @runnerArgs
    $runnerExit = $LASTEXITCODE
} finally { Pop-Location }
exit $runnerExit
