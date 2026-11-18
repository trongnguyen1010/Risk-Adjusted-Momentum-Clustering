param(
    [ValidateSet('run','verify')][string]$Action='verify',
    [string]$Config='configs/data/financial_history_batch20_qa_v1.json',
    [string]$Python=''
)
$ErrorActionPreference='Stop'
if (-not $Python) { $Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    & $Python scripts/financial_history_batch_qa.py $Action --config $Config
    if ($LASTEXITCODE) { throw 'Financial history batch QA failed closed' }
} finally { Pop-Location }
