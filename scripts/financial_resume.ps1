param(
    [ValidateSet('recover','extract','audit','verify','template','review')][string]$Action='verify',
    [string]$Config='configs/data/financial_resume50_v3/config.json',
    [string]$Python,
    [string]$PdfSha,
    [string]$Symbol,
    [string]$ReviewFile,
    [switch]$ExecuteNetwork,
    [switch]$FullOcr,
    [switch]$RetryFailed
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
if (-not $Python) { $Python=Join-Path $projectRoot '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Specify -Python with an existing executable.' }
$arguments=@((Join-Path $PSScriptRoot 'financial_resume.py'),$Action,'--config',$Config)
if ($PdfSha) { $arguments+=@('--pdf-sha',$PdfSha) }
if ($Symbol) { $arguments+=@('--symbol',$Symbol) }
if ($ReviewFile) { $arguments+=@('--review-file',$ReviewFile) }
if ($ExecuteNetwork) { $arguments+='--execute-network' }
if ($FullOcr) { $arguments+='--full-ocr' }
if ($RetryFailed) { $arguments+='--retry-failed' }
Push-Location -LiteralPath $projectRoot
try { & $Python @arguments; $runnerExit=$LASTEXITCODE } finally { Pop-Location }
exit $runnerExit
