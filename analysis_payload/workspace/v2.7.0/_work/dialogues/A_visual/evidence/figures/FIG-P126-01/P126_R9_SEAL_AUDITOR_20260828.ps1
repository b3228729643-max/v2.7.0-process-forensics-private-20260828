$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R9_SA2_THREE_HARD_PATCH_R115_DIRECT_BUILD_20260828'
$Result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R9_SEAL_AUDITOR_RESULT_20260828.json'
$ControllerResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R9_SEAL_CONTROLLER_RESULT_20260828.json'
$ControlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')

function Get-Sha256([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Get-Relative([string]$Base, [string]$Path) { return [IO.Path]::GetRelativePath($Base, $Path).Replace('\','/') }
function Get-Ticks([datetime]$Value) { return $Value.ToUniversalTime().Ticks }
function Get-RootSnapshot([string]$Base) {
    $rows = [Collections.Generic.List[string]]::new()
    foreach ($file in @(Get-ChildItem -LiteralPath $Base -Recurse -Force -File | Sort-Object FullName)) {
        $rows.Add(('F`t{0}`t{1}`t{2}`t{3}`t{4}`t{5}' -f (Get-Relative $Base $file.FullName),$file.Length,(Get-Sha256 $file.FullName),(Get-Ticks $file.CreationTimeUtc),(Get-Ticks $file.LastWriteTimeUtc),[int]$file.Attributes))
    }
    foreach ($dir in @((Get-Item -LiteralPath $Base -Force)) + @(Get-ChildItem -LiteralPath $Base -Recurse -Force -Directory | Sort-Object FullName)) {
        $relative = if ($dir.FullName -eq $Base) { '.' } else { Get-Relative $Base $dir.FullName }
        $rows.Add(('D`t{0}`t{1}`t{2}`t{3}' -f $relative,(Get-Ticks $dir.CreationTimeUtc),(Get-Ticks $dir.LastWriteTimeUtc),[int]$dir.Attributes))
    }
    $bytes = [Text.UTF8Encoding]::new($false).GetBytes((($rows -join "`n") + "`n"))
    return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

if (Test-Path -LiteralPath $Result) { throw 'AUDITOR_RESULT_ALREADY_EXISTS' }
if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'ROOT_MISSING' }
$controller = Get-Content -LiteralPath $ControllerResult -Raw -Encoding utf8 | ConvertFrom-Json
if ($controller.exit -ne 0 -or $controller.invocation_count -ne 1 -or $controller.retry_count -ne 0) { throw 'CONTROLLER_RESULT_GATE' }

$snapshot1 = Get-RootSnapshot $Root
Start-Sleep -Milliseconds 300
$snapshot2 = Get-RootSnapshot $Root
if ($snapshot1 -ne $snapshot2) { throw 'POSTMARKER_SNAPSHOT_MISMATCH' }
$files = @(Get-ChildItem -LiteralPath $Root -Recurse -Force -File)
$dirs = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force -Directory)
if ($files.Count -ne 140) { throw "ORDINARY_COUNT:$($files.Count)" }
$notRoFiles = @($files | Where-Object { -not $_.IsReadOnly })
$notRoDirs = @($dirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($notRoFiles.Count -ne 0 -or $notRoDirs.Count -ne 0) { throw 'READONLY_GATE' }

$manifestRows = @(Import-Csv -LiteralPath (Join-Path $Root 'PAYLOAD_MANIFEST.csv'))
$manifestJson = Get-Content -LiteralPath (Join-Path $Root 'PAYLOAD_MANIFEST.json') -Raw -Encoding utf8 | ConvertFrom-Json
$sealAudit = Get-Content -LiteralPath (Join-Path $Root 'SEAL_AUDIT.json') -Raw -Encoding utf8 | ConvertFrom-Json
if ($manifestRows.Count -ne 136 -or @($manifestJson.rows).Count -ne 136 -or $sealAudit.payload_count -ne 136) { throw 'MANIFEST_COUNT_GATE' }
$actualPayload = @($files | Where-Object { $ControlNames -notcontains $_.Name })
if ($actualPayload.Count -ne 136) { throw 'PAYLOAD_FS_COUNT' }
$actualMap = @{}
foreach ($file in $actualPayload) { $actualMap[(Get-Relative $Root $file.FullName)] = $file }
$identityErrors = 0
foreach ($row in $manifestRows) {
    if (-not $actualMap.ContainsKey($row.relative_path)) { $identityErrors++; continue }
    $file = $actualMap[$row.relative_path]
    if ([int64]$row.bytes -ne $file.Length -or $row.sha256 -ne (Get-Sha256 $file.FullName) -or [int64]$row.creation_time_utc_ticks -ne (Get-Ticks $file.CreationTimeUtc) -or [int64]$row.last_write_time_utc_ticks -ne (Get-Ticks $file.LastWriteTimeUtc)) { $identityErrors++ }
}
if ($identityErrors -ne 0) { throw "MANIFEST_IDENTITY:$identityErrors" }

$markerPath = Join-Path $Root 'WRITE_STOPPED'
$marker = Get-Item -LiteralPath $markerPath -Force
$lines = @([IO.File]::ReadAllLines($markerPath, [Text.UTF8Encoding]::new($false)))
$badLines = @($lines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=\t\r\n]+$' })
$keys = @($lines | ForEach-Object { ($_ -split '=',2)[0] })
$duplicateKeys = @($keys | Group-Object -CaseSensitive | Where-Object { $_.Count -ne 1 })
if ($lines.Count -ne 24 -or $badLines.Count -ne 0 -or $duplicateKeys.Count -ne 0) { throw 'MARKER_SYNTAX_GATE' }
$atOrAfter = @($files + $dirs | Where-Object { $_.FullName -ne $marker.FullName -and $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
if ($atOrAfter.Count -ne 0) { throw 'MARKER_LATEST_GATE' }
$nonMarkerMax = ($files + $dirs | Where-Object { $_.FullName -ne $marker.FullName } | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum

$csvParseFail = 0
foreach ($file in @($files | Where-Object Extension -eq '.csv')) { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvParseFail++ } }
$jsonParseFail = 0
foreach ($file in @($files | Where-Object Extension -eq '.json')) { try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding utf8 | ConvertFrom-Json } catch { $jsonParseFail++ } }
$adsCount = 0
foreach ($file in $files) { $adsCount += @((Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue) | Where-Object Stream -ne ':$DATA').Count }
$pycCacheCount = @($files | Where-Object Extension -eq '.pyc').Count + @($dirs | Where-Object { $_.Name -eq '__pycache__' }).Count
$reparseCount = @($files + $dirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($csvParseFail -ne 0 -or $jsonParseFail -ne 0 -or $adsCount -ne 0 -or $pycCacheCount -ne 0 -or $reparseCount -ne 0) { throw 'PARSE_HYGIENE_GATE' }

$auditResult = [ordered]@{
    schema = 'P126_R9_SEAL_AUDITOR_RESULT_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R9-20260828'
    invocation_count = 1
    retry_count = 0
    exit = 0
    verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
    payload_count = 136
    control_count = 4
    ordinary_count = $files.Count
    directory_count_including_root = $dirs.Count
    readonly_files = $files.Count
    readonly_directories = $dirs.Count
    manifest_identity_errors = $identityErrors
    marker_sha256 = Get-Sha256 $markerPath
    marker_line_count = $lines.Count
    marker_bad_lines = $badLines.Count
    marker_duplicate_keys = $duplicateKeys.Count
    marker_ticks = $marker.LastWriteTimeUtc.Ticks
    strict_latest_margin_ticks = [int64]$marker.LastWriteTimeUtc.Ticks - [int64]$nonMarkerMax
    at_or_after_excluding_marker = $atOrAfter.Count
    postmarker_snapshot1_sha256 = $snapshot1
    postmarker_snapshot2_sha256 = $snapshot2
    postmarker_content_attribute_writes = 0
    csv_parse_fail = $csvParseFail
    json_parse_fail = $jsonParseFail
    ads_count = $adsCount
    pyc_cache_count = $pycCacheCount
    reparse_count = $reparseCount
}
[IO.File]::WriteAllText($Result, (($auditResult | ConvertTo-Json -Depth 5) + "`n"), [Text.UTF8Encoding]::new($false))
Write-Output ($auditResult | ConvertTo-Json -Compress)
