$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoff = 'A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R4_STATIC_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R4_SA2_STATIC_LEGEND_SEGMENT_PATCH_R115_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R4A_SA2_STATIC_LEGEND_SEGMENT_PATCH_CONTROL_RESEAL_R115_20260828'
$oldManifestPath = Join-Path $sourceRoot 'PAYLOAD_MANIFEST.csv'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4A_STATIC_WRITE_STOPPED_STAGE_V1_20260828.tmp'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4A_STATIC_CONTROL_RESEAL_CONTROLLER_RESULT_V1_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4A_STATIC_CONTROL_RESEAL_AUDIT_V1_20260828.json'
$expectedOldManifestSha = '4A80B3D2F355413061C698C91E2949B8EA803D8EF987518C0C8C00F498C6071C'
$expectedSourceBytes = 4356L
$expectedSourceSha = '3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75'
$expectedCopied = 6
$expectedPayload = 8
$expectedControls = 3
$expectedOrdinary = 11
$expectedMarkerKeys = @(
  'SCHEMA','HANDOFF_ID','OPERATION','UID','ROLE','VERDICT','SOURCE_ROOT','DESTINATION_ROOT',
  'OLD_MANIFEST_SHA256','SOURCE_ROOT_SNAPSHOT_SHA256','COPIED_MATERIAL_COUNT','OLD_CONTROLS_COPIED',
  'ADDED_PAYLOAD_COUNT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','COPY_IDENTITY_SHA256',
  'COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','BUSINESS_EVIDENCE_RERUN',
  'CONTROLLER_INVOCATION_COUNT','CONTROLLER_RETRY_COUNT','AUDITOR_INVOCATION_BUDGET'
)
$utf8NoBom = [Text.UTF8Encoding]::new($false)

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

function Add-Error([Collections.Generic.List[string]]$Errors, [string]$Text) {
  $Errors.Add($Text)
}

if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { throw 'source root missing' }
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) { throw 'destination root missing' }
if (-not (Test-Path -LiteralPath $controllerResultPath -PathType Leaf)) { throw 'controller result missing' }
if (Test-Path -LiteralPath $auditResultPath) { throw 'auditor result already exists' }
if (Test-Path -LiteralPath $stagePath) { throw 'stage remains present' }

$errors = [Collections.Generic.List[string]]::new()
$sourceSnapshotBeforeAudit = Get-TreeSnapshot $sourceRoot
$destinationSnapshotBeforeAudit = Get-TreeSnapshot $destinationRoot
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw -Encoding utf8 | ConvertFrom-Json
$oldRows = @(Import-Csv -LiteralPath $oldManifestPath)
$copyIdentityPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
$markerPath = Join-Path $destinationRoot 'WRITE_STOPPED'
$copyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
$provenance = Get-Content -LiteralPath $provenancePath -Raw -Encoding utf8 | ConvertFrom-Json
$sealAudit = Get-Content -LiteralPath $sealAuditPath -Raw -Encoding utf8 | ConvertFrom-Json

if ((Get-Sha256 $oldManifestPath) -cne $expectedOldManifestSha) { Add-Error $errors 'old manifest SHA mismatch' }
if ($oldRows.Count -ne $expectedCopied -or $copyRows.Count -ne $expectedCopied) { Add-Error $errors 'old/copy row count mismatch' }
$oldDictionary = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
$copyDictionary = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($row in $oldRows) {
  $resolved = Resolve-CanonicalMaterialPath $sourceRoot ([string]$row.relative_path)
  if ($oldDictionary.ContainsKey($resolved.canonical)) { Add-Error $errors "old duplicate: $($resolved.canonical)" } else { $oldDictionary.Add($resolved.canonical, $row) }
}
foreach ($row in $copyRows) {
  $resolved = Resolve-CanonicalMaterialPath $destinationRoot ([string]$row.relative_path)
  if ($copyDictionary.ContainsKey($resolved.canonical)) { Add-Error $errors "copy duplicate: $($resolved.canonical)" } else { $copyDictionary.Add($resolved.canonical, $row) }
}
if (@(Compare-Object -ReferenceObject @($oldDictionary.Keys) -DifferenceObject @($copyDictionary.Keys) -CaseSensitive).Count -ne 0) { Add-Error $errors 'old-to-copy path set mismatch' }
foreach ($pathKey in @($oldDictionary.Keys)) {
  if (-not $copyDictionary.ContainsKey($pathKey)) { continue }
  $old = $oldDictionary[$pathKey]
  $copy = $copyDictionary[$pathKey]
  foreach ($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')) {
    if ([string]$old.$field -cne [string]$copy.$field) { Add-Error $errors "old-to-copy field mismatch $pathKey $field" }
  }
  $sourceResolved = Resolve-CanonicalMaterialPath $sourceRoot $pathKey
  $destinationResolved = Resolve-CanonicalMaterialPath $destinationRoot $pathKey
  if ([string]$copy.source_path -cne $sourceResolved.resolved -or [string]$copy.destination_path -cne $destinationResolved.resolved) { Add-Error $errors "copy resolved path mismatch $pathKey" }
  foreach ($pair in @(@($sourceResolved.resolved,$old), @($destinationResolved.resolved,$old))) {
    $item = Get-Item -LiteralPath $pair[0]
    $expected = $pair[1]
    if ($item.Length -ne [long]$expected.bytes -or (Get-Sha256 $pair[0]) -cne ([string]$expected.sha256).ToUpperInvariant() -or $item.CreationTimeUtc.Ticks -ne [long]$expected.creation_time_utc_ticks -or $item.LastWriteTimeUtc.Ticks -ne [long]$expected.last_write_time_utc_ticks) { Add-Error $errors "actual identity mismatch $pathKey" }
  }
}

$controlNames = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')
$actualFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
$actualDirs = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force)
$actualPayloadFiles = @($actualFiles | Where-Object { $controlNames -cnotcontains ([IO.Path]::GetRelativePath($destinationRoot,$_.FullName) -replace '\\','/') })
if ($manifestRows.Count -ne $expectedPayload -or $actualPayloadFiles.Count -ne $expectedPayload) { Add-Error $errors 'payload/manifest count mismatch' }
$manifestDictionary = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach ($row in $manifestRows) {
  $resolved = Resolve-CanonicalMaterialPath $destinationRoot ([string]$row.relative_path)
  if ($manifestDictionary.ContainsKey($resolved.canonical)) { Add-Error $errors "manifest duplicate: $($resolved.canonical)" } else { $manifestDictionary.Add($resolved.canonical,$row) }
}
$actualPayloadKeys = @($actualPayloadFiles | ForEach-Object { (Resolve-CanonicalMaterialPath $destinationRoot ([IO.Path]::GetRelativePath($destinationRoot,$_.FullName))).canonical })
if (@(Compare-Object -ReferenceObject @($manifestDictionary.Keys) -DifferenceObject $actualPayloadKeys -CaseSensitive).Count -ne 0) { Add-Error $errors 'manifest-to-FS payload set mismatch' }
foreach ($key in @($manifestDictionary.Keys)) {
  $row = $manifestDictionary[$key]
  $resolved = Resolve-CanonicalMaterialPath $destinationRoot $key
  $item = Get-Item -LiteralPath $resolved.resolved
  if ($item.Length -ne [long]$row.bytes -or (Get-Sha256 $resolved.resolved) -cne ([string]$row.sha256).ToUpperInvariant() -or $item.CreationTimeUtc.Ticks -ne [long]$row.creation_time_utc_ticks -or $item.LastWriteTimeUtc.Ticks -ne [long]$row.last_write_time_utc_ticks) { Add-Error $errors "manifest identity mismatch $key" }
}

$expectedProvenance = [ordered]@{
  schema='P126_R4A_STATIC_COPY_PROVENANCE_V1'; handoff_id=$handoff; operation=$operation;
  source_root=$sourceRoot; destination_root=$destinationRoot; old_manifest_path=$oldManifestPath;
  old_manifest_sha256=$expectedOldManifestSha; source_root_snapshot_sha256=[string]$controllerResult.source_root_snapshot_before_sha256;
  copied_material_count=$expectedCopied; old_controls_copied=0; added_payload_count=2; payload_count=$expectedPayload;
  verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS'; source_bytes=$expectedSourceBytes; source_sha256=$expectedSourceSha; business_evidence_rerun=0
}
foreach ($key in $expectedProvenance.Keys) {
  $property = @($provenance.PSObject.Properties | Where-Object { $_.Name -ceq $key })
  if ($property.Count -ne 1 -or [string]$property[0].Value -cne [string]$expectedProvenance[$key]) { Add-Error $errors "provenance mismatch $key" }
}
if (@($provenance.preserved_fields).Count -ne 5 -or @(Compare-Object -ReferenceObject @('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks') -DifferenceObject @($provenance.preserved_fields) -CaseSensitive).Count -ne 0) { Add-Error $errors 'provenance preserved fields mismatch' }

$copySha = Get-Sha256 $copyIdentityPath
$provenanceSha = Get-Sha256 $provenancePath
$manifestSha = Get-Sha256 $manifestPath
$sealAuditSha = Get-Sha256 $sealAuditPath
$expectedSealAudit = [ordered]@{
  schema='P126_R4A_STATIC_SEAL_AUDIT_V1'; handoff_id=$handoff; operation=$operation; verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';
  copied_material_count=$expectedCopied; old_controls_copied=0; added_payload_count=2; payload_count=$expectedPayload; control_count=$expectedControls; ordinary_count=$expectedOrdinary;
  old_manifest_sha256=$expectedOldManifestSha; copy_identity_sha256=$copySha; copy_provenance_sha256=$provenanceSha; payload_manifest_sha256=$manifestSha;
  source_root_snapshot_sha256=[string]$controllerResult.source_root_snapshot_before_sha256; source_bytes=$expectedSourceBytes; source_sha256=$expectedSourceSha; business_evidence_rerun=0
}
foreach ($key in $expectedSealAudit.Keys) {
  $property = @($sealAudit.PSObject.Properties | Where-Object { $_.Name -ceq $key })
  if ($property.Count -ne 1 -or [string]$property[0].Value -cne [string]$expectedSealAudit[$key]) { Add-Error $errors "seal audit mismatch $key" }
}
if ($null -ne $sealAudit.errors -and @($sealAudit.errors | Where-Object { $null -ne $_ }).Count -ne 0) { Add-Error $errors 'seal audit errors nonempty' }

$markerBytes = [IO.File]::ReadAllBytes($markerPath)
$markerText = $utf8NoBom.GetString($markerBytes)
$markerLines = @($markerText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
$markerDictionary = [Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
if ($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF) { Add-Error $errors 'marker BOM present' }
if ($markerText.Contains("`t")) { Add-Error $errors 'marker TAB present' }
foreach ($line in $markerLines) {
  if ($line -notmatch '^[A-Z0-9_]+=[^=].*$') { Add-Error $errors "marker bad line: $line"; continue }
  $parts = $line -split '=',2
  if ($markerDictionary.ContainsKey($parts[0])) { Add-Error $errors "marker duplicate key: $($parts[0])" } else { $markerDictionary.Add($parts[0],$parts[1]) }
}
if (@(Compare-Object -ReferenceObject $expectedMarkerKeys -DifferenceObject @($markerDictionary.Keys) -CaseSensitive).Count -ne 0) { Add-Error $errors 'marker exact key set mismatch' }
$expectedMarker = [ordered]@{
  SCHEMA='P126_R4A_STATIC_WRITE_STOPPED_V1'; HANDOFF_ID=$handoff; OPERATION=$operation; UID='FIG-P126-01'; ROLE='SA2'; VERDICT='STATIC_ONLY_NOT_RENDERED_NOT_PASS';
  SOURCE_ROOT=$sourceRoot; DESTINATION_ROOT=$destinationRoot; OLD_MANIFEST_SHA256=$expectedOldManifestSha; SOURCE_ROOT_SNAPSHOT_SHA256=[string]$controllerResult.source_root_snapshot_before_sha256;
  COPIED_MATERIAL_COUNT='6'; OLD_CONTROLS_COPIED='0'; ADDED_PAYLOAD_COUNT='2'; PAYLOAD_COUNT='8'; CONTROL_COUNT='3'; ORDINARY_COUNT='11';
  COPY_IDENTITY_SHA256=$copySha; COPY_PROVENANCE_SHA256=$provenanceSha; PAYLOAD_MANIFEST_SHA256=$manifestSha; SEAL_AUDIT_SHA256=$sealAuditSha;
  BUSINESS_EVIDENCE_RERUN='0'; CONTROLLER_INVOCATION_COUNT='1'; CONTROLLER_RETRY_COUNT='0'; AUDITOR_INVOCATION_BUDGET='1'
}
foreach ($key in $expectedMarker.Keys) {
  if (-not $markerDictionary.ContainsKey($key) -or $markerDictionary[$key] -cne [string]$expectedMarker[$key]) { Add-Error $errors "marker value mismatch $key" }
}

$expectedController = [ordered]@{
  schema='P126_R4A_STATIC_CONTROLLER_RESULT_V1'; handoff_id=$handoff; operation=$operation; verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';
  invocation_count=1; retry_count=0; exit_code=0; natural_exit=$true; source_root=$sourceRoot; destination_root=$destinationRoot;
  copied_material_count=$expectedCopied; old_controls_copied=0; added_payload_count=2; payload_count=$expectedPayload; control_count=$expectedControls; ordinary_count=$expectedOrdinary;
  old_manifest_sha256=$expectedOldManifestSha; copy_identity_sha256=$copySha; copy_provenance_sha256=$provenanceSha; payload_manifest_sha256=$manifestSha; seal_audit_sha256=$sealAuditSha;
  marker_sha256=(Get-Sha256 $markerPath); marker_last_write_utc_ticks=(Get-Item -LiteralPath $markerPath).LastWriteTimeUtc.Ticks; marker_physical_lines=$expectedMarkerKeys.Count;
  source_root_snapshot_before_sha256=$sourceSnapshotBeforeAudit; source_root_snapshot_after_sha256=$sourceSnapshotBeforeAudit; destination_postmarker_snapshot_sha256=$destinationSnapshotBeforeAudit;
  business_evidence_rerun=0
}
foreach ($key in $expectedController.Keys) {
  $property = @($controllerResult.PSObject.Properties | Where-Object { $_.Name -ceq $key })
  if ($property.Count -ne 1 -or [string]$property[0].Value -cne [string]$expectedController[$key]) { Add-Error $errors "controller result mismatch $key" }
}
if ($null -ne $controllerResult.errors -and @($controllerResult.errors | Where-Object { $null -ne $_ }).Count -ne 0) { Add-Error $errors 'controller errors nonempty' }
$startParsed = [DateTime]::MinValue
$endParsed = [DateTime]::MinValue
if (-not [DateTime]::TryParse([string]$controllerResult.start_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$startParsed)) { Add-Error $errors 'controller start UTC invalid' }
if (-not [DateTime]::TryParse([string]$controllerResult.end_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$endParsed)) { Add-Error $errors 'controller end UTC invalid' }
if ($endParsed -lt $startParsed) { Add-Error $errors 'controller UTC order invalid' }

if ($actualFiles.Count -ne $expectedOrdinary) { Add-Error $errors 'ordinary count mismatch' }
if (@($actualFiles | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count -ne 0) { Add-Error $errors 'writable file found' }
if (@($actualDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 }).Count -ne 0) { Add-Error $errors 'writable directory found' }
$markerItem = Get-Item -LiteralPath $markerPath
$nonMarkerItems = @($actualFiles | Where-Object { $_.FullName -cne $markerPath }) + $actualDirs
$maxNonMarkerTicks = (@($nonMarkerItems) | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$atOrAfter = @($nonMarkerItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count
if ([long]$maxNonMarkerTicks -ge $markerItem.LastWriteTimeUtc.Ticks -or $atOrAfter -ne 0) { Add-Error $errors 'marker strict-latest gate failed' }

$csvCount = 0; $csvFailures = 0; $jsonCount = 0; $jsonFailures = 0; $adsCount = 0
foreach ($file in $actualFiles) {
  if ($file.Extension -ieq '.csv') { $csvCount++; try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvFailures++ } }
  if ($file.Extension -ieq '.json') { $jsonCount++; try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding utf8 | ConvertFrom-Json } catch { $jsonFailures++ } }
  $adsCount += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop | Where-Object { $_.Stream -ne ':$DATA' }).Count
}
$cachePycCount = @($actualFiles | Where-Object { ([IO.Path]::GetRelativePath($destinationRoot,$_.FullName) -replace '\\','/') -match '(?i)(^|/)(__pycache__|\.pytest_cache|\.mypy_cache)(/|$)|\.(pyc|pyo)$' }).Count
$reparseCount = @(@($actualFiles + $actualDirs) | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($csvFailures -ne 0 -or $jsonFailures -ne 0 -or $adsCount -ne 0 -or $cachePycCount -ne 0 -or $reparseCount -ne 0) { Add-Error $errors 'parse or hygiene failure' }
if (Test-Path -LiteralPath $stagePath) { Add-Error $errors 'stage present after marker' }

$sourceSnapshotAfterAudit = Get-TreeSnapshot $sourceRoot
$destinationSnapshotAfterAudit = Get-TreeSnapshot $destinationRoot
if ($sourceSnapshotBeforeAudit -cne $sourceSnapshotAfterAudit) { Add-Error $errors 'source root changed during audit' }
if ($destinationSnapshotBeforeAudit -cne $destinationSnapshotAfterAudit) { Add-Error $errors 'postmarker destination mutation' }

$result = [ordered]@{
  schema='P126_R4A_STATIC_AUDIT_RESULT_V1'; handoff_id=$handoff; operation=$operation; verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';
  invocation_count=1; retry_count=0; copied_material_count=$expectedCopied; old_controls_copied=0; payload_count=$expectedPayload; control_count=$expectedControls; ordinary_count=$actualFiles.Count;
  directory_count_including_root=$actualDirs.Count; readonly_files=@($actualFiles | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0 }).Count;
  readonly_dirs=@($actualDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0 }).Count;
  old_manifest_sha256=$expectedOldManifestSha; copy_identity_sha256=$copySha; copy_provenance_sha256=$provenanceSha; payload_manifest_sha256=$manifestSha; seal_audit_sha256=$sealAuditSha;
  marker_sha256=Get-Sha256 $markerPath; marker_physical_lines=$markerLines.Count; marker_unique_keys=$markerDictionary.Count; marker_last_write_utc_ticks=$markerItem.LastWriteTimeUtc.Ticks;
  strict_latest_margin_ticks=$markerItem.LastWriteTimeUtc.Ticks-[long]$maxNonMarkerTicks; at_or_after_excluding_marker=$atOrAfter;
  source_root_snapshot_sha256=$sourceSnapshotAfterAudit; destination_postmarker_snapshot_sha256=$destinationSnapshotAfterAudit; postmarker_content_attribute_writes=if($destinationSnapshotBeforeAudit -ceq $destinationSnapshotAfterAudit){0}else{1};
  csv_file_count=$csvCount; csv_parse_failures=$csvFailures; json_file_count=$jsonCount; json_parse_failures=$jsonFailures; ads_count=$adsCount; cache_pyc_count=$cachePycCount; reparse_count=$reparseCount;
  stage_absent=(-not (Test-Path -LiteralPath $stagePath)); business_evidence_rerun=0; errors=@($errors); hard_gate=($errors.Count -eq 0); audited_utc=[DateTime]::UtcNow.ToString('o')
}
[IO.File]::WriteAllText($auditResultPath, ($result | ConvertTo-Json -Depth 8) + "`n", $utf8NoBom)
$resultAttributes = [IO.File]::GetAttributes($auditResultPath)
[IO.File]::SetAttributes($auditResultPath, ($resultAttributes -bor [IO.FileAttributes]::ReadOnly))
if ($errors.Count -ne 0) { throw ($errors -join '; ') }
$result | ConvertTo-Json -Depth 8
