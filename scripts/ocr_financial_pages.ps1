param([Parameter(Mandatory=$true)][string]$ImageDirectory)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
[Windows.Storage.StorageFile,Windows.Storage,ContentType=WindowsRuntime] > $null
[Windows.Graphics.Imaging.BitmapDecoder,Windows.Graphics.Imaging,ContentType=WindowsRuntime] > $null
[Windows.Media.Ocr.OcrEngine,Windows.Foundation,ContentType=WindowsRuntime] > $null
[Windows.Globalization.Language,Windows.Foundation,ContentType=WindowsRuntime] > $null
$taskMethod = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
} | Select-Object -First 1
function Await-OcrOperation($Operation, $ResultType) {
    $task = $taskMethod.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    $task.Wait()
    $task.Result
}
$language = [Windows.Globalization.Language]::new('en-US')
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($language)
if ($null -eq $engine) { throw 'Windows en-US OCR unavailable' }
foreach ($imageFile in Get-ChildItem -LiteralPath $ImageDirectory -Filter '*.png' | Sort-Object Name) {
    $destination = [System.IO.Path]::ChangeExtension($imageFile.FullName, '.ocr.json')
    if (Test-Path -LiteralPath $destination) { throw "Immutable output exists: $destination" }
    $file = Await-OcrOperation ([Windows.Storage.StorageFile]::GetFileFromPathAsync($imageFile.FullName)) ([Windows.Storage.StorageFile])
    $stream = Await-OcrOperation ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
    try {
        $decoder = Await-OcrOperation ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bitmap = Await-OcrOperation ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        try {
            if ($bitmap.PixelWidth -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension -or $bitmap.PixelHeight -gt [Windows.Media.Ocr.OcrEngine]::MaxImageDimension) { throw 'OCR dimension cap exceeded' }
            $result = Await-OcrOperation ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
            $lines = @($result.Lines | ForEach-Object {
                @{text=$_.Text; words=@($_.Words | ForEach-Object {
                    @{text=$_.Text; x=$_.BoundingRect.X; y=$_.BoundingRect.Y; width=$_.BoundingRect.Width; height=$_.BoundingRect.Height}
                })}
            })
            $hashAlgorithm = [System.Security.Cryptography.SHA256]::Create()
            try { $imageHash = [BitConverter]::ToString($hashAlgorithm.ComputeHash([System.IO.File]::ReadAllBytes($imageFile.FullName))).Replace('-', '').ToLower() } finally { $hashAlgorithm.Dispose() }
            $record = @{engine='Windows.Media.Ocr'; language='en-US'; language_limitation='Vietnamese labels require visual verification'; image_sha256=$imageHash; width=$bitmap.PixelWidth; height=$bitmap.PixelHeight; text=$result.Text; lines=$lines; financial_features_allowed=$false}
            [System.IO.File]::WriteAllText($destination, ($record | ConvertTo-Json -Depth 8), [System.Text.UTF8Encoding]::new($false))
        } finally { $bitmap.Dispose() }
    } finally { $stream.Dispose() }
}
