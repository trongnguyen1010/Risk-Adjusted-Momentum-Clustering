param([Parameter(Mandatory=$true)][string]$PlanPath)
$ErrorActionPreference = 'Stop'
$planFile = (Resolve-Path -LiteralPath $PlanPath).Path
$plan = Get-Content -LiteralPath $planFile -Raw -Encoding utf8 | ConvertFrom-Json
$workspace = [IO.Path]::GetFullPath($plan.workspace).TrimEnd([IO.Path]::DirectorySeparatorChar)
if (-not (Test-Path -LiteralPath (Join-Path $workspace 'AGENTS.md'))) { throw 'Missing workspace marker' }
$prefix = $workspace + [IO.Path]::DirectorySeparatorChar
$checked = @()
foreach ($entry in $plan.entries) {
    $source = [IO.Path]::GetFullPath((Join-Path $workspace $entry.old))
    $target = [IO.Path]::GetFullPath((Join-Path $workspace $entry.new))
    if (-not $source.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase) -or -not $target.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside workspace' }
    if ([IO.Path]::GetPathRoot($source) -ne [IO.Path]::GetPathRoot($target)) { throw 'Same volume required' }
    $item = Get-Item -LiteralPath $source -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Source already a reparse point: $source" }
    if (Test-Path -LiteralPath $target) { throw "Target exists: $target" }
    if ($entry.kind -eq 'MOVE_FILE_KEEP_HARDLINK') {
        if ($item.PSIsContainer -or (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) { throw 'File hash mismatch' }
    } elseif ($entry.kind -ne 'NEW_DIRECTORY_JUNCTION' -or -not $item.PSIsContainer) { throw 'Unknown entry kind' }
    $checked += [pscustomobject]@{ Source=$source; Target=$target; Kind=$entry.kind }
}
$journal = Join-Path ([IO.Path]::GetDirectoryName($planFile)) 'operations.jsonl'
if (Test-Path -LiteralPath $journal) { throw 'Refuse rerun; inspect existing operation journal' }
$done = 0
foreach ($entry in $checked) {
    New-Item -ItemType Directory -Path ([IO.Path]::GetDirectoryName($entry.Target)) -Force | Out-Null
    if ($entry.Kind -eq 'NEW_DIRECTORY_JUNCTION') {
        # New domain path points at the old immutable directory; no data move.
        New-Item -ItemType Junction -Path $entry.Target -Target $entry.Source | Out-Null
    } else {
        Move-Item -LiteralPath $entry.Source -Destination $entry.Target
        try {
            New-Item -ItemType HardLink -Path $entry.Source -Target $entry.Target | Out-Null
        } catch {
            # Both absolute paths were checked above; restore the original path.
            Move-Item -LiteralPath $entry.Target -Destination $entry.Source
            throw
        }
    }
    $done++
    [pscustomobject]@{Source=$entry.Source;Target=$entry.Target;Kind=$entry.Kind;Status='DONE'} | ConvertTo-Json -Compress | Add-Content -LiteralPath $journal -Encoding utf8
    if ($done % 30 -eq 0) { Write-Output "CONSOLIDATED $done / $($checked.Count)" }
}
Write-Output "CONSOLIDATION_DONE $done"
