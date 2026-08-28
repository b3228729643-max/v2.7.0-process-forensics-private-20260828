$ErrorActionPreference = 'Stop'
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827'
$ManifestPath = Join-Path $Root 'PAYLOAD_MANIFEST.json'
$MarkerPath = Join-Path $Root 'WRITE_STOPPED'

if (-not [System.IO.Directory]::Exists($Root)) { throw 'Evidence root is absent.' }
if ([System.IO.File]::Exists($ManifestPath)) { throw 'PAYLOAD_MANIFEST.json already exists; refusing a second seal.' }
if ([System.IO.File]::Exists($MarkerPath)) { throw 'WRITE_STOPPED already exists; refusing a second seal.' }

$PayloadFiles = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Sort-Object FullName)
$Entries = foreach ($File in $PayloadFiles) {
    $Relative = [System.IO.Path]::GetRelativePath($Root, $File.FullName).Replace('\', '/')
    $Hash = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash
    [pscustomobject]@{
        path = $Relative
        bytes = [int64]$File.Length
        sha256 = $Hash
    }
}
$Manifest = [ordered]@{
    manifest_version = 1
    uid = 'FIG-P049-01'
    handoff_id = 'A-R111-P049-SA3-FRESH-ISOLATED-20260827'
    root = $Root
    payload_file_count = $Entries.Count
    manifest_self_exclusion = 'PAYLOAD_MANIFEST.json is excluded because a file cannot contain its own stable SHA-256.'
    postseal_marker_exclusion = 'WRITE_STOPPED is intentionally created after all payload, manifest, audit, and readonly operations.'
    files = @($Entries)
}
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
[System.IO.File]::WriteAllText($ManifestPath, ($Manifest | ConvertTo-Json -Depth 8), $Utf8NoBom)

$Readback = Get-Content -LiteralPath $ManifestPath -Raw | ConvertFrom-Json
$ReadbackPaths = @($Readback.files | ForEach-Object { $_.path })
$ActualPayloadPaths = @($PayloadFiles | ForEach-Object { [System.IO.Path]::GetRelativePath($Root, $_.FullName).Replace('\', '/') })
if ($Readback.payload_file_count -ne $PayloadFiles.Count) { throw 'Manifest payload count mismatch before sealing.' }
if (@(Compare-Object -ReferenceObject $ActualPayloadPaths -DifferenceObject $ReadbackPaths).Count -ne 0) { throw 'Manifest path set mismatch before sealing.' }
foreach ($Entry in $Readback.files) {
    $Target = Join-Path $Root ($Entry.path.Replace('/', '\'))
    $Item = Get-Item -LiteralPath $Target
    if ($Item.Length -ne [int64]$Entry.bytes) { throw "Manifest byte mismatch before sealing: $($Entry.path)" }
    if ((Get-FileHash -LiteralPath $Target -Algorithm SHA256).Hash -ne $Entry.sha256) { throw "Manifest hash mismatch before sealing: $($Entry.path)" }
}

$AllFilesBeforeMarker = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)
foreach ($File in $AllFilesBeforeMarker) {
    $Attr = [System.IO.File]::GetAttributes($File.FullName)
    [System.IO.File]::SetAttributes($File.FullName, ($Attr -bor [System.IO.FileAttributes]::ReadOnly))
}
$AllDirectories = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)
foreach ($Directory in $AllDirectories) {
    $Attr = [System.IO.File]::GetAttributes($Directory.FullName)
    [System.IO.File]::SetAttributes($Directory.FullName, ($Attr -bor [System.IO.FileAttributes]::ReadOnly))
}
$RootAttr = [System.IO.File]::GetAttributes($Root)
[System.IO.File]::SetAttributes($Root, ($RootAttr -bor [System.IO.FileAttributes]::ReadOnly))

$Marker = [ordered]@{
    marker = 'WRITE_STOPPED'
    uid = 'FIG-P049-01'
    sealed_at = (Get-Date).ToString('o')
    manifest_sha256 = (Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256).Hash
    payload_file_count = $PayloadFiles.Count
    rule = 'This file is the unique final root write. No later root write is permitted.'
}
[System.IO.File]::WriteAllText($MarkerPath, ($Marker | ConvertTo-Json -Depth 4), $Utf8NoBom)
$MarkerAttr = [System.IO.File]::GetAttributes($MarkerPath)
[System.IO.File]::SetAttributes($MarkerPath, ($MarkerAttr -bor [System.IO.FileAttributes]::ReadOnly))

[pscustomobject]@{
    seal = 'CREATED_ONCE'
    root = $Root
    payload_file_count = $PayloadFiles.Count
    manifest_sha256 = $Marker.manifest_sha256
    write_stopped = $MarkerPath
    sealed_at = $Marker.sealed_at
} | ConvertTo-Json -Compress
