param(
  [string]$Config = 'configs/product/local.example.json',
  [int]$Port = 0
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectRoot '.venv\Scripts\python.exe'
$configPath = if ([System.IO.Path]::IsPathRooted($Config)) {
  [System.IO.Path]::GetFullPath($Config)
} else {
  [System.IO.Path]::GetFullPath((Join-Path $projectRoot $Config))
}

if (-not (Test-Path -LiteralPath $python)) {
  throw "Không tìm thấy Python environment: $python"
}
if (-not (Test-Path -LiteralPath $configPath)) {
  throw "Không tìm thấy product config: $configPath"
}

$settings = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json
if (-not $settings.output -or -not $settings.web_root) {
  throw 'Product config phải khai báo output và web_root.'
}
$bundle = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $settings.output))
$webRoot = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $settings.web_root))
$servePort = if ($Port -gt 0) { $Port } else { [int]$settings.port }

if (-not (Test-Path -LiteralPath (Join-Path $bundle 'manifest.json'))) {
  throw "Product bundle chưa tồn tại: $bundle. Hãy tạo artifact mới và cập nhật product config; script không tự tái tạo legacy pilot."
}
if (-not (Test-Path -LiteralPath $webRoot)) {
  throw "Không tìm thấy web root: $webRoot"
}

Write-Host "Mở http://127.0.0.1:$servePort/"
& $python (Join-Path $projectRoot 'run.py') serve --bundle $bundle --web-root $webRoot --port $servePort
