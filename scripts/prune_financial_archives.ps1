param(
    [string]$Ready = 'artifacts/archives/financial-cleanup-20261008-v1/prune-ready.json',
    [string]$Log = 'artifacts/archives/financial-cleanup-20261008-v1/prune-log.jsonl'
)
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
$financialRoot = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'data/financial')).Path
$readyPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $Ready))
$archiveRoot = [IO.Path]::GetFullPath((Join-Path $projectRoot 'artifacts/archives'))
if (-not $readyPath.StartsWith($archiveRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Ready file outside archives' }
$plan = Get-Content -LiteralPath $readyPath -Raw | ConvertFrom-Json
if ($plan.status -ne 'ALL_ARCHIVES_AND_SOURCE_HASHES_VERIFIED') { throw 'Archive/source verification required' }
$logPath = [IO.Path]::GetFullPath((Join-Path $projectRoot $Log))
if (-not $logPath.StartsWith($archiveRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Log outside archives' }
if (Test-Path -LiteralPath $logPath) { throw 'Prune log already exists; do not repeat blindly' }
# Validate every absolute leaf before any recursive deletion.
foreach ($target in $plan.targets) {
    $resolved = (Resolve-Path -LiteralPath $target.absolute_path).Path
    if ($target.status -ne 'PRUNE_READY' -or (Split-Path -Parent $resolved) -ne $financialRoot -or (Split-Path -Leaf $resolved) -ne $target.name) { throw 'Invalid target outside financial leaf directory' }
    if ((Get-Item -LiteralPath $resolved).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse target forbidden' }
}
foreach ($target in $plan.targets) {
    Remove-Item -LiteralPath $target.absolute_path -Recurse -Force
    $record = [ordered]@{ at = [DateTime]::UtcNow.ToString('o'); name = $target.name; action = 'REMOVED_VERIFIED_ARCHIVED_TREE'; archive_sha256 = $target.archive_sha256 }
    $record | ConvertTo-Json -Compress | Add-Content -LiteralPath $logPath -Encoding utf8
    Write-Output $target.name
}
