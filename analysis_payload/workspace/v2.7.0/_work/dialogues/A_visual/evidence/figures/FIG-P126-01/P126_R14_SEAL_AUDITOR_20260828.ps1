Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R14_SA2_DISCONNECTED_LEGEND_HANDLER_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$pdf = Join-Path $root 'build\v260_FIG-P126-01_standalone.pdf'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R14_WRITE_STOPPED_STAGE_20260828.tmp'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R14_SEAL_CONTROLLER_RESULT_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R14_SEAL_AUDITOR_RESULT_20260828.json'
$manifestCsv = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $root 'PAYLOAD_MANIFEST.json'
$sealAudit = Join-Path $root 'SEAL_AUDIT.json'
$marker = Join-Path $root 'WRITE_STOPPED'
$controls = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')

function Sha256([string]$path) {
  return (Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpperInvariant()
}

function Write-Utf8NoBom([string]$path, [string]$text) {
  [IO.File]::WriteAllText($path, $text, [Text.UTF8Encoding]::new($false))
}

function Canonical-Relative([string]$base, [string]$path) {
  $relative = [IO.Path]::GetRelativePath($base, $path).Replace('\', '/')
  while ($relative.StartsWith('./', [StringComparison]::Ordinal)) { $relative = $relative.Substring(2) }
  if ([string]::IsNullOrWhiteSpace($relative)) { throw 'EMPTY_RELATIVE_PATH' }
  if ([IO.Path]::IsPathRooted($relative) -or $relative.StartsWith('/', [StringComparison]::Ordinal)) { throw "ROOTED_RELATIVE_PATH:$relative" }
  $segments = $relative.Split('/')
  if (@($segments | Where-Object { [string]::IsNullOrEmpty($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw "UNSAFE_RELATIVE_PATH:$relative" }
  $resolvedBase = [IO.Path]::GetFullPath($base).TrimEnd('\')
  $resolvedPath = [IO.Path]::GetFullPath($path)
  if (-not $resolvedPath.StartsWith($resolvedBase + '\', [StringComparison]::OrdinalIgnoreCase)) { throw "ESCAPE_PATH:$relative" }
  return $relative
}

function Get-AdsNondefaultCount([string]$path) {
  $streams = @(Get-Item -LiteralPath $path -Stream * -Force -ErrorAction Stop)
  return @($streams | Where-Object { $_.Stream -ne ':$DATA' }).Count
}

function Snapshot-Hash([string]$base) {
  $rows = [Collections.Generic.List[string]]::new()
  foreach ($file in @(Get-ChildItem -LiteralPath $base -File -Recurse -Force -ErrorAction Stop)) {
    $relative = Canonical-Relative $base $file.FullName
    $rows.Add("F`t$relative`t$($file.Length)`t$(Sha256 $file.FullName)`t$($file.CreationTimeUtc.Ticks)`t$($file.LastWriteTimeUtc.Ticks)`t$([int]$file.Attributes)")
  }
  foreach ($dir in @((Get-Item -LiteralPath $base -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $base -Directory -Recurse -Force -ErrorAction Stop)) {
    $relative = if ($dir.FullName -eq $base) { '.' } else { Canonical-Relative $base $dir.FullName }
    $rows.Add("D`t$relative`t0`t-`t$($dir.CreationTimeUtc.Ticks)`t$($dir.LastWriteTimeUtc.Ticks)`t$([int]$dir.Attributes)")
  }
  $array = $rows.ToArray()
  [Array]::Sort($array, [StringComparer]::Ordinal)
  $bytes = [Text.UTF8Encoding]::new($false).GetBytes(([string]::Join("`n", $array)) + "`n")
  return [ordered]@{ entries = $array.Count; sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) }
}

if (Test-Path -LiteralPath $auditResultPath) { throw 'AUDITOR_RESULT_EXISTS' }
if (Test-Path -LiteralPath $stage) { throw 'STAGE_STILL_EXISTS' }
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 10 -ErrorAction Stop
if (-not $controllerResult.success -or $controllerResult.invocation_count -ne 1 -or $controllerResult.retry_count -ne 0) { throw 'CONTROLLER_RESULT_BINDING' }
foreach ($path in @($manifestCsv, $manifestJson, $sealAudit, $marker)) { if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "CONTROL_MISSING:$path" } }

$csvRows = @(Import-Csv -LiteralPath $manifestCsv -ErrorAction Stop)
$jsonObject = Get-Content -LiteralPath $manifestJson -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 20 -ErrorAction Stop
$jsonRows = @($jsonObject.rows)
if ($csvRows.Count -ne $jsonRows.Count) { throw 'DUAL_MANIFEST_COUNT' }
if (@($csvRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'CSV_MANIFEST_DUPLICATE' }
if (@($jsonRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'JSON_MANIFEST_DUPLICATE' }
$csvMap = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($row in $csvRows) { $csvMap.Add([string]$row.relative_path, $row) }
$jsonMap = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($row in $jsonRows) { $jsonMap.Add([string]$row.relative_path, $row) }
if ($csvMap.Count -ne $jsonMap.Count) { throw 'DUAL_MANIFEST_SET_COUNT' }
foreach ($key in $csvMap.Keys) {
  if (-not $jsonMap.ContainsKey($key)) { throw "JSON_MANIFEST_MISSING:$key" }
  $a = $csvMap[$key]
  $b = $jsonMap[$key]
  if ([long]$a.bytes -ne [long]$b.bytes -or [string]$a.sha256 -cne [string]$b.sha256 -or [long]$a.creation_time_utc_ticks -ne [long]$b.creation_time_utc_ticks -or [long]$a.last_write_time_utc_ticks -ne [long]$b.last_write_time_utc_ticks) { throw "DUAL_MANIFEST_IDENTITY:$key" }
}

$payloadFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object { $controls -cnotcontains $_.Name })
$actualMap = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($file in $payloadFiles) { $actualMap.Add((Canonical-Relative $root $file.FullName), $file) }
if ($actualMap.Count -ne $csvMap.Count) { throw 'MANIFEST_FS_SET_COUNT' }
$identityMismatch = 0
foreach ($key in $csvMap.Keys) {
  if (-not $actualMap.ContainsKey($key)) { throw "PAYLOAD_MISSING:$key" }
  $row = $csvMap[$key]
  $file = $actualMap[$key]
  if ([long]$row.bytes -ne $file.Length -or [string]$row.sha256 -cne (Sha256 $file.FullName) -or [long]$row.creation_time_utc_ticks -ne $file.CreationTimeUtc.Ticks -or [long]$row.last_write_time_utc_ticks -ne $file.LastWriteTimeUtc.Ticks) { $identityMismatch++ }
}
if ($identityMismatch -ne 0) { throw 'MANIFEST_FS_IDENTITY' }

$allFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$allDirs = @((Get-Item -LiteralPath $root -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
$fileRoFailures = @($allFiles | Where-Object { -not $_.IsReadOnly }).Count
$dirRoFailures = @($allDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count
if ($fileRoFailures -ne 0 -or $dirRoFailures -ne 0) { throw 'READONLY_FAILURE' }

$markerItem = Get-Item -LiteralPath $marker -Force -ErrorAction Stop
$markerLines = @([IO.File]::ReadAllLines($marker, [Text.UTF8Encoding]::new($false)))
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=].*$' }).Count -ne 0) { throw 'MARKER_BAD_LINE' }
$markerMap = [Collections.Generic.Dictionary[string, string]]::new([StringComparer]::Ordinal)
foreach ($line in $markerLines) {
  $parts = $line -split '=', 2
  if ($markerMap.ContainsKey($parts[0])) { throw "MARKER_DUPLICATE:$($parts[0])" }
  $markerMap.Add($parts[0], $parts[1])
}
$requiredKeys = @('SCHEMA','HANDOFF_ID','STATUS','HARD_DEFECT_COUNT','HARD_DEFECT_ID','ROOT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','MANIFEST_CSV_SHA256','MANIFEST_JSON_SHA256','SEAL_AUDIT_SHA256','SOURCE_BYTES','SOURCE_SHA256','PDF_BYTES','PDF_SHA256','OBJECT_DENOMINATOR','UNORDERED_PAIRS','X2_LEGEND_OCCUPIED_RUNS','X2_LEGEND_OCCUPIED_LENGTH_PX','X2_LEGEND_INTERNAL_BLANK_RUNS','CONTROLLER_INVOCATION','RETRY_COUNT','BUSINESS_EVIDENCE_RERUN','PREMARKER_FILES_READONLY','PREMARKER_DIRS_READONLY','MARKER_LAST_WRITE_UTC_TICKS')
if ($markerMap.Count -ne $requiredKeys.Count -or @($requiredKeys | Where-Object { -not $markerMap.ContainsKey($_) }).Count -ne 0) { throw 'MARKER_KEY_SET' }
if ($markerMap['STATUS'] -cne 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE' -or $markerMap['HARD_DEFECT_ID'] -cne 'HARD-LEGEND-X2-CONTINUOUS') { throw 'MARKER_VERDICT' }
if ([int]$markerMap['PAYLOAD_COUNT'] -ne $csvRows.Count -or [int]$markerMap['CONTROL_COUNT'] -ne 4 -or [int]$markerMap['ORDINARY_COUNT'] -ne $allFiles.Count) { throw 'MARKER_COUNTS' }
if ($markerMap['MANIFEST_CSV_SHA256'] -cne (Sha256 $manifestCsv) -or $markerMap['MANIFEST_JSON_SHA256'] -cne (Sha256 $manifestJson) -or $markerMap['SEAL_AUDIT_SHA256'] -cne (Sha256 $sealAudit)) { throw 'MARKER_CONTROL_HASH' }
if ([long]$markerMap['MARKER_LAST_WRITE_UTC_TICKS'] -ne $markerItem.LastWriteTimeUtc.Ticks) { throw 'MARKER_TICKS_BINDING' }

$atOrAfter = 0
$maxNonMarkerTicks = [long]0
foreach ($item in @($allFiles | Where-Object { $_.FullName -ne $marker }) + $allDirs) {
  if ($item.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks) { $atOrAfter++ }
  if ($item.LastWriteTimeUtc.Ticks -gt $maxNonMarkerTicks) { $maxNonMarkerTicks = $item.LastWriteTimeUtc.Ticks }
}
$strictMargin = $markerItem.LastWriteTimeUtc.Ticks - $maxNonMarkerTicks
if ($atOrAfter -ne 0 -or $strictMargin -le 0) { throw 'MARKER_STRICT_LATEST' }

$csvFailures = 0
foreach ($item in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object Extension -eq '.csv')) { try { $null = @(Import-Csv -LiteralPath $item.FullName -ErrorAction Stop) } catch { $csvFailures++ } }
$jsonFailures = 0
foreach ($item in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object Extension -eq '.json')) { try { $null = Get-Content -LiteralPath $item.FullName -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 30 -ErrorAction Stop } catch { $jsonFailures++ } }
$adsNondefault = 0
foreach ($item in @($allFiles + $allDirs)) { $adsNondefault += Get-AdsNondefaultCount $item.FullName }
$forbiddenCache = @(Get-ChildItem -LiteralPath $root -Force -Recurse -ErrorAction Stop | Where-Object { $_.Name -eq '__pycache__' -or $_.Extension -in @('.pyc', '.pyo') }).Count
$reparseCount = @($allFiles + $allDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($csvFailures -ne 0 -or $jsonFailures -ne 0 -or $adsNondefault -ne 0 -or $forbiddenCache -ne 0 -or $reparseCount -ne 0) { throw 'PARSE_HYGIENE_FAILURE' }

$snapshotA = Snapshot-Hash $root
Start-Sleep -Milliseconds 300
$snapshotB = Snapshot-Hash $root
if ($snapshotA.sha256 -ne $snapshotB.sha256 -or $snapshotA.entries -ne $snapshotB.entries) { throw 'POSTMARKER_DRIFT' }
if ($snapshotA.sha256 -cne [string]$controllerResult.snapshot1_sha256 -or $snapshotA.sha256 -cne [string]$controllerResult.snapshot2_sha256) { throw 'CONTROLLER_AUDITOR_SNAPSHOT' }
if ((Get-Item -LiteralPath $source -Force).Length -ne 4626 -or (Sha256 $source) -ne '6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502') { throw 'SOURCE_IDENTITY' }
if ((Get-Item -LiteralPath $pdf -Force).Length -ne 34054 -or (Sha256 $pdf) -ne '204CC34980BF059DFFA4016314C1FBFEFC94A0066C01FF7E77A4A26946B65F3D') { throw 'PDF_IDENTITY' }

$result = [ordered]@{
  schema = 'P126_R14_SEAL_AUDITOR_RESULT_V1'
  success = $true
  handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R14-20260828'
  status = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
  hard_defect_id = 'HARD-LEGEND-X2-CONTINUOUS'
  payload_count = $csvRows.Count
  control_count = 4
  ordinary_count = $allFiles.Count
  directory_count_including_root = $allDirs.Count
  manifest_identity_mismatch = $identityMismatch
  file_readonly_failures = $fileRoFailures
  directory_readonly_failures = $dirRoFailures
  marker_lines = $markerLines.Count
  marker_keys = $markerMap.Count
  marker_sha256 = Sha256 $marker
  marker_ticks = $markerItem.LastWriteTimeUtc.Ticks
  strict_latest_margin_ticks = $strictMargin
  at_or_after_excluding_marker = $atOrAfter
  postmarker_snapshot_entries = $snapshotA.entries
  postmarker_snapshot_sha256 = $snapshotA.sha256
  postmarker_content_attribute_drift = 0
  csv_parse_failures = $csvFailures
  json_parse_failures = $jsonFailures
  ads_nondefault = $adsNondefault
  forbidden_cache_pyc = $forbiddenCache
  reparse_count = $reparseCount
  source_identity_mismatch = 0
  pdf_identity_mismatch = 0
  invocation_count = 1
  retry_count = 0
}
Write-Utf8NoBom $auditResultPath (($result | ConvertTo-Json -Depth 6) + "`n")
