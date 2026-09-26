$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$asyncMethods = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
  $_.Name -eq 'AsTask' -and $_.IsGenericMethod -and $_.GetParameters().Count -eq 1 -and
  $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
}
$asTaskGeneric = $asyncMethods | Select-Object -First 1
if (-not $asTaskGeneric) { throw 'WinRT AsTask generic adapter unavailable' }
function Wait-WinRt($operation, [Type]$resultType) {
  $task = $asTaskGeneric.MakeGenericMethod($resultType).Invoke($null, @($operation))
  $task.Wait()
  return $task.Result
}

$languageType = [Windows.Globalization.Language, Windows.Globalization, ContentType=WindowsRuntime]
$engineType = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType=WindowsRuntime]
$streamType = [Windows.Storage.Streams.InMemoryRandomAccessStream, Windows.Storage.Streams, ContentType=WindowsRuntime]
$writerType = [Windows.Storage.Streams.DataWriter, Windows.Storage.Streams, ContentType=WindowsRuntime]
$decoderType = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$bitmapType = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType=WindowsRuntime]
$resultType = [Windows.Media.Ocr.OcrResult, Windows.Media.Ocr, ContentType=WindowsRuntime]
$engine = $engineType::TryCreateFromLanguage($languageType::new('pt-BR'))
if (-not $engine) { throw 'Windows.Media.Ocr pt-BR is unavailable' }

$payload = [Console]::In.ReadToEnd() | ConvertFrom-Json
$output = [System.Collections.Generic.List[object]]::new()
foreach ($region in $payload.regions) {
  $stream = $streamType::new()
  $writer = $writerType::new($stream)
  $writer.WriteBytes([Convert]::FromBase64String($region.image_base64))
  [void](Wait-WinRt ($writer.StoreAsync()) ([uint32]))
  [void](Wait-WinRt ($writer.FlushAsync()) ([bool]))
  [void]$writer.DetachStream()
  [void]$stream.Seek(0)
  $decoder = Wait-WinRt ($decoderType::CreateAsync($stream)) $decoderType
  $bitmap = Wait-WinRt ($decoder.GetSoftwareBitmapAsync()) $bitmapType
  $recognized = Wait-WinRt ($engine.RecognizeAsync($bitmap)) $resultType
  $lines = [System.Collections.Generic.List[object]]::new()
  foreach ($line in $recognized.Lines) {
    $words = @($line.Words)
    if ($words.Count -eq 0 -or -not $line.Text.Trim()) { continue }
    $x0 = ($words | ForEach-Object { $_.BoundingRect.X } | Measure-Object -Minimum).Minimum
    $y0 = ($words | ForEach-Object { $_.BoundingRect.Y } | Measure-Object -Minimum).Minimum
    $x1 = ($words | ForEach-Object { $_.BoundingRect.X + $_.BoundingRect.Width } | Measure-Object -Maximum).Maximum
    $y1 = ($words | ForEach-Object { $_.BoundingRect.Y + $_.BoundingRect.Height } | Measure-Object -Maximum).Maximum
    $lines.Add([pscustomobject]@{
      text = $line.Text.Trim()
      bbox_px = @([math]::Round($x0, 2), [math]::Round($y0, 2), [math]::Round($x1, 2), [math]::Round($y1, 2))
    })
  }
  $output.Add([pscustomobject]@{ region_id = $region.region_id; lines = $lines })
  $bitmap.Dispose()
  $stream.Dispose()
}
try {
  $json = @{ ok = $true; regions = $output } | ConvertTo-Json -Depth 8 -Compress
  $json = [regex]::Replace($json, '[^\x00-\x7F]', { param($match) '\u{0:X4}' -f [int][char]$match.Value })
  [Console]::Out.WriteLine($json)
}
finally { $engine = $null }
