[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoffId = 'A-R114-P092-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1-20260828'
$operation = 'P092_R2_SA1_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R2_SA1_FRESH_ISOLATED_R114_20260828')
$targetRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01\STRICT_R2A_SA1_R114_EVIDENCE_ONLY_CONTROL_RESEAL_20260828')
$externalRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P092-01')
$sourceManifest = Join-Path $sourceRoot 'CONTENT_MANIFEST.csv'
$stageMarker = Join-Path $externalRoot 'P092_R2A_WRITE_STOPPED_V1.stage'
$externalAudit = Join-Path $externalRoot 'P092_R2A_CONTROL_RESEAL_V1_EXTERNAL_AUDIT.json'
$externalHandoff = Join-Path $externalRoot 'P092_R2A_CONTROL_RESEAL_V1_HANDOFF.md'

function Assert-True {
    param(
        [Parameter(Mandatory = $true)][bool]$Condition,
        [Parameter(Mandatory = $true)][string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativeName {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )
    return ([IO.Path]::GetRelativePath($Root, $Path) -replace '\\', '/')
}

function Get-TreeSnapshot {
    param([Parameter(Mandatory = $true)][string]$Root)
    $rootItem = Get-Item -LiteralPath $Root -Force
    $rows = [Collections.Generic.List[object]]::new()
    $rows.Add([pscustomobject][ordered]@{
        relative_name = '.'
        item_type = 'DIRECTORY'
        bytes = '0'
        sha256 = ''
        creation_utc_ticks = $rootItem.CreationTimeUtc.Ticks.ToString()
        last_write_utc_ticks = $rootItem.LastWriteTimeUtc.Ticks.ToString()
        attributes = ([int64]$rootItem.Attributes).ToString()
    })
    $items = @(Get-ChildItem -LiteralPath $Root -Recurse -Force | Sort-Object FullName)
    foreach ($item in $items) {
        $isDirectory = [bool]($item.Attributes -band [IO.FileAttributes]::Directory)
        $rows.Add([pscustomobject][ordered]@{
            relative_name = Get-RelativeName -Root $Root -Path $item.FullName
            item_type = $(if ($isDirectory) { 'DIRECTORY' } else { 'FILE' })
            bytes = $(if ($isDirectory) { '0' } else { $item.Length.ToString() })
            sha256 = $(if ($isDirectory) { '' } else { Get-Sha256 -Path $item.FullName })
            creation_utc_ticks = $item.CreationTimeUtc.Ticks.ToString()
            last_write_utc_ticks = $item.LastWriteTimeUtc.Ticks.ToString()
            attributes = ([int64]$item.Attributes).ToString()
        })
    }
    return @($rows)
}

function Get-SnapshotDigest {
    param([Parameter(Mandatory = $true)][object[]]$Rows)
    $text = ($Rows | ConvertTo-Json -Depth 5 -Compress)
    $data = [Text.UTF8Encoding]::new($false).GetBytes($text)
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return ([Convert]::ToHexString($sha.ComputeHash($data)))
    }
    finally {
        $sha.Dispose()
    }
}

function Set-ItemReadOnly {
    param([Parameter(Mandatory = $true)][string]$Path)
    $item = Get-Item -LiteralPath $Path -Force
    if ([bool]($item.Attributes -band [IO.FileAttributes]::Directory)) {
        $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::ReadOnly
    }
    else {
        $item.IsReadOnly = $true
    }
}

function Get-PayloadEntry {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Kind
    )
    $item = Get-Item -LiteralPath $Path -Force
    return [pscustomobject][ordered]@{
        relative_path = Get-RelativeName -Root $Root -Path $item.FullName
        bytes = $item.Length.ToString()
        sha256 = Get-Sha256 -Path $item.FullName
        creation_utc_ticks = $item.CreationTimeUtc.Ticks.ToString()
        last_write_utc_ticks = $item.LastWriteTimeUtc.Ticks.ToString()
        payload_kind = $Kind
    }
}

function Compare-Snapshots {
    param(
        [Parameter(Mandatory = $true)][object[]]$First,
        [Parameter(Mandatory = $true)][object[]]$Second
    )
    $firstText = $First | ConvertTo-Json -Depth 5 -Compress
    $secondText = $Second | ConvertTo-Json -Depth 5 -Compress
    return [int]($firstText -ne $secondText)
}

Assert-True -Condition (Test-Path -LiteralPath $sourceRoot -PathType Container) -Message 'Source root is absent.'
Assert-True -Condition (Test-Path -LiteralPath $sourceManifest -PathType Leaf) -Message 'Source manifest is absent.'
Assert-True -Condition (-not (Test-Path -LiteralPath $targetRoot)) -Message 'Target root already exists.'
Assert-True -Condition (Test-Path -LiteralPath (Split-Path -Parent $targetRoot) -PathType Container) -Message 'Target parent is absent.'
Assert-True -Condition (-not (Test-Path -LiteralPath $stageMarker)) -Message 'External marker stage already exists.'
Assert-True -Condition (-not (Test-Path -LiteralPath $externalAudit)) -Message 'External audit path already exists.'
Assert-True -Condition (-not (Test-Path -LiteralPath $externalHandoff)) -Message 'External handoff path already exists.'

$sourceBefore = @(Get-TreeSnapshot -Root $sourceRoot)
$sourceBeforeDigest = Get-SnapshotDigest -Rows $sourceBefore
$sourceRows = @(Import-Csv -LiteralPath $sourceManifest)
$materialRows = @($sourceRows | Where-Object { $_.entry_type -eq 'ROOT_CONTENT' })
$sourceControlRows = @($sourceRows | Where-Object { $_.entry_type -eq 'FINAL_MARKER_EXPECTED' })
Assert-True -Condition ($materialRows.Count -eq 19) -Message 'Source material row count is not 19.'
Assert-True -Condition ($sourceControlRows.Count -eq 1) -Message 'Source marker declaration count is not 1.'
Assert-True -Condition (@($materialRows | Group-Object relative_name | Where-Object { $_.Count -ne 1 }).Count -eq 0) -Message 'Source material names are not unique.'

New-Item -ItemType Directory -Path $targetRoot -ErrorAction Stop | Out-Null
$copyRows = [Collections.Generic.List[object]]::new()
foreach ($row in ($materialRows | Sort-Object relative_name)) {
    $relativeName = [string]$row.relative_name
    $sourcePath = Join-Path $sourceRoot ($relativeName -replace '/', '\\')
    $destinationPath = Join-Path $targetRoot ($relativeName -replace '/', '\\')
    Assert-True -Condition (Test-Path -LiteralPath $sourcePath -PathType Leaf) -Message "Source material is absent: $relativeName"
    $sourceItem = Get-Item -LiteralPath $sourcePath -Force
    Assert-True -Condition ($sourceItem.Length -eq [int64]$row.bytes) -Message "Source byte mismatch: $relativeName"
    Assert-True -Condition ((Get-Sha256 -Path $sourcePath) -eq ([string]$row.sha256).ToUpperInvariant()) -Message "Source hash mismatch: $relativeName"
    $destinationParent = Split-Path -Parent $destinationPath
    if (-not (Test-Path -LiteralPath $destinationParent -PathType Container)) {
        New-Item -ItemType Directory -Path $destinationParent -ErrorAction Stop | Out-Null
    }
    [IO.File]::Copy($sourcePath, $destinationPath, $false)
    [IO.File]::SetCreationTimeUtc($destinationPath, $sourceItem.CreationTimeUtc)
    [IO.File]::SetLastWriteTimeUtc($destinationPath, $sourceItem.LastWriteTimeUtc)
    $destinationItem = Get-Item -LiteralPath $destinationPath -Force
    $destinationSha = Get-Sha256 -Path $destinationPath
    Assert-True -Condition ($destinationItem.Length -eq $sourceItem.Length) -Message "Copied byte mismatch: $relativeName"
    Assert-True -Condition ($destinationSha -eq (Get-Sha256 -Path $sourcePath)) -Message "Copied hash mismatch: $relativeName"
    Assert-True -Condition ($destinationItem.CreationTimeUtc.Ticks -eq $sourceItem.CreationTimeUtc.Ticks) -Message "Copied creation ticks mismatch: $relativeName"
    Assert-True -Condition ($destinationItem.LastWriteTimeUtc.Ticks -eq $sourceItem.LastWriteTimeUtc.Ticks) -Message "Copied last-write ticks mismatch: $relativeName"
    $copyRows.Add([pscustomobject][ordered]@{
        source_relative_path = $relativeName
        destination_relative_path = $relativeName
        bytes = $sourceItem.Length.ToString()
        sha256 = $destinationSha
        creation_utc_ticks = $sourceItem.CreationTimeUtc.Ticks.ToString()
        last_write_utc_ticks = $sourceItem.LastWriteTimeUtc.Ticks.ToString()
    })
}

$copyIdentityPath = Join-Path $targetRoot 'COPY_IDENTITY.csv'
$copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM
$provenancePath = Join-Path $targetRoot 'COPY_PROVENANCE.json'
$provenanceObject = [ordered]@{
    handoff_id = $handoffId
    operation = $operation
    source_root = $sourceRoot
    destination_root = $targetRoot
    source_manifest = $sourceManifest
    copied_material_count = 19
    added_payload_count = 2
    final_payload_count = 21
    created_utc = [DateTime]::UtcNow.ToString('o')
    source_tree_before_digest = $sourceBeforeDigest
}
$provenanceObject | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $provenancePath -Encoding utf8NoBOM

$payloadPaths = @(
    @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force -File | Where-Object { $_.Name -notin @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED') })
)
Assert-True -Condition ($payloadPaths.Count -eq 21) -Message 'Final payload count is not 21.'
$payloadRows = [Collections.Generic.List[object]]::new()
foreach ($payloadPath in ($payloadPaths | Sort-Object FullName)) {
    $relativeName = Get-RelativeName -Root $targetRoot -Path $payloadPath.FullName
    $kind = $(if ($relativeName -in @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json')) { 'RESEAL_PROVENANCE' } else { 'COPIED_MATERIAL' })
    $payloadRows.Add((Get-PayloadEntry -Root $targetRoot -Path $payloadPath.FullName -Kind $kind))
}

$payloadManifestPath = Join-Path $targetRoot 'PAYLOAD_MANIFEST.csv'
$payloadRows | Export-Csv -LiteralPath $payloadManifestPath -NoTypeInformation -Encoding utf8NoBOM
$manifestReadback = @(Import-Csv -LiteralPath $payloadManifestPath)
Assert-True -Condition ($manifestReadback.Count -eq 21) -Message 'Payload manifest row count is not 21.'
Assert-True -Condition (@($manifestReadback | Group-Object relative_path | Where-Object { $_.Count -ne 1 }).Count -eq 0) -Message 'Payload manifest names are not unique.'

$manifestMismatchCount = 0
foreach ($row in $manifestReadback) {
    $payloadPath = Join-Path $targetRoot (([string]$row.relative_path) -replace '/', '\\')
    if (-not (Test-Path -LiteralPath $payloadPath -PathType Leaf)) {
        $manifestMismatchCount += 1
        continue
    }
    $item = Get-Item -LiteralPath $payloadPath -Force
    if ($item.Length.ToString() -ne [string]$row.bytes) { $manifestMismatchCount += 1 }
    if ((Get-Sha256 -Path $payloadPath) -ne ([string]$row.sha256).ToUpperInvariant()) { $manifestMismatchCount += 1 }
    if ($item.CreationTimeUtc.Ticks.ToString() -ne [string]$row.creation_utc_ticks) { $manifestMismatchCount += 1 }
    if ($item.LastWriteTimeUtc.Ticks.ToString() -ne [string]$row.last_write_utc_ticks) { $manifestMismatchCount += 1 }
}
Assert-True -Condition ($manifestMismatchCount -eq 0) -Message 'Payload manifest identity mismatch.'

$sealAuditPath = Join-Path $targetRoot 'SEAL_AUDIT.json'
$preMarkerAudit = [ordered]@{
    handoff_id = $handoffId
    operation = $operation
    source_material_count = 19
    copy_identity_mismatch_count = 0
    payload_count = 21
    manifest_row_count = 21
    manifest_mismatch_count = 0
    manifest_sha256 = Get-Sha256 -Path $payloadManifestPath
    control_count_final = 3
    ordinary_count_final = 24
    source_tree_before_digest = $sourceBeforeDigest
    premarker_status = 'PASS'
    created_utc = [DateTime]::UtcNow.ToString('o')
}
$preMarkerAudit | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $sealAuditPath -Encoding utf8NoBOM

$markerLines = @(
    "HANDOFF_ID=$handoffId",
    "OPERATION=$operation",
    'OUTCOME=SA1_CONTENT_PASS_RESEALED_READY_FOR_MAIN_REVIEW',
    "SOURCE_ROOT=$sourceRoot",
    "TARGET_ROOT=$targetRoot",
    'SOURCE_MATERIAL_COUNT=19',
    'PAYLOAD_COUNT=21',
    'CONTROL_COUNT=3',
    'ORDINARY_COUNT=24',
    "PAYLOAD_MANIFEST_SHA256=$(Get-Sha256 -Path $payloadManifestPath)",
    "SEAL_AUDIT_SHA256=$(Get-Sha256 -Path $sealAuditPath)",
    "PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))"
)
Assert-True -Condition (@($markerLines | Where-Object { [string]::IsNullOrWhiteSpace($_) }).Count -eq 0) -Message 'Marker contains a blank line.'
Assert-True -Condition (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=]+$' }).Count -eq 0) -Message 'Marker line syntax is invalid.'
Assert-True -Condition (@($markerLines | Where-Object { $_ -match '\$' -or $_ -match "`t" -or $_ -match '(?i)\brue\b' }).Count -eq 0) -Message 'Marker contains a prohibited token.'
$markerLines | Set-Content -LiteralPath $stageMarker -Encoding utf8NoBOM
Set-ItemReadOnly -Path $stageMarker

$existingFiles = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force -File)
$existingDirectories = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force -Directory | Sort-Object FullName -Descending)
Assert-True -Condition ($existingFiles.Count -eq 23) -Message 'Premarker ordinary file count is not 23.'
foreach ($file in $existingFiles) { Set-ItemReadOnly -Path $file.FullName }
foreach ($directory in $existingDirectories) { Set-ItemReadOnly -Path $directory.FullName }
Set-ItemReadOnly -Path $targetRoot

$readonlyFileFailures = @($existingFiles | Where-Object { -not (Get-Item -LiteralPath $_.FullName -Force).IsReadOnly }).Count
$readonlyDirectoryFailures = @($existingDirectories | Where-Object { -not ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) }).Count
$rootReadOnly = [bool]((Get-Item -LiteralPath $targetRoot -Force).Attributes -band [IO.FileAttributes]::ReadOnly)
Assert-True -Condition ($readonlyFileFailures -eq 0) -Message 'Premarker files are not all ReadOnly.'
Assert-True -Condition ($readonlyDirectoryFailures -eq 0) -Message 'Premarker directories are not all ReadOnly.'
Assert-True -Condition $rootReadOnly -Message 'Target root is not ReadOnly.'

$targetBeforeMarker = @(Get-TreeSnapshot -Root $targetRoot)
$targetMaxTicks = [DateTime]::UtcNow.Ticks
foreach ($entry in $targetBeforeMarker) {
    $entryTicks = [int64]$entry.last_write_utc_ticks
    if ($entryTicks -gt $targetMaxTicks) { $targetMaxTicks = $entryTicks }
}
$futureTicks = $targetMaxTicks + [TimeSpan]::FromMinutes(2).Ticks
$futureTime = [DateTime]::new($futureTicks, [DateTimeKind]::Utc)
[IO.File]::SetLastWriteTimeUtc($stageMarker, $futureTime)
Assert-True -Condition ((Get-Item -LiteralPath $stageMarker -Force).IsReadOnly) -Message 'Staged marker lost ReadOnly.'
Assert-True -Condition ((Get-Item -LiteralPath $stageMarker -Force).LastWriteTimeUtc.Ticks -eq $futureTicks) -Message 'Staged marker future time mismatch.'

$markerDestination = Join-Path $targetRoot 'WRITE_STOPPED'
Move-Item -LiteralPath $stageMarker -Destination $markerDestination -ErrorAction Stop

$postMarkerFirst = @(Get-TreeSnapshot -Root $targetRoot)
Start-Sleep -Milliseconds 250
$postMarkerSecond = @(Get-TreeSnapshot -Root $targetRoot)
$postMarkerDiffCount = Compare-Snapshots -First $postMarkerFirst -Second $postMarkerSecond

$finalFiles = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force -File)
$finalDirectories = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force -Directory)
$markerItem = Get-Item -LiteralPath $markerDestination -Force
$nonMarkerItems = [Collections.Generic.List[object]]::new()
$nonMarkerItems.Add((Get-Item -LiteralPath $targetRoot -Force))
foreach ($directory in $finalDirectories) { $nonMarkerItems.Add($directory) }
foreach ($file in ($finalFiles | Where-Object { $_.FullName -ne $markerItem.FullName })) { $nonMarkerItems.Add($file) }
$atOrAfterCount = @($nonMarkerItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count
$maxNonMarkerTicks = ($nonMarkerItems | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc.Ticks
$markerMarginTicks = $markerItem.LastWriteTimeUtc.Ticks - $maxNonMarkerTicks

$finalReadonlyFileFailures = @($finalFiles | Where-Object { -not (Get-Item -LiteralPath $_.FullName -Force).IsReadOnly }).Count
$finalReadonlyDirectoryFailures = @($finalDirectories | Where-Object { -not ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) }).Count
$finalRootReadOnly = [bool]((Get-Item -LiteralPath $targetRoot -Force).Attributes -band [IO.FileAttributes]::ReadOnly)

$finalManifestRows = @(Import-Csv -LiteralPath $payloadManifestPath)
$finalCopyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
$null = Get-Content -LiteralPath $provenancePath -Raw -Encoding UTF8 | ConvertFrom-Json
$null = Get-Content -LiteralPath $sealAuditPath -Raw -Encoding UTF8 | ConvertFrom-Json
$markerPhysicalLines = @(Get-Content -LiteralPath $markerDestination -Encoding UTF8)
$markerSyntaxFailures = @($markerPhysicalLines | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -notmatch '^[A-Z0-9_]+=[^=]+$' -or $_ -match '\$' -or $_ -match "`t" -or $_ -match '(?i)\brue\b' }).Count

$finalManifestMismatchCount = 0
foreach ($row in $finalManifestRows) {
    $payloadPath = Join-Path $targetRoot (([string]$row.relative_path) -replace '/', '\\')
    if (-not (Test-Path -LiteralPath $payloadPath -PathType Leaf)) {
        $finalManifestMismatchCount += 1
        continue
    }
    $item = Get-Item -LiteralPath $payloadPath -Force
    if ($item.Length.ToString() -ne [string]$row.bytes) { $finalManifestMismatchCount += 1 }
    if ((Get-Sha256 -Path $payloadPath) -ne ([string]$row.sha256).ToUpperInvariant()) { $finalManifestMismatchCount += 1 }
    if ($item.CreationTimeUtc.Ticks.ToString() -ne [string]$row.creation_utc_ticks) { $finalManifestMismatchCount += 1 }
    if ($item.LastWriteTimeUtc.Ticks.ToString() -ne [string]$row.last_write_utc_ticks) { $finalManifestMismatchCount += 1 }
}

$copyMismatchCount = 0
foreach ($row in $finalCopyRows) {
    $sourcePath = Join-Path $sourceRoot (([string]$row.source_relative_path) -replace '/', '\\')
    $destinationPath = Join-Path $targetRoot (([string]$row.destination_relative_path) -replace '/', '\\')
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf) -or -not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) {
        $copyMismatchCount += 1
        continue
    }
    $sourceItem = Get-Item -LiteralPath $sourcePath -Force
    $destinationItem = Get-Item -LiteralPath $destinationPath -Force
    if ($sourceItem.Length -ne $destinationItem.Length) { $copyMismatchCount += 1 }
    if ((Get-Sha256 -Path $sourcePath) -ne (Get-Sha256 -Path $destinationPath)) { $copyMismatchCount += 1 }
    if ($sourceItem.CreationTimeUtc.Ticks -ne $destinationItem.CreationTimeUtc.Ticks) { $copyMismatchCount += 1 }
    if ($sourceItem.LastWriteTimeUtc.Ticks -ne $destinationItem.LastWriteTimeUtc.Ticks) { $copyMismatchCount += 1 }
}

$alternateStreamCount = 0
foreach ($file in $finalFiles) {
    $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop)
    $alternateStreamCount += @($streams | Where-Object { $_.Stream -ne ':$DATA' }).Count
}
$cacheArtifactCount = @(
    @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force) |
        Where-Object { $_.FullName -match '(?i)(^|[\\/])(__pycache__|\.cache|cache)([\\/]|$)' -or $_.Name -match '(?i)\.pyc$' }
).Count
$reparseCount = @(
    @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Force) |
        Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }
).Count

$sourceAfter = @(Get-TreeSnapshot -Root $sourceRoot)
$sourceAfterDigest = Get-SnapshotDigest -Rows $sourceAfter
$sourceWriteDiffCount = Compare-Snapshots -First $sourceBefore -Second $sourceAfter

Assert-True -Condition ($finalFiles.Count -eq 24) -Message 'Final ordinary file count is not 24.'
Assert-True -Condition ($finalManifestRows.Count -eq 21) -Message 'Final manifest row count is not 21.'
Assert-True -Condition ($finalCopyRows.Count -eq 19) -Message 'Final copy identity row count is not 19.'
Assert-True -Condition ($finalManifestMismatchCount -eq 0) -Message 'Final manifest mismatch is nonzero.'
Assert-True -Condition ($copyMismatchCount -eq 0) -Message 'Final copy identity mismatch is nonzero.'
Assert-True -Condition ($finalReadonlyFileFailures -eq 0) -Message 'Final file ReadOnly failure is nonzero.'
Assert-True -Condition ($finalReadonlyDirectoryFailures -eq 0) -Message 'Final directory ReadOnly failure is nonzero.'
Assert-True -Condition $finalRootReadOnly -Message 'Final root is not ReadOnly.'
Assert-True -Condition ($markerSyntaxFailures -eq 0) -Message 'Final marker syntax failure is nonzero.'
Assert-True -Condition ($atOrAfterCount -eq 0) -Message 'A non-marker target item is at or after the marker.'
Assert-True -Condition ($markerMarginTicks -gt 0) -Message 'Marker is not strictly latest.'
Assert-True -Condition ($postMarkerDiffCount -eq 0) -Message 'Postmarker root content or attribute drift is nonzero.'
Assert-True -Condition ($alternateStreamCount -eq 0) -Message 'Alternate stream count is nonzero.'
Assert-True -Condition ($cacheArtifactCount -eq 0) -Message 'Cache artifact count is nonzero.'
Assert-True -Condition ($reparseCount -eq 0) -Message 'Reparse count is nonzero.'
Assert-True -Condition ($sourceWriteDiffCount -eq 0) -Message 'Source evidence root changed.'
Assert-True -Condition ($sourceBeforeDigest -eq $sourceAfterDigest) -Message 'Source evidence digest changed.'

$auditObject = [ordered]@{
    handoff_id = $handoffId
    operation = $operation
    outcome = 'SA1_CONTENT_PASS_RESEALED_READY_FOR_MAIN_REVIEW'
    source_root = $sourceRoot
    target_root = $targetRoot
    copied_material_count = 19
    payload_count = 21
    control_count = 3
    ordinary_count = 24
    copy_identity_mismatch_count = $copyMismatchCount
    manifest_mismatch_count = $finalManifestMismatchCount
    readonly_file_failure_count = $finalReadonlyFileFailures
    readonly_directory_failure_count = $finalReadonlyDirectoryFailures
    root_readonly = $finalRootReadOnly
    marker_physical_line_count = $markerPhysicalLines.Count
    marker_syntax_failure_count = $markerSyntaxFailures
    marker_last_write_utc_ticks = $markerItem.LastWriteTimeUtc.Ticks.ToString()
    marker_margin_ticks = $markerMarginTicks.ToString()
    at_or_after_excluding_marker = $atOrAfterCount
    postmarker_content_attribute_diff_count = $postMarkerDiffCount
    alternate_stream_count = $alternateStreamCount
    cache_artifact_count = $cacheArtifactCount
    reparse_count = $reparseCount
    source_write_diff_count = $sourceWriteDiffCount
    source_tree_before_digest = $sourceBeforeDigest
    source_tree_after_digest = $sourceAfterDigest
    payload_manifest_sha256 = Get-Sha256 -Path $payloadManifestPath
    seal_audit_sha256 = Get-Sha256 -Path $sealAuditPath
    write_stopped_sha256 = Get-Sha256 -Path $markerDestination
    first_postmarker_snapshot_digest = Get-SnapshotDigest -Rows $postMarkerFirst
    second_postmarker_snapshot_digest = Get-SnapshotDigest -Rows $postMarkerSecond
    completed_utc = [DateTime]::UtcNow.ToString('o')
    status = 'PASS'
}
$auditObject | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $externalAudit -Encoding utf8NoBOM

$handoffLines = @(
    '# P092 R2A evidence-only control reseal handoff',
    '',
    "- HANDOFF_ID: $handoffId",
    "- Operation: $operation",
    '- Outcome: `SA1_CONTENT_PASS_RESEALED_READY_FOR_MAIN_REVIEW`',
    "- Source root: $sourceRoot",
    "- Target root: $targetRoot",
    '- Copied material: `19`',
    '- Payload / controls / ordinary: `21 / 3 / 24`',
    "- Copy identity mismatch: $copyMismatchCount",
    "- Manifest mismatch: $finalManifestMismatchCount",
    "- Files at or after marker excluding marker: $atOrAfterCount",
    "- Marker strict-latest margin ticks: $markerMarginTicks",
    "- Postmarker content+attribute diff: $postMarkerDiffCount",
    "- Source-root write diff: $sourceWriteDiffCount",
    "- PAYLOAD_MANIFEST SHA-256: $(Get-Sha256 -Path $payloadManifestPath)",
    "- SEAL_AUDIT SHA-256: $(Get-Sha256 -Path $sealAuditPath)",
    "- WRITE_STOPPED SHA-256: $(Get-Sha256 -Path $markerDestination)",
    '',
    'The rejected source root was used read-only. No PDF, render, object, pair, manual, mathematical, semantic, source, build, Git, or central-state work was rerun. This evidence-only reseal requests Main acceptance of the preserved fresh SA1 content direction before any SA3 dispatch.'
)
$handoffLines | Set-Content -LiteralPath $externalHandoff -Encoding utf8NoBOM
Set-ItemReadOnly -Path $externalAudit
Set-ItemReadOnly -Path $externalHandoff

[pscustomobject][ordered]@{
    handoff_id = $handoffId
    operation = $operation
    invocation_count = 1
    target_root = $targetRoot
    payload_count = 21
    control_count = 3
    ordinary_count = 24
    marker_margin_ticks = $markerMarginTicks.ToString()
    postmarker_diff_count = $postMarkerDiffCount
    external_audit = $externalAudit
    external_handoff = $externalHandoff
    status = 'PASS'
} | ConvertTo-Json -Depth 5
