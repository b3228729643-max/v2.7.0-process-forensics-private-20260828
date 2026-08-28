$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828'
$Stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R9_WRITE_STOPPED_STAGE_20260828.tmp'
$Result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R9_SEAL_CONTROLLER_RESULT_20260828.json'
$Controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')
$ExpectedPayload = 136
$ExpectedOrdinary = 140

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-Relative([string]$Base, [string]$Path) {
    return [IO.Path]::GetRelativePath($Base, $Path).Replace('\','/')
}

function Get-Ticks([datetime]$Value) {
    return $Value.ToUniversalTime().Ticks
}

function Set-ReadOnlyFile([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    $item.IsReadOnly = $true
}

function Set-ReadOnlyDirectory([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force
    $item.Attributes = $item.Attributes -bor [IO.FileAttributes]::ReadOnly
}

function Get-RootSnapshot([string]$Base) {
    $rows = [Collections.Generic.List[string]]::new()
    foreach ($file in @(Get-ChildItem -LiteralPath $Base -Recurse -Force -File | Sort-Object FullName)) {
        $rows.Add(('F`t{0}`t{1}`t{2}`t{3}`t{4}`t{5}' -f (Get-Relative $Base $file.FullName),$file.Length,(Get-Sha256 $file.FullName),(Get-Ticks $file.CreationTimeUtc),(Get-Ticks $file.LastWriteTimeUtc),[int]$file.Attributes))
    }
    foreach ($dir in @((Get-Item -LiteralPath $Base -Force)) + @(Get-ChildItem -LiteralPath $Base -Recurse -Force -Directory | Sort-Object FullName)) {
        $relative = if ($dir.FullName -eq $Base) { '.' } else { Get-Relative $Base $dir.FullName }
        $rows.Add(('D`t{0}`t{1}`t{2}`t{3}' -f $relative,(Get-Ticks $dir.CreationTimeUtc),(Get-Ticks $dir.LastWriteTimeUtc),[int]$dir.Attributes))
    }
    $text = ($rows -join "`n") + "`n"
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes($text)
    $hash = [Security.Cryptography.SHA256]::HashData($bytes)
    return [Convert]::ToHexString($hash)
}

if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'ROOT_MISSING' }
if (Test-Path -LiteralPath $Stage) { throw 'STAGE_ALREADY_EXISTS' }
if (Test-Path -LiteralPath $Result) { throw 'RESULT_ALREADY_EXISTS' }
foreach ($name in $Controls) {
    if (Test-Path -LiteralPath (Join-Path $Root $name)) { throw "CONTROL_ALREADY_EXISTS:$name" }
}

$payloadFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File | Sort-Object FullName)
if ($payloadFiles.Count -ne $ExpectedPayload) { throw "PAYLOAD_COUNT:$($payloadFiles.Count)" }
$payloadRows = foreach ($file in $payloadFiles) {
    [pscustomobject][ordered]@{
        relative_path = Get-Relative $Root $file.FullName
        bytes = [int64]$file.Length
        sha256 = Get-Sha256 $file.FullName
        creation_time_utc_ticks = Get-Ticks $file.CreationTimeUtc
        last_write_time_utc_ticks = Get-Ticks $file.LastWriteTimeUtc
    }
}
$duplicatePaths = @($payloadRows | Group-Object -Property relative_path -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($duplicatePaths.Count -ne 0) { throw 'DUPLICATE_PAYLOAD_PATH' }

$csvPath = Join-Path $Root 'PAYLOAD_MANIFEST.csv'
$jsonPath = Join-Path $Root 'PAYLOAD_MANIFEST.json'
$auditPath = Join-Path $Root 'SEAL_AUDIT.json'
$payloadRows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8
$manifestJson = [ordered]@{
    schema = 'P126_R9_PAYLOAD_MANIFEST_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R9-20260828'
    verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
    payload_count = $ExpectedPayload
    rows = @($payloadRows)
}
[IO.File]::WriteAllText($jsonPath, (($manifestJson | ConvertTo-Json -Depth 8) + "`n"), [Text.UTF8Encoding]::new($false))

$csvRows = @(Import-Csv -LiteralPath $csvPath)
$jsonRead = Get-Content -LiteralPath $jsonPath -Raw -Encoding utf8 | ConvertFrom-Json
if ($csvRows.Count -ne $ExpectedPayload -or @($jsonRead.rows).Count -ne $ExpectedPayload) { throw 'MANIFEST_ROW_COUNT' }
$audit = [ordered]@{
    schema = 'P126_R9_SEAL_AUDIT_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R9-20260828'
    verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
    payload_count = $ExpectedPayload
    control_count = 4
    expected_ordinary_count = $ExpectedOrdinary
    payload_manifest_csv_sha256 = Get-Sha256 $csvPath
    payload_manifest_json_sha256 = Get-Sha256 $jsonPath
    denominator_n = 60
    unordered_pairs_c = 1770
    hard_failure_count = 2
    hard_failure_ids = @('HARD-LEGEND-X2-CONTINUOUS','HARD-LABEL6-Q4-MARKER-CONTACT')
    premarker_validation = 'PASS'
}
[IO.File]::WriteAllText($auditPath, (($audit | ConvertTo-Json -Depth 6) + "`n"), [Text.UTF8Encoding]::new($false))

$premarkerFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
if ($premarkerFiles.Count -ne ($ExpectedOrdinary - 1)) { throw "PREMARKER_COUNT:$($premarkerFiles.Count)" }
foreach ($file in $premarkerFiles) { Set-ReadOnlyFile $file.FullName }
$dirs = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory | Sort-Object { $_.FullName.Length } -Descending)
foreach ($dir in $dirs) { Set-ReadOnlyDirectory $dir.FullName }
Set-ReadOnlyDirectory $Root

$premarkerFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
$allDirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory)
$notReadOnlyFiles = @($premarkerFiles | Where-Object { -not $_.IsReadOnly })
$notReadOnlyDirs = @($allDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($notReadOnlyFiles.Count -ne 0 -or $notReadOnlyDirs.Count -ne 0) { throw 'PREMARKER_READONLY_GATE' }

$maxTicks = (@($premarkerFiles | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) + @($allDirs | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks, [int64]$maxTicks + [TimeSpan]::FromMinutes(2).Ticks)
$markerLines = @(
    'SCHEMA=P126_R9_WRITE_STOPPED_V1',
    'HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R9-20260828',
    'UID=FIG-P126-01',
    'VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE',
    'PAYLOAD_COUNT=136',
    'CONTROL_COUNT=4',
    'ORDINARY_COUNT=140',
    'N=60',
    'C=1770',
    'MACHINE_CANDIDATES=218',
    'MANUAL_OBJECTS=60',
    'MANUAL_PAIRS=1770',
    'MANUAL_VIEWS=23',
    'HARD_FAILURE_COUNT=2',
    'HARD_FAILURE_1=HARD-LEGEND-X2-CONTINUOUS',
    'HARD_FAILURE_2=HARD-LABEL6-Q4-MARKER-CONTACT',
    ('PAYLOAD_MANIFEST_CSV_SHA256=' + (Get-Sha256 $csvPath)),
    ('PAYLOAD_MANIFEST_JSON_SHA256=' + (Get-Sha256 $jsonPath)),
    ('SEAL_AUDIT_SHA256=' + (Get-Sha256 $auditPath)),
    'CONTROLLER_INVOCATION_COUNT=1',
    'CONTROLLER_RETRY_COUNT=0',
    'TEX_AFTER_BUILD_RELEASE=0',
    'SOURCE_WRITE_AFTER_BUILD=0',
    'POSTMARKER_ROOT_WRITES=0'
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=\t\r\n]+$' }).Count -ne 0) { throw 'MARKER_SYNTAX' }
[IO.File]::WriteAllLines($Stage, $markerLines, [Text.UTF8Encoding]::new($false))
Set-ReadOnlyFile $Stage
[IO.File]::SetLastWriteTimeUtc($Stage, [DateTime]::new($futureTicks, [DateTimeKind]::Utc))
Set-ReadOnlyFile $Stage
$markerInfo = Get-Item -LiteralPath $Stage -Force
if (-not $markerInfo.IsReadOnly -or $markerInfo.LastWriteTimeUtc.Ticks -le $maxTicks) { throw 'STAGE_MARKER_GATE' }

$markerPath = Join-Path $Root 'WRITE_STOPPED'
Move-Item -LiteralPath $Stage -Destination $markerPath

$snapshot1 = Get-RootSnapshot $Root
Start-Sleep -Milliseconds 300
$snapshot2 = Get-RootSnapshot $Root
if ($snapshot1 -ne $snapshot2) { throw 'POSTMARKER_SNAPSHOT_MISMATCH' }
$finalFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
$finalDirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory)
$marker = Get-Item -LiteralPath $markerPath -Force
$atOrAfter = @($finalFiles + $finalDirs | Where-Object { $_.FullName -ne $marker.FullName -and $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$finalNotRoFiles = @($finalFiles | Where-Object { -not $_.IsReadOnly })
$finalNotRoDirs = @($finalDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($finalFiles.Count -ne $ExpectedOrdinary -or $finalNotRoFiles.Count -ne 0 -or $finalNotRoDirs.Count -ne 0 -or $atOrAfter.Count -ne 0) { throw 'FINAL_GATE' }
$nonMarkerMax = ($finalFiles + $finalDirs | Where-Object { $_.FullName -ne $marker.FullName } | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$resultData = [ordered]@{
    schema = 'P126_R9_SEAL_CONTROLLER_RESULT_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R9-20260828'
    invocation_count = 1
    retry_count = 0
    exit = 0
    payload_count = $ExpectedPayload
    control_count = 4
    ordinary_count = $finalFiles.Count
    directory_count_including_root = $finalDirs.Count
    readonly_files = $finalFiles.Count
    readonly_directories = $finalDirs.Count
    marker_sha256 = Get-Sha256 $markerPath
    marker_ticks = $marker.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = [int64]$marker.LastWriteTimeUtc.Ticks - [int64]$nonMarkerMax
    at_or_after_excluding_marker = $atOrAfter.Count
    postmarker_snapshot1_sha256 = $snapshot1
    postmarker_snapshot2_sha256 = $snapshot2
    postmarker_content_attribute_writes = 0
}
[IO.File]::WriteAllText($Result, (($resultData | ConvertTo-Json -Depth 5) + "`n"), [Text.UTF8Encoding]::new($false))
Write-Output ($resultData | ConvertTo-Json -Compress)
