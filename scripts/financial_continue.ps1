param(
    [ValidateSet('prepare','recover','extract','audit','verify')][string]$Action='verify',
    [string]$Config='configs/data/financial_continuation50_v2.json',
    [string]$Python,
    [string]$PdfSha,
    [switch]$ExecuteNetwork,
    [switch]$FullOcr,
    [switch]$RetryFailed
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
if (-not $Python) { $Python=Join-Path $projectRoot '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Specify -Python with an existing executable.' }
$arguments=@((Join-Path $PSScriptRoot 'financial_continue.py'),$Action,'--config',$Config)
if ($PdfSha) { $arguments+=@('--pdf-sha',$PdfSha) }
if ($ExecuteNetwork) { $arguments+='--execute-network' }
if ($FullOcr) { $arguments+='--full-ocr' }
if ($RetryFailed) { $arguments+='--retry-failed' }
Push-Location -LiteralPath $projectRoot
try { & $Python @arguments; $runnerExit=$LASTEXITCODE } finally { Pop-Location }
exit $runnerExit
