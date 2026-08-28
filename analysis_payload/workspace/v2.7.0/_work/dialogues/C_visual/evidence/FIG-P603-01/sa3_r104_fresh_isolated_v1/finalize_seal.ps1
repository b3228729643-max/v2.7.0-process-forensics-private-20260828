$ErrorActionPreference = 'Stop'
$ExpectedRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P603-01\sa3_r104_fresh_isolated_v1'
$Root = [System.IO.Path]::GetFullPath((Split-Path -Parent $MyInvocation.MyCommand.Path))
if ($Root -ne $ExpectedRoot) {
    throw "Unexpected seal root: $Root"
}

$ManifestPath = Join-Path $Root 'MANIFEST.csv'
$ManifestTempPath = Join-Path $Root 'MANIFEST.csv.tmp'
$MarkerPath = Join-Path $Root 'WRITE_STOPPED'
if (Test-Path -LiteralPath $ManifestPath) { throw 'MANIFEST.csv already exists' }
if (Test-Path -LiteralPath $ManifestTempPath) { throw 'MANIFEST.csv.tmp already exists' }
if (Test-Path -LiteralPath $MarkerPath) { throw 'WRITE_STOPPED already exists' }

$Required = @(
    'IDENTITY.json',
    'REPORT.md',
    'RESULT_CARD.json',
    'RESULT_CARD.md',
    'after_visual_acceptance.md',
    'after_font_audit.csv',
    'after_pixel_measurements.csv',
    'after_overlap_report.csv',
    'after_text_measurement_overlay_300dpi.png',
    'full_page_200dpi.png',
    'full_page_300dpi.png',
    'figure_crop_300dpi.png',
    'standalone_300dpi.png',
    'grayscale_300dpi.png',
    'standalone_grayscale_300dpi.png',
    'machine_object_inventory.csv',
    'machine_all_pairs.csv',
    'machine_clip_inventory.csv',
    'machine_terminal_check.json',
    'manual_glyph_review.csv',
    'manual_graphic_review.csv',
    'manual_pair_review.csv',
    'manual_peer_role_review.csv',
    'manual_clip_boundary_review.csv',
    'manual_hard_gate_review.csv'
)
foreach ($Relative in $Required) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root $Relative) -PathType Leaf)) {
        throw "Required evidence file missing: $Relative"
    }
}

$Terminal = Get-Content -LiteralPath (Join-Path $Root 'machine_terminal_check.json') -Raw | ConvertFrom-Json
if (-not $Terminal.terminal_machine_checks_pass) { throw 'Terminal machine checks are not PASS' }
$Result = Get-Content -LiteralPath (Join-Path $Root 'RESULT_CARD.json') -Raw | ConvertFrom-Json
if ($Result.decision -ne 'PASS' -or $Result.authority -ne 'C_LOCAL_PASS_ONLY' -or $Result.next_state -ne 'WAIT_MAINLINE' -or $Result.global_pass_claimed) {
    throw 'Result card authority/status is not the expected local-only disposition'
}

$CacheEntries = @(Get-ChildItem -LiteralPath $Root -Recurse -Force | Where-Object {
    $_.Name -eq '__pycache__' -or $_.Extension -eq '.pyc' -or $_.Extension -eq '.pyo'
})
if ($CacheEntries.Count -ne 0) { throw 'cache/pyc/pyo entries found' }

$AdsEntries = @()
Get-ChildItem -LiteralPath $Root -Recurse -File -Force | ForEach-Object {
    Get-Item -LiteralPath $_.FullName -Stream * | Where-Object {
        $_.Stream -ne ':$DATA' -and $_.Stream -ne '$DATA'
    } | ForEach-Object { $script:AdsEntries += $_ }
}
if ($AdsEntries.Count -ne 0) { throw 'NTFS alternate data streams found' }

$ManualFiles = @(Get-ChildItem -LiteralPath $Root -File -Filter 'manual_*.csv')
foreach ($ManualFile in $ManualFiles) {
    $Rows = @(Import-Csv -LiteralPath $ManualFile.FullName)
    if ($Rows.Count -eq 0) { throw "Empty manual ledger: $($ManualFile.Name)" }
    foreach ($Row in $Rows) {
        if ($Row.reviewer -ne 'SA3') { throw "Missing/wrong reviewer in $($ManualFile.Name)" }
        if ($Row.PSObject.Properties.Name -contains 'note') {
            if ([string]::IsNullOrWhiteSpace($Row.note)) { throw "Blank manual note in $($ManualFile.Name)" }
        }
        if ($Row.PSObject.Properties.Name -contains 'decision') {
            if ($Row.decision -match 'FAIL|PENDING|UNKNOWN' -or [string]::IsNullOrWhiteSpace($Row.decision)) {
                throw "Unresolved manual decision in $($ManualFile.Name)"
            }
        }
    }
}

$ContentFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Sort-Object FullName)
if ($ContentFiles.Count -ne 451) { throw "Unexpected pre-manifest content file count: $($ContentFiles.Count)" }

$ManifestRows = foreach ($File in $ContentFiles) {
    if ($File.FullName -eq $ManifestPath -or $File.FullName -eq $ManifestTempPath -or $File.FullName -eq $MarkerPath) {
        throw "Manifest or marker entered pre-manifest content list: $($File.FullName)"
    }
    [PSCustomObject]@{
        resolved_path = [System.IO.Path]::GetFullPath($File.FullName)
        bytes = [Int64]$File.Length
        SHA256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
        UTC_mtime = $File.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
        FILETIME100ns = [Int64]$File.LastWriteTimeUtc.ToFileTimeUtc()
    }
}

$ManifestRows | Export-Csv -LiteralPath $ManifestTempPath -NoTypeInformation -Encoding UTF8
$LoadedManifest = @(Import-Csv -LiteralPath $ManifestTempPath)
if ($LoadedManifest.Count -ne $ContentFiles.Count) { throw 'Manifest row count mismatch' }
if (@($LoadedManifest | Where-Object { $_.resolved_path -eq $ManifestPath -or $_.resolved_path -eq $MarkerPath }).Count -ne 0) {
    throw 'Manifest improperly lists itself or marker'
}
for ($Index = 0; $Index -lt $LoadedManifest.Count; $Index++) {
    $Row = $LoadedManifest[$Index]
    $File = Get-Item -LiteralPath $Row.resolved_path
    if ([Int64]$Row.bytes -ne [Int64]$File.Length) { throw "Manifest byte mismatch: $($Row.resolved_path)" }
    if ($Row.SHA256 -ne (Get-FileHash -LiteralPath $Row.resolved_path -Algorithm SHA256).Hash.ToUpperInvariant()) { throw "Manifest hash mismatch: $($Row.resolved_path)" }
    if ([Int64]$Row.FILETIME100ns -ne [Int64]$File.LastWriteTimeUtc.ToFileTimeUtc()) { throw "Manifest FILETIME mismatch: $($Row.resolved_path)" }
}
Move-Item -LiteralPath $ManifestTempPath -Destination $ManifestPath

$AllPreMarkerFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)
foreach ($File in $AllPreMarkerFiles) {
    Set-ItemProperty -LiteralPath $File.FullName -Name IsReadOnly -Value $true
}

$SealUtc = [DateTime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
$MarkerLines = @(
    'HANDOFF_ID=C-FIG-P603-01-R104-SA3-FRESH-ISOLATED-V1',
    'UID=FIG-P603-01',
    'ROLE=SA3',
    'RESULT=PASS',
    'AUTHORITY=C_LOCAL_PASS_ONLY',
    'NEXT_STATE=WAIT_MAINLINE',
    'GLOBAL_PASS_CLAIMED=NO',
    'TEX_EXECUTION=DISABLED',
    'SOURCE_WRITER=NONE',
    'MANIFEST=MANIFEST.csv',
    "MANIFEST_CONTENT_ROWS=$($ContentFiles.Count)",
    'ADS_COUNT=0',
    'CACHE_PYC_COUNT=0',
    "SEALED_UTC=$SealUtc",
    'POST_SEAL_WRITES=PROHIBITED'
)
Set-Content -LiteralPath $MarkerPath -Value $MarkerLines -Encoding UTF8
Set-ItemProperty -LiteralPath $MarkerPath -Name IsReadOnly -Value $true

Write-Output "SEALED_ROOT=$Root"
Write-Output "MANIFEST_CONTENT_ROWS=$($ContentFiles.Count)"
Write-Output "SEALED_UTC=$SealUtc"
