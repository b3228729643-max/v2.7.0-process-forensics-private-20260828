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
$stagedMarker = [IO.Path]::Combine($externalBase, 'P126_R1A_WRITE_STOPPED_STAGE_20260828')
$controllerResult = [IO.Path]::Combine($externalBase, 'P126_R1A_CONTROL_RESEAL_CONTROLLER_RESULT_20260828.json')
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

function Set-ReadOnlyAttribute {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $item = Get-Item -LiteralPath $LiteralPath -Force
    [IO.File]::SetAttributes($item.FullName, ($item.Attributes -bor [IO.FileAttributes]::ReadOnly))
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
    Assert-Condition -Condition (Test-Path -LiteralPath $sourceManifest -PathType Leaf) -Message 'Source manifest is missing.'
    Assert-Condition -Condition (Test-Path -LiteralPath $sourceMarker -PathType Leaf) -Message 'Source marker is missing.'
    Assert-Condition -Condition (-not (Test-Path -LiteralPath $destinationRoot)) -Message 'Destination root already exists.'
    Assert-Condition -Condition (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($destinationRoot)) -PathType Container) -Message 'Destination parent is missing.'
    Assert-Condition -Condition (-not (Test-Path -LiteralPath $stagedMarker)) -Message 'External staged marker already exists.'
    Assert-Condition -Condition (-not (Test-Path -LiteralPath $controllerResult)) -Message 'Controller result already exists.'
    Assert-Condition -Condition ((Get-Sha256 -LiteralPath $sourceManifest) -eq $expectedSourceManifestSha256) -Message 'Source manifest identity mismatch.'
    Assert-Condition -Condition ((Get-Sha256 -LiteralPath $sourceMarker) -eq $expectedSourceMarkerSha256) -Message 'Source marker identity mismatch.'

    $controllerPath = $PSCommandPath
    $controllerBytes = (Get-Item -LiteralPath $controllerPath).Length
    $controllerSha256 = Get-Sha256 -LiteralPath $controllerPath
    $sourceSnapshotBefore = Get-TreeSnapshot -Root $sourceRoot
    $manifestRows = @(Import-Csv -LiteralPath $sourceManifest)
    Assert-Condition -Condition ($manifestRows.Count -eq $expectedMaterialCount) -Message 'Source manifest material count mismatch.'
    $requiredColumns = @('RELATIVE_PATH', 'BYTES', 'SHA256', 'LAST_WRITE_UTC', 'ATTRIBUTES')
    $actualColumns = @($manifestRows[0].PSObject.Properties.Name)
    Assert-Condition -Condition (@((Compare-Object -ReferenceObject $requiredColumns -DifferenceObject $actualColumns)).Count -eq 0) -Message 'Source manifest columns mismatch.'
    $duplicateSourceRows = @($manifestRows | Group-Object -Property { $_['RELATIVE_PATH'] } | Where-Object { $_.Count -ne 1 })
    Assert-Condition -Condition ($duplicateSourceRows.Count -eq 0) -Message 'Source manifest contains duplicate paths.'

    $resolvedRows = [Collections.Generic.List[object]]::new()
    foreach ($row in $manifestRows) {
        $relativeForward = [string]$row.RELATIVE_PATH
        Assert-Condition -Condition (-not [string]::IsNullOrWhiteSpace($relativeForward)) -Message 'Source manifest contains a blank path.'
        Assert-Condition -Condition (-not [IO.Path]::IsPathRooted($relativeForward)) -Message "Rooted manifest path: $relativeForward"
        $segments = @($relativeForward -split '/')
        Assert-Condition -Condition (@($segments | Where-Object { $_ -eq '..' -or $_ -eq '.' -or [string]::IsNullOrWhiteSpace($_) }).Count -eq 0) -Message "Unsafe manifest path: $relativeForward"
        Assert-Condition -Condition ($relativeForward -notin @('PREMARKER_MANIFEST.csv', 'WSTOP.txt', 'PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')) -Message "Control path is not material: $relativeForward"
        $relativeNative = $relativeForward -replace '/', [IO.Path]::DirectorySeparatorChar
        $sourcePath = [IO.Path]::GetFullPath([IO.Path]::Combine($sourceRoot, $relativeNative))
        Assert-Condition -Condition ($sourcePath.StartsWith($sourceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) -Message "Manifest path escapes source root: $relativeForward"
        Assert-Condition -Condition (Test-Path -LiteralPath $sourcePath -PathType Leaf) -Message "Manifest material is missing: $relativeForward"
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        $sourceSha256 = Get-Sha256 -LiteralPath $sourcePath
        $manifestLastWriteTicks = ([DateTime]::Parse([string]$row.LAST_WRITE_UTC, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()).Ticks
        Assert-Condition -Condition ([int64]$row.BYTES -eq [int64]$sourceItem.Length) -Message "Manifest byte mismatch: $relativeForward"
        Assert-Condition -Condition ([string]$row.SHA256 -eq $sourceSha256) -Message "Manifest SHA mismatch: $relativeForward"
        Assert-Condition -Condition ($manifestLastWriteTicks -eq $sourceItem.LastWriteTimeUtc.Ticks) -Message "Manifest last-write mismatch: $relativeForward"
        $resolvedRows.Add([pscustomobject]@{
            relative_path = $relativeForward
            source_path = $sourcePath
            bytes = [int64]$sourceItem.Length
            sha256 = $sourceSha256
            creation_time_utc_ticks = [int64]$sourceItem.CreationTimeUtc.Ticks
            last_write_time_utc_ticks = [int64]$sourceItem.LastWriteTimeUtc.Ticks
        })
    }

    [IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
    $copyRows = [Collections.Generic.List[object]]::new()
    foreach ($resolved in @($resolvedRows | Sort-Object -Property relative_path -CaseSensitive)) {
        $relativeNative = $resolved.relative_path -replace '/', [IO.Path]::DirectorySeparatorChar
        $destinationPath = [IO.Path]::GetFullPath([IO.Path]::Combine($destinationRoot, $relativeNative))
        $destinationParent = [IO.Path]::GetDirectoryName($destinationPath)
        [IO.Directory]::CreateDirectory($destinationParent) | Out-Null
        Copy-Item -LiteralPath $resolved.source_path -Destination $destinationPath
        [IO.File]::SetAttributes($destinationPath, [IO.FileAttributes]::Archive)
        [IO.File]::SetCreationTimeUtc($destinationPath, [DateTime]::new($resolved.creation_time_utc_ticks, [DateTimeKind]::Utc))
        [IO.File]::SetLastWriteTimeUtc($destinationPath, [DateTime]::new($resolved.last_write_time_utc_ticks, [DateTimeKind]::Utc))
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $destinationSha256 = Get-Sha256 -LiteralPath $destinationPath
        $identityMatch = (
            [int64]$destinationItem.Length -eq $resolved.bytes -and
            $destinationSha256 -eq $resolved.sha256 -and
            $destinationItem.CreationTimeUtc.Ticks -eq $resolved.creation_time_utc_ticks -and
            $destinationItem.LastWriteTimeUtc.Ticks -eq $resolved.last_write_time_utc_ticks
        )
        Assert-Condition -Condition $identityMatch -Message "Copied material identity mismatch: $($resolved.relative_path)"
        $copyRows.Add([pscustomobject]@{
            relative_path = $resolved.relative_path
            bytes = $resolved.bytes
            sha256 = $resolved.sha256
            source_creation_time_utc_ticks = $resolved.creation_time_utc_ticks
            destination_creation_time_utc_ticks = [int64]$destinationItem.CreationTimeUtc.Ticks
            source_last_write_time_utc_ticks = $resolved.last_write_time_utc_ticks
            destination_last_write_time_utc_ticks = [int64]$destinationItem.LastWriteTimeUtc.Ticks
            identity_match = $identityMatch
        })
    }

    $copyIdentityPath = [IO.Path]::Combine($destinationRoot, 'COPY_IDENTITY.csv')
    @($copyRows) | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -UseQuotes AsNeeded -Encoding utf8
    $copyIdentitySha256 = Get-Sha256 -LiteralPath $copyIdentityPath
    $copyMismatchCount = @($copyRows | Where-Object { -not $_.identity_match }).Count
    Assert-Condition -Condition ($copyRows.Count -eq $expectedMaterialCount -and $copyMismatchCount -eq 0) -Message 'Copy identity closure failed.'

    $copyProvenancePath = [IO.Path]::Combine($destinationRoot, 'COPY_PROVENANCE.md')
    $provenanceLines = @(
        'FORMAT_VERSION=1',
        "HANDOFF_ID=$handoffId",
        "OPERATION=$operation",
        "SOURCE_ROOT=$sourceRoot",
        "DESTINATION_ROOT=$destinationRoot",
        "SOURCE_PREMARKER_MANIFEST=$sourceManifest",
        "SOURCE_PREMARKER_MANIFEST_SHA256=$expectedSourceManifestSha256",
        "SOURCE_WSTOP=$sourceMarker",
        "SOURCE_WSTOP_SHA256=$expectedSourceMarkerSha256",
        "SOURCE_TREE_ITEM_COUNT=$($sourceSnapshotBefore.item_count)",
        "SOURCE_TREE_FILE_BYTES=$($sourceSnapshotBefore.file_bytes)",
        "SOURCE_TREE_CANONICAL_SHA256=$($sourceSnapshotBefore.canonical_sha256)",
        "MATERIAL_COUNT=$expectedMaterialCount",
        'PRESERVED_IDENTITY=RELATIVE_PATH,BYTES,SHA256,CREATION_TIME_UTC_TICKS,LAST_WRITE_TIME_UTC_TICKS',
        "COPY_IDENTITY_SHA256=$copyIdentitySha256",
        "CONTROLLER_PATH=$controllerPath",
        "CONTROLLER_BYTES=$controllerBytes",
        "CONTROLLER_SHA256=$controllerSha256",
        'CONTENT_VERDICT=FAIL_TO_MAIN_SOURCE_SCOPE_PRESERVED',
        'CONTROL_RESEAL_STATUS=AWAITING_FINAL_MARKER'
    )
    Write-Utf8NoBomText -LiteralPath $copyProvenancePath -Text (($provenanceLines -join "`n") + "`n")
    $copyProvenanceSha256 = Get-Sha256 -LiteralPath $copyProvenancePath

    $payloadRelativePaths = @($resolvedRows.relative_path) + @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.md')
    $payloadDuplicateGroups = @($payloadRelativePaths | Group-Object | Where-Object { $_.Count -ne 1 })
    Assert-Condition -Condition ($payloadRelativePaths.Count -eq $expectedPayloadCount -and $payloadDuplicateGroups.Count -eq 0) -Message 'Payload path model failed.'
    $payloadRows = [Collections.Generic.List[object]]::new()
    foreach ($relativePath in @($payloadRelativePaths | Sort-Object -CaseSensitive)) {
        $payloadPath = [IO.Path]::Combine($destinationRoot, ($relativePath -replace '/', [IO.Path]::DirectorySeparatorChar))
        Assert-Condition -Condition (Test-Path -LiteralPath $payloadPath -PathType Leaf) -Message "Payload file is missing: $relativePath"
        $payloadItem = Get-Item -LiteralPath $payloadPath -Force
        $payloadRows.Add([pscustomobject]@{
            relative_path = $relativePath
            bytes = [int64]$payloadItem.Length
            sha256 = Get-Sha256 -LiteralPath $payloadPath
            creation_time_utc_ticks = [int64]$payloadItem.CreationTimeUtc.Ticks
            last_write_time_utc_ticks = [int64]$payloadItem.LastWriteTimeUtc.Ticks
        })
    }

    $payloadManifestPath = [IO.Path]::Combine($destinationRoot, 'PAYLOAD_MANIFEST.csv')
    @($payloadRows) | Export-Csv -LiteralPath $payloadManifestPath -NoTypeInformation -UseQuotes AsNeeded -Encoding utf8
    $payloadManifestSha256 = Get-Sha256 -LiteralPath $payloadManifestPath
    $payloadManifestRows = @(Import-Csv -LiteralPath $payloadManifestPath)
    $payloadManifestDuplicateGroups = @($payloadManifestRows | Group-Object -Property { $_['relative_path'] } | Where-Object { $_.Count -ne 1 })
    Assert-Condition -Condition ($payloadManifestRows.Count -eq $expectedPayloadCount -and $payloadManifestDuplicateGroups.Count -eq 0) -Message 'Payload manifest validation failed.'

    $sealAuditPath = [IO.Path]::Combine($destinationRoot, 'SEAL_AUDIT.json')
    $sealAudit = [ordered]@{
        format_version = 1
        handoff_id = $handoffId
        operation = $operation
        content_verdict = 'FAIL_TO_MAIN_SOURCE_SCOPE_PRESERVED'
        control_reseal_status = 'PREMARKER_IDENTITY_COMPLETE'
        source_root = $sourceRoot
        destination_root = $destinationRoot
        source_material_count = $expectedMaterialCount
        payload_count = $expectedPayloadCount
        control_count = $expectedControlCount
        ordinary_count = $expectedOrdinaryCount
        copy_identity_mismatch_count = $copyMismatchCount
        payload_manifest_row_count = $payloadManifestRows.Count
        payload_manifest_duplicate_count = $payloadManifestDuplicateGroups.Count
        source_premarker_manifest_sha256 = $expectedSourceManifestSha256
        source_wstop_sha256 = $expectedSourceMarkerSha256
        copy_identity_sha256 = $copyIdentitySha256
        copy_provenance_sha256 = $copyProvenanceSha256
        payload_manifest_sha256 = $payloadManifestSha256
        controller_sha256 = $controllerSha256
        source_tree_snapshot_before_sha256 = $sourceSnapshotBefore.canonical_sha256
        strict_mode_microtests = $microtests
        premarker_identity_verified = $true
        final_marker_required = $true
        postmarker_write_policy = 'ZERO_CONTENT_AND_ATTRIBUTE_WRITES'
    }
    Write-Utf8NoBomJson -LiteralPath $sealAuditPath -InputObject $sealAudit
    $sealAuditSha256 = Get-Sha256 -LiteralPath $sealAuditPath

    $premarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
    Assert-Condition -Condition ($premarkerFiles.Count -eq ($expectedOrdinaryCount - 1)) -Message 'Premarker file count mismatch.'
    foreach ($file in $premarkerFiles) {
        Set-ReadOnlyAttribute -LiteralPath $file.FullName
    }
    $premarkerDirectories = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force)
    foreach ($directory in @($premarkerDirectories | Sort-Object { $_.FullName.Length } -Descending)) {
        Set-ReadOnlyAttribute -LiteralPath $directory.FullName
    }
    $premarkerWritableFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force | Where-Object { -not (Test-IsReadOnly -Item $_) })
    $premarkerWritableDirectories = @($premarkerDirectories | ForEach-Object { Get-Item -LiteralPath $_.FullName -Force } | Where-Object { -not (Test-IsReadOnly -Item $_) })
    Assert-Condition -Condition ($premarkerWritableFiles.Count -eq 0 -and $premarkerWritableDirectories.Count -eq 0) -Message 'Premarker readonly gate failed.'

    $premarkerItems = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force)
    $maximumPremarkerTicks = (@($premarkerItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
    $futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(10).Ticks, ([int64]$maximumPremarkerTicks + [TimeSpan]::FromMinutes(5).Ticks))
    $markerLines = @(
        'FORMAT_VERSION=1',
        "HANDOFF_ID=$handoffId",
        "OPERATION=$operation",
        'CONTENT_VERDICT=FAIL_TO_MAIN_SOURCE_SCOPE_PRESERVED',
        'CONTROL_RESEAL_STATUS=SEALED_AWAIT_MAIN_ACCEPTANCE',
        "SOURCE_ROOT=$sourceRoot",
        "DESTINATION_ROOT=$destinationRoot",
        "SOURCE_MATERIAL_COUNT=$expectedMaterialCount",
        "PAYLOAD_COUNT=$expectedPayloadCount",
        "CONTROL_COUNT=$expectedControlCount",
        "ORDINARY_COUNT=$expectedOrdinaryCount",
        "SOURCE_PREMARKER_MANIFEST_SHA256=$expectedSourceManifestSha256",
        "SOURCE_WSTOP_SHA256=$expectedSourceMarkerSha256",
        "COPY_IDENTITY_SHA256=$copyIdentitySha256",
        "COPY_PROVENANCE_SHA256=$copyProvenanceSha256",
        "PAYLOAD_MANIFEST_SHA256=$payloadManifestSha256",
        "SEAL_AUDIT_SHA256=$sealAuditSha256",
        "CONTROLLER_SHA256=$controllerSha256",
        'CONTROLLER_INVOCATION_COUNT=1',
        'CONTROLLER_RETRY_COUNT=0',
        'PREMARKER_READONLY_VERIFIED=true',
        'EXTERNAL_MARKER_STAGE=true',
        'FINAL_MOVE_COUNT=1',
        'POSTMARKER_ROOT_CONTENT_ATTRIBUTE_WRITES=0',
        "MARKER_TARGET_LAST_WRITE_UTC_TICKS=$futureTicks"
    )
    Assert-Condition -Condition (@($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^=\r\n\t]+$' }).Count -eq 0) -Message 'Marker line syntax failed.'
    Assert-Condition -Condition (@($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -eq 0) -Message 'Marker key uniqueness failed.'
    Write-Utf8NoBomText -LiteralPath $stagedMarker -Text (($markerLines -join "`n") + "`n")
    [IO.File]::SetLastWriteTimeUtc($stagedMarker, [DateTime]::new($futureTicks, [DateTimeKind]::Utc))
    Set-ReadOnlyAttribute -LiteralPath $stagedMarker
    $stagedMarkerItem = Get-Item -LiteralPath $stagedMarker -Force
    Assert-Condition -Condition ((Test-IsReadOnly -Item $stagedMarkerItem) -and $stagedMarkerItem.LastWriteTimeUtc.Ticks -eq $futureTicks) -Message 'External marker staging gate failed.'

    $targetMarker = [IO.Path]::Combine($destinationRoot, 'WRITE_STOPPED')
    Assert-Condition -Condition (-not (Test-Path -LiteralPath $targetMarker)) -Message 'Destination marker already exists.'
    Move-Item -LiteralPath $stagedMarker -Destination $targetMarker

    $postmarkerSnapshot1 = Get-TreeSnapshot -Root $destinationRoot
    $ordinaryFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
    $allDirectories = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force)
    $writableFiles = @($ordinaryFiles | Where-Object { -not (Test-IsReadOnly -Item $_) })
    $writableDirectories = @($allDirectories | ForEach-Object { Get-Item -LiteralPath $_.FullName -Force } | Where-Object { -not (Test-IsReadOnly -Item $_) })
    Assert-Condition -Condition ($ordinaryFiles.Count -eq $expectedOrdinaryCount) -Message 'Final ordinary count mismatch.'
    Assert-Condition -Condition ($writableFiles.Count -eq 0 -and $writableDirectories.Count -eq 0) -Message 'Final readonly gate failed.'
    $markerItem = Get-Item -LiteralPath $targetMarker -Force
    $itemsExcludingMarker = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force | Where-Object { $_.FullName -ne $markerItem.FullName })
    $atOrAfterMarker = @($itemsExcludingMarker | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
    $maximumOtherTicks = (@($itemsExcludingMarker | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
    $markerMarginTicks = $markerItem.LastWriteTimeUtc.Ticks - [int64]$maximumOtherTicks
    Assert-Condition -Condition ($atOrAfterMarker.Count -eq 0 -and $markerMarginTicks -gt 0) -Message 'Final marker ordering gate failed.'
    $postmarkerSnapshot2 = Get-TreeSnapshot -Root $destinationRoot
    Assert-Condition -Condition ($postmarkerSnapshot1.canonical_sha256 -eq $postmarkerSnapshot2.canonical_sha256) -Message 'Postmarker root mutation detected.'
    $sourceSnapshotAfter = Get-TreeSnapshot -Root $sourceRoot
    Assert-Condition -Condition ($sourceSnapshotBefore.canonical_sha256 -eq $sourceSnapshotAfter.canonical_sha256) -Message 'Source root mutation detected.'

    $result = [ordered]@{
        format_version = 1
        handoff_id = $handoffId
        operation = $operation
        status = 'CONTROLLER_SUCCESS'
        controller_invocation_count = 1
        controller_retry_count = 0
        start_utc = $startUtc.ToString('o')
        end_utc = [DateTime]::UtcNow.ToString('o')
        source_root = $sourceRoot
        destination_root = $destinationRoot
        material_count = $expectedMaterialCount
        payload_count = $expectedPayloadCount
        control_count = $expectedControlCount
        ordinary_count = $ordinaryFiles.Count
        readonly_file_count = $ordinaryFiles.Count - $writableFiles.Count
        readonly_directory_count = $allDirectories.Count - $writableDirectories.Count
        copy_identity_mismatch_count = $copyMismatchCount
        marker_path = $targetMarker
        marker_sha256 = Get-Sha256 -LiteralPath $targetMarker
        marker_last_write_utc_ticks = $markerItem.LastWriteTimeUtc.Ticks
        marker_margin_ticks = $markerMarginTicks
        at_or_after_excluding_marker_count = $atOrAfterMarker.Count
        postmarker_snapshot_sha256 = $postmarkerSnapshot2.canonical_sha256
        postmarker_content_attribute_write_count = 0
        source_snapshot_before_sha256 = $sourceSnapshotBefore.canonical_sha256
        source_snapshot_after_sha256 = $sourceSnapshotAfter.canonical_sha256
        payload_manifest_sha256 = $payloadManifestSha256
        seal_audit_sha256 = $sealAuditSha256
        controller_path = $controllerPath
        controller_bytes = $controllerBytes
        controller_sha256 = $controllerSha256
        strict_mode_microtests = $microtests
    }
    Write-Utf8NoBomJson -LiteralPath $controllerResult -InputObject $result
    Write-Output ($result | ConvertTo-Json -Depth 12 -Compress)
}
catch {
    $failure = [ordered]@{
        format_version = 1
        handoff_id = $handoffId
        operation = $operation
        status = 'CONTROLLER_FAILURE_FIRST_ERROR_STOP'
        controller_invocation_count = 1
        controller_retry_count = 0
        error = $_.Exception.Message
        failed_utc = [DateTime]::UtcNow.ToString('o')
    }
    if (-not (Test-Path -LiteralPath $controllerResult)) {
        Write-Utf8NoBomJson -LiteralPath $controllerResult -InputObject $failure
    }
    throw
}
