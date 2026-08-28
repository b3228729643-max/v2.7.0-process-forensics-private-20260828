param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Operation = 'P670_REPLACEMENT_V2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$HandoffId = 'C-FIG-P670-01-R114-SA2-R168-READONLY-ADJUDICATION-FRESH-REPLACEMENT-V2-CONTROL-RESEAL-V1'
$SourceHandoffId = 'C-FIG-P670-01-R114-SA2-R168-READONLY-ADJUDICATION-FRESH-REPLACEMENT-V2'
$Uid = 'FIG-P670-01'
$Verdict = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
$OldRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa2_r114_r168_readonly_adjudication_fresh_replacement_v2'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa2_r114_r168_readonly_adjudication_fresh_replacement_v2_control_reseal_v1'
$ExternalRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\FIG-P670-01\control_reseal_v1'
$OldBaselinePath = Join-Path $ExternalRoot 'OLD_ROOT_BEFORE.csv'
$ControllerResultPath = Join-Path $ExternalRoot 'CONTROLLER_RESULT.json'
$AuditResultPath = Join-Path $ExternalRoot 'AUDIT_RESULT.json'
$ExpectedOldManifestSha = 'BA321E0EC557F9E12121B7FAB9CC6499DA67D20F4CF6A179AAA3012ABAA6BB39'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$StartedUtc = [DateTime]::UtcNow

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativePathStrict {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$Path
    )
    return [System.IO.Path]::GetRelativePath($Base, $Path).Replace('/', '\')
}

function Get-FileRecord {
    param(
        [Parameter(Mandatory = $true)][string]$Base,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $Item = Get-Item -LiteralPath $Path -Force
    return [pscustomobject][ordered]@{
        relative_path = Get-RelativePathStrict -Base $Base -Path $Item.FullName
        resolved_path = $Item.FullName
        bytes = [int64]$Item.Length
        sha256 = Get-Sha256 -Path $Item.FullName
        creation_filetime_utc = [int64]$Item.CreationTimeUtc.ToFileTimeUtc()
        last_write_filetime_utc = [int64]$Item.LastWriteTimeUtc.ToFileTimeUtc()
        attributes = $Item.Attributes.ToString()
    }
}

function Get-TreeFileRecords {
    param([Parameter(Mandatory = $true)][string]$Root)
    $Rows = @()
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Sort-Object FullName)) {
        $Rows += Get-FileRecord -Base $Root -Path $File.FullName
    }
    return @($Rows)
}

function Get-TreeDirectoryRecords {
    param([Parameter(Mandatory = $true)][string]$Root)
    $Rows = @()
    $RootItem = Get-Item -LiteralPath $Root -Force
    $Rows += [pscustomobject][ordered]@{
        relative_path = '.'
        resolved_path = $RootItem.FullName
        last_write_filetime_utc = [int64]$RootItem.LastWriteTimeUtc.ToFileTimeUtc()
        attributes = $RootItem.Attributes.ToString()
    }
    foreach ($Directory in @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Sort-Object FullName)) {
        $Rows += [pscustomobject][ordered]@{
            relative_path = Get-RelativePathStrict -Base $Root -Path $Directory.FullName
            resolved_path = $Directory.FullName
            last_write_filetime_utc = [int64]$Directory.LastWriteTimeUtc.ToFileTimeUtc()
            attributes = $Directory.Attributes.ToString()
        }
    }
    return @($Rows)
}

function Compare-RecordSets {
    param(
        [Parameter(Mandatory = $true)][object[]]$Expected,
        [Parameter(Mandatory = $true)][object[]]$Actual,
        [string[]]$Fields = @('bytes', 'sha256', 'creation_filetime_utc', 'last_write_filetime_utc', 'attributes')
    )
    $ActualMap = @{}
    foreach ($Row in $Actual) { $ActualMap[[string]$Row.relative_path] = $Row }
    $Mismatches = @()
    foreach ($Row in $Expected) {
        $Relative = [string]$Row.relative_path
        if (-not $ActualMap.ContainsKey($Relative)) {
            $Mismatches += "missing:$Relative"
            continue
        }
        $Other = $ActualMap[$Relative]
        foreach ($Field in $Fields) {
            if ([string]$Row.$Field -cne [string]$Other.$Field) {
                $Mismatches += "$Field`:$Relative"
            }
        }
    }
    $ExpectedPaths = @($Expected | ForEach-Object { [string]$_.relative_path })
    foreach ($Row in $Actual) {
        if ($ExpectedPaths -notcontains [string]$Row.relative_path) {
            $Mismatches += "extra:$($Row.relative_path)"
        }
    }
    return @($Mismatches)
}

function Test-Hygiene {
    param([Parameter(Mandatory = $true)][string]$Root)
    $Ads = 0
    $CachePyc = 0
    $Reparse = 0
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)) {
        if (($File.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { $Reparse++ }
        if ($File.Extension -in @('.pyc', '.pyo') -or $File.FullName -match '(^|[\\/])__pycache__([\\/]|$)') { $CachePyc++ }
        foreach ($Stream in @(Get-Item -LiteralPath $File.FullName -Stream * -Force)) {
            if ($Stream.Stream -notin @(':$DATA', '::$DATA')) { $Ads++ }
        }
    }
    foreach ($Directory in @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force)) {
        if (($Directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) { $Reparse++ }
        if ($Directory.Name -eq '__pycache__') { $CachePyc++ }
    }
    return [ordered]@{ ads = $Ads; cache_pyc = $CachePyc; reparse = $Reparse }
}

function Test-Parse {
    param([Parameter(Mandatory = $true)][string]$Root)
    $Csv = 0
    $Json = 0
    $Failures = @()
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)) {
        try {
            if ($File.Extension -ieq '.csv') {
                $null = @(Import-Csv -LiteralPath $File.FullName)
                $Csv++
            }
            elseif ($File.Extension -ieq '.json') {
                $null = Get-Content -LiteralPath $File.FullName -Raw | ConvertFrom-Json
                $Json++
            }
        }
        catch {
            $Failures += $File.FullName
        }
    }
    return [ordered]@{ csv = $Csv; json = $Json; failures = @($Failures) }
}

function Write-JsonNoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value,
        [int]$Depth = 20
    )
    $Json = $Value | ConvertTo-Json -Depth $Depth
    [System.IO.File]::WriteAllText($Path, $Json + [Environment]::NewLine, $Utf8NoBom)
}

if (Test-Path -LiteralPath $AuditResultPath) {
    throw 'Audit result already exists; auditor is one-shot.'
}
if (-not (Test-Path -LiteralPath $OldRoot -PathType Container)) { throw 'Old root missing.' }
if (-not (Test-Path -LiteralPath $NewRoot -PathType Container)) { throw 'New root missing.' }
if (-not (Test-Path -LiteralPath $OldBaselinePath -PathType Leaf)) { throw 'Old baseline missing.' }
if (-not (Test-Path -LiteralPath $ControllerResultPath -PathType Leaf)) { throw 'Controller result missing.' }

$Controller = Get-Content -LiteralPath $ControllerResultPath -Raw | ConvertFrom-Json
if ([string]$Controller.status -cne 'PASS' -or [int]$Controller.invocation_count -ne 1 -or [int]$Controller.retry_count -ne 0) {
    throw 'Controller result is not a one-shot PASS.'
}

$OldBaseline = @(Import-Csv -LiteralPath $OldBaselinePath)
$OldActual = @(Get-TreeFileRecords -Root $OldRoot)
$OldDiffs = @(Compare-RecordSets -Expected $OldBaseline -Actual $OldActual)
$OldManifestPath = Join-Path $OldRoot 'MANIFEST.csv'
$OldMarkerPath = Join-Path $OldRoot 'WRITE_STOPPED'
$OldControlFailures = @()
if ($OldActual.Count -ne 29) { $OldControlFailures += 'old_file_count' }
if ((Get-Sha256 -Path $OldManifestPath) -cne $ExpectedOldManifestSha) { $OldControlFailures += 'old_manifest_sha' }
foreach ($ControlName in @('MANIFEST.csv', 'WRITE_STOPPED')) {
    $Expected = @($OldBaseline | Where-Object { $_.relative_path -ceq $ControlName })
    $Actual = @($OldActual | Where-Object { $_.relative_path -ceq $ControlName })
    if ($Expected.Count -ne 1 -or $Actual.Count -ne 1 -or @(Compare-RecordSets -Expected $Expected -Actual $Actual).Count -ne 0) {
        $OldControlFailures += "old_control:$ControlName"
    }
}

$CopyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
$CopyProvenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
$PayloadManifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
$SealAuditPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
$MarkerPath = Join-Path $NewRoot 'WRITE_STOPPED'
foreach ($RequiredPath in @($CopyIdentityPath, $CopyProvenancePath, $PayloadManifestPath, $SealAuditPath, $MarkerPath)) {
    if (-not (Test-Path -LiteralPath $RequiredPath -PathType Leaf)) { throw "Required sealed file missing: $RequiredPath" }
}

$CopyRows = @(Import-Csv -LiteralPath $CopyIdentityPath)
$CopyMismatches = @()
if ($CopyRows.Count -ne 27) { $CopyMismatches += 'copy_rows' }
foreach ($Row in $CopyRows) {
    $SourcePath = [string]$Row.source_resolved_path
    $DestinationPath = [string]$Row.destination_resolved_path
    if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf) -or -not (Test-Path -LiteralPath $DestinationPath -PathType Leaf)) {
        $CopyMismatches += "missing:$($Row.relative_path)"
        continue
    }
    $Source = Get-Item -LiteralPath $SourcePath -Force
    $Destination = Get-Item -LiteralPath $DestinationPath -Force
    if ([int64]$Source.Length -ne [int64]$Row.bytes -or [int64]$Destination.Length -ne [int64]$Row.bytes) { $CopyMismatches += "bytes:$($Row.relative_path)" }
    if ((Get-Sha256 -Path $SourcePath) -cne [string]$Row.sha256 -or (Get-Sha256 -Path $DestinationPath) -cne [string]$Row.sha256) { $CopyMismatches += "sha:$($Row.relative_path)" }
    if ([int64]$Source.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$Row.source_creation_filetime_utc -or [int64]$Destination.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$Row.destination_creation_filetime_utc -or [int64]$Row.source_creation_filetime_utc -ne [int64]$Row.destination_creation_filetime_utc) { $CopyMismatches += "creation:$($Row.relative_path)" }
    if ([int64]$Source.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$Row.source_last_write_filetime_utc -or [int64]$Destination.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$Row.destination_last_write_filetime_utc -or [int64]$Row.source_last_write_filetime_utc -ne [int64]$Row.destination_last_write_filetime_utc) { $CopyMismatches += "lastwrite:$($Row.relative_path)" }
}

$Provenance = Get-Content -LiteralPath $CopyProvenancePath -Raw | ConvertFrom-Json
$ProvenanceFailures = @()
if ([string]$Provenance.operation -cne $Operation) { $ProvenanceFailures += 'operation' }
if ([string]$Provenance.handoff_id -cne $HandoffId) { $ProvenanceFailures += 'handoff_id' }
if ([string]$Provenance.source_handoff_id -cne $SourceHandoffId) { $ProvenanceFailures += 'source_handoff_id' }
if ([string]$Provenance.source_root -cne (Get-Item -LiteralPath $OldRoot -Force).FullName) { $ProvenanceFailures += 'source_root' }
if ([string]$Provenance.destination_root -cne (Get-Item -LiteralPath $NewRoot -Force).FullName) { $ProvenanceFailures += 'destination_root' }
if ([string]$Provenance.source_manifest_expected_sha256 -cne $ExpectedOldManifestSha) { $ProvenanceFailures += 'source_manifest_sha' }
if ([bool]$Provenance.control_only -ne $true -or [bool]$Provenance.rerun_pdf_render_object_pair_manual_math_semantic -ne $false) { $ProvenanceFailures += 'scope' }

$PayloadRows = @(Import-Csv -LiteralPath $PayloadManifestPath)
$AllFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
$ControlNames = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$PayloadActual = @($AllFiles | Where-Object { (Get-RelativePathStrict -Base $NewRoot -Path $_.FullName) -notin $ControlNames })
$ControlActual = @($AllFiles | Where-Object { (Get-RelativePathStrict -Base $NewRoot -Path $_.FullName) -in $ControlNames })
$ManifestMismatches = @()
if ($PayloadRows.Count -ne 29) { $ManifestMismatches += 'manifest_rows' }
if (@($PayloadRows.relative_path | Sort-Object -Unique).Count -ne 29) { $ManifestMismatches += 'manifest_duplicate' }
if ($PayloadActual.Count -ne 29) { $ManifestMismatches += 'payload_fs_count' }
if ($ControlActual.Count -ne 3) { $ManifestMismatches += 'control_count' }
$PayloadActualPaths = @($PayloadActual | ForEach-Object { Get-RelativePathStrict -Base $NewRoot -Path $_.FullName })
foreach ($Path in @($PayloadRows.relative_path)) { if ($PayloadActualPaths -notcontains $Path) { $ManifestMismatches += "missing:$Path" } }
foreach ($Path in $PayloadActualPaths) { if (@($PayloadRows.relative_path) -notcontains $Path) { $ManifestMismatches += "extra:$Path" } }
foreach ($Row in $PayloadRows) {
    $Path = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($NewRoot, ([string]$Row.relative_path)))
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { continue }
    $Item = Get-Item -LiteralPath $Path -Force
    if ($Item.FullName -cne [string]$Row.resolved_path) { $ManifestMismatches += "resolved:$($Row.relative_path)" }
    if ([int64]$Item.Length -ne [int64]$Row.bytes) { $ManifestMismatches += "bytes:$($Row.relative_path)" }
    if ((Get-Sha256 -Path $Path) -cne ([string]$Row.sha256).ToUpperInvariant()) { $ManifestMismatches += "sha:$($Row.relative_path)" }
    if ([int64]$Item.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$Row.creation_filetime_utc) { $ManifestMismatches += "creation:$($Row.relative_path)" }
    if ([int64]$Item.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$Row.last_write_filetime_utc) { $ManifestMismatches += "lastwrite:$($Row.relative_path)" }
}

$MarkerBytes = [System.IO.File]::ReadAllBytes($MarkerPath)
$MarkerHasBom = ($MarkerBytes.Length -ge 3 -and $MarkerBytes[0] -eq 0xEF -and $MarkerBytes[1] -eq 0xBB -and $MarkerBytes[2] -eq 0xBF)
$MarkerLines = @(Get-Content -LiteralPath $MarkerPath)
$MarkerBadLines = @()
$MarkerMap = @{}
foreach ($Line in $MarkerLines) {
    if ($Line -notmatch '^[A-Z0-9_]+=[^\r\n]+$' -or [regex]::Matches($Line, '=').Count -ne 1 -or $Line -match "`t" -or $Line -match 'PLACEHOLDER') {
        $MarkerBadLines += $Line
        continue
    }
    $Parts = $Line -split '=', 2
    if ($MarkerMap.ContainsKey($Parts[0])) {
        $MarkerBadLines += "duplicate:$($Parts[0])"
    }
    else {
        $MarkerMap[$Parts[0]] = $Parts[1]
    }
}
$RequiredMarker = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    SEALED_ROOT = $NewRoot
    MANIFEST_ROWS = '29'
    MANIFEST_SHA256 = Get-Sha256 -Path $PayloadManifestPath
    VERDICT = $Verdict
    ACTUAL_SOURCE_ROOT = $OldRoot
    CONTROL_ONLY = 'true'
    POST_MARKER_ROOT_WRITES = '0'
}
$MarkerRequiredFailures = @()
foreach ($Key in $RequiredMarker.Keys) {
    if (-not $MarkerMap.ContainsKey($Key) -or [string]$MarkerMap[$Key] -cne [string]$RequiredMarker[$Key]) {
        $MarkerRequiredFailures += $Key
    }
}
if (-not $MarkerMap.ContainsKey('SOURCE_HANDOFF_ID') -or [string]$MarkerMap.SOURCE_HANDOFF_ID -cne $SourceHandoffId) { $MarkerRequiredFailures += 'SOURCE_HANDOFF_ID' }
if (-not $MarkerMap.ContainsKey('OPERATION') -or [string]$MarkerMap.OPERATION -cne $Operation) { $MarkerRequiredFailures += 'OPERATION' }
if (-not $MarkerMap.ContainsKey('FILETIME0') -or [string]::IsNullOrWhiteSpace([string]$MarkerMap.FILETIME0)) { $MarkerRequiredFailures += 'FILETIME0' }
if (-not $MarkerMap.ContainsKey('FILETIME0_UTC') -or [string]::IsNullOrWhiteSpace([string]$MarkerMap.FILETIME0_UTC)) { $MarkerRequiredFailures += 'FILETIME0_UTC' }

$MarkerItem = Get-Item -LiteralPath $MarkerPath -Force
$OtherFiles = @($AllFiles | Where-Object { $_.FullName -cne $MarkerPath })
$AtOrAfter = @($OtherFiles | Where-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $MarkerItem.LastWriteTimeUtc.ToFileTimeUtc() })
$MaxOtherTicks = [int64](@($OtherFiles | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum)
$StrictMargin = [int64]$MarkerItem.LastWriteTimeUtc.ToFileTimeUtc() - $MaxOtherTicks

$ReadOnlyFileFailures = @($AllFiles | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
$AllDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force)
$ReadOnlyDirectoryFailures = @($AllDirectories | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
$Hygiene = Test-Hygiene -Root $NewRoot
$Parse = Test-Parse -Root $NewRoot

$CurrentFileSnapshot = @(Get-TreeFileRecords -Root $NewRoot)
$CurrentDirectorySnapshot = @(Get-TreeDirectoryRecords -Root $NewRoot)
$PostMarkerFileDiffs = @(Compare-RecordSets -Expected @($Controller.final_file_snapshot) -Actual $CurrentFileSnapshot)
$PostMarkerDirectoryDiffs = @(Compare-RecordSets -Expected @($Controller.final_directory_snapshot) -Actual $CurrentDirectorySnapshot -Fields @('last_write_filetime_utc', 'attributes'))

$Failures = @()
if ($OldDiffs.Count -ne 0 -or $OldControlFailures.Count -ne 0) { $Failures += 'old_root_identity' }
if ($CopyMismatches.Count -ne 0) { $Failures += 'copy_identity' }
if ($ProvenanceFailures.Count -ne 0) { $Failures += 'provenance' }
if ($ManifestMismatches.Count -ne 0) { $Failures += 'manifest' }
if ($AllFiles.Count -ne 32) { $Failures += 'ordinary_count' }
if ($MarkerHasBom -or $MarkerBadLines.Count -ne 0 -or $MarkerRequiredFailures.Count -ne 0) { $Failures += 'marker_syntax' }
if ($AtOrAfter.Count -ne 0 -or $StrictMargin -le 0) { $Failures += 'marker_order' }
if ($ReadOnlyFileFailures.Count -ne 0 -or $ReadOnlyDirectoryFailures.Count -ne 0) { $Failures += 'readonly' }
if ($Hygiene.ads -ne 0 -or $Hygiene.cache_pyc -ne 0 -or $Hygiene.reparse -ne 0) { $Failures += 'hygiene' }
if (@($Parse.failures).Count -ne 0) { $Failures += 'parse' }
if ($PostMarkerFileDiffs.Count -ne 0 -or $PostMarkerDirectoryDiffs.Count -ne 0) { $Failures += 'post_marker_change' }

$FinishedUtc = [DateTime]::UtcNow
$Audit = [ordered]@{
    status = $(if ($Failures.Count -eq 0) { 'PASS' } else { 'FAIL' })
    operation = $Operation
    invocation_count = 1
    retry_count = 0
    started_utc = $StartedUtc.ToString('o')
    finished_utc = $FinishedUtc.ToString('o')
    duration_seconds = ($FinishedUtc - $StartedUtc).TotalSeconds
    old_root = $OldRoot
    old_root_file_count = $OldActual.Count
    old_root_mismatch = $OldDiffs.Count
    old_control_mismatch = $OldControlFailures.Count
    copied_material_rows = $CopyRows.Count
    copy_identity_mismatch = $CopyMismatches.Count
    provenance_failures = $ProvenanceFailures.Count
    payload_rows = $PayloadRows.Count
    payload_files = $PayloadActual.Count
    controls = $ControlActual.Count
    ordinary = $AllFiles.Count
    manifest_mismatch = $ManifestMismatches.Count
    payload_manifest_sha256 = Get-Sha256 -Path $PayloadManifestPath
    files_readonly = $AllFiles.Count - $ReadOnlyFileFailures.Count
    file_count = $AllFiles.Count
    dirs_readonly = $AllDirectories.Count - $ReadOnlyDirectoryFailures.Count
    dir_count_including_root = $AllDirectories.Count
    marker_physical_lines = $MarkerLines.Count
    marker_unique_keys = $MarkerMap.Count
    marker_bad_lines = $MarkerBadLines.Count
    marker_required_failures = $MarkerRequiredFailures.Count
    marker_has_utf8_bom = $MarkerHasBom
    marker_last_write_filetime_utc = [int64]$MarkerItem.LastWriteTimeUtc.ToFileTimeUtc()
    max_other_last_write_filetime_utc = $MaxOtherTicks
    marker_strict_margin_ticks = $StrictMargin
    at_or_after_excluding_marker = $AtOrAfter.Count
    post_marker_file_identity_or_attribute_mismatch = $PostMarkerFileDiffs.Count
    post_marker_directory_time_or_attribute_mismatch = $PostMarkerDirectoryDiffs.Count
    csv_parse_count = $Parse.csv
    json_parse_count = $Parse.json
    parse_failures = @($Parse.failures).Count
    ads = $Hygiene.ads
    cache_pyc = $Hygiene.cache_pyc
    reparse = $Hygiene.reparse
    failures = @($Failures)
}
Write-JsonNoBom -Path $AuditResultPath -Value $Audit
Write-Output ($Audit | ConvertTo-Json -Depth 6)
if ($Failures.Count -ne 0) { exit 1 }
exit 0
