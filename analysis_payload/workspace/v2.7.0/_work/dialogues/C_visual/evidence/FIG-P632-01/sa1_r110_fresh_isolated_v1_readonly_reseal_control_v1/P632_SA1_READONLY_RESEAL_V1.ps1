param(
    [Parameter(Mandatory = $true)][string]$OldRoot,
    [Parameter(Mandatory = $true)][string]$NewRoot,
    [Parameter(Mandatory = $true)][string]$ControlRoot,
    [Parameter(Mandatory = $true)][string]$ExpectedControllerSha256
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$startedUtc = [DateTime]::UtcNow
$invocationPath = Join-Path $ControlRoot 'CONTROLLER_INVOCATION.json'
$resultPath = Join-Path $ControlRoot 'CONTROLLER_RESULT.json'
$success = $false
$failure = $null
$newRootCreated = $false

function Write-Utf8Atomic {
    param([string]$Path, [string]$Text)
    $tmp = $Path + '.tmp-' + [Guid]::NewGuid().ToString('N')
    [IO.File]::WriteAllText($tmp, $Text, $script:utf8NoBom)
    [IO.File]::Move($tmp, $Path)
}

function Write-JsonAtomic {
    param([string]$Path, [object]$Value)
    Write-Utf8Atomic -Path $Path -Text ($Value | ConvertTo-Json -Depth 30)
}

function Get-Sha256 {
    param([string]$Path)
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativePathSafe {
    param([string]$Base, [string]$Path)
    return [IO.Path]::GetRelativePath($Base, $Path).Replace('/', '\')
}

function Assert-ContainedPath {
    param([string]$Base, [string]$Candidate)
    $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd('\') + '\'
    $candidateFull = [IO.Path]::GetFullPath($Candidate)
    if (-not $candidateFull.StartsWith($baseFull, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Path escapes root: $candidateFull"
    }
}

function Set-ReadonlyFile {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path
    $item.IsReadOnly = $true
}

function Set-ReadonlyDirectory {
    param([string]$Path)
    $item = Get-Item -LiteralPath $Path
    $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::ReadOnly
}

function Get-AdsCount {
    param([System.IO.FileInfo[]]$Files)
    $count = 0
    foreach ($file in $Files) {
        $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop | Where-Object { $_.Stream -ne ':$DATA' })
        $count += $streams.Count
    }
    return $count
}

function Test-JsonCsvParse {
    param([System.IO.FileInfo[]]$Files)
    $jsonFailures = 0
    $csvFailures = 0
    foreach ($file in $Files) {
        if ($file.Extension -ieq '.json') {
            try { Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $jsonFailures++ }
        } elseif ($file.Extension -ieq '.csv') {
            try { Import-Csv -LiteralPath $file.FullName | Out-Null } catch { $csvFailures++ }
        }
    }
    return [ordered]@{ json_failures = $jsonFailures; csv_failures = $csvFailures }
}

try {
    if (-not (Test-Path -LiteralPath $ControlRoot -PathType Container)) { throw 'Control root missing' }
    if (Test-Path -LiteralPath $invocationPath) { throw 'Invocation record already exists; retry prohibited' }
    if (Test-Path -LiteralPath $resultPath) { throw 'Result record already exists; retry prohibited' }
    if (Test-Path -LiteralPath $NewRoot) { throw 'New root must not exist before invocation' }

    $controllerPath = [IO.Path]::GetFullPath($PSCommandPath)
    $controllerSha = Get-Sha256 -Path $controllerPath
    if ($controllerSha -ne $ExpectedControllerSha256.ToUpperInvariant()) { throw 'Controller SHA identity gate failed' }

    $oldResolved = (Resolve-Path -LiteralPath $OldRoot).Path
    $newResolved = [IO.Path]::GetFullPath($NewRoot)
    $controlResolved = (Resolve-Path -LiteralPath $ControlRoot).Path
    if ($newResolved.Equals($oldResolved, [StringComparison]::OrdinalIgnoreCase)) { throw 'Old and new roots must differ' }
    if ($newResolved.StartsWith($oldResolved.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'New root cannot be nested in old root' }

    $oldManifestPath = Join-Path $oldResolved 'MANIFEST.json'
    $oldWstopPath = Join-Path $oldResolved 'WRITE_STOPPED'
    if ((Get-Sha256 -Path $oldManifestPath) -ne '1603663F3E6A0AEAC0AB570753100BCDF04F833A5BE04AA4BBA6CBDB85DF5B12') { throw 'Old manifest identity mismatch' }
    if ((Get-Sha256 -Path $oldWstopPath) -ne '6EB000A064DA7D16D74E10FFA6A61A10B9E19E1EDE976348DDCF430A04BC6170') { throw 'Old WSTOP identity mismatch' }

    $oldManifest = Get-Content -LiteralPath $oldManifestPath -Raw | ConvertFrom-Json
    $oldEntries = @($oldManifest.entries)
    if ($oldEntries.Count -ne 46) { throw 'Old payload denominator must be 46' }
    if (@($oldEntries.path | Group-Object | Where-Object Count -gt 1).Count -ne 0) { throw 'Old manifest duplicate path' }
    $oldFiles = @(Get-ChildItem -LiteralPath $oldResolved -File -Recurse)
    $oldDirs = @((Get-Item -LiteralPath $oldResolved)) + @(Get-ChildItem -LiteralPath $oldResolved -Directory -Recurse)
    if ($oldFiles.Count -ne 48) { throw 'Old ordinary denominator must be 48' }
    if (@($oldFiles | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'Old root contains writable files' }
    if (@($oldDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'Old root contains writable directories' }

    foreach ($entry in $oldEntries) {
        if ($entry.path -in @('MANIFEST.json', 'WRITE_STOPPED')) { throw 'Old controls must not be material payload' }
        $sourcePath = Join-Path $oldResolved $entry.path
        Assert-ContainedPath -Base $oldResolved -Candidate $sourcePath
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Missing old payload: $($entry.path)" }
        $sourceItem = Get-Item -LiteralPath $sourcePath
        if ($sourceItem.Length -ne [int64]$entry.bytes) { throw "Old payload bytes mismatch: $($entry.path)" }
        if ((Get-Sha256 -Path $sourcePath) -ne $entry.sha256.ToUpperInvariant()) { throw "Old payload SHA mismatch: $($entry.path)" }
    }

    $invocation = [ordered]@{
        schema_version = '1.0'
        authorization = 'MAIN_R286_P632_SA1_ROOT_REJECT_ONE_CONTROL_RESEAL_AUTHORIZATION'
        invocation_ordinal = 1
        invocation_limit = 1
        retry_count = 0
        controller_path = $controllerPath
        controller_bytes = (Get-Item -LiteralPath $controllerPath).Length
        controller_sha256 = $controllerSha
        old_root = $oldResolved
        new_root = $newResolved
        control_root = $controlResolved
        new_root_existed_before = $false
        started_utc = $startedUtc.ToString('o')
    }
    Write-JsonAtomic -Path $invocationPath -Value $invocation

    New-Item -ItemType Directory -Path $newResolved -ErrorAction Stop | Out-Null
    $newRootCreated = $true
    $identityRows = [System.Collections.Generic.List[object]]::new()
    foreach ($entry in $oldEntries) {
        $relative = [string]$entry.path
        $sourcePath = Join-Path $oldResolved $relative
        $destPath = Join-Path $newResolved $relative
        Assert-ContainedPath -Base $newResolved -Candidate $destPath
        $destDir = Split-Path -Parent $destPath
        if (-not (Test-Path -LiteralPath $destDir)) { New-Item -ItemType Directory -Path $destDir | Out-Null }
        Copy-Item -LiteralPath $sourcePath -Destination $destPath -Force
        [IO.File]::SetAttributes($destPath, [IO.FileAttributes]::Normal)
        $sourceItem = Get-Item -LiteralPath $sourcePath
        [IO.File]::SetLastWriteTimeUtc($destPath, $sourceItem.LastWriteTimeUtc)
        $destItem = Get-Item -LiteralPath $destPath
        $sourceSha = Get-Sha256 -Path $sourcePath
        $destSha = Get-Sha256 -Path $destPath
        $identityRows.Add([pscustomobject][ordered]@{
            relative_path = $relative
            source_resolved_path = $sourceItem.FullName
            destination_resolved_path = $destItem.FullName
            source_bytes = $sourceItem.Length
            destination_bytes = $destItem.Length
            source_sha256 = $sourceSha
            destination_sha256 = $destSha
            source_mtime_utc_ticks = $sourceItem.LastWriteTimeUtc.Ticks
            destination_mtime_utc_ticks = $destItem.LastWriteTimeUtc.Ticks
            path_match = $true
            bytes_match = ($sourceItem.Length -eq $destItem.Length)
            sha256_match = ($sourceSha -eq $destSha)
            mtime_ticks_match = ($sourceItem.LastWriteTimeUtc.Ticks -eq $destItem.LastWriteTimeUtc.Ticks)
        }) | Out-Null
    }
    if ($identityRows.Count -ne 46) { throw 'Copy identity row denominator mismatch' }
    if (@($identityRows | Where-Object { -not $_.bytes_match -or -not $_.sha256_match -or -not $_.mtime_ticks_match }).Count -ne 0) { throw 'Source-to-destination identity mismatch' }

    $copyIdentityPath = Join-Path $newResolved 'COPY_IDENTITY.csv'
    $csvText = ($identityRows | ConvertTo-Csv -NoTypeInformation) -join "`r`n"
    Write-Utf8Atomic -Path $copyIdentityPath -Text ($csvText + "`r`n")

    $copyProvenancePath = Join-Path $newResolved 'COPY_PROVENANCE.json'
    $copyProvenance = [ordered]@{
        schema_version = '1.0'
        handoff_id = 'C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-READONLY-RESEAL-V1'
        authorization = 'MAIN_R286_P632_SA1_ROOT_REJECT_ONE_CONTROL_RESEAL_AUTHORIZATION'
        operation = 'evidence-only readonly control reseal'
        original_root = $oldResolved
        destination_root = $newResolved
        original_manifest_resolved_path = $oldManifestPath
        original_manifest_bytes = (Get-Item -LiteralPath $oldManifestPath).Length
        original_manifest_sha256 = Get-Sha256 -Path $oldManifestPath
        original_wstop_resolved_path = $oldWstopPath
        original_wstop_bytes = (Get-Item -LiteralPath $oldWstopPath).Length
        original_wstop_sha256 = Get-Sha256 -Path $oldWstopPath
        copied_material_payload_count = 46
        copied_old_manifest_count = 0
        copied_old_wstop_count = 0
        added_control_payload_count = 2
        visual_object_pair_manual_semantic_rerun_count = 0
        source_tex_git_role_uid_write_count = 0
        controller_invocation_ordinal = 1
        controller_retry_count = 0
        created_utc = [DateTime]::UtcNow.ToString('o')
    }
    Write-JsonAtomic -Path $copyProvenancePath -Value $copyProvenance

    $payloadPaths = [System.Collections.Generic.List[string]]::new()
    foreach ($entry in $oldEntries) { $payloadPaths.Add([string]$entry.path) | Out-Null }
    $payloadPaths.Add('COPY_IDENTITY.csv') | Out-Null
    $payloadPaths.Add('COPY_PROVENANCE.json') | Out-Null
    if ($payloadPaths.Count -ne 48) { throw 'Projected payload denominator must be 48' }
    if (@($payloadPaths | Group-Object | Where-Object Count -gt 1).Count -ne 0) { throw 'Projected payload duplicate path' }

    $manifestEntries = [System.Collections.Generic.List[object]]::new()
    foreach ($relative in $payloadPaths) {
        $path = Join-Path $newResolved $relative
        $item = Get-Item -LiteralPath $path
        $kind = if ($relative -in @('COPY_IDENTITY.csv', 'COPY_PROVENANCE.json')) { 'control_payload' } else { 'material_payload' }
        $manifestEntries.Add([pscustomobject][ordered]@{
            path = $relative
            bytes = $item.Length
            sha256 = Get-Sha256 -Path $path
            mtime_utc_ticks = $item.LastWriteTimeUtc.Ticks
            kind = $kind
        }) | Out-Null
    }
    $payloadManifestPath = Join-Path $newResolved 'PAYLOAD_MANIFEST.json'
    $payloadManifest = [ordered]@{
        schema_version = '1.0'
        handoff_id = 'C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-READONLY-RESEAL-V1'
        root = $newResolved
        payload_entry_count = 48
        material_payload_count = 46
        added_control_payload_count = 2
        control_files_excluded = @('PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
        entries = $manifestEntries
    }
    Write-JsonAtomic -Path $payloadManifestPath -Value $payloadManifest

    foreach ($relative in $payloadPaths) { Set-ReadonlyFile -Path (Join-Path $newResolved $relative) }
    Set-ReadonlyFile -Path $payloadManifestPath

    $preSealFiles = @(Get-ChildItem -LiteralPath $newResolved -File -Recurse)
    if ($preSealFiles.Count -ne 49) { throw 'Pre-SEAL file denominator must be 49' }
    $manifestReloaded = Get-Content -LiteralPath $payloadManifestPath -Raw | ConvertFrom-Json
    $manifestRows = @($manifestReloaded.entries)
    $manifestMissing = 0
    $manifestExtra = 0
    $manifestBytesMismatch = 0
    $manifestShaMismatch = 0
    $manifestTicksMismatch = 0
    foreach ($entry in $manifestRows) {
        $path = Join-Path $newResolved $entry.path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestMissing++; continue }
        $item = Get-Item -LiteralPath $path
        if ($item.Length -ne [int64]$entry.bytes) { $manifestBytesMismatch++ }
        if ((Get-Sha256 -Path $path) -ne $entry.sha256.ToUpperInvariant()) { $manifestShaMismatch++ }
        if ($item.LastWriteTimeUtc.Ticks -ne [int64]$entry.mtime_utc_ticks) { $manifestTicksMismatch++ }
    }
    $manifestNames = @($manifestRows.path)
    $manifestExtra = @($preSealFiles | ForEach-Object { Get-RelativePathSafe -Base $newResolved -Path $_.FullName } | Where-Object { $_ -notin $manifestNames -and $_ -ne 'PAYLOAD_MANIFEST.json' }).Count
    if ($manifestRows.Count -ne 48 -or @($manifestRows.path | Group-Object | Where-Object Count -gt 1).Count -ne 0 -or $manifestMissing -ne 0 -or $manifestExtra -ne 0 -or $manifestBytesMismatch -ne 0 -or $manifestShaMismatch -ne 0 -or $manifestTicksMismatch -ne 0) { throw 'Payload manifest closure gate failed' }

    $parse = Test-JsonCsvParse -Files $preSealFiles
    $ads = Get-AdsCount -Files $preSealFiles
    $cache = @($preSealFiles | Where-Object { $_.Name -match '\.(pyc|pyo)$' -or $_.FullName -match '([\\/])(__pycache__|\.cache)([\\/]|$)' }).Count
    $preSealDirs = @((Get-Item -LiteralPath $newResolved)) + @(Get-ChildItem -LiteralPath $newResolved -Directory -Recurse)
    $reparse = @($preSealFiles + $preSealDirs | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
    if ($parse.json_failures -ne 0 -or $parse.csv_failures -ne 0 -or $ads -ne 0 -or $cache -ne 0 -or $reparse -ne 0) { throw 'Pre-WSTOP parse/ADS/cache/pyc/reparse gate failed' }

    $sealAuditPath = Join-Path $newResolved 'SEAL_AUDIT.json'
    $sealAudit = [ordered]@{
        schema_version = '1.0'
        handoff_id = 'C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-READONLY-RESEAL-V1'
        audit_stage = 'completed_before_WRITE_STOPPED'
        original_material_payload_count = 46
        copy_identity_rows = 46
        source_destination_path_mismatch = 0
        source_destination_bytes_mismatch = 0
        source_destination_sha256_mismatch = 0
        source_destination_mtime_ticks_mismatch = 0
        copied_old_manifest_count = 0
        copied_old_wstop_count = 0
        added_control_payload_count = 2
        payload_manifest_rows = 48
        payload_manifest_duplicate = 0
        payload_manifest_missing = $manifestMissing
        payload_manifest_extra = $manifestExtra
        payload_manifest_bytes_mismatch = $manifestBytesMismatch
        payload_manifest_sha256_mismatch = $manifestShaMismatch
        payload_manifest_mtime_ticks_mismatch = $manifestTicksMismatch
        json_parse_failures = $parse.json_failures
        csv_parse_failures = $parse.csv_failures
        ads_count = $ads
        cache_pyc_pyo_count = $cache
        reparse_count = $reparse
        expected_premarker_files = 50
        expected_final_files = 51
        expected_final_payload = 48
        expected_final_controls = 3
        visual_object_pair_manual_semantic_rerun_count = 0
        controller_invocation_ordinal = 1
        retry_count = 0
        completed_utc = [DateTime]::UtcNow.ToString('o')
    }
    Write-JsonAtomic -Path $sealAuditPath -Value $sealAudit
    Set-ReadonlyFile -Path $sealAuditPath
    foreach ($dir in @((Get-Item -LiteralPath $newResolved)) + @(Get-ChildItem -LiteralPath $newResolved -Directory -Recurse)) { Set-ReadonlyDirectory -Path $dir.FullName }

    $premarkerFiles = @(Get-ChildItem -LiteralPath $newResolved -File -Recurse)
    $premarkerDirs = @((Get-Item -LiteralPath $newResolved)) + @(Get-ChildItem -LiteralPath $newResolved -Directory -Recurse)
    if ($premarkerFiles.Count -ne 50) { throw 'Premarker file denominator must be 50' }
    if (@($premarkerFiles | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'Premarker writable file gate failed' }
    if (@($premarkerDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'Premarker writable directory gate failed' }
    $parseFinalPre = Test-JsonCsvParse -Files $premarkerFiles
    $adsFinalPre = Get-AdsCount -Files $premarkerFiles
    $cacheFinalPre = @($premarkerFiles | Where-Object { $_.Name -match '\.(pyc|pyo)$' -or $_.FullName -match '([\\/])(__pycache__|\.cache)([\\/]|$)' }).Count
    $reparseFinalPre = @($premarkerFiles + $premarkerDirs | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
    if ($parseFinalPre.json_failures -ne 0 -or $parseFinalPre.csv_failures -ne 0 -or $adsFinalPre -ne 0 -or $cacheFinalPre -ne 0 -or $reparseFinalPre -ne 0) { throw 'Final premarker gate failed' }

    $manifestSha = Get-Sha256 -Path $payloadManifestPath
    $sealAuditSha = Get-Sha256 -Path $sealAuditPath
    $maxPreTicks = ($premarkerFiles | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
    $targetMarkerTicks = [Math]::Max([DateTime]::UtcNow.Ticks + 10000000L, [int64]$maxPreTicks + 10000000L)
    $wstopPath = Join-Path $newResolved 'WRITE_STOPPED'
    $wstop = [ordered]@{
        schema_version = '1.0'
        handoff_id = 'C-FIG-P632-01-R110-SA1-FRESH-ISOLATED-READONLY-RESEAL-V1'
        outcome = 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
        evidence_only_reseal = $true
        payload_count = 48
        control_count = 3
        ordinary_file_count = 51
        payload_manifest_sha256 = $manifestSha
        seal_audit_sha256 = $sealAuditSha
        premarker_file_count = 50
        max_premarker_mtime_utc_ticks = [int64]$maxPreTicks
        marker_target_mtime_utc_ticks = $targetMarkerTicks
        postmarker_content_writes = 0
        controller_invocation_ordinal = 1
        retry_count = 0
    }
    [IO.File]::WriteAllText($wstopPath, ($wstop | ConvertTo-Json -Depth 20), $utf8NoBom)
    [IO.File]::SetLastWriteTimeUtc($wstopPath, [DateTime]::new($targetMarkerTicks, [DateTimeKind]::Utc))
    Set-ReadonlyFile -Path $wstopPath
    $success = $true
}
catch {
    $failure = $_.Exception.ToString()
    if ($newRootCreated -and (Test-Path -LiteralPath $NewRoot)) {
        foreach ($file in @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -ErrorAction SilentlyContinue)) {
            try { $file.IsReadOnly = $true } catch {}
        }
        foreach ($dir in @((Get-Item -LiteralPath $NewRoot -ErrorAction SilentlyContinue)) + @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -ErrorAction SilentlyContinue)) {
            if ($null -ne $dir) { try { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly } catch {} }
        }
    }
}
finally {
    $finishedUtc = [DateTime]::UtcNow
    $result = [ordered]@{
        schema_version = '1.0'
        invocation_ordinal = 1
        invocation_limit = 1
        retry_count = 0
        started_utc = $startedUtc.ToString('o')
        finished_utc = $finishedUtc.ToString('o')
        duration_seconds = [Math]::Round(($finishedUtc - $startedUtc).TotalSeconds, 6)
        success = $success
        exit_code = $(if ($success) { 0 } else { 1 })
        failure = $failure
        new_root_created = $newRootCreated
        new_root = [IO.Path]::GetFullPath($NewRoot)
        controller_sha256 = $(if (Test-Path -LiteralPath $PSCommandPath) { Get-Sha256 -Path $PSCommandPath } else { $null })
    }
    Write-JsonAtomic -Path $resultPath -Value $result
}

if (-not $success) { exit 1 }
exit 0
