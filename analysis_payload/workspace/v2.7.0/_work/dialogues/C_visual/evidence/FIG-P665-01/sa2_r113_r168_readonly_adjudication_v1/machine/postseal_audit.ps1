$ErrorActionPreference = 'Stop'
$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa2_r113_r168_readonly_adjudication_v1'
$Manifest = Join-Path $Root 'SEALED_MANIFEST.csv'
$Marker = Join-Path $Root 'FINAL_MARKER.txt'
$ExpectedKeys = @('HANDOFF_ID','UID','SEALED_ROOT','MANIFEST_ROWS','MANIFEST_SHA256','VERDICT')

$MarkerLines = @(Get-Content -LiteralPath $Marker)
$MarkerMap = @{}
$MalformedMarkerLines = 0
foreach ($Line in $MarkerLines) {
    if ($Line.Contains("`t") -or $Line -notmatch '^([A-Z][A-Z0-9_]*)=([^=\r\n]+)$' -or $Line -match 'TODO|TBD|PLACEHOLDER|UNKNOWN') {
        $MalformedMarkerLines++
        continue
    }
    $Key = $Matches[1]
    $Value = $Matches[2]
    if ($MarkerMap.ContainsKey($Key) -or [string]::IsNullOrWhiteSpace($Value)) { $MalformedMarkerLines++ } else { $MarkerMap[$Key] = $Value }
}
$MarkerKeyDifferences = @(Compare-Object ($ExpectedKeys | Sort-Object) ($MarkerMap.Keys | Sort-Object)).Count

function Get-Sha256([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Relative([string]$Path) { return $Path.Substring($Root.Length + 1).Replace('\','/') }

$Rows = @(Import-Csv -LiteralPath $Manifest)
$AllFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -File)
$PayloadFiles = @($AllFiles | Where-Object { $_.FullName -ne $Manifest -and $_.FullName -ne $Marker })
$ManifestSet = @($Rows.relative_path | Sort-Object)
$FileSet = @($PayloadFiles | ForEach-Object { Relative $_.FullName } | Sort-Object)
$SetDifferences = @(Compare-Object $ManifestSet $FileSet).Count

$IdentityDifferences = 0
foreach ($Row in $Rows) {
    $Path = Join-Path $Root ($Row.relative_path.Replace('/','\'))
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { $IdentityDifferences++; continue }
    $Info = Get-Item -LiteralPath $Path
    if ($Info.Length -ne [int64]$Row.bytes) { $IdentityDifferences++ }
    if ((Get-Sha256 $Path) -ne $Row.sha256) { $IdentityDifferences++ }
    if ([IO.File]::GetCreationTimeUtc($Path).ToFileTimeUtc() -ne [int64]$Row.creation_filetime_utc_ticks) { $IdentityDifferences++ }
    if ([IO.File]::GetLastWriteTimeUtc($Path).ToFileTimeUtc() -ne [int64]$Row.last_write_filetime_utc_ticks) { $IdentityDifferences++ }
}

$AllDirectories = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory)
$NonReadonlyFiles = @($AllFiles | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count
$NonReadonlyDirectories = @($AllDirectories | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count
$Reparse = @($AllFiles + $AllDirectories | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
$CachePyc = @($AllFiles | Where-Object { $_.FullName -match '(^|[\\/])(__pycache__|\.cache)([\\/]|$)|\.(pyc|pyo)$|\.tmp$|~$' }).Count
$AdditionalAds = 0
foreach ($File in $AllFiles) {
    $Streams = @(Get-Item -LiteralPath $File.FullName -Stream * -ErrorAction SilentlyContinue)
    $AdditionalAds += @($Streams | Where-Object { $_.Stream -ne ':$DATA' }).Count
}

$MarkerInfo = Get-Item -LiteralPath $Marker
$MarkerTicks = [IO.File]::GetLastWriteTimeUtc($Marker).ToFileTimeUtc()
$AtOrAfterExcludingMarker = @($AllFiles | Where-Object { $_.FullName -ne $Marker -and [IO.File]::GetLastWriteTimeUtc($_.FullName).ToFileTimeUtc() -ge $MarkerTicks }).Count
$MarkerNamedFiles = @($AllFiles | Where-Object { $_.Name -like '*MARKER*' }).Count
$ManifestShaDifference = if ((Get-Sha256 $Manifest) -eq $MarkerMap['MANIFEST_SHA256']) { 0 } else { 1 }
$ManifestRowDifference = if ($Rows.Count -eq [int]$MarkerMap['MANIFEST_ROWS']) { 0 } else { 1 }

$Result = [ordered]@{
    marker_physical_lines = $MarkerLines.Count
    malformed_marker_lines = $MalformedMarkerLines
    marker_key_differences = $MarkerKeyDifferences
    marker_named_file_count = $MarkerNamedFiles
    marker_is_unique_and_latest = if ($MarkerNamedFiles -eq 1 -and $AtOrAfterExcludingMarker -eq 0) { 1 } else { 0 }
    at_or_after_marker_excluding_marker = $AtOrAfterExcludingMarker
    manifest_rows = $Rows.Count
    manifest_row_difference = $ManifestRowDifference
    manifest_sha256_difference = $ManifestShaDifference
    manifest_filesystem_set_differences = $SetDifferences
    manifest_identity_differences = $IdentityDifferences
    nonreadonly_file_count = $NonReadonlyFiles
    nonreadonly_directory_count = $NonReadonlyDirectories
    postmarker_content_changes = $SetDifferences + $IdentityDifferences
    postmarker_attribute_changes = $NonReadonlyFiles + $NonReadonlyDirectories
    additional_ads_count = $AdditionalAds
    cache_pyc_count = $CachePyc
    reparse_point_count = $Reparse
    marker_last_write_filetime_utc_ticks = $MarkerTicks
    HANDOFF_ID = $MarkerMap['HANDOFF_ID']
    UID = $MarkerMap['UID']
    SEALED_ROOT = $MarkerMap['SEALED_ROOT']
    MANIFEST_ROWS = $MarkerMap['MANIFEST_ROWS']
    MANIFEST_SHA256 = $MarkerMap['MANIFEST_SHA256']
    VERDICT = $MarkerMap['VERDICT']
}
$Result | ConvertTo-Json -Depth 4
