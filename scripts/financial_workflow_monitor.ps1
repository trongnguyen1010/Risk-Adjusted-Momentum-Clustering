param([ValidateRange(1024,65535)][int]$Port=8765,[string]$Python='')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if (-not $Python) { $Python=Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe' }
$env:PYTHONIOENCODING='utf-8'
Push-Location $root
try {
 & $Python 'run.py' monitor --root $root --port $Port
 if ($LASTEXITCODE) { throw 'Local workflow monitor exited with error' }
} finally { Pop-Location }
