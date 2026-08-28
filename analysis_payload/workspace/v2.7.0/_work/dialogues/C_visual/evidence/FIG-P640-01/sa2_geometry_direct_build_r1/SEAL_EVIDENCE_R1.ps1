param()

$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($PSScriptRoot)
$Manifest = [IO.Path]::Combine($Root, 'MANIFEST.csv')
$Marker = [IO.Path]::Combine($Root, 'WRITE_STOPPED.json')

if ([IO.File]::Exists($Manifest) -or [IO.File]::Exists($Marker)) {
    throw 'seal outputs already exist; immutable rerun refused'
}

$cacheNames = @('__pycache__', '.pytest_cache', '.mypy_cache')
$cacheDirs = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Where-Object { $_.Name -in $cacheNames })
$pycFiles = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Where-Object { $_.Extension -in @('.pyc', '.pyo') })
if ($cacheDirs.Count -ne 0 -or $pycFiles.Count -ne 0) {
    throw "cache artifacts present: dirs=$($cacheDirs.Count), pyc=$($pycFiles.Count)"
}

$payloadFiles = @(
    Get-ChildItem -LiteralPath $Root -File -Recurse -Force |
        Where-Object { $_.FullName -ne $Manifest -and $_.FullName -ne $Marker } |
        Sort-Object FullName
)

$ads = @()
foreach ($file in $payloadFiles) {
    $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop | Where-Object { $_.Stream -ne ':$DATA' })
    foreach ($stream in $streams) {
        $ads += "$($file.FullName):$($stream.Stream)"
    }
}
if ($ads.Count -ne 0) {
    throw "alternate data streams present: $($ads -join '; ')"
}

$rows = @()
foreach ($file in $payloadFiles) {
    $relative = [IO.Path]::GetRelativePath($Root, $file.FullName).Replace('\', '/')
    $rows += [pscustomobject]@{
        path = $relative
        resolved_path = [IO.Path]::GetFullPath($file.FullName)
        bytes = $file.Length
        sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
        mtime_utc = $file.LastWriteTimeUtc.ToString('o')
        mtime_filetime_100ns = $file.LastWriteTimeUtc.ToFileTimeUtc()
    }
}

$rows | Export-Csv -LiteralPath $Manifest -NoTypeInformation -Encoding utf8NoBOM
$manifestItem = Get-Item -LiteralPath $Manifest -Force
$manifestHash = (Get-FileHash -LiteralPath $Manifest -Algorithm SHA256).Hash.ToUpperInvariant()

$recordLines = @($rows | ForEach-Object { "$($_.path)|$($_.bytes)|$($_.sha256)|$($_.mtime_filetime_100ns)" })
$recordBytes = [Text.Encoding]::UTF8.GetBytes(($recordLines -join "`n"))
$sha = [Security.Cryptography.SHA256]::Create()
try {
    $recordsetHash = ([Convert]::ToHexString($sha.ComputeHash($recordBytes))).ToUpperInvariant()
} finally {
    $sha.Dispose()
}

foreach ($file in $payloadFiles) {
    $file.IsReadOnly = $true
}
$manifestItem.IsReadOnly = $true

$readOnlyFailures = @()
foreach ($path in @($payloadFiles.FullName) + @($Manifest)) {
    if (-not (Get-Item -LiteralPath $path -Force).IsReadOnly) {
        $readOnlyFailures += $path
    }
}
if ($readOnlyFailures.Count -ne 0) {
    throw "read-only freeze failed: $($readOnlyFailures -join '; ')"
}

$markerData = [ordered]@{
    handoff_id = 'C-FIG-P640-01-SA2-GEOMETRY-DIRECT-BUILD-R1'
    uid = 'FIG-P640-01'
    role = 'SA2'
    result = 'FAIL_TO_SA2'
    local_pass_claimed = $false
    write_stopped_utc = [DateTime]::UtcNow.ToString('o')
    payload_file_count = $payloadFiles.Count
    control_file_count = 1
    seal_file_count = 1
    expected_ordinary_file_count = $payloadFiles.Count + 2
    manifest_listed_file_count = $rows.Count
    manifest_self_excluded = $true
    write_stopped_self_excluded = $true
    manifest_bytes = $manifestItem.Length
    manifest_sha256 = $manifestHash
    canonical_payload_recordset_sha256 = $recordsetHash
    payload_and_manifest_readonly = $true
    write_stopped_readonly_boundary = 'EXCLUDED_MARKER_ARCHIVE'
    ads_count = 0
    pyc_or_cache_count = 0
    machine_denominators = [ordered]@{
        objects = 40
        glyphs_including_spaces = 160
        glyphs_nonspace = 145
        unordered_pairs = 780
        critical_pairs = 76
        clips = 40
    }
    manual_decisions = [ordered]@{
        objects_pass = 40
        glyph_groups_pass = 9
        critical_pairs_pass = 75
        critical_pairs_fail = 1
        hard_failure_pair = 'PAIR_0779'
    }
    tex_invocation_count = 1
    tex_retry_count = 0
    post_tex_process_count = 0
    source_sha256 = 'FFAE906011BBAD21FD1AD53997693934828394C2AE516649CCCF8DA5938D9B89'
    wrapper_sha256 = '495C5D0D36BE60B82BDB44AF4E352960680416785F991F8F0A15F0E495ABDC5C'
    pdf_sha256 = '0ECC4B13E75A981AD23E7EBCA1CB2BAEBEF83D85EEE3A4518395C54AC296B87A'
    next_role = 'SA2'
    tex_retry_authorized = $false
    source_commit_authorized = $false
    central_state_or_inventory_written = $false
}

$json = $markerData | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($Marker, $json + "`n", [Text.UTF8Encoding]::new($false))
[IO.File]::SetAttributes($Marker, [IO.FileAttributes]::Archive)
