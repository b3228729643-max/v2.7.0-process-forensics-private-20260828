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

function Assert-True { param([Parameter(Mandatory)][bool]$Value, [Parameter(Mandatory)][string]$Message) if (-not $Value) { throw $Message } }
function Get-Sha256 { param([Parameter(Mandatory)][string]$LiteralPath) (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant() }
function Write-TextNoBom { param([Parameter(Mandatory)][string]$LiteralPath, [Parameter(Mandatory)][string]$Text) [IO.File]::WriteAllText($LiteralPath, $Text, $utf8NoBom) }
function Write-JsonNoBom { param([Parameter(Mandatory)][string]$LiteralPath, [Parameter(Mandatory)]$Value) Write-TextNoBom -LiteralPath $LiteralPath -Text (($Value | ConvertTo-Json -Depth 12) + "`n") }
function Convert-ForwardPath { param([Parameter(Mandatory)][string]$Path) $Path.Replace('\', '/') }
function Convert-NativePath { param([Parameter(Mandatory)][string]$ForwardPath) $ForwardPath.Replace('/', [IO.Path]::DirectorySeparatorChar) }
function Get-RelativeForwardPath { param([Parameter(Mandatory)][string]$Root, [Parameter(Mandatory)][string]$FullName) Convert-ForwardPath -Path ([IO.Path]::GetRelativePath($Root, $FullName)) }

function Get-CanonicalHash {
    param([Parameter(Mandatory)][string[]]$Rows)
    $text = if ($Rows.Count -eq 0) { '' } else { ($Rows -join "`n") + "`n" }
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($utf8NoBom.GetBytes($text)))
}

function Get-TreeSnapshot {
    param([Parameter(Mandatory)][string]$Root)
    $rootItem = Get-Item -LiteralPath $Root -Force
    $items = @($rootItem) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
    $rows = [Collections.Generic.List[string]]::new(); $fileBytes = [int64]0
    foreach ($item in @($items | Sort-Object -Property FullName)) {
        $relative = if ($item.FullName -eq $rootItem.FullName) { '.' } else { Get-RelativeForwardPath -Root $Root -FullName $item.FullName }
        Assert-True -Value (-not ($relative.Contains("`t") -or $relative.Contains("`r") -or $relative.Contains("`n"))) -Message "Unsafe snapshot path: $relative"
        if ($item.PSIsContainer) { $kind = 'D'; $bytes = [int64]0; $sha = '' } else { $kind = 'F'; $bytes = [int64]$item.Length; $sha = Get-Sha256 -LiteralPath $item.FullName; $fileBytes += $bytes }
        $rows.Add(("{0}`t{1}`t{2}`t{3}`t{4}`t{5}`t{6}" -f $kind, $relative, $bytes, $sha, $item.CreationTimeUtc.Ticks, $item.LastWriteTimeUtc.Ticks, [int64]$item.Attributes))
    }
    $ordered = @($rows | Sort-Object -CaseSensitive)
    [pscustomobject]@{ item_count = $ordered.Count; file_bytes = $fileBytes; canonical_sha256 = Get-CanonicalHash -Rows $ordered }
}

function Test-ReadOnly { param([Parameter(Mandatory)]$Item) (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) }

function Read-KeyValueFile {
    param([Parameter(Mandatory)][string]$LiteralPath)
    $raw = [IO.File]::ReadAllBytes($LiteralPath)
    Assert-True -Value (-not ($raw.Length -ge 3 -and $raw[0] -eq 0xEF -and $raw[1] -eq 0xBB -and $raw[2] -eq 0xBF)) -Message "BOM forbidden: $LiteralPath"
    $lines = @([IO.File]::ReadAllLines($LiteralPath, $utf8NoBom))
    Assert-True -Value ($lines.Count -gt 0 -and @($lines | Where-Object { $_ -notmatch '^[^=\s]+=[^=\r\n\t]+$' }).Count -eq 0) -Message "Invalid key-value file: $LiteralPath"
    $pairs = [ordered]@{}
    foreach ($line in $lines) { $parts = $line -split '=', 2; Assert-True -Value (-not $pairs.Contains($parts[0])) -Message "Duplicate key: $LiteralPath"; $pairs[$parts[0]] = $parts[1] }
    [pscustomobject]@{ lines = $lines; pairs = $pairs }
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
    $startUtc = [DateTime]::UtcNow; $microtests = Invoke-Microtests
    Assert-True -Value ($PSVersionTable.PSVersion.Major -ge 7) -Message 'PowerShell 7 or later is required.'
    Assert-True -Value (Test-Path -LiteralPath $sourceRoot -PathType Container) -Message 'Source root missing.'
    Assert-True -Value (Test-Path -LiteralPath $destinationRoot -PathType Container) -Message 'Destination root missing.'
    Assert-True -Value (Test-Path -LiteralPath $controllerResult -PathType Leaf) -Message 'Controller result missing.'
    Assert-True -Value (-not (Test-Path -LiteralPath $auditorResult)) -Message 'Auditor result already exists.'
    Assert-True -Value ((Get-Sha256 -LiteralPath $sourceManifest) -eq $expectedSourceManifestSha256 -and (Get-Sha256 -LiteralPath $sourceMarker) -eq $expectedSourceMarkerSha256) -Message 'Source control identity mismatch.'

    $auditorPath = $PSCommandPath; $auditorItem = Get-Item -LiteralPath $auditorPath -Force; $auditorSha256 = Get-Sha256 -LiteralPath $auditorPath
    $controllerData = Get-Content -LiteralPath $controllerResult -Raw | ConvertFrom-Json
    Assert-True -Value ($controllerData.status -eq 'CONTROLLER_SUCCESS' -and $controllerData.controller_invocation_count -eq 1 -and $controllerData.controller_retry_count -eq 0) -Message 'Controller result contract mismatch.'
    $sourceSnapshot = Get-TreeSnapshot -Root $sourceRoot
    Assert-True -Value ($sourceSnapshot.canonical_sha256 -eq $controllerData.source_snapshot_before_sha256 -and $sourceSnapshot.canonical_sha256 -eq $controllerData.source_snapshot_after_sha256) -Message 'Source root changed.'

    $copyIdentityPath = [IO.Path]::Combine($destinationRoot, 'COPY_IDENTITY.csv'); $copyProvenancePath = [IO.Path]::Combine($destinationRoot, 'COPY_PROVENANCE.md')
    $payloadManifestPath = [IO.Path]::Combine($destinationRoot, 'PAYLOAD_MANIFEST.csv'); $sealAuditPath = [IO.Path]::Combine($destinationRoot, 'SEAL_AUDIT.json'); $markerPath = [IO.Path]::Combine($destinationRoot, 'WRITE_STOPPED')
    foreach ($path in @($copyIdentityPath, $copyProvenancePath, $payloadManifestPath, $sealAuditPath, $markerPath)) { Assert-True -Value (Test-Path -LiteralPath $path -PathType Leaf) -Message "Missing required file: $path" }

    $copyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
    Assert-True -Value ($copyRows.Count -eq $expectedMaterialCount) -Message 'Copy row count mismatch.'
    $copyDuplicateGroups = @($copyRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 })
    Assert-True -Value ($copyDuplicateGroups.Count -eq 0) -Message 'Copy duplicate paths.'
    $copyMismatchCount = 0
    foreach ($copyRow in $copyRows) {
        $relativeForward = Convert-ForwardPath -Path ([string]$copyRow.relative_path)
        $native = Convert-NativePath -ForwardPath $relativeForward
        $sourcePath = [IO.Path]::Combine($sourceRoot, $native); $destinationPath = [IO.Path]::Combine($destinationRoot, $native)
        Assert-True -Value (Test-Path -LiteralPath $sourcePath -PathType Leaf) -Message "Source material missing: $relativeForward"
        Assert-True -Value (Test-Path -LiteralPath $destinationPath -PathType Leaf) -Message "Destination material missing: $relativeForward"
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force; $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $match = ([int64]$copyRow.bytes -eq [int64]$sourceItem.Length -and [int64]$copyRow.bytes -eq [int64]$destinationItem.Length -and [string]$copyRow.sha256 -eq (Get-Sha256 -LiteralPath $sourcePath) -and [string]$copyRow.sha256 -eq (Get-Sha256 -LiteralPath $destinationPath) -and [int64]$copyRow.source_creation_time_utc_ticks -eq $sourceItem.CreationTimeUtc.Ticks -and [int64]$copyRow.destination_creation_time_utc_ticks -eq $destinationItem.CreationTimeUtc.Ticks -and [int64]$copyRow.source_last_write_time_utc_ticks -eq $sourceItem.LastWriteTimeUtc.Ticks -and [int64]$copyRow.destination_last_write_time_utc_ticks -eq $destinationItem.LastWriteTimeUtc.Ticks -and [string]$copyRow.identity_match -eq 'True')
        if (-not $match) { $copyMismatchCount++ }
    }
    Assert-True -Value ($copyMismatchCount -eq 0) -Message 'Copy identity mismatch.'

    $payloadRows = @(Import-Csv -LiteralPath $payloadManifestPath)
    Assert-True -Value ($payloadRows.Count -eq $expectedPayloadCount) -Message 'Payload manifest row count mismatch.'
    $payloadDuplicateGroups = @($payloadRows | Group-Object -Property { [string]$_.relative_path } | Where-Object { $_.Count -ne 1 })
    Assert-True -Value ($payloadDuplicateGroups.Count -eq 0) -Message 'Payload duplicate paths.'
    $manifestMismatchCount = 0
    foreach ($payloadRow in $payloadRows) {
        $relativeForward = Convert-ForwardPath -Path ([string]$payloadRow.relative_path)
        $path = [IO.Path]::Combine($destinationRoot, (Convert-NativePath -ForwardPath $relativeForward))
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestMismatchCount++; continue }
        $item = Get-Item -LiteralPath $path -Force
        if (-not ([int64]$payloadRow.bytes -eq [int64]$item.Length -and [string]$payloadRow.sha256 -eq (Get-Sha256 -LiteralPath $path) -and [int64]$payloadRow.creation_time_utc_ticks -eq $item.CreationTimeUtc.Ticks -and [int64]$payloadRow.last_write_time_utc_ticks -eq $item.LastWriteTimeUtc.Ticks)) { $manifestMismatchCount++ }
    }
    Assert-True -Value ($manifestMismatchCount -eq 0) -Message 'Payload manifest identity mismatch.'

    $actualFiles = @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
    $expectedPayloadSet = @($payloadRows | ForEach-Object { Convert-ForwardPath -Path ([string]$_.relative_path) } | Sort-Object -CaseSensitive)
    $expectedOrdinarySet = @($expectedPayloadSet + @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED') | ForEach-Object { Convert-ForwardPath -Path $_ } | Sort-Object -CaseSensitive)
    $actualOrdinarySet = @($actualFiles | ForEach-Object { Convert-ForwardPath -Path (Get-RelativeForwardPath -Root $destinationRoot -FullName $_.FullName) } | Sort-Object -CaseSensitive)
    $ordinarySetDifference = @((Compare-Object -ReferenceObject $expectedOrdinarySet -DifferenceObject $actualOrdinarySet -CaseSensitive))
    Assert-True -Value ($actualFiles.Count -eq $expectedOrdinaryCount -and $ordinarySetDifference.Count -eq 0) -Message 'Canonical ordinary set mismatch.'

    $allDirectories = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force)
    $writableFiles = @($actualFiles | Where-Object { -not (Test-ReadOnly -Item $_) }); $writableDirectories = @($allDirectories | ForEach-Object { Get-Item -LiteralPath $_.FullName -Force } | Where-Object { -not (Test-ReadOnly -Item $_) })
    Assert-True -Value ($writableFiles.Count -eq 0 -and $writableDirectories.Count -eq 0) -Message 'Readonly audit failed.'

    $markerData = Read-KeyValueFile -LiteralPath $markerPath
    $requiredMarkerKeys = @('FORMAT_VERSION','HANDOFF_ID','OPERATION','CONTENT_VERDICT','CONTROL_RESEAL_STATUS','SOURCE_ROOT','DESTINATION_ROOT','SOURCE_MATERIAL_COUNT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','SOURCE_PREMARKER_MANIFEST_SHA256','SOURCE_WSTOP_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','CONTROLLER_SHA256','CONTROLLER_INVOCATION_COUNT','CONTROLLER_RETRY_COUNT','PREMARKER_READONLY_VERIFIED','EXTERNAL_MARKER_STAGE','FINAL_MOVE_COUNT','POSTMARKER_ROOT_CONTENT_ATTRIBUTE_WRITES','MARKER_TARGET_LAST_WRITE_UTC_TICKS')
    $markerKeyDifference = @((Compare-Object -ReferenceObject $requiredMarkerKeys -DifferenceObject @($markerData.pairs.Keys)))
    Assert-True -Value ($markerKeyDifference.Count -eq 0 -and $markerData.pairs['HANDOFF_ID'] -eq $handoffId -and $markerData.pairs['OPERATION'] -eq $operation) -Message 'Marker identity/key mismatch.'
    Assert-True -Value ([int]$markerData.pairs['SOURCE_MATERIAL_COUNT'] -eq $expectedMaterialCount -and [int]$markerData.pairs['PAYLOAD_COUNT'] -eq $expectedPayloadCount -and [int]$markerData.pairs['CONTROL_COUNT'] -eq $expectedControlCount -and [int]$markerData.pairs['ORDINARY_COUNT'] -eq $expectedOrdinaryCount) -Message 'Marker count model mismatch.'
    Assert-True -Value ($markerData.pairs['COPY_IDENTITY_SHA256'] -eq (Get-Sha256 -LiteralPath $copyIdentityPath) -and $markerData.pairs['COPY_PROVENANCE_SHA256'] -eq (Get-Sha256 -LiteralPath $copyProvenancePath) -and $markerData.pairs['PAYLOAD_MANIFEST_SHA256'] -eq (Get-Sha256 -LiteralPath $payloadManifestPath) -and $markerData.pairs['SEAL_AUDIT_SHA256'] -eq (Get-Sha256 -LiteralPath $sealAuditPath)) -Message 'Marker hash binding mismatch.'
    $sealAudit = Get-Content -LiteralPath $sealAuditPath -Raw | ConvertFrom-Json
    Assert-True -Value ($sealAudit.source_material_count -eq $expectedMaterialCount -and $sealAudit.payload_count -eq $expectedPayloadCount -and $sealAudit.control_count -eq $expectedControlCount -and $sealAudit.ordinary_count -eq $expectedOrdinaryCount) -Message 'Seal audit count mismatch.'
    $provenance = Read-KeyValueFile -LiteralPath $copyProvenancePath
    Assert-True -Value ($provenance.pairs['SOURCE_ROOT'] -eq $sourceRoot -and $provenance.pairs['DESTINATION_ROOT'] -eq $destinationRoot -and $provenance.pairs['PATH_CANONICALIZATION'] -eq 'BACKSLASH_TO_FORWARD_SLASH') -Message 'Provenance mismatch.'

    $markerItem = Get-Item -LiteralPath $markerPath -Force
    $itemsExcludingMarker = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force | Where-Object { $_.FullName -ne $markerItem.FullName })
    $atOrAfter = @($itemsExcludingMarker | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
    $maximumOtherTicks = (@($itemsExcludingMarker | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
    $marginTicks = $markerItem.LastWriteTimeUtc.Ticks - [int64]$maximumOtherTicks
    Assert-True -Value ($atOrAfter.Count -eq 0 -and $marginTicks -gt 0) -Message 'Marker ordering failed.'

    $jsonParseFailureCount = 0
    foreach ($file in @($actualFiles | Where-Object { $_.Extension -eq '.json' })) { try { Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $jsonParseFailureCount++ } }
    $csvParseFailureCount = 0
    foreach ($file in @($actualFiles | Where-Object { $_.Extension -eq '.csv' })) { try { @(Import-Csv -LiteralPath $file.FullName) | Out-Null } catch { $csvParseFailureCount++ } }
    Assert-True -Value ($jsonParseFailureCount -eq 0 -and $csvParseFailureCount -eq 0) -Message 'Structured parse failed.'
    $alternateDataStreamCount = 0
    foreach ($file in $actualFiles) { $alternateDataStreamCount += @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object { $_.Stream -ne ':$DATA' }).Count }
    $destinationItems = @((Get-Item -LiteralPath $destinationRoot -Force)) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force)
    $cacheArtifactCount = @($destinationItems | Where-Object { $_.Name -match '(?i)(\.pyc$|^__pycache__$|\.cache$|thumbs\.db$|desktop\.ini$)' }).Count
    $reparsePointCount = @($destinationItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
    Assert-True -Value ($alternateDataStreamCount -eq 0 -and $cacheArtifactCount -eq 0 -and $reparsePointCount -eq 0) -Message 'Hygiene audit failed.'

    $destinationSnapshot = Get-TreeSnapshot -Root $destinationRoot
    Assert-True -Value ($destinationSnapshot.canonical_sha256 -eq $controllerData.postmarker_snapshot_sha256) -Message 'Postmarker destination mutation.'
    $sourceSnapshotAfter = Get-TreeSnapshot -Root $sourceRoot
    Assert-True -Value ($sourceSnapshotAfter.canonical_sha256 -eq $controllerData.source_snapshot_before_sha256) -Message 'Source root mutation.'

    $result = [ordered]@{
        format_version = 2; handoff_id = $handoffId; operation = $operation; status = 'AUDIT_PASS_EVIDENCE_ONLY_CONTROL_RESEAL_AWAIT_MAIN_ACCEPTANCE'; auditor_invocation_count = 1; auditor_retry_count = 0;
        start_utc = $startUtc.ToString('o'); end_utc = [DateTime]::UtcNow.ToString('o'); source_root = $sourceRoot; destination_root = $destinationRoot;
        material_count = $expectedMaterialCount; payload_count = $expectedPayloadCount; control_count = $expectedControlCount; ordinary_count = $actualFiles.Count; directory_count_including_root = $allDirectories.Count;
        readonly_file_count = $actualFiles.Count - $writableFiles.Count; readonly_directory_count = $allDirectories.Count - $writableDirectories.Count; copy_identity_mismatch_count = $copyMismatchCount;
        payload_manifest_mismatch_count = $manifestMismatchCount; ordinary_set_difference_count = $ordinarySetDifference.Count; marker_line_count = $markerData.lines.Count; marker_margin_ticks = $marginTicks;
        at_or_after_excluding_marker_count = $atOrAfter.Count; postmarker_content_attribute_write_count = 0; alternate_data_stream_count = $alternateDataStreamCount; cache_artifact_count = $cacheArtifactCount; reparse_point_count = $reparsePointCount;
        json_parse_failure_count = $jsonParseFailureCount; csv_parse_failure_count = $csvParseFailureCount; destination_snapshot_sha256 = $destinationSnapshot.canonical_sha256; source_snapshot_sha256 = $sourceSnapshotAfter.canonical_sha256;
        payload_manifest_sha256 = Get-Sha256 -LiteralPath $payloadManifestPath; seal_audit_sha256 = Get-Sha256 -LiteralPath $sealAuditPath; marker_sha256 = Get-Sha256 -LiteralPath $markerPath;
        auditor_path = $auditorPath; auditor_bytes = $auditorItem.Length; auditor_sha256 = $auditorSha256; strict_mode_and_path_microtests = $microtests
    }
    Write-JsonNoBom -LiteralPath $auditorResult -Value $result
    Write-Output ($result | ConvertTo-Json -Depth 12 -Compress)
}
catch {
    $failure = [ordered]@{ format_version = 2; handoff_id = $handoffId; operation = $operation; status = 'AUDITOR_FAILURE_FIRST_ERROR_STOP'; auditor_invocation_count = 1; auditor_retry_count = 0; error = $_.Exception.Message; failed_utc = [DateTime]::UtcNow.ToString('o') }
    if (-not (Test-Path -LiteralPath $auditorResult)) { Write-JsonNoBom -LiteralPath $auditorResult -Value $failure }
    throw
}
