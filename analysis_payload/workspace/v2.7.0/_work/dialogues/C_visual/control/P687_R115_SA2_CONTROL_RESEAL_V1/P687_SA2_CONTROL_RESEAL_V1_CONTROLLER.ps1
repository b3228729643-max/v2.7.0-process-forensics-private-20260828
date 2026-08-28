Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$HandoffId = 'C-FIG-P687-01-R115-SA2-R168-READONLY-ADJUDICATION-CONTROL-RESEAL-V1'
$Uid = 'FIG-P687-01'
$Operation = 'P687_R115_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$Verdict = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
$SourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa2_r115_r168_readonly_adjudication_v1'
$NewRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P687-01\sa2_r115_r168_readonly_adjudication_v1_control_reseal_v1'
$ControlRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\control\P687_R115_SA2_CONTROL_RESEAL_V1'
$ArtifactRoot = Join-Path $ControlRoot 'artifacts'
$SourceBeforePath = Join-Path $ArtifactRoot 'SOURCE_ROOT_BEFORE.csv'
$PostMarkerStatePath = Join-Path $ArtifactRoot 'POSTMARKER_ROOT_STATE.csv'
$ControllerResultPath = Join-Path $ArtifactRoot 'CONTROLLER_RESULT.json'
$StagedMarkerPath = Join-Path $ArtifactRoot 'WRITE_STOPPED.staged'
$OldControlNames = @('MANIFEST_CONTROL.txt', 'root_external_readonly_audit.txt', 'WSTOP')

function Write-Utf8NoBom {
    param([string]$LiteralPath, [string]$Text)
    $encoding = [System.Text.UTF8Encoding]::new($false)
    [System.IO.File]::WriteAllText($LiteralPath, $Text, $encoding)
}

function Get-Sha256 {
    param([string]$LiteralPath)
    return (Get-FileHash -LiteralPath $LiteralPath -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-ResolvedFullPath {
    param([string]$LiteralPath)
    return [System.IO.Path]::GetFullPath($LiteralPath)
}

function ConvertTo-CanonicalRelativePath {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) { throw 'CANONICAL_EMPTY' }
    $canonical = $Value.Replace('\', '/')
    $canonical = [regex]::Replace($canonical, '^(?:\./)+', '')
    if ([string]::IsNullOrWhiteSpace($canonical)) { throw 'CANONICAL_EMPTY_AFTER_DOT_SLASH' }
    if ([System.IO.Path]::IsPathRooted($canonical) -or $canonical -match '^[A-Za-z]:') {
        throw "CANONICAL_ROOTED:$Value"
    }
    $segments = $canonical.Split('/')
    if ($segments.Count -eq 0) { throw "CANONICAL_NO_SEGMENTS:$Value" }
    foreach ($segment in $segments) {
        if ([string]::IsNullOrEmpty($segment)) { throw "CANONICAL_EMPTY_SEGMENT:$Value" }
        if ($segment -eq '.') { throw "CANONICAL_DOT_SEGMENT:$Value" }
        if ($segment -eq '..') { throw "CANONICAL_PARENT_SEGMENT:$Value" }
        if ($segment.Contains(':')) { throw "CANONICAL_COLON_SEGMENT:$Value" }
    }
    return [string]::Join('/', $segments)
}

function Resolve-ContainedPath {
    param([string]$Root, [string]$CanonicalRelativePath)
    $canonical = ConvertTo-CanonicalRelativePath -Value $CanonicalRelativePath
    $rootFull = [System.IO.Path]::GetFullPath($Root).TrimEnd('\', '/')
    $nativeRelative = $canonical.Replace('/', [System.IO.Path]::DirectorySeparatorChar)
    $candidate = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($rootFull, $nativeRelative))
    $prefix = $rootFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "PATH_ESCAPE:$canonical"
    }
    return $candidate
}

function Get-CanonicalRelativeFromRoot {
    param([string]$Root, [string]$LiteralPath)
    $relative = [System.IO.Path]::GetRelativePath(
        [System.IO.Path]::GetFullPath($Root),
        [System.IO.Path]::GetFullPath($LiteralPath)
    )
    return ConvertTo-CanonicalRelativePath -Value $relative
}

function Assert-CanonicalSelfTest {
    $left = @('.\top.txt', '.\nested\child.txt') | ForEach-Object { ConvertTo-CanonicalRelativePath -Value $_ }
    $right = @('top.txt', 'nested/child.txt') | ForEach-Object { ConvertTo-CanonicalRelativePath -Value $_ }
    $caseDiff = @(Compare-Object -ReferenceObject $left -DifferenceObject $right -CaseSensitive).Count
    if ($caseDiff -ne 0) { throw "CANONICAL_SELFTEST_DIFF:$caseDiff" }
    if ((ConvertTo-CanonicalRelativePath -Value '.\.\top.txt') -ne 'top.txt') { throw 'CANONICAL_MULTI_PREFIX_FAILED' }
    if ((ConvertTo-CanonicalRelativePath -Value 'Case.TXT') -ne 'Case.TXT') { throw 'CANONICAL_CASE_FAILED' }
    $invalid = @('', '/', '\rooted', 'C:\rooted', 'a//b', 'a/./b', 'a/../b', '../escape')
    $rejected = 0
    foreach ($value in $invalid) {
        try { $null = ConvertTo-CanonicalRelativePath -Value $value } catch { $rejected++ }
    }
    if ($rejected -ne $invalid.Count) { throw "CANONICAL_INVALID_REJECTED:$rejected" }
    return [ordered]@{ CASE_SENSITIVE_DIFF = $caseDiff; INVALID_REJECTED = $rejected }
}

function Get-TreeState {
    param([string]$RootPath)
    $rootItem = Get-Item -LiteralPath $RootPath -Force
    $rows = [System.Collections.Generic.List[object]]::new()
    $rows.Add([pscustomobject][ordered]@{
        TYPE = 'ROOT'
        RELATIVE_PATH = '@ROOT'
        RESOLVED_PATH = [System.IO.Path]::GetFullPath($rootItem.FullName)
        BYTES = ''
        SHA256 = ''
        CREATION_FILETIME_UTC = [int64]$rootItem.CreationTimeUtc.ToFileTimeUtc()
        LASTWRITE_FILETIME_UTC = [int64]$rootItem.LastWriteTimeUtc.ToFileTimeUtc()
        ATTRIBUTES = [int64]$rootItem.Attributes
        READONLY = (($rootItem.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0)
    })
    foreach ($directory in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -Directory | Sort-Object FullName -CaseSensitive)) {
        $rows.Add([pscustomobject][ordered]@{
            TYPE = 'DIRECTORY'
            RELATIVE_PATH = Get-CanonicalRelativeFromRoot -Root $RootPath -LiteralPath $directory.FullName
            RESOLVED_PATH = [System.IO.Path]::GetFullPath($directory.FullName)
            BYTES = ''
            SHA256 = ''
            CREATION_FILETIME_UTC = [int64]$directory.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = [int64]$directory.LastWriteTimeUtc.ToFileTimeUtc()
            ATTRIBUTES = [int64]$directory.Attributes
            READONLY = (($directory.Attributes -band [System.IO.FileAttributes]::ReadOnly) -ne 0)
        })
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File | Sort-Object FullName -CaseSensitive)) {
        $rows.Add([pscustomobject][ordered]@{
            TYPE = 'FILE'
            RELATIVE_PATH = Get-CanonicalRelativeFromRoot -Root $RootPath -LiteralPath $file.FullName
            RESOLVED_PATH = [System.IO.Path]::GetFullPath($file.FullName)
            BYTES = [int64]$file.Length
            SHA256 = Get-Sha256 -LiteralPath $file.FullName
            CREATION_FILETIME_UTC = [int64]$file.CreationTimeUtc.ToFileTimeUtc()
            LASTWRITE_FILETIME_UTC = [int64]$file.LastWriteTimeUtc.ToFileTimeUtc()
            ATTRIBUTES = [int64]$file.Attributes
            READONLY = $file.IsReadOnly
        })
    }
    return @($rows)
}

function Compare-StateRows {
    param([object[]]$Before, [object[]]$After)
    $fields = @('TYPE','RELATIVE_PATH','RESOLVED_PATH','BYTES','SHA256','CREATION_FILETIME_UTC','LASTWRITE_FILETIME_UTC','ATTRIBUTES','READONLY')
    $beforeMap = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
    $afterMap = [System.Collections.Generic.Dictionary[string,string]]::new([System.StringComparer]::Ordinal)
    foreach ($row in $Before) {
        $key = "$($row.TYPE)|$($row.RELATIVE_PATH)"
        $beforeMap.Add($key, (($fields | ForEach-Object { [string]$row.$_ }) -join '|'))
    }
    foreach ($row in $After) {
        $key = "$($row.TYPE)|$($row.RELATIVE_PATH)"
        $afterMap.Add($key, (($fields | ForEach-Object { [string]$row.$_ }) -join '|'))
    }
    $mismatch = 0
    foreach ($key in $beforeMap.Keys) {
        if (-not $afterMap.ContainsKey($key) -or $beforeMap[$key] -cne $afterMap[$key]) { $mismatch++ }
    }
    foreach ($key in $afterMap.Keys) {
        if (-not $beforeMap.ContainsKey($key)) { $mismatch++ }
    }
    return $mismatch
}

function Assert-ParseAndHygiene {
    param([string]$RootPath)
    $parseFailures = 0
    foreach ($csv in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File -Filter '*.csv')) {
        try { $null = @(Import-Csv -LiteralPath $csv.FullName) } catch { $parseFailures++ }
    }
    foreach ($json in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File -Filter '*.json')) {
        try { $null = (Get-Content -LiteralPath $json.FullName -Raw | ConvertFrom-Json) } catch { $parseFailures++ }
    }
    if ($parseFailures -ne 0) { throw "PARSE_FAILURES:$parseFailures" }
    $adsFailures = 0
    foreach ($file in @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse -File)) {
        $extraStreams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop | Where-Object { $_.Stream -notin @(':$DATA', '$DATA') })
        $adsFailures += $extraStreams.Count
    }
    if ($adsFailures -ne 0) { throw "ADS_FAILURES:$adsFailures" }
    $cachePyc = @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse | Where-Object { $_.Name -eq '__pycache__' -or $_.Extension -eq '.pyc' -or $_.Name -match '(^|[._-])cache($|[._-])' })
    if ($cachePyc.Count -ne 0) { throw "CACHE_PYC_FAILURES:$($cachePyc.Count)" }
    $reparse = @(Get-ChildItem -LiteralPath $RootPath -Force -Recurse | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 })
    if ($reparse.Count -ne 0) { throw "REPARSE_FAILURES:$($reparse.Count)" }
}

$selfTest = Assert-CanonicalSelfTest
if (-not (Test-Path -LiteralPath $SourceRoot -PathType Container)) { throw 'SOURCE_ROOT_MISSING' }
if (Test-Path -LiteralPath $NewRoot) { throw 'NEW_ROOT_NOT_ABSENT' }
if (-not (Test-Path -LiteralPath $ArtifactRoot -PathType Container)) { throw 'ARTIFACT_ROOT_MISSING' }
if (@(Get-ChildItem -LiteralPath $ArtifactRoot -Force).Count -ne 0) { throw 'ARTIFACT_ROOT_NOT_EMPTY' }

$sourceBefore = @(Get-TreeState -RootPath $SourceRoot)
$sourceBefore | Export-Csv -LiteralPath $SourceBeforePath -NoTypeInformation -Encoding utf8NoBOM
$sourceFiles = @(Get-ChildItem -LiteralPath $SourceRoot -Force -Recurse -File)
$sourceDirectories = @(Get-ChildItem -LiteralPath $SourceRoot -Force -Recurse -Directory)
if ($sourceFiles.Count -ne 40 -or $sourceDirectories.Count -ne 0) { throw "SOURCE_COUNTS:$($sourceFiles.Count):$($sourceDirectories.Count)" }
if (@($sourceFiles | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'SOURCE_WRITABLE_FILE' }
$sourceRootItem = Get-Item -LiteralPath $SourceRoot -Force
if (($sourceRootItem.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0) { throw 'SOURCE_ROOT_NOT_READONLY' }

$oldControlSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($name in $OldControlNames) { $null = $oldControlSet.Add($name) }
$sourceRows = [System.Collections.Generic.List[object]]::new()
$seenMaterial = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
$seenControls = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($file in $sourceFiles) {
    $relative = Get-CanonicalRelativeFromRoot -Root $SourceRoot -LiteralPath $file.FullName
    if ($oldControlSet.Contains($relative)) {
        if (-not $seenControls.Add($relative)) { throw "OLD_CONTROL_DUPLICATE:$relative" }
        continue
    }
    if (-not $seenMaterial.Add($relative)) { throw "MATERIAL_DUPLICATE:$relative" }
    $sourceRows.Add([pscustomobject][ordered]@{
        RELATIVE_PATH = $relative
        SOURCE_RESOLVED_PATH = [System.IO.Path]::GetFullPath($file.FullName)
        BYTES = [int64]$file.Length
        SHA256 = Get-Sha256 -LiteralPath $file.FullName
        CREATION_FILETIME_UTC = [int64]$file.CreationTimeUtc.ToFileTimeUtc()
        LASTWRITE_FILETIME_UTC = [int64]$file.LastWriteTimeUtc.ToFileTimeUtc()
    })
}
if ($sourceRows.Count -ne 37 -or $seenControls.Count -ne 3) { throw "MATERIAL_CONTROL_COUNTS:$($sourceRows.Count):$($seenControls.Count)" }
foreach ($name in $OldControlNames) { if (-not $seenControls.Contains($name)) { throw "OLD_CONTROL_MISSING:$name" } }

$null = New-Item -ItemType Directory -Path $NewRoot
$copyRows = [System.Collections.Generic.List[object]]::new()
foreach ($row in @($sourceRows | Sort-Object RELATIVE_PATH -CaseSensitive)) {
    $destination = Resolve-ContainedPath -Root $NewRoot -CanonicalRelativePath $row.RELATIVE_PATH
    $destinationParent = [System.IO.Path]::GetDirectoryName($destination)
    $null = [System.IO.Directory]::CreateDirectory($destinationParent)
    [System.IO.File]::Copy($row.SOURCE_RESOLVED_PATH, $destination, $false)
    $destinationItem = Get-Item -LiteralPath $destination -Force
    $destinationItem.IsReadOnly = $false
    $destinationItem.CreationTimeUtc = [datetime]::FromFileTimeUtc([int64]$row.CREATION_FILETIME_UTC)
    $destinationItem.LastWriteTimeUtc = [datetime]::FromFileTimeUtc([int64]$row.LASTWRITE_FILETIME_UTC)
    $destinationItem = Get-Item -LiteralPath $destination -Force
    $destinationSha = Get-Sha256 -LiteralPath $destination
    if ([int64]$destinationItem.Length -ne [int64]$row.BYTES -or $destinationSha -cne [string]$row.SHA256 -or [int64]$destinationItem.CreationTimeUtc.ToFileTimeUtc() -ne [int64]$row.CREATION_FILETIME_UTC -or [int64]$destinationItem.LastWriteTimeUtc.ToFileTimeUtc() -ne [int64]$row.LASTWRITE_FILETIME_UTC) {
        throw "COPY_IDENTITY_MISMATCH:$($row.RELATIVE_PATH)"
    }
    $copyRows.Add([pscustomobject][ordered]@{
        RELATIVE_PATH = $row.RELATIVE_PATH
        SOURCE_RESOLVED_PATH = $row.SOURCE_RESOLVED_PATH
        DESTINATION_RESOLVED_PATH = [System.IO.Path]::GetFullPath($destination)
        SOURCE_BYTES = [int64]$row.BYTES
        DESTINATION_BYTES = [int64]$destinationItem.Length
        SOURCE_SHA256 = $row.SHA256
        DESTINATION_SHA256 = $destinationSha
        SOURCE_CREATION_FILETIME_UTC = [int64]$row.CREATION_FILETIME_UTC
        DESTINATION_CREATION_FILETIME_UTC = [int64]$destinationItem.CreationTimeUtc.ToFileTimeUtc()
        SOURCE_LASTWRITE_FILETIME_UTC = [int64]$row.LASTWRITE_FILETIME_UTC
        DESTINATION_LASTWRITE_FILETIME_UTC = [int64]$destinationItem.LastWriteTimeUtc.ToFileTimeUtc()
    })
}

$copyIdentityPath = Join-Path $NewRoot 'COPY_IDENTITY.csv'
$copyRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM
$oldControlIdentities = @($OldControlNames | ForEach-Object {
    $path = Join-Path $SourceRoot $_
    $item = Get-Item -LiteralPath $path -Force
    [ordered]@{ RELATIVE_PATH = $_; BYTES = [int64]$item.Length; SHA256 = Get-Sha256 -LiteralPath $path; CREATION_FILETIME_UTC = [int64]$item.CreationTimeUtc.ToFileTimeUtc(); LASTWRITE_FILETIME_UTC = [int64]$item.LastWriteTimeUtc.ToFileTimeUtc() }
})
$provenance = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    SOURCE_ROOT = Get-ResolvedFullPath -LiteralPath $SourceRoot
    DESTINATION_ROOT = Get-ResolvedFullPath -LiteralPath $NewRoot
    MATERIAL_ROWS = 37
    COPY_IDENTITY_ROWS = 37
    OLD_CONTROLS_COPIED = 0
    OLD_CONTROL_IDENTITIES = $oldControlIdentities
    CONTROL_ONLY = $true
    BUSINESS_RERUN = $false
    VERDICT = $Verdict
}
$copyProvenancePath = Join-Path $NewRoot 'COPY_PROVENANCE.json'
Write-Utf8NoBom -LiteralPath $copyProvenancePath -Text (($provenance | ConvertTo-Json -Depth 8) + "`r`n")

$payloadPaths = [System.Collections.Generic.List[string]]::new()
foreach ($row in $sourceRows) { $payloadPaths.Add($row.RELATIVE_PATH) }
$payloadPaths.Add('COPY_IDENTITY.csv')
$payloadPaths.Add('COPY_PROVENANCE.json')
if ($payloadPaths.Count -ne 39) { throw "PAYLOAD_PROJECTED_COUNT:$($payloadPaths.Count)" }
$payloadRows = [System.Collections.Generic.List[object]]::new()
foreach ($relative in @($payloadPaths | Sort-Object -CaseSensitive)) {
    $path = Resolve-ContainedPath -Root $NewRoot -CanonicalRelativePath $relative
    $item = Get-Item -LiteralPath $path -Force
    $payloadRows.Add([pscustomobject][ordered]@{
        RELATIVE_PATH = $relative
        RESOLVED_PATH = [System.IO.Path]::GetFullPath($path)
        BYTES = [int64]$item.Length
        SHA256 = Get-Sha256 -LiteralPath $path
        CREATION_FILETIME_UTC = [int64]$item.CreationTimeUtc.ToFileTimeUtc()
        LASTWRITE_FILETIME_UTC = [int64]$item.LastWriteTimeUtc.ToFileTimeUtc()
    })
}
$payloadManifestPath = Join-Path $NewRoot 'PAYLOAD_MANIFEST.csv'
$payloadRows | Export-Csv -LiteralPath $payloadManifestPath -NoTypeInformation -Encoding utf8NoBOM
$payloadManifestSha = Get-Sha256 -LiteralPath $payloadManifestPath

$sealAudit = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    SOURCE_ROOT = Get-ResolvedFullPath -LiteralPath $SourceRoot
    SEALED_ROOT = Get-ResolvedFullPath -LiteralPath $NewRoot
    MATERIAL_ROWS = 37
    COPY_IDENTITY_ROWS = 37
    PAYLOAD_ROWS = 39
    CONTROL_ROWS = 3
    PROJECTED_ORDINARY_FILES = 42
    OLD_CONTROLS_COPIED = 0
    COPY_IDENTITY_MISMATCH = 0
    PAYLOAD_MANIFEST_SHA256 = $payloadManifestSha
    VERDICT = $Verdict
    CONTROL_ONLY = $true
    BUSINESS_RERUN = $false
    POST_MARKER_ROOT_WRITES = 0
}
$sealAuditPath = Join-Path $NewRoot 'SEAL_AUDIT.json'
Write-Utf8NoBom -LiteralPath $sealAuditPath -Text (($sealAudit | ConvertTo-Json -Depth 8) + "`r`n")
$sealAuditSha = Get-Sha256 -LiteralPath $sealAuditPath

Assert-ParseAndHygiene -RootPath $NewRoot
$premarkerFiles = @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -File)
$premarkerDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -Directory)
if ($premarkerFiles.Count -ne 41) { throw "PREMARKER_FILE_COUNT:$($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { (Get-Item -LiteralPath $file.FullName -Force).IsReadOnly = $true }
foreach ($directory in $premarkerDirectories) { $directory.Attributes = $directory.Attributes -bor [System.IO.FileAttributes]::ReadOnly }
$writableFiles = @($premarkerFiles | Where-Object { -not (Get-Item -LiteralPath $_.FullName -Force).IsReadOnly })
$writableDirectories = @($premarkerDirectories | Where-Object { ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
if ($writableFiles.Count -ne 0 -or $writableDirectories.Count -ne 0) { throw 'PREMARKER_READONLY_GATE_FAILED' }

$allPremarkerItems = @($premarkerFiles) + @($premarkerDirectories)
$maxOtherTicks = [int64](($allPremarkerItems | ForEach-Object { [int64](Get-Item -LiteralPath $_.FullName -Force).LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum)
$nowTicks = [datetime]::UtcNow.ToFileTimeUtc()
$markerTicks = [Math]::Max($maxOtherTicks + 10000000L, $nowTicks + 600000000L)
$markerLines = @(
    "HANDOFF_ID=$HandoffId",
    "UID=$Uid",
    "OPERATION=$Operation",
    "SEALED_ROOT=$(Get-ResolvedFullPath -LiteralPath $NewRoot)",
    "ACTUAL_SOURCE_ROOT=$(Get-ResolvedFullPath -LiteralPath $SourceRoot)",
    'MATERIAL_ROWS=37',
    'COPY_IDENTITY_ROWS=37',
    'PAYLOAD_ROWS=39',
    'CONTROL_ROWS=3',
    'ORDINARY_FILES=42',
    'MANIFEST_ROWS=39',
    "MANIFEST_SHA256=$payloadManifestSha",
    "SEAL_AUDIT_SHA256=$sealAuditSha",
    "VERDICT=$Verdict",
    'OLD_CONTROLS_COPIED=0',
    'CONTROL_ONLY=true',
    'BUSINESS_RERUN=false',
    'POST_MARKER_ROOT_WRITES=0'
)
if ($markerLines.Count -ne 18) { throw 'MARKER_LINE_COUNT_BUILD_FAILED' }
foreach ($line in $markerLines) { if ($line -notmatch '^[A-Z0-9_]+=[^=\r\n].*$') { throw "MARKER_LINE_BUILD_FAILED:$line" } }
Write-Utf8NoBom -LiteralPath $StagedMarkerPath -Text (($markerLines -join "`r`n") + "`r`n")
$stagedBytes = [System.IO.File]::ReadAllBytes($StagedMarkerPath)
if ($stagedBytes.Length -ge 3 -and $stagedBytes[0] -eq 0xEF -and $stagedBytes[1] -eq 0xBB -and $stagedBytes[2] -eq 0xBF) { throw 'MARKER_BOM_PRESENT' }
$stagedParsed = @{}
foreach ($line in @(Get-Content -LiteralPath $StagedMarkerPath)) {
    if ($line -notmatch '^([^=]+)=(.+)$') { throw "MARKER_PARSE_FAILED:$line" }
    if ($stagedParsed.ContainsKey($Matches[1])) { throw "MARKER_DUPLICATE_KEY:$($Matches[1])" }
    $stagedParsed[$Matches[1]] = $Matches[2]
}
if ($stagedParsed.Count -ne 18) { throw 'MARKER_KEY_COUNT_FAILED' }
$stagedItem = Get-Item -LiteralPath $StagedMarkerPath -Force
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
$finalDirectories = @((Get-Item -LiteralPath $NewRoot -Force)) + @(Get-ChildItem -LiteralPath $NewRoot -Force -Recurse -Directory)
$finalMarker = Get-Item -LiteralPath $finalMarkerPath -Force
$otherItems = @($finalFiles | Where-Object { $_.FullName -cne $finalMarkerPath }) + @($finalDirectories)
$atOrAfter = @($otherItems | Where-Object { [int64]$_.LastWriteTimeUtc.ToFileTimeUtc() -ge [int64]$finalMarker.LastWriteTimeUtc.ToFileTimeUtc() })
$finalWritableFiles = @($finalFiles | Where-Object { -not $_.IsReadOnly })
$finalWritableDirectories = @($finalDirectories | Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) -eq 0 })
if ($finalFiles.Count -ne 42 -or $finalWritableFiles.Count -ne 0 -or $finalWritableDirectories.Count -ne 0 -or $atOrAfter.Count -ne 0) { throw 'FINAL_CONTROL_GATE_FAILED' }

$result = [ordered]@{
    HANDOFF_ID = $HandoffId
    UID = $Uid
    OPERATION = $Operation
    INVOCATION_COUNT = 1
    SECOND_INVOCATION_ALLOWED = $false
    SUCCESS = $true
    CANONICAL_SELFTEST_CASE_SENSITIVE_DIFF = $selfTest.CASE_SENSITIVE_DIFF
    CANONICAL_SELFTEST_INVALID_REJECTED = $selfTest.INVALID_REJECTED
    SOURCE_ROOT = Get-ResolvedFullPath -LiteralPath $SourceRoot
    DESTINATION_ROOT = Get-ResolvedFullPath -LiteralPath $NewRoot
    SOURCE_MATERIAL_ROWS = 37
    OLD_CONTROLS_COPIED = 0
    COPY_IDENTITY_ROWS = 37
    COPY_IDENTITY_MISMATCH = 0
    PAYLOAD_ROWS = 39
    CONTROL_ROWS = 3
    ORDINARY_FILES = 42
    PAYLOAD_MANIFEST_SHA256 = $payloadManifestSha
    SEAL_AUDIT_SHA256 = $sealAuditSha
    WRITE_STOPPED_SHA256 = Get-Sha256 -LiteralPath $finalMarkerPath
    WRITE_STOPPED_FILETIME_UTC = [int64]$finalMarker.LastWriteTimeUtc.ToFileTimeUtc()
    MAX_OTHER_FILETIME_UTC = [int64](($otherItems | ForEach-Object { [int64]$_.LastWriteTimeUtc.ToFileTimeUtc() } | Measure-Object -Maximum).Maximum)
    STRICT_LATEST = $true
    AT_OR_AFTER_EXCLUDING_MARKER = 0
    READONLY_FILES = $finalFiles.Count
    READONLY_DIRECTORIES = $finalDirectories.Count
    SOURCE_ROOT_MISMATCH = 0
    POST_MARKER_ROOT_WRITES = 0
    VERDICT = $Verdict
}
Write-Utf8NoBom -LiteralPath $ControllerResultPath -Text (($result | ConvertTo-Json -Depth 8) + "`r`n")
$result | ConvertTo-Json -Compress
