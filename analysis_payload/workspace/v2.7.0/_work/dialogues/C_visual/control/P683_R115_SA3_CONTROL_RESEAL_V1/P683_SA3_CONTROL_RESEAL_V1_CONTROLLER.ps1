param(
    [Parameter(Mandatory = $true)]
    [string]$AuthorizationToken
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ExpectedToken = 'MAIN_R486_P683_SA3_CONTROL_RESEAL_V1_EXECUTE_ONCE_GRANTED'
$HandoffId = 'C-FIG-P683-01-R115-SA3-FRESH-ISOLATED-CONTROL-RESEAL-V1'
$Uid = 'FIG-P683-01'
$Operation = 'P683_R115_SA3_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$Verdict = 'SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE'
$SourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P683-01\sa3_r115_fresh_isolated_v1_control_reseal_v1'
$ControlRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P683_R115_SA3_CONTROL_RESEAL_V1'
$ArtifactRoot = Join-Path $ControlRoot 'artifacts'
$OldManifest = Join-Path $SourceRoot 'MANIFEST_SHA256.csv'
$OldMarker = Join-Path $SourceRoot 'WRITE_STOPPED'
$ExpectedOldManifestSha256 = '6552FAD53836A9D0E3A0368A98C868AD3BB8B4C2BC955C27F1D231D89920294E'
$ExpectedOldMarkerSha256 = '435C310BEBB54CE13403133A7487D4769954F53D223F87049BA1C7684E1B66D9'
$SourceBeforePath = Join-Path $ArtifactRoot 'SOURCE_ROOT_BEFORE.csv'
$PostMarkerStatePath = Join-Path $ArtifactRoot 'POSTMARKER_ROOT_STATE.csv'
$ControllerResultPath = Join-Path $ArtifactRoot 'CONTROLLER_RESULT.json'
$StagedMarkerPath = Join-Path $ArtifactRoot 'WRITE_STOPPED.staged'

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

function Assert-PathInsideRoot {
    param(
        [Parameter(Mandatory = $true)][string]$RootPath,
        [Parameter(Mandatory = $true)][string]$CandidatePath
    )
    $rootFull = (Get-ResolvedFullPath -LiteralPath $RootPath).TrimEnd('\') + '\'
    $candidateFull = Get-ResolvedFullPath -LiteralPath $CandidatePath
    if (-not $candidateFull.StartsWith($rootFull, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "PATH_OUTSIDE_ROOT:$candidateFull"
    }
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

function Assert-NoUnexpectedStreams {
    param([Parameter(Mandatory = $true)][string[]]$FilePaths)
    $bad = @()
    foreach ($filePath in @($FilePaths)) {
        $streams = @(Get-Item -LiteralPath $filePath -Stream * -ErrorAction Stop)
        $bad += @($streams | Where-Object { $_.Stream -ne ':$DATA' })
    }
    if (@($bad).Count -ne 0) { throw "UNEXPECTED_STREAM_COUNT:$(@($bad).Count)" }
}

function Assert-ParseAndHygiene {
    param([Parameter(Mandatory = $true)][string]$RootPath)
    $files = @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File)
    foreach ($file in @($files | Where-Object { $_.Extension -ieq '.json' })) {
        $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    foreach ($file in @($files | Where-Object { $_.Extension -ieq '.csv' })) {
        $null = @(Import-Csv -LiteralPath $file.FullName)
    }
    $badCache = @($files | Where-Object {
        $_.Name -match '\.pyc$' -or $_.FullName -match '[\\/](?:__pycache__|\.pytest_cache|\.mypy_cache|\.ruff_cache|cache)[\\/]'
    })
    if ($badCache.Count -ne 0) { throw "CACHE_OR_PYC_COUNT:$($badCache.Count)" }
    $reparse = (@((Get-Item -LiteralPath $RootPath)) + @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse)) | Where-Object {
        ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
    }
    if (@($reparse).Count -ne 0) { throw "REPARSE_COUNT:$(@($reparse).Count)" }
    Assert-NoUnexpectedStreams -FilePaths @($files.FullName)
}

$canonicalSelfTest = Assert-CanonicalizationSelfTest
if ($AuthorizationToken -cne $ExpectedToken) { throw 'AUTHORIZATION_TOKEN_MISMATCH' }
if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) { throw 'SOURCE_ROOT_MISSING' }
if (Test-Path -LiteralPath $NewRoot) { throw 'NEW_ROOT_ALREADY_EXISTS' }
if (-not (Test-Path -LiteralPath $ArtifactRoot -PathType Container)) { throw 'ARTIFACT_ROOT_MISSING' }
foreach ($externalPath in @($SourceBeforePath, $PostMarkerStatePath, $ControllerResultPath, $StagedMarkerPath)) {
    if (Test-Path -LiteralPath $externalPath) { throw "EXTERNAL_ARTIFACT_ALREADY_EXISTS:$externalPath" }
}
if ((Get-Sha256 -LiteralPath $OldManifest) -cne $ExpectedOldManifestSha256) { throw 'OLD_MANIFEST_SHA_MISMATCH' }
if ((Get-Sha256 -LiteralPath $OldMarker) -cne $ExpectedOldMarkerSha256) { throw 'OLD_MARKER_SHA_MISMATCH' }

$sourceBefore = @(Get-TreeState -RootPath $SourceRoot)
$sourceBefore | Export-Csv -LiteralPath $SourceBeforePath -NoTypeInformation -Encoding utf8NoBOM

$oldRows = @(Import-Csv -LiteralPath $OldManifest)
if ($oldRows.Count -ne 42) { throw "OLD_MANIFEST_ROW_COUNT:$($oldRows.Count)" }
$oldHeader = Get-Content -LiteralPath $OldManifest -TotalCount 1 -Encoding UTF8
if ($oldHeader -cne 'TYPE,RELATIVE_PATH,BYTES,SHA256') { throw 'OLD_MANIFEST_HEADER_MISMATCH' }
$oldFileRows = @($oldRows | Where-Object { [string]$_.TYPE -ceq 'FILE' })
$oldDirectoryRows = @($oldRows | Where-Object { [string]$_.TYPE -ceq 'DIRECTORY' })
$oldRootRows = @($oldRows | Where-Object { [string]$_.TYPE -ceq 'ROOT' })
if ($oldFileRows.Count -ne 39 -or $oldDirectoryRows.Count -ne 2 -or $oldRootRows.Count -ne 1 -or [string]$oldRootRows[0].RELATIVE_PATH -cne '.') {
    throw 'OLD_MANIFEST_TYPE_COUNT_MISMATCH'
}
$manifestDirectoryRelative = @($oldDirectoryRows | ForEach-Object { ConvertTo-CanonicalRelativePath -RelativePath ([string]$_.RELATIVE_PATH) } | Sort-Object -CaseSensitive)
$actualDirectoryRelative = @(Get-ChildItem -LiteralPath $SourceRoot -Force -Recurse -Directory | ForEach-Object { Get-CanonicalRelativePath -BasePath $SourceRoot -TargetPath $_.FullName } | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $manifestDirectoryRelative -DifferenceObject $actualDirectoryRelative -CaseSensitive).Count -ne 0) { throw 'OLD_MANIFEST_DIRECTORY_SET_MISMATCH' }
$materialRows = @()
foreach ($row in $oldFileRows) {
    $relativeCanonical = ConvertTo-CanonicalRelativePath -RelativePath ([string]$row.RelativePath)
    if ($relativeCanonical -cin @('MANIFEST_SHA256.csv', 'WRITE_STOPPED')) { throw "OLD_CONTROL_LISTED_AS_MATERIAL:$relativeCanonical" }
    $sourcePath = Join-Path $SourceRoot ($relativeCanonical -replace '/', '\')
    Assert-PathInsideRoot -RootPath $SourceRoot -CandidatePath $sourcePath
    if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "OLD_MATERIAL_MISSING:$relativeCanonical" }
    $sourceItem = Get-Item -LiteralPath $sourcePath
    if ([int64]$row.Bytes -ne [int64]$sourceItem.Length) { throw "OLD_MANIFEST_BYTES_MISMATCH:$relativeCanonical" }
    if ([string]$row.SHA256 -cne (Get-Sha256 -LiteralPath $sourcePath)) { throw "OLD_MANIFEST_SHA_MISMATCH:$relativeCanonical" }
    $materialRows += [pscustomobject][ordered]@{
        RELATIVE_PATH = $relativeCanonical
        SOURCE_RESOLVED_PATH = Get-ResolvedFullPath -LiteralPath $sourcePath
        SOURCE_BYTES = [int64]$sourceItem.Length
        SOURCE_SHA256 = Get-Sha256 -LiteralPath $sourcePath
        SOURCE_CREATION_FILETIME_UTC = [int64]$sourceItem.CreationTimeUtc.ToFileTimeUtc()
        SOURCE_LASTWRITE_FILETIME_UTC = [int64]$sourceItem.LastWriteTimeUtc.ToFileTimeUtc()
    }
}
if (@($materialRows.RELATIVE_PATH | Sort-Object -CaseSensitive -Unique).Count -ne 39) { throw 'OLD_MANIFEST_DUPLICATE_RELATIVE_PATH' }
$sourceMaterialFiles = @(Get-ChildItem -LiteralPath $SourceRoot -Force -Recurse -File | Where-Object {
    $_.FullName -ne $OldManifest -and $_.FullName -ne $OldMarker
})
$sourceMaterialRelative = @($sourceMaterialFiles | ForEach-Object { Get-CanonicalRelativePath -BasePath $SourceRoot -TargetPath $_.FullName } | Sort-Object -CaseSensitive)
$manifestRelative = @($materialRows.RELATIVE_PATH | Sort-Object -CaseSensitive)
if (@(Compare-Object -ReferenceObject $manifestRelative -DifferenceObject $sourceMaterialRelative -CaseSensitive).Count -ne 0) { throw 'OLD_MANIFEST_SET_MISMATCH' }

$null = New-Item -ItemType Directory -Path $NewRoot
$copyIdentity = @()
foreach ($material in $materialRows) {
    $destinationPath = Join-Path $NewRoot ($material.RELATIVE_PATH -replace '/', '\')
    Assert-PathInsideRoot -RootPath $NewRoot -CandidatePath $destinationPath
    $destinationDirectory = Split-Path -Parent $destinationPath
    if (-not (Test-Path -LiteralPath $destinationDirectory -PathType Container)) {
        $null = New-Item -ItemType Directory -Path $destinationDirectory -Force
    }
    Copy-Item -LiteralPath $material.SOURCE_RESOLVED_PATH -Destination $destinationPath
    $destinationItem = Get-Item -LiteralPath $destinationPath
    $destinationItem.IsReadOnly = $false
    $destinationItem.CreationTimeUtc = [datetime]::FromFileTimeUtc([int64]$material.SOURCE_CREATION_FILETIME_UTC)
    $destinationItem.LastWriteTimeUtc = [datetime]::FromFileTimeUtc([int64]$material.SOURCE_LASTWRITE_FILETIME_UTC)
    $destinationItem = Get-Item -LiteralPath $destinationPath
    $destinationSha = Get-Sha256 -LiteralPath $destinationPath
    if ([int64]$destinationItem.Length -ne [int64]$material.SOURCE_BYTES -or
        $destinationSha -cne [string]$material.SOURCE_SHA256 -or
        [int64]$destinationItem.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$material.SOURCE_CREATION_FILETIME_UTC -or
        [int64]$destinationItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$material.SOURCE_LASTWRITE_FILETIME_UTC) {
        throw "COPY_IDENTITY_MISMATCH:$($material.RELATIVE_PATH)"
    }
    $copyIdentity += [pscustomobject][ordered]@{
        RELATIVE_PATH = $material.RELATIVE_PATH
        SOURCE_RESOLVED_PATH = $material.SOURCE_RESOLVED_PATH
        DESTINATION_RESOLVED_PATH = Get-ResolvedFullPath -LiteralPath $destinationPath
        BYTES = [int64]$destinationItem.Length
        SHA256 = $destinationSha
        CREATION_FILETIME_UTC = [int64]$destinationItem.CreationTimeUtc.ToFileTimeUtc()
        LASTWRITE_FILETIME_UTC = [int64]$destinationItem.LastWriteTimeUtc.ToFileTimeUtc()
    }
}

$copyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
$copyIdentity | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM
$provenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
$provenance = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    CONTROL_ONLY = $true
    BUSINESS_RERUN = $false
    SOURCE_ROOT = Get-ResolvedFullPath -LiteralPath $SourceRoot
    DESTINATION_ROOT = Get-ResolvedFullPath -LiteralPath $NewRoot
    SOURCE_MANIFEST_PATH = Get-ResolvedFullPath -LiteralPath $OldManifest
    SOURCE_MANIFEST_SHA256 = $ExpectedOldManifestSha256
    SOURCE_MARKER_PATH = Get-ResolvedFullPath -LiteralPath $OldMarker
    SOURCE_MARKER_SHA256 = $ExpectedOldMarkerSha256
    MATERIAL_ROWS = 39
    SOURCE_MANIFEST_DIRECTORY_ROWS = 3
    ADDED_PAYLOAD_ROWS = 2
    PAYLOAD_ROWS = 41
    CANONICAL_RELATIVE_PATH_RULE = 'BACKSLASH_TO_SLASH;STRIP_ALL_LEADING_DOT_SLASH;REJECT_EMPTY_ROOTED_EMPTYSEG_DOTSEG_PARENTSEG;PRESERVE_CASE'
    CANONICAL_RELATIVE_PATHS = @($materialRows.RELATIVE_PATH | Sort-Object -CaseSensitive)
    VERDICT = $Verdict
}
Write-Utf8NoBom -LiteralPath $provenancePath -Text (($provenance | ConvertTo-Json -Depth 6) + "`r`n")

$payloadFiles = @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -File)
if ($payloadFiles.Count -ne 41) { throw "PAYLOAD_FILE_COUNT:$($payloadFiles.Count)" }
$payloadManifestRows = @()
foreach ($file in $payloadFiles) {
    $payloadManifestRows += [pscustomobject][ordered]@{
        RELATIVE_PATH = Get-CanonicalRelativePath -BasePath $NewRoot -TargetPath $file.FullName
        BYTES = [int64]$file.Length
        SHA256 = Get-Sha256 -LiteralPath $file.FullName
        CREATION_FILETIME_UTC = [int64]$file.CreationTimeUtc.ToFileTimeUtc()
        LASTWRITE_FILETIME_UTC = [int64]$file.LastWriteTimeUtc.ToFileTimeUtc()
    }
}
if (@($payloadManifestRows.RELATIVE_PATH | Sort-Object -CaseSensitive -Unique).Count -ne 41) { throw 'PAYLOAD_DUPLICATE_RELATIVE_PATH' }
$payloadManifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
$payloadManifestRows | Sort-Object RELATIVE_PATH | Export-Csv -LiteralPath $payloadManifestPath -NoTypeInformation -Encoding utf8NoBOM
$payloadManifestSha = Get-Sha256 -LiteralPath $payloadManifestPath

$sealAuditPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
$sealAudit = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    CONTROL_ONLY = $true
    SOURCE_MATERIAL_ROWS = 39
    COPY_IDENTITY_ROWS = 39
    PAYLOAD_ROWS = 41
    CONTROL_ROWS_BEFORE_MARKER = 2
    PROJECTED_ORDINARY_FILES = 44
    OLD_CONTROLS_COPIED = 0
    COPY_IDENTITY_MISMATCH = 0
    PAYLOAD_MANIFEST_SHA256 = $payloadManifestSha
    VERDICT = $Verdict
    POST_MARKER_ROOT_WRITES = 0
}
Write-Utf8NoBom -LiteralPath $sealAuditPath -Text (($sealAudit | ConvertTo-Json -Depth 6) + "`r`n")
$sealAuditSha = Get-Sha256 -LiteralPath $sealAuditPath

Assert-ParseAndHygiene -RootPath $NewRoot
$premarkerFiles = @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -File)
if ($premarkerFiles.Count -ne 43) { throw "PREMARKER_FILE_COUNT:$($premarkerFiles.Count)" }
$premarkerDirectories = @((Get-Item -LiteralPath $NewRoot)) + @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -Directory)
foreach ($file in $premarkerFiles) { (Get-Item -LiteralPath $file.FullName).IsReadOnly = $true }
foreach ($directory in $premarkerDirectories) {
    $directory.Attributes = $directory.Attributes -bor [System.IO.FileAttributes]::ReadOnly
}
$notReadOnlyFiles = @($premarkerFiles | Where-Object { -not (Get-Item -LiteralPath $_.FullName).IsReadOnly })
$notReadOnlyDirectories = @($premarkerDirectories | Where-Object {
    ((Get-Item -LiteralPath $_.FullName).Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0
})
if ($notReadOnlyFiles.Count -ne 0 -or $notReadOnlyDirectories.Count -ne 0) { throw 'PREMARKER_READONLY_GATE_FAILED' }

$maxOtherTicks = (@($premarkerFiles | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName).LastWriteTimeUtc.ToFileTimeUtc() }) + @($premarkerDirectories | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName).LastWriteTimeUtc.ToFileTimeUtc() }) | Measure-Object -Maximum).Maximum
$nowTicks = [datetime]::UtcNow.ToFileTimeUtc()
$markerTicks = [Math]::Max([int64]$maxOtherTicks + 10000000L, [int64]$nowTicks + 600000000L)
$markerLines = @(
    "HANDOFF_ID=$HandoffId",
    "UID=$Uid",
    "OPERATION=$Operation",
    "SEALED_ROOT=$(Get-ResolvedFullPath -LiteralPath $NewRoot)",
    "ACTUAL_SOURCE_ROOT=$(Get-ResolvedFullPath -LiteralPath $SourceRoot)",
    'MATERIAL_ROWS=39',
    'PAYLOAD_ROWS=41',
    'MANIFEST_ROWS=41',
    "MANIFEST_SHA256=$payloadManifestSha",
    "SEAL_AUDIT_SHA256=$sealAuditSha",
    "VERDICT=$Verdict",
    'CONTROL_ONLY=true',
    'POST_MARKER_ROOT_WRITES=0'
)
if ($markerLines.Count -ne 13) { throw 'MARKER_LINE_COUNT_BUILD_FAILED' }
foreach ($line in $markerLines) {
    if ($line -notmatch '^[A-Z0-9_]+=[^=\r\n].*$') { throw "MARKER_LINE_BUILD_FAILED:$line" }
}
Write-Utf8NoBom -LiteralPath $StagedMarkerPath -Text (($markerLines -join "`r`n") + "`r`n")
$stagedItem = Get-Item -LiteralPath $StagedMarkerPath
$stagedItem.CreationTimeUtc = [datetime]::FromFileTimeUtc($markerTicks)
$stagedItem.LastWriteTimeUtc = [datetime]::FromFileTimeUtc($markerTicks)
$stagedItem.IsReadOnly = $true
$finalMarkerPath = Join-Path $NewRoot 'WRITE_STOPPED'
Move-Item -LiteralPath $StagedMarkerPath -Destination $finalMarkerPath

$postMarkerState = @(Get-TreeState -RootPath $NewRoot)
$postMarkerState | Export-Csv -LiteralPath $PostMarkerStatePath -NoTypeInformation -Encoding utf8NoBOM
$sourceAfter = @(Get-TreeState -RootPath $SourceRoot)
$sourceMismatch = Compare-StateRows -Before $sourceBefore -After $sourceAfter
if ($sourceMismatch -ne 0) { throw "SOURCE_ROOT_AFTER_MISMATCH:$sourceMismatch" }
$finalFiles = @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -File)
$finalDirectories = @((Get-Item -LiteralPath $NewRoot)) + @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -Directory)
$finalMarker = Get-Item -LiteralPath $finalMarkerPath
$otherItems = @($finalFiles | Where-Object { $_.FullName -ne $finalMarkerPath }) + @($finalDirectories)
$atOrAfter = @($otherItems | Where-Object { [int64]$_.LastWriteTimeUtc.ToFileTimeUtc() -ge [int64]$finalMarker.LastWriteTimeUtc.ToFileTimeUtc() })
$finalWritableFiles = @($finalFiles | Where-Object { -not $_.IsReadOnly })
$finalWritableDirectories = @($finalDirectories | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
if ($finalFiles.Count -ne 44 -or $finalWritableFiles.Count -ne 0 -or $finalWritableDirectories.Count -ne 0 -or $atOrAfter.Count -ne 0) {
    throw 'FINAL_CONTROL_GATE_FAILED'
}

$result = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    INVOCATION_COUNT = 1
    SECOND_INVOCATION_ALLOWED = $false
    SUCCESS = $true
    CANONICAL_SELFTEST_CASE_SENSITIVE_DIFF = $canonicalSelfTest.CASE_SENSITIVE_DIFF
    CANONICAL_SELFTEST_INVALID_REJECTED = $canonicalSelfTest.INVALID_REJECTED
    SOURCE_ROOT = Get-ResolvedFullPath -LiteralPath $SourceRoot
    DESTINATION_ROOT = Get-ResolvedFullPath -LiteralPath $NewRoot
    SOURCE_MANIFEST_SHA256 = $ExpectedOldManifestSha256
    SOURCE_MARKER_SHA256 = $ExpectedOldMarkerSha256
    MATERIAL_ROWS = 39
    COPY_IDENTITY_ROWS = 39
    PAYLOAD_ROWS = 41
    CONTROL_ROWS = 3
    ORDINARY_FILES = 44
    PAYLOAD_MANIFEST_SHA256 = $payloadManifestSha
    SEAL_AUDIT_SHA256 = $sealAuditSha
    WRITE_STOPPED_SHA256 = Get-Sha256 -LiteralPath $finalMarkerPath
    WRITE_STOPPED_FILETIME_UTC = [int64]$finalMarker.LastWriteTimeUtc.ToFileTimeUtc()
    MAX_OTHER_FILETIME_UTC = [int64]($otherItems | ForEach-Object { [int64]$_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum
    STRICT_LATEST = $true
    AT_OR_AFTER_EXCLUDING_MARKER = 0
    READONLY_FILES = $finalFiles.Count
    READONLY_DIRECTORIES = $finalDirectories.Count
    SOURCE_ROOT_MISMATCH = 0
    POST_MARKER_ROOT_WRITES = 0
    VERDICT = $Verdict
}
Write-Utf8NoBom -LiteralPath $ControllerResultPath -Text (($result | ConvertTo-Json -Depth 7) + "`r`n")
Write-Output ($result | ConvertTo-Json -Depth 7 -Compress)
