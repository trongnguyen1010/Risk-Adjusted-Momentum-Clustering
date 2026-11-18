param(
    [ValidateSet('plan','run','verify')][string]$Action='verify',
    [switch]$Network,
    [ValidateRange(0,15)][int]$MaxNewRequests=15,
    [string]$Python=''
)
$ErrorActionPreference='Stop'
if (-not $Python) {$Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'}
Push-Location (Split-Path -Parent $PSScriptRoot)
try {
    $metadataConfig=Get-Content -Raw -Encoding utf8 configs/data/financial_history20_metadata_v1.json | ConvertFrom-Json
    $workspaceRoot=[System.IO.Path]::GetFullPath($PWD.Path)
    $workerRoot=[System.IO.Path]::GetFullPath((Join-Path $workspaceRoot $metadataConfig.campaign_worker_root))
    if (-not $workerRoot.StartsWith($workspaceRoot+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)) {throw 'Worker folder outside project'}
    New-Item -ItemType Directory -Force -Path $workerRoot | Out-Null
    $metadataArgs=@('scripts/financial_history20_metadata.py',$Action,'--max-new-requests',"$MaxNewRequests")
    if ($Network) {$metadataArgs+='--network'}
    & $Python @metadataArgs
    if ($LASTEXITCODE) {throw 'Metadata flow failed closed'}
} finally {Pop-Location}
