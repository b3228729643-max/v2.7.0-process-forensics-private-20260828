#requires -Version 7.0

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$HandoffId = 'C-FIG-P662-01-R112-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1'
$Uid = 'FIG-P662-01'
$Verdict = 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
$SourceRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa1_r112_fresh_isolated_v1')
$NewRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P662-01\sa1_r112_fresh_isolated_v1_control_reseal_v1')
$OldManifestPath = [IO.Path]::Combine($SourceRoot, 'controls', 'manifest.csv')
$ExternalResultPath = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\P662_SA1_CONTROL_RESEAL_V1_RESULT.json')
$ExternalMarkerPath = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\P662_SA1_CONTROL_RESEAL_V1_WRITE_STOPPED.precreated')
$Utf8NoBom = [Text.UTF8Encoding]::new($false)
$MarkerMoved = $false
$StartedUtc = [DateTime]::UtcNow

function Get-Sha256([string]$LiteralPath) {
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativeForward([string]$Root, [string]$Path) {
    return [IO.Path]::GetRelativePath($Root, $Path).Replace('\', '/')
}

function Get-FileIdentity([string]$Root, [string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    return [pscustomobject]@{
        relative_path = Get-RelativeForward $Root $item.FullName
        bytes = [int64]$item.Length
        sha256 = Get-Sha256 $item.FullName
        creation_filetime_utc_ticks = [int64]$item.CreationTimeUtc.ToFileTimeUtc()
        last_write_filetime_utc_ticks = [int64]$item.LastWriteTimeUtc.ToFileTimeUtc()
        attributes = $item.Attributes.ToString()
    }
}

function Get-RootFileSnapshot([string]$Root) {
    $map = [ordered]@{}
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Sort-Object FullName)) {
        $identity = Get-FileIdentity $Root $file.FullName
        $map[$identity.relative_path] = $identity
    }
    return $map
}

function Get-RootDirectorySnapshot([string]$Root) {
    $map = [ordered]@{}
    $directories = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force | Sort-Object FullName)
    foreach ($directory in $directories) {
        $relative = if ($directory.FullName -eq $Root) { '.' } else { Get-RelativeForward $Root $directory.FullName }
        $map[$relative] = [pscustomobject]@{
            relative_path = $relative
            creation_filetime_utc_ticks = [int64]$directory.CreationTimeUtc.ToFileTimeUtc()
            last_write_filetime_utc_ticks = [int64]$directory.LastWriteTimeUtc.ToFileTimeUtc()
            attributes = $directory.Attributes.ToString()
        }
    }
    return $map
}

function Compare-IdentityMaps($Left, $Right) {
    $mismatches = [System.Collections.Generic.List[string]]::new()
    foreach ($key in $Left.Keys) {
        if (-not $Right.Contains($key)) {
            $mismatches.Add("missing:$key")
            continue
        }
        $a = $Left[$key]
        $b = $Right[$key]
        foreach ($field in @('bytes', 'sha256', 'creation_filetime_utc_ticks', 'last_write_filetime_utc_ticks', 'attributes')) {
            if ($a.PSObject.Properties.Name -contains $field -and $b.PSObject.Properties.Name -contains $field) {
                if ([string]$a.$field -cne [string]$b.$field) {
                    $mismatches.Add("${key}:$field")
                }
            }
        }
    }
    foreach ($key in $Right.Keys) {
        if (-not $Left.Contains($key)) {
            $mismatches.Add("extra:$key")
        }
    }
    return @($mismatches)
}

function Set-ReadOnlyAttribute([string]$Path) {
    $attributes = [IO.File]::GetAttributes($Path)
    [IO.File]::SetAttributes($Path, ($attributes -bor [IO.FileAttributes]::ReadOnly))
}

function Get-Hygiene([string]$Root) {
    $files = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)
    $directories = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force)
    $ads = @($files | ForEach-Object {
        Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue |
            Where-Object { $_.Stream -notin @(':$DATA', '$DATA') }
    })
    $cache = @($files | Where-Object {
        $_.FullName -match '(?i)(^|[\\/])(__pycache__|\.pytest_cache|\.mypy_cache|\.cache)([\\/]|$)|\.(pyc|pyo)$'
    })
    $reparse = @($files + $directories | Where-Object {
        ([IO.File]::GetAttributes($_.FullName) -band [IO.FileAttributes]::ReparsePoint) -ne 0
    })
    return [pscustomobject]@{
        ads_count = $ads.Count
        cache_pyc_count = $cache.Count
        reparse_count = $reparse.Count
    }
}

function Assert-ParseablePayload([string]$Root) {
    $errors = [System.Collections.Generic.List[string]]::new()
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)) {
        try {
            if ($file.Extension -ieq '.json') {
                Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null
            }
            elseif ($file.Extension -ieq '.csv') {
                Import-Csv -LiteralPath $file.FullName | Out-Null
            }
        }
        catch {
            $errors.Add((Get-RelativeForward $Root $file.FullName))
        }
    }
    if ($errors.Count -ne 0) {
        throw "Parse failures: $($errors -join ', ')"
    }
}

function Assert-Manifest([string]$Root, [string]$ManifestPath, [string[]]$ControlRelatives, [int]$ExpectedRows) {
    $rows = @(Import-Csv -LiteralPath $ManifestPath)
    if ($rows.Count -ne $ExpectedRows) { throw "Manifest row count $($rows.Count), expected $ExpectedRows" }
    if (@($rows | Group-Object relative_path | Where-Object Count -gt 1).Count -ne 0) { throw 'Duplicate manifest paths' }
    $mismatch = [System.Collections.Generic.List[string]]::new()
    foreach ($row in $rows) {
        $path = [IO.Path]::Combine($Root, $row.relative_path.Replace('/', '\'))
        if (-not [IO.File]::Exists($path)) {
            $mismatch.Add("missing:$($row.relative_path)")
            continue
        }
        $identity = Get-FileIdentity $Root $path
        if ([int64]$row.bytes -ne $identity.bytes) { $mismatch.Add("bytes:$($row.relative_path)") }
        if ([string]$row.sha256 -cne $identity.sha256) { $mismatch.Add("sha:$($row.relative_path)") }
        if ([int64]$row.creation_filetime_utc_ticks -ne $identity.creation_filetime_utc_ticks) { $mismatch.Add("creation:$($row.relative_path)") }
        if ([int64]$row.last_write_filetime_utc_ticks -ne $identity.last_write_filetime_utc_ticks) { $mismatch.Add("lastwrite:$($row.relative_path)") }
    }
    $all = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object { Get-RelativeForward $Root $_.FullName })
    $payloadFs = @($all | Where-Object { $_ -notin $ControlRelatives })
    $extra = @($payloadFs | Where-Object { $_ -notin $rows.relative_path })
    $unlisted = @($rows.relative_path | Where-Object { $_ -notin $payloadFs })
    if ($mismatch.Count -ne 0 -or $extra.Count -ne 0 -or $unlisted.Count -ne 0) {
        throw "Manifest mismatch=$($mismatch.Count), extra=$($extra.Count), unlisted=$($unlisted.Count)"
    }
    return [pscustomobject]@{
        rows = $rows.Count
        identity_mismatch = $mismatch.Count
        extra = $extra.Count
        unlisted = $unlisted.Count
    }
}

function Write-ExternalResult($Object) {
    $json = $Object | ConvertTo-Json -Depth 12
    [IO.File]::WriteAllText($ExternalResultPath, $json + [Environment]::NewLine, $Utf8NoBom)
    Set-ReadOnlyAttribute $ExternalResultPath
}

try {
    if (-not [IO.Directory]::Exists($SourceRoot)) { throw 'Source root missing' }
    if ([IO.Directory]::Exists($NewRoot) -or [IO.File]::Exists($NewRoot)) { throw 'New root already exists' }
    if ([IO.File]::Exists($ExternalResultPath) -or [IO.File]::Exists($ExternalMarkerPath)) { throw 'External result or marker already exists' }

    $tokens = $null
    $parseErrors = $null
    $null = [Management.Automation.Language.Parser]::ParseFile($PSCommandPath, [ref]$tokens, [ref]$parseErrors)
    if ($parseErrors.Count -ne 0) { throw "Controller AST parse errors: $($parseErrors.Count)" }

    $controllerIdentity = Get-FileIdentity ([IO.Path]::GetDirectoryName($PSCommandPath)) $PSCommandPath
    $sourceBefore = Get-RootFileSnapshot $SourceRoot
    $oldRows = @(Import-Csv -LiteralPath $OldManifestPath)
    if ($oldRows.Count -ne 42) { throw "Old manifest rows $($oldRows.Count), expected 42" }
    if (@($oldRows | Group-Object relative_path | Where-Object Count -gt 1).Count -ne 0) { throw 'Old manifest duplicate paths' }
    if (@($oldRows | Where-Object { $_.relative_path -in @('controls/manifest.csv', 'WRITE_STOPPED') }).Count -ne 0) { throw 'Old control unexpectedly bound as material' }

    [IO.Directory]::CreateDirectory($NewRoot) | Out-Null
    $copyRows = [System.Collections.Generic.List[object]]::new()
    foreach ($row in $oldRows) {
        $relative = [string]$row.relative_path
        $sourcePath = [IO.Path]::Combine($SourceRoot, $relative.Replace('/', '\'))
        $destPath = [IO.Path]::Combine($NewRoot, $relative.Replace('/', '\'))
        if (-not [IO.File]::Exists($sourcePath)) { throw "Material source missing: $relative" }
        $sourceIdentity = Get-FileIdentity $SourceRoot $sourcePath
        if ($sourceIdentity.bytes -ne [int64]$row.bytes -or $sourceIdentity.sha256 -cne [string]$row.sha256 -or
            $sourceIdentity.creation_filetime_utc_ticks -ne [int64]$row.creation_filetime_utc_ticks -or
            $sourceIdentity.last_write_filetime_utc_ticks -ne [int64]$row.last_write_filetime_utc_ticks) {
            throw "Old manifest identity mismatch: $relative"
        }
        [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destPath)) | Out-Null
        [IO.File]::Copy($sourcePath, $destPath, $false)
        [IO.File]::SetCreationTimeUtc($destPath, [DateTime]::FromFileTimeUtc([int64]$row.creation_filetime_utc_ticks))
        [IO.File]::SetLastWriteTimeUtc($destPath, [DateTime]::FromFileTimeUtc([int64]$row.last_write_filetime_utc_ticks))
        $destIdentity = Get-FileIdentity $NewRoot $destPath
        if ($sourceIdentity.bytes -ne $destIdentity.bytes -or $sourceIdentity.sha256 -cne $destIdentity.sha256 -or
            $sourceIdentity.creation_filetime_utc_ticks -ne $destIdentity.creation_filetime_utc_ticks -or
            $sourceIdentity.last_write_filetime_utc_ticks -ne $destIdentity.last_write_filetime_utc_ticks) {
            throw "Copy identity mismatch: $relative"
        }
        $copyRows.Add([pscustomobject]@{
            relative_path = $relative
            source_resolved_path = $sourcePath
            destination_resolved_path = $destPath
            source_bytes = $sourceIdentity.bytes
            destination_bytes = $destIdentity.bytes
            source_sha256 = $sourceIdentity.sha256
            destination_sha256 = $destIdentity.sha256
            source_creation_filetime_utc_ticks = $sourceIdentity.creation_filetime_utc_ticks
            destination_creation_filetime_utc_ticks = $destIdentity.creation_filetime_utc_ticks
            source_last_write_filetime_utc_ticks = $sourceIdentity.last_write_filetime_utc_ticks
            destination_last_write_filetime_utc_ticks = $destIdentity.last_write_filetime_utc_ticks
            mismatch_count = 0
        })
    }

    $copyIdentityPath = [IO.Path]::Combine($NewRoot, 'COPY_IDENTITY.csv')
    $copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8

    $oldManifestItem = Get-Item -LiteralPath $OldManifestPath -Force
    $copyProvenancePath = [IO.Path]::Combine($NewRoot, 'COPY_PROVENANCE.json')
    $provenance = [ordered]@{
        handoff_id = $HandoffId
        uid = $Uid
        operation = 'evidence-only sibling control reseal'
        source_root_resolved = $SourceRoot
        destination_root_resolved = $NewRoot
        source_manifest_resolved = $OldManifestPath
        source_manifest_bytes = [int64]$oldManifestItem.Length
        source_manifest_sha256 = Get-Sha256 $OldManifestPath
        copied_material_count = 42
        excluded_old_manifest_count = 1
        excluded_old_write_stopped_count = 1
        old_controls_copied = 0
        copy_identity_relative_path = 'COPY_IDENTITY.csv'
        copy_identity_rows = 42
        material_identity_mismatch_count = 0
        business_evidence_rerun = 0
        visual_object_pair_manual_math_semantic_rerun = 0
        source_pdf_tex_git_central_writes = 0
        verdict_preserved = $Verdict
        controller_resolved_path = $PSCommandPath
        controller_bytes = $controllerIdentity.bytes
        controller_sha256 = $controllerIdentity.sha256
        invocation_ordinal = 1
        retry_count = 0
    }
    [IO.File]::WriteAllText($copyProvenancePath, (($provenance | ConvertTo-Json -Depth 8) + [Environment]::NewLine), $Utf8NoBom)

    $payloadPaths = [System.Collections.Generic.List[string]]::new()
    foreach ($row in $oldRows) { $payloadPaths.Add([string]$row.relative_path) }
    $payloadPaths.Add('COPY_IDENTITY.csv')
    $payloadPaths.Add('COPY_PROVENANCE.json')
    if ($payloadPaths.Count -ne 44 -or @($payloadPaths | Sort-Object -Unique).Count -ne 44) { throw 'Projected payload count or uniqueness failed' }

    $manifestRows = [System.Collections.Generic.List[object]]::new()
    foreach ($relative in @($payloadPaths | Sort-Object)) {
        $path = [IO.Path]::Combine($NewRoot, $relative.Replace('/', '\'))
        $identity = Get-FileIdentity $NewRoot $path
        $manifestRows.Add([pscustomobject]@{
            relative_path = $relative
            bytes = $identity.bytes
            sha256 = $identity.sha256
            creation_filetime_utc_ticks = $identity.creation_filetime_utc_ticks
            last_write_filetime_utc_ticks = $identity.last_write_filetime_utc_ticks
        })
    }
    $manifestPath = [IO.Path]::Combine($NewRoot, 'PAYLOAD_MANIFEST.csv')
    $manifestRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8
    $manifestHash = Get-Sha256 $manifestPath

    $copyCheckMismatch = 0
    foreach ($copy in $copyRows) {
        $destIdentity = Get-FileIdentity $NewRoot $copy.destination_resolved_path
        if ($destIdentity.bytes -ne $copy.source_bytes -or $destIdentity.sha256 -cne $copy.source_sha256 -or
            $destIdentity.creation_filetime_utc_ticks -ne $copy.source_creation_filetime_utc_ticks -or
            $destIdentity.last_write_filetime_utc_ticks -ne $copy.source_last_write_filetime_utc_ticks) {
            $copyCheckMismatch++
        }
    }
    if ($copyCheckMismatch -ne 0) { throw "Copy recheck mismatch count $copyCheckMismatch" }

    Assert-ParseablePayload $NewRoot
    $hygieneBeforeAudit = Get-Hygiene $NewRoot
    if ($hygieneBeforeAudit.ads_count -ne 0 -or $hygieneBeforeAudit.cache_pyc_count -ne 0 -or $hygieneBeforeAudit.reparse_count -ne 0) { throw 'Preseal hygiene failed' }

    $manifestCheck = Assert-Manifest $NewRoot $manifestPath @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED') 44
    $sealAuditPath = [IO.Path]::Combine($NewRoot, 'SEAL_AUDIT.json')
    $sealAudit = [ordered]@{
        handoff_id = $HandoffId
        uid = $Uid
        source_root_resolved = $SourceRoot
        sealed_root_resolved = $NewRoot
        old_manifest_bound_material_count = 42
        old_controls_copied = 0
        copy_identity_rows = 42
        copy_identity_mismatch_count = $copyCheckMismatch
        payload_count = 44
        manifest_rows = $manifestCheck.rows
        manifest_identity_mismatch = $manifestCheck.identity_mismatch
        manifest_extra = $manifestCheck.extra
        manifest_unlisted = $manifestCheck.unlisted
        payload_manifest_relative_path = 'PAYLOAD_MANIFEST.csv'
        payload_manifest_sha256 = $manifestHash
        json_csv_parse_failures = 0
        ads_count = $hygieneBeforeAudit.ads_count
        cache_pyc_count = $hygieneBeforeAudit.cache_pyc_count
        reparse_count = $hygieneBeforeAudit.reparse_count
        projected_controls = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
        projected_ordinary_count = 47
        marker_contract = 'precreated outside root after all root premarker operations; explicit key=value validation; ReadOnly; single move is final root-content operation'
        verdict = $Verdict
    }
    [IO.File]::WriteAllText($sealAuditPath, (($sealAudit | ConvertTo-Json -Depth 8) + [Environment]::NewLine), $Utf8NoBom)
    Get-Content -LiteralPath $sealAuditPath -Raw | ConvertFrom-Json | Out-Null
    Assert-ParseablePayload $NewRoot

    $hygienePreMarker = Get-Hygiene $NewRoot
    if ($hygienePreMarker.ads_count -ne 0 -or $hygienePreMarker.cache_pyc_count -ne 0 -or $hygienePreMarker.reparse_count -ne 0) { throw 'Final premarker hygiene failed' }

    $preMarkerFiles = @(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)
    if ($preMarkerFiles.Count -ne 46) { throw "Premarker file count $($preMarkerFiles.Count), expected 46" }
    foreach ($file in $preMarkerFiles) { Set-ReadOnlyAttribute $file.FullName }
    $preMarkerDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force | Sort-Object { $_.FullName.Length } -Descending)
    foreach ($directory in $preMarkerDirectories) { Set-ReadOnlyAttribute $directory.FullName }

    $preMarkerFiles = @(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)
    $preMarkerDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force)
    $preMarkerWritableFiles = @($preMarkerFiles | Where-Object { ([IO.File]::GetAttributes($_.FullName) -band [IO.FileAttributes]::ReadOnly) -eq 0 })
    $preMarkerWritableDirectories = @($preMarkerDirectories | Where-Object { ([IO.File]::GetAttributes($_.FullName) -band [IO.FileAttributes]::ReadOnly) -eq 0 })
    if ($preMarkerWritableFiles.Count -ne 0 -or $preMarkerWritableDirectories.Count -ne 0) { throw 'ReadOnly premarker gate failed' }

    $sealAuditHash = Get-Sha256 $sealAuditPath
    $maxPreMarkerFileTime = ($preMarkerFiles | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
    $markerFileTime = [int64]$maxPreMarkerFileTime + 10000000
    $markerLines = @(
        "WRITE_STOPPED=CONTROL_RESEAL_COMPLETE",
        "HANDOFF_ID=$HandoffId",
        "UID=$Uid",
        'ROLE=FRESH_ISOLATED_SA1_CONTROL_RESEAL',
        "SOURCE_ROOT=$SourceRoot",
        "SEALED_ROOT=$NewRoot",
        'MATERIAL_COUNT=42',
        'COPY_IDENTITY_ROWS=42',
        'PAYLOAD_COUNT=44',
        'MANIFEST_ROWS=44',
        "MANIFEST_SHA256=$manifestHash",
        "SEAL_AUDIT_SHA256=$sealAuditHash",
        'CONTROL_COUNT=3',
        'ORDINARY_COUNT=47',
        "DIRECTORY_COUNT_INCLUDING_ROOT=$($preMarkerDirectories.Count)",
        'ROOT_READONLY_PREMARKER=PASS',
        'ALL_PREMARKER_FILES_READONLY=PASS',
        'FINAL_ROOT_CONTENT_OPERATION=SINGLE_ATOMIC_MOVE_OF_THIS_PRECREATED_MARKER',
        'POST_MARKER_CONTENT_WRITES=0',
        'POST_MARKER_ATTRIBUTE_CHANGES=0',
        "VERDICT=$Verdict"
    )
    [IO.File]::WriteAllLines($ExternalMarkerPath, $markerLines, $Utf8NoBom)
    $markerTime = [DateTime]::FromFileTimeUtc($markerFileTime)
    [IO.File]::SetCreationTimeUtc($ExternalMarkerPath, $markerTime)
    [IO.File]::SetLastWriteTimeUtc($ExternalMarkerPath, $markerTime)
    Set-ReadOnlyAttribute $ExternalMarkerPath

    $markerRaw = [IO.File]::ReadAllText($ExternalMarkerPath, $Utf8NoBom)
    if ($markerRaw.Contains("`t") -or $markerRaw -match '(?i)<[^>]+>|TBD|PLACEHOLDER|(^|[^A-Za-z])rue([^A-Za-z]|$)') { throw 'Marker contains tab, placeholder, or malformed rue token' }
    $parsedMarker = [ordered]@{}
    foreach ($line in [IO.File]::ReadAllLines($ExternalMarkerPath, $Utf8NoBom)) {
        if ($line -notmatch '^[^=\t]+=[^\t]+$') { throw "Malformed marker line: $line" }
        $parts = $line.Split('=', 2)
        if ([string]::IsNullOrWhiteSpace($parts[0]) -or [string]::IsNullOrWhiteSpace($parts[1])) { throw "Empty marker key/value: $line" }
        if ($parsedMarker.Contains($parts[0])) { throw "Duplicate marker key: $($parts[0])" }
        $parsedMarker[$parts[0]] = $parts[1]
    }
    $requiredExact = [ordered]@{
        HANDOFF_ID = $HandoffId
        UID = $Uid
        SEALED_ROOT = $NewRoot
        MANIFEST_ROWS = '44'
        MANIFEST_SHA256 = $manifestHash
        VERDICT = $Verdict
    }
    foreach ($key in $requiredExact.Keys) {
        if (-not $parsedMarker.Contains($key) -or [string]$parsedMarker[$key] -cne [string]$requiredExact[$key]) { throw "Marker key mismatch: $key" }
    }

    $markerDestination = [IO.Path]::Combine($NewRoot, 'WRITE_STOPPED')
    [IO.File]::Move($ExternalMarkerPath, $markerDestination)
    $MarkerMoved = $true

    $postMoveFilesBeforeAudit = Get-RootFileSnapshot $NewRoot
    $postMoveDirectoriesBeforeAudit = Get-RootDirectorySnapshot $NewRoot
    $finalFiles = @(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)
    $finalDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force)
    if ($finalFiles.Count -ne 47) { throw "Final ordinary count $($finalFiles.Count), expected 47" }
    $readOnlyFiles = @($finalFiles | Where-Object { ([IO.File]::GetAttributes($_.FullName) -band [IO.FileAttributes]::ReadOnly) -ne 0 })
    $readOnlyDirectories = @($finalDirectories | Where-Object { ([IO.File]::GetAttributes($_.FullName) -band [IO.FileAttributes]::ReadOnly) -ne 0 })
    if ($readOnlyFiles.Count -ne 47 -or $readOnlyDirectories.Count -ne $finalDirectories.Count) { throw 'Final ReadOnly audit failed' }

    $markers = @($finalFiles | Where-Object Name -ceq 'WRITE_STOPPED')
    if ($markers.Count -ne 1) { throw "Marker count $($markers.Count), expected 1" }
    $markerItem = $markers[0]
    $otherFiles = @($finalFiles | Where-Object FullName -cne $markerItem.FullName)
    $atOrAfter = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerItem.LastWriteTimeUtc.ToFileTimeUtc() })
    if ($atOrAfter.Count -ne 0) { throw "Files at or after marker: $($atOrAfter.Count)" }

    $manifestFinalCheck = Assert-Manifest $NewRoot $manifestPath @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED') 44
    Assert-ParseablePayload $NewRoot
    $hygieneFinal = Get-Hygiene $NewRoot
    if ($hygieneFinal.ads_count -ne 0 -or $hygieneFinal.cache_pyc_count -ne 0 -or $hygieneFinal.reparse_count -ne 0) { throw 'Final hygiene audit failed' }

    $copyFinalMismatch = 0
    foreach ($copy in $copyRows) {
        $destIdentity = Get-FileIdentity $NewRoot $copy.destination_resolved_path
        if ($destIdentity.bytes -ne $copy.source_bytes -or $destIdentity.sha256 -cne $copy.source_sha256 -or
            $destIdentity.creation_filetime_utc_ticks -ne $copy.source_creation_filetime_utc_ticks -or
            $destIdentity.last_write_filetime_utc_ticks -ne $copy.source_last_write_filetime_utc_ticks) {
            $copyFinalMismatch++
        }
    }
    if ($copyFinalMismatch -ne 0) { throw "Final copy mismatch count $copyFinalMismatch" }

    $sourceAfter = Get-RootFileSnapshot $SourceRoot
    $oldRootMismatch = Compare-IdentityMaps $sourceBefore $sourceAfter
    if ($oldRootMismatch.Count -ne 0) { throw "Old root changed: $($oldRootMismatch.Count)" }

    $postMoveFilesAfterAudit = Get-RootFileSnapshot $NewRoot
    $postMoveDirectoriesAfterAudit = Get-RootDirectorySnapshot $NewRoot
    $postMarkerFileChanges = Compare-IdentityMaps $postMoveFilesBeforeAudit $postMoveFilesAfterAudit
    $postMarkerDirectoryChanges = Compare-IdentityMaps $postMoveDirectoriesBeforeAudit $postMoveDirectoriesAfterAudit
    if ($postMarkerFileChanges.Count -ne 0 -or $postMarkerDirectoryChanges.Count -ne 0) { throw 'Postmarker content or attribute change detected' }

    $finishedUtc = [DateTime]::UtcNow
    $result = [ordered]@{
        status = 'PASS'
        handoff_id = $HandoffId
        uid = $Uid
        verdict = $Verdict
        controller_resolved_path = $PSCommandPath
        controller_bytes = $controllerIdentity.bytes
        controller_sha256 = $controllerIdentity.sha256
        controller_ast_parse_errors = 0
        invocation_count = 1
        retry_count = 0
        started_utc = $StartedUtc.ToString('o')
        finished_utc = $finishedUtc.ToString('o')
        source_root_resolved = $SourceRoot
        sealed_root_resolved = $NewRoot
        old_root_ordinary = $sourceBefore.Count
        old_root_identity_mismatch_after = $oldRootMismatch.Count
        old_manifest_material_rows = 42
        copied_old_controls = 0
        copy_identity_rows = $copyRows.Count
        source_destination_identity_mismatch = $copyFinalMismatch
        payload_count = 44
        manifest_rows = $manifestFinalCheck.rows
        manifest_identity_mismatch = $manifestFinalCheck.identity_mismatch
        manifest_extra = $manifestFinalCheck.extra
        manifest_unlisted = $manifestFinalCheck.unlisted
        manifest_resolved_path = $manifestPath
        manifest_bytes = (Get-Item -LiteralPath $manifestPath -Force).Length
        manifest_sha256 = Get-Sha256 $manifestPath
        seal_audit_resolved_path = $sealAuditPath
        seal_audit_bytes = (Get-Item -LiteralPath $sealAuditPath -Force).Length
        seal_audit_sha256 = Get-Sha256 $sealAuditPath
        write_stopped_resolved_path = $markerDestination
        write_stopped_bytes = (Get-Item -LiteralPath $markerDestination -Force).Length
        write_stopped_sha256 = Get-Sha256 $markerDestination
        write_stopped_filetime_utc_ticks = $markerItem.LastWriteTimeUtc.ToFileTimeUtc()
        max_other_filetime_utc_ticks = ($otherFiles | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
        at_or_after_excluding_marker = $atOrAfter.Count
        ordinary_count = $finalFiles.Count
        readonly_files = $readOnlyFiles.Count
        directory_count_including_root = $finalDirectories.Count
        readonly_directories = $readOnlyDirectories.Count
        json_csv_parse_failures = 0
        ads_count = $hygieneFinal.ads_count
        cache_pyc_count = $hygieneFinal.cache_pyc_count
        reparse_count = $hygieneFinal.reparse_count
        postmarker_file_content_or_attribute_changes = $postMarkerFileChanges.Count
        postmarker_directory_attribute_changes = $postMarkerDirectoryChanges.Count
        marker_key_values_validated = @('HANDOFF_ID', 'UID', 'SEALED_ROOT', 'MANIFEST_ROWS', 'MANIFEST_SHA256', 'VERDICT')
        isolated_marker_value_lines = 0
        placeholder_tab_or_rue_tokens = 0
    }
    Write-ExternalResult $result
    $result | ConvertTo-Json -Depth 12
}
catch {
    $errorText = $_.Exception.Message
    if (-not $MarkerMoved -and [IO.Directory]::Exists($NewRoot)) {
        foreach ($file in @(Get-ChildItem -LiteralPath $NewRoot -Recurse -File -Force)) {
            try { Set-ReadOnlyAttribute $file.FullName } catch { }
        }
        foreach ($directory in @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Recurse -Directory -Force)) {
            try { Set-ReadOnlyAttribute $directory.FullName } catch { }
        }
    }
    if (-not [IO.File]::Exists($ExternalResultPath)) {
        $failure = [ordered]@{
            status = 'FAIL'
            handoff_id = $HandoffId
            invocation_count = 1
            retry_count = 0
            marker_moved = $MarkerMoved
            started_utc = $StartedUtc.ToString('o')
            finished_utc = [DateTime]::UtcNow.ToString('o')
            error = $errorText
            source_root_resolved = $SourceRoot
            attempted_root_resolved = $NewRoot
        }
        Write-ExternalResult $failure
    }
    throw
}
