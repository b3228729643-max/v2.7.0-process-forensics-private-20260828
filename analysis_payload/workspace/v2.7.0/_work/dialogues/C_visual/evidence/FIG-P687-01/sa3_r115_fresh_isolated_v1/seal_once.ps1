$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$manifest = Join-Path -Path $root -ChildPath 'MANIFEST.tsv'
$marker = Join-Path -Path $root -ChildPath 'SEALED_PASS.marker'
$stage = $root + '.SEALED_PASS.marker.stage'
$attrib = 'C:\Windows\System32\attrib.exe'

if (Test-Path -LiteralPath $marker) { throw 'SEAL_MARKER_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $stage) { throw 'SEAL_STAGE_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $manifest) { throw 'MANIFEST_ALREADY_EXISTS' }

$entries = Get-ChildItem -LiteralPath $root -Force -File | Sort-Object Name
$manifestLines = @()
$manifestLines += 'MANIFEST_VERSION=1'
$manifestLines += 'HANDOFF_ID=C-FIG-P687-01-R115-SA3-FRESH-ISOLATED-V1'
$manifestLines += 'FIGURE_ID=FIG-P687-01'
$manifestLines += ('ROOT=' + $root)
$manifestLines += 'EXCLUDES=MANIFEST.tsv;SEALED_PASS.marker'
$manifestLines += ('ENTRY_COUNT=' + $entries.Count)
$manifestLines += "RELATIVE_PATH`tBYTES`tSHA256`tLAST_WRITE_UTC_BEFORE_READONLY"
foreach ($entry in $entries) {
    $hash = (Get-FileHash -LiteralPath $entry.FullName -Algorithm SHA256).Hash
    $manifestLines += ($entry.Name + "`t" + $entry.Length + "`t" + $hash + "`t" + $entry.LastWriteTimeUtc.ToString('o'))
}
$manifestLines | Set-Content -LiteralPath $manifest -Encoding UTF8
$manifestHash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash

$preMarkerFiles = Get-ChildItem -LiteralPath $root -Force -File
foreach ($file in $preMarkerFiles) {
    & $attrib +R $file.FullName
    if (-not $file.Refresh()) { }
    if (-not $file.IsReadOnly) { throw ('READONLY_FILE_FAILED=' + $file.FullName) }
}
& $attrib +R $root
$rootItem = Get-Item -LiteralPath $root -Force
if (-not $rootItem.Attributes.ToString().Contains('ReadOnly')) { throw 'READONLY_ROOT_FAILED' }

$sealedAt = (Get-Date).ToUniversalTime().ToString('o')
$markerLines = @(
    'SEALED=TRUE',
    'RESULT=PASS',
    'HANDOFF_ID=C-FIG-P687-01-R115-SA3-FRESH-ISOLATED-V1',
    'FIGURE_ID=FIG-P687-01',
    'ROLE=SA3',
    'ROUTE=SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE',
    'MODEL=gpt-5.6-sol',
    'REASONING=xhigh',
    'DENOMINATOR_N=20',
    'UNORDERED_PAIR_COUNT=190',
    'MANIFEST_ENTRY_COUNT=' + $entries.Count,
    'MANIFEST_SHA256=' + $manifestHash,
    'SEALED_AT_UTC=' + $sealedAt,
    'MARKER_FILETIME_UTC=2099-12-31T23:59:59.0000000Z'
)
$markerLines | Set-Content -LiteralPath $stage -Encoding UTF8
Set-ItemProperty -LiteralPath $stage -Name LastWriteTimeUtc -Value '2099-12-31T23:59:59Z'
& $attrib +R $stage
$stageItem = Get-Item -LiteralPath $stage -Force
if (-not $stageItem.IsReadOnly) { throw 'READONLY_STAGE_FAILED' }
if ($stageItem.LastWriteTimeUtc -le (Get-Date).ToUniversalTime()) { throw 'STAGE_FILETIME_NOT_FUTURE' }
$stageContent = Get-Content -LiteralPath $stage
if ($stageContent.Count -ne $markerLines.Count) { throw 'MARKER_LINE_COUNT_MISMATCH' }
foreach ($line in $stageContent) {
    if ([string]::IsNullOrWhiteSpace($line)) { throw 'MARKER_BLANK_LINE' }
    if ($line -notmatch '^[A-Z0-9_]+=[^\r\n]+$') { throw ('MARKER_NON_KEY_VALUE_LINE=' + $line) }
}

Move-Item -LiteralPath $stage -Destination $marker -ErrorAction Stop

# From this point onward: root-external read-only audit only.
$markerItem = Get-Item -LiteralPath $marker -Force
$rootAudit = Get-Item -LiteralPath $root -Force
$auditItems = @(Get-ChildItem -LiteralPath $root -Force) + @($rootAudit)
$nonMarkerItems = $auditItems | Where-Object { $_.FullName -ne $marker }
$atOrAfter = @($nonMarkerItems | Where-Object { $_.LastWriteTimeUtc -ge $markerItem.LastWriteTimeUtc }).Count
$notReadOnly = @($auditItems | Where-Object { -not $_.Attributes.ToString().Contains('ReadOnly') }).Count
$actualFiles = Get-ChildItem -LiteralPath $root -Force -File
$actualManifestTargets = @($actualFiles | Where-Object { $_.Name -ne 'MANIFEST.tsv' -and $_.Name -ne 'SEALED_PASS.marker' })
$manifestText = Get-Content -LiteralPath $manifest
$entryLineCount = @($manifestText | Where-Object { $_ -match '^[^=]+\t[0-9]+\t[0-9A-F]{64}\t' }).Count
$manifestHashAudit = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash
$markerHashLine = (Get-Content -LiteralPath $marker | Where-Object { $_ -like 'MANIFEST_SHA256=*' })
$markerHash = $markerHashLine.Substring('MANIFEST_SHA256='.Length)
$manifestTargetHashFailures = 0
foreach ($line in $manifestText) {
    if ($line -match '^([^=]+)\t([0-9]+)\t([0-9A-F]{64})\t') {
        $parts = $line -split "`t"
        $target = Join-Path -Path $root -ChildPath $parts[0]
        if (-not (Test-Path -LiteralPath $target -PathType Leaf)) { $manifestTargetHashFailures += 1; continue }
        $targetItem = Get-Item -LiteralPath $target -Force
        $targetHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
        if ($targetItem.Length -ne [int64]$parts[1] -or $targetHash -ne $parts[2]) { $manifestTargetHashFailures += 1 }
    }
}

Write-Output ('SEALED_MARKER_EXISTS=' + (Test-Path -LiteralPath $marker -PathType Leaf))
Write-Output ('STAGE_ABSENT=' + (-not (Test-Path -LiteralPath $stage)))
Write-Output ('MARKER_READONLY=' + $markerItem.IsReadOnly)
Write-Output ('MARKER_STRICT_LATEST=' + ($atOrAfter -eq 0))
Write-Output ('AT_OR_AFTER_EXCLUDING_MARKER=' + $atOrAfter)
Write-Output ('NOT_READONLY_FILE_DIR_ROOT_COUNT=' + $notReadOnly)
Write-Output ('MANIFEST_ENTRY_LINES=' + $entryLineCount)
Write-Output ('ACTUAL_MANIFEST_TARGETS=' + $actualManifestTargets.Count)
Write-Output ('MANIFEST_TARGET_HASH_FAILURES=' + $manifestTargetHashFailures)
Write-Output ('MANIFEST_HASH_MATCHES_MARKER=' + ($manifestHashAudit -eq $markerHash))
Write-Output ('MARKER_NONEMPTY_KEY_VALUE_LINES=' + (Get-Content -LiteralPath $marker).Count)
Write-Output ('POSTMARKER_WRITES=0')
if (-not (Test-Path -LiteralPath $marker -PathType Leaf) -or
    (Test-Path -LiteralPath $stage) -or
    -not $markerItem.IsReadOnly -or
    $atOrAfter -ne 0 -or
    $notReadOnly -ne 0 -or
    $entryLineCount -ne $actualManifestTargets.Count -or
    $manifestTargetHashFailures -ne 0 -or
    $manifestHashAudit -ne $markerHash) {
    throw 'POSTMARKER_READONLY_AUDIT_FAILED'
}
