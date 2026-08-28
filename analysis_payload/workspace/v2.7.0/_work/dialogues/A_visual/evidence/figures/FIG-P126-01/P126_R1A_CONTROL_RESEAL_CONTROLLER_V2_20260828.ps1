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

function Assert-True {
    param([Parameter(Mandatory)][bool]$Value, [Parameter(Mandatory)][string]$Message)
    if (-not $Value) { throw $Message }
}

function Get-Sha256 {
    param([Parameter(Mandatory)][string]$LiteralPath)
    (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Write-TextNoBom {
    param([Parameter(Mandatory)][string]$LiteralPath, [Parameter(Mandatory)][string]$Text)
    [IO.File]::WriteAllText($LiteralPath, $Text, $utf8NoBom)
}

function Write-JsonNoBom {
    param([Parameter(Mandatory)][string]$LiteralPath, [Parameter(Mandatory)]$Value)
    Write-TextNoBom -LiteralPath $LiteralPath -Text (($Value | ConvertTo-Json -Depth 12) + "`n")
}

function Convert-ForwardPath {
    param([Parameter(Mandatory)][string]$Path)
    $Path.Replace('\', '/')
}

function Convert-NativePath {
    param([Parameter(Mandatory)][string]$ForwardPath)
    $ForwardPath.Replace('/', [IO.Path]::DirectorySeparatorChar)
}

function Get-RelativeForwardPath {
    param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$FullName)
    Convert-ForwardPath -Path ([IO.Path]::GetRelativePath($Root, $FullName))
}

function Get-CanonicalHash {
    param([Parameter(Mandatory)][string[]]$Rows)
    $text = if ($Rows.Count -eq 0) { '' } else { ($Rows -join "`n") + "`n" }
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($utf8NoBom.GetBytes($text)))
}

function Get-TreeSnapshot {
    param([Parameter(Mandatory)][string]$Root)
    $rootItem = Get-Item -LiteralPath $Root -Force
    $items = @($rootItem) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
    $rows = [Collections.Generic.List[string]]::new()
    $fileBytes = [int64]0
    foreach ($item in @($items | Sort-Object -Property FullName)) {
        $relative = if ($item.FullName -eq $rootItem.FullName) { '.' } else { Get-RelativeForwardPath -Root $Root -FullName $item.FullName }
        Assert-True -Value (-not ($relative.Contains("`t") -or $relative.Contains("`r") -or $relative.Contains("`n"))) -Message "Unsafe snapshot path: $relative"
        if ($item.PSIsContainer) {
            $kind = 'D'; $bytes = [int64]0; $sha = ''
        } else {
            $kind = 'F'; $bytes = [int64]$item.Length; $sha = Get-Sha256 -LiteralPath $item.FullName; $fileBytes += $bytes
        }
        $rows.Add(("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $kind, $relative, $bytes, $sha, $item.CreationTimeUtc.Ticks, $item.LastWriteTimeUtc.Ticks, [int64]$item.Attributes))
    }
    $ordered = @($rows | Sort-Object -CaseSensitive)
    [pscustomobject]@{ item_count = $ordered.Count; file_bytes = $fileBytes; canonical_sha256 = Get-CanonicalHash -Rows $ordered }
}

function Test-ReadOnly {
    param([Parameter(Mandatory)]$Item)
    (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

function Set-ReadOnly {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $item = Get-Item -LiteralPath $LiteralPath -Force
    [IO.File]::SetAttributes($item.FullName, ($item.Attributes -bor [IO.FileAttributes]::ReadOnly))
}

function Invoke-Microtests {
    $empty = @((Compare-Object -ReferenceObject @() -DifferenceObject @())).Count
    $equal = @((Compare-Object -ReferenceObject @('a') -DifferenceObject @('a'))).Count
    $different = @((Compare-Object -ReferenceObject @('a') -DifferenceObject @('b'))).Count
    $uniqueRows = @([pscustomobject]@{ relative_path = 'a' }, [pscustomobject]@{ relative_path = 'b' })
    $duplicateRows = @([pscustomobject]@{ relative_path = 'a' }, [pscustomobject]@{ relative_path = 'a' }, [pscustomobject]@{ relative_path = 'b' })
    $uniqueDuplicateGroups = @($uniqueRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 }).Count
    $duplicateGroups = @($duplicateRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 }).Count
    $rawRepresentative = @('top-level.txt', 'nested\child.txt')
    $canonicalExpected = @($rawRepresentative | ForEach-Object { Convert-ForwardPath -Path $_ } | Sort-Object -CaseSensitive)
    $simulatedActual = @('top-level.txt', 'nested/child.txt' | Sort-Object -CaseSensitive)
    $canonicalSetDifference = @((Compare-Object -ReferenceObject $canonicalExpected -DifferenceObject $simulatedActual -CaseSensitive)).Count
    Assert-True -Value ($empty -eq 0 -and $equal -eq 0 -and $different -eq 2) -Message 'StrictMode comparison microtest failed.'
    Assert-True -Value ($uniqueDuplicateGroups -eq 0 -and $duplicateGroups -eq 1) -Message 'Explicit-property duplicate microtest failed.'
    Assert-True -Value ($canonicalSetDifference -eq 0) -Message 'Forward-path canonicalization microtest failed.'
    [pscustomobject]@{ empty = $empty; equal = $equal; different = $different; unique_duplicate_groups = $uniqueDuplicateGroups; duplicate_groups = $duplicateGroups; canonical_set_difference = $canonicalSetDifference }
}

try {
    $startUtc = [DateTime]::UtcNow
    $microtests = Invoke-Microtests
    Assert-True -Value ($PSVersionTable.PSVersion.Major -ge 7) -Message 'PowerShell 7 or later is required.'
    Assert-True -Value (Test-Path -LiteralPath $sourceRoot -PathType Container) -Message 'Source root is missing.'
    Assert-True -Value (Test-Path -LiteralPath $sourceManifest -PathType Leaf) -Message 'Source manifest is missing.'
    Assert-True -Value (Test-Path -LiteralPath $sourceMarker -PathType Leaf) -Message 'Source marker is missing.'
    Assert-True -Value (-not (Test-Path -LiteralPath $destinationRoot)) -Message 'Destination root already exists.'
    Assert-True -Value (Test-Path -LiteralPath ([IO.Path]::GetDirectoryName($destinationRoot)) -PathType Container) -Message 'Destination parent is missing.'
    Assert-True -Value (-not (Test-Path -LiteralPath $stagedMarker)) -Message 'External staged marker already exists.'
    Assert-True -Value (-not (Test-Path -LiteralPath $controllerResult)) -Message 'Controller result already exists.'
    Assert-True -Value ((Get-Sha256 -LiteralPath $sourceManifest) -eq $expectedSourceManifestSha256) -Message 'Source manifest identity mismatch.'
    Assert-True -Value ((Get-Sha256 -LiteralPath $sourceMarker) -eq $expectedSourceMarkerSha256) -Message 'Source marker identity mismatch.'

    $controllerPath = $PSCommandPath
    $controllerItem = Get-Item -LiteralPath $controllerPath -Force
    $controllerSha256 = Get-Sha256 -LiteralPath $controllerPath
    $sourceSnapshotBefore = Get-TreeSnapshot -Root $sourceRoot
    $manifestRows = @(Import-Csv -LiteralPath $sourceManifest)
    Assert-True -Value ($manifestRows.Count -eq $expectedMaterialCount) -Message 'Source manifest material count mismatch.'
    $requiredColumns = @('RELATIVE_PATH', 'BYTES', 'SHA256', 'LAST_WRITE_UTC', 'ATTRIBUTES')
    $actualColumns = @($manifestRows[0].PSObject.Properties.Name)
    Assert-True -Value (@((Compare-Object -ReferenceObject $requiredColumns -DifferenceObject $actualColumns)).Count -eq 0) -Message 'Source manifest columns mismatch.'

    $resolvedRows = [Collections.Generic.List[object]]::new()
    foreach ($row in $manifestRows) {
        $relativeForward = Convert-ForwardPath -Path ([string]$row.RELATIVE_PATH)
        Assert-True -Value (-not [string]::IsNullOrWhiteSpace($relativeForward)) -Message 'Blank manifest path.'
        Assert-True -Value (-not [IO.Path]::IsPathRooted($relativeForward)) -Message "Rooted manifest path: $relativeForward"
        $segments = @($relativeForward -split '/')
        Assert-True -Value (@($segments | Where-Object { $_ -eq '..' -or $_ -eq '.' -or [string]::IsNullOrWhiteSpace($_) }).Count -eq 0) -Message "Unsafe manifest path: $relativeForward"
        Assert-True -Value ($relativeForward -notin @('PREMARKER_MANIFEST.csv', 'WSTOP.txt', 'PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')) -Message "Control path in material set: $relativeForward"
        $sourcePath = [IO.Path]::GetFullPath([IO.Path]::Combine($sourceRoot, (Convert-NativePath -ForwardPath $relativeForward)))
        Assert-True -Value ($sourcePath.StartsWith($sourceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) -Message "Path escapes source root: $relativeForward"
        Assert-True -Value (Test-Path -LiteralPath $sourcePath -PathType Leaf) -Message "Missing material: $relativeForward"
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        $sourceSha256 = Get-Sha256 -LiteralPath $sourcePath
        $manifestTicks = ([DateTime]::Parse([string]$row.LAST_WRITE_UTC, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind).ToUniversalTime()).Ticks
        Assert-True -Value ([int64]$row.BYTES -eq [int64]$sourceItem.Length) -Message "Byte mismatch: $relativeForward"
        Assert-True -Value ([string]$row.SHA256 -eq $sourceSha256) -Message "SHA mismatch: $relativeForward"
        Assert-True -Value ($manifestTicks -eq $sourceItem.LastWriteTimeUtc.Ticks) -Message "Last-write mismatch: $relativeForward"
        $resolvedRows.Add([pscustomobject]@{ relative_path = $relativeForward; source_path = $sourcePath; bytes = [int64]$sourceItem.Length; sha256 = $sourceSha256; creation_time_utc_ticks = [int64]$sourceItem.CreationTimeUtc.Ticks; last_write_time_utc_ticks = [int64]$sourceItem.LastWriteTimeUtc.Ticks })
    }
    $resolvedDuplicateGroups = @($resolvedRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 })
    Assert-True -Value ($resolvedDuplicateGroups.Count -eq 0) -Message 'Canonical material paths are not unique.'

    [IO.Directory]::CreateDirectory($destinationRoot) | Out-Null
    $copyRows = [Collections.Generic.List[object]]::new()
    foreach ($resolved in @($resolvedRows | Sort-Object -Property relative_path -CaseSensitive)) {
        $destinationPath = [IO.Path]::GetFullPath([IO.Path]::Combine($destinationRoot, (Convert-NativePath -ForwardPath $resolved.relative_path)))
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destinationPath)) | Out-Null
        Copy-Item -LiteralPath $resolved.source_path -Destination $destinationPath
        [IO.File]::SetAttributes($destinationPath, [IO.FileAttributes]::Archive)
        [IO.File]::SetCreationTimeUtc($destinationPath, [DateTime]::new($resolved.creation_time_utc_ticks, [DateTimeKind]::Utc))
        [IO.File]::SetLastWriteTimeUtc($destinationPath, [DateTime]::new($resolved.last_write_time_utc_ticks, [DateTimeKind]::Utc))
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $match = ([int64]$destinationItem.Length -eq $resolved.bytes -and (Get-Sha256 -LiteralPath $destinationPath) -eq $resolved.sha256 -and $destinationItem.CreationTimeUtc.Ticks -eq $resolved.creation_time_utc_ticks -and $destinationItem.LastWriteTimeUtc.Ticks -eq $resolved.last_write_time_utc_ticks)
        Assert-True -Value $match -Message "Copied identity mismatch: $($resolved.relative_path)"
        $copyRows.Add([pscustomobject]@{ relative_path = $resolved.relative_path; bytes = $resolved.bytes; sha256 = $resolved.sha256; source_creation_time_utc_ticks = $resolved.creation_time_utc_ticks; destination_creation_time_utc_ticks = [int64]$destinationItem.CreationTimeUtc.Ticks; source_last_write_time_utc_ticks = $resolved.last_write_time_utc_ticks; destination_last_write_time_utc_ticks = [int64]$destinationItem.LastWriteTimeUtc.Ticks; identity_match = $match })
    }

    $copyIdentityPath = [IO.Path]::Combine($destinationRoot, 'COPY_IDENTITY.csv')
    @($copyRows) | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -UseQuotes AsNeeded -Encoding utf8
    $copyIdentitySha256 = Get-Sha256 -LiteralPath $copyIdentityPath
    $copyMismatchCount = @($copyRows | Where-Object { -not $_.identity_match }).Count
    Assert-True -Value ($copyRows.Count -eq $expectedMaterialCount -and $copyMismatchCount -eq 0) -Message 'Copy identity closure failed.'

    $copyProvenancePath = [IO.Path]::Combine($destinationRoot, 'COPY_PROVENANCE.md')
    $provenance = @(
        'FORMAT_VERSION=2', "HANDOFF_ID=$handoffId", "OPERATION=$operation", "SOURCE_ROOT=$sourceRoot", "DESTINATION_ROOT=$destinationRoot",
        "SOURCE_PREMARKER_MANIFEST=$sourceManifest", "SOURCE_PREMARKER_MANIFEST_SHA256=$expectedSourceManifestSha256", "SOURCE_WSTOP=$sourceMarker", "SOURCE_WSTOP_SHA256=$expectedSourceMarkerSha256",
        "SOURCE_TREE_ITEM_COUNT=$($sourceSnapshotBefore.item_count)", "SOURCE_TREE_FILE_BYTES=$($sourceSnapshotBefore.file_bytes)", "SOURCE_TREE_CANONICAL_SHA256=$($sourceSnapshotBefore.canonical_sha256)",
        "MATERIAL_COUNT=$expectedMaterialCount", 'PATH_CANONICALIZATION=BACKSLASH_TO_FORWARD_SLASH', 'PRESERVED_IDENTITY=RELATIVE_PATH,BYTES,SHA256,CREATION_TIME_UTC_TICKS,LAST_WRITE_TIME_UTC_TICKS',
        "COPY_IDENTITY_SHA256=$copyIdentitySha256", "CONTROLLER_PATH=$controllerPath", "CONTROLLER_BYTES=$($controllerItem.Length)", "CONTROLLER_SHA256=$controllerSha256",
        'CONTENT_VERDICT=FAIL_TO_MAIN_SOURCE_SCOPE_PRESERVED', 'CONTROL_RESEAL_STATUS=AWAITING_FINAL_MARKER'
    )
    Write-TextNoBom -LiteralPath $copyProvenancePath -Text (($provenance -join "`n") + "`n")
    $copyProvenanceSha256 = Get-Sha256 -LiteralPath $copyProvenancePath

    $payloadPaths = @($resolvedRows | ForEach-Object { Convert-ForwardPath -Path ([string]$_.relative_path) }) + @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.md')
    $payloadDuplicateGroups = @($payloadPaths | Group-Object -Property { [string]$_ } | Where-Object { $_.Count -ne 1 })
    Assert-True -Value ($payloadPaths.Count -eq $expectedPayloadCount -and $payloadDuplicateGroups.Count -eq 0) -Message 'Payload path model failed.'
    $payloadRows = [Collections.Generic.List[object]]::new()
    foreach ($relativePath in @($payloadPaths | Sort-Object -CaseSensitive)) {
        $payloadPath = [IO.Path]::Combine($destinationRoot, (Convert-NativePath -ForwardPath $relativePath))
        Assert-True -Value (Test-Path -LiteralPath $payloadPath -PathType Leaf) -Message "Missing payload: $relativePath"
        $payloadItem = Get-Item -LiteralPath $payloadPath -Force
        $payloadRows.Add([pscustomobject]@{ relative_path = $relativePath; bytes = [int64]$payloadItem.Length; sha256 = Get-Sha256 -LiteralPath $payloadPath; creation_time_utc_ticks = [int64]$payloadItem.CreationTimeUtc.Ticks; last_write_time_utc_ticks = [int64]$payloadItem.LastWriteTimeUtc.Ticks })
    }

    $payloadManifestPath = [IO.Path]::Combine($destinationRoot, 'PAYLOAD_MANIFEST.csv')
    @($payloadRows) | Export-Csv -LiteralPath $payloadManifestPath -NoTypeInformation -UseQuotes AsNeeded -Encoding utf8
    $payloadManifestSha256 = Get-Sha256 -LiteralPath $payloadManifestPath
    $payloadManifestRows = @(Import-Csv -LiteralPath $payloadManifestPath)
    $payloadManifestDuplicateGroups = @($payloadManifestRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 })
    Assert-True -Value ($payloadManifestRows.Count -eq $expectedPayloadCount -and $payloadManifestDuplicateGroups.Count -eq 0) -Message 'Payload manifest validation failed.'

    $sealAuditPath = [IO.Path]::Combine($destinationRoot, 'SEAL_AUDIT.json')
    $sealAudit = [ordered]@{
        format_version = 2; handoff_id = $handoffId; operation = $operation; content_verdict = 'FAIL_TO_MAIN_SOURCE_SCOPE_PRESERVED'; control_reseal_status = 'PREMARKER_IDENTITY_COMPLETE';
        source_root = $sourceRoot; destination_root = $destinationRoot; source_material_count = $expectedMaterialCount; payload_count = $expectedPayloadCount; control_count = $expectedControlCount; ordinary_count = $expectedOrdinaryCount;
        copy_identity_mismatch_count = $copyMismatchCount; payload_manifest_row_count = $payloadManifestRows.Count; payload_manifest_duplicate_count = $payloadManifestDuplicateGroups.Count;
        source_premarker_manifest_sha256 = $expectedSourceManifestSha256; source_wstop_sha256 = $expectedSourceMarkerSha256; copy_identity_sha256 = $copyIdentitySha256; copy_provenance_sha256 = $copyProvenanceSha256;
        payload_manifest_sha256 = $payloadManifestSha256; controller_sha256 = $controllerSha256; source_tree_snapshot_before_sha256 = $sourceSnapshotBefore.canonical_sha256; strict_mode_and_path_microtests = $microtests;
        path_canonicalization = 'BACKSLASH_TO_FORWARD_SLASH'; premarker_identity_verified = $true; final_marker_required = $true; postmarker_write_policy = 'ZERO_CONTENT_AND_ATTRIBUTE_WRITES'
    }
    Write-JsonNoBom -LiteralPath $sealAuditPath -Value $sealAudit
    $sealAuditSha256 = Get-Sha256 -LiteralPath $sealAuditPath

    $premarkerFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
    Assert-True -Value ($premarkerFiles.Count -eq ($expectedOrdinaryCount - 1)) -Message 'Premarker file count mismatch.'
    foreach ($file in $premarkerFiles) { Set-ReadOnly -LiteralPath $file.FullName }
    $premarkerDirectories = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force)
    foreach ($directory in @($premarkerDirectories | Sort-Object { $_.FullName.Length } -Descending)) { Set-ReadOnly -LiteralPath $directory.FullName }
    $premarkerWritableFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force | Where-Object { -not (Test-ReadOnly -Item $_) })
    $premarkerWritableDirectories = @($premarkerDirectories | ForEach-Object { Get-Item -LiteralPath $_.FullName -Force } | Where-Object { -not (Test-ReadOnly -Item $_) })
    Assert-True -Value ($premarkerWritableFiles.Count -eq 0 -and $premarkerWritableDirectories.Count -eq 0) -Message 'Premarker readonly gate failed.'

    $premarkerItems = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force)
    $maximumPremarkerTicks = (@($premarkerItems | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
    $futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(10).Ticks, ([int64]$maximumPremarkerTicks + [TimeSpan]::FromMinutes(5).Ticks))
    $markerLines = @(
        'FORMAT_VERSION=2', "HANDOFF_ID=$handoffId", "OPERATION=$operation", 'CONTENT_VERDICT=FAIL_TO_MAIN_SOURCE_SCOPE_PRESERVED', 'CONTROL_RESEAL_STATUS=SEALED_AWAIT_MAIN_ACCEPTANCE',
        "SOURCE_ROOT=$sourceRoot", "DESTINATION_ROOT=$destinationRoot", "SOURCE_MATERIAL_COUNT=$expectedMaterialCount", "PAYLOAD_COUNT=$expectedPayloadCount", "CONTROL_COUNT=$expectedControlCount", "ORDINARY_COUNT=$expectedOrdinaryCount",
        "SOURCE_PREMARKER_MANIFEST_SHA256=$expectedSourceManifestSha256", "SOURCE_WSTOP_SHA256=$expectedSourceMarkerSha256", "COPY_IDENTITY_SHA256=$copyIdentitySha256", "COPY_PROVENANCE_SHA256=$copyProvenanceSha256",
        "PAYLOAD_MANIFEST_SHA256=$payloadManifestSha256", "SEAL_AUDIT_SHA256=$sealAuditSha256", "CONTROLLER_SHA256=$controllerSha256", 'CONTROLLER_INVOCATION_COUNT=1', 'CONTROLLER_RETRY_COUNT=0',
        'PREMARKER_READONLY_VERIFIED=true', 'EXTERNAL_MARKER_STAGE=true', 'FINAL_MOVE_COUNT=1', 'POSTMARKER_ROOT_CONTENT_ATTRIBUTE_WRITES=0', "MARKER_TARGET_LAST_WRITE_UTC_TICKS=$futureTicks"
    )
    Assert-True -Value (@($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^=\r\n\t]+$' }).Count -eq 0) -Message 'Marker syntax failed.'
    Assert-True -Value (@($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object -Property { [string]$_ } | Where-Object { $_.Count -ne 1 }).Count -eq 0) -Message 'Marker duplicate key.'
    Write-TextNoBom -LiteralPath $stagedMarker -Text (($markerLines -join "`n") + "`n")
    [IO.File]::SetLastWriteTimeUtc($stagedMarker, [DateTime]::new($futureTicks, [DateTimeKind]::Utc))
    Set-ReadOnly -LiteralPath $stagedMarker
    $stagedItem = Get-Item -LiteralPath $stagedMarker -Force
    Assert-True -Value ((Test-ReadOnly -Item $stagedItem) -and $stagedItem.LastWriteTimeUtc.Ticks -eq $futureTicks) -Message 'External marker staging gate failed.'

    $targetMarker = [IO.Path]::Combine($destinationRoot, 'WRITE_STOPPED')
    Assert-True -Value (-not (Test-Path -LiteralPath $targetMarker)) -Message 'Destination marker already exists.'
    Move-Item -LiteralPath $stagedMarker -Destination $targetMarker

    $postmarkerSnapshot1 = Get-TreeSnapshot -Root $destinationRoot
    $ordinaryFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
    $allDirectories = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force)
    $writableFiles = @($ordinaryFiles | Where-Object { -not (Test-ReadOnly -Item $_) })
    $writableDirectories = @($allDirectories | ForEach-Object { Get-Item -LiteralPath $_.FullName -Force } | Where-Object { -not (Test-ReadOnly -Item $_) })
    $expectedOrdinarySet = @($payloadPaths + @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED') | ForEach-Object { Convert-ForwardPath -Path $_ } | Sort-Object -CaseSensitive)
    $actualOrdinarySet = @($ordinaryFiles | ForEach-Object { Convert-ForwardPath -Path (Get-RelativeForwardPath -Root $destinationRoot -FullName $_.FullName) } | Sort-Object -CaseSensitive)
    $ordinarySetDifference = @((Compare-Object -ReferenceObject $expectedOrdinarySet -DifferenceObject $actualOrdinarySet -CaseSensitive))
    Assert-True -Value ($ordinaryFiles.Count -eq $expectedOrdinaryCount -and $ordinarySetDifference.Count -eq 0 -and $writableFiles.Count -eq 0 -and $writableDirectories.Count -eq 0) -Message 'Final set/count/readonly gate failed.'
    $markerItem = Get-Item -LiteralPath $targetMarker -Force
    $itemsExcludingMarker = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force | Where-Object { $_.FullName -ne $markerItem.FullName })
    $atOrAfter = @($itemsExcludingMarker | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
    $maximumOtherTicks = (@($itemsExcludingMarker | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
    $marginTicks = $markerItem.LastWriteTimeUtc.Ticks - [int64]$maximumOtherTicks
    Assert-True -Value ($atOrAfter.Count -eq 0 -and $marginTicks -gt 0) -Message 'Marker order gate failed.'
    $postmarkerSnapshot2 = Get-TreeSnapshot -Root $destinationRoot
    Assert-True -Value ($postmarkerSnapshot1.canonical_sha256 -eq $postmarkerSnapshot2.canonical_sha256) -Message 'Postmarker mutation detected.'
    $sourceSnapshotAfter = Get-TreeSnapshot -Root $sourceRoot
    Assert-True -Value ($sourceSnapshotBefore.canonical_sha256 -eq $sourceSnapshotAfter.canonical_sha256) -Message 'Source root mutation detected.'

    $result = [ordered]@{
        format_version = 2; handoff_id = $handoffId; operation = $operation; status = 'CONTROLLER_SUCCESS'; controller_invocation_count = 1; controller_retry_count = 0;
        start_utc = $startUtc.ToString('o'); end_utc = [DateTime]::UtcNow.ToString('o'); source_root = $sourceRoot; destination_root = $destinationRoot;
        material_count = $expectedMaterialCount; payload_count = $expectedPayloadCount; control_count = $expectedControlCount; ordinary_count = $ordinaryFiles.Count;
        readonly_file_count = $ordinaryFiles.Count - $writableFiles.Count; readonly_directory_count = $allDirectories.Count - $writableDirectories.Count; copy_identity_mismatch_count = $copyMismatchCount; ordinary_set_difference_count = $ordinarySetDifference.Count;
        marker_path = $targetMarker; marker_sha256 = Get-Sha256 -LiteralPath $targetMarker; marker_last_write_utc_ticks = $markerItem.LastWriteTimeUtc.Ticks; marker_margin_ticks = $marginTicks;
        at_or_after_excluding_marker_count = $atOrAfter.Count; postmarker_snapshot_sha256 = $postmarkerSnapshot2.canonical_sha256; postmarker_content_attribute_write_count = 0;
        source_snapshot_before_sha256 = $sourceSnapshotBefore.canonical_sha256; source_snapshot_after_sha256 = $sourceSnapshotAfter.canonical_sha256;
        payload_manifest_sha256 = $payloadManifestSha256; seal_audit_sha256 = $sealAuditSha256; controller_path = $controllerPath; controller_bytes = $controllerItem.Length; controller_sha256 = $controllerSha256;
        strict_mode_and_path_microtests = $microtests
    }
    Write-JsonNoBom -LiteralPath $controllerResult -Value $result
    Write-Output ($result | ConvertTo-Json -Depth 12 -Compress)
}
catch {
    $failure = [ordered]@{ format_version = 2; handoff_id = $handoffId; operation = $operation; status = 'CONTROLLER_FAILURE_FIRST_ERROR_STOP'; controller_invocation_count = 1; controller_retry_count = 0; error = $_.Exception.Message; failed_utc = [DateTime]::UtcNow.ToString('o') }
    if (-not (Test-Path -LiteralPath $controllerResult)) { Write-JsonNoBom -LiteralPath $controllerResult -Value $failure }
    throw
}
