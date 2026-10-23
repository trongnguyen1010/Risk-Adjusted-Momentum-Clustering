param(
    [ValidateSet('plan','run','verify')][string]$Action='verify',
    [switch]$Network,
    [ValidateRange(0,2100)][int]$MaxNewRequests=200,
    [string]$Python=''
)
$ErrorActionPreference='Stop'
if (-not $Python) { $Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $batchArgs=@('scripts/financial_history_batch.py',$Action,'--max-new-requests',"$MaxNewRequests")
    if ($Network) { $batchArgs+='--network' }
    & $Python @batchArgs
    if ($LASTEXITCODE) { throw 'F3 history successor failed closed' }
} finally { Pop-Location }
