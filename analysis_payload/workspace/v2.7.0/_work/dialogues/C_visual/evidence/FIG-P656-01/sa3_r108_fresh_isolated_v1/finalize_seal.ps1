$ErrorActionPreference = 'Stop'
$root = (Get-Item -LiteralPath $PSCommandPath -Force).DirectoryName
$manifest = Join-Path $root 'MANIFEST.sha256'
$prepared = Join-Path $root '.WRITE_STOPPED.prepared'
$final = Join-Path $root 'WRITE_STOPPED'

if (-not (Test-Path -LiteralPath $manifest -PathType Leaf)) { throw 'MANIFEST.sha256 is absent' }
if (Test-Path -LiteralPath $prepared) { throw '.WRITE_STOPPED.prepared already exists' }
if (Test-Path -LiteralPath $final) { throw 'WRITE_STOPPED already exists' }

$manifestHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash
$payloadCount = @(Get-Content -LiteralPath $manifest | Where-Object { $_ -and -not $_.StartsWith('#') }).Count
$marker = @(
    'WRITE_STOPPED'
    'HANDOFF_ID=C-FIG-P656-01-R108-SA3-FRESH-ISOLATED-V1'
    'RESULT=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE'
    "MANIFEST_SHA256=$manifestHash"
    "MANIFEST_PAYLOAD_COUNT=$payloadCount"
    'POST_MARKER_WRITES=0'
) -join "`n"
Set-Content -LiteralPath $prepared -Value ($marker + "`n") -Encoding utf8NoBOM -NoNewline

$files = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File)
foreach ($file in $files) {
    & "$env:SystemRoot\System32\attrib.exe" +R $file.FullName
    if ($LASTEXITCODE -ne 0) { throw "Failed to make file read-only: $($file.FullName)" }
}
$directories = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory | Sort-Object { $_.FullName.Length } -Descending)
foreach ($directory in $directories) {
    & "$env:SystemRoot\System32\attrib.exe" +R $directory.FullName
    if ($LASTEXITCODE -ne 0) { throw "Failed to make directory read-only: $($directory.FullName)" }
}
& "$env:SystemRoot\System32\attrib.exe" +R $root
if ($LASTEXITCODE -ne 0) { throw 'Failed to make evidence root read-only' }

# Final filesystem mutation: publish the already read-only marker. No statement follows.
Move-Item -LiteralPath $prepared -Destination $final
