Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828'
$Manifest = Join-Path $Root 'PAYLOAD_MANIFEST.csv'
$SealAudit = Join-Path $Root 'SEAL_AUDIT.json'
$Marker = Join-Path $Root 'WRITE_STOPPED'
$ControllerResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R5_SEAL_CONTROLLER_RESULT_20260828.json'
$AuditResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R5_SEAL_AUDITOR_RESULT_20260828.json'
$Utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-Sha256([string]$Path) { return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Write-Utf8NoBom([string]$Path, [string]$Content) { [IO.File]::WriteAllText($Path, $Content, $Utf8NoBom) }
function Test-ReadOnly([string]$Path) { return (([IO.File]::GetAttributes($Path) -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function Get-CanonicalRelative([string]$Base, [string]$Path) {
    $relative = [IO.Path]::GetRelativePath($Base, $Path).Replace('\', '/')
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative)) { throw "unsafe path $relative" }
    $parts = @($relative.Split('/'))
    if (@($parts | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw "unsafe segment $relative" }
    return $relative
}
function Get-TreeSnapshot([string]$Base) {
    $rows = [Collections.Generic.List[string]]::new()
    $files = @(Get-ChildItem -LiteralPath $Base -File -Recurse | Sort-Object FullName)
    foreach ($file in $files) {
        $rel = Get-CanonicalRelative $Base $file.FullName
        $rows.Add("F`t$rel`t$($file.Length)`t$(Get-Sha256 $file.FullName)`t$($file.CreationTimeUtc.Ticks)`t$($file.LastWriteTimeUtc.Ticks)`t$([int][IO.File]::GetAttributes($file.FullName))")
    }
    $dirs = @((Get-Item -LiteralPath $Base)) + @(Get-ChildItem -LiteralPath $Base -Directory -Recurse | Sort-Object FullName)
    foreach ($dir in $dirs) {
        $rel = if ($dir.FullName -eq $Base) { '.' } else { Get-CanonicalRelative $Base $dir.FullName }
        $rows.Add("D`t$rel`t0`t-`t$($dir.CreationTimeUtc.Ticks)`t$($dir.LastWriteTimeUtc.Ticks)`t$([int][IO.File]::GetAttributes($dir.FullName))")
    }
    $text = (@($rows | Sort-Object -CaseSensitive) -join "`n") + "`n"
    $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($Utf8NoBom.GetBytes($text)))
    return [ordered]@{ file_count=$files.Count; directory_count=$dirs.Count; sha256=$hash }
}

if (Test-Path -LiteralPath $AuditResult) { throw 'auditor result already exists' }
$controller = Get-Content -LiteralPath $ControllerResult -Raw | ConvertFrom-Json
if ($controller.exit -ne 0 -or -not $controller.natural -or $controller.invocation_count -ne 1 -or $controller.retry_count -ne 0) { throw 'controller result invalid' }

$files = @(Get-ChildItem -LiteralPath $Root -File -Recurse)
$dirs = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Directory -Recurse)
$payload = @($files | Where-Object { $_.FullName -notin @($Manifest, $SealAudit, $Marker) })
$controls = @($files | Where-Object { $_.FullName -in @($Manifest, $SealAudit, $Marker) })
$rows = @(Import-Csv -LiteralPath $Manifest)
$rowDuplicates = @($rows.relative_path | Group-Object | Where-Object { $_.Count -ne 1 }).Count
$rowMap = @{}
foreach ($row in $rows) { $rowMap[[string]$row.relative_path] = $row }
$actualMap = @{}
foreach ($file in $payload) { $actualMap[(Get-CanonicalRelative $Root $file.FullName)] = $file }
$setDiff = @(Compare-Object @($rowMap.Keys | Sort-Object -CaseSensitive) @($actualMap.Keys | Sort-Object -CaseSensitive) -CaseSensitive).Count
$identityMismatch = 0
foreach ($key in $rowMap.Keys) {
    if (-not $actualMap.ContainsKey($key)) { $identityMismatch++; continue }
    $row = $rowMap[$key]; $file = $actualMap[$key]
    if ([long]$row.bytes -ne $file.Length -or [string]$row.sha256 -ne (Get-Sha256 $file.FullName) -or [long]$row.creation_time_utc_ticks -ne $file.CreationTimeUtc.Ticks -or [long]$row.last_write_time_utc_ticks -ne $file.LastWriteTimeUtc.Ticks) { $identityMismatch++ }
}
$fileReadonlyFailures = @($files | Where-Object { -not (Test-ReadOnly $_.FullName) }).Count
$dirReadonlyFailures = @($dirs | Where-Object { -not (Test-ReadOnly $_.FullName) }).Count

$markerBytes = [IO.File]::ReadAllBytes($Marker)
$markerText = $Utf8NoBom.GetString($markerBytes)
$markerLines = @($markerText -split "`r?`n" | Where-Object { $_ -ne '' })
$markerBad = @($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^\r\n]+$' -or $_ -match "`t|\$\{|PLACEHOLDER|TAB\+rue" }).Count
$markerMap = @{}
foreach ($line in $markerLines) { $pair = $line.Split('=', 2); if ($markerMap.ContainsKey($pair[0])) { throw 'marker duplicate key' }; $markerMap[$pair[0]] = $pair[1] }
$requiredKeys = @('SCHEMA','HANDOFF_ID','OPERATION','UID','ROLE','VERDICT','HARD_DEFECT_COUNT','HARD_DEFECT_ID','ROOT','PDF_BYTES','PDF_SHA256','SOURCE_BYTES','SOURCE_SHA256','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','CONTROLLER_SHA256','CONTROLLER_INVOCATION_COUNT','RETRY_COUNT','ADDITIONAL_TEX_COUNT','POSTMARKER_ROOT_WRITE_COUNT','PREPARED_UTC','LAST_WRITE_TIME_UTC_TICKS')
$markerKeyDiff = @(Compare-Object @($requiredKeys | Sort-Object -CaseSensitive) @($markerMap.Keys | Sort-Object -CaseSensitive) -CaseSensitive).Count
if ($markerMap['PAYLOAD_COUNT'] -ne [string]$payload.Count -or $markerMap['CONTROL_COUNT'] -ne '3' -or $markerMap['ORDINARY_COUNT'] -ne [string]$files.Count -or $markerMap['PAYLOAD_MANIFEST_SHA256'] -ne (Get-Sha256 $Manifest) -or $markerMap['SEAL_AUDIT_SHA256'] -ne (Get-Sha256 $SealAudit) -or $markerMap['VERDICT'] -ne 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE') { throw 'marker binding mismatch' }

$markerTicks = (Get-Item -LiteralPath $Marker).LastWriteTimeUtc.Ticks
$nonmarkerItems = @($files | Where-Object FullName -ne $Marker) + @($dirs)
$maxOtherTicks = 0L
foreach ($item in $nonmarkerItems) { if ($item.LastWriteTimeUtc.Ticks -gt $maxOtherTicks) { $maxOtherTicks = $item.LastWriteTimeUtc.Ticks } }
$atOrAfter = @($nonmarkerItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerTicks }).Count
$strictMarginTicks = $markerTicks - $maxOtherTicks

$jsonParseFailures = 0
foreach ($file in @($files | Where-Object Extension -eq '.json')) { try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { $jsonParseFailures++ } }
$csvParseFailures = 0
foreach ($file in @($files | Where-Object Extension -eq '.csv')) { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvParseFailures++ } }
$adsCount = 0
foreach ($file in $files) { try { $adsCount += @(Get-Item -LiteralPath $file.FullName -Stream * | Where-Object Stream -ne ':$DATA').Count } catch {} }
$forbiddenCachePyc = @($files + $dirs | Where-Object { $_.FullName -match '(?i)(^|[\\/])(__pycache__|\.pytest_cache)([\\/]|$)|\.pyc$' }).Count
$reparseCount = @($dirs | Where-Object { ([IO.File]::GetAttributes($_.FullName) -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count

$snapshot = Get-TreeSnapshot $Root
$postmarkerSnapshotMismatch = @($controller.postmarker_snapshot1_sha256, $controller.postmarker_snapshot2_sha256 | Where-Object { $_ -ne $snapshot.sha256 }).Count
$audit = [ordered]@{
    schema = 'P126_R5_SEAL_AUDITOR_RESULT_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R5-20260828'
    verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
    payload_count = $payload.Count
    control_count = $controls.Count
    ordinary_count = $files.Count
    directory_count = $dirs.Count
    manifest_rows = $rows.Count
    manifest_duplicate_paths = $rowDuplicates
    manifest_set_diff = $setDiff
    manifest_identity_mismatch = $identityMismatch
    file_readonly_failures = $fileReadonlyFailures
    directory_readonly_failures = $dirReadonlyFailures
    marker_physical_nonempty_lines = $markerLines.Count
    marker_unique_keys = $markerMap.Count
    marker_bad_lines = $markerBad
    marker_key_set_diff = $markerKeyDiff
    marker_ticks = $markerTicks
    max_other_ticks = $maxOtherTicks
    strict_latest_margin_ticks = $strictMarginTicks
    at_or_after_excluding_marker = $atOrAfter
    postmarker_snapshot_mismatch = $postmarkerSnapshotMismatch
    json_parse_failures = $jsonParseFailures
    csv_parse_failures = $csvParseFailures
    ads_count = $adsCount
    forbidden_cache_pyc_count = $forbiddenCachePyc
    reparse_count = $reparseCount
    root_snapshot_sha256 = $snapshot.sha256
    pass = ($payload.Count -eq $rows.Count -and $controls.Count -eq 3 -and $files.Count -eq $payload.Count + 3 -and $rowDuplicates -eq 0 -and $setDiff -eq 0 -and $identityMismatch -eq 0 -and $fileReadonlyFailures -eq 0 -and $dirReadonlyFailures -eq 0 -and $markerLines.Count -eq 25 -and $markerMap.Count -eq 25 -and $markerBad -eq 0 -and $markerKeyDiff -eq 0 -and $strictMarginTicks -gt 0 -and $atOrAfter -eq 0 -and $postmarkerSnapshotMismatch -eq 0 -and $jsonParseFailures -eq 0 -and $csvParseFailures -eq 0 -and $adsCount -eq 0 -and $forbiddenCachePyc -eq 0 -and $reparseCount -eq 0)
    audited_utc = [DateTime]::UtcNow.ToString('o')
}
if (-not $audit.pass) { throw "seal audit failed: $($audit | ConvertTo-Json -Compress)" }
Write-Utf8NoBom $AuditResult (($audit | ConvertTo-Json -Depth 6) + "`n")
$attributes = [IO.File]::GetAttributes($AuditResult)
[IO.File]::SetAttributes($AuditResult, ($attributes -bor [IO.FileAttributes]::ReadOnly))
Write-Output ($audit | ConvertTo-Json -Depth 6)
