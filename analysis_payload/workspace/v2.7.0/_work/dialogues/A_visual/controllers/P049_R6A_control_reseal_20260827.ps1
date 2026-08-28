param(
    [Parameter(Mandatory = $true)]
    [string]$ExecutionGrant
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ExpectedGrant = 'P049_R6A_EVIDENCE_ONLY_CONTROL_RESEAL_EXPLICITLY_GRANTED'
$SourceRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6_SA3_FRESH_ISOLATED_R111_20260827')
$TargetRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R6A_SA3_R111_EVIDENCE_ONLY_CONTROL_RESEAL_20260827')
$ExpectedSourceCount = 34
$ExpectedSourceBytes = 4333519L
$ExpectedSourceSetSha256 = 'B77ADA737922FFA781C84AC7101F707E70C79C60EF33BA031729E8324D2830A9'
$ExpectedCanonicalByteLength = 4071
$MarkerPreparationPath = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\controllers\P049_R6A_WRITE_STOPPED_PREP_20260827.json')
$Utf8NoBom = [Text.UTF8Encoding]::new($false)

function Assert-True {
    param([bool]$Condition, [string]$Label)
    if (-not $Condition) { throw "ASSERT_FAIL: $Label" }
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativeForwardPath {
    param([string]$Root, [string]$Path)
    return [IO.Path]::GetRelativePath($Root, $Path).Replace([char]92, [char]47)
}

function Get-FileRows {
    param([string]$Root)
    $byPath = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
    foreach ($fullPath in [IO.Directory]::EnumerateFiles($Root, '*', [IO.SearchOption]::AllDirectories)) {
        $relativePath = Get-RelativeForwardPath -Root $Root -Path $fullPath
        Assert-True (-not $byPath.ContainsKey($relativePath)) "duplicate relative path $relativePath"
        $item = [IO.FileInfo]::new($fullPath)
        $byPath.Add($relativePath, [pscustomobject]@{
            relative_path = $relativePath
            full_path = $fullPath
            bytes = [int64]$item.Length
            sha256 = Get-Sha256 -Path $fullPath
            mtime_utc_ticks = $item.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)
        })
    }
    $keys = [string[]]$byPath.Keys
    [Array]::Sort($keys, [StringComparer]::Ordinal)
    return @($keys | ForEach-Object { $byPath[$_] })
}

function Get-CanonicalSetSha256 {
    param([object[]]$Rows)
    $builder = [Text.StringBuilder]::new()
    foreach ($row in $Rows) {
        [void]$builder.Append($row.relative_path)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.bytes.ToString([Globalization.CultureInfo]::InvariantCulture))
        [void]$builder.Append("`t")
        [void]$builder.Append($row.sha256)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.mtime_utc_ticks)
        [void]$builder.Append("`n")
    }
    $digest = [Security.Cryptography.SHA256]::HashData($Utf8NoBom.GetBytes($builder.ToString()))
    return [Convert]::ToHexString($digest)
}

function Get-CanonicalSetByteLength {
    param([object[]]$Rows)
    $builder = [Text.StringBuilder]::new()
    foreach ($row in $Rows) {
        [void]$builder.Append($row.relative_path)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.bytes.ToString([Globalization.CultureInfo]::InvariantCulture))
        [void]$builder.Append("`t")
        [void]$builder.Append($row.sha256)
        [void]$builder.Append("`t")
        [void]$builder.Append($row.mtime_utc_ticks)
        [void]$builder.Append("`n")
    }
    return $Utf8NoBom.GetByteCount($builder.ToString())
}

function Write-Utf8Json {
    param([string]$Path, [object]$Value, [int]$Depth = 12)
    $json = $Value | ConvertTo-Json -Depth $Depth
    [IO.File]::WriteAllText($Path, $json + "`n", $Utf8NoBom)
}

function Set-ReadOnlyAttribute {
    param([string]$Path)
    $attributes = [IO.File]::GetAttributes($Path)
    [IO.File]::SetAttributes($Path, $attributes -bor [IO.FileAttributes]::ReadOnly)
}

Assert-True ($PSVersionTable.PSVersion.Major -ge 7) 'PowerShell major version must be 7 or newer'
Assert-True ($ExecutionGrant -ceq $ExpectedGrant) 'execution grant token mismatch'
Assert-True ([IO.Directory]::Exists($SourceRoot)) 'source root missing'
Assert-True (-not [IO.Directory]::Exists($TargetRoot)) 'target directory must not exist'
Assert-True (-not [IO.File]::Exists($TargetRoot)) 'target file must not exist'
Assert-True (-not [IO.File]::Exists($MarkerPreparationPath)) 'external marker preparation path must not exist'
Assert-True (-not $SourceRoot.Contains('$')) 'source root contains unresolved placeholder'
Assert-True (-not $TargetRoot.Contains('$')) 'target root contains unresolved placeholder'

$sourceRootItemBefore = [IO.DirectoryInfo]::new($SourceRoot)
$sourceRootTicksBefore = $sourceRootItemBefore.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)
$sourceRootAttributesBefore = [int]$sourceRootItemBefore.Attributes
$sourceRows = @(Get-FileRows -Root $SourceRoot)
$sourceBytes = [int64](($sourceRows | Measure-Object -Property bytes -Sum).Sum)
$sourceSetSha256 = Get-CanonicalSetSha256 -Rows $sourceRows
$sourceCanonicalByteLength = Get-CanonicalSetByteLength -Rows $sourceRows
Assert-True ($sourceRows.Count -eq $ExpectedSourceCount) 'source material count mismatch'
Assert-True ($sourceBytes -eq $ExpectedSourceBytes) 'source material byte count mismatch'
Assert-True ($sourceSetSha256 -ceq $ExpectedSourceSetSha256) 'source canonical set SHA mismatch'
Assert-True ($sourceCanonicalByteLength -eq $ExpectedCanonicalByteLength) 'source canonical byte length mismatch'

[void][IO.Directory]::CreateDirectory($TargetRoot)
$copyIdentityRows = [Collections.Generic.List[object]]::new()
foreach ($row in $sourceRows) {
    $destinationPath = [IO.Path]::Combine($TargetRoot, $row.relative_path.Replace([char]47, [IO.Path]::DirectorySeparatorChar))
    $destinationParent = [IO.Path]::GetDirectoryName($destinationPath)
    [void][IO.Directory]::CreateDirectory($destinationParent)
    [IO.File]::Copy($row.full_path, $destinationPath, $false)
    [IO.File]::SetLastWriteTimeUtc($destinationPath, [DateTime]::new([int64]$row.mtime_utc_ticks, [DateTimeKind]::Utc))
    $destinationItem = [IO.FileInfo]::new($destinationPath)
    Assert-True ($destinationItem.Length -eq $row.bytes) "copied bytes mismatch: $($row.relative_path)"
    Assert-True ((Get-Sha256 -Path $destinationPath) -ceq $row.sha256) "copied SHA mismatch: $($row.relative_path)"
    Assert-True ($destinationItem.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture) -ceq $row.mtime_utc_ticks) "copied ticks mismatch: $($row.relative_path)"
    $copyIdentityRows.Add([pscustomobject]@{
        source_relative_path = $row.relative_path
        destination_relative_path = $row.relative_path
        bytes = $row.bytes.ToString([Globalization.CultureInfo]::InvariantCulture)
        sha256 = $row.sha256
        mtime_utc_ticks = $row.mtime_utc_ticks
    })
}

$copyIdentityPath = [IO.Path]::Combine($TargetRoot, 'COPY_IDENTITY.csv')
$copyIdentityCsv = $copyIdentityRows | ConvertTo-Csv -NoTypeInformation
[IO.File]::WriteAllLines($copyIdentityPath, [string[]]$copyIdentityCsv, $Utf8NoBom)

$copyProvenancePath = [IO.Path]::Combine($TargetRoot, 'COPY_PROVENANCE.json')
$copyProvenance = [ordered]@{
    handoff_id = 'A-R111-P049-SA3-FRESH-ISOLATED-20260827'
    operation = 'R6A_EVIDENCE_ONLY_CONTROL_RESEAL'
    execution_grant = $ExpectedGrant
    source_root = $SourceRoot
    target_root = $TargetRoot
    source_material_count = $sourceRows.Count
    source_material_bytes = $sourceBytes
    source_canonical_set_sha256 = $sourceSetSha256
    source_canonical_byte_length = $sourceCanonicalByteLength
    source_root_mtime_utc_ticks_before = $sourceRootTicksBefore
    source_root_attributes_before = $sourceRootAttributesBefore
    copy_identity_rows = $copyIdentityRows.Count
    controller_host = $PSHOME
    controller_ps_version = $PSVersionTable.PSVersion.ToString()
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
Write-Utf8Json -Path $copyProvenancePath -Value $copyProvenance

$payloadRows = @(Get-FileRows -Root $TargetRoot)
Assert-True ($payloadRows.Count -eq 36) 'final payload count before controls must be 36'
$payloadPaths = [string[]]$payloadRows.relative_path
Assert-True (($payloadPaths | Where-Object { $_ -in @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED.json') }).Count -eq 0) 'control name present in payload'

$manifestPath = [IO.Path]::Combine($TargetRoot, 'PAYLOAD_MANIFEST.json')
$manifestValue = [ordered]@{
    schema_version = 1
    handoff_id = 'A-R111-P049-SA3-FRESH-ISOLATED-20260827'
    operation = 'R6A_EVIDENCE_ONLY_CONTROL_RESEAL'
    root = $TargetRoot
    payload_count = $payloadRows.Count
    payload_bytes = [int64](($payloadRows | Measure-Object -Property bytes -Sum).Sum)
    files = @($payloadRows | ForEach-Object {
        [ordered]@{
            relative_path = $_.relative_path
            bytes = $_.bytes.ToString([Globalization.CultureInfo]::InvariantCulture)
            sha256 = $_.sha256
            mtime_utc_ticks = $_.mtime_utc_ticks
        }
    })
}
Write-Utf8Json -Path $manifestPath -Value $manifestValue -Depth 16
$manifestReadback = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json -DateKind String
Assert-True ([int]$manifestReadback.payload_count -eq 36) 'manifest payload count readback mismatch'
Assert-True (@($manifestReadback.files).Count -eq 36) 'manifest row count readback mismatch'

$sourceRowsAfter = @(Get-FileRows -Root $SourceRoot)
$sourceSetShaAfter = Get-CanonicalSetSha256 -Rows $sourceRowsAfter
$sourceRootItemAfter = [IO.DirectoryInfo]::new($SourceRoot)
Assert-True ($sourceRowsAfter.Count -eq $ExpectedSourceCount) 'source count changed during copy'
Assert-True (([int64](($sourceRowsAfter | Measure-Object -Property bytes -Sum).Sum)) -eq $ExpectedSourceBytes) 'source bytes changed during copy'
Assert-True ($sourceSetShaAfter -ceq $ExpectedSourceSetSha256) 'source canonical identity changed during copy'
Assert-True ($sourceRootItemAfter.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture) -ceq $sourceRootTicksBefore) 'source root mtime changed during copy'
Assert-True ([int]$sourceRootItemAfter.Attributes -eq $sourceRootAttributesBefore) 'source root attributes changed during copy'

$sealAuditPath = [IO.Path]::Combine($TargetRoot, 'SEAL_AUDIT.json')
$sealAuditValue = [ordered]@{
    schema_version = 1
    handoff_id = 'A-R111-P049-SA3-FRESH-ISOLATED-20260827'
    operation = 'R6A_EVIDENCE_ONLY_CONTROL_RESEAL'
    source_count = $sourceRows.Count
    source_bytes = $sourceBytes
    source_set_sha256 = $sourceSetSha256
    source_canonical_byte_length = $sourceCanonicalByteLength
    source_zero_write_identity_pass = $true
    copied_material_count = $copyIdentityRows.Count
    copied_identity_mismatch_count = 0
    declared_final_payload_count = 36
    declared_final_control_count = 3
    declared_final_ordinary_count = 39
    manifest_payload_count = 36
    manifest_identity_mismatch_count = 0
    old_controls_copied_count = 0
    controller_invocation_count = 1
    controller_retry_count = 0
    child_process_count = 0
    tex_invocation_count = 0
    business_visual_object_pair_manual_semantic_rerun_count = 0
    target_root = $TargetRoot
    premarker_state = 'CLEAR'
    created_at_utc = [DateTime]::UtcNow.ToString('o')
}
Write-Utf8Json -Path $sealAuditPath -Value $sealAuditValue

$preMarkerFiles = @([IO.Directory]::EnumerateFiles($TargetRoot, '*', [IO.SearchOption]::AllDirectories))
Assert-True ($preMarkerFiles.Count -eq 38) 'premarker ordinary file count must be 38'
foreach ($filePath in $preMarkerFiles) { Set-ReadOnlyAttribute -Path $filePath }
$allDirectories = @([IO.Directory]::EnumerateDirectories($TargetRoot, '*', [IO.SearchOption]::AllDirectories))
[Array]::Sort($allDirectories, [Comparison[string]]{ param($left, $right) $right.Length.CompareTo($left.Length) })
foreach ($directoryPath in $allDirectories) { Set-ReadOnlyAttribute -Path $directoryPath }
Set-ReadOnlyAttribute -Path $TargetRoot

foreach ($filePath in $preMarkerFiles) {
    Assert-True (([IO.File]::GetAttributes($filePath) -band [IO.FileAttributes]::ReadOnly) -ne 0) "premarker file not readonly: $filePath"
}
foreach ($directoryPath in @($allDirectories) + @($TargetRoot)) {
    Assert-True (([IO.File]::GetAttributes($directoryPath) -band [IO.FileAttributes]::ReadOnly) -ne 0) "premarker directory not readonly: $directoryPath"
}

$maxPreMarkerTicks = ($preMarkerFiles | ForEach-Object { [IO.File]::GetLastWriteTimeUtc($_).Ticks } | Measure-Object -Maximum).Maximum
$markerTicks = [Math]::Max([DateTime]::UtcNow.AddSeconds(1).Ticks, [int64]$maxPreMarkerTicks + 1L)
$markerValue = [ordered]@{
    schema_version = 1
    handoff_id = 'A-R111-P049-SA3-FRESH-ISOLATED-20260827'
    operation = 'R6A_EVIDENCE_ONLY_CONTROL_RESEAL'
    target_root = $TargetRoot
    source_root = $SourceRoot
    result = 'EVIDENCE_ONLY_RESEAL_COMPLETE_PRESERVING_SA3_CONTENT_PASS_DIRECTION'
    requested_main_route = 'A_LOCAL_PASS_REVIEW'
    payload_count = 36
    control_count = 3
    ordinary_count = 39
    controller_invocation_count = 1
    controller_retry_count = 0
    final_root_content_operation = 'MOVE_PREPARED_WRITE_STOPPED_JSON_INTO_ROOT'
    no_root_writes_after_marker = $true
    marker_mtime_utc_ticks = $markerTicks.ToString([Globalization.CultureInfo]::InvariantCulture)
    sealed_at_utc = [DateTime]::new($markerTicks, [DateTimeKind]::Utc).ToString('o')
}
Write-Utf8Json -Path $MarkerPreparationPath -Value $markerValue
[IO.File]::SetLastWriteTimeUtc($MarkerPreparationPath, [DateTime]::new($markerTicks, [DateTimeKind]::Utc))
Set-ReadOnlyAttribute -Path $MarkerPreparationPath
$preparedMarkerSha256 = Get-Sha256 -Path $MarkerPreparationPath
$preparedMarkerBytes = [IO.FileInfo]::new($MarkerPreparationPath).Length
$markerFinalPath = [IO.Path]::Combine($TargetRoot, 'WRITE_STOPPED.json')
Assert-True (-not [IO.File]::Exists($markerFinalPath)) 'final marker already exists'

# This move is deliberately the final target-root content operation. No target-root
# path is read, written, or has attributes changed after this statement.
[IO.File]::Move($MarkerPreparationPath, $markerFinalPath, $false)

[pscustomobject]@{
    result = 'CONTROLLER_EXIT0'
    source_root = $SourceRoot
    target_root = $TargetRoot
    source_count = $sourceRows.Count
    source_bytes = $sourceBytes
    source_set_sha256 = $sourceSetSha256
    source_canonical_byte_length = $sourceCanonicalByteLength
    payload_count = 36
    control_count = 3
    ordinary_count = 39
    marker_relative_path = 'WRITE_STOPPED.json'
    marker_bytes = $preparedMarkerBytes
    marker_sha256 = $preparedMarkerSha256
    marker_mtime_utc_ticks = $markerTicks.ToString([Globalization.CultureInfo]::InvariantCulture)
    invocation_count = 1
    retry_count = 0
} | ConvertTo-Json -Depth 6
