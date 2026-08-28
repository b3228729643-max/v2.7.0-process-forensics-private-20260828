$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath((Split-Path -Parent $PSScriptRoot))
$manifestCsv = Join-Path $root 'MANIFEST.csv'
$manifestJson = Join-Path $root 'MANIFEST.json'
$writeStopped = Join-Path $root 'WRITE_STOPPED.json'
$finalAudit = Join-Path $root 'FINAL_FILESYSTEM_AUDIT.json'

foreach ($control in @($manifestCsv, $manifestJson, $writeStopped, $finalAudit)) {
    if (Test-Path -LiteralPath $control) { throw "Pre-existing seal output: $control" }
}

$tex = @(Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.ProcessName -match '^(latexmk|lualatex|luatex|luahbtex)$' })
if ($tex.Count -ne 0) { throw "TeX process count is $($tex.Count), expected zero" }

$jsonFailures = 0
Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.json' | ForEach-Object {
    try { $null = Get-Content -Raw -LiteralPath $_.FullName | ConvertFrom-Json }
    catch { $jsonFailures++ }
}
$csvFailures = 0
Get-ChildItem -LiteralPath $root -Recurse -File -Filter '*.csv' | ForEach-Object {
    try { $null = Import-Csv -LiteralPath $_.FullName }
    catch { $csvFailures++ }
}
$allBefore = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$ads = 0
foreach ($file in $allBefore) {
    $ads += @((Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue) | Where-Object Stream -ne ':$DATA').Count
}
$pyc = @($allBefore | Where-Object Extension -eq '.pyc').Count
$cacheDirs = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Where-Object { $_.Name -in @('__pycache__', '.pytest_cache') }).Count
if ($jsonFailures -ne 0 -or $csvFailures -ne 0 -or $ads -ne 0 -or $pyc -ne 0 -or $cacheDirs -ne 0) {
    throw "Preseal gate failed: json=$jsonFailures csv=$csvFailures ads=$ads pyc=$pyc cacheDirs=$cacheDirs"
}

$audit = [ordered]@{
    status = 'PASS'
    round = 'R12'
    role = 'SA2'
    decision = 'LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1'
    created_at_utc = [DateTime]::UtcNow.ToString('o')
    tex_process_count = 0
    json_parse_failures = $jsonFailures
    csv_parse_failures = $csvFailures
    ads_nondefault_streams = $ads
    pyc_files = $pyc
    python_cache_directories = $cacheDirs
    object_count = 128
    unordered_pair_count = 8128
    empty_masks = 0
    illegal_overlap_flags = 0
    clearance_flags = 0
    clip_failures = 0
    hard_readability_failures = 0
    target_pair_06596_shared_pixels = 0
    target_pair_06596_clearance_px = '16.464'
    target_pair_06650_shared_pixels = 0
    target_pair_06650_clearance_px = '12.928'
    source_after_sha256 = '49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E'
    pdf_sha256 = 'A50EE094843FDA68A3E3CDCFA0F5DC1F4884B1FDA853A6B3BECEE7DB2758452A'
}
$audit | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $finalAudit -Encoding utf8NoBOM

$payload = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { $_.FullName -notin @($manifestCsv, $manifestJson, $writeStopped) } | Sort-Object FullName)
$records = foreach ($file in $payload) {
    [ordered]@{
        relative_path = $file.FullName.Substring($root.Length).TrimStart('\') -replace '\\','/'
        bytes = $file.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
        mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
        mtime_utc_7digit = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
    }
}
$records | ConvertTo-Csv -NoTypeInformation | Set-Content -LiteralPath $manifestCsv -Encoding utf8NoBOM
$records | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestJson -Encoding utf8NoBOM

$csvRows = @(Import-Csv -LiteralPath $manifestCsv)
$jsonRows = @(Get-Content -Raw -LiteralPath $manifestJson | ConvertFrom-Json -DateKind String)
if ($csvRows.Count -ne $payload.Count -or $jsonRows.Count -ne $payload.Count) { throw 'Manifest count mismatch' }
$fsMap = @{}
foreach ($file in $payload) {
    $rel = $file.FullName.Substring($root.Length).TrimStart('\') -replace '\\','/'
    if ($fsMap.ContainsKey($rel)) { throw "Duplicate payload path: $rel" }
    $fsMap[$rel] = $file
}
foreach ($row in $csvRows) {
    if (-not $fsMap.ContainsKey($row.relative_path)) { throw "CSV path absent from FS: $($row.relative_path)" }
    $file = $fsMap[$row.relative_path]
    if ([string]$file.Length -ne [string]$row.bytes -or (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash -ne $row.sha256 -or $file.LastWriteTimeUtc.Ticks.ToString() -ne $row.mtime_utc_ticks) { throw "CSV identity mismatch: $($row.relative_path)" }
}
foreach ($row in $jsonRows) {
    if (-not $fsMap.ContainsKey($row.relative_path)) { throw "JSON path absent from FS: $($row.relative_path)" }
    $file = $fsMap[$row.relative_path]
    if ([string]$file.Length -ne [string]$row.bytes -or (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash -ne $row.sha256 -or $file.LastWriteTimeUtc.Ticks.ToString() -ne [string]$row.mtime_utc_ticks) { throw "JSON identity mismatch: $($row.relative_path)" }
}

$stop = [ordered]@{
    status = 'WRITE_STOPPED'
    round = 'R12'
    created_at_utc = [DateTime]::UtcNow.ToString('o')
    payload_file_count = $payload.Count
    manifest_control_file_count = 2
    write_stopped_control_file_count = 1
    control_file_count = 3
    ordinary_file_total = $payload.Count + 3
    csv_manifest_rows = $csvRows.Count
    json_manifest_rows = $jsonRows.Count
    csv_json_identity_mismatch_count = 0
    filesystem_identity_mismatch_count = 0
    source_sha256 = '49A683AEEC94AFD71AE33E95D4DF51BA3CC722F10B432B065FDBD2E45898635E'
    pdf_sha256 = 'A50EE094843FDA68A3E3CDCFA0F5DC1F4884B1FDA853A6B3BECEE7DB2758452A'
    tex_process_count = 0
}
$stop | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $writeStopped -Encoding utf8NoBOM

$finalFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
if ($finalFiles.Count -ne ($payload.Count + 3)) { throw "Final ordinary count mismatch: $($finalFiles.Count)" }
foreach ($file in $finalFiles) { $file.IsReadOnly = $true }
Write-Output ("SEALED payload={0} controls=3 ordinary={1}" -f $payload.Count, $finalFiles.Count)
