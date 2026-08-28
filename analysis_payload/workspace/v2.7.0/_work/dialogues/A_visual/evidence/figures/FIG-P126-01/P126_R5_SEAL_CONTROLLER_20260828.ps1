Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R5_SA2_LEGEND_SEGMENT_PATCH_R115_DIRECT_BUILD_20260828'
$Manifest = Join-Path $Root 'PAYLOAD_MANIFEST.csv'
$SealAudit = Join-Path $Root 'SEAL_AUDIT.json'
$Marker = Join-Path $Root 'WRITE_STOPPED'
$Stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R5_WRITE_STOPPED.stage'
$ResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R5_SEAL_CONTROLLER_RESULT_20260828.json'
$Source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$Wrapper = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\讲义源码\合并总册\v260_FIG-P126-01_standalone.tex'
$Pdf = Join-Path $Root 'build\v260_FIG-P126-01_standalone.pdf'
$ControllerPath = $MyInvocation.MyCommand.Path
$Utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-Sha256([string]$Path) {
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
    [IO.File]::WriteAllText($Path, $Content, $Utf8NoBom)
}

function Get-CanonicalRelative([string]$Base, [string]$Path) {
    $relative = [IO.Path]::GetRelativePath($Base, $Path).Replace('\', '/')
    if ([string]::IsNullOrWhiteSpace($relative) -or [IO.Path]::IsPathRooted($relative)) {
        throw "unsafe relative path: $relative"
    }
    $parts = @($relative.Split('/'))
    if (@($parts | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) {
        throw "unsafe relative segment: $relative"
    }
    return $relative
}

function Test-ReadOnly([string]$Path) {
    return (([IO.File]::GetAttributes($Path) -band [IO.FileAttributes]::ReadOnly) -ne 0)
}

function Set-ReadOnly([string]$Path) {
    $attributes = [IO.File]::GetAttributes($Path)
    [IO.File]::SetAttributes($Path, ($attributes -bor [IO.FileAttributes]::ReadOnly))
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
    $bytes = $Utf8NoBom.GetBytes($text)
    $hash = [Security.Cryptography.SHA256]::HashData($bytes)
    return [ordered]@{
        file_count = $files.Count
        directory_count = $dirs.Count
        canonical_bytes = $bytes.Length
        sha256 = [Convert]::ToHexString($hash)
    }
}

if (-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'R5 root absent' }
foreach ($path in @($Manifest, $SealAudit, $Marker, $Stage, $ResultPath)) {
    if (Test-Path -LiteralPath $path) { throw "preexisting seal artifact: $path" }
}
if ((Get-Item -LiteralPath $Pdf).Length -ne 33952 -or (Get-Sha256 $Pdf) -ne '58BA180DBC92ED6DFEECCA2D77FE021C55B9D9B5DE0A1F6DB5F4B8D7316CAD06') { throw 'PDF identity mismatch' }
if ((Get-Item -LiteralPath $Source).Length -ne 4356 -or (Get-Sha256 $Source) -ne '3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75') { throw 'source identity mismatch' }
if ((Get-Item -LiteralPath $Wrapper).Length -ne 395 -or (Get-Sha256 $Wrapper) -ne '706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124') { throw 'wrapper identity mismatch' }

$payloadFiles = @(Get-ChildItem -LiteralPath $Root -File -Recurse | Where-Object { $_.FullName -notin @($Manifest, $SealAudit, $Marker) } | Sort-Object FullName)
if ($payloadFiles.Count -lt 1) { throw 'empty payload' }
$manifestRows = foreach ($file in $payloadFiles) {
    [pscustomobject][ordered]@{
        relative_path = Get-CanonicalRelative $Root $file.FullName
        bytes = $file.Length
        sha256 = Get-Sha256 $file.FullName
        creation_time_utc_ticks = $file.CreationTimeUtc.Ticks
        last_write_time_utc_ticks = $file.LastWriteTimeUtc.Ticks
    }
}
if (@($manifestRows.relative_path | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'manifest duplicate path' }
$manifestText = (($manifestRows | ConvertTo-Csv -NoTypeInformation) -join "`r`n") + "`r`n"
Write-Utf8NoBom $Manifest $manifestText
$manifestSha = Get-Sha256 $Manifest

$sealAuditObject = [ordered]@{
    schema = 'P126_R5_SEAL_AUDIT_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R5-20260828'
    operation = 'P126_R115_R5_LOCAL_SA2_SINGLE_SEAL'
    verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
    hard_defect_id = 'HARD-LEGEND-X2-SEGMENTS-COLLAPSE'
    payload_count = $manifestRows.Count
    controls_expected = 3
    ordinary_expected = $manifestRows.Count + 3
    manifest_sha256 = $manifestSha
    pdf_bytes = 33952
    pdf_sha256 = '58BA180DBC92ED6DFEECCA2D77FE021C55B9D9B5DE0A1F6DB5F4B8D7316CAD06'
    source_bytes = 4356
    source_sha256 = '3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75'
    wrapper_bytes = 395
    wrapper_sha256 = '706312FAED4A825F61E1517AFFFC852369845F9DAEA051B6E8FEB99335998124'
    controller_invocation_count = 1
    retry_count = 0
    additional_tex_count = 0
    manual_fields_generated_by_machine = 0
    premarker_status = 'CLEAR'
}
Write-Utf8NoBom $SealAudit (($sealAuditObject | ConvertTo-Json -Depth 6) + "`n")
$sealAuditSha = Get-Sha256 $SealAudit

$premarkerFiles = @(Get-ChildItem -LiteralPath $Root -File -Recurse)
$premarkerDirs = @((Get-Item -LiteralPath $Root)) + @(Get-ChildItem -LiteralPath $Root -Directory -Recurse)
foreach ($file in $premarkerFiles) { Set-ReadOnly $file.FullName }
foreach ($dir in @($premarkerDirs | Sort-Object { $_.FullName.Length } -Descending)) { Set-ReadOnly $dir.FullName }
if (@($premarkerFiles | Where-Object { -not (Test-ReadOnly $_.FullName) }).Count -ne 0) { throw 'premarker file readonly failure' }
if (@($premarkerDirs | Where-Object { -not (Test-ReadOnly $_.FullName) }).Count -ne 0) { throw 'premarker directory readonly failure' }

$maxTicks = 0L
foreach ($item in @($premarkerFiles) + @($premarkerDirs)) {
    if ($item.LastWriteTimeUtc.Ticks -gt $maxTicks) { $maxTicks = $item.LastWriteTimeUtc.Ticks }
}
$futureTicks = [Math]::Max($maxTicks + 6000000000L, [DateTime]::UtcNow.AddMinutes(10).Ticks)
$markerLines = @(
    'SCHEMA=P126_R5_WRITE_STOPPED_V1',
    'HANDOFF_ID=A-R115-P126-SA2-DIRECT-BUILD-R5-20260828',
    'OPERATION=P126_R115_R5_LOCAL_SA2_SINGLE_SEAL',
    'UID=FIG-P126-01',
    'ROLE=SA2',
    'VERDICT=LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE',
    'HARD_DEFECT_COUNT=1',
    'HARD_DEFECT_ID=HARD-LEGEND-X2-SEGMENTS-COLLAPSE',
    "ROOT=$Root",
    'PDF_BYTES=33952',
    'PDF_SHA256=58BA180DBC92ED6DFEECCA2D77FE021C55B9D9B5DE0A1F6DB5F4B8D7316CAD06',
    'SOURCE_BYTES=4356',
    'SOURCE_SHA256=3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75',
    "PAYLOAD_COUNT=$($manifestRows.Count)",
    'CONTROL_COUNT=3',
    "ORDINARY_COUNT=$($manifestRows.Count + 3)",
    "PAYLOAD_MANIFEST_SHA256=$manifestSha",
    "SEAL_AUDIT_SHA256=$sealAuditSha",
    "CONTROLLER_SHA256=$(Get-Sha256 $ControllerPath)",
    'CONTROLLER_INVOCATION_COUNT=1',
    'RETRY_COUNT=0',
    'ADDITIONAL_TEX_COUNT=0',
    'POSTMARKER_ROOT_WRITE_COUNT=0',
    "PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))",
    "LAST_WRITE_TIME_UTC_TICKS=$futureTicks"
)
if ($markerLines.Count -ne 25 -or @($markerLines | Where-Object { $_ -notmatch '^[^=\s]+=[^\r\n]+$' }).Count -ne 0) { throw 'marker syntax failure' }
Write-Utf8NoBom $Stage (($markerLines -join "`r`n") + "`r`n")
[IO.File]::SetLastWriteTimeUtc($Stage, [DateTime]::new($futureTicks, [DateTimeKind]::Utc))
Set-ReadOnly $Stage
if (-not (Test-ReadOnly $Stage) -or (Get-Item -LiteralPath $Stage).LastWriteTimeUtc.Ticks -ne $futureTicks) { throw 'external marker preparation failure' }
Move-Item -LiteralPath $Stage -Destination $Marker

$snapshot1 = Get-TreeSnapshot $Root
Start-Sleep -Milliseconds 250
$snapshot2 = Get-TreeSnapshot $Root
if ($snapshot1.sha256 -ne $snapshot2.sha256) { throw 'postmarker root snapshot changed' }
$result = [ordered]@{
    schema = 'P126_R5_SEAL_CONTROLLER_RESULT_V1'
    handoff_id = 'A-R115-P126-SA2-DIRECT-BUILD-R5-20260828'
    operation = 'P126_R115_R5_LOCAL_SA2_SINGLE_SEAL'
    invocation_count = 1
    retry_count = 0
    exit = 0
    natural = $true
    payload_count = $manifestRows.Count
    control_count = 3
    ordinary_count = $manifestRows.Count + 3
    directory_count = $snapshot2.directory_count
    manifest_sha256 = $manifestSha
    seal_audit_sha256 = $sealAuditSha
    marker_sha256 = Get-Sha256 $Marker
    marker_ticks = (Get-Item -LiteralPath $Marker).LastWriteTimeUtc.Ticks
    postmarker_snapshot1_sha256 = $snapshot1.sha256
    postmarker_snapshot2_sha256 = $snapshot2.sha256
    postmarker_snapshot_equal = ($snapshot1.sha256 -eq $snapshot2.sha256)
    source_sha256 = Get-Sha256 $Source
    wrapper_sha256 = Get-Sha256 $Wrapper
    pdf_sha256 = Get-Sha256 $Pdf
    completed_utc = [DateTime]::UtcNow.ToString('o')
}
Write-Utf8NoBom $ResultPath (($result | ConvertTo-Json -Depth 6) + "`n")
Set-ReadOnly $ResultPath
Write-Output ($result | ConvertTo-Json -Depth 6)
