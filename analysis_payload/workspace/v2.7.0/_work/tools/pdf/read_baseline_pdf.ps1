$ErrorActionPreference = 'Stop'
$toolRoot = $PSScriptRoot
$workRoot = Split-Path (Split-Path $toolRoot -Parent) -Parent
$vRoot = Split-Path $workRoot -Parent
$packageRoot = Get-ChildItem -LiteralPath $vRoot -Directory | Where-Object { $_.Name -like '*Codex_Goal*' } | Select-Object -First 1 -ExpandProperty FullName
if (-not $packageRoot) { throw 'Input package directory not found.' }
$pdfPath = Get-ChildItem -LiteralPath $packageRoot -Recurse -File -Filter '*.pdf' | Select-Object -First 1 -ExpandProperty FullName
if (-not $pdfPath) { throw 'Baseline PDF not found.' }

$outputRoot = Join-Path $workRoot 'input_read\pdf'
[System.IO.Directory]::CreateDirectory($outputRoot) | Out-Null
$pdfinfo = 'D:\texlive\2026\bin\windows\pdfinfo.exe'
$pdffonts = 'D:\texlive\2026\bin\windows\pdffonts.exe'
$pdftotext = 'D:\texlive\2026\bin\windows\pdftotext.exe'
foreach ($tool in @($pdfinfo, $pdffonts, $pdftotext)) {
    if (-not [System.IO.File]::Exists($tool)) { throw "Required Poppler tool not found: $tool" }
}

$utf8 = [System.Text.UTF8Encoding]::new($false)
$info = & $pdfinfo -box $pdfPath 2>&1
[System.IO.File]::WriteAllLines((Join-Path $outputRoot 'pdfinfo.txt'), [string[]]$info, $utf8)
$fonts = & $pdffonts $pdfPath 2>&1
[System.IO.File]::WriteAllLines((Join-Path $outputRoot 'pdffonts.txt'), [string[]]$fonts, $utf8)
$destinations = & $pdfinfo -dests $pdfPath 2>&1
[System.IO.File]::WriteAllLines((Join-Path $outputRoot 'named_destinations.txt'), [string[]]$destinations, $utf8)

$textPath = Join-Path $outputRoot 'baseline_text_layout.txt'
& $pdftotext -layout -enc UTF-8 $pdfPath $textPath
if ($LASTEXITCODE -ne 0) { throw "pdftotext failed with exit code $LASTEXITCODE" }

Write-Output "PDF=$pdfPath"
Write-Output "OUTPUT_ROOT=$outputRoot"
Write-Output "TEXT_BYTES=$([System.IO.FileInfo]::new($textPath).Length)"
Write-Output "TEXT_LINES=$(([System.IO.File]::ReadLines($textPath) | Measure-Object).Count)"
Write-Output "DESTINATION_LINES=$($destinations.Count)"
Write-Output "FONT_ROWS=$([Math]::Max(0, $fonts.Count - 2))"
