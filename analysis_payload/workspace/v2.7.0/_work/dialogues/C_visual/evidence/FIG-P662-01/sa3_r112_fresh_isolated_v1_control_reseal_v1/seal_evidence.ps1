$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$parent = Split-Path -Parent $root
$manifest = Join-Path $root 'MANIFEST.csv'
$marker = Join-Path $root 'WSTOP.txt'
$externalMarker = Join-Path $parent 'sa3_r112_fresh_isolated_v1.WSTOP.pending'
$handoff = 'C-FIG-P662-01-R112-SA3-FRESH-ISOLATED-V1'
$uid = 'FIG-P662-01'
$verdict = 'SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE'

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'SEALED_ROOT_MISSING' }
if (Test-Path -LiteralPath $manifest) { throw 'MANIFEST_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $marker) { throw 'MARKER_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $externalMarker) { throw 'EXTERNAL_MARKER_ALREADY_EXISTS' }

$premarker = @(Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName)
if ($premarker.Count -eq 0) { throw 'EMPTY_PAYLOAD' }

$manifestLines = @('RELATIVE_PATH,BYTES,SHA256,CREATION_FILETIME_TICKS,LASTWRITE_FILETIME_TICKS')
foreach ($file in $premarker) {
    $rel = $file.FullName.Substring($root.Length).TrimStart('\')
    if ($rel.Contains(',')) { throw ('COMMA_IN_RELATIVE_PATH=' + $rel) }
    $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
    $ct = $file.CreationTimeUtc.ToFileTimeUtc()
    $wt = $file.LastWriteTimeUtc.ToFileTimeUtc()
    $manifestLines += ($rel + ',' + $file.Length + ',' + $sha + ',' + $ct + ',' + $wt)
}
Set-Content -LiteralPath $manifest -Value $manifestLines -Encoding utf8 -NoNewline:$false

$manifestRows = $premarker.Count
$manifestSha = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash

$allPremarkerFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName)
$allPremarkerDirs = @((Get-Item -LiteralPath $root)) + @(Get-ChildItem -LiteralPath $root -Recurse -Directory | Sort-Object FullName)

foreach ($file in $allPremarkerFiles) {
    & attrib.exe +R $file.FullName
    if ($LASTEXITCODE -ne 0) { throw ('READONLY_FILE_SET_FAILED=' + $file.FullName) }
}
foreach ($dir in $allPremarkerDirs) {
    & attrib.exe +R $dir.FullName
    if ($LASTEXITCODE -ne 0) { throw ('READONLY_DIR_SET_FAILED=' + $dir.FullName) }
}

$maxPreLast = ($allPremarkerFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc
$maxPreCreate = ($allPremarkerFiles | Sort-Object CreationTimeUtc -Descending | Select-Object -First 1).CreationTimeUtc
$baseTime = [DateTime]::UtcNow
if ($maxPreLast -gt $baseTime) { $baseTime = $maxPreLast }
if ($maxPreCreate -gt $baseTime) { $baseTime = $maxPreCreate }
$markerTime = $baseTime.AddSeconds(2)

$markerLines = @(
    'HANDOFF_ID=' + $handoff,
    'UID=' + $uid,
    'SEALED_ROOT=' + $root,
    'MANIFEST_ROWS=' + $manifestRows,
    'MANIFEST_SHA256=' + $manifestSha,
    'VERDICT=' + $verdict
)
Set-Content -LiteralPath $externalMarker -Value $markerLines -Encoding utf8 -NoNewline:$false
Set-ItemProperty -LiteralPath $externalMarker -Name CreationTimeUtc -Value $markerTime
Set-ItemProperty -LiteralPath $externalMarker -Name LastWriteTimeUtc -Value $markerTime
& attrib.exe +R $externalMarker
if ($LASTEXITCODE -ne 0) { throw 'READONLY_EXTERNAL_MARKER_SET_FAILED' }

# Unique absolute last root-content operation.
Move-Item -LiteralPath $externalMarker -Destination $marker

# Read-only audit begins here. No subsequent content or attribute mutation is permitted.
$markerInfo = Get-Item -LiteralPath $marker
$allFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName)
$allDirs = @((Get-Item -LiteralPath $root)) + @(Get-ChildItem -LiteralPath $root -Recurse -Directory | Sort-Object FullName)
$payloadNow = @($allFiles | Where-Object { $_.FullName -ne $manifest -and $_.FullName -ne $marker })

$readOnlyFileFailures = @($allFiles | Where-Object { -not $_.IsReadOnly }).Count
$readOnlyDirFailures = @($allDirs | Where-Object { -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) }).Count
$markerCount = @($allFiles | Where-Object { $_.Name -eq 'WSTOP.txt' }).Count
$premarkerAtOrAfter = @($allFiles | Where-Object { $_.FullName -ne $marker -and $_.LastWriteTimeUtc -ge $markerInfo.LastWriteTimeUtc }).Count
$markerCreationNotStrict = @($allFiles | Where-Object { $_.FullName -ne $marker -and $_.CreationTimeUtc -ge $markerInfo.CreationTimeUtc }).Count
$markerLaterThanDirs = @($allDirs | Where-Object { $_.LastWriteTimeUtc -ge $markerInfo.LastWriteTimeUtc }).Count

$parsedMarkerLines = @(Get-Content -LiteralPath $marker)
$markerMalformed = @($parsedMarkerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=\t\r\n]+$' }).Count
$markerTabs = @($parsedMarkerLines | Where-Object { $_.Contains("`t") }).Count
$markerPlaceholders = @($parsedMarkerLines | Where-Object { $_ -match '<|>|TODO|TBD|PLACEHOLDER|UNKNOWN' }).Count
$kv = @{}
$markerDuplicateKeys = 0
foreach ($line in $parsedMarkerLines) {
    $parts = $line.Split('=', 2)
    if ($parts.Count -ne 2) { continue }
    if ($kv.ContainsKey($parts[0])) { $markerDuplicateKeys++ }
    $kv[$parts[0]] = $parts[1]
}
$markerRequiredErrors = 0
if ($kv['HANDOFF_ID'] -ne $handoff) { $markerRequiredErrors++ }
if ($kv['UID'] -ne $uid) { $markerRequiredErrors++ }
if ($kv['SEALED_ROOT'] -ne $root) { $markerRequiredErrors++ }
if ($kv['MANIFEST_ROWS'] -ne [string]$manifestRows) { $markerRequiredErrors++ }
if ($kv['MANIFEST_SHA256'] -ne $manifestSha) { $markerRequiredErrors++ }
if ($kv['VERDICT'] -ne $verdict) { $markerRequiredErrors++ }
if ($parsedMarkerLines.Count -ne 6) { $markerRequiredErrors++ }

$rows = @(Import-Csv -LiteralPath $manifest)
$manifestSet = @($rows | ForEach-Object { $_.RELATIVE_PATH } | Sort-Object -Unique)
$fsSet = @($payloadNow | ForEach-Object { $_.FullName.Substring($root.Length).TrimStart('\') } | Sort-Object -Unique)
$setDifferences = @(Compare-Object -ReferenceObject $manifestSet -DifferenceObject $fsSet).Count
$manifestRowErrors = 0
foreach ($row in $rows) {
    $path = Join-Path $root $row.RELATIVE_PATH
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $manifestRowErrors++; continue }
    $info = Get-Item -LiteralPath $path
    $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
    if ([string]$info.Length -ne $row.BYTES) { $manifestRowErrors++ }
    if ($sha -ne $row.SHA256) { $manifestRowErrors++ }
    if ([string]$info.CreationTimeUtc.ToFileTimeUtc() -ne $row.CREATION_FILETIME_TICKS) { $manifestRowErrors++ }
    if ([string]$info.LastWriteTimeUtc.ToFileTimeUtc() -ne $row.LASTWRITE_FILETIME_TICKS) { $manifestRowErrors++ }
}
$manifestIdentityErrors = 0
if ($rows.Count -ne $manifestRows) { $manifestIdentityErrors++ }
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $manifest).Hash -ne $manifestSha) { $manifestIdentityErrors++ }

$pycCount = @($allFiles | Where-Object { $_.Extension -eq '.pyc' }).Count
$cacheCount = @($allDirs | Where-Object { $_.Name -in @('__pycache__', '.cache', 'cache') }).Count
$reparseCount = @($allFiles + $allDirs | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint }).Count
$adsCount = 0
foreach ($file in $allFiles) {
    $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue)
    $adsCount += @($streams | Where-Object { $_.Stream -ne ':$DATA' }).Count
}

function Get-ContentSnapshot {
    param([string]$RootPath)
    $result = @()
    foreach ($file in @(Get-ChildItem -LiteralPath $RootPath -Recurse -File | Sort-Object FullName)) {
        $rel = $file.FullName.Substring($RootPath.Length).TrimStart('\')
        $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
        $result += ($rel + '|' + $file.Length + '|' + $sha + '|' + $file.CreationTimeUtc.ToFileTimeUtc() + '|' + $file.LastWriteTimeUtc.ToFileTimeUtc())
    }
    return $result
}

function Get-AttributeSnapshot {
    param([string]$RootPath)
    $result = @()
    $entries = @((Get-Item -LiteralPath $RootPath)) + @(Get-ChildItem -LiteralPath $RootPath -Recurse | Sort-Object FullName)
    foreach ($entry in $entries) {
        $rel = if ($entry.FullName -eq $RootPath) { '.' } else { $entry.FullName.Substring($RootPath.Length).TrimStart('\') }
        $result += ($rel + '|' + [string]$entry.Attributes)
    }
    return $result
}

$contentSnapshot1 = @(Get-ContentSnapshot -RootPath $root)
$attributeSnapshot1 = @(Get-AttributeSnapshot -RootPath $root)
$contentSnapshot2 = @(Get-ContentSnapshot -RootPath $root)
$attributeSnapshot2 = @(Get-AttributeSnapshot -RootPath $root)
$postmarkerContentChanges = @(Compare-Object -ReferenceObject $contentSnapshot1 -DifferenceObject $contentSnapshot2).Count
$postmarkerAttributeChanges = @(Compare-Object -ReferenceObject $attributeSnapshot1 -DifferenceObject $attributeSnapshot2).Count

$audit = @(
    'SEALED_ROOT=' + $root,
    'MANIFEST_ROWS=' + $manifestRows,
    'MANIFEST_SHA256=' + $manifestSha,
    'MARKER_FILE=' + $marker,
    'MARKER_UNIQUE_COUNT=' + $markerCount,
    'MARKER_MALFORMED_LINES=' + $markerMalformed,
    'MARKER_TAB_LINES=' + $markerTabs,
    'MARKER_PLACEHOLDER_LINES=' + $markerPlaceholders,
    'MARKER_DUPLICATE_KEYS=' + $markerDuplicateKeys,
    'MARKER_REQUIRED_VALUE_ERRORS=' + $markerRequiredErrors,
    'PREMARKER_AT_OR_AFTER_MARKER=' + $premarkerAtOrAfter,
    'PREMARKER_CREATION_AT_OR_AFTER_MARKER=' + $markerCreationNotStrict,
    'DIRECTORY_AT_OR_AFTER_MARKER=' + $markerLaterThanDirs,
    'READONLY_FILE_FAILURES=' + $readOnlyFileFailures,
    'READONLY_DIRECTORY_FAILURES=' + $readOnlyDirFailures,
    'MANIFEST_FS_SET_DIFFERENCES=' + $setDifferences,
    'MANIFEST_ROW_ERRORS=' + $manifestRowErrors,
    'MANIFEST_IDENTITY_ERRORS=' + $manifestIdentityErrors,
    'ADS_NONDEFAULT_COUNT=' + $adsCount,
    'CACHE_DIRECTORY_COUNT=' + $cacheCount,
    'PYC_COUNT=' + $pycCount,
    'REPARSE_COUNT=' + $reparseCount,
    'POSTMARKER_CONTENT_CHANGES=' + $postmarkerContentChanges,
    'POSTMARKER_ATTRIBUTE_CHANGES=' + $postmarkerAttributeChanges,
    'VERDICT=' + $verdict
)
$audit | ForEach-Object { Write-Output $_ }

$failureTotal = $markerMalformed + $markerTabs + $markerPlaceholders + $markerDuplicateKeys + $markerRequiredErrors + $premarkerAtOrAfter + $markerCreationNotStrict + $markerLaterThanDirs + $readOnlyFileFailures + $readOnlyDirFailures + $setDifferences + $manifestRowErrors + $manifestIdentityErrors + $adsCount + $cacheCount + $pycCount + $reparseCount + $postmarkerContentChanges + $postmarkerAttributeChanges
if ($markerCount -ne 1) { $failureTotal++ }
if ($failureTotal -ne 0) { throw ('SEAL_AUDIT_FAILURE_TOTAL=' + $failureTotal) }
