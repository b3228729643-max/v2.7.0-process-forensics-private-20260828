Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R12-20260828'
$operation = 'P126_R115_R12_SA2_SINGLE_LEGAL_SEAL_V1'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828'
$parent = [IO.Path]::GetDirectoryName($root)
$controller = Join-Path $parent 'P126_R12_SEAL_CONTROLLER_20260828.ps1'
$controllerResult = Join-Path $parent 'P126_R12_SEAL_CONTROLLER_RESULT_20260828.json'
$report = Join-Path $parent 'P126_R12_LOCAL_SA2_REPORT_20260828.md'
$handoffFile = Join-Path $parent 'P126_R12_LOCAL_SA2_HANDOFF_20260828.md'
$stageMarker = Join-Path $parent 'P126_R12_WRITE_STOPPED_STAGE_20260828.tmp'
$auditorResult = Join-Path $parent 'P126_R12_ROOT_EXTERNAL_AUDIT_20260828.json'
$auditor = $MyInvocation.MyCommand.Path
$utf8 = [Text.UTF8Encoding]::new($false)
$controlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Get-CanonicalRelative([string]$Base, [string]$Path) {
  $relative = [IO.Path]::GetRelativePath([IO.Path]::GetFullPath($Base), [IO.Path]::GetFullPath($Path)).Replace('\','/')
  if ([string]::IsNullOrWhiteSpace($relative) -or $relative -eq '.' -or $relative.StartsWith('../') -or $relative.Contains('/../') -or [IO.Path]::IsPathRooted($relative)) { throw "unsafe relative path: $relative" }
  $segments = @($relative.Split('/'))
  if (@($segments | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw "unsafe path segment: $relative" }
  $relative
}

function Test-ReadonlyAttribute([string]$Path) {
  $attributes = (Get-Item -LiteralPath $Path -Force).Attributes
  (($attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

function Get-FileRow([string]$Base, [string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force
  [ordered]@{
    relative_path = Get-CanonicalRelative $Base $Path
    bytes = [long]$item.Length
    sha256 = Get-Sha256 $Path
    creation_time_utc_ticks = [long]$item.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [long]$item.LastWriteTimeUtc.Ticks
  }
}

function Get-TextSha256([string[]]$Lines) {
  $bytes = $utf8.GetBytes(($Lines -join "`n") + "`n")
  $hasher = [Security.Cryptography.SHA256]::Create()
  try { ([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','') } finally { $hasher.Dispose() }
}

function Get-TreeSnapshot([string]$Base) {
  $lines = [Collections.Generic.List[string]]::new()
  $rootItem = Get-Item -LiteralPath $Base -Force
  $lines.Add(".|D|0|-|$($rootItem.CreationTimeUtc.Ticks)|$($rootItem.LastWriteTimeUtc.Ticks)|$([int]$rootItem.Attributes)")
  foreach ($directory in @(Get-ChildItem -LiteralPath $Base -Recurse -Directory -Force)) {
    $relative = Get-CanonicalRelative $Base $directory.FullName
    $lines.Add("$relative|D|0|-|$($directory.CreationTimeUtc.Ticks)|$($directory.LastWriteTimeUtc.Ticks)|$([int]$directory.Attributes)")
  }
  foreach ($file in @(Get-ChildItem -LiteralPath $Base -Recurse -File -Force)) {
    $relative = Get-CanonicalRelative $Base $file.FullName
    $lines.Add("$relative|F|$($file.Length)|$(Get-Sha256 $file.FullName)|$($file.CreationTimeUtc.Ticks)|$($file.LastWriteTimeUtc.Ticks)|$([int]$file.Attributes)")
  }
  $array = $lines.ToArray()
  [Array]::Sort($array, [StringComparer]::Ordinal)
  [ordered]@{count=$array.Count;sha256=(Get-TextSha256 $array)}
}

foreach ($required in @($root,$controller,$controllerResult,$report,$handoffFile)) { if (-not (Test-Path -LiteralPath $required)) { throw "required path missing: $required" } }
if (Test-Path -LiteralPath $stageMarker) { throw 'external stage marker still exists' }
if (Test-Path -LiteralPath $auditorResult) { throw 'auditor result preexists' }
if (-not (Test-ReadonlyAttribute $auditor)) { throw 'auditor is not ReadOnly' }

$controllerData = Get-Content -LiteralPath $controllerResult -Raw | ConvertFrom-Json
if (-not $controllerData.success -or $controllerData.exit_code -ne 0 -or $controllerData.controller_invocation_count -ne 1 -or $controllerData.retry_count -ne 0 -or $controllerData.handoff_id -cne $handoff -or $controllerData.operation -cne $operation) { throw 'controller result contract failure' }
if ([long]$controllerData.controller.bytes -ne (Get-Item -LiteralPath $controller).Length -or [string]$controllerData.controller.sha256 -cne (Get-Sha256 $controller)) { throw 'controller identity changed' }

$manifestCsvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$sealAuditPath = Join-Path $root 'SEAL_AUDIT.json'
$markerPath = Join-Path $root 'WRITE_STOPPED'
$csvRows = @(Import-Csv -LiteralPath $manifestCsvPath)
$jsonManifest = Get-Content -LiteralPath $manifestJsonPath -Raw | ConvertFrom-Json
$jsonRows = @($jsonManifest.rows)
$sealData = Get-Content -LiteralPath $sealAuditPath -Raw | ConvertFrom-Json
if ($csvRows.Count -ne 137 -or $jsonRows.Count -ne 137 -or $jsonManifest.payload_count -ne 137 -or $sealData.payload_count -ne 137 -or $sealData.control_count -ne 4 -or $sealData.ordinary_count -ne 141) { throw 'manifest/control declared count failure' }
if ((Get-Sha256 $manifestCsvPath) -cne [string]$controllerData.manifest_csv_sha256 -or (Get-Sha256 $manifestJsonPath) -cne [string]$controllerData.manifest_json_sha256 -or (Get-Sha256 $sealAuditPath) -cne [string]$controllerData.seal_audit_sha256) { throw 'control hash binding failure' }

$csvMap = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($row in $csvRows) { if (-not $csvMap.TryAdd([string]$row.relative_path,$row)) { throw 'duplicate CSV manifest path' } }
$jsonMap = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($row in $jsonRows) { if (-not $jsonMap.TryAdd([string]$row.relative_path,$row)) { throw 'duplicate JSON manifest path' } }
$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { $controlNames -cnotcontains $_.Name })
if ($payloadFiles.Count -ne 137) { throw 'actual payload count failure' }
$actualMap = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($file in $payloadFiles) {
  $actual = Get-FileRow $root $file.FullName
  if (-not $actualMap.TryAdd([string]$actual.relative_path,$actual)) { throw 'duplicate actual payload path' }
}
$allKeys = @($csvMap.Keys)
[Array]::Sort($allKeys,[StringComparer]::Ordinal)
foreach ($key in $allKeys) {
  if (-not $jsonMap.ContainsKey($key) -or -not $actualMap.ContainsKey($key)) { throw "manifest set missing: $key" }
  $csv = $csvMap[$key]; $json = $jsonMap[$key]; $actual = $actualMap[$key]
  foreach ($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')) {
    if ([string]$csv.$field -cne [string]$json.$field -or [string]$csv.$field -cne [string]$actual.$field) { throw "manifest identity mismatch: $key / $field" }
  }
}
if ($jsonMap.Count -ne $csvMap.Count -or $actualMap.Count -ne $csvMap.Count) { throw 'manifest set count mismatch' }

$ordinaryFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$directoryPaths = @((Get-ChildItem -LiteralPath $root -Recurse -Directory -Force).FullName) + @($root)
if ($ordinaryFiles.Count -ne 141 -or $directoryPaths.Count -ne 10) { throw 'ordinary/tree count failure' }
$fileReadonlyFail = @($ordinaryFiles | Where-Object { -not (Test-ReadonlyAttribute $_.FullName) }).Count
$directoryReadonlyFail = @($directoryPaths | Where-Object { -not (Test-ReadonlyAttribute $_) }).Count
if ($fileReadonlyFail -ne 0 -or $directoryReadonlyFail -ne 0) { throw 'tree ReadOnly failure' }

$markerBytes = [IO.File]::ReadAllBytes($markerPath)
$hasBom = ($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF)
$markerLines = @([IO.File]::ReadAllLines($markerPath,$utf8))
$expectedKeys = @('SCHEMA','HANDOFF_ID','OPERATION','VERDICT','HARD_DEFECT_ID','ROOT','PDF_SHA256','SOURCE_SHA256','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','MANIFEST_CSV_SHA256','MANIFEST_JSON_SHA256','SEAL_AUDIT_SHA256','REPORT_PATH','REPORT_SHA256','HANDOFF_PATH','HANDOFF_SHA256','CONTROLLER_INVOCATION_COUNT','AUDITOR_INVOCATION_BUDGET','RETRY_COUNT','BUSINESS_EVIDENCE_RERUN','PREMARKER_FILES_READONLY','PREMARKER_DIRS_READONLY','PREPARED_UTC')
if ($hasBom -or $markerLines.Count -ne 25 -or @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\r\n]+$' -or $_.Contains("`t") }).Count -ne 0) { throw 'marker syntax failure' }
$markerMap = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
foreach ($line in $markerLines) { $parts=$line.Split('=',2); if (-not $markerMap.TryAdd($parts[0],$parts[1])) { throw 'marker duplicate key' } }
$actualMarkerKeys = @($markerMap.Keys); [Array]::Sort($actualMarkerKeys,[StringComparer]::Ordinal)
$sortedExpected = @($expectedKeys); [Array]::Sort($sortedExpected,[StringComparer]::Ordinal)
if (@(Compare-Object -CaseSensitive -ReferenceObject $sortedExpected -DifferenceObject $actualMarkerKeys).Count -ne 0) { throw 'marker exact key set failure' }
$expectedBindings = [ordered]@{
  SCHEMA='P126_R12_WRITE_STOPPED_V1';HANDOFF_ID=$handoff;OPERATION=$operation;VERDICT='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';HARD_DEFECT_ID='HARD-LEGEND-X2-CONTINUOUS';ROOT=$root
  PDF_SHA256='F8A9112C51511A96C64855CC8A0B1B69F15C1272804D96EFC7BF8C079E7DF0AA';SOURCE_SHA256='81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD'
  PAYLOAD_COUNT='137';CONTROL_COUNT='4';ORDINARY_COUNT='141';MANIFEST_CSV_SHA256=(Get-Sha256 $manifestCsvPath);MANIFEST_JSON_SHA256=(Get-Sha256 $manifestJsonPath);SEAL_AUDIT_SHA256=(Get-Sha256 $sealAuditPath)
  REPORT_PATH=$report;REPORT_SHA256='70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4';HANDOFF_PATH=$handoffFile;HANDOFF_SHA256='057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0'
  CONTROLLER_INVOCATION_COUNT='1';AUDITOR_INVOCATION_BUDGET='1';RETRY_COUNT='0';BUSINESS_EVIDENCE_RERUN='0';PREMARKER_FILES_READONLY='140';PREMARKER_DIRS_READONLY='10'
}
foreach ($binding in $expectedBindings.GetEnumerator()) { if ($markerMap[$binding.Key] -cne [string]$binding.Value) { throw "marker binding failure: $($binding.Key)" } }
[void][DateTime]::Parse($markerMap['PREPARED_UTC'],[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind)

$markerItem = Get-Item -LiteralPath $markerPath -Force
$otherItems = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.FullName -cne $markerPath })
$maximumOther = ($otherItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count
if ($markerItem.LastWriteTimeUtc.Ticks -le $maximumOther -or $atOrAfter -ne 0) { throw 'marker strict latest failure' }

$currentSnapshot = Get-TreeSnapshot $root
if ([string]$controllerData.postmarker_snapshot_s1.sha256 -cne [string]$controllerData.postmarker_snapshot_s2.sha256 -or [string]$controllerData.postmarker_snapshot_s1.sha256 -cne [string]$currentSnapshot.sha256 -or [long]$controllerData.postmarker_snapshot_s1.count -ne [long]$currentSnapshot.count) { throw 'postmarker snapshot mismatch' }

$jsonFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.json' -Force)
$csvFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.csv' -Force)
$jsonParseFail = 0
foreach ($file in $jsonFiles) { try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { $jsonParseFail++ } }
$csvParseFail = 0
foreach ($file in $csvFiles) { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvParseFail++ } }
$adsCount = 0
foreach ($file in $ordinaryFiles) { $adsCount += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -ne ':$DATA' }).Count }
$pycCount = @(Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.pyc' -Force).Count
$pythonCacheCount = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Where-Object { $_.Name -in @('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache') }).Count
$reparseCount = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Force)
$reparseCount = @($reparseCount | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($jsonParseFail -ne 0 -or $csvParseFail -ne 0 -or $adsCount -ne 0 -or $pycCount -ne 0 -or $pythonCacheCount -ne 0 -or $reparseCount -ne 0) { throw 'parse or hygiene failure' }

if ((Get-Item -LiteralPath $report).Length -ne 2073 -or (Get-Sha256 $report) -cne '70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4' -or -not (Test-ReadonlyAttribute $report)) { throw 'external report identity failure' }
if ((Get-Item -LiteralPath $handoffFile).Length -ne 1099 -or (Get-Sha256 $handoffFile) -cne '057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0' -or -not (Test-ReadonlyAttribute $handoffFile)) { throw 'external handoff identity failure' }

$audit = [ordered]@{
  schema='P126_R12_ROOT_EXTERNAL_AUDIT_V1';handoff_id=$handoff;operation=$operation
  auditor=[ordered]@{path=$auditor;bytes=(Get-Item -LiteralPath $auditor).Length;sha256=(Get-Sha256 $auditor)};auditor_invocation_count=1;retry_count=0;exit_code=0
  payload_count=137;control_count=4;ordinary_count=141;directory_count_including_root=10
  manifest_set_identity_mismatch=0;file_readonly_fail=$fileReadonlyFail;directory_readonly_fail=$directoryReadonlyFail
  marker_path=$markerPath;marker_bytes=$markerItem.Length;marker_sha256=(Get-Sha256 $markerPath);marker_lines=25;marker_keys=25;marker_bad=0;marker_duplicate=0;marker_has_bom=$hasBom
  marker_ticks=$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]($markerItem.LastWriteTimeUtc.Ticks-$maximumOther);at_or_after_excluding_marker=$atOrAfter
  postmarker_snapshot=$currentSnapshot;postmarker_content_attribute_writes=0
  json_files=$jsonFiles.Count;json_parse_fail=$jsonParseFail;csv_files=$csvFiles.Count;csv_parse_fail=$csvParseFail;ads_count=$adsCount;pyc_count=$pycCount;python_cache_count=$pythonCacheCount;reparse_count=$reparseCount
  report_sha256=(Get-Sha256 $report);handoff_sha256=(Get-Sha256 $handoffFile);verdict='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';hard_defect_id='HARD-LEGEND-X2-CONTINUOUS';success=$true
}
[IO.File]::WriteAllText($auditorResult, ($audit | ConvertTo-Json -Depth 8) + "`n", $utf8)
$resultItem = Get-Item -LiteralPath $auditorResult
[IO.File]::SetAttributes($resultItem.FullName, ($resultItem.Attributes -bor [IO.FileAttributes]::ReadOnly))
$audit | ConvertTo-Json -Depth 8
