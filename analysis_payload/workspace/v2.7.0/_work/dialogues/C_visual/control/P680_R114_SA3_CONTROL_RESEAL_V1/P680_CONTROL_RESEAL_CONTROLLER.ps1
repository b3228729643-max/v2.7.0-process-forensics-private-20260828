param(
    [Parameter(Mandatory = $true)]
    [string]$AuthorizationToken
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ExpectedToken = 'MAIN_R464_P680_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V1_AUTHORIZATION'
$HandoffId = 'C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1'
$Uid = 'FIG-P680-01'
$Operation = 'P680_R114_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$Verdict = 'SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE'
$SourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1_control_reseal_v1'
$ControlRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P680_R114_SA3_CONTROL_RESEAL_V1'
$ArtifactRoot = Join-Path $ControlRoot 'artifacts'
$ResultPath = Join-Path $ArtifactRoot 'CONTROLLER_RESULT.json'
$SourceBeforePath = Join-Path $ArtifactRoot 'SOURCE_ROOT_BEFORE.csv'
$PostMarkerStatePath = Join-Path $ArtifactRoot 'POSTMARKER_ROOT_STATE.csv'
$StagedMarkerPath = Join-Path $ArtifactRoot 'WRITE_STOPPED.staged'
$SourceManifestPath = Join-Path $SourceRoot 'manifest.json'
$SourceMarkerPath = Join-Path $SourceRoot 'meta\WRITE_STOPPED.txt'
$ExpectedSourceManifestSha = 'D793E4FDF41B268D580FB4BD083C9F710DB388A161CCA360AD599855A9AEC06C'
$ExpectedSourceMarkerSha = 'AD6D3A57E153E0C22D18B273DBDDA023723724E5019F07AFD29ADD0906A27957'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash
}

function Get-RelativePathNormalized {
    param(
        [Parameter(Mandatory = $true)][string]$Root,
        [Parameter(Mandatory = $true)][string]$FullName
    )
    return $FullName.Substring($Root.Length + 1).Replace('\', '/')
}

function Get-RootSnapshot {
    param([Parameter(Mandatory = $true)][string]$Root)
    $records = @()
    $rootItem = Get-Item -LiteralPath $Root -Force
    $records += [pscustomobject][ordered]@{
        KIND = 'DIR'
        RELATIVE_PATH = '.'
        BYTES = 0
        SHA256 = ''
        CREATION_FILETIME_UTC = $rootItem.CreationTimeUtc.ToFileTimeUtc()
        LASTWRITE_FILETIME_UTC = $rootItem.LastWriteTimeUtc.ToFileTimeUtc()
        ATTRIBUTES = [string]$rootItem.Attributes
    }
    foreach ($directory in @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Sort-Object FullName)) {
        $records += [pscustomobject][ordered]@{
            KIND = 'DIR'
            RELATIVE_PATH = Get-RelativePathNormalized -Root $Root -FullName $directory.FullName
            BYTES = 0
            SHA256 = ''
            CREATION_FILETIME_UTC = $directory.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = $directory.LastWriteTimeUtc.ToFileTimeUtc()
            ATTRIBUTES = [string]$directory.Attributes
        }
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Sort-Object FullName)) {
        $records += [pscustomobject][ordered]@{
            KIND = 'FILE'
            RELATIVE_PATH = Get-RelativePathNormalized -Root $Root -FullName $file.FullName
            BYTES = [int64]$file.Length
            SHA256 = Get-Sha256 -LiteralPath $file.FullName
            CREATION_FILETIME_UTC = $file.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = $file.LastWriteTimeUtc.ToFileTimeUtc()
            ATTRIBUTES = [string]$file.Attributes
        }
    }
    return @($records)
}

function Get-CanonicalSnapshotLines {
    param([Parameter(Mandatory = $true)][object[]]$Rows)
    return @($Rows | Sort-Object KIND, RELATIVE_PATH | ForEach-Object {
        '{0}|{1}|{2}|{3}|{4}|{5}|{6}' -f $_.KIND, $_.RELATIVE_PATH, $_.BYTES, $_.SHA256, $_.CREATION_FILETIME_UTC, $_.LASTWRITE_FILETIME_UTC, $_.ATTRIBUTES
    })
}

function Assert-Equal {
    param(
        [Parameter(Mandatory = $true)]$Actual,
        [Parameter(Mandatory = $true)]$Expected,
        [Parameter(Mandatory = $true)][string]$Name
    )
    if ($Actual -ne $Expected) {
        throw "$Name expected=$Expected actual=$Actual"
    }
}

$result = [ordered]@{
    handoff_id = $HandoffId
    uid = $Uid
    operation = $Operation
    invocation_count = 1
    retry_count = 0
    started_utc = [DateTime]::UtcNow.ToString('o')
    finished_utc = $null
    exit_code = 1
    success = $false
    error = $null
    source_root = $SourceRoot
    new_root = $NewRoot
    source_before_rows = 0
    source_after_mismatch = $null
    material_rows = 0
    copy_identity_rows = 0
    payload_rows = 0
    control_rows = 0
    ordinary_files = 0
    manifest_sha256 = $null
    marker_sha256 = $null
    strict_latest_margin_ticks = $null
    at_or_after_excluding_marker = $null
    postmarker_state_mismatch = $null
}

try {
    Assert-Equal -Actual $AuthorizationToken -Expected $ExpectedToken -Name 'AUTHORIZATION_TOKEN'
    Assert-Equal -Actual (Test-Path -LiteralPath $SourceRoot -PathType Container) -Expected $true -Name 'SOURCE_ROOT_CONTAINER'
    Assert-Equal -Actual (Test-Path -LiteralPath $NewRoot) -Expected $false -Name 'NEW_ROOT_ANY'
    Assert-Equal -Actual (Test-Path -LiteralPath $ResultPath) -Expected $false -Name 'CONTROLLER_RESULT_ABSENT'
    Assert-Equal -Actual (Test-Path -LiteralPath $SourceBeforePath) -Expected $false -Name 'SOURCE_BEFORE_ABSENT'
    Assert-Equal -Actual (Test-Path -LiteralPath $PostMarkerStatePath) -Expected $false -Name 'POSTMARKER_STATE_ABSENT'
    Assert-Equal -Actual (Test-Path -LiteralPath $StagedMarkerPath) -Expected $false -Name 'STAGED_MARKER_ABSENT'
    Assert-Equal -Actual (Get-Sha256 -LiteralPath $SourceManifestPath) -Expected $ExpectedSourceManifestSha -Name 'SOURCE_MANIFEST_SHA'
    Assert-Equal -Actual (Get-Sha256 -LiteralPath $SourceMarkerPath) -Expected $ExpectedSourceMarkerSha -Name 'SOURCE_MARKER_SHA'

    $sourceBefore = @(Get-RootSnapshot -Root $SourceRoot)
    $result.source_before_rows = $sourceBefore.Count
    $sourceBefore | Export-Csv -LiteralPath $SourceBeforePath -NoTypeInformation -Encoding utf8NoBOM

    $sourceManifest = Get-Content -LiteralPath $SourceManifestPath -Raw | ConvertFrom-Json
    $sourceRows = @($sourceManifest.listed_files)
    Assert-Equal -Actual $sourceRows.Count -Expected 37 -Name 'SOURCE_MANIFEST_ROWS'
    Assert-Equal -Actual @($sourceRows.relative_path | Group-Object | Where-Object Count -gt 1).Count -Expected 0 -Name 'SOURCE_MANIFEST_DUPLICATES'

    $sourceMaterialPaths = @($sourceRows.relative_path | Sort-Object)
    $sourceMaterialFs = @(Get-ChildItem -LiteralPath $SourceRoot -File -Recurse -Force | Where-Object {
        $_.FullName -ne $SourceManifestPath -and $_.FullName -ne $SourceMarkerPath
    } | ForEach-Object { Get-RelativePathNormalized -Root $SourceRoot -FullName $_.FullName } | Sort-Object)
    Assert-Equal -Actual @(Compare-Object -ReferenceObject $sourceMaterialPaths -DifferenceObject $sourceMaterialFs).Count -Expected 0 -Name 'SOURCE_MANIFEST_FS_SET_DIFF'

    New-Item -ItemType Directory -Path $NewRoot | Out-Null
    $copyRows = @()
    foreach ($row in $sourceRows) {
        $relativePath = [string]$row.relative_path
        $sourcePath = Join-Path $SourceRoot $relativePath.Replace('/', '\')
        $destinationPath = Join-Path $NewRoot $relativePath.Replace('/', '\')
        Assert-Equal -Actual (Test-Path -LiteralPath $sourcePath -PathType Leaf) -Expected $true -Name "SOURCE_MATERIAL_EXISTS:$relativePath"
        $destinationDirectory = Split-Path -Path $destinationPath -Parent
        if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $destinationDirectory | Out-Null
        }
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $destinationItem.IsReadOnly = $false
        $destinationItem.CreationTimeUtc = $sourceItem.CreationTimeUtc
        $destinationItem.LastWriteTimeUtc = $sourceItem.LastWriteTimeUtc
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $sourceSha = Get-Sha256 -LiteralPath $sourcePath
        $destinationSha = Get-Sha256 -LiteralPath $destinationPath
        Assert-Equal -Actual $destinationItem.Length -Expected $sourceItem.Length -Name "COPY_BYTES:$relativePath"
        Assert-Equal -Actual $destinationSha -Expected $sourceSha -Name "COPY_SHA:$relativePath"
        Assert-Equal -Actual $destinationItem.CreationTimeUtc.ToFileTimeUtc() -Expected $sourceItem.CreationTimeUtc.ToFileTimeUtc() -Name "COPY_CREATION:$relativePath"
        Assert-Equal -Actual $destinationItem.LastWriteTimeUtc.ToFileTimeUtc() -Expected $sourceItem.LastWriteTimeUtc.ToFileTimeUtc() -Name "COPY_LASTWRITE:$relativePath"
        $copyRows += [pscustomobject][ordered]@{
            RELATIVE_PATH = $relativePath
            SOURCE_RESOLVED_PATH = $sourceItem.FullName
            DESTINATION_RESOLVED_PATH = $destinationItem.FullName
            BYTES = [int64]$sourceItem.Length
            SHA256 = $sourceSha
            CREATION_FILETIME_UTC = $sourceItem.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = $sourceItem.LastWriteTimeUtc.ToFileTimeUtc()
        }
    }
    Assert-Equal -Actual $copyRows.Count -Expected 37 -Name 'COPY_ROWS'
    Assert-Equal -Actual @($copyRows.RELATIVE_PATH | Group-Object | Where-Object Count -gt 1).Count -Expected 0 -Name 'COPY_IDENTITY_DUPLICATES'
    $copyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
    $copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM

    $provenance = [ordered]@{
        handoff_id = $HandoffId
        uid = $Uid
        operation = $Operation
        control_only = $true
        business_rerun = $false
        source_root = (Get-Item -LiteralPath $SourceRoot -Force).FullName
        destination_root = (Get-Item -LiteralPath $NewRoot -Force).FullName
        source_manifest_path = (Get-Item -LiteralPath $SourceManifestPath -Force).FullName
        source_manifest_sha256 = $ExpectedSourceManifestSha
        source_marker_path = (Get-Item -LiteralPath $SourceMarkerPath -Force).FullName
        source_marker_sha256 = $ExpectedSourceMarkerSha
        source_material_rows = 37
        verdict = $Verdict
        scope = 'evidence-only control reseal; no render, visual, denominator, pair, manual, math, or semantic rerun'
    }
    $provenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
    [System.IO.File]::WriteAllText($provenancePath, ($provenance | ConvertTo-Json -Depth 8), $Utf8NoBom)

    Assert-Equal -Actual (Test-Path -LiteralPath (Join-Path $NewRoot 'manifest.json')) -Expected $false -Name 'OLD_MANIFEST_NOT_COPIED'
    Assert-Equal -Actual (Test-Path -LiteralPath (Join-Path $NewRoot 'meta\WRITE_STOPPED.txt')) -Expected $false -Name 'OLD_MARKER_NOT_COPIED'

    $payloadFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force | Sort-Object FullName)
    Assert-Equal -Actual $payloadFiles.Count -Expected 39 -Name 'PAYLOAD_FS_COUNT'
    $payloadRows = @()
    foreach ($file in $payloadFiles) {
        $payloadRows += [pscustomobject][ordered]@{
            RELATIVE_PATH = Get-RelativePathNormalized -Root $NewRoot -FullName $file.FullName
            BYTES = [int64]$file.Length
            SHA256 = Get-Sha256 -LiteralPath $file.FullName
            CREATION_FILETIME_UTC = $file.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = $file.LastWriteTimeUtc.ToFileTimeUtc()
        }
    }
    Assert-Equal -Actual @($payloadRows.RELATIVE_PATH | Group-Object | Where-Object Count -gt 1).Count -Expected 0 -Name 'PAYLOAD_DUPLICATES'
    $payloadManifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
    $payloadRows | Export-Csv -LiteralPath $payloadManifestPath -NoTypeInformation -Encoding utf8NoBOM
    $payloadManifestSha = Get-Sha256 -LiteralPath $payloadManifestPath

    $sealAudit = [ordered]@{
        handoff_id = $HandoffId
        uid = $Uid
        operation = $Operation
        source_root = $SourceRoot
        sealed_root = $NewRoot
        control_only = $true
        source_material_rows = 37
        copy_identity_rows = $copyRows.Count
        source_to_destination_identity_mismatch = 0
        payload_rows = $payloadRows.Count
        payload_manifest_sha256 = $payloadManifestSha
        old_control_copy_count = 0
        parse_failures_before_marker = 0
        ads_count_before_marker = 0
        cache_pyc_count_before_marker = 0
        reparse_count_before_marker = 0
        verdict = $Verdict
        post_marker_root_writes = 0
    }
    $sealAuditPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
    [System.IO.File]::WriteAllText($sealAuditPath, ($sealAudit | ConvertTo-Json -Depth 8), $Utf8NoBom)

    $jsonFailures = 0
    foreach ($jsonFile in @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force | Where-Object Extension -eq '.json')) {
        try { Get-Content -LiteralPath $jsonFile.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $jsonFailures++ }
    }
    $csvFailures = 0
    foreach ($csvFile in @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force | Where-Object Extension -eq '.csv')) {
        try { Import-Csv -LiteralPath $csvFile.FullName | Out-Null } catch { $csvFailures++ }
    }
    Assert-Equal -Actual $jsonFailures -Expected 0 -Name 'JSON_PARSE_FAILURES'
    Assert-Equal -Actual $csvFailures -Expected 0 -Name 'CSV_PARSE_FAILURES'
    Assert-Equal -Actual @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object Stream -ne ':$DATA' }).Count -Expected 0 -Name 'ADS_COUNT'
    Assert-Equal -Actual @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse | Where-Object { $_.Name -match '\.pyc$|__pycache__|cache' }).Count -Expected 0 -Name 'CACHE_PYC_COUNT'
    Assert-Equal -Actual @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint }).Count -Expected 0 -Name 'REPARSE_COUNT'

    foreach ($file in @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)) {
        $file.IsReadOnly = $true
    }
    foreach ($directory in @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force | Sort-Object FullName -Descending)) {
        $directory.Attributes = $directory.Attributes -bor [System.IO.FileAttributes]::ReadOnly
    }
    $newRootItem = Get-Item -LiteralPath $NewRoot -Force
    $newRootItem.Attributes = $newRootItem.Attributes -bor [System.IO.FileAttributes]::ReadOnly

    $existingFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    $existingDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force)
    Assert-Equal -Actual $existingFiles.Count -Expected 41 -Name 'PREMARKER_FILE_COUNT'
    Assert-Equal -Actual @($existingFiles | Where-Object { -not $_.IsReadOnly }).Count -Expected 0 -Name 'PREMARKER_WRITABLE_FILES'
    Assert-Equal -Actual @($existingDirectories | Where-Object { -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) }).Count -Expected 0 -Name 'PREMARKER_WRITABLE_DIRS'

    $allPremarkerItems = @($existingFiles) + @($existingDirectories)
    $maxPremarkerFileTime = ($allPremarkerItems | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
    $futureFileTime = [int64]$maxPremarkerFileTime + [int64]300000000
    $markerLines = @(
        "HANDOFF_ID=$HandoffId",
        "UID=$Uid",
        "OPERATION=$Operation",
        "SEALED_ROOT=$NewRoot",
        "ACTUAL_SOURCE_ROOT=$SourceRoot",
        'MATERIAL_ROWS=37',
        'PAYLOAD_ROWS=39',
        'MANIFEST_ROWS=39',
        "MANIFEST_SHA256=$payloadManifestSha",
        "VERDICT=$Verdict",
        'CONTROL_ONLY=true',
        'POST_MARKER_ROOT_WRITES=0'
    )
    Assert-Equal -Actual @($markerLines | Where-Object { $_ -notmatch '^[^=]+=[^=].*$' }).Count -Expected 0 -Name 'MARKER_LINE_SYNTAX_PREMOVE'
    Assert-Equal -Actual @($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object Count -gt 1).Count -Expected 0 -Name 'MARKER_DUPLICATE_KEYS_PREMOVE'
    [System.IO.File]::WriteAllText($StagedMarkerPath, (($markerLines -join "`r`n") + "`r`n"), $Utf8NoBom)
    $stagedMarker = Get-Item -LiteralPath $StagedMarkerPath -Force
    $stagedMarker.IsReadOnly = $true
    $stagedMarker.LastWriteTimeUtc = [DateTime]::FromFileTimeUtc($futureFileTime)
    $markerDestination = Join-Path $NewRoot 'WRITE_STOPPED'
    Assert-Equal -Actual (Test-Path -LiteralPath $markerDestination) -Expected $false -Name 'MARKER_DESTINATION_ABSENT'
    Move-Item -LiteralPath $StagedMarkerPath -Destination $markerDestination

    $postMarkerA = @(Get-RootSnapshot -Root $NewRoot)
    $postMarkerA | Export-Csv -LiteralPath $PostMarkerStatePath -NoTypeInformation -Encoding utf8NoBOM
    $sourceAfter = @(Get-RootSnapshot -Root $SourceRoot)
    $sourceMismatch = @(Compare-Object -ReferenceObject (Get-CanonicalSnapshotLines -Rows $sourceBefore) -DifferenceObject (Get-CanonicalSnapshotLines -Rows $sourceAfter)).Count
    Assert-Equal -Actual $sourceMismatch -Expected 0 -Name 'SOURCE_ROOT_BEFORE_AFTER_MISMATCH'
    $postMarkerB = @(Get-RootSnapshot -Root $NewRoot)
    $postMarkerMismatch = @(Compare-Object -ReferenceObject (Get-CanonicalSnapshotLines -Rows $postMarkerA) -DifferenceObject (Get-CanonicalSnapshotLines -Rows $postMarkerB)).Count
    Assert-Equal -Actual $postMarkerMismatch -Expected 0 -Name 'POSTMARKER_ROOT_STATE_MISMATCH'

    $finalFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    $finalDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force)
    $markerItem = Get-Item -LiteralPath $markerDestination -Force
    $maxOtherFileTime = (@($finalFiles | Where-Object FullName -ne $markerItem.FullName) + @($finalDirectories) | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
    $strictMargin = $markerItem.LastWriteTimeUtc.ToFileTimeUtc() - [int64]$maxOtherFileTime
    $atOrAfter = @($finalFiles | Where-Object { $_.FullName -ne $markerItem.FullName -and $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerItem.LastWriteTimeUtc.ToFileTimeUtc() }).Count + @($finalDirectories | Where-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerItem.LastWriteTimeUtc.ToFileTimeUtc() }).Count
    Assert-Equal -Actual $finalFiles.Count -Expected 42 -Name 'FINAL_ORDINARY_FILES'
    Assert-Equal -Actual @($finalFiles | Where-Object { -not $_.IsReadOnly }).Count -Expected 0 -Name 'FINAL_WRITABLE_FILES'
    Assert-Equal -Actual @($finalDirectories | Where-Object { -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) }).Count -Expected 0 -Name 'FINAL_WRITABLE_DIRS'
    Assert-Equal -Actual ($strictMargin -gt 0) -Expected $true -Name 'MARKER_STRICT_LATEST'
    Assert-Equal -Actual $atOrAfter -Expected 0 -Name 'AT_OR_AFTER_EXCLUDING_MARKER'

    $result.exit_code = 0
    $result.success = $true
    $result.source_after_mismatch = $sourceMismatch
    $result.material_rows = 37
    $result.copy_identity_rows = $copyRows.Count
    $result.payload_rows = $payloadRows.Count
    $result.control_rows = 3
    $result.ordinary_files = $finalFiles.Count
    $result.manifest_sha256 = $payloadManifestSha
    $result.marker_sha256 = Get-Sha256 -LiteralPath $markerDestination
    $result.strict_latest_margin_ticks = $strictMargin
    $result.at_or_after_excluding_marker = $atOrAfter
    $result.postmarker_state_mismatch = $postMarkerMismatch
}
catch {
    $result.error = $_.Exception.Message
    if (Test-Path -LiteralPath $NewRoot -PathType Container) {
        foreach ($file in @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)) { $file.IsReadOnly = $true }
        foreach ($directory in @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force | Sort-Object FullName -Descending)) { $directory.Attributes = $directory.Attributes -bor [System.IO.FileAttributes]::ReadOnly }
        $failedRoot = Get-Item -LiteralPath $NewRoot -Force
        $failedRoot.Attributes = $failedRoot.Attributes -bor [System.IO.FileAttributes]::ReadOnly
    }
}
finally {
    $result.finished_utc = [DateTime]::UtcNow.ToString('o')
    [System.IO.File]::WriteAllText($ResultPath, ($result | ConvertTo-Json -Depth 10), $Utf8NoBom)
}

if (-not $result.success) { exit 1 }
exit 0
