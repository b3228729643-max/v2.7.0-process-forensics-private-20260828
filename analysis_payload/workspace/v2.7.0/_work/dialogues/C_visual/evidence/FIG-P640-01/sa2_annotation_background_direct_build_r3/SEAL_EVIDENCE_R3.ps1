param()

$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($PSScriptRoot)
$Manifest = [IO.Path]::Combine($Root, 'MANIFEST.csv')
$Marker = [IO.Path]::Combine($Root, 'WRITE_STOPPED.json')

if ([IO.File]::Exists($Manifest) -or [IO.File]::Exists($Marker)) {
    throw 'seal outputs already exist; immutable rerun refused'
}

$cacheDirs = @(Get-ChildItem -LiteralPath $Root -Directory -Recurse -Force | Where-Object { $_.Name -in @('__pycache__', '.pytest_cache', '.mypy_cache') })
$bytecode = @(Get-ChildItem -LiteralPath $Root -File -Recurse -Force | Where-Object { $_.Extension -in @('.pyc', '.pyo') })
if ($cacheDirs.Count -ne 0 -or $bytecode.Count -ne 0) {
    throw "R3 cache artifacts present: dirs=$($cacheDirs.Count), bytecode=$($bytecode.Count)"
}

$payload = @(
    Get-ChildItem -LiteralPath $Root -File -Recurse -Force |
        Where-Object { $_.FullName -ne $Manifest -and $_.FullName -ne $Marker } |
        Sort-Object FullName
)

$ads = @()
foreach ($file in $payload) {
    $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop | Where-Object { $_.Stream -ne ':$DATA' })
    foreach ($stream in $streams) { $ads += "$($file.FullName):$($stream.Stream)" }
}
if ($ads.Count -ne 0) { throw "R3 alternate data streams present: $($ads -join '; ')" }

$rows = @()
foreach ($file in $payload) {
    $rows += [pscustomobject]@{
        path = [IO.Path]::GetRelativePath($Root, $file.FullName).Replace('\', '/')
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
try { $recordsetHash = ([Convert]::ToHexString($sha.ComputeHash($recordBytes))).ToUpperInvariant() } finally { $sha.Dispose() }

foreach ($file in $payload) { $file.IsReadOnly = $true }
$manifestItem.IsReadOnly = $true
$readOnlyFailures = @()
foreach ($path in @($payload.FullName) + @($Manifest)) {
    if (-not (Get-Item -LiteralPath $path -Force).IsReadOnly) { $readOnlyFailures += $path }
}
if ($readOnlyFailures.Count -ne 0) { throw "R3 read-only freeze failed: $($readOnlyFailures -join '; ')" }

$markerData = [ordered]@{
    handoff_id = 'C-FIG-P640-01-SA2-ANNOTATION-BACKGROUND-DIRECT-BUILD-R3'
    uid = 'FIG-P640-01'
    role = 'SA2'
    result = 'LOCAL_SA2_PASS_READY_FOR_MAIN'
    local_pass_claimed = $false
    main_acceptance_pending = $true
    write_stopped_utc = [DateTime]::UtcNow.ToString('o')
    payload_file_count = $payload.Count
    control_file_count = 1
    seal_file_count = 1
    expected_ordinary_file_count = $payload.Count + 2
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
        pdf_drawings = 20
    }
    manual_decisions = [ordered]@{
        objects_pass = 40
        glyph_groups_pass = 7
        critical_pairs_pass = 76
        hard_gates_pass = 15
        views_pass = 12
    }
    pair_0779 = [ordered]@{
        shared_pixels_native_300dpi = 0
        foreground_center_distance_px = 4
        orthogonal_blank_pixel_gap = 3
        required_blank_pixel_gap = 3
    }
    pair_0688 = [ordered]@{
        final_visible_curve_glyph_intersection = 0
        native_1x_pass = $true
        native_8x_pass = $true
        adjudication = 'VISIBLE_CURVE_LEFT_BELOW_FIRST_N_WITH_CLEAN_WHITE_SEPARATION'
    }
    hard_failure_count = 0
    new_regression_count = 0
    tex_invocation_count = 1
    tex_retry_count = 0
    post_tex_process_count = 0
    source_sha256 = 'A1CB852A7B433D3B3FB39EB4F4E0310FD1F76631F01F366AF9D4B1B1B2FF434B'
    wrapper_sha256 = '495C5D0D36BE60B82BDB44AF4E352960680416785F991F8F0A15F0E495ABDC5C'
    pdf_sha256 = 'E2AE5C0DACA6C9D07B43D61D00E9FA5580E63417DE15871D8DC6BA3842F9F2D2'
    next_action = 'WAIT_MAIN_REVIEW_OF_R3_LOCAL_SA2_PASS'
    tex_retry_authorized = $false
    source_commit_authorized = $false
    central_state_or_inventory_written = $false
}

$json = $markerData | ConvertTo-Json -Depth 8
[IO.File]::WriteAllText($Marker, $json + "`n", [Text.UTF8Encoding]::new($false))
[IO.File]::SetAttributes($Marker, [IO.FileAttributes]::Archive)
