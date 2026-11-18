param(
    [ValidateSet('Verify', 'Test', 'Import')][string]$Mode = 'Verify',
    [string]$Python = 'python',
    [string]$Bundle
)
$ErrorActionPreference = 'Stop'
$IntegrationRoot = Split-Path $PSScriptRoot -Parent
Push-Location $IntegrationRoot
try {
    $env:PYTHONIOENCODING = 'utf-8'
    $env:PYTHONPATH = "$IntegrationRoot/src;$IntegrationRoot/tests;$IntegrationRoot/.tools/market-runtime;$IntegrationRoot/.tools/research-runtime"
    $env:TEMP = "$IntegrationRoot/.tmp/integration-temp"
    $env:TMP = $env:TEMP
    New-Item -ItemType Directory -Force -Path $env:TEMP | Out-Null
    $env:OMP_NUM_THREADS = '1'
    if ($Mode -eq 'Import') {
        if (-not $Bundle) { throw '-Bundle is required for Import' }
        & $Python scripts/import_market_bundle.py $Bundle
        if ($LASTEXITCODE -ne 0) { throw 'Market bundle import failed' }
    } elseif ($Mode -eq 'Test') {
        & $Python -m unittest unit.experiments.test_financial_full10_baseline unit.experiments.test_financial_exploratory unit.experiments.test_market_financial_integration unit.experiments.test_protocol unit.experiments.test_m2_runner unit.experiments.test_final_holdout unit.clustering.test_algorithms tests.test_m3_dashboard -q
        if ($LASTEXITCODE -ne 0) { throw 'Integration targeted tests failed' }
    } else {
        & $Python scripts/verify_market_financial_integration.py --publish
        if ($LASTEXITCODE -ne 0) { throw 'Market integration verification failed' }
        & $Python scripts/financial_full10_review.py --source-root M2/artifacts/financial-execution56-frozen-source-v2 --output M2/artifacts/financial-execution56-integration-review-v2
        if ($LASTEXITCODE -ne 0) { throw 'Financial verification failed' }
    }
} finally {
    Pop-Location
}
