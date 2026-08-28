param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$HandoffId = 'C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V2'
$Uid = 'FIG-P683-01'
$Operation = 'P683_R115_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V2'
$Verdict = 'SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE'
$SourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1_control_reseal_v2'
$ControlRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P683_R115_SA3_CONTROL_RESEAL_V2'
$ArtifactRoot = Join-Path $ControlRoot 'artifacts'
$OldManifest = Join-Path $SourceRoot 'MANIFEST_SHA256.csv'
$OldMarker = Join-Path $SourceRoot 'WRITE_STOPPED'
$ExpectedOldManifestSha256 = '6552FAD53836A9D0E3A0368A98C868AD3BB8B4C2BC955C27F1D231D89920294E'
$ExpectedOldMarkerSha256 = '435C310BEBB54CE13403133A7487D4769954F53D223F87049BA1C7684E1B66D9'
$SourceBeforePath = Join-Path $ArtifactRoot 'SOURCE_ROOT_BEFORE.csv'
$PostMarkerStatePath = Join-Path $ArtifactRoot 'POSTMARKER_ROOT_STATE.csv'
$ControllerResultPath = Join-Path $ArtifactRoot 'CONTROLLER_RESULT.json'
$AuditorResultPath = Join-Path $ArtifactRoot 'AUDITOR_RESULT.json'

function Get-Sha256 {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-ResolvedFullPath {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    return [System.IO.Path]::GetFullPath($LiteralPath)
}

function ConvertTo-CanonicalRelativePath {
    param([Parameter(Mandatory = $true)][AllowEmptyString()][string]$RelativePath)
    $canonical = $RelativePath.Replace('\', '/')
    $canonical = [regex]::Replace($canonical, '^(?:\./)+', '')
    if ([string]::IsNullOrWhiteSpace($canonical)) { throw 'EMPTY_RELATIVE_PATH' }
    if ([System.IO.Path]::IsPathRooted($canonical) -or
        $canonical.StartsWith('/', [System.StringComparison]::Ordinal) -or
        $canonical -match '^[A-Za-z]:') { throw "ROOTED_RELATIVE_PATH:$RelativePath" }
    $segments = $canonical.Split([char[]]@('/'), [System.StringSplitOptions]::None)
    foreach ($segment in $segments) {
        if ($segment.Length -eq 0) { throw "EMPTY_PATH_SEGMENT:$RelativePath" }
        if ($segment -ceq '.') { throw "DOT_PATH_SEGMENT:$RelativePath" }
        if ($segment -ceq '..') { throw "PARENT_PATH_SEGMENT:$RelativePath" }
    }
    return [string]::Join('/', $segments)
}

function Assert-CanonicalizationSelfTest {
    $raw = @('.\top.txt', '.\nested\child.txt')
    $expected = @('top.txt', 'nested/child.txt')
    $actual = @($raw | ForEach-Object { ConvertTo-CanonicalRelativePath -RelativePath $_ })
    $diff = @(Compare-Object -ReferenceObject $expected -DifferenceObject $actual -CaseSensitive)
    $multiLeading = ConvertTo-CanonicalRelativePath -RelativePath '.\.\top.txt'
    $preservedCase = ConvertTo-CanonicalRelativePath -RelativePath '.\Case.TXT'
    $invalid = @('', '.', '..', 'a//b', 'a/./b', 'a/../b', '/absolute.txt', 'C:\absolute.txt')
    $rejected = 0
    foreach ($candidate in $invalid) {
        try { $null = ConvertTo-CanonicalRelativePath -RelativePath $candidate }
        catch { $rejected++ }
    }
    if ($diff.Count -ne 0 -or $multiLeading -cne 'top.txt' -or $preservedCase -cne 'Case.TXT' -or $rejected -ne $invalid.Count) { throw 'CANONICALIZATION_SELFTEST_FAILED' }
    return [pscustomobject][ordered]@{
        INPUT_ROWS = $raw.Count
        EXPECTED_ROWS = $expected.Count
        CASE_SENSITIVE_DIFF = $diff.Count
        MULTI_LEADING_RESULT = $multiLeading
        PRESERVED_CASE_RESULT = $preservedCase
        INVALID_ROWS = $invalid.Count
        INVALID_REJECTED = $rejected
    }
}

function Get-CanonicalRelativePath {
    param(
        [Parameter(Mandatory = $true)][string]$BasePath,
        [Parameter(Mandatory = $true)][string]$TargetPath
    )
    return ConvertTo-CanonicalRelativePath -RelativePath ([System.IO.Path]::GetRelativePath($BasePath, $TargetPath))
}

function Get-TreeState {
    param([Parameter(Mandatory = $true)][string]$RootPath)
    $rootFull = Get-ResolvedFullPath -LiteralPath $RootPath
    $items = @((Get-Item -LiteralPath $rootFull)) + @(Get-ChildItem -LiteralPath $rootFull -Force -Recurse)
    $rows = @()
    foreach ($item in $items) {
        $isDirectory = $item.PSIsContainer
        $relative = if ($item.FullName -eq $rootFull) { '.' } else { Get-CanonicalRelativePath -BasePath $rootFull -TargetPath $item.FullName }
        $sha = ''
        $bytes = 0L
        if (-not $isDirectory) {
            $sha = Get-Sha256 -LiteralPath $item.FullName
            $bytes = [int64]$item.Length
        }
        $rows += [pscustomobject][ordered]@{
            RELATIVE_PATH = $relative
            KIND = if ($isDirectory) { 'DIRECTORY' } else { 'FILE' }
            BYTES = $bytes
            SHA256 = $sha
            CREATION_FILETIME_UTC = [int64]$item.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = [int64]$item.LastWriteTimeUtc.ToFileTimeUtc()
            ATTRIBUTES = $item.Attributes.ToString()
        }
    }
    return @($rows | Sort-Object KIND, RELATIVE_PATH)
}

function Compare-StateRows {
    param(
        [Parameter(Mandatory = $true)][array]$Before,
        [Parameter(Mandatory = $true)][array]$After
    )
    $beforeMap = [System.Collections.Generic.Dictionary[string, object]]::new([System.StringComparer]::Ordinal)
    foreach ($row in @($Before)) { $beforeMap["$($row.KIND)|$($row.RELATIVE_PATH)"] = $row }
    $afterMap = [System.Collections.Generic.Dictionary[string, object]]::new([System.StringComparer]::Ordinal)
    foreach ($row in @($After)) { $afterMap["$($row.KIND)|$($row.RELATIVE_PATH)"] = $row }
    $keys = @($beforeMap.Keys + $afterMap.Keys | Sort-Object -CaseSensitive -Unique)
    $mismatch = 0
    foreach ($key in $keys) {
        if (-not $beforeMap.ContainsKey($key) -or -not $afterMap.ContainsKey($key)) { $mismatch++; continue }
        $a = $beforeMap[$key]
        $b = $afterMap[$key]
        if ([string]$a.BYTES -ne [string]$b.BYTES -or
            [string]$a.SHA256 -ne [string]$b.SHA256 -or
            [string]$a.CREATION_FILETIME_UTC -ne [string]$b.CREATION_FILETIME_UTC -or
            [string]$a.LASTWRITE_FILETIME_UTC -ne [string]$b.LASTWRITE_FILETIME_UTC -or
            [string]$a.ATTRIBUTES -ne [string]$b.ATTRIBUTES) { $mismatch++ }
    }
    return $mismatch
}

function Write-Utf8NoBom {
    param(
        [Parameter(Mandatory = $true)][string]$LiteralPath,
        [Parameter(Mandatory = $true)][string]$Text
    )
    [System.IO.File]::WriteAllText($LiteralPath, $Text, [System.Text.UTF8Encoding]::new($false))
}

function Get-MarkerMap {
    param([Parameter(Mandatory = $true)][string]$LiteralPath)
    $bytes = [System.IO.File]::ReadAllBytes($LiteralPath)
    $hasBom = $bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF
    $lines = @(Get-Content -LiteralPath $LiteralPath -Encoding UTF8)
    $map = @{}
    $bad = 0
    $duplicates = 0
    foreach ($line in $lines) {
        if ($line -notmatch '^([A-Z0-9_]+)=([^=\r\n].*)$') { $bad++; continue }
        $key = $Matches[1]
        $value = $Matches[2]
        if ($map.ContainsKey($key)) { $duplicates++; continue }
        $map[$key] = $value
    }
    return [pscustomobject][ordered]@{
        LINES = $lines
        MAP = $map
        HAS_BOM = $hasBom
        BAD_LINES = $bad
        DUPLICATE_KEYS = $duplicates
    }
}

function Assert-NoUnexpectedStreams {
    param([Parameter(Mandatory = $true)][string[]]$FilePaths)
    $bad = @()
    foreach ($filePath in @($FilePaths)) {
        $streams = @(Get-Item -LiteralPath $filePath -Stream * -ErrorAction Stop)
        $bad += @($streams | Where-Object { $_.Stream -ne ':$DATA' })
    }
    if (@($bad).Count -ne 0) { throw "UNEXPECTED_STREAM_COUNT:$(@($bad).Count)" }
}

$canonicalSelfTest = Assert-CanonicalizationSelfTest
if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) { throw 'SOURCE_ROOT_MISSING' }
if (-not (Test-Path -LiteralPath $NewRoot -PathType Container)) { throw 'NEW_ROOT_MISSING' }
foreach ($requiredExternal in @($SourceBeforePath, $PostMarkerStatePath, $ControllerResultPath)) {
    if (-not (Test-Path -LiteralPath $requiredExternal -PathType Leaf)) { throw "REQUIRED_EXTERNAL_MISSING:$requiredExternal" }
}
if (Test-Path -LiteralPath $AuditorResultPath) { throw 'AUDITOR_RESULT_ALREADY_EXISTS' }
if ((Get-Sha256 -LiteralPath $OldManifest) -cne $ExpectedOldManifestSha256) { throw 'OLD_MANIFEST_SHA_MISMATCH' }
if ((Get-Sha256 -LiteralPath $OldMarker) -cne $ExpectedOldMarkerSha256) { throw 'OLD_MARKER_SHA_MISMATCH' }

$controllerResult = Get-Content -LiteralPath $ControllerResultPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($controllerResult.HANDOFF_ID -cne $HandoffId -or $controllerResult.OPERATION -cne $Operation -or -not [bool]$controllerResult.SUCCESS) {
    throw 'CONTROLLER_RESULT_BINDING_FAILED'
}
$sourceBefore = @(Import-Csv -LiteralPath $SourceBeforePath)
$sourceCurrent = @(Get-TreeState -RootPath $SourceRoot)
$sourceMismatch = Compare-StateRows -Before $sourceBefore -After $sourceCurrent
if ($sourceMismatch -ne 0) { throw "SOURCE_ROOT_CHANGED:$sourceMismatch" }

$files = @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -File)
$directories = @((Get-Item -LiteralPath $NewRoot)) + @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -Directory)
if ($files.Count -ne 44) { throw "ORDINARY_FILE_COUNT:$($files.Count)" }
$writableFiles = @($files | Where-Object { -not $_.IsReadOnly })
$writableDirectories = @($directories | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
if ($writableFiles.Count -ne 0 -or $writableDirectories.Count -ne 0) { throw 'READONLY_GATE_FAILED' }

$copyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
$copyProvenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
$manifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
$markerPath = Join-Path $NewRoot 'WRITE_STOPPED'
foreach ($requiredRootFile in @($copyIdentityPath, $copyProvenancePath, $manifestPath, $sealAuditPath, $markerPath)) {
    if (-not (Test-Path -LiteralPath $requiredRootFile -PathType Leaf)) { throw "REQUIRED_ROOT_FILE_MISSING:$requiredRootFile" }
}

$copyRows = @(Import-Csv -LiteralPath $copyIdentityPath)
if ($copyRows.Count -ne 39 -or @($copyRows.RELATIVE_PATH | Sort-Object -CaseSensitive -Unique).Count -ne 39) { throw 'COPY_IDENTITY_ROW_GATE_FAILED' }
$copyMismatch = 0
foreach ($row in $copyRows) {
    $canonicalRelative = ConvertTo-CanonicalRelativePath -RelativePath ([string]$row.RELATIVE_PATH)
    if ($canonicalRelative -cne [string]$row.RELATIVE_PATH) { $copyMismatch++; continue }
    $sourcePath = [string]$row.SOURCE_RESOLVED_PATH
    $destinationPath = [string]$row.DESTINATION_RESOLVED_PATH
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf) -or -not (Test-Path -LiteralPath $destinationPath -PathType Leaf)) { $copyMismatch++; continue }
    $sourceItem = Get-Item -LiteralPath $sourcePath
    $destinationItem = Get-Item -LiteralPath $destinationPath
    if ([int64]$sourceItem.Length -ne [int64]$row.BYTES -or
        [int64]$destinationItem.Length -ne [int64]$row.BYTES -or
        (Get-Sha256 -LiteralPath $sourcePath) -cne [string]$row.SHA256 -or
        (Get-Sha256 -LiteralPath $destinationPath) -cne [string]$row.SHA256 -or
        [int64]$sourceItem.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$row.CREATION_FILETIME_UTC -or
        [int64]$destinationItem.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$row.CREATION_FILETIME_UTC -or
        [int64]$sourceItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$row.LASTWRITE_FILETIME_UTC -or
        [int64]$destinationItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$row.LASTWRITE_FILETIME_UTC) { $copyMismatch++ }
}
if ($copyMismatch -ne 0) { throw "COPY_IDENTITY_MISMATCH:$copyMismatch" }

$provenance = Get-Content -LiteralPath $copyProvenancePath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($provenance.HANDOFF_ID -cne $HandoffId -or $provenance.UID -cne $Uid -or $provenance.OPERATION -cne $Operation -or
    $provenance.SOURCE_ROOT -cne (Get-ResolvedFullPath -LiteralPath $SourceRoot) -or
    $provenance.DESTINATION_ROOT -cne (Get-ResolvedFullPath -LiteralPath $NewRoot) -or
    -not [bool]$provenance.CONTROL_ONLY -or [bool]$provenance.BUSINESS_RERUN) { throw 'PROVENANCE_BINDING_FAILED' }
$provenanceCanonical = @($provenance.CANONICAL_RELATIVE_PATHS | ForEach-Object { ConvertTo-CanonicalRelativePath -RelativePath ([string]$_) })
if ($provenanceCanonical.Count -ne 39 -or @($provenanceCanonical | Sort-Object -CaseSensitive -Unique).Count -ne 39 -or
    @(Compare-Object -ReferenceObject @($copyRows.RELATIVE_PATH | Sort-Object -CaseSensitive) -DifferenceObject @($provenanceCanonical | Sort-Object -CaseSensitive) -CaseSensitive).Count -ne 0) {
    throw 'PROVENANCE_CANONICAL_PATH_SET_FAILED'
}

$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
if ($manifestRows.Count -ne 41 -or @($manifestRows.RELATIVE_PATH | Sort-Object -CaseSensitive -Unique).Count -ne 41) { throw 'MANIFEST_ROW_GATE_FAILED' }
foreach ($row in $manifestRows) {
    if ((ConvertTo-CanonicalRelativePath -RelativePath ([string]$row.RELATIVE_PATH)) -cne [string]$row.RELATIVE_PATH) { throw 'MANIFEST_NONCANONICAL_RELATIVE_PATH' }
}
$controlNames = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$payloadFiles = @($files | Where-Object { (Get-CanonicalRelativePath -BasePath $NewRoot -TargetPath $_.FullName) -cnotin $controlNames })
$manifestSet = @($manifestRows.RELATIVE_PATH | Sort-Object -CaseSensitive)
$payloadSet = @($payloadFiles | ForEach-Object { Get-CanonicalRelativePath -BasePath $NewRoot -TargetPath $_.FullName } | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $manifestSet -DifferenceObject $payloadSet -CaseSensitive).Count -ne 0) { throw 'MANIFEST_SET_MISMATCH' }
$manifestMismatch = 0
foreach ($row in $manifestRows) {
    $path = Join-Path $NewRoot (([string]$row.RELATIVE_PATH) -replace '/', '\')
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestMismatch++; continue }
    $item = Get-Item -LiteralPath $path
    if ([int64]$item.Length -ne [int64]$row.BYTES -or
        (Get-Sha256 -LiteralPath $path) -cne [string]$row.SHA256 -or
        [int64]$item.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$row.CREATION_FILETIME_UTC -or
        [int64]$item.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$row.LASTWRITE_FILETIME_UTC) { $manifestMismatch++ }
}
if ($manifestMismatch -ne 0) { throw "MANIFEST_IDENTITY_MISMATCH:$manifestMismatch" }

$sealAudit = Get-Content -LiteralPath $sealAuditPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($sealAudit.HANDOFF_ID -cne $HandoffId -or $sealAudit.OPERATION -cne $Operation -or
    [int]$sealAudit.PAYLOAD_ROWS -ne 41 -or [int]$sealAudit.PROJECTED_ORDINARY_FILES -ne 44 -or
    $sealAudit.PAYLOAD_MANIFEST_SHA256 -cne (Get-Sha256 -LiteralPath $manifestPath)) { throw 'SEAL_AUDIT_BINDING_FAILED' }

$marker = Get-MarkerMap -LiteralPath $markerPath
if ($marker.HAS_BOM -or $marker.BAD_LINES -ne 0 -or $marker.DUPLICATE_KEYS -ne 0 -or $marker.LINES.Count -ne 13) { throw 'MARKER_SYNTAX_GATE_FAILED' }
$expectedMarker = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    SEALED_ROOT = Get-ResolvedFullPath -LiteralPath $NewRoot
    ACTUAL_SOURCE_ROOT = Get-ResolvedFullPath -LiteralPath $SourceRoot
    MATERIAL_ROWS = '39'
    PAYLOAD_ROWS = '41'
    MANIFEST_ROWS = '41'
    MANIFEST_SHA256 = Get-Sha256 -LiteralPath $manifestPath
    SEAL_AUDIT_SHA256 = Get-Sha256 -LiteralPath $sealAuditPath
    VERDICT = $Verdict
    CONTROL_ONLY = 'true'
    POST_MARKER_ROOT_WRITES = '0'
}
foreach ($key in $expectedMarker.Keys) {
    if (-not $marker.MAP.ContainsKey($key) -or [string]$marker.MAP[$key] -cne [string]$expectedMarker[$key]) { throw "MARKER_REQUIRED_FIELD_MISMATCH:$key" }
}
$markerItem = Get-Item -LiteralPath $markerPath
$otherItems = @($files | Where-Object { $_.FullName -ne $markerPath }) + @($directories)
$atOrAfter = @($otherItems | Where-Object { [int64]$_.LastWriteTimeUtc.ToFileTimeUtc() -ge [int64]$markerItem.LastWriteTimeUtc.ToFileTimeUtc() })
if ($atOrAfter.Count -ne 0) { throw "MARKER_NOT_STRICT_LATEST:$($atOrAfter.Count)" }

foreach ($file in @($files | Where-Object { $_.Extension -ieq '.json' })) { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json }
foreach ($file in @($files | Where-Object { $_.Extension -ieq '.csv' })) { $null = @(Import-Csv -LiteralPath $file.FullName) }
$badCache = @($files | Where-Object { $_.Name -match '\.pyc$' -or $_.FullName -match '[\\/](?:__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|cache)[\\/]' })
if ($badCache.Count -ne 0) { throw "CACHE_OR_PYC_COUNT:$($badCache.Count)" }
$reparse = (@((Get-Item -LiteralPath $NewRoot)) + @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse)) | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 }
if (@($reparse).Count -ne 0) { throw "REPARSE_COUNT:$(@($reparse).Count)" }
Assert-NoUnexpectedStreams -FilePaths @($files.FullName)

$postMarkerRecorded = @(Import-Csv -LiteralPath $PostMarkerStatePath)
$postMarkerCurrent = @(Get-TreeState -RootPath $NewRoot)
$postMarkerMismatch = Compare-StateRows -Before $postMarkerRecorded -After $postMarkerCurrent
if ($postMarkerMismatch -ne 0) { throw "POSTMARKER_STATE_MISMATCH:$postMarkerMismatch" }

$result = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    INVOCATION_COUNT = 1
    SECOND_INVOCATION_ALLOWED = $false
    SUCCESS = $true
    CANONICAL_SELFTEST_CASE_SENSITIVE_DIFF = $canonicalSelfTest.CASE_SENSITIVE_DIFF
    CANONICAL_SELFTEST_INVALID_REJECTED = $canonicalSelfTest.INVALID_REJECTED
    SOURCE_ROOT_MISMATCH = 0
    SOURCE_MATERIAL_ROWS = 39
    COPY_IDENTITY_ROWS = 39
    COPY_IDENTITY_MISMATCH = 0
    PAYLOAD_ROWS = 41
    MANIFEST_ROWS = 41
    MANIFEST_IDENTITY_MISMATCH = 0
    CONTROL_ROWS = 3
    ORDINARY_FILES = 44
    READONLY_FILES = $files.Count
    READONLY_DIRECTORIES = $directories.Count
    WRITE_STOPPED_PHYSICAL_LINES = $marker.LINES.Count
    WRITE_STOPPED_UNIQUE_KEYS = $marker.MAP.Count
    WRITE_STOPPED_BAD_LINES = 0
    WRITE_STOPPED_SHA256 = Get-Sha256 -LiteralPath $markerPath
    PAYLOAD_MANIFEST_SHA256 = Get-Sha256 -LiteralPath $manifestPath
    STRICT_LATEST = $true
    STRICT_LATEST_MARGIN_TICKS = [int64]$markerItem.LastWriteTimeUtc.ToFileTimeUtc() - [int64]($otherItems | ForEach-Object { [int64]$_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
    AT_OR_AFTER_EXCLUDING_MARKER = 0
    POST_MARKER_STATE_MISMATCH = 0
    PARSE_FAILURES = 0
    ADS_FAILURES = 0
    CACHE_PYC_FAILURES = 0
    REPARSE_FAILURES = 0
    VERDICT = $Verdict
}
Write-Utf8NoBom -LiteralPath $AuditorResultPath -Text (($result | ConvertTo-Json -Depth 7) + "`r`n")
Write-Output ($result | ConvertTo-Json -Depth 7 -Compress)
