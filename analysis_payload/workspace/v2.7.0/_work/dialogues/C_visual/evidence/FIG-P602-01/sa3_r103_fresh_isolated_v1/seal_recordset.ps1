$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$recordRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$manifestPath = Join-Path $recordRoot 'MANIFEST.json'
$markerPath = Join-Path $recordRoot 'WRITE_STOPPED'

if (Test-Path -LiteralPath $manifestPath) {
    throw 'MANIFEST.json already exists; refusing to reseal.'
}
if (Test-Path -LiteralPath $markerPath) {
    throw 'WRITE_STOPPED already exists; refusing to write after stop.'
}

$validationPath = Join-Path $recordRoot 'machine_manual_recordset_validation.json'
$validation = Get-Content -LiteralPath $validationPath -Raw | ConvertFrom-Json
if (@($validation.failed_checks).Count -ne 0) {
    throw 'Machine recordset validation has failed checks.'
}
if ([int]$validation.manual_non_pass_total -ne 0) {
    throw 'Machine recordset validation reports non-PASS manual rows.'
}
if ([int]$validation.counts.actual_render_files -ne 717 -or [int]$validation.counts.covered_unique_render_files -ne 717) {
    throw 'Render-file coverage is not exactly 717/717.'
}

$decision = Get-Content -LiteralPath (Join-Path $recordRoot 'SA3_DECISION.json') -Raw | ConvertFrom-Json
if ($decision.decision -ne 'PASS' -or $decision.workflow_state -ne 'C_LOCAL_PASS_ONLY') {
    throw 'SA3 manual decision is not the expected local PASS state.'
}

$allPresealFiles = @(Get-ChildItem -LiteralPath $recordRoot -Recurse -File -Force)
$alternateStreams = @(
    $allPresealFiles | ForEach-Object {
        Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue |
            Where-Object Stream -ne ':$DATA'
    }
)
$cacheDirs = @(Get-ChildItem -LiteralPath $recordRoot -Recurse -Directory -Force | Where-Object Name -eq '__pycache__')
$pycFiles = @($allPresealFiles | Where-Object Extension -eq '.pyc')
if ($alternateStreams.Count -ne 0 -or $cacheDirs.Count -ne 0 -or $pycFiles.Count -ne 0) {
    throw 'Preseal cleanliness gate failed: ADS/cache/pyc is nonzero.'
}

$invariant = [System.Globalization.CultureInfo]::InvariantCulture
$entries = @(
    $allPresealFiles |
        Where-Object { $_.FullName -ne $manifestPath -and $_.FullName -ne $markerPath } |
        Sort-Object FullName |
        ForEach-Object {
            $relative = $_.FullName.Substring($recordRoot.Length).TrimStart([char[]]@('\', '/')).Replace('\', '/')
            [ordered]@{
                path = $relative
                bytes = [int64]$_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                mtime_utc = $_.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', $invariant)
                ntfs_100ns = [string]$_.LastWriteTimeUtc.ToFileTimeUtc()
            }
        }
)

$manifest = [ordered]@{
    schema = 'SA3_STRICT_MANIFEST_V1'
    handoff_id = 'C-FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1'
    recordset_id = 'FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1-RECORDSET-01'
    decision = 'PASS'
    workflow_state = 'C_LOCAL_PASS_ONLY'
    manifest_self_excluded = $true
    write_stopped_excluded = $true
    only_unlisted_files = @('MANIFEST.json', 'WRITE_STOPPED')
    listed_file_count = $entries.Count
    files = $entries
}

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$manifestJson = $manifest | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText($manifestPath, $manifestJson + "`n", $utf8NoBom)
$manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash.ToLowerInvariant()

$filesToLock = @(Get-ChildItem -LiteralPath $recordRoot -Recurse -File -Force)
foreach ($file in $filesToLock) {
    $file.IsReadOnly = $true
}

$sealUtc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ', $invariant)
$markerLines = @(
    'WRITE_STOPPED',
    'handoff_id=C-FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1',
    'recordset_id=FIG-P602-01-R103-SA3-FRESH-ISOLATED-V1-RECORDSET-01',
    'decision=PASS',
    'workflow_state=C_LOCAL_PASS_ONLY',
    "manifest_sha256=$manifestHash",
    "manifest_listed_files=$($entries.Count)",
    "sealed_utc=$sealUtc",
    'zero_writes_after_this_marker=true'
)

$temporaryMarker = [System.IO.Path]::Combine(
    [System.IO.Path]::GetTempPath(),
    'FIG-P602-01-' + [Guid]::NewGuid().ToString('N') + '.marker'
)
[System.IO.File]::WriteAllText($temporaryMarker, ($markerLines -join "`n") + "`n", $utf8NoBom)
[System.IO.File]::SetAttributes($temporaryMarker, [System.IO.FileAttributes]::ReadOnly)
Move-Item -LiteralPath $temporaryMarker -Destination $markerPath

Write-Output "SEALED manifest_sha256=$manifestHash listed_files=$($entries.Count)"
