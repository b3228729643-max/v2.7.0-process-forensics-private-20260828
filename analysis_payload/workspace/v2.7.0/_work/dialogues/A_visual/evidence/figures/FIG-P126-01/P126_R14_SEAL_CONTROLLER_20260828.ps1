Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R14_SA2_DISCONNECTED_LEGEND_HANDLER_R115_DIRECT_BUILD_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$pdf = Join-Path $root 'build\v260_FIG-P126-01_standalone.pdf'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R14_WRITE_STOPPED_STAGE_20260828.tmp'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R14_SEAL_CONTROLLER_RESULT_20260828.json'
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

function Get-TreeSnapshot([string]$base) {
  $rows = [Collections.Generic.List[string]]::new()
  $allFiles = @(Get-ChildItem -LiteralPath $base -File -Recurse -Force -ErrorAction Stop)
  foreach ($file in $allFiles) {
    $relative = Canonical-Relative $base $file.FullName
    $rows.Add("F`t$relative`t$($file.Length)`t$(Sha256 $file.FullName)`t$($file.CreationTimeUtc.Ticks)`t$($file.LastWriteTimeUtc.Ticks)`t$([int]$file.Attributes)")
  }
  $allDirs = @((Get-Item -LiteralPath $base -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $base -Directory -Recurse -Force -ErrorAction Stop)
  foreach ($dir in $allDirs) {
    $relative = if ($dir.FullName -eq $base) { '.' } else { Canonical-Relative $base $dir.FullName }
    $rows.Add("D`t$relative`t0`t-`t$($dir.CreationTimeUtc.Ticks)`t$($dir.LastWriteTimeUtc.Ticks)`t$([int]$dir.Attributes)")
  }
  $array = $rows.ToArray()
  [Array]::Sort($array, [StringComparer]::Ordinal)
  $text = ([string]::Join("`n", $array)) + "`n"
  $bytes = [Text.UTF8Encoding]::new($false).GetBytes($text)
  $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  return [ordered]@{ entries = $array.Count; sha256 = $hash; rows = $array }
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'ROOT_MISSING' }
if (Test-Path -LiteralPath $stage) { throw 'STAGE_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $resultPath) { throw 'RESULT_ALREADY_EXISTS' }
foreach ($control in $controls) {
  if (Test-Path -LiteralPath (Join-Path $root $control)) { throw "CONTROL_ALREADY_EXISTS:$control" }
}

$sourceBefore = Get-Item -LiteralPath $source -Force -ErrorAction Stop
$pdfBefore = Get-Item -LiteralPath $pdf -Force -ErrorAction Stop
if ($sourceBefore.Length -ne 4626 -or (Sha256 $source) -ne '6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502') { throw 'SOURCE_IDENTITY' }
if ($pdfBefore.Length -ne 34054 -or (Sha256 $pdf) -ne '204CC34980BF059DFFA4016314C1FBFEFC94A0066C01FF7E77A4A26946B65F3D') { throw 'PDF_IDENTITY' }

$payloadFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object { $controls -cnotcontains $_.Name })
$payloadRows = @(
  foreach ($file in $payloadFiles) {
    [pscustomobject][ordered]@{
      relative_path = Canonical-Relative $root $file.FullName
      bytes = [long]$file.Length
      sha256 = Sha256 $file.FullName
      creation_time_utc_ticks = [long]$file.CreationTimeUtc.Ticks
      last_write_time_utc_ticks = [long]$file.LastWriteTimeUtc.Ticks
    }
  }
)
$payloadRows = @($payloadRows | Sort-Object -Property { [string]$_.relative_path } -CaseSensitive)
if (@($payloadRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'PAYLOAD_DUPLICATE' }

$csvText = ($payloadRows | ConvertTo-Csv -NoTypeInformation -UseQuotes AsNeeded) -join "`r`n"
Write-Utf8NoBom $manifestCsv ($csvText + "`r`n")
$manifestObject = [ordered]@{
  schema = 'P126_R14_PAYLOAD_MANIFEST_V1'
  handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R14-20260828'
  status = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
  payload_count = $payloadRows.Count
  rows = $payloadRows
}
Write-Utf8NoBom $manifestJson (($manifestObject | ConvertTo-Json -Depth 6) + "`n")
$manifestCsvHash = Sha256 $manifestCsv
$manifestJsonHash = Sha256 $manifestJson

$csvCheck = @(Import-Csv -LiteralPath $manifestCsv -ErrorAction Stop)
$jsonCheck = Get-Content -LiteralPath $manifestJson -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 10 -ErrorAction Stop
if ($csvCheck.Count -ne $payloadRows.Count -or $jsonCheck.rows.Count -ne $payloadRows.Count) { throw 'MANIFEST_PARSE_COUNT' }

$allCsv = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object Extension -eq '.csv')
$allJson = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop | Where-Object Extension -eq '.json')
$csvParseFailures = 0
foreach ($item in $allCsv) { try { $null = @(Import-Csv -LiteralPath $item.FullName -ErrorAction Stop) } catch { $csvParseFailures++ } }
$jsonParseFailures = 0
foreach ($item in $allJson) { try { $null = Get-Content -LiteralPath $item.FullName -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 30 -ErrorAction Stop } catch { $jsonParseFailures++ } }
if ($csvParseFailures -ne 0 -or $jsonParseFailures -ne 0) { throw 'DYNAMIC_PARSE_FAILURE' }

$allBeforeControlFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$allBeforeControlDirs = @((Get-Item -LiteralPath $root -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
$adsNondefault = 0
foreach ($item in @($allBeforeControlFiles + $allBeforeControlDirs)) { $adsNondefault += Get-AdsNondefaultCount $item.FullName }
if ($adsNondefault -ne 0) { throw 'ADS_NONDEFAULT' }
$forbiddenCache = @(Get-ChildItem -LiteralPath $root -Force -Recurse -ErrorAction Stop | Where-Object { $_.Name -eq '__pycache__' -or $_.Extension -in @('.pyc', '.pyo') }).Count
$reparseCount = @($allBeforeControlFiles + $allBeforeControlDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($forbiddenCache -ne 0 -or $reparseCount -ne 0) { throw 'HYGIENE_FAILURE' }

$sealObject = [ordered]@{
  schema = 'P126_R14_SEAL_AUDIT_V1'
  handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R14-20260828'
  status = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
  hard_defect_count = 1
  hard_defect_id = 'HARD-LEGEND-X2-CONTINUOUS'
  object_denominator = 60
  unordered_pairs = 1770
  payload_count = $payloadRows.Count
  control_count = 4
  expected_ordinary_count = $payloadRows.Count + 4
  manifest_csv_sha256 = $manifestCsvHash
  manifest_json_sha256 = $manifestJsonHash
  source_bytes = 4626
  source_sha256 = '6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502'
  pdf_bytes = 34054
  pdf_sha256 = '204CC34980BF059DFFA4016314C1FBFEFC94A0066C01FF7E77A4A26946B65F3D'
  x2_legend_occupied_runs = 1
  x2_legend_occupied_length_px = 73
  x2_legend_internal_blank_runs = 0
  csv_parse_failures = $csvParseFailures
  json_parse_failures = $jsonParseFailures
  ads_nondefault = $adsNondefault
  forbidden_cache_pyc = $forbiddenCache
  reparse_count = $reparseCount
  business_evidence_rerun = 0
}
Write-Utf8NoBom $sealAudit (($sealObject | ConvertTo-Json -Depth 5) + "`n")
$sealAuditHash = Sha256 $sealAudit
$null = Get-Content -LiteralPath $sealAudit -Raw -ErrorAction Stop | ConvertFrom-Json -Depth 10 -ErrorAction Stop

$premarkerFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$premarkerDirs = @((Get-Item -LiteralPath $root -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
foreach ($item in $premarkerFiles) {
  [IO.File]::SetAttributes($item.FullName, ([IO.File]::GetAttributes($item.FullName) -bor [IO.FileAttributes]::ReadOnly))
}
foreach ($item in @($premarkerDirs | Sort-Object { $_.FullName.Length } -Descending)) {
  [IO.File]::SetAttributes($item.FullName, ([IO.File]::GetAttributes($item.FullName) -bor [IO.FileAttributes]::ReadOnly))
}
$premarkerFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force -ErrorAction Stop)
$premarkerDirs = @((Get-Item -LiteralPath $root -Force -ErrorAction Stop)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force -ErrorAction Stop)
if (@($premarkerFiles | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'FILE_READONLY_GATE' }
if (@($premarkerDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count -ne 0) { throw 'DIR_READONLY_GATE' }

$maxTicks = [long]0
foreach ($item in @($premarkerFiles + $premarkerDirs)) { if ($item.LastWriteTimeUtc.Ticks -gt $maxTicks) { $maxTicks = $item.LastWriteTimeUtc.Ticks } }
$futureA = $maxTicks + 3000000000L
$futureB = [DateTime]::UtcNow.AddMinutes(5).Ticks
$markerTicks = [Math]::Max($futureA, $futureB)
$ordinaryCount = $payloadRows.Count + 4
$markerLines = @(
  'SCHEMA=P126_R14_WRITE_STOPPED_V1',
  'HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R14-20260828',
  'STATUS=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE',
  'HARD_DEFECT_COUNT=1',
  'HARD_DEFECT_ID=HARD-LEGEND-X2-CONTINUOUS',
  "ROOT=$root",
  "PAYLOAD_COUNT=$($payloadRows.Count)",
  'CONTROL_COUNT=4',
  "ORDINARY_COUNT=$ordinaryCount",
  "MANIFEST_CSV_SHA256=$manifestCsvHash",
  "MANIFEST_JSON_SHA256=$manifestJsonHash",
  "SEAL_AUDIT_SHA256=$sealAuditHash",
  'SOURCE_BYTES=4626',
  'SOURCE_SHA256=6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502',
  'PDF_BYTES=34054',
  'PDF_SHA256=204CC34980BF059DFFA4016314C1FBFEFC94A0066C01FF7E77A4A26946B65F3D',
  'OBJECT_DENOMINATOR=60',
  'UNORDERED_PAIRS=1770',
  'X2_LEGEND_OCCUPIED_RUNS=1',
  'X2_LEGEND_OCCUPIED_LENGTH_PX=73',
  'X2_LEGEND_INTERNAL_BLANK_RUNS=0',
  'CONTROLLER_INVOCATION=1',
  'RETRY_COUNT=0',
  'BUSINESS_EVIDENCE_RERUN=0',
  'PREMARKER_FILES_READONLY=TRUE',
  'PREMARKER_DIRS_READONLY=TRUE',
  "MARKER_LAST_WRITE_UTC_TICKS=$markerTicks"
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=].*$' }).Count -ne 0) { throw 'MARKER_SYNTAX_PREWRITE' }
if (@($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'MARKER_DUPLICATE_KEY_PREWRITE' }
Write-Utf8NoBom $stage (($markerLines -join "`n") + "`n")
[IO.File]::SetAttributes($stage, ([IO.File]::GetAttributes($stage) -bor [IO.FileAttributes]::ReadOnly))
[IO.File]::SetLastWriteTimeUtc($stage, [DateTime]::new($markerTicks, [DateTimeKind]::Utc))
$stageItem = Get-Item -LiteralPath $stage -Force -ErrorAction Stop
if (-not $stageItem.IsReadOnly -or $stageItem.LastWriteTimeUtc.Ticks -ne $markerTicks) { throw 'STAGE_GATE' }
$stageRead = @([IO.File]::ReadAllLines($stage, [Text.UTF8Encoding]::new($false)))
if ($stageRead.Count -ne $markerLines.Count) { throw 'STAGE_LINE_COUNT' }

Move-Item -LiteralPath $stage -Destination $marker -ErrorAction Stop

$snapshot1 = Get-TreeSnapshot $root
Start-Sleep -Milliseconds 300
$snapshot2 = Get-TreeSnapshot $root
if ($snapshot1.sha256 -ne $snapshot2.sha256 -or $snapshot1.entries -ne $snapshot2.entries) { throw 'POSTMARKER_SNAPSHOT_DRIFT' }
$sourceAfter = Get-Item -LiteralPath $source -Force -ErrorAction Stop
$pdfAfter = Get-Item -LiteralPath $pdf -Force -ErrorAction Stop
if ($sourceAfter.Length -ne 4626 -or (Sha256 $source) -ne '6CBAEBE50574E541A04B2FDCC74B432C49AF2590B579C6A85721EDF536912502') { throw 'SOURCE_AFTER_IDENTITY' }
if ($pdfAfter.Length -ne 34054 -or (Sha256 $pdf) -ne '204CC34980BF059DFFA4016314C1FBFEFC94A0066C01FF7E77A4A26946B65F3D') { throw 'PDF_AFTER_IDENTITY' }

$result = [ordered]@{
  schema = 'P126_R14_SEAL_CONTROLLER_RESULT_V1'
  success = $true
  handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R14-20260828'
  invocation_count = 1
  retry_count = 0
  payload_count = $payloadRows.Count
  control_count = 4
  ordinary_count = $ordinaryCount
  marker_lines = $markerLines.Count
  marker_sha256 = Sha256 $marker
  marker_ticks = $markerTicks
  snapshot1_entries = $snapshot1.entries
  snapshot1_sha256 = $snapshot1.sha256
  snapshot2_entries = $snapshot2.entries
  snapshot2_sha256 = $snapshot2.sha256
  source_before_after_same = $true
  pdf_before_after_same = $true
}
Write-Utf8NoBom $resultPath (($result | ConvertTo-Json -Depth 5) + "`n")
