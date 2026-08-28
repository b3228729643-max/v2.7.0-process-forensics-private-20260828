$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoffId = 'A-R115-P126-SA2-DIRECT-BUILD-R3A-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R3A_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$preservedVerdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
$hardDefectId = 'HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3B_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$oldManifestPath = Join-Path $sourceRoot 'PAYLOAD_MANIFEST.csv'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_WRITE_STOPPED_STAGE_V2_20260828.tmp'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_CONTROL_RESEAL_CONTROLLER_RESULT_V2_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_CONTROL_RESEAL_AUDIT_V2_20260828.json'
$oldControlNames = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$expectedOldManifestSha = '405541B02D962FD75161DAEBB41C067955D7B99B992DD1F14A7399D3A6EB0D7E'
$requiredOldFields = @('relative_path', 'bytes', 'sha256', 'creation_time_utc_ticks', 'last_write_time_utc_ticks')

function Get-CanonicalRelative([string]$Value) {
    if ([string]::IsNullOrWhiteSpace($Value)) { throw 'relative path is empty' }
    $candidate = $Value.Replace('\', '/')
    $candidate = $candidate -replace '^(?:\./)+', ''
    if ([string]::IsNullOrWhiteSpace($candidate)) { throw 'relative path is empty after normalization' }
    if ([IO.Path]::IsPathRooted($candidate) -or $candidate -match '^[A-Za-z]:/' -or $candidate.StartsWith('/') -or $candidate.StartsWith('//')) {
        throw "rooted or absolute relative path rejected: $Value"
    }
    $segments = @($candidate.Split('/', [StringSplitOptions]::None))
    if ($segments.Count -eq 0) { throw "relative path has no segments: $Value" }
    foreach ($segment in $segments) {
        if ([string]::IsNullOrEmpty($segment) -or $segment -eq '.' -or $segment -eq '..') {
            throw "empty dot or parent segment rejected: $Value"
        }
    }
    return $segments -join '/'
}

function Resolve-UnderRoot([string]$Base, [string]$Relative) {
    $canonical = Get-CanonicalRelative $Relative
    $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar)
    $full = [IO.Path]::GetFullPath((Join-Path $baseFull $canonical.Replace('/', [IO.Path]::DirectorySeparatorChar)))
    $prefix = $baseFull + [IO.Path]::DirectorySeparatorChar
    if (-not $full.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "relative path escapes root: $Relative"
    }
    return $full
}

function Get-RelativePath([string]$Base, [string]$FullName) {
    return Get-CanonicalRelative ([IO.Path]::GetRelativePath($Base, $FullName))
}

function Get-FileSha([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-MaxLastWriteTicks([object[]]$Items) {
    $ticks = @($Items | ForEach-Object { [int64]$_.LastWriteTimeUtc.Ticks })
    if ($ticks.Count -eq 0) { throw 'cannot compute maximum ticks from an empty item set' }
    return [int64]($ticks | Sort-Object -Descending | Select-Object -First 1)
}

function Get-TreeSnapshot([string]$Base) {
    $rows = [System.Collections.Generic.List[string]]::new()
    $rootItem = Get-Item -LiteralPath $Base -Force
    $rows.Add(('D<TAB>.<TAB>{0}<TAB>{1}<TAB>{2}' -f $rootItem.CreationTimeUtc.Ticks, $rootItem.LastWriteTimeUtc.Ticks, [int]$rootItem.Attributes))
    foreach ($directory in @(Get-ChildItem -LiteralPath $Base -Directory -Recurse -Force)) {
        $relative = Get-RelativePath $Base $directory.FullName
        $rows.Add(('D<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}' -f $relative, $directory.CreationTimeUtc.Ticks, $directory.LastWriteTimeUtc.Ticks, [int]$directory.Attributes))
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Base -File -Recurse -Force)) {
        $relative = Get-RelativePath $Base $file.FullName
        $rows.Add(('F<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}<TAB>{4}<TAB>{5}' -f $relative, $file.Length, (Get-FileSha $file.FullName), $file.CreationTimeUtc.Ticks, $file.LastWriteTimeUtc.Ticks, [int]$file.Attributes))
    }
    $array = $rows.ToArray()
    [Array]::Sort($array, [StringComparer]::Ordinal)
    $text = ($array -join "`n") + "`n"
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($text)))
}

function Get-PayloadManifestRow([IO.FileInfo]$File, [string]$Base) {
    return [pscustomobject][ordered]@{
        relative_path = Get-RelativePath $Base $File.FullName
        bytes = [int64]$File.Length
        sha256 = Get-FileSha $File.FullName
        creation_time_utc_ticks = [int64]$File.CreationTimeUtc.Ticks
        last_write_time_utc_ticks = [int64]$File.LastWriteTimeUtc.Ticks
    }
}

function Get-RequiredPropertyValue([psobject]$Row, [string]$Name) {
    $matches = @($Row.PSObject.Properties | Where-Object { $_.Name -ceq $Name })
    if ($matches.Count -ne 1) { throw "required property missing or duplicated: $Name" }
    $value = [string]$matches[0].Value
    if ([string]::IsNullOrWhiteSpace($value)) { throw "required property blank: $Name" }
    return $value
}

$startedUtc = [DateTime]::UtcNow
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { throw 'source R3A root missing' }
if ((Get-FileSha $oldManifestPath) -ne $expectedOldManifestSha) { throw 'old manifest SHA mismatch' }
foreach ($path in @($destinationRoot, $stagePath, $resultPath, $auditResultPath)) {
    if (Test-Path -LiteralPath $path) { throw "R3B startup artifact already exists: $path" }
}

$sourceSnapshotBefore = Get-TreeSnapshot $sourceRoot
$oldRows = @(Import-Csv -LiteralPath $oldManifestPath)
if ($oldRows.Count -ne 205) { throw "old manifest row count=$($oldRows.Count)" }
$oldDictionary = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($row in $oldRows) {
    foreach ($field in $requiredOldFields) { $null = Get-RequiredPropertyValue $row $field }
    $canonical = Get-CanonicalRelative ([string]$row.relative_path)
    if ($oldDictionary.ContainsKey($canonical)) { throw "old manifest duplicate canonical path: $canonical" }
    $record = [pscustomobject][ordered]@{
        relative_path = $canonical
        bytes = [int64]$row.bytes
        sha256 = ([string]$row.sha256).ToUpperInvariant()
        creation_time_utc_ticks = [int64]$row.creation_time_utc_ticks
        last_write_time_utc_ticks = [int64]$row.last_write_time_utc_ticks
        source_path = Resolve-UnderRoot $sourceRoot $canonical
        destination_path = Resolve-UnderRoot $destinationRoot $canonical
    }
    $oldDictionary.Add($canonical, $record)
}
if ($oldDictionary.Count -ne 205) { throw 'old dictionary count mismatch' }
$actualOldPaths = [System.Collections.Generic.List[string]]::new()
foreach ($record in $oldDictionary.Values) {
    if (-not (Test-Path -LiteralPath $record.source_path -PathType Leaf)) { throw "old material missing: $($record.relative_path)" }
    $sourceItem = Get-Item -LiteralPath $record.source_path -Force
    if ($sourceItem.Length -ne $record.bytes) { throw "old byte mismatch: $($record.relative_path)" }
    if ((Get-FileSha $record.source_path) -ne $record.sha256) { throw "old SHA mismatch: $($record.relative_path)" }
    if ($sourceItem.CreationTimeUtc.Ticks -ne $record.creation_time_utc_ticks) { throw "old creation mismatch: $($record.relative_path)" }
    if ($sourceItem.LastWriteTimeUtc.Ticks -ne $record.last_write_time_utc_ticks) { throw "old last-write mismatch: $($record.relative_path)" }
    $actualOldPaths.Add((Get-RelativePath $sourceRoot $record.source_path))
}
$expectedOldPaths = @($oldDictionary.Keys | Sort-Object -CaseSensitive)
$actualOldPathsSorted = @($actualOldPaths.ToArray() | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $expectedOldPaths -DifferenceObject $actualOldPathsSorted -CaseSensitive).Count -ne 0) { throw 'old manifest/material set mismatch' }

[IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
$copyIdentity = [System.Collections.Generic.List[object]]::new()
foreach ($record in $oldDictionary.Values) {
    [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($record.destination_path)) | Out-Null
    [IO.File]::Copy($record.source_path, $record.destination_path, $false)
    [IO.File]::SetAttributes($record.destination_path, [IO.FileAttributes]::Normal)
    [IO.File]::SetCreationTimeUtc($record.destination_path, [DateTime]::new($record.creation_time_utc_ticks, [DateTimeKind]::Utc))
    [IO.File]::SetLastWriteTimeUtc($record.destination_path, [DateTime]::new($record.last_write_time_utc_ticks, [DateTimeKind]::Utc))
    $destinationItem = Get-Item -LiteralPath $record.destination_path -Force
    if ($destinationItem.Length -ne $record.bytes) { throw "copy byte mismatch: $($record.relative_path)" }
    if ((Get-FileSha $record.destination_path) -ne $record.sha256) { throw "copy SHA mismatch: $($record.relative_path)" }
    if ($destinationItem.CreationTimeUtc.Ticks -ne $record.creation_time_utc_ticks) { throw "copy creation mismatch: $($record.relative_path)" }
    if ($destinationItem.LastWriteTimeUtc.Ticks -ne $record.last_write_time_utc_ticks) { throw "copy last-write mismatch: $($record.relative_path)" }
    $copyIdentity.Add([pscustomobject][ordered]@{
        relative_path = $record.relative_path
        source_path = $record.source_path
        destination_path = $record.destination_path
        bytes = $record.bytes
        sha256 = $record.sha256
        creation_time_utc_ticks = $record.creation_time_utc_ticks
        last_write_time_utc_ticks = $record.last_write_time_utc_ticks
    })
}
if ($copyIdentity.Count -ne 205) { throw 'copy identity row count mismatch' }
if (@($copyIdentity | Where-Object { $oldControlNames -ccontains $_.relative_path }).Count -ne 0) { throw 'old control appears in copy identity' }

$copyIdentityPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$copyIdentity | Sort-Object -Property relative_path -CaseSensitive | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM
$preservedFields = @('relative_path', 'bytes', 'sha256', 'creation_time_utc_ticks', 'last_write_time_utc_ticks')
$addedPayload = @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json')
[ordered]@{
    schema = 'P126_R3B_COPY_PROVENANCE_V2'
    handoff_id = $handoffId
    operation = $operation
    source_root = [IO.Path]::GetFullPath($sourceRoot)
    destination_root = [IO.Path]::GetFullPath($destinationRoot)
    source_payload_manifest = [IO.Path]::GetFullPath($oldManifestPath)
    source_payload_manifest_sha256 = $expectedOldManifestSha
    source_root_snapshot_sha256 = $sourceSnapshotBefore
    copied_material_count = 205
    added_payload = $addedPayload
    preserved_fields = $preservedFields
    business_evidence_rerun = 0
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $provenancePath -Encoding utf8NoBOM

$payloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
if ($payloadFiles.Count -ne 207) { throw "R3B payload count=$($payloadFiles.Count)" }
$payloadRows = @($payloadFiles | ForEach-Object { Get-PayloadManifestRow $_ $destinationRoot } | Sort-Object -Property relative_path -CaseSensitive)
if (@($payloadRows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'R3B manifest duplicate path' }
$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
$payloadRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8NoBOM
$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
if ($manifestRows.Count -ne 207) { throw 'R3B written manifest row count mismatch' }
$actualPayloadPaths = @($payloadFiles | ForEach-Object { Get-RelativePath $destinationRoot $_.FullName } | Sort-Object -CaseSensitive)
$manifestPaths = @($manifestRows | ForEach-Object { Get-CanonicalRelative ([string]$_.relative_path) } | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $manifestPaths -DifferenceObject $actualPayloadPaths -CaseSensitive).Count -ne 0) { throw 'R3B manifest/FS set mismatch' }
foreach ($row in $manifestRows) {
    $relative = Get-CanonicalRelative ([string]$row.relative_path)
    $path = Resolve-UnderRoot $destinationRoot $relative
    $file = Get-Item -LiteralPath $path -Force
    if ($file.Length -ne [int64]$row.bytes) { throw "R3B manifest byte mismatch: $relative" }
    if ((Get-FileSha $path) -ne ([string]$row.sha256).ToUpperInvariant()) { throw "R3B manifest SHA mismatch: $relative" }
    if ($file.CreationTimeUtc.Ticks -ne [int64]$row.creation_time_utc_ticks) { throw "R3B manifest creation mismatch: $relative" }
    if ($file.LastWriteTimeUtc.Ticks -ne [int64]$row.last_write_time_utc_ticks) { throw "R3B manifest last-write mismatch: $relative" }
}

$manifestSha = Get-FileSha $manifestPath
$copyIdentitySha = Get-FileSha $copyIdentityPath
$copyProvenanceSha = Get-FileSha $provenancePath
$sealAudit = [ordered]@{
    schema = 'P126_R3B_PREMARKER_SEAL_AUDIT_V2'
    handoff_id = $handoffId
    operation = $operation
    preserved_business_verdict = $preservedVerdict
    hard_defect_id = $hardDefectId
    source_material_count = 205
    old_controls_copied = 0
    copy_identity_rows = 205
    payload_count = 207
    control_count_final = 3
    ordinary_count_final = 210
    manifest_rows = 207
    manifest_sha256 = $manifestSha
    copy_identity_sha256 = $copyIdentitySha
    copy_provenance_sha256 = $copyProvenanceSha
    source_root_snapshot_before_sha256 = $sourceSnapshotBefore
    copy_identity_errors = 0
    manifest_identity_errors = 0
    business_evidence_rerun = 0
    prepared_utc = [DateTime]::UtcNow.ToString('o')
}
$sealAudit | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $sealAuditPath -Encoding utf8NoBOM
$sealAuditSha = Get-FileSha $sealAuditPath

$preMarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
if ($preMarkerFiles.Count -ne 209) { throw "R3B premarker ordinary count=$($preMarkerFiles.Count)" }
foreach ($file in $preMarkerFiles) { [IO.File]::SetAttributes($file.FullName, ($file.Attributes -bor [IO.FileAttributes]::ReadOnly)) }
$destinationDirs = @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)
foreach ($directory in $destinationDirs) { [IO.File]::SetAttributes($directory.FullName, ($directory.Attributes -bor [IO.FileAttributes]::ReadOnly)) }
$destinationRootItem = Get-Item -LiteralPath $destinationRoot -Force
[IO.File]::SetAttributes($destinationRootItem.FullName, ($destinationRootItem.Attributes -bor [IO.FileAttributes]::ReadOnly))
$preMarkerDirsIncludingRoot = @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force))
if (@(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'R3B writable premarker file remains' }
if (@($preMarkerDirsIncludingRoot | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'R3B writable premarker directory remains' }

$maxDestinationTicks = Get-MaxLastWriteTicks @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force))
$future = [DateTime]::UtcNow.AddMinutes(10)
if ($future.Ticks -le $maxDestinationTicks) { $future = [DateTime]::new(($maxDestinationTicks + [TimeSpan]::FromMinutes(5).Ticks), [DateTimeKind]::Utc) }
$markerPreparedUtc = [DateTime]::UtcNow
$markerKeys = @(
    'HANDOFF_ID','OPERATION','VERDICT','ROOT','SOURCE_ROOT','COPIED_MATERIAL_COUNT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT',
    'OLD_PAYLOAD_MANIFEST_SHA256','SOURCE_ROOT_SNAPSHOT_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256',
    'SEAL_AUDIT_SHA256','HARD_DEFECT_ID','BUSINESS_EVIDENCE_RERUN','CONTROLLER_INVOCATION_COUNT','CONTROLLER_RETRY_COUNT',
    'AUDITOR_INVOCATION_BUDGET','MARKER_PREPARED_UTC','MARKER_LAST_WRITE_UTC'
)
$markerValues = [ordered]@{
    HANDOFF_ID = $handoffId
    OPERATION = $operation
    VERDICT = $preservedVerdict
    ROOT = $destinationRoot
    SOURCE_ROOT = $sourceRoot
    COPIED_MATERIAL_COUNT = '205'
    PAYLOAD_COUNT = '207'
    CONTROL_COUNT = '3'
    ORDINARY_COUNT = '210'
    OLD_PAYLOAD_MANIFEST_SHA256 = $expectedOldManifestSha
    SOURCE_ROOT_SNAPSHOT_SHA256 = $sourceSnapshotBefore
    COPY_IDENTITY_SHA256 = $copyIdentitySha
    COPY_PROVENANCE_SHA256 = $copyProvenanceSha
    PAYLOAD_MANIFEST_SHA256 = $manifestSha
    SEAL_AUDIT_SHA256 = $sealAuditSha
    HARD_DEFECT_ID = $hardDefectId
    BUSINESS_EVIDENCE_RERUN = '0'
    CONTROLLER_INVOCATION_COUNT = '1'
    CONTROLLER_RETRY_COUNT = '0'
    AUDITOR_INVOCATION_BUDGET = '1'
    MARKER_PREPARED_UTC = $markerPreparedUtc.ToString('o')
    MARKER_LAST_WRITE_UTC = $future.ToString('o')
}
$markerLines = @($markerKeys | ForEach-Object { "$_=$($markerValues[$_])" })
if ($markerLines.Count -ne 22) { throw 'R3B marker line count mismatch' }
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' }).Count -ne 0) { throw 'R3B invalid marker physical line' }
if (@($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'R3B duplicate marker key' }
if (($markerLines -join "`n") -match '(?i)PLACEHOLDER|TODO|\$\{|\$[A-Za-z_]|<[^>]+>') { throw 'R3B marker contains placeholder syntax' }
[IO.File]::WriteAllText($stagePath, (($markerLines -join "`n") + "`n"), [Text.UTF8Encoding]::new($false))
[IO.File]::SetLastWriteTimeUtc($stagePath, $future)
$stageItem = Get-Item -LiteralPath $stagePath -Force
[IO.File]::SetAttributes($stageItem.FullName, ($stageItem.Attributes -bor [IO.FileAttributes]::ReadOnly))
if (-not ((Get-Item -LiteralPath $stagePath -Force).Attributes -band [IO.FileAttributes]::ReadOnly)) { throw 'R3B external marker is writable' }

$markerPath = Join-Path $destinationRoot 'WRITE_STOPPED'
Move-Item -LiteralPath $stagePath -Destination $markerPath

$allDestinationFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
$allDestinationDirs = @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force))
$markerItem = Get-Item -LiteralPath $markerPath -Force
$otherItems = @($allDestinationFiles | Where-Object { $_.FullName -ne $markerPath }) + $allDestinationDirs
$maxOtherTicks = Get-MaxLastWriteTicks $otherItems
$marginTicks = [int64]$markerItem.LastWriteTimeUtc.Ticks - $maxOtherTicks
if ($allDestinationFiles.Count -ne 210) { throw "R3B ordinary count=$($allDestinationFiles.Count)" }
if (@($allDestinationFiles | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'R3B writable file after marker' }
if (@($allDestinationDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'R3B writable directory after marker' }
if ($marginTicks -le 0) { throw "R3B marker not strictly latest including root: $marginTicks" }
if (@($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count -ne 0) { throw 'R3B item at-or-after marker' }
if (Test-Path -LiteralPath $stagePath) { throw 'R3B marker stage remains after move' }

$destinationSnapshot1 = Get-TreeSnapshot $destinationRoot
$destinationSnapshot2 = Get-TreeSnapshot $destinationRoot
if ($destinationSnapshot1 -ne $destinationSnapshot2) { throw 'R3B postmarker destination snapshots differ' }
$sourceSnapshotAfter = Get-TreeSnapshot $sourceRoot
if ($sourceSnapshotAfter -ne $sourceSnapshotBefore) { throw 'R3A source root changed' }
$finishedUtc = [DateTime]::UtcNow

$controllerResult = [ordered]@{
    schema = 'P126_R3B_CONTROL_RESEAL_CONTROLLER_RESULT_V2'
    handoff_id = $handoffId
    operation = $operation
    preserved_business_verdict = $preservedVerdict
    hard_defect_id = $hardDefectId
    invocation_count = 1
    retry_count = 0
    exit = 0
    natural = $true
    start_utc = $startedUtc.ToString('o')
    end_utc = $finishedUtc.ToString('o')
    copied_material_count = 205
    old_controls_copied = 0
    payload_count = 207
    control_count = 3
    ordinary_count = 210
    directory_count_including_root = $allDestinationDirs.Count
    readonly_files = 210
    readonly_dirs = $allDestinationDirs.Count
    old_payload_manifest_sha256 = $expectedOldManifestSha
    copy_identity_sha256 = $copyIdentitySha
    copy_provenance_sha256 = $copyProvenanceSha
    payload_manifest_sha256 = $manifestSha
    seal_audit_sha256 = $sealAuditSha
    marker_path = $markerPath
    marker_bytes = $markerItem.Length
    marker_sha256 = Get-FileSha $markerPath
    marker_physical_lines = 22
    marker_unique_keys = 22
    marker_last_write_utc_ticks = $markerItem.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = $marginTicks
    at_or_after_excluding_marker = 0
    stage_absent_after_move = $true
    destination_postmarker_snapshot_sha256 = $destinationSnapshot1
    source_root_snapshot_before_sha256 = $sourceSnapshotBefore
    source_root_snapshot_after_sha256 = $sourceSnapshotAfter
    business_evidence_rerun = 0
    postmarker_content_attribute_writes = 0
}
$controllerResult | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM
Write-Output ($controllerResult | ConvertTo-Json -Depth 8)
