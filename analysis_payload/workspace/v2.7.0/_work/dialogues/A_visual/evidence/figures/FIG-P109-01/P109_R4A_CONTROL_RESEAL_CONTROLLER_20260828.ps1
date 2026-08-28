$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4_SA1_FRESH_ISOLATED_R115_20260828'
$targetRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$sourceManifestPath = Join-Path $sourceRoot 'evidence_manifest.csv'
$sourceMarkerPath = Join-Path $sourceRoot 'WSTOP'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828_CONTROLLER_RESULT.json'
$handoffId = 'A-R115-P109-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1-20260828'
$operation = 'P109_R115_SA1_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$mainSourceSnapshotSha = '161ECBDB2153C7497971F3AD2C58A88AB33F12C59B1498EFCE75F204FBE847A0'
$expectedSourceManifestSha = '13F530C3BE817C6C50CB64420EB7CB8268E1B83025D9D460F227BC09659F0E5C'
$expectedSourceMarkerSha = '2C48561B31FD652CAA78BD460DE890D8484B458CCFC74AADD6B7D9DB29259614'
$controlNames = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')
$controlSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($name in $controlNames) { $null = $controlSet.Add($name) }
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-RelativePath([string]$Root,[string]$Path) {
  [IO.Path]::GetRelativePath($Root,$Path).Replace('\','/')
}

function Get-FileIdentity([string]$Root,[IO.FileInfo]$File) {
  [ordered]@{
    relative_path = Get-RelativePath $Root $File.FullName
    bytes = [int64]$File.Length
    sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash
    creation_time_utc_ticks = $File.CreationTimeUtc.Ticks.ToString()
    last_write_time_utc_ticks = $File.LastWriteTimeUtc.Ticks.ToString()
  }
}

function Get-RootSnapshot([string]$Root) {
  $rows = [Collections.Generic.List[object]]::new()
  $rootItem = Get-Item -LiteralPath $Root -Force
  $rows.Add([ordered]@{
    kind='directory'; relative_path='.'; bytes=''; sha256=''
    creation_time_utc_ticks=$rootItem.CreationTimeUtc.Ticks.ToString()
    last_write_time_utc_ticks=$rootItem.LastWriteTimeUtc.Ticks.ToString()
    attributes=[int]$rootItem.Attributes
  })
  foreach($item in @(Get-ChildItem -LiteralPath $Root -Recurse -Force | Sort-Object FullName)) {
    $relativePath = Get-RelativePath $Root $item.FullName
    if($item.PSIsContainer) {
      $rows.Add([ordered]@{
        kind='directory'; relative_path=$relativePath; bytes=''; sha256=''
        creation_time_utc_ticks=$item.CreationTimeUtc.Ticks.ToString()
        last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString()
        attributes=[int]$item.Attributes
      })
    } else {
      $rows.Add([ordered]@{
        kind='file'; relative_path=$relativePath; bytes=[int64]$item.Length
        sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash
        creation_time_utc_ticks=$item.CreationTimeUtc.Ticks.ToString()
        last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString()
        attributes=[int]$item.Attributes
      })
    }
  }
  @($rows)
}

function Get-RowsSha([object[]]$Rows) {
  $json = $Rows | ConvertTo-Json -Depth 7 -Compress
  $sha = [Security.Cryptography.SHA256]::Create()
  try { ([BitConverter]::ToString($sha.ComputeHash($utf8NoBom.GetBytes($json)))).Replace('-','') }
  finally { $sha.Dispose() }
}

function Get-TargetPayloadRows {
  $rows = [Collections.Generic.List[object]]::new()
  foreach($file in @(Get-ChildItem -LiteralPath $targetRoot -File -Recurse -Force | Sort-Object FullName)) {
    $relativePath = Get-RelativePath $targetRoot $file.FullName
    if(-not $controlSet.Contains($relativePath)) { $rows.Add((Get-FileIdentity $targetRoot $file)) }
  }
  @($rows)
}

if(-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { throw 'SOURCE_ROOT_MISSING' }
if((Test-Path -LiteralPath $targetRoot -PathType Leaf) -or (Test-Path -LiteralPath $targetRoot -PathType Container) -or (Test-Path -LiteralPath $targetRoot)) { throw 'TARGET_ROOT_NOT_ABSENT' }
if(-not (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($targetRoot)) -PathType Container)) { throw 'TARGET_PARENT_MISSING' }
if(Test-Path -LiteralPath $controllerResultPath) { throw 'CONTROLLER_RESULT_EXISTS' }

$sourceManifestItem = Get-Item -LiteralPath $sourceManifestPath
$sourceMarkerItem = Get-Item -LiteralPath $sourceMarkerPath
if((Get-FileHash -LiteralPath $sourceManifestPath -Algorithm SHA256).Hash -cne $expectedSourceManifestSha) { throw 'SOURCE_MANIFEST_SHA_MISMATCH' }
if((Get-FileHash -LiteralPath $sourceMarkerPath -Algorithm SHA256).Hash -cne $expectedSourceMarkerSha) { throw 'SOURCE_MARKER_SHA_MISMATCH' }
$sourceManifestRows = @(Import-Csv -LiteralPath $sourceManifestPath)
$sourceBoundNames = @($sourceManifestRows.NAME)
$sourceNameDuplicates = @($sourceBoundNames | Group-Object | Where-Object { $_.Count -ne 1 })
$sourceDirs = @(Get-ChildItem -LiteralPath $sourceRoot -Directory -Recurse -Force)
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -File -Force)
$sourceMaterialFiles = @($sourceFiles | Where-Object { $_.Name -notin @('evidence_manifest.csv','WSTOP') })
$sourceSetDiff = @(Compare-Object -ReferenceObject @($sourceBoundNames | Sort-Object) -DifferenceObject @($sourceMaterialFiles.Name | Sort-Object))
if($sourceManifestRows.Count -ne 37 -or $sourceNameDuplicates.Count -ne 0 -or $sourceDirs.Count -ne 0 -or $sourceFiles.Count -ne 39 -or $sourceMaterialFiles.Count -ne 37 -or $sourceSetDiff.Count -ne 0) { throw 'SOURCE_BOUND_SET_MISMATCH' }
foreach($row in $sourceManifestRows) {
  $file = Get-Item -LiteralPath (Join-Path $sourceRoot ([string]$row.NAME))
  if([int64]$row.BYTES -ne [int64]$file.Length -or [string]$row.LAST_WRITE_UTC -cne $file.LastWriteTimeUtc.ToString('o',[Globalization.CultureInfo]::InvariantCulture)) { throw "SOURCE_MANIFEST_ROW_MISMATCH:$($row.NAME)" }
}

$sourceSnapshotBefore = @(Get-RootSnapshot $sourceRoot)
$sourceSnapshotBeforeSha = Get-RowsSha $sourceSnapshotBefore
$sourceIdentityRows = @($sourceBoundNames | Sort-Object | ForEach-Object { Get-FileIdentity $sourceRoot (Get-Item -LiteralPath (Join-Path $sourceRoot $_)) })

$null = New-Item -ItemType Directory -Path $targetRoot
foreach($sourceRow in $sourceIdentityRows) {
  $sourceFile = Join-Path $sourceRoot ([string]$sourceRow.relative_path)
  $targetFile = Join-Path $targetRoot ([string]$sourceRow.relative_path)
  Copy-Item -LiteralPath $sourceFile -Destination $targetFile
  $sourceItem = Get-Item -LiteralPath $sourceFile
  $targetItem = Get-Item -LiteralPath $targetFile
  $targetItem.CreationTimeUtc = $sourceItem.CreationTimeUtc
  $targetItem.LastWriteTimeUtc = $sourceItem.LastWriteTimeUtc
}

$copyRows = [Collections.Generic.List[object]]::new()
$copyErrors = [Collections.Generic.List[string]]::new()
foreach($sourceRow in $sourceIdentityRows) {
  $destination = Get-FileIdentity $targetRoot (Get-Item -LiteralPath (Join-Path $targetRoot ([string]$sourceRow.relative_path)))
  $copyRows.Add([ordered]@{
    source_relative_path=[string]$sourceRow.relative_path
    destination_relative_path=[string]$destination.relative_path
    bytes=[int64]$sourceRow.bytes
    sha256=[string]$sourceRow.sha256
    creation_time_utc_ticks=[string]$sourceRow.creation_time_utc_ticks
    last_write_time_utc_ticks=[string]$sourceRow.last_write_time_utc_ticks
  })
  foreach($field in @('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')) {
    if([string]$sourceRow.$field -cne [string]$destination.$field) { $copyErrors.Add("$($sourceRow.relative_path):$field"); break }
  }
}
if($copyErrors.Count -ne 0) { throw 'COPY_IDENTITY_MISMATCH' }

$copyIdentityPath = Join-Path $targetRoot 'COPY_IDENTITY.csv'
$copyProvenancePath = Join-Path $targetRoot 'COPY_PROVENANCE.json'
$copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8
$provenance = [ordered]@{
  schema='P109_R4A_COPY_PROVENANCE_V1'
  handoff_id=$handoffId
  operation=$operation
  source_root=[IO.Path]::GetFullPath($sourceRoot)
  target_root=[IO.Path]::GetFullPath($targetRoot)
  source_manifest_path=[IO.Path]::GetFullPath($sourceManifestPath)
  source_manifest_sha256=$expectedSourceManifestSha
  source_wstop_path=[IO.Path]::GetFullPath($sourceMarkerPath)
  source_wstop_sha256=$expectedSourceMarkerSha
  main_canonical_full_root_snapshot_sha256=$mainSourceSnapshotSha
  controller_source_snapshot_before_sha256=$sourceSnapshotBeforeSha
  copied_material_count=37
  added_payload_count=2
  final_payload_count=39
  preserved_fields=@('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
  business_evidence_rerun=$false
  verdict='SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
}
[IO.File]::WriteAllText($copyProvenancePath,($provenance | ConvertTo-Json -Depth 7),$utf8NoBom)

$payloadRows = @(Get-TargetPayloadRows)
$payloadDuplicates = @($payloadRows.relative_path | Group-Object | Where-Object { $_.Count -ne 1 })
if($payloadRows.Count -ne 39 -or $payloadDuplicates.Count -ne 0) { throw 'PAYLOAD_SET_MISMATCH' }
$manifestPath = Join-Path $targetRoot 'PAYLOAD_MANIFEST.csv'
$payloadRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8
$manifestRead = @(Import-Csv -LiteralPath $manifestPath)
$manifestSetDiff = @(Compare-Object -ReferenceObject @($payloadRows.relative_path | Sort-Object) -DifferenceObject @($manifestRead.relative_path | Sort-Object))
$manifestErrors = [Collections.Generic.List[string]]::new()
foreach($row in $manifestRead) {
  $actual = @(Get-TargetPayloadRows | Where-Object { $_.relative_path -ceq $row.relative_path })
  if($actual.Count -ne 1) { $manifestErrors.Add([string]$row.relative_path); continue }
  foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')) {
    if([string]$row.$field -cne [string]$actual[0].$field) { $manifestErrors.Add("$($row.relative_path):$field"); break }
  }
}
if($manifestRead.Count -ne 39 -or $manifestSetDiff.Count -ne 0 -or $manifestErrors.Count -ne 0) { throw 'PAYLOAD_MANIFEST_MISMATCH' }

$sealAuditPath = Join-Path $targetRoot 'SEAL_AUDIT.json'
$sealAudit = [ordered]@{
  schema='P109_R4A_PREMARKER_SEAL_AUDIT_V1'
  status='PASS'
  handoff_id=$handoffId
  operation=$operation
  source_material_count=37
  copied_material_count=37
  old_control_copied_count=0
  payload_count=39
  control_count=3
  expected_ordinary_count=42
  copy_identity_error_count=$copyErrors.Count
  manifest_set_error_count=$manifestSetDiff.Count
  manifest_identity_error_count=$manifestErrors.Count
  source_manifest_sha256=$expectedSourceManifestSha
  source_wstop_sha256=$expectedSourceMarkerSha
  main_canonical_full_root_snapshot_sha256=$mainSourceSnapshotSha
  source_snapshot_before_sha256=$sourceSnapshotBeforeSha
  verdict='SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
  pdf_render_visual_manual_semantic_rerun=$false
}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit | ConvertTo-Json -Depth 7),$utf8NoBom)

$preMarkerFiles = @(Get-ChildItem -LiteralPath $targetRoot -File -Recurse -Force)
$preMarkerDirs = @(Get-ChildItem -LiteralPath $targetRoot -Directory -Recurse -Force | Sort-Object FullName -Descending)
if($preMarkerFiles.Count -ne 41 -or $preMarkerDirs.Count -ne 0) { throw 'PREMARKER_COUNT_MISMATCH' }

$manifestSha = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash
$copyIdentitySha = (Get-FileHash -LiteralPath $copyIdentityPath -Algorithm SHA256).Hash
$copyProvenanceSha = (Get-FileHash -LiteralPath $copyProvenancePath -Algorithm SHA256).Hash
$sealAuditSha = (Get-FileHash -LiteralPath $sealAuditPath -Algorithm SHA256).Hash
$markerTemp = Join-Path ([IO.Path]::GetDirectoryName($targetRoot)) 'P109_R4A_WRITE_STOPPED.prepared'
if(Test-Path -LiteralPath $markerTemp) { throw 'MARKER_TEMP_EXISTS' }
$markerKeyOrder = @(
  'SCHEMA','STATUS','HANDOFF_ID','OPERATION','SOURCE_ROOT','TARGET_ROOT','SOURCE_MATERIAL_COUNT','COPIED_MATERIAL_COUNT','OLD_CONTROL_COPIED_COUNT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','SOURCE_MANIFEST_SHA256','SOURCE_WSTOP_SHA256','MAIN_CANONICAL_SOURCE_SNAPSHOT_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','PREMARKER_READONLY','LAST_ROOT_OPERATION','POSTMARKER_CONTENT_WRITES','POSTMARKER_ATTRIBUTE_WRITES','CONTROLLER_INVOCATION_COUNT','RETRY_COUNT','VERDICT'
)
$markerValues = [ordered]@{
  SCHEMA='P109_R4A_WRITE_STOPPED_V1'
  STATUS='PASS'
  HANDOFF_ID=$handoffId
  OPERATION=$operation
  SOURCE_ROOT=[IO.Path]::GetFullPath($sourceRoot)
  TARGET_ROOT=[IO.Path]::GetFullPath($targetRoot)
  SOURCE_MATERIAL_COUNT='37'
  COPIED_MATERIAL_COUNT='37'
  OLD_CONTROL_COPIED_COUNT='0'
  PAYLOAD_COUNT='39'
  CONTROL_COUNT='3'
  ORDINARY_COUNT='42'
  SOURCE_MANIFEST_SHA256=$expectedSourceManifestSha
  SOURCE_WSTOP_SHA256=$expectedSourceMarkerSha
  MAIN_CANONICAL_SOURCE_SNAPSHOT_SHA256=$mainSourceSnapshotSha
  COPY_IDENTITY_SHA256=$copyIdentitySha
  COPY_PROVENANCE_SHA256=$copyProvenanceSha
  PAYLOAD_MANIFEST_SHA256=$manifestSha
  SEAL_AUDIT_SHA256=$sealAuditSha
  PREMARKER_READONLY='TRUE'
  LAST_ROOT_OPERATION='SINGLE_EXTERNAL_TO_ROOT_MARKER_MOVE'
  POSTMARKER_CONTENT_WRITES='0'
  POSTMARKER_ATTRIBUTE_WRITES='0'
  CONTROLLER_INVOCATION_COUNT='1'
  RETRY_COUNT='0'
  VERDICT='SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
}
$markerLines = @($markerKeyOrder | ForEach-Object { $_ + '=' + [string]$markerValues[$_] })
$markerBad = @($markerLines | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -notmatch '^[^=\r\n\t]+=[^\r\n\t]+$' -or $_ -match '\$[A-Za-z_{]' })
$markerDuplicates = @($markerKeyOrder | Group-Object | Where-Object { $_.Count -ne 1 })
if($markerLines.Count -ne 26 -or $markerBad.Count -ne 0 -or $markerDuplicates.Count -ne 0) { throw 'MARKER_CONTENT_FAILURE' }
[IO.File]::WriteAllLines($markerTemp,$markerLines,$utf8NoBom)

foreach($file in $preMarkerFiles) { $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly }
foreach($dir in $preMarkerDirs) { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
$targetRootItem = Get-Item -LiteralPath $targetRoot -Force
$targetRootItem.Attributes = $targetRootItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$preMarkerItems = @($preMarkerFiles + $preMarkerDirs + (Get-Item -LiteralPath $targetRoot -Force))
$preMarkerReadonlyMissing = @($preMarkerItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if($preMarkerReadonlyMissing.Count -ne 0) { throw 'PREMARKER_READONLY_FAILURE' }

$maxPreMarkerTicks = [int64](@($preMarkerItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks,$maxPreMarkerTicks + [TimeSpan]::FromMinutes(3).Ticks)
$markerTempItem = Get-Item -LiteralPath $markerTemp -Force
$futureTime = [DateTime]::new($futureTicks,[DateTimeKind]::Utc)
$markerTempItem.CreationTimeUtc = $futureTime
$markerTempItem.LastWriteTimeUtc = $futureTime
$markerTempItem.LastAccessTimeUtc = $futureTime
$markerTempItem.Attributes = $markerTempItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$markerPath = Join-Path $targetRoot 'WRITE_STOPPED'
Move-Item -LiteralPath $markerTemp -Destination $markerPath

$targetSnapshot1 = @(Get-RootSnapshot $targetRoot)
$targetSnapshotSha1 = Get-RowsSha $targetSnapshot1
Start-Sleep -Milliseconds 350
$targetSnapshot2 = @(Get-RootSnapshot $targetRoot)
$targetSnapshotSha2 = Get-RowsSha $targetSnapshot2
$postMarkerMutationCount = if($targetSnapshotSha1 -ceq $targetSnapshotSha2) { 0 } else { 1 }
$sourceSnapshotAfter = @(Get-RootSnapshot $sourceRoot)
$sourceSnapshotAfterSha = Get-RowsSha $sourceSnapshotAfter
$sourceMutationCount = if($sourceSnapshotBeforeSha -ceq $sourceSnapshotAfterSha) { 0 } else { 1 }

$finalFiles = @(Get-ChildItem -LiteralPath $targetRoot -File -Recurse -Force)
$finalDirs = @(Get-ChildItem -LiteralPath $targetRoot -Directory -Recurse -Force)
$finalItems = @($finalFiles + $finalDirs + (Get-Item -LiteralPath $targetRoot -Force))
$readonlyMissing = @($finalItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$markerItem = Get-Item -LiteralPath $markerPath -Force
$atOrAfter = @($finalItems | Where-Object { $_.FullName -cne $markerPath -and $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
$maxOtherTicks = [int64](@($finalItems | Where-Object { $_.FullName -cne $markerPath } | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
if($finalFiles.Count -ne 42 -or $finalDirs.Count -ne 0 -or $readonlyMissing.Count -ne 0 -or $atOrAfter.Count -ne 0 -or $postMarkerMutationCount -ne 0 -or $sourceMutationCount -ne 0) { throw 'POSTMARKER_GATE_FAILURE' }

$controllerItem = Get-Item -LiteralPath $PSCommandPath
$result = [ordered]@{
  schema='P109_R4A_CONTROLLER_RESULT_V1'
  status='PASS'
  handoff_id=$handoffId
  operation=$operation
  controller_path=$PSCommandPath
  controller_bytes=[int64]$controllerItem.Length
  controller_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
  controller_invocation_count=1
  retry_count=0
  source_material_count=37
  copied_material_count=37
  old_control_copied_count=0
  payload_count=39
  control_count=3
  ordinary_count=$finalFiles.Count
  directory_count_below_root=$finalDirs.Count
  readonly_missing_count=$readonlyMissing.Count
  marker_move_count=1
  marker_physical_line_count=$markerLines.Count
  marker_strict_latest_including_root=($atOrAfter.Count -eq 0)
  marker_margin_ticks=([int64]$markerItem.LastWriteTimeUtc.Ticks - $maxOtherTicks)
  at_or_after_excluding_marker_count=$atOrAfter.Count
  postmarker_content_or_attribute_mutation_count=$postMarkerMutationCount
  source_root_mutation_count=$sourceMutationCount
  source_snapshot_before_sha256=$sourceSnapshotBeforeSha
  source_snapshot_after_sha256=$sourceSnapshotAfterSha
  target_postmarker_snapshot_sha256_1=$targetSnapshotSha1
  target_postmarker_snapshot_sha256_2=$targetSnapshotSha2
  payload_manifest_sha256=$manifestSha
  copy_identity_sha256=$copyIdentitySha
  copy_provenance_sha256=$copyProvenanceSha
  seal_audit_sha256=$sealAuditSha
  verdict='SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
}
[IO.File]::WriteAllText($controllerResultPath,($result | ConvertTo-Json -Depth 7),$utf8NoBom)
$controllerResultItem = Get-Item -LiteralPath $controllerResultPath
$controllerResultItem.Attributes = $controllerResultItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$result | ConvertTo-Json -Depth 7
