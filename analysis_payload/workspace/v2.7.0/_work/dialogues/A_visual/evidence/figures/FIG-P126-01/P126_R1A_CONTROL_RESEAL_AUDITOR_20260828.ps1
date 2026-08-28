#requires -Version 7.0
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoffId = 'A-R115-P126-SA2-R168-READONLY-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1_SA2_R168_READONLY_R115_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R1A_SA2_R168_READONLY_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$externalBase = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01'
$sourceManifest = [IO.Path]::Combine($sourceRoot, 'PREMARKER_MANIFEST.csv')
$sourceMarker = [IO.Path]::Combine($sourceRoot, 'WSTOP.txt')
$controllerResult = [IO.Path]::Combine($externalBase, 'P126_R1A_CONTROL_RESEAL_CONTROLLER_RESULT_20260828.json')
$auditorResult = [IO.Path]::Combine($externalBase, 'P126_R1A_CONTROL_RESEAL_AUDIT_RESULT_20260828.json')
$expectedSourceManifestSha256 = '28A3D0839B2A4C50A35B50C3576AE4FD99B6A2A2138F222A9849AEB9F50ABD1D'
$expectedSourceMarkerSha256 = 'E97A4E128A7D399E2ED5A3190D7266720607C6D0F9F6042A8F7CD445BA0E2E90'
$expectedMaterialCount = 52
$expectedPayloadCount = 54
$expectedControlCount = 3
$expectedOrdinaryCount = 57
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Assert-Condition {
    param(
        [Parameter(Mandatory)][bool]$Condition,
        [Parameter(Mandatory)][string]$Message
    )
    if (-not $Condition) {
        throw $Message
    }
}

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Write-Utf8NoBomText {
    param(
        [Parameter(Mandatory)][string]$LiteralPath,
        [Parameter(Mandatory)][string]$Text
    )
    [IO.File]::WriteAllText($LiteralPath, $Text, $utf8NoBom)
}

function Write-Utf8NoBomJson {
    param(
        [Parameter(Mandatory)][string]$LiteralPath,
        [Parameter(Mandatory)]$InputObject
    )
    $json = $InputObject | ConvertTo-Json -Depth 12
    Write-Utf8NoBomText -LiteralPath $LiteralPath -Text ($json + "`n")
}

function Get-RelativeForwardPath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$FullName
    )
    return ([IO.Path]::GetRelativePath($Root, $FullName) -replace '\\', '/')
}

function Get-CanonicalHash {
    param([Parameter(Mandatory)][string[]]$Rows)
    $body = if ($Rows.Count -eq 0) { '' } else { ($Rows -join "`n") + "`n" }
    $bytes = $utf8NoBom.GetBytes($body)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

function Get-TreeSnapshot {
    param([Parameter(Mandatory)][string]$Root)
    $rootItem = Get-Item -LiteralPath $Root -Force
    $items = @($rootItem) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
    $rows = [Collections.Generic.List[string]]::new()
    $fileBytes = [int64]0
    foreach ($item in @($items | Sort-Object -Property FullName)) {
        $relativePath = if ($item.FullName -eq $rootItem.FullName) { '.' } else { Get-RelativeForwardPath -Root $Root -FullName $item.FullName }
        Assert-Condition -Condition (-not ($relativePath.Contains("`t") -or $relativePath.Contains("`r") -or $relativePath.Contains("`n"))) -Message "Unsafe snapshot path: $relativePath"
        if ($item.PSIsContainer) {
            $kind = 'D'
            $bytes = [int64]0
            $sha = ''
        } else {
            $kind = 'F'
            $bytes = [int64]$item.Length
            $sha = Get-Sha256 -LiteralPath $item.FullName
            $fileBytes += $bytes
        }
        $rows.Add(("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $kind, $relativePath, $bytes, $sha, $item.CreationTimeUtc.Ticks, $item.LastWriteTimeUtc.Ticks, [int64]$item.Attributes))
    }
    $orderedRows = @($rows | Sort-Object -CaseSensitive)
    return [pscustomobject]@{
        item_count = $orderedRows.Count
        file_bytes = $fileBytes
        canonical_sha256 = Get-CanonicalHash -Rows $orderedRows
    }
}

function Test-IsReadOnly {
    param([Parameter(Mandatory)]$Item)
    return (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

function Read-KeyValueFile {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $rawBytes = [IO.File]::ReadAllBytes($LiteralPath)
    Assert-Condition -Condition (-not ($rawBytes.Length -ge 3 -and $rawBytes[0] -eq 0xEF -and $rawBytes[1] -eq 0xBB -and $rawBytes[2] -eq 0xBF)) -Message "BOM is forbidden: $LiteralPath"
    $lines = @([IO.File]::ReadAllLines($LiteralPath, $utf8NoBom))
    Assert-Condition -Condition ($lines.Count -gt 0) -Message "Key-value file is empty: $LiteralPath"
    $badLines = @($lines | Where-Object { $_ -notmatch '^[^=\s]+=[^=\r\n\t]+$' })
    Assert-Condition -Condition ($badLines.Count -eq 0) -Message "Invalid key-value line: $LiteralPath"
    $pairs = [ordered]@{}
    foreach ($line in $lines) {
        $parts = $line -split '=', 2
        Assert-Condition -Condition (-not $pairs.Contains($parts[0])) -Message "Duplicate key in: $LiteralPath"
        $pairs[$parts[0]] = $parts[1]
    }
    return [pscustomobject]@{
        lines = $lines
        pairs = $pairs
    }
}

function Invoke-StrictModeMicrotests {
    $emptyDifferenceCount = @((Compare-Object -ReferenceObject @() -DifferenceObject @())).Count
    $equalDifferenceCount = @((Compare-Object -ReferenceObject @('a') -DifferenceObject @('a'))).Count
    $differentDifferenceCount = @((Compare-Object -ReferenceObject @('a') -DifferenceObject @('b'))).Count
    $uniqueDuplicateGroupCount = @(@('a', 'b') | Group-Object | Where-Object { $_.Count -ne 1 }).Count
    $duplicateGroupCount = @(@('a', 'a', 'b') | Group-Object | Where-Object { $_.Count -ne 1 }).Count
    Assert-Condition -Condition ($emptyDifferenceCount -eq 0) -Message 'StrictMode empty comparison microtest failed.'
    Assert-Condition -Condition ($equalDifferenceCount -eq 0) -Message 'StrictMode equal comparison microtest failed.'
    Assert-Condition -Condition ($differentDifferenceCount -eq 2) -Message 'StrictMode different comparison microtest failed.'
    Assert-Condition -Condition ($uniqueDuplicateGroupCount -eq 0) -Message 'StrictMode unique grouping microtest failed.'
    Assert-Condition -Condition ($duplicateGroupCount -eq 1) -Message 'StrictMode duplicate grouping microtest failed.'
    return [pscustomobject]@{
        empty = $emptyDifferenceCount
        equal = $equalDifferenceCount
        different = $differentDifferenceCount
        unique_duplicate_groups = $uniqueDuplicateGroupCount
        duplicate_groups = $duplicateGroupCount
    }
}

try {
    $startUtc = [DateTime]::UtcNow
    $microtests = Invoke-StrictModeMicrotests
    Assert-Condition -Condition ($PSVersionTable.PSVersion.Major -ge 7) -Message 'PowerShell 7 or later is required.'
    Assert-Condition -Condition (Test-Path -LiteralPath $sourceRoot -PathType Container) -Message 'Source root is missing.'
    Assert-Condition -Condition (Test-Path -LiteralPath $destinationRoot -PathType Container) -Message 'Destination root is missing.'
    Assert-Condition -Condition (Test-Path -LiteralPath $controllerResult -PathType Leaf) -Message 'Controller result is missing.'
    Assert-Condition -Condition (-not (Test-Path -LiteralPath $auditorResult)) -Message 'Auditor result already exists.'
    Assert-Condition -Condition ((Get-Sha256 -LiteralPath $sourceManifest) -eq $expectedSourceManifestSha256) -Message 'Source manifest identity mismatch.'
    Assert-Condition -Condition ((Get-Sha256 -LiteralPath $sourceMarker) -eq $expectedSourceMarkerSha256) -Message 'Source marker identity mismatch.'

    $auditorPath = $PSCommandPath
    $auditorBytes = (Get-Item -LiteralPath $auditorPath).Length
    $auditorSha256 = Get-Sha256 -LiteralPath $auditorPath
    $controllerData = Get-Content -LiteralPath $controllerResult -Raw | ConvertFrom-Json
    Assert-Condition -Condition ($controllerData.status -eq 'CONTROLLER_SUCCESS') -Message 'Controller did not report success.'
    Assert-Condition -Condition ($controllerData.controller_invocation_count -eq 1 -and $controllerData.controller_retry_count -eq 0) -Message 'Controller invocation contract mismatch.'

    $sourceSnapshot = Get-TreeSnapshot -Root $sourceRoot
    Assert-Condition -Condition ($sourceSnapshot.canonical_sha256 -eq $controllerData.source_snapshot_before_sha256) -Message 'Source root changed after controller input snapshot.'
    Assert-Condition -Condition ($sourceSnapshot.canonical_sha256 -eq $controllerData.source_snapshot_after_sha256) -Message 'Source root changed during controller invocation.'

    $copyIdentityPath = [IO.Path]::Combine($destinationRoot, 'COPY_IDENTITY.csv')
    $copyProvenancePath = [IO.Path]::Combine($destinationRoot, 'COPY_PROVENANCE.md')
    $payloadManifestPath = [IO.Path]::Combine($destinationRoot, 'PAYLOAD_MANIFEST.csv')
    $sealAuditPath = [IO.Path]::Combine($destinationRoot, 'SEAL_AUDIT.json')
    $markerPath = [IO.Path]::Combine($destinationRoot, 'WRITE_STOPPED')
    foreach ($requiredPath in @($copyIdentityPath, $copyProvenancePath, $payloadManifestPath, $sealAuditPath, $markerPath)) {
        Assert-Condition -Condition (Test-Path -LiteralPath $requiredPath -PathType Leaf) -Message "Required file is missing: $requiredPath"
    }

    $copyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
    Assert-Condition -Condition ($copyRows.Count -eq $expectedMaterialCount) -Message 'Copy identity row count mismatch.'
    $copyDuplicateGroups = @($copyRows | Group-Object -Property { $_['relative_path'] } | Where-Object { $_.Count -ne 1 })
    Assert-Condition -Condition ($copyDuplicateGroups.Count -eq 0) -Message 'Copy identity duplicate paths.'
    $copyMismatchCount = 0
    foreach ($copyRow in $copyRows) {
        $relativePath = [string]$copyRow.relative_path
        $relativeNative = $relativePath -replace '/', [IO.Path]::DirectorySeparatorChar
        $sourcePath = [IO.Path]::Combine($sourceRoot, $relativeNative)
        $destinationPath = [IO.Path]::Combine($destinationRoot, $relativeNative)
        Assert-Condition -Condition (Test-Path -LiteralPath $sourcePath -PathType Leaf) -Message "Source material missing: $relativePath"
        Assert-Condition -Condition (Test-Path -LiteralPath $destinationPath -PathType Leaf) -Message "Destination material missing: $relativePath"
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $match = (
            [int64]$copyRow.bytes -eq [int64]$sourceItem.Length -and
            [int64]$copyRow.bytes -eq [int64]$destinationItem.Length -and
            [string]$copyRow.sha256 -eq (Get-Sha256 -LiteralPath $sourcePath) -and
            [string]$copyRow.sha256 -eq (Get-Sha256 -LiteralPath $destinationPath) -and
            [int64]$copyRow.source_creation_time_utc_ticks -eq $sourceItem.CreationTimeUtc.Ticks -and
            [int64]$copyRow.destination_creation_time_utc_ticks -eq $destinationItem.CreationTimeUtc.Ticks -and
            [int64]$copyRow.source_last_write_time_utc_ticks -eq $sourceItem.LastWriteTimeUtc.Ticks -and
            [int64]$copyRow.destination_last_write_time_utc_ticks -eq $destinationItem.LastWriteTimeUtc.Ticks -and
            [string]$copyRow.identity_match -eq 'True'
        )
        if (-not $match) {
            $copyMismatchCount++
        }
    }
    Assert-Condition -Condition ($copyMismatchCount -eq 0) -Message 'Copy identity audit failed.'

    $payloadRows = @(Import-Csv -LiteralPath $payloadManifestPath)
    Assert-Condition -Condition ($payloadRows.Count -eq $expectedPayloadCount) -Message 'Payload manifest row count mismatch.'
    $payloadDuplicateGroups = @($payloadRows | Group-Object -Property { $_['relative_path'] } | Where-Object { $_.Count -ne 1 })
    Assert-Condition -Condition ($payloadDuplicateGroups.Count -eq 0) -Message 'Payload manifest duplicate paths.'
    $manifestMismatchCount = 0
    foreach ($payloadRow in $payloadRows) {
        $payloadPath = [IO.Path]::Combine($destinationRoot, ([string]$payloadRow.relative_path -replace '/', [IO.Path]::DirectorySeparatorChar))
        if (-not (Test-Path -LiteralPath $payloadPath -PathType Leaf)) {
            $manifestMismatchCount++
            continue
        }
        $payloadItem = Get-Item -LiteralPath $payloadPath -Force
        $match = (
            [int64]$payloadRow.bytes -eq [int64]$payloadItem.Length -and
            [string]$payloadRow.sha256 -eq (Get-Sha256 -LiteralPath $payloadPath) -and
            [int64]$payloadRow.creation_time_utc_ticks -eq $payloadItem.CreationTimeUtc.Ticks -and
            [int64]$payloadRow.last_write_time_utc_ticks -eq $payloadItem.LastWriteTimeUtc.Ticks
        )
        if (-not $match) {
            $manifestMismatchCount++
        }
    }
    Assert-Condition -Condition ($manifestMismatchCount -eq 0) -Message 'Payload manifest identity audit failed.'

    $expectedPayloadSet = @($payloadRows.relative_path | Sort-Object -CaseSensitive)
    $actualFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
    $actualRelativeSet = @($actualFiles | ForEach-Object { Get-RelativeForwardPath -Root $destinationRoot -FullName $_.FullName } | Sort-Object -CaseSensitive)
    $expectedOrdinarySet = @($expectedPayloadSet + @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED') | Sort-Object -CaseSensitive)
    $ordinarySetDifference = @((Compare-Object -ReferenceObject $expectedOrdinarySet -DifferenceObject $actualRelativeSet -CaseSensitive))
    Assert-Condition -Condition ($actualFiles.Count -eq $expectedOrdinaryCount -and $ordinarySetDifference.Count -eq 0) -Message 'Final ordinary file set mismatch.'

    $allDirectories = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force)
    $writableFiles = @($actualFiles | Where-Object { -not (Test-IsReadOnly -Item $_) })
    $writableDirectories = @($allDirectories | ForEach-Object { Get-Item -LiteralPath $_.FullName -Force } | Where-Object { -not (Test-IsReadOnly -Item $_) })
    Assert-Condition -Condition ($writableFiles.Count -eq 0 -and $writableDirectories.Count -eq 0) -Message 'Readonly audit failed.'

    $markerData = Read-KeyValueFile -LiteralPath $markerPath
    $requiredMarkerKeys = @(
        'FORMAT_VERSION', 'HANDOFF_ID', 'OPERATION', 'CONTENT_VERDICT', 'CONTROL_RESEAL_STATUS',
        'SOURCE_ROOT', 'DESTINATION_ROOT', 'SOURCE_MATERIAL_COUNT', 'PAYLOAD_COUNT', 'CONTROL_COUNT',
        'ORDINARY_COUNT', 'SOURCE_PREMARKER_MANIFEST_SHA256', 'SOURCE_WSTOP_SHA256',
        'COPY_IDENTITY_SHA256', 'COPY_PROVENANCE_SHA256', 'PAYLOAD_MANIFEST_SHA256',
        'SEAL_AUDIT_SHA256', 'CONTROLLER_SHA256', 'CONTROLLER_INVOCATION_COUNT',
        'CONTROLLER_RETRY_COUNT', 'PREMARKER_READONLY_VERIFIED', 'EXTERNAL_MARKER_STAGE',
        'FINAL_MOVE_COUNT', 'POSTMARKER_ROOT_CONTENT_ATTRIBUTE_WRITES', 'MARKER_TARGET_LAST_WRITE_UTC_TICKS'
    )
    $markerKeyDifference = @((Compare-Object -ReferenceObject $requiredMarkerKeys -DifferenceObject @($markerData.pairs.Keys)))
    Assert-Condition -Condition ($markerKeyDifference.Count -eq 0) -Message 'Marker key set mismatch.'
    Assert-Condition -Condition ($markerData.pairs['HANDOFF_ID'] -eq $handoffId -and $markerData.pairs['OPERATION'] -eq $operation) -Message 'Marker identity mismatch.'
    Assert-Condition -Condition ([int]$markerData.pairs['SOURCE_MATERIAL_COUNT'] -eq $expectedMaterialCount) -Message 'Marker material count mismatch.'
    Assert-Condition -Condition ([int]$markerData.pairs['PAYLOAD_COUNT'] -eq $expectedPayloadCount) -Message 'Marker payload count mismatch.'
    Assert-Condition -Condition ([int]$markerData.pairs['CONTROL_COUNT'] -eq $expectedControlCount) -Message 'Marker control count mismatch.'
    Assert-Condition -Condition ([int]$markerData.pairs['ORDINARY_COUNT'] -eq $expectedOrdinaryCount) -Message 'Marker ordinary count mismatch.'
    Assert-Condition -Condition ($markerData.pairs['COPY_IDENTITY_SHA256'] -eq (Get-Sha256 -LiteralPath $copyIdentityPath)) -Message 'Marker copy identity hash mismatch.'
    Assert-Condition -Condition ($markerData.pairs['COPY_PROVENANCE_SHA256'] -eq (Get-Sha256 -LiteralPath $copyProvenancePath)) -Message 'Marker copy provenance hash mismatch.'
    Assert-Condition -Condition ($markerData.pairs['PAYLOAD_MANIFEST_SHA256'] -eq (Get-Sha256 -LiteralPath $payloadManifestPath)) -Message 'Marker payload manifest hash mismatch.'
    Assert-Condition -Condition ($markerData.pairs['SEAL_AUDIT_SHA256'] -eq (Get-Sha256 -LiteralPath $sealAuditPath)) -Message 'Marker seal audit hash mismatch.'

    $sealAudit = Get-Content -LiteralPath $sealAuditPath -Raw | ConvertFrom-Json
    Assert-Condition -Condition ($sealAudit.source_material_count -eq $expectedMaterialCount -and $sealAudit.payload_count -eq $expectedPayloadCount -and $sealAudit.control_count -eq $expectedControlCount -and $sealAudit.ordinary_count -eq $expectedOrdinaryCount) -Message 'Seal audit count model mismatch.'
    $provenanceData = Read-KeyValueFile -LiteralPath $copyProvenancePath
    Assert-Condition -Condition ($provenanceData.pairs['SOURCE_ROOT'] -eq $sourceRoot -and $provenanceData.pairs['DESTINATION_ROOT'] -eq $destinationRoot) -Message 'Resolved provenance root mismatch.'
    Assert-Condition -Condition ($provenanceData.pairs['SOURCE_PREMARKER_MANIFEST_SHA256'] -eq $expectedSourceManifestSha256 -and $provenanceData.pairs['SOURCE_WSTOP_SHA256'] -eq $expectedSourceMarkerSha256) -Message 'Resolved provenance source control mismatch.'

    $markerItem = Get-Item -LiteralPath $markerPath -Force
    $itemsExcludingMarker = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force | Where-Object { $_.FullName -ne $markerItem.FullName })
    $atOrAfterMarker = @($itemsExcludingMarker | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
    $maximumOtherTicks = (@($itemsExcludingMarker | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
    $markerMarginTicks = $markerItem.LastWriteTimeUtc.Ticks - [int64]$maximumOtherTicks
    Assert-Condition -Condition ($atOrAfterMarker.Count -eq 0 -and $markerMarginTicks -gt 0) -Message 'Marker ordering audit failed.'

    $jsonParseFailureCount = 0
    foreach ($jsonFile in @($actualFiles | Where-Object { $_.Extension -eq '.json' })) {
        try {
            Get-Content -LiteralPath $jsonFile.FullName -Raw | ConvertFrom-Json | Out-Null
        } catch {
            $jsonParseFailureCount++
        }
    }
    $csvParseFailureCount = 0
    foreach ($csvFile in @($actualFiles | Where-Object { $_.Extension -eq '.csv' })) {
        try {
            @(Import-Csv -LiteralPath $csvFile.FullName) | Out-Null
        } catch {
            $csvParseFailureCount++
        }
    }
    Assert-Condition -Condition ($jsonParseFailureCount -eq 0 -and $csvParseFailureCount -eq 0) -Message 'Structured-file parse audit failed.'

    $alternateDataStreamCount = 0
    foreach ($file in $actualFiles) {
        $streams = @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object { $_.Stream -ne ':$DATA' })
        $alternateDataStreamCount += $streams.Count
    }
    $destinationItems = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force)
    $cacheArtifactCount = @($destinationItems | Where-Object { $_.Name -match '(?i)(\.pyc$|^__pycache__$|\.cache$|thumbs\.db$|desktop\.ini$)' }).Count
    $reparsePointCount = @($destinationItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
    Assert-Condition -Condition ($alternateDataStreamCount -eq 0 -and $cacheArtifactCount -eq 0 -and $reparsePointCount -eq 0) -Message 'Hygiene audit failed.'

    $destinationSnapshot = Get-TreeSnapshot -Root $destinationRoot
    Assert-Condition -Condition ($destinationSnapshot.canonical_sha256 -eq $controllerData.postmarker_snapshot_sha256) -Message 'Postmarker destination mutation detected.'
    $sourceSnapshotAfterAudit = Get-TreeSnapshot -Root $sourceRoot
    Assert-Condition -Condition ($sourceSnapshotAfterAudit.canonical_sha256 -eq $controllerData.source_snapshot_before_sha256) -Message 'Source root mutation detected during audit.'

    $result = [ordered]@{
        format_version = 1
        handoff_id = $handoffId
        operation = $operation
        status = 'AUDIT_PASS_EVIDENCE_ONLY_CONTROL_RESEAL_AWAIT_MAIN_ACCEPTANCE'
        auditor_invocation_count = 1
        auditor_retry_count = 0
        start_utc = $startUtc.ToString('o')
        end_utc = [DateTime]::UtcNow.ToString('o')
        source_root = $sourceRoot
        destination_root = $destinationRoot
        material_count = $expectedMaterialCount
        payload_count = $expectedPayloadCount
        control_count = $expectedControlCount
        ordinary_count = $actualFiles.Count
        directory_count_including_root = $allDirectories.Count
        readonly_file_count = $actualFiles.Count - $writableFiles.Count
        readonly_directory_count = $allDirectories.Count - $writableDirectories.Count
        copy_identity_mismatch_count = $copyMismatchCount
        payload_manifest_mismatch_count = $manifestMismatchCount
        ordinary_set_difference_count = $ordinarySetDifference.Count
        marker_line_count = $markerData.lines.Count
        marker_margin_ticks = $markerMarginTicks
        at_or_after_excluding_marker_count = $atOrAfterMarker.Count
        postmarker_content_attribute_write_count = 0
        alternate_data_stream_count = $alternateDataStreamCount
        cache_artifact_count = $cacheArtifactCount
        reparse_point_count = $reparsePointCount
        json_parse_failure_count = $jsonParseFailureCount
        csv_parse_failure_count = $csvParseFailureCount
        destination_snapshot_sha256 = $destinationSnapshot.canonical_sha256
        source_snapshot_sha256 = $sourceSnapshotAfterAudit.canonical_sha256
        payload_manifest_sha256 = Get-Sha256 -LiteralPath $payloadManifestPath
        seal_audit_sha256 = Get-Sha256 -LiteralPath $sealAuditPath
        marker_sha256 = Get-Sha256 -LiteralPath $markerPath
        auditor_path = $auditorPath
        auditor_bytes = $auditorBytes
        auditor_sha256 = $auditorSha256
        strict_mode_microtests = $microtests
    }
    Write-Utf8NoBomJson -LiteralPath $auditorResult -InputObject $result
    Write-Output ($result | ConvertTo-Json -Depth 12 -Compress)
}
catch {
    $failure = [ordered]@{
        format_version = 1
        handoff_id = $handoffId
        operation = $operation
        status = 'AUDITOR_FAILURE_FIRST_ERROR_STOP'
        auditor_invocation_count = 1
        auditor_retry_count = 0
        error = $_.Exception.Message
        failed_utc = [DateTime]::UtcNow.ToString('o')
    }
    if (-not (Test-Path -LiteralPath $auditorResult)) {
        Write-Utf8NoBomJson -LiteralPath $auditorResult -InputObject $failure
    }
    throw
}
