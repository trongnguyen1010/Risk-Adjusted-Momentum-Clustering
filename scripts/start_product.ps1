param(
  [int]$Port = 8000
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$bundle = Join-Path $projectRoot 'artifacts\product\pilot-v1'

if (-not (Test-Path -LiteralPath $python)) {
  throw "Không tìm thấy Python environment: $python"
}

if (-not (Test-Path -LiteralPath (Join-Path $bundle 'manifest.json'))) {
  & $python (Join-Path $projectRoot 'run.py') product-build `
    --canonical (Join-Path $projectRoot 'data\canonical\canonical-1d2a54288bfc') `
    --features (Join-Path $projectRoot 'data\runs\run-4a1a6203dba7') `
    --experiment (Join-Path $projectRoot 'data\experiments\experiment-de5f4d68afa0') `
    --output $bundle
  if ($LASTEXITCODE -ne 0) { throw 'Không thể tạo product bundle.' }
}

Write-Host "Mở http://127.0.0.1:$Port/?ticker=FPT"
& $python (Join-Path $projectRoot 'run.py') serve --bundle $bundle --web-root (Join-Path $projectRoot 'web') --port $Port
