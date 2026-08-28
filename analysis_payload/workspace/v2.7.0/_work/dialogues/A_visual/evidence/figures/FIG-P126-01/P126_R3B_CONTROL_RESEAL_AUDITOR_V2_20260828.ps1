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
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_CONTROL_RESEAL_CONTROLLER_RESULT_V2_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3B_CONTROL_RESEAL_AUDIT_V2_20260828.json'
$oldControlNames = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$newControlNames = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$expectedOldManifestSha = '405541B02D962FD75161DAEBB41C067955D7B99B992DD1F14A7399D3A6EB0D7E'
$requiredFiveFields = @('relative_path', 'bytes', 'sha256', 'creation_time_utc_ticks', 'last_write_time_utc_ticks')

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

function Get-RequiredPropertyValue([psobject]$Row, [string]$Name) {
    $matches = @($Row.PSObject.Properties | Where-Object { $_.Name -ceq $Name })
    if ($matches.Count -ne 1) { throw "required property missing or duplicated: $Name" }
    $value = [string]$matches[0].Value
    if ([string]::IsNullOrWhiteSpace($value)) { throw "required property blank: $Name" }
    return $value
}

function Add-Error([Collections.Generic.List[string]]$Errors, [string]$Message) {
    $Errors.Add($Message)
}

if (Test-Path -LiteralPath $auditResultPath) { throw 'R3B auditor result already exists' }
if (Test-Path -LiteralPath $stagePath) { throw 'R3B external marker stage still exists' }
if (-not (Test-Path -LiteralPath $destinationRoot -PathType Container)) { throw 'R3B destination root missing' }
if ((Get-FileSha $oldManifestPath) -ne $expectedOldManifestSha) { throw 'old manifest SHA mismatch' }
$errors = [System.Collections.Generic.List[string]]::new()
$controllerResult = Get-Content -LiteralPath $controllerResultPath -Raw -Encoding utf8 | ConvertFrom-Json
$sourceSnapshotBeforeAudit = Get-TreeSnapshot $sourceRoot
$destinationSnapshotBeforeAudit = Get-TreeSnapshot $destinationRoot

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

if ($oldRows.Count -ne 205) { Add-Error $errors "old rows=$($oldRows.Count)" }
if ($copyRows.Count -ne 205) { Add-Error $errors "copy rows=$($copyRows.Count)" }
if ($manifestRows.Count -ne 207) { Add-Error $errors "manifest rows=$($manifestRows.Count)" }

$oldDictionary = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($row in $oldRows) {
    foreach ($field in $requiredFiveFields) { $null = Get-RequiredPropertyValue $row $field }
    $relative = Get-CanonicalRelative ([string]$row.relative_path)
    if ($oldDictionary.ContainsKey($relative)) { Add-Error $errors "old duplicate path $relative"; continue }
    $oldDictionary.Add($relative, [pscustomobject][ordered]@{
        relative_path = $relative
        bytes = [int64]$row.bytes
        sha256 = ([string]$row.sha256).ToUpperInvariant()
        creation_time_utc_ticks = [int64]$row.creation_time_utc_ticks
        last_write_time_utc_ticks = [int64]$row.last_write_time_utc_ticks
    })
}
$copyDictionary = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($row in $copyRows) {
    foreach ($field in $requiredFiveFields) { $null = Get-RequiredPropertyValue $row $field }
    $relative = Get-CanonicalRelative ([string]$row.relative_path)
    if ($copyDictionary.ContainsKey($relative)) { Add-Error $errors "copy duplicate path $relative"; continue }
    $copyDictionary.Add($relative, $row)
}
if ($oldDictionary.Count -ne 205) { Add-Error $errors "old dictionary count=$($oldDictionary.Count)" }
if ($copyDictionary.Count -ne 205) { Add-Error $errors "copy dictionary count=$($copyDictionary.Count)" }
$oldPathSet = @($oldDictionary.Keys | Sort-Object -CaseSensitive)
$copyPathSet = @($copyDictionary.Keys | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $oldPathSet -DifferenceObject $copyPathSet -CaseSensitive).Count -ne 0) { Add-Error $errors 'old/copy ordinal path set mismatch' }
foreach ($controlName in $oldControlNames) {
    if ($copyDictionary.ContainsKey($controlName)) { Add-Error $errors "old control copied: $controlName" }
}

foreach ($relative in $oldDictionary.Keys) {
    if (-not $copyDictionary.ContainsKey($relative)) { continue }
    $old = $oldDictionary[$relative]
    $copy = $copyDictionary[$relative]
    if ([int64]$copy.bytes -ne $old.bytes) { Add-Error $errors "old/copy bytes mismatch $relative" }
    if (([string]$copy.sha256).ToUpperInvariant() -cne $old.sha256) { Add-Error $errors "old/copy SHA mismatch $relative" }
    if ([int64]$copy.creation_time_utc_ticks -ne $old.creation_time_utc_ticks) { Add-Error $errors "old/copy creation mismatch $relative" }
    if ([int64]$copy.last_write_time_utc_ticks -ne $old.last_write_time_utc_ticks) { Add-Error $errors "old/copy last-write mismatch $relative" }
    $sourcePath = Resolve-UnderRoot $sourceRoot $relative
    $destinationPath = Resolve-UnderRoot $destinationRoot $relative
    if ([string]$copy.source_path -cne $sourcePath) { Add-Error $errors "copy source resolved path mismatch $relative" }
    if ([string]$copy.destination_path -cne $destinationPath) { Add-Error $errors "copy destination resolved path mismatch $relative" }
    foreach ($entry in @([pscustomobject]@{ label = 'source'; path = $sourcePath }, [pscustomobject]@{ label = 'destination'; path = $destinationPath })) {
        if (-not (Test-Path -LiteralPath $entry.path -PathType Leaf)) { Add-Error $errors "$($entry.label) missing $relative"; continue }
        $file = Get-Item -LiteralPath $entry.path -Force
        if ($file.Length -ne $old.bytes) { Add-Error $errors "$($entry.label) bytes mismatch $relative" }
        if ((Get-FileSha $entry.path) -cne $old.sha256) { Add-Error $errors "$($entry.label) SHA mismatch $relative" }
        if ($file.CreationTimeUtc.Ticks -ne $old.creation_time_utc_ticks) { Add-Error $errors "$($entry.label) creation mismatch $relative" }
        if ($file.LastWriteTimeUtc.Ticks -ne $old.last_write_time_utc_ticks) { Add-Error $errors "$($entry.label) last-write mismatch $relative" }
    }
}

$expectedAddedPayload = @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json')
$expectedPreservedFields = @('relative_path', 'bytes', 'sha256', 'creation_time_utc_ticks', 'last_write_time_utc_ticks')
$expectedProvenance = [ordered]@{
    schema = 'P126_R3B_COPY_PROVENANCE_V2'
    handoff_id = $handoffId
    operation = $operation
    source_root = [IO.Path]::GetFullPath($sourceRoot)
    destination_root = [IO.Path]::GetFullPath($destinationRoot)
    source_payload_manifest = [IO.Path]::GetFullPath($oldManifestPath)
    source_payload_manifest_sha256 = $expectedOldManifestSha
    source_root_snapshot_sha256 = [string]$controllerResult.source_root_snapshot_before_sha256
    copied_material_count = 205
    business_evidence_rerun = 0
}
foreach ($key in $expectedProvenance.Keys) {
    $property = @($provenance.PSObject.Properties | Where-Object { $_.Name -ceq $key })
    if ($property.Count -ne 1) { Add-Error $errors "provenance missing field $key"; continue }
    if ([string]$property[0].Value -cne [string]$expectedProvenance[$key]) { Add-Error $errors "provenance value mismatch $key" }
}
if ((@($provenance.added_payload) -join '|') -cne ($expectedAddedPayload -join '|')) { Add-Error $errors 'provenance added_payload mismatch' }
if ((@($provenance.preserved_fields) -join '|') -cne ($expectedPreservedFields -join '|')) { Add-Error $errors 'provenance preserved_fields mismatch' }

$expectedSealAudit = [ordered]@{
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
    manifest_sha256 = Get-FileSha $manifestPath
    copy_identity_sha256 = Get-FileSha $copyIdentityPath
    copy_provenance_sha256 = Get-FileSha $provenancePath
    source_root_snapshot_before_sha256 = [string]$controllerResult.source_root_snapshot_before_sha256
    copy_identity_errors = 0
    manifest_identity_errors = 0
    business_evidence_rerun = 0
}
foreach ($key in $expectedSealAudit.Keys) {
    $property = @($sealAudit.PSObject.Properties | Where-Object { $_.Name -ceq $key })
    if ($property.Count -ne 1) { Add-Error $errors "seal audit missing field $key"; continue }
    if ([string]$property[0].Value -cne [string]$expectedSealAudit[$key]) { Add-Error $errors "seal audit value mismatch $key" }
}
$preparedUtc = [DateTime]::MinValue
if (-not [DateTime]::TryParse([string]$sealAudit.prepared_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$preparedUtc)) { Add-Error $errors 'seal audit prepared_utc invalid' }

$manifestDictionary = [Collections.Generic.Dictionary[string, object]]::new([StringComparer]::Ordinal)
foreach ($row in $manifestRows) {
    foreach ($field in $requiredFiveFields) { $null = Get-RequiredPropertyValue $row $field }
    $relative = Get-CanonicalRelative ([string]$row.relative_path)
    if ($manifestDictionary.ContainsKey($relative)) { Add-Error $errors "manifest duplicate path $relative"; continue }
    $manifestDictionary.Add($relative, $row)
}
$actualPayloadFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { -not ($_.DirectoryName -eq $destinationRoot -and $newControlNames -contains $_.Name) })
$actualPayloadPaths = @($actualPayloadFiles | ForEach-Object { Get-RelativePath $destinationRoot $_.FullName } | Sort-Object -CaseSensitive)
$manifestPathSet = @($manifestDictionary.Keys | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $manifestPathSet -DifferenceObject $actualPayloadPaths -CaseSensitive).Count -ne 0) { Add-Error $errors 'manifest/FS payload set mismatch' }
foreach ($relative in $manifestDictionary.Keys) {
    $row = $manifestDictionary[$relative]
    $path = Resolve-UnderRoot $destinationRoot $relative
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Add-Error $errors "manifest file missing $relative"; continue }
    $file = Get-Item -LiteralPath $path -Force
    if ($file.Length -ne [int64]$row.bytes) { Add-Error $errors "manifest byte mismatch $relative" }
    if ((Get-FileSha $path) -cne ([string]$row.sha256).ToUpperInvariant()) { Add-Error $errors "manifest SHA mismatch $relative" }
    if ($file.CreationTimeUtc.Ticks -ne [int64]$row.creation_time_utc_ticks) { Add-Error $errors "manifest creation mismatch $relative" }
    if ($file.LastWriteTimeUtc.Ticks -ne [int64]$row.last_write_time_utc_ticks) { Add-Error $errors "manifest last-write mismatch $relative" }
}

$allFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force)
$allDirs = @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Directory -Recurse -Force))
$notReadonlyFiles = @($allFiles | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$notReadonlyDirs = @($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($allFiles.Count -ne 210) { Add-Error $errors "ordinary count=$($allFiles.Count)" }
if ($notReadonlyFiles.Count -ne 0) { Add-Error $errors "writable files=$($notReadonlyFiles.Count)" }
if ($notReadonlyDirs.Count -ne 0) { Add-Error $errors "writable dirs=$($notReadonlyDirs.Count)" }

$markerBytes = [IO.File]::ReadAllBytes($markerPath)
if ($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF) { Add-Error $errors 'marker has BOM' }
$markerText = [Text.Encoding]::UTF8.GetString($markerBytes)
if ($markerText.Contains("`t")) { Add-Error $errors 'marker has TAB' }
if ($markerText -match '(?i)PLACEHOLDER|TODO|\$\{|\$[A-Za-z_]|<[^>]+>') { Add-Error $errors 'marker has placeholder token' }
$markerLines = @($markerText -split "`r?`n" | Where-Object { $_.Length -gt 0 })
$badMarkerLines = @($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' })
$markerDictionary = [Collections.Generic.Dictionary[string, string]]::new([StringComparer]::Ordinal)
foreach ($line in $markerLines) {
    $parts = $line -split '=', 2
    if ($parts.Count -ne 2) { Add-Error $errors "marker line lacks one key/value split: $line"; continue }
    if ($markerDictionary.ContainsKey($parts[0])) { Add-Error $errors "duplicate marker key $($parts[0])" } else { $markerDictionary.Add($parts[0], $parts[1]) }
}
$expectedMarkerKeys = @(
    'HANDOFF_ID','OPERATION','VERDICT','ROOT','SOURCE_ROOT','COPIED_MATERIAL_COUNT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT',
    'OLD_PAYLOAD_MANIFEST_SHA256','SOURCE_ROOT_SNAPSHOT_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256',
    'SEAL_AUDIT_SHA256','HARD_DEFECT_ID','BUSINESS_EVIDENCE_RERUN','CONTROLLER_INVOCATION_COUNT','CONTROLLER_RETRY_COUNT',
    'AUDITOR_INVOCATION_BUDGET','MARKER_PREPARED_UTC','MARKER_LAST_WRITE_UTC'
)
if ($markerLines.Count -ne 22) { Add-Error $errors "marker physical lines=$($markerLines.Count)" }
if ($badMarkerLines.Count -ne 0) { Add-Error $errors "bad marker lines=$($badMarkerLines.Count)" }
$actualMarkerKeys = @($markerDictionary.Keys | Sort-Object -CaseSensitive)
$expectedMarkerKeysSorted = @($expectedMarkerKeys | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $expectedMarkerKeysSorted -DifferenceObject $actualMarkerKeys -CaseSensitive).Count -ne 0) { Add-Error $errors 'marker exact key set mismatch' }
$expectedMarkerValues = [ordered]@{
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
    SOURCE_ROOT_SNAPSHOT_SHA256 = [string]$controllerResult.source_root_snapshot_before_sha256
    COPY_IDENTITY_SHA256 = Get-FileSha $copyIdentityPath
    COPY_PROVENANCE_SHA256 = Get-FileSha $provenancePath
    PAYLOAD_MANIFEST_SHA256 = Get-FileSha $manifestPath
    SEAL_AUDIT_SHA256 = Get-FileSha $sealAuditPath
    HARD_DEFECT_ID = $hardDefectId
    BUSINESS_EVIDENCE_RERUN = '0'
    CONTROLLER_INVOCATION_COUNT = '1'
    CONTROLLER_RETRY_COUNT = '0'
    AUDITOR_INVOCATION_BUDGET = '1'
}
foreach ($key in $expectedMarkerValues.Keys) {
    if (-not $markerDictionary.ContainsKey($key)) { continue }
    if ($markerDictionary[$key] -cne [string]$expectedMarkerValues[$key]) { Add-Error $errors "marker value mismatch $key" }
}
$markerPreparedUtc = [DateTime]::MinValue
$markerLastWriteUtc = [DateTime]::MinValue
if (-not $markerDictionary.ContainsKey('MARKER_PREPARED_UTC') -or -not [DateTime]::TryParse($markerDictionary['MARKER_PREPARED_UTC'], [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$markerPreparedUtc)) { Add-Error $errors 'marker prepared UTC invalid' }
if (-not $markerDictionary.ContainsKey('MARKER_LAST_WRITE_UTC') -or -not [DateTime]::TryParse($markerDictionary['MARKER_LAST_WRITE_UTC'], [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$markerLastWriteUtc)) { Add-Error $errors 'marker last-write UTC invalid' }

$marker = Get-Item -LiteralPath $markerPath -Force
if ($markerLastWriteUtc.ToUniversalTime().Ticks -ne $marker.LastWriteTimeUtc.Ticks) { Add-Error $errors 'marker declared last-write does not equal FILETIME' }
if ($markerPreparedUtc.ToUniversalTime().Ticks -ge $markerLastWriteUtc.ToUniversalTime().Ticks) { Add-Error $errors 'marker prepared UTC is not before future FILETIME' }
$otherItems = @($allFiles | Where-Object { $_.FullName -ne $markerPath }) + $allDirs
$maxOtherTicks = Get-MaxLastWriteTicks $otherItems
$marginTicks = [int64]$marker.LastWriteTimeUtc.Ticks - $maxOtherTicks
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
if ($marginTicks -le 0) { Add-Error $errors "marker strict-latest margin=$marginTicks" }
if ($atOrAfter.Count -ne 0) { Add-Error $errors "at-or-after excluding marker=$($atOrAfter.Count)" }
if (Test-Path -LiteralPath $stagePath) { Add-Error $errors 'external marker stage remains' }

$expectedControllerResult = [ordered]@{
    schema = 'P126_R3B_CONTROL_RESEAL_CONTROLLER_RESULT_V2'
    handoff_id = $handoffId
    operation = $operation
    preserved_business_verdict = $preservedVerdict
    hard_defect_id = $hardDefectId
    invocation_count = 1
    retry_count = 0
    exit = 0
    natural = 'True'
    copied_material_count = 205
    old_controls_copied = 0
    payload_count = 207
    control_count = 3
    ordinary_count = 210
    directory_count_including_root = $allDirs.Count
    readonly_files = 210
    readonly_dirs = $allDirs.Count
    old_payload_manifest_sha256 = $expectedOldManifestSha
    copy_identity_sha256 = Get-FileSha $copyIdentityPath
    copy_provenance_sha256 = Get-FileSha $provenancePath
    payload_manifest_sha256 = Get-FileSha $manifestPath
    seal_audit_sha256 = Get-FileSha $sealAuditPath
    marker_path = $markerPath
    marker_bytes = $marker.Length
    marker_sha256 = Get-FileSha $markerPath
    marker_physical_lines = 22
    marker_unique_keys = 22
    marker_last_write_utc_ticks = $marker.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = $marginTicks
    at_or_after_excluding_marker = 0
    stage_absent_after_move = 'True'
    source_root_snapshot_before_sha256 = $sourceSnapshotBeforeAudit
    source_root_snapshot_after_sha256 = $sourceSnapshotBeforeAudit
    business_evidence_rerun = 0
    postmarker_content_attribute_writes = 0
}
foreach ($key in $expectedControllerResult.Keys) {
    $property = @($controllerResult.PSObject.Properties | Where-Object { $_.Name -ceq $key })
    if ($property.Count -ne 1) { Add-Error $errors "controller result missing field $key"; continue }
    if ([string]$property[0].Value -cne [string]$expectedControllerResult[$key]) { Add-Error $errors "controller result value mismatch $key" }
}
$controllerStartUtc = [DateTime]::MinValue
$controllerEndUtc = [DateTime]::MinValue
if (-not [DateTime]::TryParse([string]$controllerResult.start_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$controllerStartUtc)) { Add-Error $errors 'controller start UTC invalid' }
if (-not [DateTime]::TryParse([string]$controllerResult.end_utc, [Globalization.CultureInfo]::InvariantCulture, [Globalization.DateTimeStyles]::RoundtripKind, [ref]$controllerEndUtc)) { Add-Error $errors 'controller end UTC invalid' }
if ($controllerEndUtc.ToUniversalTime().Ticks -lt $controllerStartUtc.ToUniversalTime().Ticks) { Add-Error $errors 'controller end precedes start' }

$csvFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { $_.Extension -ieq '.csv' })
$jsonFiles = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { $_.Extension -ieq '.json' })
$csvParseFailures = [System.Collections.Generic.List[string]]::new()
$jsonParseFailures = [System.Collections.Generic.List[string]]::new()
foreach ($csvFile in $csvFiles) {
    try { $null = @(Import-Csv -LiteralPath $csvFile.FullName) } catch { $csvParseFailures.Add((Get-RelativePath $destinationRoot $csvFile.FullName)) }
}
foreach ($jsonFile in $jsonFiles) {
    try { $null = Get-Content -LiteralPath $jsonFile.FullName -Raw -Encoding utf8 | ConvertFrom-Json } catch { $jsonParseFailures.Add((Get-RelativePath $destinationRoot $jsonFile.FullName)) }
}
if ($csvFiles.Count -ne 12) { Add-Error $errors "CSV file count=$($csvFiles.Count)" }
if ($jsonFiles.Count -ne 9) { Add-Error $errors "JSON file count=$($jsonFiles.Count)" }
if ($csvParseFailures.Count -ne 0) { Add-Error $errors "CSV parse failures=$($csvParseFailures.Count)" }
if ($jsonParseFailures.Count -ne 0) { Add-Error $errors "JSON parse failures=$($jsonParseFailures.Count)" }

$ads = [System.Collections.Generic.List[string]]::new()
foreach ($file in $allFiles) {
    foreach ($stream in @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue)) {
        if ($stream.Stream -ne ':$DATA') { $ads.Add("$($file.FullName):$($stream.Stream)") }
    }
}
$cachePyc = @(Get-ChildItem -LiteralPath $destinationRoot -File -Recurse -Force | Where-Object { $_.Extension -eq '.pyc' -or $_.Directory.Name -eq '__pycache__' })
$reparse = @(@(Get-Item -LiteralPath $destinationRoot -Force) + @(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force) | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
if ($ads.Count -ne 0) { Add-Error $errors "ADS count=$($ads.Count)" }
if ($cachePyc.Count -ne 0) { Add-Error $errors "cache-pyc count=$($cachePyc.Count)" }
if ($reparse.Count -ne 0) { Add-Error $errors "reparse count=$($reparse.Count)" }

$destinationSnapshotAfterAudit = Get-TreeSnapshot $destinationRoot
$sourceSnapshotAfterAudit = Get-TreeSnapshot $sourceRoot
if ($destinationSnapshotBeforeAudit -cne [string]$controllerResult.destination_postmarker_snapshot_sha256) { Add-Error $errors 'destination snapshot differs from controller' }
if ($destinationSnapshotAfterAudit -cne $destinationSnapshotBeforeAudit) { Add-Error $errors 'destination postmarker content or attribute changed' }
if ($sourceSnapshotBeforeAudit -cne [string]$controllerResult.source_root_snapshot_before_sha256) { Add-Error $errors 'source snapshot differs from controller before snapshot' }
if ($sourceSnapshotAfterAudit -cne $sourceSnapshotBeforeAudit) { Add-Error $errors 'old source root changed during audit' }

$result = [ordered]@{
    schema = 'P126_R3B_CONTROL_RESEAL_AUDIT_V2'
    handoff_id = $handoffId
    operation = $operation
    preserved_business_verdict = $preservedVerdict
    hard_defect_id = $hardDefectId
    invocation_count = 1
    retry_count = 0
    copied_material_count = $copyDictionary.Count
    old_controls_copied = @($oldControlNames | Where-Object { $copyDictionary.ContainsKey($_) }).Count
    payload_count = $manifestDictionary.Count
    control_count = 3
    ordinary_count = $allFiles.Count
    directory_count_including_root = $allDirs.Count
    readonly_files = $allFiles.Count - $notReadonlyFiles.Count
    readonly_dirs = $allDirs.Count - $notReadonlyDirs.Count
    marker_physical_lines = $markerLines.Count
    marker_unique_keys = $markerDictionary.Count
    marker_bad_lines = $badMarkerLines.Count
    marker_sha256 = Get-FileSha $markerPath
    marker_last_write_utc_ticks = $marker.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = $marginTicks
    at_or_after_excluding_marker = $atOrAfter.Count
    destination_postmarker_snapshot_sha256 = $destinationSnapshotAfterAudit
    source_root_snapshot_sha256 = $sourceSnapshotAfterAudit
    postmarker_content_attribute_writes = 0
    CSV_file_count = $csvFiles.Count
    CSV_parse_failures = $csvParseFailures.Count
    JSON_file_count = $jsonFiles.Count
    JSON_parse_failures = $jsonParseFailures.Count
    ADS_count = $ads.Count
    cache_pyc_count = $cachePyc.Count
    reparse_count = $reparse.Count
    stage_absent = -not (Test-Path -LiteralPath $stagePath)
    errors = @($errors)
    hard_gate = $errors.Count -eq 0
    audited_utc = [DateTime]::UtcNow.ToString('o')
}
$result | ConvertTo-Json -Depth 9 | Set-Content -LiteralPath $auditResultPath -Encoding utf8NoBOM
Write-Output ($result | ConvertTo-Json -Depth 9)
if ($errors.Count -ne 0) { exit 1 }
