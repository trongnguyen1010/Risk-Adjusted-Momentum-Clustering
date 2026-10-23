param([ValidateSet('Archive','Restore','Status')][string]$Mode='Status',[string]$Source='')
$ErrorActionPreference='Stop'
$projectRoot=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$auditRoot=Join-Path $projectRoot 'artifacts/repository/financial-history-storage-20261023'
$planPath=Join-Path $auditRoot 'plan.json'
$pinPath=Join-Path $auditRoot 'plan.sha256'
if (-not (Test-Path -LiteralPath $pinPath)) {throw 'Plan pin missing'}
if ((Get-FileHash -LiteralPath $planPath).Hash.ToLowerInvariant() -ne (Get-Content -LiteralPath $pinPath -Raw).Trim()) {throw 'Plan changed'}
$plan=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$archiveRoot=[IO.Path]::GetFullPath((Join-Path $projectRoot $plan.archive_root))
function Checked-Path([string]$relative) {
 if ([IO.Path]::IsPathRooted($relative) -or $relative.Contains(':') -or $relative -match '(^|/)\.\.(/|$)') {throw 'Unsafe relative path'}
 $p=[IO.Path]::GetFullPath((Join-Path $projectRoot $relative))
 if (-not $p.StartsWith($projectRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {throw 'Outside workspace'}
 $ancestor=$p
 while ($ancestor -and $ancestor -ne $projectRoot) {
  if ((Test-Path -LiteralPath $ancestor) -and ((Get-Item -LiteralPath $ancestor -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Reparse rejected'}
  $ancestor=Split-Path -Parent $ancestor
 }
 return $p
}
$rows=@($plan.targets | Where-Object { -not $Source -or $_.source -eq $Source })
if ($Source -and $rows.Count -ne 1) {throw 'Source must match one exact planned tree'}
if ($Mode -eq 'Status') {
 [pscustomobject]@{PlannedTrees=$rows.Count;InMainFolders=@($rows | Where-Object {Test-Path -LiteralPath (Join-Path $projectRoot $_.source)}).Count;InArchive=@($rows | Where-Object {Test-Path -LiteralPath (Join-Path $projectRoot $_.destination)}).Count};return
}
# Check final absolute source/destination roots before moving any tree.
foreach ($row in $rows) {
 $src=Checked-Path $row.source;$dst=Checked-Path $row.destination
 if ((Split-Path -Parent $src) -notin @((Join-Path $projectRoot 'data/financial'),(Join-Path $projectRoot 'artifacts/reports'))) {throw 'Source not a direct approved leaf'}
 if (-not $dst.StartsWith($archiveRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {throw 'Destination outside history archive'}
 if ([IO.Path]::GetPathRoot($src) -ne [IO.Path]::GetPathRoot($dst)) {throw 'Cross-volume move rejected'}
}
foreach ($row in $rows) {
 $from=Checked-Path $(if ($Mode -eq 'Archive') {$row.source} else {$row.destination})
 $to=Checked-Path $(if ($Mode -eq 'Archive') {$row.destination} else {$row.source})
 if (-not (Test-Path -LiteralPath $from) -and (Test-Path -LiteralPath $to)) {continue}
 if (-not (Test-Path -LiteralPath $from -PathType Container) -or (Test-Path -LiteralPath $to)) {throw 'Missing source or occupied destination; nothing overwritten'}
 if ($Mode -eq 'Restore') {
  & 'C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe' (Join-Path $PSScriptRoot 'financial_history_storage.py') check --source $row.source
  if ($LASTEXITCODE -ne 0) {throw 'Archive inventory check failed; restore refused'}
 }
 [void](New-Item -ItemType Directory -Path (Split-Path -Parent $to) -Force)
 Move-Item -LiteralPath $from -Destination $to
 [ordered]@{at_utc=[DateTime]::UtcNow.ToString('o');action=$Mode;source=$row.source;destination=$row.destination;files=$row.files} | ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $auditRoot 'moves.jsonl') -Encoding utf8
 Write-Output "$Mode $($row.source)"
}
