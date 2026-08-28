$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoffId = 'A-R115-P126-SA2-DIRECT-BUILD-R3A-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R3A_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3B_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$oldManifestPath = Join-Path $sourceRoot 'PAYLOAD_MANIFEST.csv'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_WRITE_STOPPED_STAGE_V1_20260828.tmp'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_CONTROL_RESEAL_CONTROLLER_RESULT_V1_20260828.json'
$controlNames = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$expectedOldManifestSha = '405541B02D962FD75161DAEBB41C067955D7B99B992DD1F14A7399D3A6EB0D7E'
$expectedSourceSnapshotSha = $null

function Get-CanonicalRelative([string]$Value) {
    return $Value.Replace('\', '/')
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

$startedUtc = [DateTime]::UtcNow
if (-not (Test-Path -LiteralPath $sourceRoot -PathType Container)) { throw 'source R3A root missing' }
if ((Get-FileSha $oldManifestPath) -ne $expectedOldManifestSha) { throw 'old manifest SHA mismatch' }
if (Test-Path -LiteralPath $destinationRoot) { throw 'R3B destination already exists' }
if (Test-Path -LiteralPath $stagePath) { throw 'R3B marker stage already exists' }
if (Test-Path -LiteralPath $resultPath) { throw 'R3B controller result already exists' }

$sourceSnapshotBefore = Get-TreeSnapshot $sourceRoot
$expectedSourceSnapshotSha = $sourceSnapshotBefore
$oldRows = @(Import-Csv -LiteralPath $oldManifestPath)
if ($oldRows.Count -ne 205) { throw "old manifest row count=$($oldRows.Count)" }
$requiredFields = @('relative_path', 'bytes', 'sha256', 'creation_time_utc_ticks', 'last_write_time_utc_ticks')
foreach ($field in $requiredFields) {
    if (@($oldRows | Where-Object { [string]::IsNullOrWhiteSpace([string]$_.PSObject.Properties[$field].Value) }).Count -ne 0) {
        throw "old manifest blank required field: $field"
    }
}
$resolvedOldRows = @($oldRows | ForEach-Object {
    $canonical = Get-CanonicalRelative ([string]$_.relative_path)
    [pscustomobject][ordered]@{
        relative_path = $canonical
        bytes = [int64]$_.bytes
        sha256 = ([string]$_.sha256).ToUpperInvariant()
        creation_time_utc_ticks = [int64]$_.creation_time_utc_ticks
        last_write_time_utc_ticks = [int64]$_.last_write_time_utc_ticks
        source_path = [IO.Path]::GetFullPath((Join-Path $sourceRoot $canonical.Replace('/', '\')))
        destination_path = [IO.Path]::GetFullPath((Join-Path $destinationRoot $canonical.Replace('/', '\')))
    }
})
if (@($resolvedOldRows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'old canonical relative path duplicate' }

$oldActualPaths = @($resolvedOldRows | ForEach-Object {
    if (-not (Test-Path -LiteralPath $_.source_path -PathType Leaf)) { throw "old material missing: $($_.relative_path)" }
    Get-CanonicalRelative ([IO.Path]::GetRelativePath($sourceRoot, $_.source_path))
} | Sort-Object -CaseSensitive)
$oldExpectedPaths = @($resolvedOldRows.relative_path | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $oldExpectedPaths -DifferenceObject $oldActualPaths -CaseSensitive).Count -ne 0) { throw 'old manifest/material set mismatch' }

[IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
$copyIdentity = [System.Collections.Generic.List[object]]::new()
foreach ($row in $resolvedOldRows) {
    $parent = [IO.Path]::GetDirectoryName($row.destination_path)
    [IO.Directory]::CreateDirectory($parent) | Out-Null
    [IO.File]::Copy($row.source_path, $row.destination_path, $false)
    [IO.File]::SetAttributes($row.destination_path, [IO.FileAttributes]::Normal)
    [IO.File]::SetCreationTimeUtc($row.destination_path, [DateTime]::new($row.creation_time_utc_ticks, [DateTimeKind]::Utc))
    [IO.File]::SetLastWriteTimeUtc($row.destination_path, [DateTime]::new($row.last_write_time_utc_ticks, [DateTimeKind]::Utc))
    $destination = Get-Item -LiteralPath $row.destination_path -Force
    if ($destination.Length -ne $row.bytes) { throw "copy byte mismatch: $($row.relative_path)" }
    if ((Get-FileSha $row.destination_path) -ne $row.sha256) { throw "copy SHA mismatch: $($row.relative_path)" }
    if ($destination.CreationTimeUtc.Ticks -ne $row.creation_time_utc_ticks) { throw "copy creation mismatch: $($row.relative_path)" }
    if ($destination.LastWriteTimeUtc.Ticks -ne $row.last_write_time_utc_ticks) { throw "copy last-write mismatch: $($row.relative_path)" }
    $copyIdentity.Add([pscustomobject][ordered]@{
        relative_path = $row.relative_path
        source_path = $row.source_path
        destination_path = $row.destination_path
        bytes = $row.bytes
        sha256 = $row.sha256
        creation_time_utc_ticks = $row.creation_time_utc_ticks
        last_write_time_utc_ticks = $row.last_write_time_utc_ticks
    })
}
if ($copyIdentity.Count -ne 205) { throw 'copy identity row count mismatch' }

$copyIdentityPath = Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$provenancePath = Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$copyIdentity | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM
[ordered]@{
    schema = 'P126_R3B_COPY_PROVENANCE_V1'
    handoff_id = $handoffId
    operation = $operation
    source_root = [IO.Path]::GetFullPath($sourceRoot)
    destination_root = [IO.Path]::GetFullPath($destinationRoot)
    source_payload_manifest = [IO.Path]::GetFullPath($oldManifestPath)
    source_payload_manifest_sha256 = $expectedOldManifestSha
    source_root_snapshot_sha256 = $sourceSnapshotBefore
    copied_material_count = 205
    added_payload = @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json')
    preserved_fields = @('relative_path', 'bytes', 'sha256', 'creation_time_utc_ticks', 'last_write_time_utc_ticks')
    business_evidence_rerun = 0
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $provenancePath -Encoding utf8NoBOM

$payloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Sort-Object -Property FullName -CaseSensitive)
if ($payloadFiles.Count -ne 207) { throw "R3B payload count=$($payloadFiles.Count)" }
$payloadRows = @($payloadFiles | ForEach-Object { Get-PayloadManifestRow $_ $destinationRoot })
if (@($payloadRows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'R3B manifest duplicate path' }

$manifestPath = Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $destinationRoot 'SEAL_AUDIT.json'
$payloadRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8NoBOM
$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
if ($manifestRows.Count -ne 207) { throw 'R3B written manifest row count mismatch' }
$actualPayloadPaths = @($payloadFiles | ForEach-Object { Get-RelativePath $destinationRoot $_.FullName } | Sort-Object -CaseSensitive)
$manifestPaths = @($manifestRows.relative_path | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $manifestPaths -DifferenceObject $actualPayloadPaths -CaseSensitive).Count -ne 0) { throw 'R3B manifest/FS set mismatch' }
foreach ($row in $manifestRows) {
    $path = Join-Path $destinationRoot ([string]$row.relative_path).Replace('/', '\')
    $file = Get-Item -LiteralPath $path -Force
    if ($file.Length -ne [int64]$row.bytes) { throw "R3B manifest byte mismatch: $($row.relative_path)" }
    if ((Get-FileSha $path) -ne ([string]$row.sha256).ToUpperInvariant()) { throw "R3B manifest SHA mismatch: $($row.relative_path)" }
    if ($file.CreationTimeUtc.Ticks -ne [int64]$row.creation_time_utc_ticks) { throw "R3B manifest creation mismatch: $($row.relative_path)" }
    if ($file.LastWriteTimeUtc.Ticks -ne [int64]$row.last_write_time_utc_ticks) { throw "R3B manifest last-write mismatch: $($row.relative_path)" }
}

[ordered]@{
    schema = 'P126_R3B_PREMARKER_SEAL_AUDIT_V1'
    handoff_id = $handoffId
    operation = $operation
    preserved_business_verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
    hard_defect_id = 'HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE'
    source_material_count = 205
    copy_identity_rows = $copyIdentity.Count
    payload_count = 207
    control_count_final = 3
    ordinary_count_final = 210
    manifest_rows = $manifestRows.Count
    manifest_sha256 = Get-FileSha $manifestPath
    copy_identity_sha256 = Get-FileSha $copyIdentityPath
    copy_provenance_sha256 = Get-FileSha $provenancePath
    source_root_snapshot_before_sha256 = $sourceSnapshotBefore
    copy_identity_errors = 0
    manifest_identity_errors = 0
    prepared_utc = [DateTime]::UtcNow.ToString('o')
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $sealAuditPath -Encoding utf8NoBOM

$preMarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
if ($preMarkerFiles.Count -ne 209) { throw "R3B premarker ordinary count=$($preMarkerFiles.Count)" }
foreach ($file in $preMarkerFiles) {
    [IO.File]::SetAttributes($file.FullName, ($file.Attributes -bor [IO.FileAttributes]::ReadOnly))
}
$destinationDirs = @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)
foreach ($directory in $destinationDirs) {
    [IO.File]::SetAttributes($directory.FullName, ($directory.Attributes -bor [IO.FileAttributes]::ReadOnly))
}
$destinationRootItem = Get-Item -LiteralPath $destinationRoot -Force
[IO.File]::SetAttributes($destinationRootItem.FullName, ($destinationRootItem.Attributes -bor [IO.FileAttributes]::ReadOnly))
$preMarkerDirsIncludingRoot = @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force))
if (@(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'R3B writable premarker file remains' }
if (@($preMarkerDirsIncludingRoot | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'R3B writable premarker directory remains' }

$maxDestinationTicks = Get-MaxLastWriteTicks @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force))
$future = [DateTime]::UtcNow.AddMinutes(10)
if ($future.Ticks -le $maxDestinationTicks) { $future = [DateTime]::new(($maxDestinationTicks + [TimeSpan]::FromMinutes(5).Ticks), [DateTimeKind]::Utc) }
$manifestSha = Get-FileSha $manifestPath
$sealAuditSha = Get-FileSha $sealAuditPath
$copyIdentitySha = Get-FileSha $copyIdentityPath
$copyProvenanceSha = Get-FileSha $provenancePath
$markerLines = @(
    "HANDOFF_ID=$handoffId",
    "OPERATION=$operation",
    'VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE',
    "ROOT=$destinationRoot",
    "SOURCE_ROOT=$sourceRoot",
    'COPIED_MATERIAL_COUNT=205',
    'PAYLOAD_COUNT=207',
    'CONTROL_COUNT=3',
    'ORDINARY_COUNT=210',
    "OLD_PAYLOAD_MANIFEST_SHA256=$expectedOldManifestSha",
    "SOURCE_ROOT_SNAPSHOT_SHA256=$sourceSnapshotBefore",
    "COPY_IDENTITY_SHA256=$copyIdentitySha",
    "COPY_PROVENANCE_SHA256=$copyProvenanceSha",
    "PAYLOAD_MANIFEST_SHA256=$manifestSha",
    "SEAL_AUDIT_SHA256=$sealAuditSha",
    'HARD_DEFECT_ID=HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE',
    'BUSINESS_EVIDENCE_RERUN=0',
    'CONTROLLER_INVOCATION_COUNT=1',
    'CONTROLLER_RETRY_COUNT=0',
    'AUDITOR_INVOCATION_BUDGET=1',
    "MARKER_PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))",
    "MARKER_LAST_WRITE_UTC=$($future.ToString('o'))"
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' }).Count -ne 0) { throw 'R3B invalid marker physical line' }
if (@($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'R3B duplicate marker key' }
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

$destinationSnapshot1 = Get-TreeSnapshot $destinationRoot
$destinationSnapshot2 = Get-TreeSnapshot $destinationRoot
if ($destinationSnapshot1 -ne $destinationSnapshot2) { throw 'R3B postmarker destination snapshots differ' }
$sourceSnapshotAfter = Get-TreeSnapshot $sourceRoot
if ($sourceSnapshotAfter -ne $sourceSnapshotBefore) { throw 'R3A source root changed' }

$finishedUtc = [DateTime]::UtcNow
[ordered]@{
    schema = 'P126_R3B_CONTROL_RESEAL_CONTROLLER_RESULT_V1'
    handoff_id = $handoffId
    operation = $operation
    invocation_count = 1
    retry_count = 0
    exit = 0
    natural = $true
    start_utc = $startedUtc.ToString('o')
    end_utc = $finishedUtc.ToString('o')
    copied_material_count = 205
    payload_count = 207
    control_count = 3
    ordinary_count = $allDestinationFiles.Count
    directory_count_including_root = $allDestinationDirs.Count
    readonly_files = @($allDestinationFiles | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReadOnly }).Count
    readonly_dirs = @($allDestinationDirs | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReadOnly }).Count
    marker_path = $markerPath
    marker_bytes = $markerItem.Length
    marker_sha256 = Get-FileSha $markerPath
    marker_last_write_utc_ticks = $markerItem.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = $marginTicks
    at_or_after_excluding_marker = 0
    destination_postmarker_snapshot_sha256 = $destinationSnapshot1
    source_root_snapshot_before_sha256 = $sourceSnapshotBefore
    source_root_snapshot_after_sha256 = $sourceSnapshotAfter
    postmarker_content_attribute_writes = 0
} | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM

Write-Output (Get-Content -LiteralPath $resultPath -Raw -Encoding utf8)
