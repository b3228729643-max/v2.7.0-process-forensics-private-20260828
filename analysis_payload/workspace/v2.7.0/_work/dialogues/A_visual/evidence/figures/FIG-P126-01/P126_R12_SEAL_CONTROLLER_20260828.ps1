Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R12-20260828'
$operation = 'P126_R115_R12_SA2_SINGLE_LEGAL_SEAL_V1'
$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828'
$parent = [IO.Path]::GetDirectoryName($root)
$report = Join-Path $parent 'P126_R12_LOCAL_SA2_REPORT_20260828.md'
$handoffFile = Join-Path $parent 'P126_R12_LOCAL_SA2_HANDOFF_20260828.md'
$stageMarker = Join-Path $parent 'P126_R12_WRITE_STOPPED_STAGE_20260828.tmp'
$controllerResult = Join-Path $parent 'P126_R12_SEAL_CONTROLLER_RESULT_20260828.json'
$controller = $MyInvocation.MyCommand.Path
$utf8 = [Text.UTF8Encoding]::new($false)
$controlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')

function Get-Sha256([string]$Path) {
  (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}

function Get-CanonicalRelative([string]$Base, [string]$Path) {
  $relative = [IO.Path]::GetRelativePath([IO.Path]::GetFullPath($Base), [IO.Path]::GetFullPath($Path)).Replace('\','/')
  if ([string]::IsNullOrWhiteSpace($relative) -or $relative -eq '.' -or $relative.StartsWith('../') -or $relative.Contains('/../') -or [IO.Path]::IsPathRooted($relative)) { throw "unsafe relative path: $relative" }
  $segments = @($relative.Split('/'))
  if (@($segments | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw "unsafe path segment: $relative" }
  $relative
}

function Get-FileRow([string]$Base, [string]$Path) {
  $item = Get-Item -LiteralPath $Path
  [ordered]@{
    relative_path = Get-CanonicalRelative $Base $Path
    bytes = [long]$item.Length
    sha256 = Get-Sha256 $Path
    creation_time_utc_ticks = [long]$item.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [long]$item.LastWriteTimeUtc.Ticks
  }
}

function Set-ReadonlyAttribute([string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force
  [IO.File]::SetAttributes($item.FullName, ($item.Attributes -bor [IO.FileAttributes]::ReadOnly))
}

function Test-ReadonlyAttribute([string]$Path) {
  $attributes = (Get-Item -LiteralPath $Path -Force).Attributes
  (($attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
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

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'R12 root missing' }
foreach ($name in $controlNames) { if (Test-Path -LiteralPath (Join-Path $root $name)) { throw "control preexists: $name" } }
foreach ($path in @($stageMarker,$controllerResult)) { if (Test-Path -LiteralPath $path) { throw "external path preexists: $path" } }

$controllerIdentity = [ordered]@{path=$controller;bytes=(Get-Item -LiteralPath $controller).Length;sha256=Get-Sha256 $controller}
if (-not (Test-ReadonlyAttribute $controller)) { throw 'controller is not ReadOnly' }
if ((Get-Item -LiteralPath $report).Length -ne 2073 -or (Get-Sha256 $report) -cne '70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4' -or -not (Test-ReadonlyAttribute $report)) { throw 'report identity mismatch' }
if ((Get-Item -LiteralPath $handoffFile).Length -ne 1099 -or (Get-Sha256 $handoffFile) -cne '057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0' -or -not (Test-ReadonlyAttribute $handoffFile)) { throw 'handoff identity mismatch' }

$result = Get-Content -LiteralPath (Join-Path $root 'RESULT.json') -Raw | ConvertFrom-Json
if ($result.verdict -cne 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE' -or $result.hard_defect_id -cne 'HARD-LEGEND-X2-CONTINUOUS') { throw 'business result binding mismatch' }
$preseal = Get-Content -LiteralPath (Join-Path $root 'PRESEAL_VALIDATION.json') -Raw | ConvertFrom-Json
if (-not $preseal.ready_for_single_seal -or $preseal.manual_pairs -ne 1770 -or $preseal.object_manual_fail -ne 1) { throw 'preseal validation mismatch' }

$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { $controlNames -cnotcontains $_.Name })
if ($payloadFiles.Count -ne 137) { throw "payload count mismatch before controls: $($payloadFiles.Count)" }
$payloadRows = @($payloadFiles | ForEach-Object { Get-FileRow $root $_.FullName } | Sort-Object -Property relative_path)
if (@($payloadRows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'duplicate payload relative path' }

$manifestCsv = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $root 'PAYLOAD_MANIFEST.json'
$sealAudit = Join-Path $root 'SEAL_AUDIT.json'
$csvLines = @($payloadRows | Select-Object relative_path,bytes,sha256,creation_time_utc_ticks,last_write_time_utc_ticks | ConvertTo-Csv -NoTypeInformation)
[IO.File]::WriteAllLines($manifestCsv, $csvLines, $utf8)
$manifestObject = [ordered]@{schema='P126_R12_PAYLOAD_MANIFEST_V1';handoff_id=$handoff;payload_count=$payloadRows.Count;rows=$payloadRows}
[IO.File]::WriteAllText($manifestJson, ($manifestObject | ConvertTo-Json -Depth 8) + "`n", $utf8)
$manifestCsvSha = Get-Sha256 $manifestCsv
$manifestJsonSha = Get-Sha256 $manifestJson
$auditObject = [ordered]@{
  schema='P126_R12_SEAL_AUDIT_V1';handoff_id=$handoff;operation=$operation
  verdict='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';hard_defect_id='HARD-LEGEND-X2-CONTINUOUS'
  payload_count=137;control_count=4;ordinary_count=141;directory_count_including_root=10
  manifest_csv_sha256=$manifestCsvSha;manifest_json_sha256=$manifestJsonSha
  report_sha256='70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4'
  handoff_sha256='057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0'
  controller_invocation_count=1;retry_count=0;business_evidence_rerun=0
  premarker_validation='PASS'
}
[IO.File]::WriteAllText($sealAudit, ($auditObject | ConvertTo-Json -Depth 6) + "`n", $utf8)
$sealAuditSha = Get-Sha256 $sealAudit

$parsedCsv = @(Import-Csv -LiteralPath $manifestCsv)
$parsedJson = Get-Content -LiteralPath $manifestJson -Raw | ConvertFrom-Json
$parsedAudit = Get-Content -LiteralPath $sealAudit -Raw | ConvertFrom-Json
if ($parsedCsv.Count -ne 137 -or $parsedJson.payload_count -ne 137 -or $parsedAudit.ordinary_count -ne 141) { throw 'premarker control parse/count failure' }

$premarkerFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
if ($premarkerFiles.Count -ne 140) { throw "premarker file count mismatch: $($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { Set-ReadonlyAttribute $file.FullName }
$directories = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Sort-Object -Property FullName -Descending)
foreach ($directory in $directories) { Set-ReadonlyAttribute $directory.FullName }
Set-ReadonlyAttribute $root
$premarkerFileReadonly = @($premarkerFiles | Where-Object { -not (Test-ReadonlyAttribute $_.FullName) }).Count
$premarkerDirectoryPaths = @($directories.FullName) + @($root)
$premarkerDirectoryReadonly = @($premarkerDirectoryPaths | Where-Object { -not (Test-ReadonlyAttribute $_) }).Count
if ($premarkerFileReadonly -ne 0 -or $premarkerDirectoryReadonly -ne 0) { throw 'premarker ReadOnly gate failed' }

$markerLines = @(
  'SCHEMA=P126_R12_WRITE_STOPPED_V1',
  "HANDOFF_ID=$handoff",
  "OPERATION=$operation",
  'VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE',
  'HARD_DEFECT_ID=HARD-LEGEND-X2-CONTINUOUS',
  "ROOT=$root",
  'PDF_SHA256=F8A9112C51511A96C64855CC8A0B1B69F15C1272804D96EFC7BF8C079E7DF0AA',
  'SOURCE_SHA256=81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD',
  'PAYLOAD_COUNT=137',
  'CONTROL_COUNT=4',
  'ORDINARY_COUNT=141',
  "MANIFEST_CSV_SHA256=$manifestCsvSha",
  "MANIFEST_JSON_SHA256=$manifestJsonSha",
  "SEAL_AUDIT_SHA256=$sealAuditSha",
  "REPORT_PATH=$report",
  'REPORT_SHA256=70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4',
  "HANDOFF_PATH=$handoffFile",
  'HANDOFF_SHA256=057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0',
  'CONTROLLER_INVOCATION_COUNT=1',
  'AUDITOR_INVOCATION_BUDGET=1',
  'RETRY_COUNT=0',
  'BUSINESS_EVIDENCE_RERUN=0',
  'PREMARKER_FILES_READONLY=140',
  'PREMARKER_DIRS_READONLY=10',
  "PREPARED_UTC=$([DateTime]::UtcNow.ToString('O'))"
)
if ($markerLines.Count -ne 25 -or @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\r\n]+$' -or $_.Contains("`t") }).Count -ne 0) { throw 'marker syntax failure' }
$markerKeys = @($markerLines | ForEach-Object { $_.Split('=',2)[0] })
if (@($markerKeys | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'marker duplicate key' }
[IO.File]::WriteAllLines($stageMarker, $markerLines, $utf8)
Set-ReadonlyAttribute $stageMarker
$allPremarkerItems = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Force)
$maximumTicks = ($allPremarkerItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(10).Ticks, [long]$maximumTicks + [TimeSpan]::FromMinutes(5).Ticks)
[IO.File]::SetLastWriteTimeUtc($stageMarker, [DateTime]::new($futureTicks, [DateTimeKind]::Utc))
if (-not (Test-ReadonlyAttribute $stageMarker)) { throw 'external marker ReadOnly gate failed' }

$markerDestination = Join-Path $root 'WRITE_STOPPED'
Move-Item -LiteralPath $stageMarker -Destination $markerDestination

$snapshot1 = Get-TreeSnapshot $root
Start-Sleep -Milliseconds 250
$snapshot2 = Get-TreeSnapshot $root
if ($snapshot1.sha256 -cne $snapshot2.sha256 -or $snapshot1.count -ne $snapshot2.count) { throw 'postmarker snapshot changed' }
$ordinaryFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$allDirectoryPaths = @((Get-ChildItem -LiteralPath $root -Recurse -Directory -Force).FullName) + @($root)
if ($ordinaryFiles.Count -ne 141 -or $allDirectoryPaths.Count -ne 10) { throw 'postmarker count mismatch' }
if (@($ordinaryFiles | Where-Object { -not (Test-ReadonlyAttribute $_.FullName) }).Count -ne 0 -or @($allDirectoryPaths | Where-Object { -not (Test-ReadonlyAttribute $_) }).Count -ne 0) { throw 'postmarker ReadOnly failure' }
$markerItem = Get-Item -LiteralPath $markerDestination -Force
$otherItems = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.FullName -cne $markerDestination })
$otherMaximum = ($otherItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count
if ($markerItem.LastWriteTimeUtc.Ticks -le $otherMaximum -or $atOrAfter -ne 0) { throw 'marker strict-latest failure' }

$controllerResultObject = [ordered]@{
  schema='P126_R12_SEAL_CONTROLLER_RESULT_V1';handoff_id=$handoff;operation=$operation
  controller=$controllerIdentity;controller_invocation_count=1;retry_count=0;exit_code=0;natural_exit=$true
  payload_count=137;control_count=4;ordinary_count=141;directory_count_including_root=10
  manifest_csv_sha256=$manifestCsvSha;manifest_json_sha256=$manifestJsonSha;seal_audit_sha256=$sealAuditSha
  marker_path=$markerDestination;marker_bytes=$markerItem.Length;marker_sha256=(Get-Sha256 $markerDestination);marker_lines=25;marker_ticks=$markerItem.LastWriteTimeUtc.Ticks
  strict_latest_margin_ticks=[long]($markerItem.LastWriteTimeUtc.Ticks-$otherMaximum);at_or_after_excluding_marker=$atOrAfter
  postmarker_snapshot_s1=$snapshot1;postmarker_snapshot_s2=$snapshot2
  report_sha256='70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4';handoff_sha256='057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0'
  success=$true
}
[IO.File]::WriteAllText($controllerResult, ($controllerResultObject | ConvertTo-Json -Depth 8) + "`n", $utf8)
$controllerResultObject | ConvertTo-Json -Depth 8
