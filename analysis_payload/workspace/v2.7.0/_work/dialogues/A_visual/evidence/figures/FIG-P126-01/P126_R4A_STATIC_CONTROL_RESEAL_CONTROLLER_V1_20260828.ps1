$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoff = 'A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R4_STATIC_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R4_SA2_STATIC_LEGEND_SEGMENT_PATCH_R115_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R4A_SA2_STATIC_LEGEND_SEGMENT_PATCH_CONTROL_RESEAL_R115_20260828'
$oldManifestPath = Join-Path $sourceRoot 'PAYLOAD_MANIFEST.csv'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4A_STATIC_WRITE_STOPPED_STAGE_V1_20260828.tmp'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4A_STATIC_CONTROL_RESEAL_CONTROLLER_RESULT_V1_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4A_STATIC_CONTROL_RESEAL_AUDIT_V1_20260828.json'
$expectedOldManifestSha = '4A80B3D2F355413061C698C91E2949B8EA803D8EF987518C0C8C00F498C6071C'
$expectedSourceBytes = 4356L
$expectedSourceSha = '3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75'
$expectedCopied = 6
$expectedPayload = 8
$expectedControls = 3
$expectedOrdinary = 11
$utf8NoBom = [Text.UTF8Encoding]::new($false)
$startUtc = [DateTime]::UtcNow

function Get-Sha256([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Resolve-CanonicalMaterialPath([string]$Base, [string]$InputPath) {
  if ([string]::IsNullOrWhiteSpace($InputPath)) { throw 'empty relative path' }
  $canonical = (($InputPath -replace '\\', '/') -replace '^(\./)+', '')
  if ([string]::IsNullOrWhiteSpace($canonical)) { throw 'empty canonical path' }
  if ($canonical.StartsWith('/') -or $canonical.StartsWith('//') -or $canonical -match '^[A-Za-z]:' -or [IO.Path]::IsPathRooted($canonical)) { throw "rooted path rejected: $InputPath" }
  $segments = @($canonical -split '/')
  if ($segments.Count -eq 0 -or @($segments | Where-Object { [string]::IsNullOrEmpty($_) -or $_ -ceq '.' -or $_ -ceq '..' }).Count -ne 0) { throw "unsafe segment rejected: $InputPath" }
  $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd('\', '/')
  $resolved = [IO.Path]::GetFullPath([IO.Path]::Combine($baseFull, ($segments -join [IO.Path]::DirectorySeparatorChar)))
  $prefix = $baseFull + [IO.Path]::DirectorySeparatorChar
  if (-not $resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw "containment rejected: $InputPath" }
  return [pscustomobject]@{ canonical = $canonical; resolved = $resolved }
}

function Get-TreeSnapshot([string]$Base) {
  $rows = [Collections.Generic.List[string]]::new()
  $rootItem = Get-Item -LiteralPath $Base -Force
  $rows.Add(('D<TAB>.<TAB>{0}<TAB>{1}<TAB>{2}' -f $rootItem.CreationTimeUtc.Ticks, $rootItem.LastWriteTimeUtc.Ticks, [int]$rootItem.Attributes).Replace('<TAB>', "`t"))
  foreach ($dir in @(Get-ChildItem -LiteralPath $Base -Directory -Recurse -Force | Sort-Object FullName)) {
    $relative = [IO.Path]::GetRelativePath($Base, $dir.FullName) -replace '\\', '/'
    $rows.Add(('D<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}' -f $relative, $dir.CreationTimeUtc.Ticks, $dir.LastWriteTimeUtc.Ticks, [int]$dir.Attributes).Replace('<TAB>', "`t"))
  }
  foreach ($file in @(Get-ChildItem -LiteralPath $Base -File -Recurse -Force | Sort-Object FullName)) {
    $relative = [IO.Path]::GetRelativePath($Base, $file.FullName) -replace '\\', '/'
    $rows.Add(('F<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}<TAB>{4}<TAB>{5}' -f $relative, $file.Length, (Get-Sha256 $file.FullName), $file.CreationTimeUtc.Ticks, $file.LastWriteTimeUtc.Ticks, [int]$file.Attributes).Replace('<TAB>', "`t"))
  }
  $bytes = $utf8NoBom.GetBytes(($rows -join "`n") + "`n")
  return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function Set-ReadOnlyBit([string]$Path) {
  $attributes = [IO.File]::GetAttributes($Path)
  [IO.File]::SetAttributes($Path, ($attributes -bor [IO.FileAttributes]::ReadOnly))
}

foreach ($path in @($destinationRoot, $stagePath, $resultPath, $auditResultPath)) {
  if (Test-Path -LiteralPath $path) { throw "startup absence failed: $path" }
}
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { throw 'source root missing' }
if ((Get-Sha256 $oldManifestPath) -cne $expectedOldManifestSha) { throw 'old manifest SHA mismatch' }
$sourceSnapshotBefore = Get-TreeSnapshot $sourceRoot

$oldRows = @(Import-Csv -LiteralPath $oldManifestPath)
if ($oldRows.Count -ne $expectedCopied) { throw 'old manifest row count mismatch' }
$requiredFields = @('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
$resolvedOldRows = [Collections.Generic.List[object]]::new()
foreach ($row in $oldRows) {
  foreach ($field in $requiredFields) {
    $property = @($row.PSObject.Properties | Where-Object { $_.Name -ceq $field })
    if ($property.Count -ne 1 -or [string]::IsNullOrWhiteSpace([string]$property[0].Value)) { throw "old manifest field invalid: $field" }
  }
  $resolved = Resolve-CanonicalMaterialPath $sourceRoot ([string]$row.relative_path)
  $resolvedOldRows.Add([pscustomobject][ordered]@{
    relative_path = $resolved.canonical
    source_path = $resolved.resolved
    bytes = [long]$row.bytes
    sha256 = ([string]$row.sha256).ToUpperInvariant()
    creation_time_utc_ticks = [long]$row.creation_time_utc_ticks
    last_write_time_utc_ticks = [long]$row.last_write_time_utc_ticks
  })
}
if (@($resolvedOldRows | Group-Object -Property relative_path -CaseSensitive | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'canonical duplicate path' }

[IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
$copyRows = [Collections.Generic.List[object]]::new()
foreach ($row in $resolvedOldRows) {
  $destination = Resolve-CanonicalMaterialPath $destinationRoot $row.relative_path
  $destinationDirectory = [IO.Path]::GetDirectoryName($destination.resolved)
  [IO.Directory]::CreateDirectory($destinationDirectory) | Out-Null
  [IO.File]::Copy($row.source_path, $destination.resolved, $false)
  [IO.File]::SetAttributes($destination.resolved, [IO.FileAttributes]::Normal)
  [IO.File]::SetCreationTimeUtc($destination.resolved, [DateTime]::new($row.creation_time_utc_ticks, [DateTimeKind]::Utc))
  [IO.File]::SetLastWriteTimeUtc($destination.resolved, [DateTime]::new($row.last_write_time_utc_ticks, [DateTimeKind]::Utc))
  $sourceItem = Get-Item -LiteralPath $row.source_path
  $destinationItem = Get-Item -LiteralPath $destination.resolved
  if ($sourceItem.Length -ne $row.bytes -or $destinationItem.Length -ne $row.bytes) { throw "copy bytes mismatch: $($row.relative_path)" }
  if ((Get-Sha256 $row.source_path) -cne $row.sha256 -or (Get-Sha256 $destination.resolved) -cne $row.sha256) { throw "copy SHA mismatch: $($row.relative_path)" }
  if ($destinationItem.CreationTimeUtc.Ticks -ne $row.creation_time_utc_ticks -or $destinationItem.LastWriteTimeUtc.Ticks -ne $row.last_write_time_utc_ticks) { throw "copy FILETIME mismatch: $($row.relative_path)" }
  $copyRows.Add([pscustomobject][ordered]@{
    relative_path = $row.relative_path
    source_path = $row.source_path
    destination_path = $destination.resolved
    bytes = $row.bytes
    sha256 = $row.sha256
    creation_time_utc_ticks = $row.creation_time_utc_ticks
    last_write_time_utc_ticks = $row.last_write_time_utc_ticks
  })
}

$copyIdentityPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM
$copyIdentitySha = Get-Sha256 $copyIdentityPath
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$provenance = [ordered]@{
  schema = 'P126_R4A_STATIC_COPY_PROVENANCE_V1'
  handoff_id = $handoff
  operation = $operation
  source_root = $sourceRoot
  destination_root = $destinationRoot
  old_manifest_path = $oldManifestPath
  old_manifest_sha256 = $expectedOldManifestSha
  source_root_snapshot_sha256 = $sourceSnapshotBefore
  copied_material_count = $expectedCopied
  old_controls_copied = 0
  added_payload_count = 2
  payload_count = $expectedPayload
  preserved_fields = @('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
  verdict = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  source_bytes = $expectedSourceBytes
  source_sha256 = $expectedSourceSha
  business_evidence_rerun = 0
}
[IO.File]::WriteAllText($provenancePath, ($provenance | ConvertTo-Json -Depth 7) + "`n", $utf8NoBom)
$provenanceSha = Get-Sha256 $provenancePath

$payloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
if ($payloadFiles.Count -ne $expectedPayload) { throw 'payload count mismatch' }
$manifestRows = [Collections.Generic.List[object]]::new()
foreach ($file in @($payloadFiles | Sort-Object FullName)) {
  $relative = Resolve-CanonicalMaterialPath $destinationRoot ([IO.Path]::GetRelativePath($destinationRoot, $file.FullName))
  $manifestRows.Add([pscustomobject][ordered]@{
    relative_path = $relative.canonical
    bytes = [long]$file.Length
    sha256 = Get-Sha256 $file.FullName
    creation_time_utc_ticks = [long]$file.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [long]$file.LastWriteTimeUtc.Ticks
  })
}
$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$manifestRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8NoBOM
$manifestSha = Get-Sha256 $manifestPath
$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
$sealAudit = [ordered]@{
  schema = 'P126_R4A_STATIC_SEAL_AUDIT_V1'
  handoff_id = $handoff
  operation = $operation
  verdict = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  copied_material_count = $expectedCopied
  old_controls_copied = 0
  added_payload_count = 2
  payload_count = $expectedPayload
  control_count = $expectedControls
  ordinary_count = $expectedOrdinary
  old_manifest_sha256 = $expectedOldManifestSha
  copy_identity_sha256 = $copyIdentitySha
  copy_provenance_sha256 = $provenanceSha
  payload_manifest_sha256 = $manifestSha
  source_root_snapshot_sha256 = $sourceSnapshotBefore
  source_bytes = $expectedSourceBytes
  source_sha256 = $expectedSourceSha
  business_evidence_rerun = 0
  errors = @()
}
[IO.File]::WriteAllText($sealAuditPath, ($sealAudit | ConvertTo-Json -Depth 7) + "`n", $utf8NoBom)
$sealAuditSha = Get-Sha256 $sealAuditPath

$premarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
$premarkerDirs = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force)
if ($premarkerFiles.Count -ne ($expectedOrdinary - 1)) { throw 'premarker ordinary count mismatch' }
foreach ($file in $premarkerFiles) { Set-ReadOnlyBit $file.FullName }
foreach ($dir in @($premarkerDirs | Sort-Object FullName -Descending)) { Set-ReadOnlyBit $dir.FullName }
if (@(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count -ne 0) { throw 'premarker writable file' }
if (@($premarkerDirs | Where-Object { ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count -ne 0) { throw 'premarker writable directory' }

$maxPremarkerTicks = (@($premarkerFiles + $premarkerDirs) | ForEach-Object { (Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks, [long]$maxPremarkerTicks + 3000000000L)
$markerLines = @(
  'SCHEMA=P126_R4A_STATIC_WRITE_STOPPED_V1',
  "HANDOFF_ID=$handoff",
  "OPERATION=$operation",
  'UID=FIG-P126-01',
  'ROLE=SA2',
  'VERDICT=STATIC_ONLY_NOT_RENDERED_NOT_PASS',
  "SOURCE_ROOT=$sourceRoot",
  "DESTINATION_ROOT=$destinationRoot",
  "OLD_MANIFEST_SHA256=$expectedOldManifestSha",
  "SOURCE_ROOT_SNAPSHOT_SHA256=$sourceSnapshotBefore",
  "COPIED_MATERIAL_COUNT=$expectedCopied",
  'OLD_CONTROLS_COPIED=0',
  'ADDED_PAYLOAD_COUNT=2',
  "PAYLOAD_COUNT=$expectedPayload",
  "CONTROL_COUNT=$expectedControls",
  "ORDINARY_COUNT=$expectedOrdinary",
  "COPY_IDENTITY_SHA256=$copyIdentitySha",
  "COPY_PROVENANCE_SHA256=$provenanceSha",
  "PAYLOAD_MANIFEST_SHA256=$manifestSha",
  "SEAL_AUDIT_SHA256=$sealAuditSha",
  'BUSINESS_EVIDENCE_RERUN=0',
  'CONTROLLER_INVOCATION_COUNT=1',
  'CONTROLLER_RETRY_COUNT=0',
  'AUDITOR_INVOCATION_BUDGET=1'
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=].*$' }).Count -ne 0) { throw 'marker syntax invalid' }
if (@($markerLines | ForEach-Object { ($_ -split '=',2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'marker duplicate key' }
[IO.File]::WriteAllText($stagePath, ($markerLines -join "`n") + "`n", $utf8NoBom)
[IO.File]::SetLastWriteTimeUtc($stagePath, [DateTime]::new($futureTicks, [DateTimeKind]::Utc))
Set-ReadOnlyBit $stagePath
$markerShaBeforeMove = Get-Sha256 $stagePath
$markerTicksBeforeMove = (Get-Item -LiteralPath $stagePath).LastWriteTimeUtc.Ticks
Move-Item -LiteralPath $stagePath -Destination (Join-Path $destinationRoot 'WRITE_STOPPED') -ErrorAction Stop

$destinationSnapshotAfter = Get-TreeSnapshot $destinationRoot
$sourceSnapshotAfter = Get-TreeSnapshot $sourceRoot
$endUtc = [DateTime]::UtcNow
$result = [ordered]@{
  schema = 'P126_R4A_STATIC_CONTROLLER_RESULT_V1'
  handoff_id = $handoff
  operation = $operation
  verdict = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  invocation_count = 1
  retry_count = 0
  exit_code = 0
  natural_exit = $true
  start_utc = $startUtc.ToString('o')
  end_utc = $endUtc.ToString('o')
  source_root = $sourceRoot
  destination_root = $destinationRoot
  copied_material_count = $expectedCopied
  old_controls_copied = 0
  added_payload_count = 2
  payload_count = $expectedPayload
  control_count = $expectedControls
  ordinary_count = $expectedOrdinary
  old_manifest_sha256 = $expectedOldManifestSha
  copy_identity_sha256 = $copyIdentitySha
  copy_provenance_sha256 = $provenanceSha
  payload_manifest_sha256 = $manifestSha
  seal_audit_sha256 = $sealAuditSha
  marker_sha256 = $markerShaBeforeMove
  marker_last_write_utc_ticks = $markerTicksBeforeMove
  marker_physical_lines = $markerLines.Count
  source_root_snapshot_before_sha256 = $sourceSnapshotBefore
  source_root_snapshot_after_sha256 = $sourceSnapshotAfter
  destination_postmarker_snapshot_sha256 = $destinationSnapshotAfter
  business_evidence_rerun = 0
  errors = @()
}
[IO.File]::WriteAllText($resultPath, ($result | ConvertTo-Json -Depth 8) + "`n", $utf8NoBom)
Set-ReadOnlyBit $resultPath
$result | ConvertTo-Json -Depth 8
