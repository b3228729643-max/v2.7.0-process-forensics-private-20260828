$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R3A_SA2_COORDINATE_QUADRATIC_PATCH_R115_DIRECT_BUILD_20260828'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3A_WRITE_STOPPED_STAGE_20260828.tmp'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R3A_SEAL_CONTROLLER_RESULT_20260828.json'
$controlNames = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'SEAL_AUDIT.json', 'WRITE_STOPPED')
$handoffId = 'A-R115-P126-SA2-DIRECT-BUILD-R3A-20260828'
$verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
$pdfSha = '19F221487DB1930170608EAE0E09F019313791D808C724D05DBAC23465F746B2'
$sourceSha = '366C905854F0F3952225600D5BD66AAB706B637A453FD23DDF9611E4C002AC20'
$hardDefectId = 'HARD-LEGEND-GRAYSCALE-DASH-COLLAPSE'

function Get-RelativePath([string]$Base, [string]$FullName) {
    return [IO.Path]::GetRelativePath($Base, $FullName).Replace('\', '/')
}

function Get-FileIdentity([IO.FileInfo]$File, [string]$Base) {
    return [ordered]@{
        relative_path = Get-RelativePath $Base $File.FullName
        bytes = [int64]$File.Length
        sha256 = (Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
        creation_time_utc_ticks = [int64]$File.CreationTimeUtc.Ticks
        last_write_time_utc_ticks = [int64]$File.LastWriteTimeUtc.Ticks
    }
}

function Get-TreeSnapshot([string]$Base) {
    $rows = [System.Collections.Generic.List[string]]::new()
    $rootItem = Get-Item -LiteralPath $Base -Force
    $rows.Add(('D<TAB>.<TAB>{0}<TAB>{1}<TAB>{2}' -f $rootItem.CreationTimeUtc.Ticks, $rootItem.LastWriteTimeUtc.Ticks, [int]$rootItem.Attributes))
    foreach ($directory in @(Get-ChildItem -LiteralPath $Base -Directory -Recurse -Force | Sort-Object -Property FullName -CaseSensitive)) {
        $relative = Get-RelativePath $Base $directory.FullName
        $rows.Add(('D<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}' -f $relative, $directory.CreationTimeUtc.Ticks, $directory.LastWriteTimeUtc.Ticks, [int]$directory.Attributes))
    }
    foreach ($file in @(Get-ChildItem -LiteralPath $Base -File -Recurse -Force | Sort-Object -Property FullName -CaseSensitive)) {
        $relative = Get-RelativePath $Base $file.FullName
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToUpperInvariant()
        $rows.Add(('F<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}<TAB>{4}<TAB>{5}' -f $relative, $file.Length, $hash, $file.CreationTimeUtc.Ticks, $file.LastWriteTimeUtc.Ticks, [int]$file.Attributes))
    }
    $text = ($rows -join "`n") + "`n"
    $bytes = [Text.Encoding]::UTF8.GetBytes($text)
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

$started = [DateTime]::UtcNow
if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'R3A root is missing' }
if (Test-Path -LiteralPath $stage) { throw 'external WSTOP stage already exists' }
if (Test-Path -LiteralPath $resultPath) { throw 'controller result already exists' }
foreach ($name in $controlNames) {
    if (Test-Path -LiteralPath (Join-Path $root $name)) { throw "control already exists: $name" }
}

$payloadFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Sort-Object -Property FullName -CaseSensitive)
$payloadRows = @($payloadFiles | ForEach-Object { [pscustomobject](Get-FileIdentity $_ $root) })
if ($payloadRows.Count -ne 205) { throw "payload count mismatch: $($payloadRows.Count)" }
$duplicates = @($payloadRows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 })
if ($duplicates.Count -ne 0) { throw 'duplicate payload relative path' }

$csvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$jsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$auditPath = Join-Path $root 'SEAL_AUDIT.json'
$payloadRows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8NoBOM
@{
    schema = 'P126_R3A_PAYLOAD_MANIFEST_V1'
    handoff_id = $handoffId
    payload_count = $payloadRows.Count
    rows = $payloadRows
} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $jsonPath -Encoding utf8NoBOM

$csvRows = @(Import-Csv -LiteralPath $csvPath)
$jsonObject = Get-Content -LiteralPath $jsonPath -Raw -Encoding utf8 | ConvertFrom-Json
if ($csvRows.Count -ne $payloadRows.Count) { throw 'CSV manifest row count mismatch' }
if (@($jsonObject.rows).Count -ne $payloadRows.Count) { throw 'JSON manifest row count mismatch' }
foreach ($row in $payloadRows) {
    $destination = Join-Path $root $row.relative_path.Replace('/', '\')
    $item = Get-Item -LiteralPath $destination -Force
    if ($item.Length -ne [int64]$row.bytes) { throw "manifest byte mismatch: $($row.relative_path)" }
    if ((Get-FileHash -LiteralPath $destination -Algorithm SHA256).Hash.ToUpperInvariant() -ne $row.sha256) { throw "manifest SHA mismatch: $($row.relative_path)" }
    if ($item.CreationTimeUtc.Ticks -ne [int64]$row.creation_time_utc_ticks) { throw "manifest creation time mismatch: $($row.relative_path)" }
    if ($item.LastWriteTimeUtc.Ticks -ne [int64]$row.last_write_time_utc_ticks) { throw "manifest last-write mismatch: $($row.relative_path)" }
}

$presealAudit = [ordered]@{
    schema = 'P126_R3A_PREMARKER_SEAL_AUDIT_V1'
    handoff_id = $handoffId
    verdict = $verdict
    payload_count = $payloadRows.Count
    control_count_final = 4
    ordinary_count_final = $payloadRows.Count + 4
    csv_manifest_sha256 = (Get-FileHash -LiteralPath $csvPath -Algorithm SHA256).Hash.ToUpperInvariant()
    json_manifest_sha256 = (Get-FileHash -LiteralPath $jsonPath -Algorithm SHA256).Hash.ToUpperInvariant()
    pdf_sha256 = $pdfSha
    source_sha256 = $sourceSha
    hard_defect_id = $hardDefectId
    manual_fields_generated_by_script = 0
    premarker_identity_errors = 0
    prepared_utc = [DateTime]::UtcNow.ToString('o')
}
$presealAudit | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $auditPath -Encoding utf8NoBOM

$preMarkerFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
if ($preMarkerFiles.Count -ne ($payloadRows.Count + 3)) { throw "premarker file count mismatch: $($preMarkerFiles.Count)" }
foreach ($file in $preMarkerFiles) {
    [IO.File]::SetAttributes($file.FullName, ($file.Attributes -bor [IO.FileAttributes]::ReadOnly))
}
$directories = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending)
foreach ($directory in $directories) {
    [IO.File]::SetAttributes($directory.FullName, ($directory.Attributes -bor [IO.FileAttributes]::ReadOnly))
}
$rootItem = Get-Item -LiteralPath $root -Force
[IO.File]::SetAttributes($rootItem.FullName, ($rootItem.Attributes -bor [IO.FileAttributes]::ReadOnly))

$premarkerNotReadonlyFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$premarkerNotReadonlyDirs = @(@(Get-Item -LiteralPath $root -Force) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force) | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($premarkerNotReadonlyFiles.Count -ne 0) { throw 'premarker writable file remains' }
if ($premarkerNotReadonlyDirs.Count -ne 0) { throw 'premarker writable directory remains' }

$allPreMarkerItems = @(@(Get-Item -LiteralPath $root -Force) + @(Get-ChildItem -LiteralPath $root -Recurse -Force))
$maxTicks = ($allPreMarkerItems | Measure-Object -Property @{ Expression = { $_.LastWriteTimeUtc.Ticks } } -Maximum).Maximum
$future = [DateTime]::UtcNow.AddMinutes(10)
if ($future.Ticks -le [int64]$maxTicks) { $future = [DateTime]::new(([int64]$maxTicks + [TimeSpan]::FromMinutes(5).Ticks), [DateTimeKind]::Utc) }

$manifestCsvSha = (Get-FileHash -LiteralPath $csvPath -Algorithm SHA256).Hash.ToUpperInvariant()
$manifestJsonSha = (Get-FileHash -LiteralPath $jsonPath -Algorithm SHA256).Hash.ToUpperInvariant()
$sealAuditSha = (Get-FileHash -LiteralPath $auditPath -Algorithm SHA256).Hash.ToUpperInvariant()
$markerLines = @(
    "HANDOFF_ID=$handoffId",
    'OPERATION=P126_R3A_POST_BUILD_NON_TEX_SINGLE_SEAL',
    "VERDICT=$verdict",
    "ROOT=$root",
    "PAYLOAD_COUNT=$($payloadRows.Count)",
    'CONTROL_COUNT=4',
    "ORDINARY_COUNT=$($payloadRows.Count + 4)",
    "PAYLOAD_MANIFEST_CSV_SHA256=$manifestCsvSha",
    "PAYLOAD_MANIFEST_JSON_SHA256=$manifestJsonSha",
    "SEAL_AUDIT_SHA256=$sealAuditSha",
    "PDF_SHA256=$pdfSha",
    "SOURCE_SHA256=$sourceSha",
    'N=14',
    'C=91',
    'MANUAL_OBJECTS=14',
    'MANUAL_PAIRS=91',
    'MANUAL_VIEWS=17',
    'MANUAL_MATH_SEMANTIC=10',
    'MANUAL_GLYPH_CODEPOINT=25',
    'UNIQUE_HARD_DEFECTS=1',
    "HARD_DEFECT_ID=$hardDefectId",
    'MANUAL_FIELDS_SCRIPT_GENERATED=0',
    'COMMIT_COUNT=0',
    'ADDITIONAL_TYPESET_COUNT=0',
    "MARKER_PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))",
    "MARKER_LAST_WRITE_UTC=$($future.ToString('o'))"
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$' }).Count -ne 0) { throw 'invalid WSTOP physical line' }
if (@($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'duplicate WSTOP key' }
[IO.File]::WriteAllText($stage, (($markerLines -join "`n") + "`n"), [Text.UTF8Encoding]::new($false))
[IO.File]::SetLastWriteTimeUtc($stage, $future)
$stageItem = Get-Item -LiteralPath $stage -Force
[IO.File]::SetAttributes($stageItem.FullName, ($stageItem.Attributes -bor [IO.FileAttributes]::ReadOnly))
if (-not ((Get-Item -LiteralPath $stage -Force).Attributes -band [IO.FileAttributes]::ReadOnly)) { throw 'external marker is not ReadOnly' }

$markerPath = Join-Path $root 'WRITE_STOPPED'
Move-Item -LiteralPath $stage -Destination $markerPath

$markerItem = Get-Item -LiteralPath $markerPath -Force
$allFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$allDirs = @(@(Get-Item -LiteralPath $root -Force) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force))
$notReadonlyFiles = @($allFiles | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$notReadonlyDirs = @($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$otherItems = @($allFiles | Where-Object { $_.FullName -ne $markerPath }) + $allDirs
$maxOtherTicks = ($otherItems | Measure-Object -Property @{ Expression = { $_.LastWriteTimeUtc.Ticks } } -Maximum).Maximum
$margin = [int64]$markerItem.LastWriteTimeUtc.Ticks - [int64]$maxOtherTicks
if ($allFiles.Count -ne ($payloadRows.Count + 4)) { throw "final ordinary count mismatch: $($allFiles.Count)" }
if ($notReadonlyFiles.Count -ne 0 -or $notReadonlyDirs.Count -ne 0) { throw 'postmarker readonly gate failed' }
if ($margin -le 0) { throw "WSTOP is not strictly latest including root: $margin" }

$snapshot1 = Get-TreeSnapshot $root
$snapshot2 = Get-TreeSnapshot $root
if ($snapshot1 -ne $snapshot2) { throw 'postmarker snapshots differ' }

$finished = [DateTime]::UtcNow
$result = [ordered]@{
    schema = 'P126_R3A_SEAL_CONTROLLER_RESULT_V1'
    handoff_id = $handoffId
    verdict = $verdict
    invocation_count = 1
    retry_count = 0
    start_utc = $started.ToString('o')
    end_utc = $finished.ToString('o')
    exit = 0
    natural = $true
    payload_count = $payloadRows.Count
    control_count = 4
    ordinary_count = $allFiles.Count
    directory_count_including_root = $allDirs.Count
    readonly_files = $allFiles.Count - $notReadonlyFiles.Count
    readonly_dirs = $allDirs.Count - $notReadonlyDirs.Count
    marker_path = $markerPath
    marker_bytes = $markerItem.Length
    marker_sha256 = (Get-FileHash -LiteralPath $markerPath -Algorithm SHA256).Hash.ToUpperInvariant()
    marker_last_write_utc_ticks = $markerItem.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = $margin
    files_at_or_after_excluding_marker = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count
    postmarker_snapshot_sha256 = $snapshot1
    postmarker_content_attribute_writes = 0
}
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $resultPath -Encoding utf8NoBOM
Write-Output ($result | ConvertTo-Json -Depth 6)
