param(
    [ValidateSet('plan','run','verify')][string]$Action='verify',
    [switch]$Network,
    [ValidateRange(0,42000)][int]$MaxNewRequests=42000,
    [string]$Config='configs/data/financial_acquisition_total500_bulk_v1.json',
    [string]$Python=''
)
$ErrorActionPreference='Stop'
if (-not $Python) { $Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $batchArgs=@('scripts/financial_acquisition_bulk.py',$Action,'--config',$Config,'--max-new-requests',"$MaxNewRequests")
    if ($Network) { $batchArgs+='--network' }
    & $Python @batchArgs
    if ($LASTEXITCODE) { throw 'Acquisition-first collector failed closed' }
} finally { Pop-Location }
