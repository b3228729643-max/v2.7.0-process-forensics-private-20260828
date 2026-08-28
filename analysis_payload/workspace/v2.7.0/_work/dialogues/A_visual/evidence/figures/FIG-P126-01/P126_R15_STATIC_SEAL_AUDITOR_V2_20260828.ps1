Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R15_SA2_STATIC_FORGET_PLOT_PATCH_R115_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$manifest = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$sealAudit = Join-Path $root 'SEAL_AUDIT.json'
$marker = Join-Path $root 'WRITE_STOPPED'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R15_STATIC_WSTOP_STAGE_20260828.tmp'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R15_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R15_STATIC_SEAL_AUDITOR_V2_RESULT_20260828.json'
$controls = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')

function Sha([string]$path) {
  return (Get-FileHash -LiteralPath $path -Algorithm SHA256 -ErrorAction Stop).Hash.ToUpperInvariant()
}

function Write-Utf8NoBom([string]$path, [string]$text) {
  [IO.File]::WriteAllText($path, $text, [Text.UTF8Encoding]::new($false))
}

function Relative-Path([string]$path) {
  $relative = [IO.Path]::GetRelativePath($root, $path).Replace('\', '/')
  if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative)) { throw "BAD_RELATIVE:$relative" }
  if (@($relative.Split('/') | Where-Object { [string]::IsNullOrEmpty($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw "BAD_SEGMENT:$relative" }
  return $relative
}

function Ads-Count([string]$path) {
  return @((Get-Item -LiteralPath $path -Stream * -Force -ErrorAction Stop) | Where-Object { $_.Stream -ne ':$DATA' }).Count
}

function Snapshot {
  $rows = [Collections.Generic.List[string]]::new()
  foreach ($file in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)) {
    $rows.Add("F`t$(Relative-Path $file.FullName)`t$($file.Length)`t$(Sha $file.FullName)`t$($file.CreationTimeUtc.Ticks)`t$($file.LastWriteTimeUtc.Ticks)`t$([int]$file.Attributes)")
  }
  $directories = @((Get-Item -LiteralPath $root -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
  foreach ($directory in $directories) {
    $relative = if ($directory.FullName -eq $root) { '.' } else { Relative-Path $directory.FullName }
    $rows.Add("D`t$relative`t0`t-`t$($directory.CreationTimeUtc.Ticks)`t$($directory.LastWriteTimeUtc.Ticks)`t$([int]$directory.Attributes)")
  }
  $array = $rows.ToArray()
  [Array]::Sort($array, [StringComparer]::Ordinal)
  $bytes = [Text.UTF8Encoding]::new($false).GetBytes(([string]::Join("`n", $array)) + "`n")
  return [ordered]@{ entries = $array.Count; sha256 = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) }
}

if (Test-Path -LiteralPath $stage) { throw 'STAGE_EXISTS' }
if (Test-Path -LiteralPath $resultPath) { throw 'RESULT_EXISTS' }
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 10 -ErrorAction Stop
if (-not $controllerResult.success -or $controllerResult.invocation_count -ne 1 -or $controllerResult.retry_count -ne 0) { throw 'CONTROLLER_RESULT' }

$manifestRows = @(Import-Csv -LiteralPath $manifest -ErrorAction Stop)
if (@($manifestRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'MANIFEST_DUPLICATE' }
$payloadFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object { $controls -cnotcontains $_.Name })
$payloadMap = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($file in $payloadFiles) { $payloadMap.Add((Relative-Path $file.FullName), $file) }
if ($payloadMap.Count -ne $manifestRows.Count) { throw 'MANIFEST_SET_COUNT' }
$identityMismatch = 0
foreach ($row in $manifestRows) {
  $key = [string]$row.relative_path
  if (-not $payloadMap.ContainsKey($key)) { throw "PAYLOAD_MISSING:$key" }
  $file = $payloadMap[$key]
  if ([long]$row.bytes -ne $file.Length -or [string]$row.sha256 -cne (Sha $file.FullName) -or [long]$row.creation_time_utc_ticks -ne $file.CreationTimeUtc.Ticks -or [long]$row.last_write_time_utc_ticks -ne $file.LastWriteTimeUtc.Ticks) { $identityMismatch++ }
}
if ($identityMismatch -ne 0) { throw 'MANIFEST_IDENTITY' }

$files = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$directories = @((Get-Item -LiteralPath $root -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
$fileReadonlyFailures = @($files | Where-Object { -not $_.IsReadOnly }).Count
$directoryReadonlyFailures = @($directories | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count
if ($fileReadonlyFailures -ne 0 -or $directoryReadonlyFailures -ne 0) { throw 'READONLY' }

$markerItem = Get-Item -LiteralPath $marker -Force -ErrorAction Stop
$markerLines = @([IO.File]::ReadAllLines($marker, [Text.UTF8Encoding]::new($false)))
$markerMap = [Collections.Generic.Dictionary[string, string]]::new([StringComparer]::Ordinal)
foreach ($line in $markerLines) {
  if ($line -notmatch '^[A-Z0-9_]+=[^=].*$') { throw 'MARKER_BAD_LINE' }
  $parts = $line -split '=', 2
  if ($markerMap.ContainsKey($parts[0])) { throw 'MARKER_DUPLICATE_KEY' }
  $markerMap.Add($parts[0], $parts[1])
}
$requiredKeys = @('SCHEMA','HANDOFF_ID','STATUS','ROOT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','MANIFEST_SHA256','SEAL_AUDIT_SHA256','SOURCE_BEFORE_BYTES','SOURCE_BEFORE_SHA256','SOURCE_AFTER_BYTES','SOURCE_AFTER_SHA256','INCREMENTAL_DIFF_ADDITIONS','INCREMENTAL_DIFF_DELETIONS','ORDINARY_ADDPLOTS','ORDINARY_ADDPLOTS_WITH_FORGET_PLOT','MANUAL_LEGEND_IMAGES','LEGEND_ENTRIES','RENDER_VALIDATION_PENDING','TEX_BUILD_COUNT','CONTROLLER_INVOCATION','RETRY_COUNT','PREMARKER_TREE_READONLY','MARKER_LAST_WRITE_UTC_TICKS')
if ($markerMap.Count -ne $requiredKeys.Count -or @($requiredKeys | Where-Object { -not $markerMap.ContainsKey($_) }).Count -ne 0) { throw 'MARKER_KEY_SET' }
if ($markerMap['STATUS'] -cne 'STATIC_ONLY_NOT_RENDERED_NOT_PASS' -or [int]$markerMap['PAYLOAD_COUNT'] -ne $manifestRows.Count -or [int]$markerMap['CONTROL_COUNT'] -ne 3 -or [int]$markerMap['ORDINARY_COUNT'] -ne $files.Count) { throw 'MARKER_COUNTS' }
if ($markerMap['MANIFEST_SHA256'] -cne (Sha $manifest) -or $markerMap['SEAL_AUDIT_SHA256'] -cne (Sha $sealAudit)) { throw 'MARKER_HASH' }
if ([long]$markerMap['MARKER_LAST_WRITE_UTC_TICKS'] -ne $markerItem.LastWriteTimeUtc.Ticks) { throw 'MARKER_TICKS' }

$atOrAfter = 0
$maxNonMarkerTicks = [long]0
foreach ($item in @($files | Where-Object { $_.FullName -ne $marker }) + $directories) {
  if ($item.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks) { $atOrAfter++ }
  if ($item.LastWriteTimeUtc.Ticks -gt $maxNonMarkerTicks) { $maxNonMarkerTicks = $item.LastWriteTimeUtc.Ticks }
}
$strictMargin = $markerItem.LastWriteTimeUtc.Ticks - $maxNonMarkerTicks
if ($atOrAfter -ne 0 -or $strictMargin -le 0) { throw 'MARKER_NOT_LATEST' }

$csvFailures = 0
foreach ($file in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object -Property Extension -EQ '.csv')) {
  try { $null = @(Import-Csv -LiteralPath $file.FullName -ErrorAction Stop) } catch { $csvFailures++ }
}
$jsonFailures = 0
foreach ($file in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object -Property Extension -EQ '.json')) {
  try { $null = Get-Content -LiteralPath $file.FullName -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 30 -ErrorAction Stop } catch { $jsonFailures++ }
}
$adsNondefault = 0
foreach ($item in @($files + $directories)) { $adsNondefault += Ads-Count $item.FullName }
$cachePycReparse = @(Get-ChildItem -LiteralPath $root -Force -Recurse -ErrorAction Stop | Where-Object { $_.Name -eq '__pycache__' -or $_.Extension -in @('.pyc','.pyo') -or ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($csvFailures -ne 0 -or $jsonFailures -ne 0 -or $adsNondefault -ne 0 -or $cachePycReparse -ne 0) { throw 'HYGIENE' }

$snapshot1 = Snapshot
Start-Sleep -Milliseconds 300
$snapshot2 = Snapshot
if ($snapshot1.sha256 -ne $snapshot2.sha256 -or $snapshot1.sha256 -cne [string]$controllerResult.snapshot_sha256) { throw 'POSTMARKER_SNAPSHOT' }
if ((Get-Item -LiteralPath $source -Force).Length -ne 4686 -or (Sha $source) -ne '2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405') { throw 'SOURCE_IDENTITY' }

$result = [ordered]@{
  schema = 'P126_R15_STATIC_SEAL_AUDITOR_V2_RESULT_V1'
  success = $true
  handoff_id = 'A-R115-P126-SA2-STATIC-FORGET-PLOT-PATCH-20260828'
  status = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  payload_count = $manifestRows.Count
  control_count = 3
  ordinary_count = $files.Count
  directory_count_including_root = $directories.Count
  manifest_identity_mismatch = $identityMismatch
  file_readonly_failures = $fileReadonlyFailures
  directory_readonly_failures = $directoryReadonlyFailures
  marker_lines = $markerLines.Count
  marker_keys = $markerMap.Count
  marker_sha256 = Sha $marker
  strict_latest_margin_ticks = $strictMargin
  at_or_after_excluding_marker = $atOrAfter
  postmarker_snapshot_entries = $snapshot1.entries
  postmarker_snapshot_sha256 = $snapshot1.sha256
  postmarker_drift = 0
  csv_parse_failures = $csvFailures
  json_parse_failures = $jsonFailures
  ads_nondefault = $adsNondefault
  cache_pyc_reparse = $cachePycReparse
  source_identity_mismatch = 0
  invocation_count = 1
  retry_count = 0
  superseded_auditor_v1_exit = 1
  superseded_auditor_v1_root_writes = 0
}
Write-Utf8NoBom $resultPath (($result | ConvertTo-Json -Depth 5) + "`n")
