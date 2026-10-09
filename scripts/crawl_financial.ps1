param(
    [ValidateSet('doctor','plan','run','verify')][string]$Action = 'doctor',
    [string]$Config = 'configs/data/financial_crawl_user.example.json',
    [string]$Output,
    [string]$Run,
    [string[]]$ResumeFrom = @(),
    [string[]]$SeedRun = @(),
    [switch]$ExecuteNetwork,
    [string]$Python
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$pythonCandidates = @()
if ($Python) { $pythonCandidates += $Python }
else {
    $pythonCandidates += (Join-Path $projectRoot '.venv\Scripts\python.exe')
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonCandidates += $pythonCommand.Source }
}
$selectedPython = $null
foreach ($candidate in $pythonCandidates) {
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { continue }
    try { $probeOutput = & $candidate -c 'import sys; print(sys.version_info >= (3,11))' 2>&1 }
    catch { continue }
    if ($LASTEXITCODE -eq 0 -and ($probeOutput -join '').Trim() -eq 'True') {
        $selectedPython = $candidate
        break
    }
}
if (-not $selectedPython) {
    Write-Error 'Không tìm được Python >=3.11 chạy được. Tạo lại .venv hoặc truyền -Python đường dẫn python.exe hợp lệ.'
    exit 3
}
$arguments = @((Join-Path $PSScriptRoot 'crawl_financial.py'), $Action)
if ($Action -eq 'verify') {
    if (-not $Run) { throw '-Run là bắt buộc cho verify' }
    $arguments += @('--run', $Run)
} else {
    $arguments += @('--config', $Config)
}
if ($Action -eq 'run') {
    if (-not $Output) { throw '-Output là bắt buộc; dùng thư mục mới dưới data/' }
    $arguments += @('--output', $Output)
    foreach ($item in $ResumeFrom) { $arguments += @('--resume-from', $item) }
    foreach ($item in $SeedRun) { $arguments += @('--seed-run', $item) }
    if ($ExecuteNetwork) { $arguments += '--execute-network' }
}
& $selectedPython @arguments
exit $LASTEXITCODE
