param([ValidateSet('Status','Prune')][string]$Mode='Status')
$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$logRoot=Join-Path $projectRoot 'artifacts/repository/project-cleanup-20261023'
$planPath=Join-Path $logRoot 'plan.json'
$ready=Get-Content -LiteralPath (Join-Path $logRoot 'ready.json') -Raw | ConvertFrom-Json
if ((Get-FileHash -LiteralPath $planPath).Hash.ToLowerInvariant() -ne $ready.plan_sha256) {throw 'Plan hash changed'}
$plan=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
function Resolve-CleanupPath([string]$relative) {
    if ([IO.Path]::IsPathRooted($relative) -or $relative -match '(^|/)\.\.(/|$)' -or $relative.Contains(':')) {throw 'Unsafe relative path'}
    $path=[IO.Path]::GetFullPath((Join-Path $projectRoot $relative))
    if (-not $path.StartsWith($projectRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {throw 'Target outside project'}
    $ancestor=$path
    while ($ancestor -and $ancestor -ne $projectRoot) {
        if ((Test-Path -LiteralPath $ancestor) -and ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Reparse path rejected'}
        $ancestor=Split-Path -Parent $ancestor
    }
    return $path
}
$archive=Resolve-CleanupPath $ready.archive
if ((Get-FileHash -LiteralPath $archive).Hash.ToLowerInvariant() -ne $ready.archive_sha256) {throw 'Archive hash changed'}
foreach ($property in $plan.anchors.PSObject.Properties) {
    if ((Get-FileHash -LiteralPath (Resolve-CleanupPath $property.Name)).Hash.ToLowerInvariant() -ne $property.Value) {throw 'Active evidence anchor changed'}
}
if ($Mode -eq 'Status') { $ready; return }
$rows=@($plan.archive_files)+@($plan.cache_files)
# Validate all final absolute targets and hashes before deleting any file.
foreach ($row in $rows) {
    $path=Resolve-CleanupPath $row.path
    if ((Test-Path -LiteralPath $path) -and (Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant() -ne $row.sha256) {throw "Changed file: $($row.path)"}
}
$removed=0; $bytes=0L; $emptyParents=[Collections.Generic.HashSet[string]]::new()
foreach ($row in $rows) {
    $path=Resolve-CleanupPath $row.path
    if (Test-Path -LiteralPath $path -PathType Leaf) {
        Remove-Item -LiteralPath $path -Force
        $removed++;$bytes+=$row.bytes
        $parent=Split-Path -Parent $path
        while ($parent -ne $projectRoot -and $parent.StartsWith($projectRoot+[IO.Path]::DirectorySeparatorChar)) {
            [void]$emptyParents.Add($parent);$parent=Split-Path -Parent $parent
        }
    }
}
foreach ($folder in ($emptyParents | Sort-Object Length -Descending)) {
    if ((Test-Path -LiteralPath $folder -PathType Container) -and -not (Get-ChildItem -LiteralPath $folder -Force | Select-Object -First 1)) {
        Remove-Item -LiteralPath $folder -Force
    }
}
[pscustomobject]@{Status='PRUNED_VERIFIED_ARCHIVE_AND_REGENERABLE_CACHE';RemovedFiles=$removed;RemovedBytes=$bytes;Archive=$ready.archive;ArchiveSha256=$ready.archive_sha256;PlanSha256=$ready.plan_sha256} |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $logRoot 'prune-result.json') -Encoding utf8
Get-Content -LiteralPath (Join-Path $logRoot 'prune-result.json')
