param(
    [ValidateSet('prepare','run','status','verify')][string]$Action = 'status',
    [switch]$Network,
    [string]$Config = 'configs/data/financial_pdf_pipeline_v1.json',
    [string]$Python = ''
)
$ErrorActionPreference = 'Stop'
if (-not $Python) { $Python = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $env:PYTHONPATH = Join-Path $PWD 'src'
    $runnerArgs = @((Join-Path $PSScriptRoot 'financial_pdf_pipeline.py'), $Action, '--config', $Config)
    if ($Network) { $runnerArgs += '--network' }
    & $Python @runnerArgs
    $runnerExit = $LASTEXITCODE
} finally { Pop-Location }
exit $runnerExit
