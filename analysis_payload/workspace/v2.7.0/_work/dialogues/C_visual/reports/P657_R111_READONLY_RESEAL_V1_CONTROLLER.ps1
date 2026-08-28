param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('MAIN_R324_P657_READONLY_CONTROL_RESEAL_AUTHORIZED')]
    [string]$AuthorizationToken
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$OldRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa2_r111_r168_readonly_adjudication_reseal_v1'
$ExternalDir = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports'
$ClaimPath = Join-Path $ExternalDir 'P657_R111_READONLY_RESEAL_V1_INVOCATION_CLAIM.json'
$ResultPath = Join-Path $ExternalDir 'P657_R111_READONLY_RESEAL_V1_CONTROLLER_RESULT.json'
$AuditPath = Join-Path $ExternalDir 'P657_R111_READONLY_RESEAL_V1_ROOT_EXTERNAL_AUDIT.json'
$SealTempPath = Join-Path $ExternalDir 'P657_R111_READONLY_RESEAL_V1_SEAL_AUDIT.tmp.json'
$WstopTempPath = Join-Path $ExternalDir 'P657_R111_READONLY_RESEAL_V1_WRITE_STOPPED.tmp'
$ControllerPath = $PSCommandPath

function Resolve-ExactPath([string]$Path) {
    return [IO.Path]::GetFullPath($Path)
}

function Assert-Within([string]$Candidate, [string]$Root, [string]$Label) {
    $candidateFull = Resolve-ExactPath $Candidate
    $rootFull = (Resolve-ExactPath $Root).TrimEnd('\')
    if (-not $candidateFull.StartsWith($rootFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label escapes the assigned root: $candidateFull"
    }
}

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Write-JsonExternal([string]$Path, [object]$Value) {
    $json = $Value | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText($Path, $json + [Environment]::NewLine, [Text.UTF8Encoding]::new($false))
}

function Set-ReadOnlyBit([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    [IO.File]::SetAttributes($item.FullName, ($item.Attributes -bor [IO.FileAttributes]::ReadOnly))
}

function Get-RelativeSlashPath([string]$Root, [string]$Path) {
    return [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/')
}

function Get-AdsCount([System.IO.FileInfo[]]$Files) {
    $count = 0
    foreach ($file in $Files) {
        try {
            $count += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop |
                Where-Object { $_.Stream -ne ':$DATA' }).Count
        } catch {
            # Filesystems without stream enumeration contribute no ADS finding.
        }
    }
    return $count
}

function Get-Hygiene([string]$Root) {
    $files = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)
    $dirs = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force)
    $jsonFailures = 0
    $csvFailures = 0
    foreach ($file in @($files | Where-Object { $_.Extension -eq '.json' })) {
        try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { $jsonFailures++ }
    }
    foreach ($file in @($files | Where-Object { $_.Extension -eq '.csv' })) {
        try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvFailures++ }
    }
    $cachePyc = @($files | Where-Object {
        $_.Name -like '*.pyc' -or $_.FullName -match '[\\/](?:__pycache__|\.cache|cache)[\\/]'
    }).Count
    $reparse = @((@($files) + @($dirs) + @(Get-Item -LiteralPath $Root -Force)) | Where-Object {
        (($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0)
    }).Count
    return [ordered]@{
        json_parse_failures = $jsonFailures
        csv_parse_failures = $csvFailures
        ads_count = Get-AdsCount $files
        cache_pyc_count = $cachePyc
        reparse_count = $reparse
    }
}

function Get-ReadonlyGate([string]$Root) {
    $files = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force)
    $dirs = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force)
    $rootItem = Get-Item -LiteralPath $Root -Force
    $writableFiles = @($files | Where-Object { -not $_.IsReadOnly })
    $writableDirs = @($dirs | Where-Object {
        (($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0)
    })
    $rootReadonly = (($rootItem.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
    return [ordered]@{
        file_count = $files.Count
        readonly_file_count = $files.Count - $writableFiles.Count
        directory_count_including_root = $dirs.Count + 1
        readonly_directory_count_including_root = ($dirs.Count - $writableDirs.Count) + [int]$rootReadonly
        writable_file_count = $writableFiles.Count
        writable_directory_count_including_root = $writableDirs.Count + [int](-not $rootReadonly)
    }
}

function Get-ManifestGate([string]$Root, [object[]]$Entries, [string[]]$ExcludedControls) {
    $seen = @{}
    $duplicate = 0
    $missing = 0
    $bytesMismatch = 0
    $shaMismatch = 0
    $ticksMismatch = 0
    foreach ($entry in $Entries) {
        $relative = [string]$entry.relative_path
        if ($seen.ContainsKey($relative)) { $duplicate++ } else { $seen[$relative] = $true }
        $path = Join-Path $Root ($relative -replace '/', '\')
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $missing++; continue }
        $item = Get-Item -LiteralPath $path -Force
        if ([int64]$item.Length -ne [int64]$entry.bytes) { $bytesMismatch++ }
        if ((Get-Sha256 $path) -ne ([string]$entry.sha256).ToUpperInvariant()) { $shaMismatch++ }
        if ([int64]$item.LastWriteTimeUtc.Ticks -ne [int64]$entry.last_write_utc_ticks) { $ticksMismatch++ }
    }
    $actual = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force |
        ForEach-Object { Get-RelativeSlashPath $Root $_.FullName })
    $expected = @($Entries | ForEach-Object { [string]$_.relative_path }) + @($ExcludedControls)
    $missingSet = @($expected | Where-Object { $_ -notin $actual })
    $extraSet = @($actual | Where-Object { $_ -notin $expected })
    return [ordered]@{
        manifest_rows = $Entries.Count
        expected_file_count = $expected.Count
        actual_file_count = $actual.Count
        duplicate_paths = $duplicate
        missing_paths = $missing + $missingSet.Count
        extra_paths = $extraSet.Count
        bytes_mismatch = $bytesMismatch
        sha256_mismatch = $shaMismatch
        last_write_ticks_mismatch = $ticksMismatch
    }
}

if ($PSVersionTable.PSEdition -ne 'Core') { throw 'PowerShell 7/Core is required.' }
if ($AuthorizationToken -ne 'MAIN_R324_P657_READONLY_CONTROL_RESEAL_AUTHORIZED') { throw 'Authorization token mismatch.' }
if (-not (Test-Path -LiteralPath $OldRoot -PathType Container)) { throw 'Old root missing.' }
if (Test-Path -LiteralPath $NewRoot) { throw 'New root must not exist at invocation start.' }
foreach ($externalPath in @($ClaimPath, $ResultPath, $AuditPath, $SealTempPath, $WstopTempPath)) {
    if (Test-Path -LiteralPath $externalPath) { throw "External controller artifact already exists: $externalPath" }
}

$controllerIdentity = [ordered]@{
    path = Resolve-ExactPath $ControllerPath
    bytes = (Get-Item -LiteralPath $ControllerPath).Length
    sha256 = Get-Sha256 $ControllerPath
}
$claim = [ordered]@{
    authorization = $AuthorizationToken
    invocation_ordinal = 1
    invocation_limit = 1
    retry_count = 0
    controller_pid = $PID
    started_utc = [DateTime]::UtcNow.ToString('o')
    controller = $controllerIdentity
    old_root = Resolve-ExactPath $OldRoot
    new_root = Resolve-ExactPath $NewRoot
}
Write-JsonExternal $ClaimPath $claim

$started = [DateTime]::UtcNow
$success = $false
$failure = $null
try {
    $oldManifestPath = Join-Path $OldRoot 'MANIFEST.json'
    $oldWstopPath = Join-Path $OldRoot 'WRITE_STOPPED'
    $oldManifest = Get-Content -LiteralPath $oldManifestPath -Raw | ConvertFrom-Json
    $oldEntries = @($oldManifest.files)
    if ($oldEntries.Count -ne 487) { throw "Old manifest rows must be 487, got $($oldEntries.Count)." }
    if (@($oldEntries | Where-Object { $_.path -in @('MANIFEST.json', 'WRITE_STOPPED') }).Count -ne 0) {
        throw 'Old controls unexpectedly occur in old manifest material.'
    }
    if (@($oldEntries.path | Sort-Object -Unique).Count -ne 487) { throw 'Old manifest has duplicate material paths.' }

    $oldActualRelativePaths = @(Get-ChildItem -LiteralPath $OldRoot -File -Recurse -Force |
        ForEach-Object { Get-RelativeSlashPath $OldRoot $_.FullName })
    $oldExpectedRelativePaths = @($oldEntries | ForEach-Object { [string]$_.path }) + @('MANIFEST.json', 'WRITE_STOPPED')
    $oldMissingPaths = @($oldExpectedRelativePaths | Where-Object { $_ -notin $oldActualRelativePaths })
    $oldExtraPaths = @($oldActualRelativePaths | Where-Object { $_ -notin $oldExpectedRelativePaths })
    if ($oldActualRelativePaths.Count -ne 489 -or $oldMissingPaths.Count -ne 0 -or $oldExtraPaths.Count -ne 0) {
        throw "Old root set gate failed: actual=$($oldActualRelativePaths.Count), missing=$($oldMissingPaths.Count), extra=$($oldExtraPaths.Count)."
    }

    $oldControlIdentityBefore = @(
        [ordered]@{ path = 'MANIFEST.json'; bytes = (Get-Item $oldManifestPath).Length; sha256 = Get-Sha256 $oldManifestPath; ticks = (Get-Item $oldManifestPath).LastWriteTimeUtc.Ticks },
        [ordered]@{ path = 'WRITE_STOPPED'; bytes = (Get-Item $oldWstopPath).Length; sha256 = Get-Sha256 $oldWstopPath; ticks = (Get-Item $oldWstopPath).LastWriteTimeUtc.Ticks }
    )

    New-Item -ItemType Directory -Path $NewRoot -Force | Out-Null
    $copyRows = [Collections.Generic.List[object]]::new()
    foreach ($entry in $oldEntries) {
        $relative = [string]$entry.path
        $sourcePath = Join-Path $OldRoot ($relative -replace '/', '\')
        $destinationPath = Join-Path $NewRoot ($relative -replace '/', '\')
        Assert-Within $sourcePath $OldRoot 'source material path'
        Assert-Within $destinationPath $NewRoot 'destination material path'
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Missing old material: $relative" }
        $destinationDirectory = Split-Path -Parent $destinationPath
        if (-not (Test-Path -LiteralPath $destinationDirectory)) {
            New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        }
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        [IO.File]::SetLastWriteTimeUtc($destinationPath, $sourceItem.LastWriteTimeUtc)
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $sourceSha = Get-Sha256 $sourcePath
        $destinationSha = Get-Sha256 $destinationPath
        $row = [ordered]@{
            relative_path = $relative
            source_resolved_path = Resolve-ExactPath $sourcePath
            destination_resolved_path = Resolve-ExactPath $destinationPath
            source_bytes = [int64]$sourceItem.Length
            destination_bytes = [int64]$destinationItem.Length
            source_sha256 = $sourceSha
            destination_sha256 = $destinationSha
            source_last_write_utc_ticks = [int64]$sourceItem.LastWriteTimeUtc.Ticks
            destination_last_write_utc_ticks = [int64]$destinationItem.LastWriteTimeUtc.Ticks
            identity_match = ([int64]$sourceItem.Length -eq [int64]$destinationItem.Length -and $sourceSha -eq $destinationSha -and [int64]$sourceItem.LastWriteTimeUtc.Ticks -eq [int64]$destinationItem.LastWriteTimeUtc.Ticks)
        }
        if (-not $row.identity_match) { throw "Copy identity mismatch: $relative" }
        $copyRows.Add([pscustomobject]$row)
    }

    $copyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
    $copyRows | ConvertTo-Csv -NoTypeInformation | Set-Content -LiteralPath $copyIdentityPath -Encoding utf8NoBOM
    if (@(Import-Csv -LiteralPath $copyIdentityPath).Count -ne 487) { throw 'COPY_IDENTITY row count mismatch.' }

    $provenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
    $provenance = [ordered]@{
        schema = 'P657_R111_SA2_READONLY_RESEAL_PROVENANCE_V1'
        handoff_id = 'C-FIG-P657-01-R111-SA2-R168-READONLY-RESEAL-V1'
        authorization = $AuthorizationToken
        controller = $controllerIdentity
        invocation_ordinal = 1
        invocation_limit = 1
        retry_count = 0
        old_root_resolved = Resolve-ExactPath $OldRoot
        new_root_resolved = Resolve-ExactPath $NewRoot
        old_manifest = [ordered]@{ path = Resolve-ExactPath $oldManifestPath; bytes = (Get-Item $oldManifestPath).Length; sha256 = Get-Sha256 $oldManifestPath }
        old_write_stopped = [ordered]@{ path = Resolve-ExactPath $oldWstopPath; bytes = (Get-Item $oldWstopPath).Length; sha256 = Get-Sha256 $oldWstopPath }
        copied_material_count = 487
        copied_old_controls = [ordered]@{ manifest_json = 0; write_stopped = 0 }
        added_payload = @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json')
        projected_payload_count = 489
        projected_controls = @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
        projected_ordinary_count = 492
        business_decision_unchanged = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
        evidence_only = $true
    }
    Write-JsonExternal $provenancePath $provenance

    $payloadFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    if ($payloadFiles.Count -ne 489) { throw "Payload count must be 489, got $($payloadFiles.Count)." }
    $payloadEntries = @($payloadFiles | ForEach-Object {
        [ordered]@{
            relative_path = Get-RelativeSlashPath $NewRoot $_.FullName
            bytes = [int64]$_.Length
            sha256 = Get-Sha256 $_.FullName
            last_write_utc_ticks = [int64]$_.LastWriteTimeUtc.Ticks
        }
    } | Sort-Object relative_path)
    $payloadManifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.json'
    $payloadManifest = [ordered]@{
        schema = 'P657_R111_SA2_READONLY_RESEAL_PAYLOAD_MANIFEST_V1'
        handoff_id = 'C-FIG-P657-01-R111-SA2-R168-READONLY-RESEAL-V1'
        root_resolved = Resolve-ExactPath $NewRoot
        payload_count = 489
        control_exclusions = @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
        entries = $payloadEntries
    }
    Write-JsonExternal $payloadManifestPath $payloadManifest

    $manifestGatePayloadOnly = Get-ManifestGate $NewRoot $payloadEntries @('PAYLOAD_MANIFEST.json')
    foreach ($key in @('duplicate_paths','missing_paths','extra_paths','bytes_mismatch','sha256_mismatch','last_write_ticks_mismatch')) {
        if ([int]$manifestGatePayloadOnly[$key] -ne 0) { throw "Pre-seal payload manifest gate failed: $key" }
    }
    $hygieneBeforeSeal = Get-Hygiene $NewRoot
    foreach ($key in @('json_parse_failures','csv_parse_failures','ads_count','cache_pyc_count','reparse_count')) {
        if ([int]$hygieneBeforeSeal[$key] -ne 0) { throw "Pre-seal hygiene gate failed: $key" }
    }

    $preSealFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    if ($preSealFiles.Count -ne 490) { throw "Expected 490 files before SEAL_AUDIT, got $($preSealFiles.Count)." }
    foreach ($file in $preSealFiles) { Set-ReadOnlyBit $file.FullName }
    $preSealDirs = @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force | Sort-Object FullName -Descending)
    foreach ($dir in $preSealDirs) { Set-ReadOnlyBit $dir.FullName }
    Set-ReadOnlyBit $NewRoot
    $readonly490 = Get-ReadonlyGate $NewRoot
    if ($readonly490.file_count -ne 490 -or $readonly490.writable_file_count -ne 0 -or $readonly490.writable_directory_count_including_root -ne 0) {
        throw 'Readonly gate for 490 pre-SEAL files/directories failed.'
    }

    $sealAudit = [ordered]@{
        schema = 'P657_R111_SA2_READONLY_RESEAL_AUDIT_V1'
        handoff_id = 'C-FIG-P657-01-R111-SA2-R168-READONLY-RESEAL-V1'
        old_root_resolved = Resolve-ExactPath $OldRoot
        new_root_resolved = Resolve-ExactPath $NewRoot
        business_decision = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
        old_material_rows = 487
        copied_material_identity_mismatch = @($copyRows | Where-Object { -not $_.identity_match }).Count
        payload_count = 489
        payload_manifest_gate = $manifestGatePayloadOnly
        hygiene_before_seal = $hygieneBeforeSeal
        readonly_gate_before_this_control_move = $readonly490
        old_controls_copied = 0
        invocation_ordinal = 1
        retry_count = 0
        next_control_move = 'SEAL_AUDIT.json moved from outside root as read-only file'
        final_marker_contract = 'WRITE_STOPPED precreated outside root, read-only, strict-latest, moved as unique final root-content operation'
    }
    Write-JsonExternal $SealTempPath $sealAudit
    Set-ReadOnlyBit $SealTempPath
    Move-Item -LiteralPath $SealTempPath -Destination (Join-Path $NewRoot 'SEAL_AUDIT.json')

    $readonly491 = Get-ReadonlyGate $NewRoot
    if ($readonly491.file_count -ne 491 -or $readonly491.writable_file_count -ne 0 -or $readonly491.writable_directory_count_including_root -ne 0) {
        throw 'Readonly gate for 491 pre-WSTOP files/directories failed.'
    }
    $hygiene491 = Get-Hygiene $NewRoot
    foreach ($key in @('json_parse_failures','csv_parse_failures','ads_count','cache_pyc_count','reparse_count')) {
        if ([int]$hygiene491[$key] -ne 0) { throw "Pre-WSTOP hygiene gate failed: $key" }
    }

    $sealAuditPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
    $manifestItem = Get-Item -LiteralPath $payloadManifestPath
    $sealAuditItem = Get-Item -LiteralPath $sealAuditPath
    $copyIdentityItem = Get-Item -LiteralPath $copyIdentityPath
    $provenanceItem = Get-Item -LiteralPath $provenancePath
    $maxTicksBeforeMarker = (@(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force |
        ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
    $markerTicks = [int64]$maxTicksBeforeMarker + 10000000
    $markerTime = [DateTime]::new($markerTicks, [DateTimeKind]::Utc)
    $wstop = [ordered]@{
        schema = 'P657_R111_SA2_READONLY_RESEAL_WRITE_STOPPED_V1'
        handoff_id = 'C-FIG-P657-01-R111-SA2-R168-READONLY-RESEAL-V1'
        result = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
        root_resolved = Resolve-ExactPath $NewRoot
        invocation_ordinal = 1
        invocation_limit = 1
        retry_count = 0
        copied_material_count = 487
        payload_count = 489
        control_count = 3
        ordinary_file_count_after_marker = 492
        readonly_gate_before_marker = $readonly491
        hygiene_before_marker = $hygiene491
        copy_identity = [ordered]@{ path = Resolve-ExactPath $copyIdentityPath; bytes = $copyIdentityItem.Length; sha256 = Get-Sha256 $copyIdentityPath }
        copy_provenance = [ordered]@{ path = Resolve-ExactPath $provenancePath; bytes = $provenanceItem.Length; sha256 = Get-Sha256 $provenancePath }
        payload_manifest = [ordered]@{ path = Resolve-ExactPath $payloadManifestPath; bytes = $manifestItem.Length; sha256 = Get-Sha256 $payloadManifestPath; rows = 489 }
        seal_audit = [ordered]@{ path = Resolve-ExactPath $sealAuditPath; bytes = $sealAuditItem.Length; sha256 = Get-Sha256 $sealAuditPath }
        old_root_zero_write_check_pending_external_audit = $true
        marker_last_write_utc_ticks = $markerTicks
        post_marker_root_content_or_attribute_writes_permitted = 0
    }
    Write-JsonExternal $WstopTempPath $wstop
    [IO.File]::SetLastWriteTimeUtc($WstopTempPath, $markerTime)
    Set-ReadOnlyBit $WstopTempPath
    $tempMarkerItem = Get-Item -LiteralPath $WstopTempPath -Force
    if (-not $tempMarkerItem.IsReadOnly -or $tempMarkerItem.LastWriteTimeUtc.Ticks -ne $markerTicks) {
        throw 'External WSTOP precreation gate failed.'
    }
    $null = Get-Content -LiteralPath $WstopTempPath -Raw | ConvertFrom-Json

    # Sole final root-content operation. No root attribute or content mutation is permitted after this move.
    Move-Item -LiteralPath $WstopTempPath -Destination (Join-Path $NewRoot 'WRITE_STOPPED')

    $finalFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    $finalDirs = @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force)
    $finalReadonly = Get-ReadonlyGate $NewRoot
    $finalHygiene = Get-Hygiene $NewRoot
    $finalManifestGate = Get-ManifestGate $NewRoot $payloadEntries @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
    $markerPath = Join-Path $NewRoot 'WRITE_STOPPED'
    $markerItem = Get-Item -LiteralPath $markerPath -Force
    $atOrAfterExcludingMarker = @($finalFiles | Where-Object {
        $_.FullName -ne $markerItem.FullName -and $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks
    }).Count
    $markerCount = @($finalFiles | Where-Object { $_.Name -eq 'WRITE_STOPPED' }).Count

    $oldMismatchAfter = 0
    foreach ($entry in $oldEntries) {
        $relative = [string]$entry.path
        $sourcePath = Join-Path $OldRoot ($relative -replace '/', '\')
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        $copyRow = $copyRows | Where-Object { $_.relative_path -eq $relative } | Select-Object -First 1
        if ([int64]$sourceItem.Length -ne [int64]$entry.bytes -or
            (Get-Sha256 $sourcePath) -ne ([string]$entry.sha256).ToUpperInvariant() -or
            [int64]$sourceItem.LastWriteTimeUtc.Ticks -ne [int64]$copyRow.source_last_write_utc_ticks) {
            $oldMismatchAfter++
        }
    }
    $oldControlIdentityAfter = @(
        [ordered]@{ path = 'MANIFEST.json'; bytes = (Get-Item $oldManifestPath).Length; sha256 = Get-Sha256 $oldManifestPath; ticks = (Get-Item $oldManifestPath).LastWriteTimeUtc.Ticks },
        [ordered]@{ path = 'WRITE_STOPPED'; bytes = (Get-Item $oldWstopPath).Length; sha256 = Get-Sha256 $oldWstopPath; ticks = (Get-Item $oldWstopPath).LastWriteTimeUtc.Ticks }
    )
    $oldControlsChanged = 0
    for ($i = 0; $i -lt 2; $i++) {
        if (($oldControlIdentityBefore[$i] | ConvertTo-Json -Compress) -ne ($oldControlIdentityAfter[$i] | ConvertTo-Json -Compress)) { $oldControlsChanged++ }
    }

    $audit = [ordered]@{
        schema = 'P657_R111_SA2_READONLY_RESEAL_ROOT_EXTERNAL_AUDIT_V1'
        controller = $controllerIdentity
        invocation_ordinal = 1
        retry_count = 0
        controller_pid = $PID
        old_root_resolved = Resolve-ExactPath $OldRoot
        new_root_resolved = Resolve-ExactPath $NewRoot
        old_material_rows = 487
        old_root_ordinary_files_before = $oldActualRelativePaths.Count
        old_root_missing_paths_before = $oldMissingPaths.Count
        old_root_extra_paths_before = $oldExtraPaths.Count
        old_material_post_operation_identity_mismatch = $oldMismatchAfter
        old_control_identity_changes = $oldControlsChanged
        source_to_destination_identity_mismatch = @($copyRows | Where-Object { -not $_.identity_match }).Count
        payload_count = 489
        control_count = 3
        ordinary_file_count = $finalFiles.Count
        manifest_gate = $finalManifestGate
        readonly_gate = $finalReadonly
        hygiene = $finalHygiene
        write_stopped_count = $markerCount
        write_stopped_ticks = $markerItem.LastWriteTimeUtc.Ticks
        at_or_after_excluding_marker = $atOrAfterExcludingMarker
        postmarker_root_content_or_attribute_writes = 0
        business_decision = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
        success = ($oldMismatchAfter -eq 0 -and $oldControlsChanged -eq 0 -and
            @($copyRows | Where-Object { -not $_.identity_match }).Count -eq 0 -and
            $finalFiles.Count -eq 492 -and $finalManifestGate.duplicate_paths -eq 0 -and
            $finalManifestGate.missing_paths -eq 0 -and $finalManifestGate.extra_paths -eq 0 -and
            $finalManifestGate.bytes_mismatch -eq 0 -and $finalManifestGate.sha256_mismatch -eq 0 -and
            $finalManifestGate.last_write_ticks_mismatch -eq 0 -and
            $finalReadonly.writable_file_count -eq 0 -and $finalReadonly.writable_directory_count_including_root -eq 0 -and
            $finalHygiene.json_parse_failures -eq 0 -and $finalHygiene.csv_parse_failures -eq 0 -and
            $finalHygiene.ads_count -eq 0 -and $finalHygiene.cache_pyc_count -eq 0 -and $finalHygiene.reparse_count -eq 0 -and
            $markerCount -eq 1 -and $atOrAfterExcludingMarker -eq 0)
    }
    Write-JsonExternal $AuditPath $audit
    if (-not $audit.success) { throw 'Root-external final audit failed. No repair or retry is permitted.' }
    $success = $true
} catch {
    $failure = $_.Exception.Message
    throw
} finally {
    $result = [ordered]@{
        invocation_ordinal = 1
        invocation_limit = 1
        retry_count = 0
        controller_pid = $PID
        started_utc = $started.ToString('o')
        finished_utc = [DateTime]::UtcNow.ToString('o')
        success = $success
        failure = $failure
        controller = $controllerIdentity
        old_root = Resolve-ExactPath $OldRoot
        new_root = Resolve-ExactPath $NewRoot
        external_audit_path = Resolve-ExactPath $AuditPath
    }
    Write-JsonExternal $ResultPath $result
}
