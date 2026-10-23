param(
    [ValidateSet('plan','run','verify')][string]$Action='verify',
    [switch]$Network,
    [ValidateRange(0,180)][int]$MaxNewRequests=180,
    [string]$Python=''
)
$ErrorActionPreference='Stop'
if (-not $Python) { $Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $probeArgs=@('scripts/financial_history20_probes.py',$Action,'--max-new-requests',"$MaxNewRequests")
    if ($Network) { $probeArgs+='--network' }
    & $Python @probeArgs
    if ($LASTEXITCODE) { throw 'Financial template probes failed closed' }
} finally { Pop-Location }
