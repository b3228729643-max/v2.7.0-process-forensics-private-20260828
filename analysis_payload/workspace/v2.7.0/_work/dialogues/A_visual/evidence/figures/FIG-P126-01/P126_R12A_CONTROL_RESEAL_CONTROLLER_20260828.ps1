Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R12-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R12_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12A_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$parent = [IO.Path]::GetDirectoryName($destinationRoot)
$stageMarker = Join-Path $parent 'P126_R12A_WRITE_STOPPED_STAGE_20260828.tmp'
$controllerResult = Join-Path $parent 'P126_R12A_CONTROL_RESEAL_CONTROLLER_RESULT_20260828.json'
$auditorResult = Join-Path $parent 'P126_R12A_CONTROL_RESEAL_AUDITOR_RESULT_20260828.json'
$report = Join-Path $parent 'P126_R12_LOCAL_SA2_REPORT_20260828.md'
$handoffFile = Join-Path $parent 'P126_R12_LOCAL_SA2_HANDOFF_20260828.md'
$controller = $MyInvocation.MyCommand.Path
$utf8 = [Text.UTF8Encoding]::new($false)
$oldControlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')
$newControlNames = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Get-CanonicalRelative([string]$Base, [string]$Path) {
  $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd('\')
  $pathFull = [IO.Path]::GetFullPath($Path)
  $relative = [IO.Path]::GetRelativePath($baseFull, $pathFull).Replace('\','/')
  $relative = [regex]::Replace($relative,'^(?:\./)+','')
  if ([string]::IsNullOrWhiteSpace($relative) -or $relative -eq '.' -or [IO.Path]::IsPathRooted($relative) -or $relative.StartsWith('/',[StringComparison]::Ordinal) -or $relative.StartsWith('../',[StringComparison]::Ordinal) -or $relative.Contains('/../',[StringComparison]::Ordinal)) { throw "unsafe relative path: $relative" }
  $segments = @($relative.Split('/'))
  if (@($segments | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw "unsafe relative path segment: $relative" }
  $resolved = [IO.Path]::GetFullPath((Join-Path $baseFull $relative.Replace('/','\')))
  if (-not ($resolved.Equals($baseFull,[StringComparison]::OrdinalIgnoreCase) -or $resolved.StartsWith($baseFull+'\',[StringComparison]::OrdinalIgnoreCase))) { throw "path escapes root: $relative" }
  $relative
}

function Get-FileIdentityRow([string]$Base, [string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force
  [ordered]@{
    relative_path = Get-CanonicalRelative $Base $Path
    resolved_path = [IO.Path]::GetFullPath($item.FullName)
    bytes = [long]$item.Length
    sha256 = Get-Sha256 $item.FullName
    creation_time_utc_ticks = [long]$item.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [long]$item.LastWriteTimeUtc.Ticks
  }
}

function Set-ReadonlyAttribute([string]$Path) {
  $item = Get-Item -LiteralPath $Path -Force
  [IO.File]::SetAttributes($item.FullName, ($item.Attributes -bor [IO.FileAttributes]::ReadOnly))
}

function Test-ReadonlyAttribute([string]$Path) {
  (((Get-Item -LiteralPath $Path -Force).Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
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
  [Array]::Sort($array,[StringComparer]::Ordinal)
  [ordered]@{entry_count=$array.Count;sha256=(Get-TextSha256 $array)}
}

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { throw 'source R12 root missing' }
if (Test-Path -LiteralPath $destinationRoot) { throw 'destination R12A preexists' }
foreach ($path in @($stageMarker,$controllerResult,$auditorResult)) { if (Test-Path -LiteralPath $path) { throw "external path preexists: $path" } }
foreach ($name in $oldControlNames) { if (Test-Path -LiteralPath (Join-Path $sourceRoot $name)) { throw "old control unexpectedly exists: $name" } }
if ((Get-Item -LiteralPath $report).Length -ne 2073 -or (Get-Sha256 $report) -cne '70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4' -or -not (Test-ReadonlyAttribute $report)) { throw 'report identity mismatch' }
if ((Get-Item -LiteralPath $handoffFile).Length -ne 1099 -or (Get-Sha256 $handoffFile) -cne '057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0' -or -not (Test-ReadonlyAttribute $handoffFile)) { throw 'handoff identity mismatch' }

$controllerIdentity = [ordered]@{path=$controller;bytes=(Get-Item -LiteralPath $controller).Length;sha256=(Get-Sha256 $controller)}
if (-not (Test-ReadonlyAttribute $controller)) { throw 'controller is not ReadOnly' }
$sourceSnapshotBefore = Get-TreeSnapshot $sourceRoot
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Force)
if ($sourceFiles.Count -ne 137) { throw "source material count mismatch: $($sourceFiles.Count)" }
$sourceRows = @($sourceFiles | ForEach-Object { Get-FileIdentityRow $sourceRoot $_.FullName } | Sort-Object -Property { [string]$_['relative_path'] })
$sourceDuplicateGroups = @($sourceRows | Group-Object -Property { [string]$_['relative_path'] } | Where-Object { $_.Count -ne 1 })
if ($sourceDuplicateGroups.Count -ne 0) { throw 'duplicate source relative path' }
$sourceBytes = [long](($sourceFiles | Measure-Object -Property Length -Sum).Sum)
if ($sourceBytes -ne 106101530) { throw "source material byte count mismatch: $sourceBytes" }

[void][IO.Directory]::CreateDirectory($destinationRoot)
$copyRows = [Collections.Generic.List[object]]::new()
foreach ($sourceRow in $sourceRows) {
  $relative = [string]$sourceRow['relative_path']
  $sourcePath = [string]$sourceRow['resolved_path']
  $destinationPath = [IO.Path]::GetFullPath((Join-Path $destinationRoot $relative.Replace('/','\')))
  $destinationDirectory = [IO.Path]::GetDirectoryName($destinationPath)
  [void][IO.Directory]::CreateDirectory($destinationDirectory)
  [IO.File]::Copy($sourcePath,$destinationPath,$false)
  [IO.File]::SetCreationTimeUtc($destinationPath,[DateTime]::new([long]$sourceRow['creation_time_utc_ticks'],[DateTimeKind]::Utc))
  [IO.File]::SetLastWriteTimeUtc($destinationPath,[DateTime]::new([long]$sourceRow['last_write_time_utc_ticks'],[DateTimeKind]::Utc))
  $destinationIdentity = Get-FileIdentityRow $destinationRoot $destinationPath
  foreach ($field in @('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')) {
    if ([string]$sourceRow[$field] -cne [string]$destinationIdentity[$field]) { throw "copy identity mismatch: $relative / $field" }
  }
  $copyRows.Add([ordered]@{
    relative_path=$relative;source_path=$sourcePath;destination_path=$destinationPath
    bytes=[long]$sourceRow['bytes'];sha256=[string]$sourceRow['sha256']
    creation_time_utc_ticks=[long]$sourceRow['creation_time_utc_ticks'];last_write_time_utc_ticks=[long]$sourceRow['last_write_time_utc_ticks']
  })
}
if ($copyRows.Count -ne 137 -or @($copyRows | Group-Object -Property { [string]$_['relative_path'] } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'COPY_IDENTITY row/set failure' }

$copyIdentityPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$copyObjects = @($copyRows | ForEach-Object { [pscustomobject]$_ })
[IO.File]::WriteAllLines($copyIdentityPath,@($copyObjects | ConvertTo-Csv -NoTypeInformation),$utf8)
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$provenance = [ordered]@{
  schema='P126_R12A_COPY_PROVENANCE_V1';handoff_id=$handoff;operation=$operation
  source_root=[IO.Path]::GetFullPath($sourceRoot);destination_root=[IO.Path]::GetFullPath($destinationRoot)
  source_snapshot_sha256=[string]$sourceSnapshotBefore['sha256'];source_snapshot_entry_count=[long]$sourceSnapshotBefore['entry_count']
  copied_material_count=137;copied_material_bytes=$sourceBytes;old_controls_copied=0;added_payload_count=2;payload_count=139
  preserved_fields=@('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
  preserved_verdict='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';hard_defect_id='HARD-LEGEND-X2-CONTINUOUS';business_evidence_rerun=0
  source_pdf_sha256='F8A9112C51511A96C64855CC8A0B1B69F15C1272804D96EFC7BF8C079E7DF0AA';source_code_sha256='81EFC188FA5E4827CAAB034C1EA3F7F4AFE25375DEE4046CD46F3FF49B0789BD'
  external_report_sha256='70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4';external_handoff_sha256='057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0'
}
[IO.File]::WriteAllText($provenancePath,($provenance | ConvertTo-Json -Depth 7)+"`n",$utf8)

$payloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force | Where-Object { $newControlNames -cnotcontains $_.Name })
if ($payloadFiles.Count -ne 139) { throw "destination payload count mismatch: $($payloadFiles.Count)" }
$payloadRows = @($payloadFiles | ForEach-Object { Get-FileIdentityRow $destinationRoot $_.FullName } | Sort-Object -Property { [string]$_['relative_path'] })
if (@($payloadRows | Group-Object -Property { [string]$_['relative_path'] } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'duplicate destination payload path' }
$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$manifestObjects = @($payloadRows | ForEach-Object { [pscustomobject]$_ })
[IO.File]::WriteAllLines($manifestPath,@($manifestObjects | Select-Object relative_path,bytes,sha256,creation_time_utc_ticks,last_write_time_utc_ticks | ConvertTo-Csv -NoTypeInformation),$utf8)
$manifestSha = Get-Sha256 $manifestPath
$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
$sealAudit = [ordered]@{
  schema='P126_R12A_SEAL_AUDIT_V1';handoff_id=$handoff;operation=$operation
  source_root=[IO.Path]::GetFullPath($sourceRoot);destination_root=[IO.Path]::GetFullPath($destinationRoot)
  source_snapshot_sha256=[string]$sourceSnapshotBefore['sha256'];copy_identity_sha256=(Get-Sha256 $copyIdentityPath);copy_provenance_sha256=(Get-Sha256 $provenancePath);payload_manifest_sha256=$manifestSha
  copied_material_count=137;old_controls_copied=0;payload_count=139;control_count=3;ordinary_count=142
  preserved_verdict='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';hard_defect_id='HARD-LEGEND-X2-CONTINUOUS';business_evidence_rerun=0
  copy_identity_mismatch=0;manifest_identity_mismatch=0;controller_invocation_count=1;retry_count=0;premarker_status='PASS'
}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit|ConvertTo-Json -Depth 7)+"`n",$utf8)
$sealAuditSha = Get-Sha256 $sealAuditPath

if (@(Import-Csv -LiteralPath $manifestPath).Count -ne 139 -or @(Import-Csv -LiteralPath $copyIdentityPath).Count -ne 137) { throw 'premarker CSV parse/count failure' }
$null = Get-Content -LiteralPath $provenancePath -Raw | ConvertFrom-Json
$null = Get-Content -LiteralPath $sealAuditPath -Raw | ConvertFrom-Json

$premarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
if ($premarkerFiles.Count -ne 141) { throw "premarker file count mismatch: $($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { Set-ReadonlyAttribute $file.FullName }
$destinationDirectories = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force | Sort-Object -Property FullName -Descending)
foreach ($directory in $destinationDirectories) { Set-ReadonlyAttribute $directory.FullName }
Set-ReadonlyAttribute $destinationRoot
$destinationDirectoryPaths = @($destinationDirectories.FullName) + @($destinationRoot)
if (@($premarkerFiles | Where-Object { -not (Test-ReadonlyAttribute $_.FullName) }).Count -ne 0 -or @($destinationDirectoryPaths | Where-Object { -not (Test-ReadonlyAttribute $_) }).Count -ne 0) { throw 'premarker ReadOnly gate failure' }

$markerLines = @(
  'SCHEMA=P126_R12A_WRITE_STOPPED_V1',
  "HANDOFF_ID=$handoff",
  "OPERATION=$operation",
  'VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE',
  'HARD_DEFECT_ID=HARD-LEGEND-X2-CONTINUOUS',
  "SOURCE_ROOT=$sourceRoot",
  "DESTINATION_ROOT=$destinationRoot",
  'SOURCE_MATERIAL_COUNT=137',
  'PAYLOAD_COUNT=139',
  'CONTROL_COUNT=3',
  'ORDINARY_COUNT=142',
  "PAYLOAD_MANIFEST_SHA256=$manifestSha",
  "COPY_IDENTITY_SHA256=$(Get-Sha256 $copyIdentityPath)",
  "COPY_PROVENANCE_SHA256=$(Get-Sha256 $provenancePath)",
  "SEAL_AUDIT_SHA256=$sealAuditSha",
  "SOURCE_SNAPSHOT_SHA256=$([string]$sourceSnapshotBefore['sha256'])",
  'CONTROLLER_INVOCATION_COUNT=1',
  'AUDITOR_INVOCATION_BUDGET=1',
  'RETRY_COUNT=0',
  'BUSINESS_EVIDENCE_RERUN=0',
  'OLD_CONTROLS_COPIED=0',
  'PREMARKER_FILES_READONLY=141',
  "PREMARKER_DIRS_READONLY=$($destinationDirectoryPaths.Count)",
  'REPORT_SHA256=70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4',
  'HANDOFF_SHA256=057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0',
  "PREPARED_UTC=$([DateTime]::UtcNow.ToString('O'))"
)
if ($markerLines.Count -ne 26 -or @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\r\n]+$' -or $_.Contains("`t") }).Count -ne 0) { throw 'marker syntax failure' }
$markerKeys = @($markerLines | ForEach-Object { $_.Split('=',2)[0] })
if (@($markerKeys | Group-Object -Property { [string]$_ } | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'marker duplicate key' }
[IO.File]::WriteAllLines($stageMarker,$markerLines,$utf8)
Set-ReadonlyAttribute $stageMarker
$allPremarkerItems = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force)
$maximumTicks = [long](($allPremarkerItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum)
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(10).Ticks,$maximumTicks+[TimeSpan]::FromMinutes(5).Ticks)
[IO.File]::SetLastWriteTimeUtc($stageMarker,[DateTime]::new($futureTicks,[DateTimeKind]::Utc))
if (-not (Test-ReadonlyAttribute $stageMarker)) { throw 'external marker ReadOnly gate failure' }
$markerPath = Join-Path $destinationRoot 'WRITE_STOPPED'
Move-Item -LiteralPath $stageMarker -Destination $markerPath

$destinationSnapshot1 = Get-TreeSnapshot $destinationRoot
Start-Sleep -Milliseconds 250
$destinationSnapshot2 = Get-TreeSnapshot $destinationRoot
$sourceSnapshotAfter = Get-TreeSnapshot $sourceRoot
if ([string]$destinationSnapshot1['sha256'] -cne [string]$destinationSnapshot2['sha256'] -or [long]$destinationSnapshot1['entry_count'] -ne [long]$destinationSnapshot2['entry_count']) { throw 'postmarker destination snapshot changed' }
if ([string]$sourceSnapshotBefore['sha256'] -cne [string]$sourceSnapshotAfter['sha256'] -or [long]$sourceSnapshotBefore['entry_count'] -ne [long]$sourceSnapshotAfter['entry_count']) { throw 'source root changed' }
$ordinaryFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
$allDestinationDirectoryPaths = @((Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force).FullName)+@($destinationRoot)
if ($ordinaryFiles.Count -ne 142 -or @($ordinaryFiles | Where-Object { -not (Test-ReadonlyAttribute $_.FullName) }).Count -ne 0 -or @($allDestinationDirectoryPaths | Where-Object { -not (Test-ReadonlyAttribute $_) }).Count -ne 0) { throw 'postmarker count or ReadOnly failure' }
$markerItem = Get-Item -LiteralPath $markerPath -Force
$otherItems = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force | Where-Object { $_.FullName -cne $markerPath })
$maximumOther = [long](($otherItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum)
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count
if ($markerItem.LastWriteTimeUtc.Ticks -le $maximumOther -or $atOrAfter -ne 0) { throw 'marker strict-latest failure' }

$resultObject = [ordered]@{
  schema='P126_R12A_CONTROL_RESEAL_CONTROLLER_RESULT_V1';handoff_id=$handoff;operation=$operation
  controller=$controllerIdentity;controller_invocation_count=1;retry_count=0;exit_code=0;natural_exit=$true;success=$true
  source_snapshot_before=$sourceSnapshotBefore;source_snapshot_after=$sourceSnapshotAfter;destination_snapshot_s1=$destinationSnapshot1;destination_snapshot_s2=$destinationSnapshot2
  copied_material_count=137;copied_material_bytes=$sourceBytes;old_controls_copied=0;payload_count=139;control_count=3;ordinary_count=142;directory_count_including_root=$allDestinationDirectoryPaths.Count
  copy_identity_sha256=(Get-Sha256 $copyIdentityPath);copy_provenance_sha256=(Get-Sha256 $provenancePath);payload_manifest_sha256=$manifestSha;seal_audit_sha256=$sealAuditSha
  marker_path=$markerPath;marker_bytes=$markerItem.Length;marker_sha256=(Get-Sha256 $markerPath);marker_lines=26;marker_keys=26;marker_ticks=$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]($markerItem.LastWriteTimeUtc.Ticks-$maximumOther);at_or_after_excluding_marker=$atOrAfter
  report_sha256='70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4';handoff_sha256='057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0'
}
[IO.File]::WriteAllText($controllerResult,($resultObject|ConvertTo-Json -Depth 9)+"`n",$utf8)
$resultObject | ConvertTo-Json -Depth 9
