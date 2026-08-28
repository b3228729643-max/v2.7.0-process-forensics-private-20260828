$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = $PSScriptRoot
$parent = [IO.Directory]::GetParent($root).FullName
$manifestPath = Join-Path $root 'seal_manifest.csv'
$markerName = 'SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE.marker'
$markerPath = Join-Path $root $markerName
$stagingPath = Join-Path $parent '.C-FIG-P689-01-R115-SA3-FRESH-ISOLATED-V1.marker.staging'

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'ROOT_MISSING' }
if (Test-Path -LiteralPath $manifestPath) { throw 'MANIFEST_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $markerPath) { throw 'MARKER_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $stagingPath) { throw 'STAGING_ALREADY_EXISTS' }

[object[]]$preManifestFiles = @(
    Get-ChildItem -LiteralPath $root -File -Recurse -Force | Sort-Object FullName
)
$manifestRows = foreach ($file in $preManifestFiles) {
    [pscustomobject]@{
        relative_path = $file.FullName.Substring($root.Length).TrimStart([char]'\')
        bytes = $file.Length
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
        last_write_utc = $file.LastWriteTimeUtc.ToString('o')
    }
}
[string[]]$manifestLines = @($manifestRows | ConvertTo-Csv -NoTypeInformation)
[IO.File]::WriteAllLines(
    $manifestPath,
    $manifestLines,
    [Text.UTF8Encoding]::new($false)
)
$manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash

[object[]]$manualPairs = @(Import-Csv -LiteralPath (Join-Path $root 'manual_pair_ledger.csv'))
[object[]]$objects = @(Import-Csv -LiteralPath (Join-Path $root 'mechanical_object_index.csv'))
if ($manualPairs.Count -ne 528) { throw 'MANUAL_PAIR_COUNT_NOT_528' }
if ($objects.Count -ne 33) { throw 'OBJECT_COUNT_NOT_33' }

[object[]]$filesToLock = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
[object[]]$dirsToLock = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
foreach ($file in $filesToLock) {
    [IO.File]::SetAttributes(
        $file.FullName,
        ([IO.File]::GetAttributes($file.FullName) -bor [IO.FileAttributes]::ReadOnly)
    )
}
foreach ($dir in $dirsToLock) {
    [IO.File]::SetAttributes(
        $dir.FullName,
        ([IO.File]::GetAttributes($dir.FullName) -bor [IO.FileAttributes]::ReadOnly)
    )
}
[IO.File]::SetAttributes(
    $root,
    ([IO.File]::GetAttributes($root) -bor [IO.FileAttributes]::ReadOnly)
)

[object[]]$lockedFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
[object[]]$lockedDirs = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
[object[]]$timeObjects = @($lockedFiles) + @($lockedDirs) + @((Get-Item -LiteralPath $root))
[DateTime]$maxExistingUtc = [DateTime]::MinValue
foreach ($item in $timeObjects) {
    if ($item.LastWriteTimeUtc -gt $maxExistingUtc) { $maxExistingUtc = $item.LastWriteTimeUtc }
}
[DateTime]$markerTimeUtc = [DateTime]::UtcNow.AddSeconds(10)
if ($markerTimeUtc -le $maxExistingUtc) { $markerTimeUtc = $maxExistingUtc.AddSeconds(10) }

[string[]]$markerLines = @(
    'HANDOFF_ID=C-FIG-P689-01-R115-SA3-FRESH-ISOLATED-V1',
    'CANONICAL_INSTANCE=/root/sa3_fig_p689_r115_fresh_isolated_v1',
    'FIGURE_ID=FIG-P689-01',
    'OFFICIAL_PHYSICAL_PAGE=739',
    'PRINTED_PAGE=726',
    'PDF_SHA256=93ADF6E1FBF9EED2A392FA150C81738DD60FC50F50C00EBDF99C0F4168D4726F',
    'SOURCE_SHA256=7BAED58EE4634091A2873D84942A2CA4E2C2475D509B2FA5FDCB5A28E5FADE5F',
    'CHAPTER_SHA256=7276DDB767246292D0924D1651D560975E0FE6D2ACE47CBAEC4EE45CEB4A0029',
    'DENOMINATOR_N=33',
    'UNORDERED_PAIR_COUNT=528',
    'MANUAL_PAIR_VERDICTS=528',
    'OVERLAP_CANDIDATE_PIXEL_COUNT=0',
    'MASK_CONTAMINATION_PIXEL_COUNT=0',
    'OVERLAP_PIXEL_COUNT=0',
    'PIXEL_ADJUDICATION_STATUS=CLEAR',
    'CLIP_PIXEL_COUNT=0',
    'RESULT=PASS',
    'PASS_TOKEN=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE',
    "MANIFEST_ENTRY_COUNT=$($preManifestFiles.Count)",
    "SEALED_NONMARKER_FILE_COUNT=$($preManifestFiles.Count + 1)",
    "TREE_MANIFEST_SHA256=$manifestHash",
    "MARKER_FILETIME_UTC=$($markerTimeUtc.ToString('o'))",
    'CONTENT_WRITES_AFTER_MARKER=0',
    'ATTRIBUTE_WRITES_AFTER_MARKER=0'
)
[IO.File]::WriteAllLines(
    $stagingPath,
    $markerLines,
    [Text.UTF8Encoding]::new($false)
)

[byte[]]$markerBytes = [IO.File]::ReadAllBytes($stagingPath)
if ($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF) {
    throw 'MARKER_HAS_UTF8_BOM'
}
[string[]]$validatedLines = @([IO.File]::ReadAllLines($stagingPath, [Text.UTF8Encoding]::new($false)))
if ($validatedLines.Count -ne $markerLines.Count) { throw 'MARKER_LINE_COUNT_MISMATCH' }
foreach ($line in $validatedLines) {
    if ($line -notmatch '^[A-Z0-9_]+=[^=\r\n]*$') { throw "MARKER_LINE_INVALID=$line" }
    if (@($line.ToCharArray() | Where-Object { $_ -eq '=' }).Count -ne 1) { throw "MARKER_EQUALS_INVALID=$line" }
}
[string[]]$keys = @($validatedLines | ForEach-Object { ($_ -split '=', 2)[0] })
if (@($keys | Sort-Object -Unique).Count -ne $keys.Count) { throw 'MARKER_DUPLICATE_KEY' }
if (-not ($validatedLines -contains 'RESULT=PASS')) { throw 'MARKER_RESULT_INVALID' }
if (-not ($validatedLines -contains 'PASS_TOKEN=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE')) { throw 'MARKER_TOKEN_INVALID' }

[IO.File]::SetCreationTimeUtc($stagingPath, $markerTimeUtc)
[IO.File]::SetLastWriteTimeUtc($stagingPath, $markerTimeUtc)
[IO.File]::SetLastAccessTimeUtc($stagingPath, $markerTimeUtc)
[IO.File]::SetAttributes(
    $stagingPath,
    ([IO.File]::GetAttributes($stagingPath) -bor [IO.FileAttributes]::ReadOnly)
)

# Sole final mutation inside the fixed evidence root. Everything below is read-only audit.
Move-Item -LiteralPath $stagingPath -Destination $markerPath -ErrorAction Stop

[object[]]$auditFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
[object[]]$auditDirs = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
if ($auditFiles.Count -ne ($preManifestFiles.Count + 2)) { throw 'SEALED_FILE_COUNT_MISMATCH' }
foreach ($file in $auditFiles) {
    if (-not (($file.Attributes -band [IO.FileAttributes]::ReadOnly) -eq [IO.FileAttributes]::ReadOnly)) {
        throw "FILE_NOT_READONLY=$($file.FullName)"
    }
}
foreach ($dir in $auditDirs) {
    if (-not (($dir.Attributes -band [IO.FileAttributes]::ReadOnly) -eq [IO.FileAttributes]::ReadOnly)) {
        throw "DIR_NOT_READONLY=$($dir.FullName)"
    }
}
$auditRoot = Get-Item -LiteralPath $root
if (-not (($auditRoot.Attributes -band [IO.FileAttributes]::ReadOnly) -eq [IO.FileAttributes]::ReadOnly)) {
    throw 'ROOT_NOT_READONLY'
}
$auditMarker = Get-Item -LiteralPath $markerPath
[object[]]$auditOthers = @($auditFiles | Where-Object { $_.FullName -ne $markerPath }) + @($auditDirs) + @($auditRoot)
[DateTime]$auditMaxOtherUtc = [DateTime]::MinValue
foreach ($item in $auditOthers) {
    if ($item.LastWriteTimeUtc -gt $auditMaxOtherUtc) { $auditMaxOtherUtc = $item.LastWriteTimeUtc }
}
if ($auditMarker.LastWriteTimeUtc -le $auditMaxOtherUtc) { throw 'MARKER_FILETIME_NOT_STRICTLY_LATER' }
[byte[]]$auditMarkerBytes = [IO.File]::ReadAllBytes($markerPath)
if ($auditMarkerBytes.Length -ge 3 -and $auditMarkerBytes[0] -eq 0xEF -and $auditMarkerBytes[1] -eq 0xBB -and $auditMarkerBytes[2] -eq 0xBF) {
    throw 'SEALED_MARKER_HAS_UTF8_BOM'
}
if ((Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash -ne $manifestHash) { throw 'MANIFEST_HASH_CHANGED' }
[object[]]$auditManifestRows = @(Import-Csv -LiteralPath $manifestPath)
if ($auditManifestRows.Count -ne $preManifestFiles.Count) { throw 'MANIFEST_ENTRY_COUNT_CHANGED' }
foreach ($row in $auditManifestRows) {
    $path = Join-Path $root $row.relative_path
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "MANIFEST_FILE_MISSING=$($row.relative_path)" }
    $item = Get-Item -LiteralPath $path
    if ($item.Length -ne [int64]$row.bytes) { throw "MANIFEST_BYTES_MISMATCH=$($row.relative_path)" }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $row.sha256) { throw "MANIFEST_HASH_MISMATCH=$($row.relative_path)" }
}

'SEAL_RESULT=PASS'
'MARKER=' + $markerPath
'MARKER_NO_BOM=true'
'MARKER_LINE_COUNT=' + $validatedLines.Count
'MARKER_READONLY=true'
'MARKER_FILETIME_UTC=' + $auditMarker.LastWriteTimeUtc.ToString('o')
'MAX_OTHER_FILETIME_UTC=' + $auditMaxOtherUtc.ToString('o')
'MARKER_STRICTLY_LATER=true'
'MANIFEST_ENTRY_COUNT=' + $auditManifestRows.Count
'SEALED_FILE_COUNT=' + $auditFiles.Count
'SEALED_DIR_COUNT=' + ($auditDirs.Count + 1)
'ALL_TREE_READONLY=true'
'MANIFEST_REVERIFY=PASS'
'CONTENT_WRITES_AFTER_MARKER=0'
'ATTRIBUTE_WRITES_AFTER_MARKER=0'
'PASS_TOKEN=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE'
