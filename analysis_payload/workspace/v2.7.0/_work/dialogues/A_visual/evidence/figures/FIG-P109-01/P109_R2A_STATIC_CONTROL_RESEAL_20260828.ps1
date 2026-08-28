$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R2_SA2_STATIC_DOMAIN_LABEL_OPAQUE_PATCH_R114_20260828'
$targetRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R2A_SA2_STATIC_DOMAIN_LABEL_OPAQUE_PATCH_CONTROL_RESEAL_R114_20260828'
$externalAuditPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R2A_SA2_STATIC_DOMAIN_LABEL_OPAQUE_PATCH_CONTROL_RESEAL_R114_20260828_EXTERNAL_AUDIT.json'
$externalReportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R2A_SA2_STATIC_DOMAIN_LABEL_OPAQUE_PATCH_CONTROL_RESEAL_R114_20260828_REPORT.md'
$externalHandoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R2A_SA2_STATIC_DOMAIN_LABEL_OPAQUE_PATCH_CONTROL_RESEAL_R114_20260828_HANDOFF.md'
$sourcePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C07\fig_v1_c07_convex_set.tex'
$handoffId = 'A-R114-P109-SA2-STATIC-DOMAIN-LABEL-PATCH-CONTROL-RESEAL-V1-20260828'
$operation = 'P109_R2_STATIC_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$payloadNames = @(
  'PRESEAL_CHECKS.json',
  'SOURCE_IDENTITY.json',
  'SOURCE_PATCH.diff',
  'STATIC_PROJECTION.md',
  'STATIC_SCOPE.md'
)
$controlNames = @('PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-IdentityRow([string]$Path) {
  $item = Get-Item -LiteralPath $Path
  [ordered]@{
    relative_path = $item.Name
    bytes = [int64]$item.Length
    sha256 = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
    creation_time_utc_ticks = $item.CreationTimeUtc.Ticks.ToString()
    last_write_time_utc_ticks = $item.LastWriteTimeUtc.Ticks.ToString()
  }
}

function Get-RootSnapshot([string]$RootPath) {
  $rows = [Collections.Generic.List[object]]::new()
  $rootItem = Get-Item -LiteralPath $RootPath
  $rows.Add([ordered]@{
    kind='directory'; relative_path='.'; bytes=$null; sha256=$null
    creation_ticks=$rootItem.CreationTimeUtc.Ticks.ToString()
    last_write_ticks=$rootItem.LastWriteTimeUtc.Ticks.ToString()
    attributes=[int]$rootItem.Attributes
  })
  foreach($item in @(Get-ChildItem -LiteralPath $RootPath -Force | Sort-Object Name)) {
    $isDirectory = $item.PSIsContainer
    $rows.Add([ordered]@{
      kind=if($isDirectory){'directory'}else{'file'}
      relative_path=$item.Name
      bytes=if($isDirectory){$null}else{[int64]$item.Length}
      sha256=if($isDirectory){$null}else{(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash}
      creation_ticks=$item.CreationTimeUtc.Ticks.ToString()
      last_write_ticks=$item.LastWriteTimeUtc.Ticks.ToString()
      attributes=[int]$item.Attributes
    })
  }
  @($rows)
}

if(-not (Test-Path -LiteralPath $sourceRoot -PathType Container)){ throw 'SOURCE_ROOT_MISSING' }
if((Test-Path -LiteralPath $targetRoot -PathType Leaf) -or (Test-Path -LiteralPath $targetRoot -PathType Container) -or (Test-Path -LiteralPath $targetRoot)){ throw 'TARGET_ROOT_NOT_ABSENT' }
if(-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($targetRoot)) -PathType Container)){ throw 'TARGET_PARENT_MISSING' }
foreach($externalPath in @($externalAuditPath,$externalReportPath,$externalHandoffPath)) {
  if(Test-Path -LiteralPath $externalPath){ throw 'EXTERNAL_OUTPUT_ALREADY_EXISTS' }
}

$sourceRootBefore = @(Get-RootSnapshot $sourceRoot)
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -File -Force | Sort-Object Name)
$sourceDirs = @(Get-ChildItem -LiteralPath $sourceRoot -Directory -Force)
$sourceNames = @($sourceFiles.Name | Sort-Object)
$sourceNameDiff = @(Compare-Object -ReferenceObject $payloadNames -DifferenceObject $sourceNames)
if($sourceFiles.Count -ne 5 -or $sourceDirs.Count -ne 0 -or $sourceNameDiff.Count -ne 0){ throw 'SOURCE_PAYLOAD_SET_MISMATCH' }
$sourceRows = @($payloadNames | ForEach-Object { Get-IdentityRow (Join-Path $sourceRoot $_) })

$targetParent = [IO.Path]::GetDirectoryName($targetRoot)
$null = New-Item -ItemType Directory -Path $targetRoot
foreach($name in $payloadNames) {
  $sourceFile = Join-Path $sourceRoot $name
  $targetFile = Join-Path $targetRoot $name
  Copy-Item -LiteralPath $sourceFile -Destination $targetFile
  $sourceItem = Get-Item -LiteralPath $sourceFile
  $targetItem = Get-Item -LiteralPath $targetFile
  $targetItem.CreationTimeUtc = $sourceItem.CreationTimeUtc
  $targetItem.LastWriteTimeUtc = $sourceItem.LastWriteTimeUtc
}

$copyErrors = [Collections.Generic.List[string]]::new()
foreach($sourceRow in $sourceRows) {
  $targetRow = Get-IdentityRow (Join-Path $targetRoot ([string]$sourceRow.relative_path))
  if(([string]$sourceRow.relative_path -cne [string]$targetRow.relative_path) -or
     ([string]$sourceRow.bytes -cne [string]$targetRow.bytes) -or
     ([string]$sourceRow.sha256 -cne [string]$targetRow.sha256) -or
     ([string]$sourceRow.creation_time_utc_ticks -cne [string]$targetRow.creation_time_utc_ticks) -or
     ([string]$sourceRow.last_write_time_utc_ticks -cne [string]$targetRow.last_write_time_utc_ticks)) {
    $copyErrors.Add([string]$sourceRow.relative_path)
  }
}
if($copyErrors.Count -ne 0){ throw 'SOURCE_TO_TARGET_IDENTITY_MISMATCH' }

$targetRows = @($payloadNames | ForEach-Object { Get-IdentityRow (Join-Path $targetRoot $_) })
$manifest = [ordered]@{
  schema='P109_STATIC_CONTROL_RESEAL_PAYLOAD_MANIFEST_V1'
  handoff_id=$handoffId
  operation=$operation
  source_root=$sourceRoot
  target_root=$targetRoot
  payload_count=5
  excluded_controls=$controlNames
  rows=$targetRows
}
$manifestPath = Join-Path $targetRoot 'PAYLOAD_MANIFEST.json'
[IO.File]::WriteAllText($manifestPath,($manifest | ConvertTo-Json -Depth 6),$utf8NoBom)

$manifestRead = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifestNames = @($manifestRead.rows.relative_path | Sort-Object)
$manifestSetDiff = @(Compare-Object -ReferenceObject $payloadNames -DifferenceObject $manifestNames)
if([int]$manifestRead.payload_count -ne 5 -or $manifestSetDiff.Count -ne 0){ throw 'MANIFEST_SET_MISMATCH' }
$manifestErrors = [Collections.Generic.List[string]]::new()
foreach($row in @($manifestRead.rows)) {
  $actual = Get-IdentityRow (Join-Path $targetRoot ([string]$row.relative_path))
  if(([string]$row.bytes -cne [string]$actual.bytes) -or
     ([string]$row.sha256 -cne [string]$actual.sha256) -or
     ([string]$row.creation_time_utc_ticks -cne [string]$actual.creation_time_utc_ticks) -or
     ([string]$row.last_write_time_utc_ticks -cne [string]$actual.last_write_time_utc_ticks)) {
    $manifestErrors.Add([string]$row.relative_path)
  }
}
if($manifestErrors.Count -ne 0){ throw 'MANIFEST_IDENTITY_MISMATCH' }

$sealAuditPath = Join-Path $targetRoot 'SEAL_AUDIT.json'
$sealAudit = [ordered]@{
  schema='P109_STATIC_CONTROL_RESEAL_AUDIT_V1'
  status='PASS'
  handoff_id=$handoffId
  operation=$operation
  source_root=$sourceRoot
  target_root=$targetRoot
  source_material_count=5
  copied_material_count=5
  old_control_copied_count=0
  payload_count=5
  control_count=3
  expected_ordinary_count=8
  source_to_target_identity_error_count=0
  manifest_set_error_count=0
  manifest_identity_error_count=0
  static_status='STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  tex_or_build_run=$false
}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit | ConvertTo-Json -Depth 5),$utf8NoBom)

$preMarkerFiles = @(Get-ChildItem -LiteralPath $targetRoot -File -Force)
$preMarkerDirs = @(Get-ChildItem -LiteralPath $targetRoot -Directory -Force)
if($preMarkerFiles.Count -ne 7 -or $preMarkerDirs.Count -ne 0){ throw 'PREMARKER_COUNT_MISMATCH' }
foreach($file in $preMarkerFiles) { $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly }
foreach($dir in $preMarkerDirs) { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
$targetRootItem = Get-Item -LiteralPath $targetRoot
$targetRootItem.Attributes = $targetRootItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$preMarkerItems = @($preMarkerFiles + $preMarkerDirs + (Get-Item -LiteralPath $targetRoot))
$preMarkerReadonlyMissing = @($preMarkerItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if($preMarkerReadonlyMissing.Count -ne 0){ throw 'PREMARKER_READONLY_FAILURE' }

$markerTemp = Join-Path $targetParent 'P109_R2A_WRITE_STOPPED.prepared'
if(Test-Path -LiteralPath $markerTemp){ throw 'MARKER_TEMP_ALREADY_EXISTS' }
$markerLines = @(
  'SCHEMA=P109_STATIC_CONTROL_RESEAL_WRITE_STOPPED_V1',
  "STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS",
  "HANDOFF_ID=$handoffId",
  "OPERATION=$operation",
  "ROOT=$targetRoot",
  'PAYLOAD_COUNT=5',
  'CONTROL_COUNT=3',
  'ORDINARY_COUNT=8',
  'PREMARKER_READONLY=TRUE',
  'LAST_ROOT_OPERATION=SINGLE_MOVE_PREPARED_READONLY_MARKER',
  'POSTMARKER_CONTENT_WRITES=0',
  'POSTMARKER_ATTRIBUTE_WRITES=0'
)
$badMarkerLines = @($markerLines | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -notmatch '^[^=\r\n]+=[^\r\n]+$' })
$markerKeys = @($markerLines | ForEach-Object { ($_ -split '=',2)[0] })
$duplicateMarkerKeys = @($markerKeys | Group-Object | Where-Object { $_.Count -ne 1 })
if($badMarkerLines.Count -ne 0 -or $duplicateMarkerKeys.Count -ne 0){ throw 'MARKER_SYNTAX_FAILURE' }
[IO.File]::WriteAllLines($markerTemp,$markerLines,$utf8NoBom)
$markerTempItem = Get-Item -LiteralPath $markerTemp
$markerTempItem.Attributes = $markerTempItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$maxPreMarkerTicks = (@($preMarkerItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks,[int64]$maxPreMarkerTicks + [TimeSpan]::FromMinutes(2).Ticks)
$markerTempItem.LastWriteTimeUtc = [DateTime]::new([int64]$futureTicks,[DateTimeKind]::Utc)
$markerPath = Join-Path $targetRoot 'WRITE_STOPPED'
Move-Item -LiteralPath $markerTemp -Destination $markerPath

$postMarkerSnapshot1 = @(Get-RootSnapshot $targetRoot)
Start-Sleep -Milliseconds 1200
$postMarkerSnapshot2 = @(Get-RootSnapshot $targetRoot)
$postMarkerMutationCount = if(($postMarkerSnapshot1 | ConvertTo-Json -Depth 6 -Compress) -ceq ($postMarkerSnapshot2 | ConvertTo-Json -Depth 6 -Compress)){0}else{1}

$finalFiles = @(Get-ChildItem -LiteralPath $targetRoot -File -Force)
$finalDirs = @(Get-ChildItem -LiteralPath $targetRoot -Directory -Force)
$finalItems = @($finalFiles + $finalDirs + (Get-Item -LiteralPath $targetRoot))
$readonlyMissing = @($finalItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$wstopFiles = @($finalFiles | Where-Object { $_.Name -eq 'WRITE_STOPPED' })
if($wstopFiles.Count -ne 1){ throw 'WSTOP_UNIQUENESS_FAILURE' }
$markerItem = $wstopFiles[0]
$atOrAfter = @($finalItems | Where-Object { $_.FullName -ne $markerPath -and $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
$maxOtherTicks = (@($finalItems | Where-Object { $_.FullName -ne $markerPath } | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum

$markerReadLines = @(Get-Content -LiteralPath $markerPath)
$markerReadBad = @($markerReadLines | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -notmatch '^[^=\r\n]+=[^\r\n]+$' })
$markerReadKeys = @($markerReadLines | ForEach-Object { ($_ -split '=',2)[0] })
$markerReadDuplicateKeys = @($markerReadKeys | Group-Object | Where-Object { $_.Count -ne 1 })

$manifestFinal = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$manifestFinalNames = @($manifestFinal.rows.relative_path | Sort-Object)
$manifestFinalSetDiff = @(Compare-Object -ReferenceObject $payloadNames -DifferenceObject $manifestFinalNames)
$manifestFinalErrors = [Collections.Generic.List[string]]::new()
foreach($row in @($manifestFinal.rows)) {
  $actual = Get-IdentityRow (Join-Path $targetRoot ([string]$row.relative_path))
  if(([string]$row.bytes -cne [string]$actual.bytes) -or
     ([string]$row.sha256 -cne [string]$actual.sha256) -or
     ([string]$row.creation_time_utc_ticks -cne [string]$actual.creation_time_utc_ticks) -or
     ([string]$row.last_write_time_utc_ticks -cne [string]$actual.last_write_time_utc_ticks)) {
    $manifestFinalErrors.Add([string]$row.relative_path)
  }
}

$parseErrors = [Collections.Generic.List[string]]::new()
foreach($file in @($finalFiles | Where-Object { $_.Extension -eq '.json' })) {
  try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json }
  catch { $parseErrors.Add($file.Name) }
}
$ads = [Collections.Generic.List[string]]::new()
foreach($file in $finalFiles) {
  foreach($stream in @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object { $_.Stream -ne ':$DATA' })) {
    $ads.Add($file.Name + ':' + $stream.Stream)
  }
}
$cachePyc = @($finalItems | Where-Object { $_.Name -match '(?i)(__pycache__|\.pyc$|cache)' })
$reparse = @($finalItems | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })

$sourceRootAfter = @(Get-RootSnapshot $sourceRoot)
$oldRootMutationCount = if(($sourceRootBefore | ConvertTo-Json -Depth 6 -Compress) -ceq ($sourceRootAfter | ConvertTo-Json -Depth 6 -Compress)){0}else{1}
$sourceIdentityAfter = @($payloadNames | ForEach-Object { Get-IdentityRow (Join-Path $sourceRoot $_) })
$sourceAfterErrors = [Collections.Generic.List[string]]::new()
for($index=0;$index -lt $sourceRows.Count;$index++) {
  if(($sourceRows[$index] | ConvertTo-Json -Compress) -cne ($sourceIdentityAfter[$index] | ConvertTo-Json -Compress)) {
    $sourceAfterErrors.Add([string]$sourceRows[$index].relative_path)
  }
}

$sourceCurrent = Get-Item -LiteralPath $sourcePath
$sourceCurrentSha = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
$controllerItem = Get-Item -LiteralPath $PSCommandPath
$controllerSha = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
$status = if(
  $finalFiles.Count -eq 8 -and $finalDirs.Count -eq 0 -and
  $readonlyMissing.Count -eq 0 -and $wstopFiles.Count -eq 1 -and $atOrAfter.Count -eq 0 -and
  $postMarkerMutationCount -eq 0 -and $manifestFinalSetDiff.Count -eq 0 -and $manifestFinalErrors.Count -eq 0 -and
  $markerReadLines.Count -eq 12 -and $markerReadBad.Count -eq 0 -and $markerReadDuplicateKeys.Count -eq 0 -and
  $parseErrors.Count -eq 0 -and $ads.Count -eq 0 -and $cachePyc.Count -eq 0 -and $reparse.Count -eq 0 -and
  $oldRootMutationCount -eq 0 -and $sourceAfterErrors.Count -eq 0 -and
  $sourceCurrent.Length -eq 1922 -and $sourceCurrentSha -ceq '887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355'
){'PASS'}else{'FAIL'}

$externalAudit = [ordered]@{
  schema='P109_STATIC_CONTROL_RESEAL_ROOT_EXTERNAL_AUDIT_V1'
  status=$status
  handoff_id=$handoffId
  operation=$operation
  source_root=$sourceRoot
  target_root=$targetRoot
  controller_path=$PSCommandPath
  controller_bytes=[int64]$controllerItem.Length
  controller_sha256=$controllerSha
  controller_invocation_count=1
  retry_count=0
  source_material_count=5
  copied_material_count=5
  old_control_copied_count=0
  source_to_target_identity_error_count=$copyErrors.Count
  payload_count=5
  control_count=3
  ordinary_count=$finalFiles.Count
  directory_count_below_root=$finalDirs.Count
  manifest_set_error_count=$manifestFinalSetDiff.Count
  manifest_identity_error_count=$manifestFinalErrors.Count
  readonly_missing_count=$readonlyMissing.Count
  wstop_unique_count=$wstopFiles.Count
  wstop_physical_line_count=$markerReadLines.Count
  wstop_bad_line_count=$markerReadBad.Count
  wstop_duplicate_key_count=$markerReadDuplicateKeys.Count
  wstop_strict_latest_including_root=($atOrAfter.Count -eq 0)
  wstop_margin_ticks=([int64]$markerItem.LastWriteTimeUtc.Ticks - [int64]$maxOtherTicks)
  excluding_marker_at_or_after_count=$atOrAfter.Count
  postmarker_content_or_attribute_mutation_count=$postMarkerMutationCount
  parse_error_count=$parseErrors.Count
  ads_count=$ads.Count
  cache_pyc_count=$cachePyc.Count
  reparse_count=$reparse.Count
  old_root_mutation_count=$oldRootMutationCount
  old_root_identity_error_count=$sourceAfterErrors.Count
  source_current_bytes=[int64]$sourceCurrent.Length
  source_current_sha256=$sourceCurrentSha
  tex_or_build_run=$false
  rendered=$false
  pass_claimed=$false
}
[IO.File]::WriteAllText($externalAuditPath,($externalAudit | ConvertTo-Json -Depth 6),$utf8NoBom)

$report = @"
# P109 R2A static control reseal report

- HANDOFF_ID: $handoffId
- Operation: $operation
- Result: $status
- Static state: STATIC_ONLY_NOT_RENDERED_NOT_PASS
- Source: 1,922 bytes / SHA-256 $sourceCurrentSha
- Copy identity: 5/5 payload path, bytes, SHA-256, CreationTimeUtc ticks, and LastWriteTimeUtc ticks preserved; old controls copied 0.
- Final model: payload 5 + controls 3 = ordinary $($finalFiles.Count).
- Manifest set/identity errors: $($manifestFinalSetDiff.Count) / $($manifestFinalErrors.Count).
- ReadOnly missing: $($readonlyMissing.Count).
- WSTOP: unique $($wstopFiles.Count), 12 physical lines, strictly latest including root with margin $([int64]$markerItem.LastWriteTimeUtc.Ticks - [int64]$maxOtherTicks) ticks, excluding-marker at-or-after $($atOrAfter.Count).
- Postmarker mutation count: $postMarkerMutationCount.
- Parse/ADS/cache-pyc/reparse: $($parseErrors.Count)/$($ads.Count)/$($cachePyc.Count)/$($reparse.Count).
- Old R2 mutation/identity errors: $oldRootMutationCount/$($sourceAfterErrors.Count).
- TeX/build/commit/fresh role/second UID: 0.

The accepted source patch remains static-only and unrendered. Request exactly one controlled standalone/direct LuaLaTeX build slot; do not start it automatically.
"@
[IO.File]::WriteAllText($externalReportPath,$report,$utf8NoBom)

$handoff = @"
# P109 R2A static handoff

A-R114-P109-SA2-STATIC-DOMAIN-LABEL-PATCH-CONTROL-RESEAL-V1-20260828 completed with root-external audit $status.

Sealed root: $targetRoot

Static patch identity: 1,922 bytes / SHA-256 $sourceCurrentSha; exact one-file 1+/1- opaque domain-label protection; not rendered and not a PASS claim.

The new root contains five losslessly copied payload files plus exactly PAYLOAD_MANIFEST.json, SEAL_AUDIT.json, and final WRITE_STOPPED. Request Main review and one controlled standalone/direct LuaLaTeX build slot. No build was started.
"@
[IO.File]::WriteAllText($externalHandoffPath,$handoff,$utf8NoBom)
foreach($externalPath in @($externalAuditPath,$externalReportPath,$externalHandoffPath)) {
  $externalItem = Get-Item -LiteralPath $externalPath
  $externalItem.Attributes = $externalItem.Attributes -bor [IO.FileAttributes]::ReadOnly
}
if($status -ne 'PASS'){ throw 'ROOT_EXTERNAL_AUDIT_FAILED' }
$externalAudit | ConvertTo-Json -Depth 6
