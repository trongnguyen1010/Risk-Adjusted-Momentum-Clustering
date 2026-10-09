param(
    [ValidateSet('doctor','plan','audit','acquire','extract','run','template','review','verify')]
    [string]$Action='doctor',
    [string]$Config='configs/data/financial_user_workflow50_v1.json',
    [string]$Run='data/financial/user_workflow50_v1',
    [string]$Python,
    [int]$Limit=0,
    [string]$Symbols,
    [string]$Symbol,
    [string]$PdfSha,
    [string]$ReviewFile,
    [switch]$ExecuteNetwork,
    [switch]$FullOcr,
    [switch]$RetryFailed
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
if (-not $Python) { $Python=Join-Path $projectRoot '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Python missing; specify -Python with an absolute executable path.' }
$arguments=@((Join-Path $PSScriptRoot 'financial_readiness.py'),$Action,'--config',$Config,'--run',$Run)
if ($Limit) { $arguments+=@('--limit',[string]$Limit) }
if ($Symbols) { $arguments+=@('--symbols',$Symbols) }
if ($Symbol) { $arguments+=@('--symbol',$Symbol) }
if ($PdfSha) { $arguments+=@('--pdf-sha',$PdfSha) }
if ($ReviewFile) { $arguments+=@('--review-file',$ReviewFile) }
if ($ExecuteNetwork) { $arguments+='--execute-network' }
if ($FullOcr) { $arguments+='--full-ocr' }
if ($RetryFailed) { $arguments+='--retry-failed' }
Push-Location -LiteralPath $projectRoot
try { & $Python @arguments; $runnerExit=$LASTEXITCODE } finally { Pop-Location }
exit $runnerExit
