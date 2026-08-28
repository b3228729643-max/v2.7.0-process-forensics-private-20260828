$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa1_r112_fresh_isolated_v1'
$parent = Split-Path -Parent $root
$manifest = Join-Path $root 'controls\manifest.csv'
$markerName = 'WRITE_STOPPED'
$markerFinal = Join-Path $root $markerName
$markerExternal = Join-Path $parent '.sa1_r112_fresh_isolated_v1.WRITE_STOPPED.precreated'

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'authorized root missing' }
if (Test-Path -LiteralPath $manifest) { throw 'manifest already exists; refuse second seal attempt' }
if (Test-Path -LiteralPath $markerFinal) { throw 'final marker already exists; refuse second seal attempt' }
if (Test-Path -LiteralPath $markerExternal) { throw 'external precreated marker already exists; refuse ambiguous seal attempt' }

$payload = Get-ChildItem -LiteralPath $root -Recurse -Force -File | Sort-Object FullName
$manifestLines = @('"relative_path","bytes","sha256","last_write_filetime_utc_ticks","creation_filetime_utc_ticks"')
foreach ($file in $payload) {
    $rel = $file.FullName.Substring($root.Length + 1).Replace('\','/')
    $relEscaped = $rel.Replace('"','""')
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
    $lwt = $file.LastWriteTimeUtc.ToFileTimeUtc()
    $ct = $file.CreationTimeUtc.ToFileTimeUtc()
    $manifestLines += ('"' + $relEscaped + '","' + $file.Length + '","' + $hash + '","' + $lwt + '","' + $ct + '"')
}
Set-Content -LiteralPath $manifest -Value $manifestLines -Encoding utf8NoBOM

$manifestRows = (Import-Csv -LiteralPath $manifest).Count
if ($manifestRows -ne $payload.Count) { throw "manifest row mismatch: $manifestRows vs $($payload.Count)" }
$manifestHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash

$latestPayloadFiletime = ($payload | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
$manifestFiletime = (Get-Item -LiteralPath $manifest).LastWriteTimeUtc.ToFileTimeUtc()
if ($manifestFiletime -gt $latestPayloadFiletime) { $latestPayloadFiletime = $manifestFiletime }
$markerTime = [datetime]::FromFileTimeUtc([int64]$latestPayloadFiletime).AddSeconds(10)

$markerLines = @(
    'WRITE_STOPPED',
    'HANDOFF_ID=C-FIG-P662-01-R112-SA1-FRESH-ISOLATED-V1',
    'CANONICAL_INSTANCE=/root/sa1_fig_p662_r112_fresh_isolated_v1',
    'UID=FIG-P662-01',
    'ROLE=FRESH_ISOLATED_SA1',
    'MODEL=gpt-5.6-sol',
    'REASONING=xhigh',
    'SEALED_ROOT=' + $root,
    'OFFICIAL_R112_PDF_BYTES=4967100',
    'OFFICIAL_R112_PDF_SHA256=D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2',
    'CURRENT_SOURCE_BYTES=3588',
    'CURRENT_SOURCE_SHA256=B5232526402FEF6735DC3F9C07B418D7BF49E0D8C17EAEFB82A54B450B63113E',
    'PHYSICAL_PAGE=710',
    'PRINTED_PAGE=697',
    'FIGURE_NUMBER=34.5',
    'VISIBLE_OBJECTS=25',
    'TEXT_ELEMENTS=21',
    'ALL_UNORDERED_PAIRS=300',
    'MANUAL_PAIR_IDS=300',
    'LEGAL_ENDPOINT_CONTACT_PAIRS=16',
    'BBOX_ONLY_FALSE_POSITIVE_PAIRS=3',
    'HARD_ILLEGAL_COLLISION_PAIRS=0',
    'HARD_ILLEGAL_COLLISION_PIXELS=0',
    'CLIPPED_FOREGROUND_PIXELS=0',
    'UNRESOLVED_PAIRS=0',
    'FINAL_VIEWS_OPENED=20',
    'NATIVE_RISK_ROIS=6',
    'NEAREST8X_RISK_ROIS=6',
    'MANIFEST_RELATIVE_PATH=controls/manifest.csv',
    'MANIFEST_ROWS=' + $manifestRows,
    'MANIFEST_SHA256=' + $manifestHash,
    'VERDICT=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
)
Set-Content -LiteralPath $markerExternal -Value $markerLines -Encoding utf8NoBOM
Set-ItemProperty -LiteralPath $markerExternal -Name LastWriteTimeUtc -Value $markerTime
Set-ItemProperty -LiteralPath $markerExternal -Name IsReadOnly -Value $true

$allFilesBeforeMarker = Get-ChildItem -LiteralPath $root -Recurse -Force -File
foreach ($file in $allFilesBeforeMarker) {
    Set-ItemProperty -LiteralPath $file.FullName -Name IsReadOnly -Value $true
}
$allDirsBeforeMarker = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory | Sort-Object FullName -Descending)
foreach ($dir in $allDirsBeforeMarker) {
    Set-ItemProperty -LiteralPath $dir.FullName -Name Attributes -Value ($dir.Attributes -bor [System.IO.FileAttributes]::ReadOnly)
}
$rootItem = Get-Item -LiteralPath $root
Set-ItemProperty -LiteralPath $root -Name Attributes -Value ($rootItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly)

$preMoveNonReadOnlyFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File | Where-Object { -not $_.IsReadOnly })
$preMoveNonReadOnlyDirs = @((Get-Item -LiteralPath $root); Get-ChildItem -LiteralPath $root -Recurse -Force -Directory) | Where-Object { -not (($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq [System.IO.FileAttributes]::ReadOnly) }
if ($preMoveNonReadOnlyFiles.Count -ne 0 -or $preMoveNonReadOnlyDirs.Count -ne 0) { throw 'pre-move ReadOnly attribute gate failed' }

# Unique absolute last root-content operation. Nothing after this line may write content or attributes.
Move-Item -LiteralPath $markerExternal -Destination $markerFinal

# Read-only verification only from here onward.
$actualFiles = Get-ChildItem -LiteralPath $root -Recurse -Force -File
$actualDirs = @((Get-Item -LiteralPath $root); Get-ChildItem -LiteralPath $root -Recurse -Force -Directory)
$nonReadOnlyFiles = @($actualFiles | Where-Object { -not $_.IsReadOnly })
$nonReadOnlyDirs = @($actualDirs | Where-Object { -not (($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq [System.IO.FileAttributes]::ReadOnly) })
$markers = @($actualFiles | Where-Object { $_.Name -eq $markerName })
$markerItem = Get-Item -LiteralPath $markerFinal
$markerFiletime = $markerItem.LastWriteTimeUtc.ToFileTimeUtc()
$otherAtOrAfter = @($actualFiles | Where-Object { $_.FullName -ne $markerFinal -and $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerFiletime })

$manifestData = Import-Csv -LiteralPath $manifest
$identityDiffs = @()
foreach ($row in $manifestData) {
    $path = Join-Path $root ($row.relative_path.Replace('/','\'))
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        $identityDiffs += 'missing:' + $row.relative_path
        continue
    }
    $item = Get-Item -LiteralPath $path
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
    if ([string]$item.Length -ne [string]$row.bytes) { $identityDiffs += 'bytes:' + $row.relative_path }
    if ($hash -ne $row.sha256) { $identityDiffs += 'sha256:' + $row.relative_path }
    if ([string]$item.LastWriteTimeUtc.ToFileTimeUtc() -ne [string]$row.last_write_filetime_utc_ticks) { $identityDiffs += 'lwt:' + $row.relative_path }
    if ([string]$item.CreationTimeUtc.ToFileTimeUtc() -ne [string]$row.creation_filetime_utc_ticks) { $identityDiffs += 'ctime:' + $row.relative_path }
}

$expectedSet = @($manifestData | ForEach-Object { $_.relative_path }) + @('controls/manifest.csv', $markerName)
$actualSet = @($actualFiles | ForEach-Object { $_.FullName.Substring($root.Length + 1).Replace('\','/') })
$missingSet = @($expectedSet | Where-Object { $_ -notin $actualSet })
$extraSet = @($actualSet | Where-Object { $_ -notin $expectedSet })
$manifestHashAfter = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash
$manifestHashInMarker = ((Get-Content -LiteralPath $markerFinal | Where-Object { $_ -like 'MANIFEST_SHA256=*' }) -replace '^MANIFEST_SHA256=','')

$namedStreams = @()
foreach ($file in $actualFiles) {
    $namedStreams += @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object { $_.Stream -ne ':$DATA' })
}
$cachePaths = @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.Name -in @('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache','.cache') })
$pycFiles = @($actualFiles | Where-Object { $_.Extension -eq '.pyc' })
$reparsePaths = @($actualDirs + $actualFiles | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -eq [System.IO.FileAttributes]::ReparsePoint })

$verificationErrors = @()
if ($nonReadOnlyFiles.Count -ne 0) { $verificationErrors += 'non_readonly_files' }
if ($nonReadOnlyDirs.Count -ne 0) { $verificationErrors += 'non_readonly_dirs' }
if ($markers.Count -ne 1) { $verificationErrors += 'marker_count' }
if ($markerFiletime -le $latestPayloadFiletime) { $verificationErrors += 'marker_not_strictly_latest' }
if ($otherAtOrAfter.Count -ne 0) { $verificationErrors += 'other_at_or_after_marker' }
if ($identityDiffs.Count -ne 0) { $verificationErrors += 'manifest_identity_diffs' }
if ($missingSet.Count -ne 0) { $verificationErrors += 'manifest_missing_set' }
if ($extraSet.Count -ne 0) { $verificationErrors += 'manifest_extra_set' }
if ($manifestHashAfter -ne $manifestHashInMarker) { $verificationErrors += 'manifest_hash_vs_marker' }
if ($namedStreams.Count -ne 0) { $verificationErrors += 'named_ads' }
if ($cachePaths.Count -ne 0) { $verificationErrors += 'cache_paths' }
if ($pycFiles.Count -ne 0) { $verificationErrors += 'pyc_files' }
if ($reparsePaths.Count -ne 0) { $verificationErrors += 'reparse_paths' }

Write-Output ('SEALED_ROOT=' + $root)
Write-Output ('PAYLOAD_MANIFEST_ROWS=' + $manifestRows)
Write-Output ('ACTUAL_REGULAR_FILES=' + $actualFiles.Count)
Write-Output ('ACTUAL_DIRECTORIES_INCLUDING_ROOT=' + $actualDirs.Count)
Write-Output ('ALL_FILES_READONLY_NONCOMPLIANT=' + $nonReadOnlyFiles.Count)
Write-Output ('ALL_DIRS_READONLY_NONCOMPLIANT=' + $nonReadOnlyDirs.Count)
Write-Output ('MARKER_COUNT=' + $markers.Count)
Write-Output ('MARKER_FILETIME_UTC_TICKS=' + $markerFiletime)
Write-Output ('LATEST_OTHER_FILETIME_UTC_TICKS=' + $latestPayloadFiletime)
Write-Output ('POSTMARKER_AT_OR_AFTER_EXCLUDING_MARKER=' + $otherAtOrAfter.Count)
Write-Output ('MANIFEST_IDENTITY_DIFFS=' + $identityDiffs.Count)
Write-Output ('MANIFEST_SET_MISSING=' + $missingSet.Count)
Write-Output ('MANIFEST_SET_EXTRA=' + $extraSet.Count)
Write-Output ('NAMED_ADS_COUNT=' + $namedStreams.Count)
Write-Output ('CACHE_PATH_COUNT=' + $cachePaths.Count)
Write-Output ('PYC_FILE_COUNT=' + $pycFiles.Count)
Write-Output ('REPARSE_PATH_COUNT=' + $reparsePaths.Count)
Write-Output ('VERIFICATION_ERROR_COUNT=' + $verificationErrors.Count)
if ($verificationErrors.Count -ne 0) {
    Write-Output ('VERIFICATION_ERRORS=' + ($verificationErrors -join ','))
    exit 3
}
Write-Output 'SEALED_VERIFICATION=COMPLETE'
Write-Output 'VERDICT=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
