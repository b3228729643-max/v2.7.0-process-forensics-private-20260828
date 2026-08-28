$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R7A-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R7_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7A_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7A_WRITE_STOPPED.stage'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7A_CONTROL_RESEAL_CONTROLLER_RESULT_20260828.json'
$verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
$hardDefects = @('HARD-LEGEND-X2-CONTINUOUS','HARD-LABEL6-AXIS-CONTOUR-OVERLAP','HARD-LABEL7-MARKER-ARROW-OCCLUSION')
$utf8NoBom = [Text.UTF8Encoding]::new($false)
$startUtc = [DateTime]::UtcNow

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Is-Readonly([IO.FileSystemInfo]$Item) { (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function Set-Readonly([IO.FileSystemInfo]$Item) { $Item.Attributes = $Item.Attributes -bor [IO.FileAttributes]::ReadOnly }

function Convert-CanonicalRelative([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { throw 'relative path is empty' }
  $canonical = $Value.Replace('\','/')
  $canonical = [regex]::Replace($canonical,'^(?:\./)+','')
  if ([string]::IsNullOrWhiteSpace($canonical)) { throw 'relative path empty after normalization' }
  if ([IO.Path]::IsPathRooted($canonical) -or $canonical.StartsWith('/',[StringComparison]::Ordinal) -or $canonical -match '^[A-Za-z]:') { throw 'rooted relative path rejected' }
  $segments = @($canonical.Split('/'))
  $invalid = @($segments | Where-Object { [string]::IsNullOrEmpty([string]$_) -or [string]$_ -eq '.' -or [string]$_ -eq '..' -or [string]$_ -match '[:*?]' })
  if ($segments.Count -eq 0 -or $invalid.Count -ne 0) { throw 'unsafe relative path segment' }
  return [string]::Join('/',$segments)
}

function Resolve-Contained([string]$Base,[string]$Relative) {
  $canonical = Convert-CanonicalRelative $Relative
  $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd('\')
  $resolved = [IO.Path]::GetFullPath((Join-Path $baseFull ($canonical.Replace('/','\'))))
  $prefix = $baseFull + '\'
  if (-not $resolved.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'resolved path escapes root' }
  return $resolved
}

function Get-Relative([string]$Base,[string]$Path) {
  return Convert-CanonicalRelative ([IO.Path]::GetRelativePath($Base,$Path))
}

function Get-TreeSnapshot([string]$Root) {
  $rows = [Collections.Generic.List[string]]::new()
  $items = @(@(Get-ChildItem -LiteralPath $Root -Recurse -Force) + @(Get-Item -LiteralPath $Root) | Sort-Object FullName)
  foreach ($item in $items) {
    $relative = if ($item.FullName -ceq $Root) {'.'} else {Get-Relative $Root $item.FullName}
    $kind = if ($item.PSIsContainer) {'D'} else {'F'}
    $bytes = if ($item.PSIsContainer) {0L} else {[long]$item.Length}
    $sha = if ($item.PSIsContainer) {''} else {Get-Sha256 $item.FullName}
    $rows.Add("$kind`t$relative`t$bytes`t$sha`t$($item.CreationTimeUtc.Ticks)`t$($item.LastWriteTimeUtc.Ticks)`t$([int]$item.Attributes)")
  }
  $text = [string]::Join("`n",$rows) + "`n"
  $hasher = [Security.Cryptography.SHA256]::Create()
  return [pscustomobject]@{count=$rows.Count;sha256=[Convert]::ToHexString($hasher.ComputeHash($utf8NoBom.GetBytes($text)));rows=@($rows)}
}

function Write-CsvNoBom([string]$Path,[object[]]$Rows,[string[]]$Columns) {
  $lines = [Collections.Generic.List[string]]::new()
  $lines.Add([string]::Join(',',$Columns))
  foreach ($row in $Rows) {
    $cells = [Collections.Generic.List[string]]::new()
    foreach ($column in $Columns) {
      $value = [string]$row.$column
      $cells.Add('"' + $value.Replace('"','""') + '"')
    }
    $lines.Add([string]::Join(',',$cells))
  }
  [IO.File]::WriteAllText($Path,[string]::Join("`r`n",$lines)+"`r`n",$utf8NoBom)
}

foreach ($path in @($destinationRoot,$stagePath,$resultPath)) { if (Test-Path -LiteralPath $path) { throw "preexisting destination artifact: $path" } }
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { throw 'source R7 root missing' }
$oldControls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','PRESEAL_VALIDATION.json','SEAL_AUDIT.json','WRITE_STOPPED')
$sourceFiles = @(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Force | Sort-Object { Get-Relative $sourceRoot $_.FullName })
if ($sourceFiles.Count -ne 188) { throw "source material count mismatch: $($sourceFiles.Count)" }
$oldControlHits = @($sourceFiles | Where-Object { (Get-Relative $sourceRoot $_.FullName) -in $oldControls })
if ($oldControlHits.Count -ne 0) { throw 'old controls unexpectedly present' }
$sourceSnapshotBefore = Get-TreeSnapshot $sourceRoot

$sourceRows = [Collections.Generic.List[object]]::new()
foreach ($file in $sourceFiles) {
  $relative = Get-Relative $sourceRoot $file.FullName
  [void](Resolve-Contained $sourceRoot $relative)
  $sourceRows.Add([pscustomobject][ordered]@{
    relative_path=$relative;source_path=[IO.Path]::GetFullPath($file.FullName);bytes=[long]$file.Length
    sha256=Get-Sha256 $file.FullName;creation_time_utc_ticks=[long]$file.CreationTimeUtc.Ticks
    last_write_time_utc_ticks=[long]$file.LastWriteTimeUtc.Ticks
  })
}
$sourceDuplicateGroups = @($sourceRows | Group-Object -Property { [string]$_.relative_path } -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($sourceDuplicateGroups.Count -ne 0) { throw 'source canonical duplicate paths' }

[IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
$copyRows = [Collections.Generic.List[object]]::new()
foreach ($row in $sourceRows) {
  $destinationPath = Resolve-Contained $destinationRoot ([string]$row.relative_path)
  $destinationParent = [IO.Path]::GetDirectoryName($destinationPath)
  [IO.Directory]::CreateDirectory($destinationParent) | Out-Null
  Copy-Item -LiteralPath ([string]$row.source_path) -Destination $destinationPath
  $destinationItem = Get-Item -LiteralPath $destinationPath
  $destinationItem.CreationTimeUtc = [DateTime]::new([long]$row.creation_time_utc_ticks,[DateTimeKind]::Utc)
  $destinationItem.LastWriteTimeUtc = [DateTime]::new([long]$row.last_write_time_utc_ticks,[DateTimeKind]::Utc)
  $destinationItem = Get-Item -LiteralPath $destinationPath
  if ([long]$destinationItem.Length -ne [long]$row.bytes -or (Get-Sha256 $destinationPath) -cne [string]$row.sha256 -or [long]$destinationItem.CreationTimeUtc.Ticks -ne [long]$row.creation_time_utc_ticks -or [long]$destinationItem.LastWriteTimeUtc.Ticks -ne [long]$row.last_write_time_utc_ticks) { throw "copy identity mismatch: $($row.relative_path)" }
  $copyRows.Add([pscustomobject][ordered]@{
    relative_path=[string]$row.relative_path;source_path=[string]$row.source_path;destination_path=$destinationPath
    bytes=[long]$row.bytes;sha256=[string]$row.sha256;creation_time_utc_ticks=[long]$row.creation_time_utc_ticks
    last_write_time_utc_ticks=[long]$row.last_write_time_utc_ticks
  })
}
$copyDuplicateGroups = @($copyRows | Group-Object -Property { [string]$_.relative_path } -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($copyRows.Count -ne 188 -or $copyDuplicateGroups.Count -ne 0) { throw 'copy row set failure' }
$sourceSet = @($sourceRows | ForEach-Object { [string]$_.relative_path } | Sort-Object -CaseSensitive)
$copySet = @($copyRows | ForEach-Object { [string]$_.relative_path } | Sort-Object -CaseSensitive)
$copySetDiff = @(Compare-Object -ReferenceObject $sourceSet -DifferenceObject $copySet -CaseSensitive)
if ($copySetDiff.Count -ne 0) { throw 'source-copy set mismatch' }

$copyIdentityPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
Write-CsvNoBom $copyIdentityPath @($copyRows) @('relative_path','source_path','destination_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
$provenance = [ordered]@{
  schema='P126_R7A_COPY_PROVENANCE_V1';handoff_id=$handoff;operation=$operation
  source_root=[IO.Path]::GetFullPath($sourceRoot);destination_root=[IO.Path]::GetFullPath($destinationRoot)
  source_root_snapshot_sha256=$sourceSnapshotBefore.sha256;source_root_snapshot_count=$sourceSnapshotBefore.count
  copied_material_count=188;added_payload_count=2;payload_count=190;control_count=3;ordinary_count=193
  preserved_fields=@('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
  preserved_verdict=$verdict;hard_defect_ids=$hardDefects;business_evidence_rerun_count=0
  source_controls_copied_count=0;controller_invocation_count=1;retry_count=0
}
[IO.File]::WriteAllText($provenancePath,($provenance|ConvertTo-Json -Depth 7)+"`n",$utf8NoBom)

$controlNames = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')
$payloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force | Where-Object { (Get-Relative $destinationRoot $_.FullName) -notin $controlNames } | Sort-Object { Get-Relative $destinationRoot $_.FullName })
if ($payloadFiles.Count -ne 190) { throw "payload count mismatch: $($payloadFiles.Count)" }
$payloadRows = [Collections.Generic.List[object]]::new()
foreach ($file in $payloadFiles) {
  $payloadRows.Add([pscustomobject][ordered]@{
    relative_path=Get-Relative $destinationRoot $file.FullName;bytes=[long]$file.Length;sha256=Get-Sha256 $file.FullName
    creation_time_utc_ticks=[long]$file.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[long]$file.LastWriteTimeUtc.Ticks
  })
}
$payloadDuplicateGroups = @($payloadRows | Group-Object -Property { [string]$_.relative_path } -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($payloadDuplicateGroups.Count -ne 0) { throw 'payload canonical duplicates' }
$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
Write-CsvNoBom $manifestPath @($payloadRows) @('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
$sealAudit = [ordered]@{
  schema='P126_R7A_SEAL_AUDIT_V1';handoff_id=$handoff;operation=$operation;verdict=$verdict;hard_defect_ids=$hardDefects
  source_root=[IO.Path]::GetFullPath($sourceRoot);destination_root=[IO.Path]::GetFullPath($destinationRoot)
  source_snapshot_sha256=$sourceSnapshotBefore.sha256;copied_material_count=188;source_controls_copied_count=0
  payload_count=190;control_count=3;ordinary_count=193;copy_identity_rows=$copyRows.Count
  copy_set_diff_count=$copySetDiff.Count;copy_identity_mismatch_count=0;payload_duplicate_count=$payloadDuplicateGroups.Count
  copy_identity_sha256=Get-Sha256 $copyIdentityPath;copy_provenance_sha256=Get-Sha256 $provenancePath
  payload_manifest_sha256=Get-Sha256 $manifestPath;business_evidence_rerun_count=0
  controller_invocation_count=1;retry_count=0;auditor_invocation_budget=1;errors=@()
}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit|ConvertTo-Json -Depth 7)+"`n",$utf8NoBom)

$premarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
$premarkerDirs = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force | Sort-Object FullName -Descending)
if ($premarkerFiles.Count -ne 192) { throw "premarker file count mismatch: $($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { Set-Readonly $file }
foreach ($dir in $premarkerDirs) { Set-Readonly $dir }
Set-Readonly (Get-Item -LiteralPath $destinationRoot)
$writableFiles = @($premarkerFiles | Where-Object { -not (Is-Readonly (Get-Item -LiteralPath $_.FullName)) })
$allPremarkerDirs = @(@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force) + @(Get-Item -LiteralPath $destinationRoot))
$writableDirs = @($allPremarkerDirs | Where-Object { -not (Is-Readonly (Get-Item -LiteralPath $_.FullName)) })
if ($writableFiles.Count -ne 0 -or $writableDirs.Count -ne 0) { throw 'premarker readonly freeze failure' }

$allPremarkerItems = @(@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force) + @(Get-Item -LiteralPath $destinationRoot))
$maxPremarkerTicks = [long](($allPremarkerItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks)
$futureTicks = [Math]::Max($maxPremarkerTicks+[TimeSpan]::FromMinutes(10).Ticks,[DateTime]::UtcNow.AddMinutes(10).Ticks)
$markerLines = @(
  'SCHEMA=P126_R7A_WRITE_STOPPED_V1',"HANDOFF_ID=$handoff","OPERATION=$operation",'UID=FIG-P126-01','ROLE=SA2',"VERDICT=$verdict",
  "ROOT=$destinationRoot","SOURCE_ROOT=$sourceRoot",'COPIED_MATERIAL_COUNT=188','ADDED_PAYLOAD_COUNT=2','PAYLOAD_COUNT=190','CONTROL_COUNT=3','ORDINARY_COUNT=193',
  "SOURCE_ROOT_SNAPSHOT_SHA256=$($sourceSnapshotBefore.sha256)","COPY_IDENTITY_SHA256=$(Get-Sha256 $copyIdentityPath)","COPY_PROVENANCE_SHA256=$(Get-Sha256 $provenancePath)",
  "PAYLOAD_MANIFEST_SHA256=$(Get-Sha256 $manifestPath)","SEAL_AUDIT_SHA256=$(Get-Sha256 $sealAuditPath)",'BUSINESS_EVIDENCE_RERUN_COUNT=0',
  'CONTROLLER_INVOCATION_COUNT=1','RETRY_COUNT=0','AUDITOR_INVOCATION_BUDGET=1',"HARD_DEFECT_IDS=$([string]::Join(';',$hardDefects))",
  "PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))","WSTOP_LAST_WRITE_UTC_TICKS=$futureTicks"
)
$badMarkerLines = @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' })
$markerKeys = @($markerLines | ForEach-Object { ($_ -split '=',2)[0] })
$markerDuplicateKeys = @($markerKeys | Group-Object -Property { [string]$_ } -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($badMarkerLines.Count -ne 0 -or $markerDuplicateKeys.Count -ne 0 -or $markerLines.Count -ne 25) { throw 'marker syntax/key failure' }
[IO.File]::WriteAllText($stagePath,[string]::Join("`r`n",$markerLines)+"`r`n",$utf8NoBom)
$stageItem = Get-Item -LiteralPath $stagePath
$stageItem.LastWriteTimeUtc=[DateTime]::new($futureTicks,[DateTimeKind]::Utc)
Set-Readonly $stageItem
if (-not (Is-Readonly (Get-Item -LiteralPath $stagePath)) -or (Get-Item -LiteralPath $stagePath).LastWriteTimeUtc.Ticks -ne $futureTicks) { throw 'external marker preparation failure' }

$markerPath = Join-Path $destinationRoot 'WRITE_STOPPED'
Move-Item -LiteralPath $stagePath -Destination $markerPath

$sourceSnapshotAfter = Get-TreeSnapshot $sourceRoot
$destinationSnapshot1 = Get-TreeSnapshot $destinationRoot
Start-Sleep -Milliseconds 250
$destinationSnapshot2 = Get-TreeSnapshot $destinationRoot
$marker = Get-Item -LiteralPath $markerPath
$allFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
$allDirs = @(@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force) + @(Get-Item -LiteralPath $destinationRoot))
$otherItems = @(@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force | Where-Object { $_.FullName -cne $markerPath }) + @(Get-Item -LiteralPath $destinationRoot))
$maxOtherTicks = [long](($otherItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks)
$result = [ordered]@{
  schema='P126_R7A_CONTROLLER_RESULT_V1';handoff_id=$handoff;operation=$operation;verdict=$verdict
  controller_invocation_count=1;retry_count=0;exit_code=0;natural_exit=$true;start_utc=$startUtc.ToString('o');end_utc=[DateTime]::UtcNow.ToString('o')
  source_root_snapshot_before_sha256=$sourceSnapshotBefore.sha256;source_root_snapshot_after_sha256=$sourceSnapshotAfter.sha256
  destination_snapshot1_sha256=$destinationSnapshot1.sha256;destination_snapshot2_sha256=$destinationSnapshot2.sha256
  copied_material_count=188;payload_count=190;control_count=3;ordinary_count=$allFiles.Count;directory_count=$allDirs.Count
  readonly_files=@($allFiles|Where-Object{Is-Readonly $_}).Count;readonly_directories=@($allDirs|Where-Object{Is-Readonly $_}).Count
  marker_path=$markerPath;marker_bytes=[long]$marker.Length;marker_sha256=Get-Sha256 $markerPath;marker_line_count=$markerLines.Count
  marker_ticks=[long]$marker.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]$marker.LastWriteTimeUtc.Ticks-$maxOtherTicks
  copy_identity_sha256=Get-Sha256 $copyIdentityPath;copy_provenance_sha256=Get-Sha256 $provenancePath
  payload_manifest_sha256=Get-Sha256 $manifestPath;seal_audit_sha256=Get-Sha256 $sealAuditPath;postmarker_root_writes=0
}
[IO.File]::WriteAllText($resultPath,($result|ConvertTo-Json -Depth 7)+"`n",$utf8NoBom)
$result | ConvertTo-Json -Depth 7
