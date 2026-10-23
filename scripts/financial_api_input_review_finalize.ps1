param(
    [Parameter(Mandatory=$true)][int]$WorkerPid,
    [Parameter(Mandatory=$true)][string]$WorkerStartedAt,
    [string]$PythonExecutable = "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$reviewRoot = Join-Path $projectRoot 'data/financial/history_api_input_review1522_v1'
$reportRoot = Join-Path $projectRoot 'artifacts/reports/financial-api-input-review1522-v1'
New-Item -ItemType Directory -Force -Path $reportRoot | Out-Null
$deadline = [DateTime]::UtcNow.AddHours(2)
function Write-ProgressReport {
    $state = Get-Content -LiteralPath (Join-Path $reviewRoot 'pipeline-status.json') -Raw | ConvertFrom-Json
    $percent = if ($state.total) { [Math]::Round(100 * $state.completed / $state.total, 1) } else { 0 }
    $body = @"
# Tiến độ review input API

Cập nhật: $([DateTime]::UtcNow.ToString('o')).

- Stage: $($state.stage).
- Đã xử lý: $($state.completed)/$($state.total) mã ($percent%).
- Mã gần nhất: $($state.last_symbol).
- Kết quả API mới được chấp nhận: 0; reference reviewed từ stage33 giữ nguyên.
- Không tải PDF, không OCR mới, chưa lập PDF download plan.

Khi worker chốt xong, helper tự kiểm manifest/output và cập nhật [report cuối](report.md), verification.json và active documentation pointers. Số học chẩn đoán không được cộng thành chỉ số đã kiểm chứng.
"@
    [IO.File]::WriteAllText((Join-Path $reportRoot 'progress.md'), $body, [Text.UTF8Encoding]::new($false))
    return $state
}
try {
    do {
        $state = Write-ProgressReport
        $worker = Get-Process -Id $WorkerPid -ErrorAction SilentlyContinue
        $sameWorker = $worker -and ($worker.StartTime.ToUniversalTime().ToString('o') -eq $WorkerStartedAt)
        if (-not $sameWorker) { break }
        if ([DateTime]::UtcNow -ge $deadline) { throw 'Offline finalizer observation deadline reached; worker not stopped or budget reset.' }
        Start-Sleep -Seconds 30
    } while ($true)
    $state = Write-ProgressReport
    if ($state.stage -ne 'COMPLETE_EXPANDED_API_INPUT_REVIEW') {
        throw "Worker did not seal a complete review: $($state.stage) $($state.reason)"
    }
    Push-Location -LiteralPath $projectRoot
    try {
        $env:PYTHONIOENCODING = 'utf-8'
        & $PythonExecutable 'scripts/financial_api_input_review_verify.py'
        if ($LASTEXITCODE -ne 0) { throw "Final verification failed: $LASTEXITCODE" }
    } finally { Pop-Location }
    [IO.File]::WriteAllText((Join-Path $reviewRoot 'finalizer-status.json'), '{"stage":"COMPLETE_OFFLINE_REVIEW_AND_VERIFICATION","network_requests":0,"pdf_downloads":0}', [Text.UTF8Encoding]::new($false))
} catch {
    $failure = @{ stage='HELD_FINALIZER_REVIEW_REQUIRED'; reason=$_.Exception.Message; at=[DateTime]::UtcNow.ToString('o') } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $reviewRoot 'finalizer-status.json'), $failure, [Text.UTF8Encoding]::new($false))
    throw
}
