param([ValidateSet('Run','Status')][string]$Mode='Status', [string]$Python='C:/Users/ASUS/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe')
$ErrorActionPreference='Stop'
$root=[IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$audit=Join-Path $root 'artifacts/repository/financial-cache-archive-20261023'
$planPath=Join-Path $audit 'plan.json'
$plan=Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$script=Join-Path $PSScriptRoot 'financial_cache_archive.py'
$env:PYTHONIOENCODING='utf-8'
if ($Mode -eq 'Status') { & $Python $script status; return }
foreach ($target in $plan.targets) {
    $batch=$target.label
    $resultPath=Join-Path $audit ($batch+'-pruned.json')
    $cachePath=[IO.Path]::GetFullPath((Join-Path $root $target.root))
    $expected=[IO.Path]::GetFullPath((Join-Path $root ('data/financial/'+[IO.Path]::GetFileName([IO.Path]::GetDirectoryName($target.root))+'/candidates')))
    $financialRoot=[IO.Path]::GetFullPath((Join-Path $root 'data/financial'))
    if ($cachePath -ne $expected -or -not $cachePath.StartsWith($financialRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase) -or (Split-Path -Leaf $cachePath) -ne 'candidates') {throw 'Unsafe cache destination'}
    if (Test-Path -LiteralPath $resultPath) {
        if (Test-Path -LiteralPath $cachePath) {throw 'Cache reappeared after prune; review before rerun'}
        continue
    }
    $packedPath=Join-Path $audit ($batch+'-packed.json')
    if (Test-Path -LiteralPath $packedPath) { & $Python $script verify --batch $batch }
    else { & $Python $script pack --batch $batch }
    if ($LASTEXITCODE -ne 0) {throw "Archive/verification failed for $batch; source retained"}
    $ready=Get-Content -LiteralPath (Join-Path $audit ($batch+'-ready.json')) -Raw | ConvertFrom-Json
    if ($ready.status -ne 'ARCHIVE_AND_SOURCE_VERIFIED' -or $ready.root -ne $target.root -or $ready.absolute_root -ne $cachePath) {throw 'Ready/source mismatch'}
    if ((Get-FileHash -LiteralPath $planPath).Hash.ToLowerInvariant() -ne $ready.plan_sha256) {throw 'Plan changed'}
    $archivePath=[IO.Path]::GetFullPath((Join-Path $root $ready.archive))
    $archiveRoot=[IO.Path]::GetFullPath((Join-Path $root 'artifacts/archives'))
    if (-not $archivePath.StartsWith($archiveRoot+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) {throw 'Archive outside workspace archive root'}
    if ((Get-FileHash -LiteralPath $archivePath).Hash.ToLowerInvariant() -ne $ready.archive_sha256) {throw 'Archive changed'}
    foreach ($path in @($cachePath,(Split-Path -Parent $cachePath),$financialRoot)) {
        if ((Get-Item -LiteralPath $path -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Reparse path rejected'}
    }
    # All paths and archive bytes checked; only this exact derived-cache subtree.
    Remove-Item -LiteralPath $cachePath -Recurse -Force
    if (Test-Path -LiteralPath $cachePath) {throw 'Prune incomplete'}
    [ordered]@{status='PRUNED_VERIFIED_DERIVED_CACHE';batch=$batch;root=$target.root;files=$target.files;bytes=$target.bytes;archive=$ready.archive;archive_sha256=$ready.archive_sha256;plan_sha256=$ready.plan_sha256;at_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content -LiteralPath $resultPath -Encoding utf8
    Write-Output "PRUNED batch=$batch files=$($target.files)"
}
Write-Output 'ALL_FOUR_DERIVED_CACHES_ARCHIVED_AND_PRUNED'
