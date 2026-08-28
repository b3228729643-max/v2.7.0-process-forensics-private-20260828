param(
    [Parameter(Mandatory = $true)]
    [string]$AuthorizationToken
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ExpectedToken = 'MAIN_R434_P670_SINGLE_CONTROL_RESEAL_AUTHORIZED'
$Operation = 'P670_REPLACEMENT_V2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$HandoffId = 'C-FIG-P670-01-R114-SA2-R168-READONLY-ADJUDICATION-FRESH-REPLACEMENT-V2-CONTROL-RESEAL-V1'
$SourceHandoffId = 'C-FIG-P670-01-R114-SA2-R168-READONLY-ADJUDICATION-FRESH-REPLACEMENT-V2'
$Uid = 'FIG-P670-01'
$Verdict = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
$OldRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa2_r114_r168_readonly_adjudication_fresh_replacement_v2'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P670-01\sa2_r114_r168_readonly_adjudication_fresh_replacement_v2_control_reseal_v1'
$OldManifest = Join-Path $OldRoot 'MANIFEST.csv'
$OldMarker = Join-Path $OldRoot 'WRITE_STOPPED'
$ExpectedOldManifestSha = 'BA321E0EC557F9E12121B7FAB9CC6499DA67D20F4CF6A179AAA3012ABAA6BB39'
$ExternalRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\FIG-P670-01\control_reseal_v1'
$OldBaselinePath = Join-Path $ExternalRoot 'OLD_ROOT_BEFORE.csv'
$PreparedMarkerPath = Join-Path $ExternalRoot 'WRITE_STOPPED.prepared'
$ControllerResultPath = Join-Path $ExternalRoot 'CONTROLLER_RESULT.json'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$StartedUtc = [DateTime]::UtcNow
$RootCreated = $false
$MarkerMoved = $false

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
    return [ordered]@{
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
    $Records = @()
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Sort-Object FullName)) {
        $Records += [pscustomobject](Get-FileRecord -Base $Root -Path $File.FullName)
    }
    return @($Records)
}

function Get-TreeDirectoryRecords {
    param([Parameter(Mandatory = $true)][string]$Root)
    $Records = @()
    $RootItem = Get-Item -LiteralPath $Root -Force
    $Records += [pscustomobject][ordered]@{
        relative_path = '.'
        resolved_path = $RootItem.FullName
        last_write_filetime_utc = [int64]$RootItem.LastWriteTimeUtc.ToFileTimeUtc()
        attributes = $RootItem.Attributes.ToString()
    }
    foreach ($Directory in @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Sort-Object FullName)) {
        $Records += [pscustomobject][ordered]@{
            relative_path = Get-RelativePathStrict -Base $Root -Path $Directory.FullName
            resolved_path = $Directory.FullName
            last_write_filetime_utc = [int64]$Directory.LastWriteTimeUtc.ToFileTimeUtc()
            attributes = $Directory.Attributes.ToString()
        }
    }
    return @($Records)
}

function Write-Utf8NoBomLines {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string[]]$Lines
    )
    [System.IO.File]::WriteAllLines($Path, $Lines, $Utf8NoBom)
}

function Write-JsonNoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)]$Value,
        [int]$Depth = 12
    )
    $Json = $Value | ConvertTo-Json -Depth $Depth
    [System.IO.File]::WriteAllText($Path, $Json + [Environment]::NewLine, $Utf8NoBom)
}

function Write-CsvNoBom {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][object[]]$Rows
    )
    $Lines = @($Rows | ConvertTo-Csv -NoTypeInformation)
    Write-Utf8NoBomLines -Path $Path -Lines ([string[]]$Lines)
}

function Assert-WithinRoot {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$Path
    )
    $ResolvedRoot = [System.IO.Path]::GetFullPath($Root).TrimEnd('\') + '\'
    $ResolvedPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $ResolvedPath.StartsWith($ResolvedRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes root: $ResolvedPath"
    }
}

function Test-Hygiene {
    param([Parameter(Mandatory = $true)][string]$Root)
    $Ads = 0
    $CachePyc = 0
    $Reparse = 0
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)) {
        if (($File.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            $Reparse++
        }
        if ($File.Extension -in @('.pyc', '.pyo') -or $File.FullName -match '(^|[\\/])__pycache__([\\/]|$)') {
            $CachePyc++
        }
        foreach ($Stream in @(Get-Item -LiteralPath $File.FullName -Stream * -Force)) {
            if ($Stream.Stream -notin @(':$DATA', '::$DATA')) {
                $Ads++
            }
        }
    }
    foreach ($Directory in @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force)) {
        if (($Directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            $Reparse++
        }
        if ($Directory.Name -eq '__pycache__') {
            $CachePyc++
        }
    }
    return [ordered]@{ ads = $Ads; cache_pyc = $CachePyc; reparse = $Reparse }
}

function Test-Parse {
    param([Parameter(Mandatory = $true)][string]$Root)
    $CsvCount = 0
    $JsonCount = 0
    $Failures = @()
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)) {
        try {
            if ($File.Extension -ieq '.csv') {
                $null = @(Import-Csv -LiteralPath $File.FullName)
                $CsvCount++
            }
            elseif ($File.Extension -ieq '.json') {
                $null = Get-Content -LiteralPath $File.FullName -Raw | ConvertFrom-Json
                $JsonCount++
            }
        }
        catch {
            $Failures += $File.FullName
        }
    }
    return [ordered]@{ csv = $CsvCount; json = $JsonCount; failures = @($Failures) }
}

function Set-TreeReadOnly {
    param([Parameter(Mandatory = $true)][string]$Root)
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)) {
        $File.Attributes = $File.Attributes -bor [System.IO.FileAttributes]::ReadOnly
    }
    $Directories = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)
    foreach ($Directory in $Directories) {
        $Directory.Attributes = $Directory.Attributes -bor [System.IO.FileAttributes]::ReadOnly
    }
    $RootItem = Get-Item -LiteralPath $Root -Force
    $RootItem.Attributes = $RootItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}

function Get-ReadOnlyFailures {
    param([Parameter(Mandatory = $true)][string]$Root)
    $Failures = @()
    foreach ($Item in @((Get-ChildItem -LiteralPath $Root -File -Recurse -Force), (Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force), (Get-Item -LiteralPath $Root -Force))) {
        foreach ($Entry in @($Item)) {
            if (($Entry.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) {
                $Failures += $Entry.FullName
            }
        }
    }
    return @($Failures)
}

function Compare-RecordSets {
    param(
        [Parameter(Mandatory = $true)][object[]]$Before,
        [Parameter(Mandatory = $true)][object[]]$After
    )
    $AfterMap = @{}
    foreach ($Row in $After) { $AfterMap[$Row.relative_path] = $Row }
    $Mismatches = @()
    foreach ($Row in $Before) {
        if (-not $AfterMap.ContainsKey($Row.relative_path)) {
            $Mismatches += "missing:$($Row.relative_path)"
            continue
        }
        $Other = $AfterMap[$Row.relative_path]
        foreach ($Field in @('bytes', 'sha256', 'creation_filetime_utc', 'last_write_filetime_utc', 'attributes')) {
            if ([string]$Row.$Field -cne [string]$Other.$Field) {
                $Mismatches += "$Field`:$($Row.relative_path)"
            }
        }
    }
    foreach ($Row in $After) {
        if (-not (@($Before.relative_path) -contains $Row.relative_path)) {
            $Mismatches += "extra:$($Row.relative_path)"
        }
    }
    return @($Mismatches)
}

if ($AuthorizationToken -cne $ExpectedToken) {
    throw 'Authorization token mismatch.'
}
if (Test-Path -LiteralPath $ControllerResultPath) {
    throw 'Controller result already exists; invocation is not fresh.'
}
if (Test-Path -LiteralPath $OldBaselinePath) {
    throw 'Old-root baseline already exists; invocation is not fresh.'
}
if (Test-Path -LiteralPath $PreparedMarkerPath) {
    throw 'Prepared marker already exists; invocation is not fresh.'
}

try {
    if (-not (Test-Path -LiteralPath $OldRoot -PathType Container)) { throw 'Old root missing.' }
    if ((Test-Path -LiteralPath $NewRoot -PathType Leaf) -or (Test-Path -LiteralPath $NewRoot -PathType Container) -or (Test-Path -LiteralPath $NewRoot)) {
        throw 'New root is not absent.'
    }
    if (-not (Test-Path -LiteralPath $OldManifest -PathType Leaf)) { throw 'Old manifest missing.' }
    if (-not (Test-Path -LiteralPath $OldMarker -PathType Leaf)) { throw 'Old marker missing.' }
    if ((Get-Sha256 -Path $OldManifest) -cne $ExpectedOldManifestSha) { throw 'Old manifest SHA mismatch.' }

    $OldFilesBefore = @(Get-TreeFileRecords -Root $OldRoot)
    if ($OldFilesBefore.Count -ne 29) { throw "Old root file count is $($OldFilesBefore.Count), expected 29." }
    Write-CsvNoBom -Path $OldBaselinePath -Rows $OldFilesBefore
    $OldBaselineSha = Get-Sha256 -Path $OldBaselinePath

    $OldRows = @(Import-Csv -LiteralPath $OldManifest)
    if ($OldRows.Count -ne 27) { throw "Old manifest row count is $($OldRows.Count), expected 27." }
    if (@($OldRows.relative_path | Sort-Object -Unique).Count -ne 27) { throw 'Old manifest has duplicate paths.' }
    if (@($OldRows.relative_path | Where-Object { $_ -in @('MANIFEST.csv', 'WRITE_STOPPED') }).Count -ne 0) { throw 'Old controls are listed as material.' }

    $OldMarkerLines = @(Get-Content -LiteralPath $OldMarker)
    $OldMarkerHandoff = @($OldMarkerLines | Where-Object { $_ -like 'HANDOFF_ID=*' })
    if ($OldMarkerHandoff.Count -ne 1 -or $OldMarkerHandoff[0].Substring(11) -cne $SourceHandoffId) {
        throw 'Old marker HANDOFF_ID mismatch.'
    }

    $ExpectedOldPaths = @($OldRows.relative_path) + @('MANIFEST.csv', 'WRITE_STOPPED')
    $ActualOldPaths = @($OldFilesBefore.relative_path)
    if (@($ExpectedOldPaths | Where-Object { $ActualOldPaths -notcontains $_ }).Count -ne 0 -or @($ActualOldPaths | Where-Object { $ExpectedOldPaths -notcontains $_ }).Count -ne 0) {
        throw 'Old root set is not manifest material plus two controls.'
    }

    foreach ($Row in $OldRows) {
        $Relative = ([string]$Row.relative_path).Replace('/', '\')
        $SourcePath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($OldRoot, $Relative))
        Assert-WithinRoot -Root $OldRoot -Path $SourcePath
        if (-not (Test-Path -LiteralPath $SourcePath -PathType Leaf)) { throw "Old material missing: $Relative" }
        $SourceItem = Get-Item -LiteralPath $SourcePath -Force
        if ([int64]$SourceItem.Length -ne [int64]$Row.bytes) { throw "Old material bytes mismatch: $Relative" }
        if ((Get-Sha256 -Path $SourcePath) -cne ([string]$Row.sha256).ToUpperInvariant()) { throw "Old material SHA mismatch: $Relative" }
        if ([int64]$SourceItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$Row.last_write_filetime_utc) { throw "Old material last-write mismatch: $Relative" }
    }

    $null = New-Item -ItemType Directory -Path $NewRoot
    $RootCreated = $true
    $CopyRows = @()
    foreach ($Row in $OldRows) {
        $Relative = ([string]$Row.relative_path).Replace('/', '\')
        $SourcePath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($OldRoot, $Relative))
        $DestinationPath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($NewRoot, $Relative))
        Assert-WithinRoot -Root $NewRoot -Path $DestinationPath
        $DestinationDirectory = Split-Path -Parent $DestinationPath
        if (-not (Test-Path -LiteralPath $DestinationDirectory -PathType Container)) {
            $null = New-Item -ItemType Directory -Path $DestinationDirectory
        }
        Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath
        $SourceItem = Get-Item -LiteralPath $SourcePath -Force
        [System.IO.File]::SetCreationTimeUtc($DestinationPath, $SourceItem.CreationTimeUtc)
        [System.IO.File]::SetLastWriteTimeUtc($DestinationPath, $SourceItem.LastWriteTimeUtc)
        $DestinationItem = Get-Item -LiteralPath $DestinationPath -Force
        if ([int64]$DestinationItem.Length -ne [int64]$SourceItem.Length -or
            (Get-Sha256 -Path $DestinationPath) -cne (Get-Sha256 -Path $SourcePath) -or
            [int64]$DestinationItem.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$SourceItem.CreationTimeUtc.ToFileTimeUtc() -or
            [int64]$DestinationItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$SourceItem.LastWriteTimeUtc.ToFileTimeUtc()) {
            throw "Copy identity mismatch: $Relative"
        }
        $CopyRows += [pscustomobject][ordered]@{
            relative_path = $Relative
            source_resolved_path = $SourceItem.FullName
            destination_resolved_path = $DestinationItem.FullName
            bytes = [int64]$SourceItem.Length
            sha256 = Get-Sha256 -Path $SourcePath
            source_creation_filetime_utc = [int64]$SourceItem.CreationTimeUtc.ToFileTimeUtc()
            destination_creation_filetime_utc = [int64]$DestinationItem.CreationTimeUtc.ToFileTimeUtc()
            source_last_write_filetime_utc = [int64]$SourceItem.LastWriteTimeUtc.ToFileTimeUtc()
            destination_last_write_filetime_utc = [int64]$DestinationItem.LastWriteTimeUtc.ToFileTimeUtc()
        }
    }

    $CopyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
    Write-CsvNoBom -Path $CopyIdentityPath -Rows $CopyRows
    $OldManifestRecord = $OldFilesBefore | Where-Object { $_.relative_path -ceq 'MANIFEST.csv' }
    $OldMarkerRecord = $OldFilesBefore | Where-Object { $_.relative_path -ceq 'WRITE_STOPPED' }
    $CopyProvenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
    $CopyProvenance = [ordered]@{
        operation = $Operation
        handoff_id = $HandoffId
        uid = $Uid
        verdict = $Verdict
        control_only = $true
        rerun_pdf_render_object_pair_manual_math_semantic = $false
        source_handoff_id = $SourceHandoffId
        source_root = (Get-Item -LiteralPath $OldRoot -Force).FullName
        destination_root = (Get-Item -LiteralPath $NewRoot -Force).FullName
        source_manifest = $OldManifestRecord
        source_write_stopped = $OldMarkerRecord
        source_manifest_expected_sha256 = $ExpectedOldManifestSha
        material_rows = 27
        old_controls_copied = 0
        added_payload = @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json')
        projected_payload = 29
    }
    Write-JsonNoBom -Path $CopyProvenancePath -Value $CopyProvenance

    $PayloadFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force | Sort-Object FullName)
    if ($PayloadFiles.Count -ne 29) { throw "Payload count is $($PayloadFiles.Count), expected 29." }
    $PayloadRows = @()
    foreach ($File in $PayloadFiles) {
        $Relative = Get-RelativePathStrict -Base $NewRoot -Path $File.FullName
        $PayloadRows += [pscustomobject][ordered]@{
            relative_path = $Relative
            resolved_path = $File.FullName
            bytes = [int64]$File.Length
            sha256 = Get-Sha256 -Path $File.FullName
            creation_filetime_utc = [int64]$File.CreationTimeUtc.ToFileTimeUtc()
            last_write_filetime_utc = [int64]$File.LastWriteTimeUtc.ToFileTimeUtc()
        }
    }
    $PayloadManifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
    Write-CsvNoBom -Path $PayloadManifestPath -Rows $PayloadRows
    $PayloadManifestSha = Get-Sha256 -Path $PayloadManifestPath

    $PayloadActual = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force | Where-Object { $_.FullName -cne $PayloadManifestPath })
    if ($PayloadActual.Count -ne 29) { throw 'Payload/manifest count equation failed.' }
    $PayloadActualPaths = @($PayloadActual | ForEach-Object { Get-RelativePathStrict -Base $NewRoot -Path $_.FullName })
    if (@($PayloadRows.relative_path | Where-Object { $PayloadActualPaths -notcontains $_ }).Count -ne 0 -or @($PayloadActualPaths | Where-Object { $PayloadRows.relative_path -notcontains $_ }).Count -ne 0) {
        throw 'Payload manifest set mismatch.'
    }
    foreach ($Row in $PayloadRows) {
        $Path = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($NewRoot, ([string]$Row.relative_path)))
        $Item = Get-Item -LiteralPath $Path -Force
        if ($Item.FullName -cne [string]$Row.resolved_path -or
            [int64]$Item.Length -ne [int64]$Row.bytes -or
            (Get-Sha256 -Path $Path) -cne ([string]$Row.sha256).ToUpperInvariant() -or
            [int64]$Item.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$Row.creation_filetime_utc -or
            [int64]$Item.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$Row.last_write_filetime_utc) {
            throw "Payload manifest identity mismatch: $($Row.relative_path)"
        }
    }

    $HygieneBeforeSeal = Test-Hygiene -Root $NewRoot
    $ParseBeforeSeal = Test-Parse -Root $NewRoot
    if ($HygieneBeforeSeal.ads -ne 0 -or $HygieneBeforeSeal.cache_pyc -ne 0 -or $HygieneBeforeSeal.reparse -ne 0 -or @($ParseBeforeSeal.failures).Count -ne 0) {
        throw 'Pre-seal hygiene/parse gate failed.'
    }

    $SealAuditPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
    $SealAudit = [ordered]@{
        operation = $Operation
        handoff_id = $HandoffId
        uid = $Uid
        sealed_root = (Get-Item -LiteralPath $NewRoot -Force).FullName
        actual_source_root = (Get-Item -LiteralPath $OldRoot -Force).FullName
        control_only = $true
        verdict = $Verdict
        material_copied = 27
        added_payload = 2
        payload_rows = 29
        controls_before_marker = 2
        files_before_marker = 31
        payload_manifest_path = $PayloadManifestPath
        payload_manifest_sha256 = $PayloadManifestSha
        copy_identity_path = $CopyIdentityPath
        copy_provenance_path = $CopyProvenancePath
        old_manifest_sha256 = $ExpectedOldManifestSha
        old_controls_copied = 0
        identity_mismatch = 0
        parse_failures = 0
        ads = 0
        cache_pyc = 0
        reparse = 0
        post_marker_root_writes = 0
    }
    Write-JsonNoBom -Path $SealAuditPath -Value $SealAudit

    $PreMarkerFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    if ($PreMarkerFiles.Count -ne 31) { throw "Pre-marker file count is $($PreMarkerFiles.Count), expected 31." }
    $HygieneFinal = Test-Hygiene -Root $NewRoot
    $ParseFinal = Test-Parse -Root $NewRoot
    if ($HygieneFinal.ads -ne 0 -or $HygieneFinal.cache_pyc -ne 0 -or $HygieneFinal.reparse -ne 0 -or @($ParseFinal.failures).Count -ne 0) {
        throw 'Final pre-marker hygiene/parse gate failed.'
    }

    Set-TreeReadOnly -Root $NewRoot
    $PreMarkerReadOnlyFailures = @(Get-ReadOnlyFailures -Root $NewRoot)
    if ($PreMarkerReadOnlyFailures.Count -ne 0) { throw 'Pre-marker readonly gate failed.' }

    $MaxOtherTicks = [int64](@(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum)
    $MarkerTicks = $MaxOtherTicks + [int64]10000000
    $MarkerUtc = [DateTime]::FromFileTimeUtc($MarkerTicks).ToString('o')
    $MarkerLines = [string[]]@(
        "HANDOFF_ID=$HandoffId",
        "UID=$Uid",
        "SEALED_ROOT=$NewRoot",
        'MANIFEST_ROWS=29',
        "MANIFEST_SHA256=$PayloadManifestSha",
        "VERDICT=$Verdict",
        "ACTUAL_SOURCE_ROOT=$OldRoot",
        "SOURCE_HANDOFF_ID=$SourceHandoffId",
        'CONTROL_ONLY=true',
        "OPERATION=$Operation",
        'POST_MARKER_ROOT_WRITES=0',
        ("FILETIME0={0}" -f $MaxOtherTicks),
        ("FILETIME0_UTC={0}" -f ([DateTime]::FromFileTimeUtc($MaxOtherTicks).ToString('o')))
    )
    $MarkerBadLines = @($MarkerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\r\n]+$' -or $_ -match "`t" -or $_ -match 'PLACEHOLDER' })
    $MarkerKeys = @($MarkerLines | ForEach-Object { ($_ -split '=', 2)[0] })
    if ($MarkerBadLines.Count -ne 0 -or @($MarkerKeys | Sort-Object -Unique).Count -ne $MarkerLines.Count) {
        throw 'Prepared marker syntax gate failed.'
    }
    Write-Utf8NoBomLines -Path $PreparedMarkerPath -Lines $MarkerLines
    [System.IO.File]::SetLastWriteTimeUtc($PreparedMarkerPath, [DateTime]::FromFileTimeUtc($MarkerTicks))
    $PreparedItem = Get-Item -LiteralPath $PreparedMarkerPath -Force
    $PreparedItem.Attributes = $PreparedItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly
    if ([int64]$PreparedItem.LastWriteTimeUtc.ToFileTimeUtc() -ne $MarkerTicks -or ($PreparedItem.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) {
        throw 'Prepared marker identity/readonly gate failed.'
    }

    $FinalMarkerPath = Join-Path $NewRoot 'WRITE_STOPPED'
    if (Test-Path -LiteralPath $FinalMarkerPath) { throw 'Final marker path already exists.' }
    [System.IO.File]::Move($PreparedMarkerPath, $FinalMarkerPath)
    $MarkerMoved = $true

    $FinalFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    $FinalDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force)
    $FinalReadOnlyFailures = @(Get-ReadOnlyFailures -Root $NewRoot)
    $FinalHygiene = Test-Hygiene -Root $NewRoot
    $MarkerItem = Get-Item -LiteralPath $FinalMarkerPath -Force
    $AtOrAfter = @($FinalFiles | Where-Object { $_.FullName -cne $FinalMarkerPath -and $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $MarkerItem.LastWriteTimeUtc.ToFileTimeUtc() })
    $StrictLatest = ($AtOrAfter.Count -eq 0)
    if ($FinalFiles.Count -ne 32 -or $FinalReadOnlyFailures.Count -ne 0 -or -not $StrictLatest -or $FinalHygiene.ads -ne 0 -or $FinalHygiene.cache_pyc -ne 0 -or $FinalHygiene.reparse -ne 0) {
        throw 'Post-move read-only audit failed.'
    }

    $OldFilesAfter = @(Get-TreeFileRecords -Root $OldRoot)
    $OldRootDiffs = @(Compare-RecordSets -Before $OldFilesBefore -After $OldFilesAfter)
    if ($OldRootDiffs.Count -ne 0) { throw 'Old root changed during controller invocation.' }

    $FinalFileSnapshot = @(Get-TreeFileRecords -Root $NewRoot)
    $FinalDirectorySnapshot = @(Get-TreeDirectoryRecords -Root $NewRoot)
    $FinishedUtc = [DateTime]::UtcNow
    $ControllerResult = [ordered]@{
        status = 'PASS'
        operation = $Operation
        authorization_token = $AuthorizationToken
        invocation_count = 1
        retry_count = 0
        started_utc = $StartedUtc.ToString('o')
        finished_utc = $FinishedUtc.ToString('o')
        duration_seconds = ($FinishedUtc - $StartedUtc).TotalSeconds
        handoff_id = $HandoffId
        uid = $Uid
        old_root = $OldRoot
        new_root = $NewRoot
        old_baseline_path = $OldBaselinePath
        old_baseline_sha256 = $OldBaselineSha
        old_root_before_count = $OldFilesBefore.Count
        old_root_after_count = $OldFilesAfter.Count
        old_root_mismatch = $OldRootDiffs.Count
        source_material = 27
        copied_old_controls = 0
        payload = 29
        controls = 3
        ordinary = 32
        payload_manifest_rows = 29
        payload_manifest_sha256 = $PayloadManifestSha
        files_readonly = $FinalFiles.Count - $FinalReadOnlyFailures.Count
        file_count = $FinalFiles.Count
        directory_count_including_root = $FinalDirectories.Count
        directories_readonly = @($FinalDirectories | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 }).Count
        write_stopped_lines = $MarkerLines.Count
        write_stopped_bad_lines = $MarkerBadLines.Count
        write_stopped_strict_latest = $StrictLatest
        write_stopped_at_or_after_excluding_marker = $AtOrAfter.Count
        write_stopped_last_write_filetime_utc = [int64]$MarkerItem.LastWriteTimeUtc.ToFileTimeUtc()
        max_other_last_write_filetime_utc = $MaxOtherTicks
        strict_margin_ticks = [int64]$MarkerItem.LastWriteTimeUtc.ToFileTimeUtc() - $MaxOtherTicks
        parse_failures = @($ParseFinal.failures).Count
        ads = $FinalHygiene.ads
        cache_pyc = $FinalHygiene.cache_pyc
        reparse = $FinalHygiene.reparse
        post_marker_root_writes = 0
        final_file_snapshot = $FinalFileSnapshot
        final_directory_snapshot = $FinalDirectorySnapshot
    }
    Write-JsonNoBom -Path $ControllerResultPath -Value $ControllerResult -Depth 20
    Write-Output ($ControllerResult | ConvertTo-Json -Depth 4)
    exit 0
}
catch {
    $FinishedUtc = [DateTime]::UtcNow
    $Failure = [ordered]@{
        status = 'FAIL'
        operation = $Operation
        invocation_count = 1
        retry_count = 0
        started_utc = $StartedUtc.ToString('o')
        finished_utc = $FinishedUtc.ToString('o')
        duration_seconds = ($FinishedUtc - $StartedUtc).TotalSeconds
        root_created = $RootCreated
        marker_moved = $MarkerMoved
        error = $_.Exception.Message
        new_root = $NewRoot
        post_marker_root_writes = 0
    }
    if (-not (Test-Path -LiteralPath $ControllerResultPath)) {
        Write-JsonNoBom -Path $ControllerResultPath -Value $Failure
    }
    Write-Error $_
    exit 1
}
