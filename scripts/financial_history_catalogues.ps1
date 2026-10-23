param(
    [ValidateSet('plan','run','verify')][string]$Action='verify',
    [switch]$Network,
    [ValidateRange(0,15)][int]$MaxNewRequests=15,
    [string]$Python=''
)
$ErrorActionPreference='Stop'
if (-not $Python) { $Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $catalogueArgs=@('scripts/financial_history_catalogues.py',$Action,'--max-new-requests',"$MaxNewRequests")
    if ($Network) { $catalogueArgs+='--network' }
    & $Python @catalogueArgs
    if ($LASTEXITCODE) { throw 'Public financial catalogues failed closed' }
} finally { Pop-Location }
