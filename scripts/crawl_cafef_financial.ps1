param(
    [ValidateSet('doctor','plan','run','verify','feedback','prepare50')][string]$Action='doctor',
    [string]$Config='configs/data/cafef_financial_trial50_v1.json',
    [string]$Output,
    [string]$Run,
    [string]$ResumeFrom,
    [string]$Python,
    [switch]$ExecuteNetwork
)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path -LiteralPath (Split-Path -Parent $PSScriptRoot)).Path
if (-not $Python) { $Python=Join-Path $projectRoot '.venv/Scripts/python.exe' }
if (-not (Test-Path -LiteralPath $Python)) { throw 'Python not found; specify -Python absolute executable' }
$arguments=@((Join-Path $PSScriptRoot 'crawl_cafef_financial.py'),$Action.ToLowerInvariant(),'--config',$Config)
if ($Output) { $arguments+=@('--output',$Output) }
if ($Run) { $arguments+=@('--run',$Run) }
if ($ResumeFrom) { $arguments+=@('--resume-from',$ResumeFrom) }
if ($ExecuteNetwork) { $arguments+='--execute-network' }
Push-Location -LiteralPath $projectRoot
try { & $Python @arguments; $runnerExit=$LASTEXITCODE } finally { Pop-Location }
exit $runnerExit
