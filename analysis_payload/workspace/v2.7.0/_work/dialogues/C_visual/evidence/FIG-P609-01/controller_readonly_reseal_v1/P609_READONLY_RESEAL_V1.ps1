param(
    [Parameter(Mandatory = $true)]
    [string]$AuthorizationToken
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-Identity([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    [ordered]@{
        path = $item.FullName
        bytes = [int64]$item.Length
        sha256 = Get-Sha256 $item.FullName
        mtime_utc_ticks = [int64]$item.LastWriteTimeUtc.Ticks
        mtime_filetime_utc = [int64]$item.LastWriteTimeUtc.ToFileTimeUtc()
    }
}

function Write-JsonAtomic([string]$Path, $Object, [int]$Depth = 20) {
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $tmp = "$Path.tmp-$PID"
    $json = $Object | ConvertTo-Json -Depth $Depth
    [System.IO.File]::WriteAllText($tmp, $json + "`r`n", [System.Text.UTF8Encoding]::new($false))
    Move-Item -LiteralPath $tmp -Destination $Path
}

function Write-CsvAtomic([string]$Path, [object[]]$Rows) {
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
    $tmp = "$Path.tmp-$PID"
    $Rows | Export-Csv -LiteralPath $tmp -NoTypeInformation -Encoding utf8NoBOM
    Move-Item -LiteralPath $tmp -Destination $Path
}

function Set-ReadOnlyTree([string]$Root) {
    if (-not (Test-Path -LiteralPath $Root -PathType Container)) { return }
    Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object {
        [System.IO.File]::SetAttributes($_.FullName, ($_.Attributes -bor [System.IO.FileAttributes]::ReadOnly))
    }
    $dirs = @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force | Sort-Object { $_.FullName.Length } -Descending)
    foreach ($dir in $dirs) {
        [System.IO.File]::SetAttributes($dir.FullName, ($dir.Attributes -bor [System.IO.FileAttributes]::ReadOnly))
    }
    $rootItem = Get-Item -LiteralPath $Root -Force
    [System.IO.File]::SetAttributes($rootItem.FullName, ($rootItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly))
}

function Assert-Equal($Actual, $Expected, [string]$Label) {
    if ($Actual -ne $Expected) {
        throw "$Label mismatch: actual=[$Actual] expected=[$Expected]"
    }
}

function Test-RootPreMarker([string]$Root, [string[]]$ControlNames) {
    $files = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)
    $manifest = Get-Content -LiteralPath (Join-Path $Root 'evidence_manifest.json') -Raw | ConvertFrom-Json -Depth 100
    $entries = @($manifest.entries)
    $payloadFiles = @($files | Where-Object { $ControlNames -notcontains $_.Name })
    $payloadRelative = @($payloadFiles | ForEach-Object { [System.IO.Path]::GetRelativePath($Root,$_.FullName) })
    $mismatch = 0
    foreach ($entry in $entries) {
        $path = Join-Path $Root ([string]$entry.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $mismatch++; continue }
        $id = Get-Identity $path
        if ($id.path -ne [string]$entry.resolved_path -or $id.bytes -ne [int64]$entry.bytes -or
            $id.sha256 -ne [string]$entry.sha256 -or $id.mtime_utc_ticks -ne [int64]$entry.mtime_utc_ticks -or
            $id.mtime_filetime_utc -ne [int64]$entry.mtime_filetime_utc) { $mismatch++ }
    }
    $entryPaths = @($entries | ForEach-Object { [string]$_.path })
    $mismatch += @($entryPaths | Where-Object { $payloadRelative -notcontains $_ }).Count
    $mismatch += @($payloadRelative | Where-Object { $entryPaths -notcontains $_ }).Count
    [ordered]@{ payload_count=$payloadFiles.Count; manifest_mismatch_count=$mismatch }
}

function Test-Root([string]$Root, [string[]]$ControlNames) {
    $files = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)
    $dirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force)
    $manifestPath = Join-Path $Root 'evidence_manifest.json'
    $sealPath = Join-Path $Root 'SEAL.json'
    $markerPath = Join-Path $Root 'WRITE_STOPPED'
    $manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json -Depth 100
    $manifestEntries = @($manifest.entries)
    $manifestPaths = @($manifestEntries | ForEach-Object { [string]$_.path })
    $duplicatePaths = @($manifestPaths | Group-Object | Where-Object Count -gt 1)
    $payloadFiles = @($files | Where-Object { $ControlNames -notcontains $_.Name })
    $payloadRelative = @($payloadFiles | ForEach-Object { [System.IO.Path]::GetRelativePath($Root, $_.FullName) })
    $missing = @($manifestPaths | Where-Object { $payloadRelative -notcontains $_ })
    $extra = @($payloadRelative | Where-Object { $manifestPaths -notcontains $_ })
    $identityMismatch = [System.Collections.Generic.List[object]]::new()
    foreach ($entry in $manifestEntries) {
        $path = Join-Path $Root ([string]$entry.path)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { continue }
        $id = Get-Identity $path
        $resolvedExpected = [System.IO.Path]::GetFullPath([string]$entry.resolved_path)
        $resolvedActual = [System.IO.Path]::GetFullPath($id.path)
        if (($resolvedActual -ne $resolvedExpected) -or
            ($id.bytes -ne [int64]$entry.bytes) -or
            ($id.sha256 -ne [string]$entry.sha256) -or
            ($id.mtime_utc_ticks -ne [int64]$entry.mtime_utc_ticks) -or
            ($id.mtime_filetime_utc -ne [int64]$entry.mtime_filetime_utc)) {
            $identityMismatch.Add([ordered]@{ path = [string]$entry.path; actual = $id; expected = $entry })
        }
    }
    $copyRows = @(Import-Csv -LiteralPath (Join-Path $Root 'COPY_IDENTITY.csv'))
    $copyMismatch = @($copyRows | Where-Object {
        $_.path_match -ne 'True' -or $_.bytes_match -ne 'True' -or $_.sha256_match -ne 'True' -or
        $_.mtime_ticks_match -ne 'True' -or $_.filetime_match -ne 'True'
    })
    $oldControlsCopied = @($payloadRelative | Where-Object { @('evidence_manifest.json','SEAL.json','WRITE_STOPPED') -contains $_ })
    $readonlyFiles = @($files | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 })
    $readonlyDirs = @($dirs | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0 })
    $ads = [System.Collections.Generic.List[object]]::new()
    foreach ($file in $files) {
        $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -notin @(':$DATA','::$DATA') })
        foreach ($stream in $streams) { $ads.Add([ordered]@{ path=$file.FullName; stream=$stream.Stream; length=$stream.Length }) }
    }
    $cache = @($files | Where-Object { $_.Extension -in @('.pyc','.pyo') -or $_.FullName -match '[\\/](__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache)([\\/]|$)' })
    $reparse = @((Get-ChildItem -LiteralPath $Root -Recurse -Force) + @((Get-Item -LiteralPath $Root -Force)) | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 })
    $marker = Get-Item -LiteralPath $markerPath -Force
    $otherFiles = @($files | Where-Object FullName -ne $marker.FullName)
    $atOrAfter = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
    $postMarker = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.Ticks -gt $marker.LastWriteTimeUtc.Ticks })
    $maxTicks = [int64](($files | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc.Ticks)
    $latestFiles = @($files | Where-Object { $_.LastWriteTimeUtc.Ticks -eq $maxTicks })
    $jsonFailures = [System.Collections.Generic.List[string]]::new()
    foreach ($file in @($files | Where-Object Extension -eq '.json')) {
        try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json -Depth 100 }
        catch { $jsonFailures.Add($file.FullName) }
    }
    $csvFailures = [System.Collections.Generic.List[string]]::new()
    foreach ($file in @($files | Where-Object Extension -eq '.csv')) {
        try { $null = @(Import-Csv -LiteralPath $file.FullName) }
        catch { $csvFailures.Add($file.FullName) }
    }
    [ordered]@{
        root = [System.IO.Path]::GetFullPath($Root)
        ordinary_count = $files.Count
        payload_count = $payloadFiles.Count
        control_count = @($files | Where-Object { $ControlNames -contains $_.Name }).Count
        manifest_rows = $manifestEntries.Count
        manifest_duplicate_path_count = $duplicatePaths.Count
        manifest_missing_count = $missing.Count
        manifest_extra_count = $extra.Count
        manifest_identity_mismatch_count = $identityMismatch.Count
        copy_identity_rows = $copyRows.Count
        copy_identity_mismatch_count = $copyMismatch.Count
        old_controls_copied_count = $oldControlsCopied.Count
        readonly_file_count = $readonlyFiles.Count
        writable_file_count = $files.Count - $readonlyFiles.Count
        directory_count_including_root = $dirs.Count
        readonly_directory_count = $readonlyDirs.Count
        writable_directory_count = $dirs.Count - $readonlyDirs.Count
        root_readonly = ((Get-Item -LiteralPath $Root -Force).Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0
        ads_count = $ads.Count
        cache_pyc_count = $cache.Count
        reparse_count = $reparse.Count
        marker_path = $marker.FullName
        marker_mtime_utc_ticks = [int64]$marker.LastWriteTimeUtc.Ticks
        marker_unique_latest = ($latestFiles.Count -eq 1 -and $latestFiles[0].FullName -eq $marker.FullName)
        files_at_or_after_marker_excluding_marker = $atOrAfter.Count
        post_marker_write_count = $postMarker.Count
        json_parse_failure_count = $jsonFailures.Count
        csv_parse_failure_count = $csvFailures.Count
        manifest_sha256 = Get-Sha256 $manifestPath
        seal_sha256 = Get-Sha256 $sealPath
        write_stopped_sha256 = Get-Sha256 $markerPath
    }
}

$controllerPath = [System.IO.Path]::GetFullPath($MyInvocation.MyCommand.Path)
$controllerDir = Split-Path -Parent $controllerPath
$authorizationPath = Join-Path $controllerDir 'AUTHORIZATION.json'
$claimPath = Join-Path $controllerDir 'INVOCATION_CLAIM.json'
$resultPath = Join-Path $controllerDir 'CONTROLLER_RESULT.json'
$auditPath = Join-Path $controllerDir 'ROOT_EXTERNAL_AUDIT.json'
$handoffPath = Join-Path $controllerDir 'P609_READONLY_RESEAL_HANDOFF.md'
$startedUtc = [DateTime]::UtcNow
$newRoot = $null
$auth = $null
$claimWritten = $false
$success = $false
$failureMessage = $null

try {
    if (-not (Test-Path -LiteralPath $authorizationPath -PathType Leaf)) { throw 'AUTHORIZATION.json missing' }
    $auth = Get-Content -LiteralPath $authorizationPath -Raw | ConvertFrom-Json -Depth 100
    Assert-Equal $AuthorizationToken ([string]$auth.authorization_token) 'authorization_token'
    Assert-Equal (Get-Sha256 $controllerPath) ([string]$auth.controller_sha256) 'controller_sha256'
    Assert-Equal ([int64](Get-Item -LiteralPath $controllerPath).Length) ([int64]$auth.controller_bytes) 'controller_bytes'
    $tokens = $null
    $parseErrors = $null
    $null = [System.Management.Automation.Language.Parser]::ParseFile($controllerPath, [ref]$tokens, [ref]$parseErrors)
    Assert-Equal @($parseErrors).Count 0 'controller_ast_parse_error_count'
    if (Test-Path -LiteralPath $claimPath) { throw 'INVOCATION_CLAIM already exists: retry forbidden' }
    $oldRoot = [System.IO.Path]::GetFullPath([string]$auth.old_root)
    $newRoot = [System.IO.Path]::GetFullPath([string]$auth.new_root)
    if (Test-Path -LiteralPath $newRoot) { throw 'new root already exists' }
    if (-not (Test-Path -LiteralPath $oldRoot -PathType Container)) { throw 'old root missing' }
    $oldManifestPath = Join-Path $oldRoot 'evidence_manifest.json'
    $oldSealPath = Join-Path $oldRoot 'SEAL.json'
    $oldMarkerPath = Join-Path $oldRoot 'WRITE_STOPPED'
    Assert-Equal (Get-Sha256 $oldManifestPath) ([string]$auth.old_manifest_sha256) 'old manifest SHA'
    Assert-Equal (Get-Sha256 $oldSealPath) ([string]$auth.old_seal_sha256) 'old seal SHA'
    Assert-Equal (Get-Sha256 $oldMarkerPath) ([string]$auth.old_write_stopped_sha256) 'old WSTOP SHA'
    $oldManifest = Get-Content -LiteralPath $oldManifestPath -Raw | ConvertFrom-Json -Depth 100
    $oldEntries = @($oldManifest.entries)
    Assert-Equal $oldEntries.Count ([int]$auth.expected_material_count) 'old manifest material count'
    $oldEntryPaths = @($oldEntries | ForEach-Object { [string]$_.path })
    Assert-Equal @($oldEntryPaths | Group-Object | Where-Object Count -gt 1).Count 0 'old manifest duplicate paths'
    foreach ($control in @('evidence_manifest.json','SEAL.json','WRITE_STOPPED')) {
        if ($oldEntryPaths -contains $control) { throw "old control appears in material manifest: $control" }
    }
    $oldFiles = @(Get-ChildItem -LiteralPath $oldRoot -Recurse -File -Force)
    Assert-Equal $oldFiles.Count 32 'old ordinary count'

    $controllerId = Get-Identity $controllerPath
    $authorizationId = Get-Identity $authorizationPath
    Write-JsonAtomic $claimPath ([ordered]@{
        schema='P609-readonly-reseal-invocation-claim-v1'
        authorization_token=$AuthorizationToken
        ordinal=1
        invocation_limit=1
        retry_count=0
        claimed_utc=$startedUtc.ToString('o')
        controller=$controllerId
        authorization=$authorizationId
        old_root=$oldRoot
        new_root=$newRoot
        new_root_absent_before_invocation=$true
    })
    $claimWritten = $true

    New-Item -ItemType Directory -Path $newRoot | Out-Null
    $copyRows = [System.Collections.Generic.List[object]]::new()
    foreach ($entry in $oldEntries) {
        $relative = [string]$entry.path
        if ([System.IO.Path]::IsPathRooted($relative) -or $relative -match '(^|[\\/])\.\.([\\/]|$)') { throw "unsafe relative path: $relative" }
        $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $oldRoot $relative))
        $destPath = [System.IO.Path]::GetFullPath((Join-Path $newRoot $relative))
        if (-not $sourcePath.StartsWith($oldRoot + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "source containment failed: $relative" }
        if (-not $destPath.StartsWith($newRoot + [System.IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw "destination containment failed: $relative" }
        $sourceId = Get-Identity $sourcePath
        Assert-Equal $sourceId.bytes ([int64]$entry.bytes) "old payload bytes $relative"
        Assert-Equal $sourceId.sha256 ([string]$entry.sha256) "old payload SHA $relative"
        $destParent = Split-Path -Parent $destPath
        if (-not (Test-Path -LiteralPath $destParent -PathType Container)) { New-Item -ItemType Directory -Path $destParent | Out-Null }
        Copy-Item -LiteralPath $sourcePath -Destination $destPath
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        (Get-Item -LiteralPath $destPath -Force).LastWriteTimeUtc = $sourceItem.LastWriteTimeUtc
        $destId = Get-Identity $destPath
        $copyRows.Add([pscustomobject][ordered]@{
            relative_path=$relative
            source_resolved_path=$sourceId.path
            dest_resolved_path=$destId.path
            source_bytes=$sourceId.bytes
            dest_bytes=$destId.bytes
            source_sha256=$sourceId.sha256
            dest_sha256=$destId.sha256
            source_mtime_utc_ticks=$sourceId.mtime_utc_ticks
            dest_mtime_utc_ticks=$destId.mtime_utc_ticks
            source_filetime_utc=$sourceId.mtime_filetime_utc
            dest_filetime_utc=$destId.mtime_filetime_utc
            path_match=([System.IO.Path]::GetRelativePath($oldRoot,$sourceId.path) -eq [System.IO.Path]::GetRelativePath($newRoot,$destId.path))
            bytes_match=($sourceId.bytes -eq $destId.bytes)
            sha256_match=($sourceId.sha256 -eq $destId.sha256)
            mtime_ticks_match=($sourceId.mtime_utc_ticks -eq $destId.mtime_utc_ticks)
            filetime_match=($sourceId.mtime_filetime_utc -eq $destId.mtime_filetime_utc)
        })
    }
    Assert-Equal $copyRows.Count 29 'copied material count'
    Assert-Equal @($copyRows | Where-Object { -not ($_.path_match -and $_.bytes_match -and $_.sha256_match -and $_.mtime_ticks_match -and $_.filetime_match) }).Count 0 'copy identity mismatches'

    $copyIdentityPath = Join-Path $newRoot 'COPY_IDENTITY.csv'
    Write-CsvAtomic $copyIdentityPath @($copyRows)
    $copyIdentityId = Get-Identity $copyIdentityPath
    $provenancePath = Join-Path $newRoot 'COPY_PROVENANCE.json'
    $provenance = [ordered]@{
        schema='P609-evidence-only-readonly-reseal-provenance-v1'
        handoff_id='C-FIG-P609-01-R108-SA2-R168-READONLY-RESEAL-V1'
        decision_preserved='P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
        operation='EVIDENCE_ONLY_COPY_AND_READONLY_RESEAL'
        business_evidence_rerun_count=0
        visual_semantic_manual_modification_count=0
        source_write_count=0
        tex_call_count=0
        git_operation_count=0
        old_root=$oldRoot
        new_root=$newRoot
        controller=$controllerId
        authorization=$authorizationId
        old_controls=[ordered]@{
            evidence_manifest=(Get-Identity $oldManifestPath)
            seal=(Get-Identity $oldSealPath)
            write_stopped=(Get-Identity $oldMarkerPath)
            copied_count=0
        }
        material_source_count=29
        material_copy_count=29
        added_payload_count=2
        projected_payload_count=31
        projected_control_count=3
        projected_ordinary_count=34
        copy_identity=$copyIdentityId
    }
    Write-JsonAtomic $provenancePath $provenance

    $controlNames = @('evidence_manifest.json','SEAL.json','WRITE_STOPPED')
    $payloadFiles = @(Get-ChildItem -LiteralPath $newRoot -Recurse -File -Force | Where-Object { $controlNames -notcontains $_.Name })
    Assert-Equal $payloadFiles.Count 31 'pre-manifest payload count'
    $manifestEntries = @($payloadFiles | Sort-Object FullName | ForEach-Object {
        $id = Get-Identity $_.FullName
        [ordered]@{
            path=[System.IO.Path]::GetRelativePath($newRoot,$_.FullName)
            resolved_path=$id.path
            bytes=$id.bytes
            sha256=$id.sha256
            mtime_utc_ticks=$id.mtime_utc_ticks
            mtime_filetime_utc=$id.mtime_filetime_utc
        }
    })
    $manifestPath = Join-Path $newRoot 'evidence_manifest.json'
    Write-JsonAtomic $manifestPath ([ordered]@{
        schema='FIG-P609-01-evidence-manifest-readonly-reseal-v1'
        root=$newRoot
        handoff_id='C-FIG-P609-01-R108-SA2-R168-READONLY-RESEAL-V1'
        payload_count=31
        material_copy_count=29
        added_control_payload_count=2
        excluded_control_files=$controlNames
        entries=$manifestEntries
    }) 100
    $manifestId = Get-Identity $manifestPath
    $sealPath = Join-Path $newRoot 'SEAL.json'
    Write-JsonAtomic $sealPath ([ordered]@{
        schema='FIG-P609-01-readonly-reseal-v1'
        handoff_id='C-FIG-P609-01-R108-SA2-R168-READONLY-RESEAL-V1'
        actual_instance='/root/sa2_fig_p609_r108_r168_readonly_v1'
        model='gpt-5.6-sol'
        reasoning_effort='xhigh'
        fork_turns='none'
        decision='P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
        original_root=$oldRoot
        resealed_root=$newRoot
        material_count=29
        added_payload_count=2
        payload_count=31
        control_count=3
        ordinary_count=34
        old_control_copy_count=0
        copy_identity=(Get-Identity $copyIdentityPath)
        copy_provenance=(Get-Identity $provenancePath)
        manifest=$manifestId
        controller=$controllerId
        post_marker_writes_allowed=0
    })
    $sealId = Get-Identity $sealPath

    $preMarkerFiles = @(Get-ChildItem -LiteralPath $newRoot -Recurse -File -Force)
    Assert-Equal $preMarkerFiles.Count 33 'pre-WSTOP ordinary count'
    Assert-Equal @($preMarkerFiles | Where-Object Name -in @('evidence_manifest.json','SEAL.json')).Count 2 'pre-WSTOP controls'
    Assert-Equal @($preMarkerFiles | Where-Object Name -in @('WRITE_STOPPED')).Count 0 'pre-WSTOP marker count'
    foreach ($name in @('evidence_manifest.json','SEAL.json','WRITE_STOPPED')) {
        $copied = @($copyRows | Where-Object relative_path -eq $name).Count
        Assert-Equal $copied 0 "old control copied $name"
    }
    $preAudit = Test-RootPreMarker -Root $newRoot -ControlNames $controlNames
    Assert-Equal $preAudit.payload_count 31 'pre-WSTOP manifest payload count'
    Assert-Equal $preAudit.manifest_mismatch_count 0 'pre-WSTOP manifest mismatch'

    $markerPath = Join-Path $newRoot 'WRITE_STOPPED'
    $maxPreTicks = [int64](($preMarkerFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc.Ticks)
    $markerTargetTicks = [int64]$maxPreTicks + 10000000L
    $markerObject = [ordered]@{
        schema='FIG-P609-01-write-stopped-readonly-reseal-v1'
        handoff_id='C-FIG-P609-01-R108-SA2-R168-READONLY-RESEAL-V1'
        decision='P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
        payload_count=31
        control_count=3
        ordinary_count=34
        material_copy_count=29
        old_control_copy_count=0
        manifest_sha256=$manifestId.sha256
        seal_sha256=$sealId.sha256
        controller_sha256=$controllerId.sha256
        post_marker_writes_allowed=0
        marker_target_mtime_utc_ticks=$markerTargetTicks
    }
    Write-JsonAtomic $markerPath $markerObject
    (Get-Item -LiteralPath $markerPath -Force).LastWriteTimeUtc = [DateTime]::new($markerTargetTicks,[DateTimeKind]::Utc)
    Set-ReadOnlyTree $newRoot

    $audit = Test-Root -Root $newRoot -ControlNames $controlNames
    $expectedAudit = [ordered]@{
        ordinary_count=34; payload_count=31; control_count=3; manifest_rows=31;
        manifest_duplicate_path_count=0; manifest_missing_count=0; manifest_extra_count=0;
        manifest_identity_mismatch_count=0; copy_identity_rows=29; copy_identity_mismatch_count=0;
        old_controls_copied_count=0; readonly_file_count=34; writable_file_count=0;
        writable_directory_count=0; ads_count=0; cache_pyc_count=0; reparse_count=0;
        files_at_or_after_marker_excluding_marker=0; post_marker_write_count=0;
        json_parse_failure_count=0; csv_parse_failure_count=0
    }
    foreach ($gate in $expectedAudit.GetEnumerator()) { Assert-Equal $audit[$gate.Key] $gate.Value "final audit $($gate.Key)" }
    Assert-Equal $audit.root_readonly $true 'final audit root_readonly'
    Assert-Equal $audit.marker_unique_latest $true 'final audit marker_unique_latest'
    Write-JsonAtomic $auditPath ([ordered]@{
        schema='P609-root-external-readonly-audit-v1'
        audited_utc=[DateTime]::UtcNow.ToString('o')
        controller=$controllerId
        authorization=$authorizationId
        invocation=[ordered]@{ ordinal=1; limit=1; retry_count=0 }
        audit=$audit
        equations=[ordered]@{
            material_plus_added_equals_payload='29+2=31'
            payload_plus_controls_equals_ordinary='31+3=34'
            readonly_files='34/34'
        }
        status='PASS'
    }) 100
    $handoffText = @"
# P609 evidence-only readonly reseal handoff

- HANDOFF_ID: C-FIG-P609-01-R108-SA2-R168-READONLY-RESEAL-V1
- Decision preserved: P609_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1
- Original instance: /root/sa2_fig_p609_r108_r168_readonly_v1
- Model / effort / fork: gpt-5.6-sol / xhigh / none
- Old root: $oldRoot
- New root: $newRoot
- Invocation: 1/1, retry 0, controller exit 0
- Copy identity: 29/29, path/bytes/SHA/NTFS mtime mismatch 0
- Old controls copied: 0
- New root accounting: material 29 + added payload 2 = payload 31; controls 3; ordinary 34
- Manifest / filesystem mismatches: 0
- Read-only: files 34/34; all directories including root read-only
- Hygiene: ADS/cache/pyc/reparse 0
- Stop marker: unique latest; files at/after excluding marker 0; post-marker writes 0
- Manifest SHA-256: $($audit.manifest_sha256)
- SEAL SHA-256: $($audit.seal_sha256)
- WRITE_STOPPED SHA-256: $($audit.write_stopped_sha256)
- Business evidence, visual/semantic/manual judgments, source, TeX, Git: unchanged / 0
"@
    [System.IO.File]::WriteAllText($handoffPath, $handoffText, [System.Text.UTF8Encoding]::new($false))
    $success = $true
}
catch {
    $failureMessage = $_.Exception.ToString()
    if ($newRoot -and (Test-Path -LiteralPath $newRoot -PathType Container)) {
        $markerPathOnFailure = Join-Path $newRoot 'WRITE_STOPPED'
        if (-not (Test-Path -LiteralPath $markerPathOnFailure -PathType Leaf)) {
            try {
                Write-JsonAtomic (Join-Path $newRoot 'RESEAL_FAILED.json') ([ordered]@{
                    schema='P609-readonly-reseal-failure-v1'
                    failed_utc=[DateTime]::UtcNow.ToString('o')
                    invocation_ordinal=1
                    retry_count=0
                    error=$failureMessage
                })
            } catch {}
        }
        try { Set-ReadOnlyTree $newRoot } catch {}
    }
}
finally {
    $finishedUtc = [DateTime]::UtcNow
    $result = [ordered]@{
        schema='P609-readonly-reseal-controller-result-v1'
        status=if($success){'PASS'}else{'FAIL'}
        controller_exit_code=if($success){0}else{1}
        invocation_count=if($claimWritten){1}else{0}
        invocation_limit=1
        retry_count=0
        started_utc=$startedUtc.ToString('o')
        finished_utc=$finishedUtc.ToString('o')
        duration_seconds=($finishedUtc-$startedUtc).TotalSeconds
        controller=if(Test-Path -LiteralPath $controllerPath){Get-Identity $controllerPath}else{$null}
        authorization=if(Test-Path -LiteralPath $authorizationPath){Get-Identity $authorizationPath}else{$null}
        old_root=if($auth){[string]$auth.old_root}else{$null}
        new_root=$newRoot
        root_external_audit=if(Test-Path -LiteralPath $auditPath){Get-Identity $auditPath}else{$null}
        handoff=if(Test-Path -LiteralPath $handoffPath){Get-Identity $handoffPath}else{$null}
        failure=$failureMessage
    }
    try { Write-JsonAtomic $resultPath $result 100 } catch {}
    try {
        Get-ChildItem -LiteralPath $controllerDir -File -Force | ForEach-Object {
            [System.IO.File]::SetAttributes($_.FullName, ($_.Attributes -bor [System.IO.FileAttributes]::ReadOnly))
        }
        $controllerDirItem = Get-Item -LiteralPath $controllerDir -Force
        [System.IO.File]::SetAttributes($controllerDirItem.FullName, ($controllerDirItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly))
    } catch {}
}

if (-not $success) { exit 1 }
exit 0
