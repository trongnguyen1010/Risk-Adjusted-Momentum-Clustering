param([string]$Config = 'configs/data/financial_recovery_readiness_v1.json')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$runtimePython = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe'
& $runtimePython (Join-Path $PSScriptRoot 'financial_recovery_readiness.py') --config $Config
if ($LASTEXITCODE -ne 0) { throw 'Financial recovery readiness failed' }
