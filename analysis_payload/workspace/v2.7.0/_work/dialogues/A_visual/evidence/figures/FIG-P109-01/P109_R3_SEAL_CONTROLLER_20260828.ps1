$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828'
$sourcePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C07\fig_v1_c07_convex_set.tex'
$pdfPath = Join-Path $root 'build\v260_FIG-P109-01_standalone.pdf'
$externalResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828_SEAL_CONTROLLER_RESULT.json'
$handoffId = 'A-R114-P109-SA2-DIRECT-BUILD-R3-20260828'
$controlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')
$controlSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($name in $controlNames){ $null = $controlSet.Add($name) }
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-RelativePath([string]$Path) {
  [IO.Path]::GetRelativePath($root,$Path).Replace('\','/')
}

function Get-FileRow([IO.FileInfo]$File) {
  [ordered]@{
    relative_path = Get-RelativePath $File.FullName
    bytes = [int64]$File.Length
    sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash
    creation_time_utc_ticks = $File.CreationTimeUtc.Ticks.ToString()
    last_write_time_utc_ticks = $File.LastWriteTimeUtc.Ticks.ToString()
  }
}

function Get-PayloadRows {
  $rows = [Collections.Generic.List[object]]::new()
  foreach($file in @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Sort-Object FullName)) {
    $relativePath = Get-RelativePath $file.FullName
    if(-not $controlSet.Contains($relativePath)) { $rows.Add((Get-FileRow $file)) }
  }
  @($rows)
}

function Get-RootSnapshotRows {
  $rows = [Collections.Generic.List[object]]::new()
  $rootItem = Get-Item -LiteralPath $root -Force
  $rows.Add([ordered]@{
    kind='directory'; relative_path='.'; bytes=''; sha256=''
    creation_time_utc_ticks=$rootItem.CreationTimeUtc.Ticks.ToString()
    last_write_time_utc_ticks=$rootItem.LastWriteTimeUtc.Ticks.ToString()
    attributes=[int]$rootItem.Attributes
  })
  foreach($item in @(Get-ChildItem -LiteralPath $root -Recurse -Force | Sort-Object FullName)) {
    $relativePath = Get-RelativePath $item.FullName
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
  $text = $Rows | ConvertTo-Json -Depth 6 -Compress
  $bytes = $utf8NoBom.GetBytes($text)
  $sha = [Security.Cryptography.SHA256]::Create()
  try { ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','') }
  finally { $sha.Dispose() }
}

function Assert-ManualCsv([string]$Name,[int]$ExpectedCount,[string]$IdColumn) {
  $path = Join-Path $root $Name
  $rows = @(Import-Csv -LiteralPath $path)
  $unique = @($rows.$IdColumn | Sort-Object -Unique)
  $nonPass = @($rows | Where-Object { $_.decision -cne 'PASS' })
  $blank = @($rows | Where-Object { [string]::IsNullOrWhiteSpace($_.note) })
  if($rows.Count -ne $ExpectedCount -or $unique.Count -ne $ExpectedCount -or $nonPass.Count -ne 0 -or $blank.Count -ne 0) {
    throw "MANUAL_LEDGER_FAILURE:$Name"
  }
  @($rows)
}

if(-not (Test-Path -LiteralPath $root -PathType Container)){ throw 'ROOT_MISSING' }
if(Test-Path -LiteralPath $externalResultPath){ throw 'EXTERNAL_RESULT_EXISTS' }
foreach($name in $controlNames) {
  if(Test-Path -LiteralPath (Join-Path $root $name)){ throw "CONTROL_ALREADY_EXISTS:$name" }
}

$sourceItem = Get-Item -LiteralPath $sourcePath
$sourceSha = (Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash
if($sourceItem.Length -ne 1922 -or $sourceSha -cne '887326D54E8DD97AA6D580EFA7CCD21FA371A94CACD36EB7029E80FC4D2D9355'){ throw 'SOURCE_IDENTITY_MISMATCH' }
$pdfItem = Get-Item -LiteralPath $pdfPath
$pdfSha = (Get-FileHash -LiteralPath $pdfPath -Algorithm SHA256).Hash
if($pdfItem.Length -ne 26500 -or $pdfSha -cne 'C615152183FCB524F2B4FBDFB4A69D43C134DCDE20F989BF0050C2D2776A199D'){ throw 'PDF_IDENTITY_MISMATCH' }

$objects = Assert-ManualCsv 'MANUAL_OBJECTS.csv' 15 'object_id'
$pairs = Assert-ManualCsv 'MANUAL_PAIRS.csv' 105 'pair_id'
$views = Assert-ManualCsv 'MANUAL_VIEWS.csv' 20 'view_id'
$mathRows = Assert-ManualCsv 'MANUAL_MATH_SEMANTICS.csv' 8 'check_id'
$glyphRows = Assert-ManualCsv 'MANUAL_GLYPH_CODEPOINTS.csv' 52 'glyph_id'
$machinePairs = @(Import-Csv -LiteralPath (Join-Path $root 'MACHINE_PAIRS.csv'))
if($machinePairs.Count -ne 105){ throw 'MACHINE_PAIR_COUNT_MISMATCH' }
$pairMapErrors = @(
  foreach($machine in $machinePairs) {
    $manual = @($pairs | Where-Object { $_.pair_id -ceq $machine.pair_id })
    if($manual.Count -ne 1 -or $manual[0].object_a -cne $machine.object_a -or $manual[0].object_b -cne $machine.object_b) { $machine.pair_id }
  }
)
if($pairMapErrors.Count -ne 0){ throw 'MANUAL_PAIR_MAPPING_MISMATCH' }

$crosscheck = Get-Content -LiteralPath (Join-Path $root 'FINAL_CROSSCHECK.json') -Raw | ConvertFrom-Json
if($crosscheck.result -cne 'LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH' -or
   [int]$crosscheck.denominator.object_count -ne 15 -or [int]$crosscheck.denominator.unordered_pair_count -ne 105 -or
   [int]$crosscheck.hard_failure_count -ne 0){ throw 'FINAL_CROSSCHECK_MISMATCH' }

$payloadRows = @(Get-PayloadRows)
$payloadPaths = @($payloadRows.relative_path)
$duplicatePayloadPaths = @($payloadPaths | Group-Object | Where-Object { $_.Count -ne 1 })
if($payloadRows.Count -lt 1 -or $duplicatePayloadPaths.Count -ne 0){ throw 'PAYLOAD_SET_INVALID' }

$manifestCsvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$sealAuditPath = Join-Path $root 'SEAL_AUDIT.json'
$payloadRows | Export-Csv -LiteralPath $manifestCsvPath -NoTypeInformation -Encoding utf8
$manifestJson = [ordered]@{
  schema='P109_R3_PAYLOAD_MANIFEST_V1'
  handoff_id=$handoffId
  root=$root
  payload_count=$payloadRows.Count
  excluded_controls=$controlNames
  rows=$payloadRows
}
[IO.File]::WriteAllText($manifestJsonPath,($manifestJson | ConvertTo-Json -Depth 7),$utf8NoBom)

$csvRead = @(Import-Csv -LiteralPath $manifestCsvPath)
$jsonRead = Get-Content -LiteralPath $manifestJsonPath -Raw | ConvertFrom-Json
$jsonRows = @($jsonRead.rows)
$livePayloadRows = @(Get-PayloadRows)
if($csvRead.Count -ne $payloadRows.Count -or $jsonRows.Count -ne $payloadRows.Count -or $livePayloadRows.Count -ne $payloadRows.Count){ throw 'MANIFEST_COUNT_MISMATCH' }
$identityErrors = [Collections.Generic.List[string]]::new()
foreach($expected in $payloadRows) {
  $csvRow = @($csvRead | Where-Object { $_.relative_path -ceq $expected.relative_path })
  $jsonRow = @($jsonRows | Where-Object { $_.relative_path -ceq $expected.relative_path })
  $liveRow = @($livePayloadRows | Where-Object { $_.relative_path -ceq $expected.relative_path })
  if($csvRow.Count -ne 1 -or $jsonRow.Count -ne 1 -or $liveRow.Count -ne 1) { $identityErrors.Add($expected.relative_path); continue }
  foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')) {
    if(([string]$expected.$field -cne [string]$csvRow[0].$field) -or
       ([string]$expected.$field -cne [string]$jsonRow[0].$field) -or
       ([string]$expected.$field -cne [string]$liveRow[0].$field)) { $identityErrors.Add("$($expected.relative_path):$field"); break }
  }
}
if($identityErrors.Count -ne 0){ throw 'MANIFEST_IDENTITY_MISMATCH' }

$sealAudit = [ordered]@{
  schema='P109_R3_PREMARKER_SEAL_AUDIT_V1'
  status='PASS'
  handoff_id=$handoffId
  payload_count=$payloadRows.Count
  manifest_csv_rows=$csvRead.Count
  manifest_json_rows=$jsonRows.Count
  control_count=4
  expected_ordinary_count=($payloadRows.Count + 4)
  duplicate_payload_path_count=$duplicatePayloadPaths.Count
  manifest_identity_error_count=$identityErrors.Count
  object_count=$objects.Count
  unordered_pair_count=$pairs.Count
  view_count=$views.Count
  math_semantic_count=$mathRows.Count
  glyph_codepoint_count=$glyphRows.Count
  machine_pair_mapping_error_count=$pairMapErrors.Count
  hard_failure_count=0
  source_sha256=$sourceSha
  pdf_sha256=$pdfSha
  commit_created=$false
  tex_after_build_release=$false
}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit | ConvertTo-Json -Depth 6),$utf8NoBom)

$preMarkerFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$preMarkerDirs = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force | Sort-Object FullName -Descending)
if($preMarkerFiles.Count -ne ($payloadRows.Count + 3)){ throw 'PREMARKER_FILE_COUNT_MISMATCH' }

$markerTemp = Join-Path ([IO.Path]::GetDirectoryName($root)) 'P109_R3_WRITE_STOPPED.prepared'
if(Test-Path -LiteralPath $markerTemp){ throw 'MARKER_TEMP_EXISTS' }
$markerLines = @(
  'SCHEMA=P109_R3_WRITE_STOPPED_V1',
  'STATUS=LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH',
  "HANDOFF_ID=$handoffId",
  "ROOT=$root",
  "PAYLOAD_COUNT=$($payloadRows.Count)",
  'CONTROL_COUNT=4',
  "ORDINARY_COUNT=$($payloadRows.Count + 4)",
  'PREMARKER_READONLY=TRUE',
  'LAST_ROOT_OPERATION=SINGLE_MOVE_PREPARED_READONLY_MARKER',
  'POSTMARKER_CONTENT_WRITES=0',
  'POSTMARKER_ATTRIBUTE_WRITES=0',
  'COMMIT_CREATED=FALSE'
)
$badMarkerLines = @($markerLines | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -notmatch '^[^=\r\n]+=[^\r\n]+$' })
$markerKeys = @($markerLines | ForEach-Object { ($_ -split '=',2)[0] })
$duplicateMarkerKeys = @($markerKeys | Group-Object | Where-Object { $_.Count -ne 1 })
if($badMarkerLines.Count -ne 0 -or $duplicateMarkerKeys.Count -ne 0){ throw 'MARKER_SYNTAX_FAILURE' }
[IO.File]::WriteAllLines($markerTemp,$markerLines,$utf8NoBom)

foreach($file in $preMarkerFiles){ $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly }
foreach($dir in $preMarkerDirs){ $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
$rootItem = Get-Item -LiteralPath $root -Force
$rootItem.Attributes = $rootItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$preMarkerItems = @($preMarkerFiles + $preMarkerDirs + (Get-Item -LiteralPath $root -Force))
$preMarkerReadonlyMissing = @($preMarkerItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if($preMarkerReadonlyMissing.Count -ne 0){ throw 'PREMARKER_READONLY_FAILURE' }

$maxTicks = [int64](@($preMarkerItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks,$maxTicks + [TimeSpan]::FromMinutes(3).Ticks)
$markerTempItem = Get-Item -LiteralPath $markerTemp -Force
$markerTempItem.LastWriteTimeUtc = [DateTime]::new($futureTicks,[DateTimeKind]::Utc)
$markerTempItem.Attributes = $markerTempItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$markerPath = Join-Path $root 'WRITE_STOPPED'
Move-Item -LiteralPath $markerTemp -Destination $markerPath

$snapshot1 = @(Get-RootSnapshotRows)
$snapshotSha1 = Get-RowsSha $snapshot1
Start-Sleep -Milliseconds 300
$snapshot2 = @(Get-RootSnapshotRows)
$snapshotSha2 = Get-RowsSha $snapshot2
$postMarkerMutationCount = if($snapshotSha1 -ceq $snapshotSha2){0}else{1}

$finalFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$finalDirs = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
$finalItems = @($finalFiles + $finalDirs + (Get-Item -LiteralPath $root -Force))
$readonlyMissing = @($finalItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$markerItem = Get-Item -LiteralPath $markerPath -Force
$atOrAfter = @($finalItems | Where-Object { $_.FullName -cne $markerPath -and $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
$maxOtherTicks = [int64](@($finalItems | Where-Object { $_.FullName -cne $markerPath } | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
if($finalFiles.Count -ne ($payloadRows.Count + 4) -or $readonlyMissing.Count -ne 0 -or $atOrAfter.Count -ne 0 -or $postMarkerMutationCount -ne 0){ throw 'POSTMARKER_GATE_FAILURE' }

$controllerItem = Get-Item -LiteralPath $PSCommandPath
$result = [ordered]@{
  schema='P109_R3_SEAL_CONTROLLER_RESULT_V1'
  status='PASS'
  handoff_id=$handoffId
  controller_path=$PSCommandPath
  controller_bytes=[int64]$controllerItem.Length
  controller_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
  controller_invocation_count=1
  retry_count=0
  payload_count=$payloadRows.Count
  control_count=4
  ordinary_count=$finalFiles.Count
  directory_count_below_root=$finalDirs.Count
  readonly_missing_count=$readonlyMissing.Count
  marker_physical_line_count=$markerLines.Count
  marker_strict_latest_including_root=($atOrAfter.Count -eq 0)
  marker_margin_ticks=([int64]$markerItem.LastWriteTimeUtc.Ticks - $maxOtherTicks)
  at_or_after_excluding_marker_count=$atOrAfter.Count
  postmarker_content_or_attribute_mutation_count=$postMarkerMutationCount
  postmarker_snapshot_sha256_1=$snapshotSha1
  postmarker_snapshot_sha256_2=$snapshotSha2
  source_bytes=[int64]$sourceItem.Length
  source_sha256=$sourceSha
  pdf_bytes=[int64]$pdfItem.Length
  pdf_sha256=$pdfSha
  tex_or_build_run=$false
  commit_created=$false
}
[IO.File]::WriteAllText($externalResultPath,($result | ConvertTo-Json -Depth 6),$utf8NoBom)
$externalItem = Get-Item -LiteralPath $externalResultPath
$externalItem.Attributes = $externalItem.Attributes -bor [IO.FileAttributes]::ReadOnly
$result | ConvertTo-Json -Depth 6
