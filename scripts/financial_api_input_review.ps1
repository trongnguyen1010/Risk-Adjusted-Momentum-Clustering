param(
    [string]$PythonExecutable = "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe",
    [string]$Config = 'configs/data/financial_api_input_review1522_v1.json'
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath $PythonExecutable)) {
    throw "Python executable not found: $PythonExecutable"
}
Push-Location -LiteralPath $projectRoot
try {
    $env:PYTHONIOENCODING = 'utf-8'
    & $PythonExecutable -u 'scripts/financial_api_input_review.py' --config $Config
    if ($LASTEXITCODE -ne 0) { throw "Offline API input review failed: exit $LASTEXITCODE" }
} finally {
    Pop-Location
}
