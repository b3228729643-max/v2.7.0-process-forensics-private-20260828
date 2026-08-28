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
$ControllerResultPath = Join-Path $ArtifactRoot 'CONTROLLER_RESULT.json'
$SourceBeforePath = Join-Path $ArtifactRoot 'SOURCE_ROOT_BEFORE.csv'
$PostMarkerStatePath = Join-Path $ArtifactRoot 'POSTMARKER_ROOT_STATE.csv'
$AuditorResultPath = Join-Path $ArtifactRoot 'AUDITOR_RESULT.json'
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
        KIND = 'DIR'; RELATIVE_PATH = '.'; BYTES = 0; SHA256 = ''
        CREATION_FILETIME_UTC = $rootItem.CreationTimeUtc.ToFileTimeUtc()
        LASTWRITE_FILETIME_UTC = $rootItem.LastWriteTimeUtc.ToFileTimeUtc()
        ATTRIBUTES = [string]$rootItem.Attributes
    }
    foreach ($directory in @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Sort-Object FullName)) {
        $records += [pscustomobject][ordered]@{
            KIND = 'DIR'; RELATIVE_PATH = Get-RelativePathNormalized -Root $Root -FullName $directory.FullName; BYTES = 0; SHA256 = ''
            CREATION_FILETIME_UTC = $directory.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = $directory.LastWriteTimeUtc.ToFileTimeUtc()
            ATTRIBUTES = [string]$directory.Attributes
        }
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Sort-Object FullName)) {
        $records += [pscustomobject][ordered]@{
            KIND = 'FILE'; RELATIVE_PATH = Get-RelativePathNormalized -Root $Root -FullName $file.FullName; BYTES = [int64]$file.Length; SHA256 = Get-Sha256 -LiteralPath $file.FullName
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
    if ($Actual -ne $Expected) { throw "$Name expected=$Expected actual=$Actual" }
}

$audit = [ordered]@{
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
    old_root_before_after_mismatch = $null
    copy_identity_rows = 0
    source_destination_mismatch = $null
    payload_manifest_rows = 0
    payload_manifest_fs_mismatch = $null
    ordinary_files = 0
    readonly_files = 0
    readonly_directories = 0
    total_directories = 0
    marker_physical_lines = 0
    marker_unique_keys = 0
    marker_bad_lines = 0
    marker_required_field_mismatch = $null
    strict_latest_margin_ticks = $null
    at_or_after_excluding_marker = $null
    postmarker_state_mismatch = $null
    json_parse_failures = 0
    csv_parse_failures = 0
    ads_count = 0
    cache_pyc_count = 0
    reparse_count = 0
}

try {
    Assert-Equal -Actual $AuthorizationToken -Expected $ExpectedToken -Name 'AUTHORIZATION_TOKEN'
    Assert-Equal -Actual (Test-Path -LiteralPath $AuditorResultPath) -Expected $false -Name 'AUDITOR_RESULT_ABSENT'
    Assert-Equal -Actual (Test-Path -LiteralPath $NewRoot -PathType Container) -Expected $true -Name 'NEW_ROOT_CONTAINER'
    $controllerResult = Get-Content -LiteralPath $ControllerResultPath -Raw | ConvertFrom-Json
    Assert-Equal -Actual $controllerResult.success -Expected $true -Name 'CONTROLLER_SUCCESS'
    Assert-Equal -Actual $controllerResult.invocation_count -Expected 1 -Name 'CONTROLLER_INVOCATION_COUNT'
    Assert-Equal -Actual $controllerResult.retry_count -Expected 0 -Name 'CONTROLLER_RETRY_COUNT'

    $sourceBefore = @(Import-Csv -LiteralPath $SourceBeforePath)
    $sourceCurrent = @(Get-RootSnapshot -Root $SourceRoot)
    $oldMismatch = @(Compare-Object -ReferenceObject (Get-CanonicalSnapshotLines -Rows $sourceBefore) -DifferenceObject (Get-CanonicalSnapshotLines -Rows $sourceCurrent)).Count
    Assert-Equal -Actual $oldMismatch -Expected 0 -Name 'OLD_ROOT_BEFORE_AFTER_MISMATCH'

    $copyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
    $copyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
    Assert-Equal -Actual $copyRows.Count -Expected 37 -Name 'COPY_IDENTITY_ROWS'
    Assert-Equal -Actual @($copyRows.RELATIVE_PATH | Group-Object | Where-Object Count -gt 1).Count -Expected 0 -Name 'COPY_IDENTITY_DUPLICATES'
    $copyMismatch = 0
    foreach ($row in $copyRows) {
        $sourcePath = [string]$row.SOURCE_RESOLVED_PATH
        $destinationPath = [string]$row.DESTINATION_RESOLVED_PATH
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf) -or -not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) { $copyMismatch++; continue }
        $sourceItem = Get-Item -LiteralPath $sourcePath -Force
        $destinationItem = Get-Item -LiteralPath $destinationPath -Force
        $destinationRelative = Get-RelativePathNormalized -Root $NewRoot -FullName $destinationItem.FullName
        if ($destinationRelative -ne $row.RELATIVE_PATH) { $copyMismatch++ }
        if ($sourceItem.Length -ne [int64]$row.BYTES -or $destinationItem.Length -ne [int64]$row.BYTES) { $copyMismatch++ }
        if ((Get-Sha256 -LiteralPath $sourcePath) -ne $row.SHA256 -or (Get-Sha256 -LiteralPath $destinationPath) -ne $row.SHA256) { $copyMismatch++ }
        if ($sourceItem.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$row.CREATION_FILETIME_UTC -or $destinationItem.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$row.CREATION_FILETIME_UTC) { $copyMismatch++ }
        if ($sourceItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$row.LASTWRITE_FILETIME_UTC -or $destinationItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$row.LASTWRITE_FILETIME_UTC) { $copyMismatch++ }
    }
    Assert-Equal -Actual $copyMismatch -Expected 0 -Name 'SOURCE_DESTINATION_IDENTITY_MISMATCH'

    $payloadManifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
    $payloadManifest = @(Import-Csv -LiteralPath $payloadManifestPath)
    Assert-Equal -Actual $payloadManifest.Count -Expected 39 -Name 'PAYLOAD_MANIFEST_ROWS'
    Assert-Equal -Actual @($payloadManifest.RELATIVE_PATH | Group-Object | Where-Object Count -gt 1).Count -Expected 0 -Name 'PAYLOAD_MANIFEST_DUPLICATES'
    $controlNames = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
    $allFiles = @(Get-ChildItem -LiteralPath $NewRoot -File -Recurse -Force)
    $payloadFiles = @($allFiles | Where-Object { (Get-RelativePathNormalized -Root $NewRoot -FullName $_.FullName) -notin $controlNames })
    $payloadFsPaths = @($payloadFiles | ForEach-Object { Get-RelativePathNormalized -Root $NewRoot -FullName $_.FullName } | Sort-Object)
    $manifestPaths = @($payloadManifest.RELATIVE_PATH | Sort-Object)
    $manifestFsMismatch = @(Compare-Object -ReferenceObject $manifestPaths -DifferenceObject $payloadFsPaths).Count
    $manifestIdentityMismatch = 0
    foreach ($row in $payloadManifest) {
        $path = Join-Path $NewRoot ([string]$row.RELATIVE_PATH).Replace('/', '\')
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestIdentityMismatch++; continue }
        $item = Get-Item -LiteralPath $path -Force
        if ($item.Length -ne [int64]$row.BYTES) { $manifestIdentityMismatch++ }
        if ((Get-Sha256 -LiteralPath $path) -ne $row.SHA256) { $manifestIdentityMismatch++ }
        if ($item.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$row.CREATION_FILETIME_UTC) { $manifestIdentityMismatch++ }
        if ($item.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$row.LASTWRITE_FILETIME_UTC) { $manifestIdentityMismatch++ }
    }
    Assert-Equal -Actual $manifestFsMismatch -Expected 0 -Name 'PAYLOAD_MANIFEST_FS_SET_MISMATCH'
    Assert-Equal -Actual $manifestIdentityMismatch -Expected 0 -Name 'PAYLOAD_MANIFEST_IDENTITY_MISMATCH'
    Assert-Equal -Actual $allFiles.Count -Expected 42 -Name 'ORDINARY_FILES'

    $allDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Directory -Recurse -Force)
    $readonlyFileCount = @($allFiles | Where-Object IsReadOnly).Count
    $readonlyDirectoryCount = @($allDirectories | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReadOnly }).Count
    Assert-Equal -Actual $readonlyFileCount -Expected $allFiles.Count -Name 'READONLY_FILES'
    Assert-Equal -Actual $readonlyDirectoryCount -Expected $allDirectories.Count -Name 'READONLY_DIRECTORIES'

    $markerPath = Join-Path $NewRoot 'WRITE_STOPPED'
    $markerBytes = [System.IO.File]::ReadAllBytes($markerPath)
    $hasBom = $markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF
    Assert-Equal -Actual $hasBom -Expected $false -Name 'MARKER_BOM'
    $markerLines = @(Get-Content -LiteralPath $markerPath)
    $markerMap = @{}
    $badLines = 0
    foreach ($line in $markerLines) {
        if ($line -notmatch '^([^=]+)=(.+)$') { $badLines++; continue }
        $key = $matches[1]
        $value = $matches[2]
        if ($markerMap.ContainsKey($key) -or [string]::IsNullOrWhiteSpace($value)) { $badLines++ } else { $markerMap[$key] = $value }
        if ($line.Contains("`t") -or $line -match '<[^>]+>|PLACEHOLDER|TBD|TODO') { $badLines++ }
    }
    $required = [ordered]@{
        HANDOFF_ID = $HandoffId
        UID = $Uid
        OPERATION = $Operation
        SEALED_ROOT = $NewRoot
        ACTUAL_SOURCE_ROOT = $SourceRoot
        MATERIAL_ROWS = '37'
        PAYLOAD_ROWS = '39'
        MANIFEST_ROWS = '39'
        MANIFEST_SHA256 = Get-Sha256 -LiteralPath $payloadManifestPath
        VERDICT = $Verdict
        CONTROL_ONLY = 'true'
        POST_MARKER_ROOT_WRITES = '0'
    }
    $requiredMismatch = 0
    foreach ($key in $required.Keys) {
        if (-not $markerMap.ContainsKey($key) -or $markerMap[$key] -ne $required[$key]) { $requiredMismatch++ }
    }
    Assert-Equal -Actual $badLines -Expected 0 -Name 'MARKER_BAD_LINES'
    Assert-Equal -Actual @($markerMap.Keys).Count -Expected @($required.Keys).Count -Name 'MARKER_KEY_COUNT'
    Assert-Equal -Actual $requiredMismatch -Expected 0 -Name 'MARKER_REQUIRED_FIELD_MISMATCH'

    $markerItem = Get-Item -LiteralPath $markerPath -Force
    $maxOtherFileTime = (@($allFiles | Where-Object FullName -ne $markerItem.FullName) + @($allDirectories) | ForEach-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
    $strictMargin = $markerItem.LastWriteTimeUtc.ToFileTimeUtc() - [int64]$maxOtherFileTime
    $atOrAfter = @($allFiles | Where-Object { $_.FullName -ne $markerItem.FullName -and $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerItem.LastWriteTimeUtc.ToFileTimeUtc() }).Count + @($allDirectories | Where-Object { $_.LastWriteTimeUtc.ToFileTimeUtc() -ge $markerItem.LastWriteTimeUtc.ToFileTimeUtc() }).Count
    Assert-Equal -Actual ($strictMargin -gt 0) -Expected $true -Name 'MARKER_STRICT_LATEST'
    Assert-Equal -Actual $atOrAfter -Expected 0 -Name 'AT_OR_AFTER_EXCLUDING_MARKER'

    $postMarkerReference = @(Import-Csv -LiteralPath $PostMarkerStatePath)
    $postMarkerCurrent = @(Get-RootSnapshot -Root $NewRoot)
    $postMarkerMismatch = @(Compare-Object -ReferenceObject (Get-CanonicalSnapshotLines -Rows $postMarkerReference) -DifferenceObject (Get-CanonicalSnapshotLines -Rows $postMarkerCurrent)).Count
    Assert-Equal -Actual $postMarkerMismatch -Expected 0 -Name 'POSTMARKER_STATE_MISMATCH'

    $jsonFailures = 0
    foreach ($jsonFile in @($allFiles | Where-Object Extension -eq '.json')) {
        try { Get-Content -LiteralPath $jsonFile.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $jsonFailures++ }
    }
    $csvFailures = 0
    foreach ($csvFile in @($allFiles | Where-Object Extension -eq '.csv')) {
        try { Import-Csv -LiteralPath $csvFile.FullName | Out-Null } catch { $csvFailures++ }
    }
    $adsCount = @($allFiles | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object Stream -ne ':$DATA' }).Count
    $cachePycCount = @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse | Where-Object { $_.Name -match '\.pyc$|__pycache__|cache' }).Count
    $reparseCount = @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint }).Count
    Assert-Equal -Actual $jsonFailures -Expected 0 -Name 'JSON_PARSE_FAILURES'
    Assert-Equal -Actual $csvFailures -Expected 0 -Name 'CSV_PARSE_FAILURES'
    Assert-Equal -Actual $adsCount -Expected 0 -Name 'ADS_COUNT'
    Assert-Equal -Actual $cachePycCount -Expected 0 -Name 'CACHE_PYC_COUNT'
    Assert-Equal -Actual $reparseCount -Expected 0 -Name 'REPARSE_COUNT'

    $audit.exit_code = 0
    $audit.success = $true
    $audit.old_root_before_after_mismatch = $oldMismatch
    $audit.copy_identity_rows = $copyRows.Count
    $audit.source_destination_mismatch = $copyMismatch
    $audit.payload_manifest_rows = $payloadManifest.Count
    $audit.payload_manifest_fs_mismatch = $manifestFsMismatch + $manifestIdentityMismatch
    $audit.ordinary_files = $allFiles.Count
    $audit.readonly_files = $readonlyFileCount
    $audit.readonly_directories = $readonlyDirectoryCount
    $audit.total_directories = $allDirectories.Count
    $audit.marker_physical_lines = $markerLines.Count
    $audit.marker_unique_keys = @($markerMap.Keys).Count
    $audit.marker_bad_lines = $badLines
    $audit.marker_required_field_mismatch = $requiredMismatch
    $audit.strict_latest_margin_ticks = $strictMargin
    $audit.at_or_after_excluding_marker = $atOrAfter
    $audit.postmarker_state_mismatch = $postMarkerMismatch
    $audit.json_parse_failures = $jsonFailures
    $audit.csv_parse_failures = $csvFailures
    $audit.ads_count = $adsCount
    $audit.cache_pyc_count = $cachePycCount
    $audit.reparse_count = $reparseCount
}
catch {
    $audit.error = $_.Exception.Message
}
finally {
    $audit.finished_utc = [DateTime]::UtcNow.ToString('o')
    [System.IO.File]::WriteAllText($AuditorResultPath, ($audit | ConvertTo-Json -Depth 10), $Utf8NoBom)
}

if (-not $audit.success) { exit 1 }
exit 0
