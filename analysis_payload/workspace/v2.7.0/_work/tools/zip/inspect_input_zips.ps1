$ErrorActionPreference = 'Stop'
$toolRoot = $PSScriptRoot
$workRoot = Split-Path (Split-Path $toolRoot -Parent) -Parent
$vRoot = Split-Path $workRoot -Parent
$packageRoot = Get-ChildItem -LiteralPath $vRoot -Directory | Where-Object { $_.Name -like '*Codex_Goal*' } | Select-Object -First 1 -ExpandProperty FullName
if (-not $packageRoot) { throw 'Input package directory not found.' }
$inputZips = Get-ChildItem -LiteralPath $packageRoot -Recurse -File -Filter '*.zip'
$sourceZip = $inputZips | Where-Object { $_.Name -like '*LaTeX*' } | Select-Object -First 1 -ExpandProperty FullName
$evidenceZip = $inputZips | Where-Object { $_.FullName -ne $sourceZip } | Select-Object -First 1 -ExpandProperty FullName
if (-not $sourceZip -or -not $evidenceZip) { throw 'Expected two input ZIP files were not found.' }
$outputRoot = Join-Path $workRoot 'input_read\zip_manifests'

& "$toolRoot\inspect_zip.ps1" `
    -ZipPath $sourceZip `
    -ManifestPath "$outputRoot\source_zip_manifest.json"

& "$toolRoot\inspect_zip.ps1" `
    -ZipPath $evidenceZip `
    -ManifestPath "$outputRoot\evidence_zip_manifest.json"
