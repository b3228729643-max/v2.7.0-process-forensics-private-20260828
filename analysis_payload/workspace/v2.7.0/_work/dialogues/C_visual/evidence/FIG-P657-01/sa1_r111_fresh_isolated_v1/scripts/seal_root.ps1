$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P657-01\sa1_r111_fresh_isolated_v1'
$manifestPath = Join-Path $root 'MANIFEST.tsv'
$auditPath = Join-Path $root 'SEAL_AUDIT.json'
$markerPath = Join-Path $root 'WRITE_STOPPED'

if (Test-Path -LiteralPath $markerPath) {
    throw 'WRITE_STOPPED already exists; refusing a second seal.'
}

$required = @(
    'EVIDENCE_INDEX.md',
    'raw\page706_full_page_200dpi.png',
    'raw\page706_native300dpi.png',
    'raw\figure_with_caption_native300dpi.png',
    'raw\standalone_figure_native300dpi.png',
    'raw\standalone_figure_grayscale300dpi.png',
    'review\after_pixel_measurements.csv',
    'review\object_pair_manual_ledger.csv',
    'review\after_overlap_adjudication.md',
    'review\after_visual_acceptance.md'
)
$missing = @()
foreach ($relativeRequired in $required) {
    $requiredPath = Join-Path $root $relativeRequired
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        $missing += $relativeRequired
    }
}
if ($missing.Count -ne 0) {
    throw "Missing required payload: $($missing -join ', ')"
}

$csvFiles = Get-ChildItem -LiteralPath (Join-Path $root 'review') -File -Filter '*.csv'
$parseErrors = @()
foreach ($file in $csvFiles) {
    try {
        $null = Import-Csv -LiteralPath $file.FullName
    } catch {
        $parseErrors += $file.FullName
    }
}
try {
    $null = Get-Content -LiteralPath (Join-Path $root 'review\automated_measurement_summary.json') -Raw | ConvertFrom-Json
} catch {
    $parseErrors += 'review\automated_measurement_summary.json'
}
if ($parseErrors.Count -ne 0) {
    throw "Parse errors: $($parseErrors -join ', ')"
}

$pixelRows = @(Import-Csv -LiteralPath (Join-Path $root 'review\after_pixel_measurements.csv'))
$pairRows = @(Import-Csv -LiteralPath (Join-Path $root 'review\object_pair_manual_ledger.csv'))
$objectRows = @(Import-Csv -LiteralPath (Join-Path $root 'review\visible_object_denominator_raw.csv'))
if ($pixelRows.Count -ne 25 -or @($pixelRows | Where-Object PASS_FAIL -ne 'PASS').Count -ne 0) {
    throw 'Pixel manual ledger is not closed at 25 PASS rows.'
}
if ($pairRows.Count -ne 190 -or @($pairRows | Where-Object { $_.manual_decision -notin @('CLEAR','LEGAL_ATTACHMENT','CLEAR_BBOX_FALSE_POSITIVE') }).Count -ne 0) {
    throw 'Pair manual ledger is not closed at 190 decided rows.'
}
if ($objectRows.Count -ne 20) {
    throw 'Visible-object denominator is not 20.'
}

$allItems = @(Get-ChildItem -LiteralPath $root -Force -Recurse)
$cacheItems = @($allItems | Where-Object {
    $_.Name -in @('__pycache__','.pytest_cache','.cache') -or $_.Extension -in @('.pyc','.pyo')
})
$reparseItems = @($allItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 })

$adsItems = @()
foreach ($file in @($allItems | Where-Object { -not $_.PSIsContainer })) {
    try {
        $adsItems += @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object Stream -ne ':$DATA')
    } catch {
        throw "ADS inspection failed for $($file.FullName): $($_.Exception.Message)"
    }
}
if ($cacheItems.Count -ne 0 -or $reparseItems.Count -ne 0 -or $adsItems.Count -ne 0) {
    throw "Preseal hygiene failure: cache/pyc=$($cacheItems.Count), reparse=$($reparseItems.Count), ADS=$($adsItems.Count)"
}

$sourcePdf = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r111_fullbook\main_full.pdf'
$sourceTex = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C05\fig_v5_c05_distribution_relations.tex'
$pdfInfo = Get-Item -LiteralPath $sourcePdf
$texInfo = Get-Item -LiteralPath $sourceTex
$pdfHash = (Get-FileHash -LiteralPath $sourcePdf -Algorithm SHA256).Hash
$texHash = (Get-FileHash -LiteralPath $sourceTex -Algorithm SHA256).Hash
if ($pdfInfo.Length -ne 4967076 -or $pdfHash -ne 'DAB1062500E39DD2C34C6B4A9FF51CAC2BE0A4C84B2F45F5FB8E645C4BC012D6') {
    throw 'Official R111 PDF identity drifted before seal.'
}
if ($texInfo.Length -ne 2927 -or $texHash -ne 'B2B3A8748133B55169F08A543DF39E238E2FB3DFFF67EA0067C543CD9FDE31D2') {
    throw 'Current source identity drifted before seal.'
}

$audit = [ordered]@{
    schema = 'FIG_SA1_SEAL_AUDIT_V1'
    handoff_id = 'C-FIG-P657-01-R111-SA1-FRESH-ISOLATED-V1'
    figure_id = 'FIG-P657-01'
    result = 'PASS'
    disposition = 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
    official_pdf_bytes = [int64]$pdfInfo.Length
    official_pdf_sha256 = $pdfHash
    source_bytes = [int64]$texInfo.Length
    source_sha256 = $texHash
    object_count = $objectRows.Count
    unordered_pair_count = $pairRows.Count
    pixel_manual_row_count = $pixelRows.Count
    parse_error_count = $parseErrors.Count
    ads_count = $adsItems.Count
    cache_pyc_count = $cacheItems.Count
    reparse_point_count = $reparseItems.Count
    text_graphics_overlap_pixel_count = 0
    maximum_independent_text_pair_overlap_pixel_count = 0
    clip_pixel_count = 0
    manifest_scope = 'all regular root files existing before MANIFEST.tsv and WRITE_STOPPED; MANIFEST.tsv and WRITE_STOPPED are necessarily self/last-marker exclusions'
}
$audit | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $auditPath -Encoding utf8

$payloadFiles = @(Get-ChildItem -LiteralPath $root -File -Force -Recurse | Where-Object {
    $_.FullName -ne $manifestPath -and $_.FullName -ne $markerPath
} | Sort-Object FullName)

$manifestLines = [System.Collections.Generic.List[string]]::new()
$manifestLines.Add("relative_path`tbytes`tsha256`tcreation_time_utc_ticks`tlast_write_time_utc_ticks")
foreach ($file in $payloadFiles) {
    $relative = $file.FullName.Substring($root.Length + 1)
    $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    $manifestLines.Add("$relative`t$($file.Length)`t$hash`t$($file.CreationTimeUtc.Ticks)`t$($file.LastWriteTimeUtc.Ticks)")
}
$manifestLines | Set-Content -LiteralPath $manifestPath -Encoding utf8

Start-Sleep -Milliseconds 150

$filesBeforeMarker = @(Get-ChildItem -LiteralPath $root -File -Force -Recurse)
foreach ($file in $filesBeforeMarker) {
    $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly
}
$dirsDeepFirst = @(Get-ChildItem -LiteralPath $root -Directory -Force -Recurse | Sort-Object FullName -Descending)
foreach ($dir in $dirsDeepFirst) {
    $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly
}
(Get-Item -LiteralPath $root).Attributes = (Get-Item -LiteralPath $root).Attributes -bor [IO.FileAttributes]::ReadOnly

$markerText = @(
    'WRITE_STOPPED',
    'HANDOFF_ID=C-FIG-P657-01-R111-SA1-FRESH-ISOLATED-V1',
    'RESULT=PASS',
    'DISPOSITION=SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3',
    'POSTSEAL_ROOT_WRITES=FORBIDDEN'
) -join "`r`n"
[IO.File]::WriteAllText($markerPath, $markerText, [Text.UTF8Encoding]::new($false))
(Get-Item -LiteralPath $markerPath).Attributes = (Get-Item -LiteralPath $markerPath).Attributes -bor [IO.FileAttributes]::ReadOnly
(Get-Item -LiteralPath $root).Attributes = (Get-Item -LiteralPath $root).Attributes -bor [IO.FileAttributes]::ReadOnly

$marker = Get-Item -LiteralPath $markerPath
$postMarker = @(Get-ChildItem -LiteralPath $root -File -Force -Recurse | Where-Object {
    $_.FullName -ne $markerPath -and $_.LastWriteTimeUtc.Ticks -gt $marker.LastWriteTimeUtc.Ticks
})
$notReadOnlyFiles = @(Get-ChildItem -LiteralPath $root -File -Force -Recurse | Where-Object {
    ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0
})
$notReadOnlyDirs = @((Get-Item -LiteralPath $root) + @(Get-ChildItem -LiteralPath $root -Directory -Force -Recurse) | Where-Object {
    ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0
})

if ($postMarker.Count -ne 0 -or $notReadOnlyFiles.Count -ne 0 -or $notReadOnlyDirs.Count -ne 0) {
    throw "Postseal invariant failure: postmarker=$($postMarker.Count), writable_files=$($notReadOnlyFiles.Count), writable_dirs=$($notReadOnlyDirs.Count)"
}

Write-Output "SEALED_ROOT=$root"
Write-Output "MANIFEST_ROWS=$($payloadFiles.Count)"
Write-Output "MARKER_LAST_WRITE_UTC_TICKS=$($marker.LastWriteTimeUtc.Ticks)"
Write-Output "POSTMARKER0=$($postMarker.Count)"
Write-Output "READONLY_FILES_MISSING=$($notReadOnlyFiles.Count)"
Write-Output "READONLY_DIRS_MISSING=$($notReadOnlyDirs.Count)"
Write-Output "PARSE_ERRORS=$($parseErrors.Count) ADS=$($adsItems.Count) CACHE_PYC=$($cacheItems.Count) REPARSE=$($reparseItems.Count)"
