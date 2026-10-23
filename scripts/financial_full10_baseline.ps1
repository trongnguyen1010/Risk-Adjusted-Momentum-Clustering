param(
    [ValidateSet('Run','Check','Status')][string]$Mode = 'Status',
    [string]$Python = 'python'
)
$ErrorActionPreference = 'Stop'
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $ProjectRoot
try {
    if ($Mode -eq 'Status') {
        Get-Content -LiteralPath 'data/financial/financial_full10_baseline_v1/pipeline-status.json'
    } else {
        $Arguments = @('scripts/financial_full10_baseline.py')
        if ($Mode -eq 'Check') { $Arguments += '--check-only' }
        & $Python @Arguments
        if ($LASTEXITCODE -ne 0) { throw "Financial baseline exited $LASTEXITCODE" }
    }
} finally { Pop-Location }
