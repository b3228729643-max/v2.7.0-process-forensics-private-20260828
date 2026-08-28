[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$Root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11A_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827'
$External = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R11A_SA2_P4_COORDINATE_DIRECT_BUILD_R113_20260827_EXTERNAL'
$Worktree = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual'
$Source = Join-Path $Worktree 'src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex'
$Wrapper = Join-Path $Worktree 'src\讲义源码\合并总册\v260_FIG-P067-01_standalone.tex'
$Pdf = Join-Path $Root 'build\v260_FIG-P067-01_standalone.pdf'
$Controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED.json')
$ExpectedSourceSha = '11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144'
$ExpectedWrapperSha = 'ADDF75D1C82DAB9AB4D5A76E6B241DA1CEB7AED9C2E536106ECFD7710B2D14BF'
$ExpectedPdfSha = '586EFE2C968A05C014A9AD8D639A8CFF0EDD0B21306CA31183485A7C75A338A1'

function Get-Sha256([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash.ToUpperInvariant()
}

function Get-Relative([string]$Base,[string]$Path) {
    return [IO.Path]::GetRelativePath($Base,$Path).Replace('\','/')
}

function Get-PayloadRows {
    param([string]$Base,[string[]]$Excluded)
    $rows = @()
    foreach($file in @(Get-ChildItem -LiteralPath $Base -Recurse -File -Force)) {
        $relative = Get-Relative $Base $file.FullName
        if($relative -in $Excluded) { continue }
        $rows += [pscustomobject]@{
            relative_path = $relative
            bytes = [int64]$file.Length
            sha256 = Get-Sha256 $file.FullName
            mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
        }
    }
    return @($rows | Sort-Object -Property relative_path)
}

function Get-Snapshot {
    param([string]$Base)
    $rows = @()
    foreach($item in @((Get-Item -LiteralPath $Base -Force)) + @(Get-ChildItem -LiteralPath $Base -Recurse -Force)) {
        $relative = if($item.FullName -eq $Base) { '.' } else { Get-Relative $Base $item.FullName }
        $rows += [pscustomobject]@{
            relative_path = $relative
            kind = if($item.PSIsContainer) { 'directory' } else { 'file' }
            bytes = if($item.PSIsContainer) { 'DIRECTORY' } else { ([int64]$item.Length).ToString() }
            mtime_utc_ticks = $item.LastWriteTimeUtc.Ticks.ToString()
            attributes = $item.Attributes.ToString()
        }
    }
    return @($rows | Sort-Object relative_path)
}

if(-not (Test-Path -LiteralPath $Root -PathType Container)) { throw 'root missing' }
if(@($Controls | Where-Object { Test-Path -LiteralPath (Join-Path $Root $_) }).Count -ne 0) { throw 'seal control already exists' }
if((Get-Item -LiteralPath $Source).Length -ne 4014 -or (Get-Sha256 $Source) -ne $ExpectedSourceSha) { throw 'source identity mismatch' }
if((Get-Item -LiteralPath $Wrapper).Length -ne 388 -or (Get-Sha256 $Wrapper) -ne $ExpectedWrapperSha) { throw 'wrapper identity mismatch' }
if((Get-Item -LiteralPath $Pdf).Length -ne 34213 -or (Get-Sha256 $Pdf) -ne $ExpectedPdfSha) { throw 'PDF identity mismatch' }
if(@(Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue).Count -ne 0) { throw 'TeX process present' }
if(@(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force | Where-Object { $_.Name -in @('__pycache__','.pytest_cache') }).Count -ne 0) { throw 'unauthorized cache directory present' }
if(@(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Where-Object { $_.Extension -eq '.pyc' }).Count -ne 0) { throw 'pyc present' }

$payload = @(Get-PayloadRows -Base $Root -Excluded $Controls)
if($payload.Count -lt 1) { throw 'empty payload' }
if(@($payload | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'duplicate payload path' }

$manifestCsv = Join-Path $Root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $Root 'PAYLOAD_MANIFEST.json'
$sealAuditPath = Join-Path $Root 'SEAL_AUDIT.json'
$payload | Export-Csv -LiteralPath $manifestCsv -NoTypeInformation -Encoding utf8
$payload | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $manifestJson -Encoding utf8NoBOM

$parseFailures = @()
foreach($jsonFile in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter '*.json' -Force)) {
    try { $null = Get-Content -LiteralPath $jsonFile.FullName -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String }
    catch { $parseFailures += (Get-Relative $Root $jsonFile.FullName) }
}
foreach($csvFile in @(Get-ChildItem -LiteralPath $Root -Recurse -File -Filter '*.csv' -Force)) {
    try { $null = @(Import-Csv -LiteralPath $csvFile.FullName).Count }
    catch { $parseFailures += (Get-Relative $Root $csvFile.FullName) }
}
if($parseFailures.Count -ne 0) { throw ('parse failures: ' + ($parseFailures -join ';')) }

$sealAudit = [ordered]@{
    handoff_id = 'A-R113-P067-SA2-DIRECT-BUILD-R11A-20260827'
    phase = 'PRE_MARKER_SEAL_AUDIT'
    payload_count = $payload.Count
    manifest_control_count = 2
    seal_audit_control_count = 1
    write_stopped_control_count = 1
    control_count = 4
    declared_final_ordinary_count = $payload.Count + 4
    duplicate_payload_path_count = 0
    parse_failure_count = 0
    unauthorized_cache_dir_count = 0
    pyc_count = 0
    authorized_texcache_present = (Test-Path -LiteralPath (Join-Path $Root 'texcache') -PathType Container)
    source_sha256 = $ExpectedSourceSha
    wrapper_sha256 = $ExpectedWrapperSha
    pdf_sha256 = $ExpectedPdfSha
    manual_object_rows = 100
    manual_critical_rows = 70
    manual_target_rows = 6
    manual_view_rows = 34
    hard_failure_count = 0
    verdict = 'LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH'
}
$sealAudit | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $sealAuditPath -Encoding utf8NoBOM

$filesBeforeMarker = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)
$directoriesBeforeMarker = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force)
foreach($file in $filesBeforeMarker) { $file.IsReadOnly = $true }
foreach($directory in $directoriesBeforeMarker) { $directory.Attributes = $directory.Attributes -bor [IO.FileAttributes]::ReadOnly }
if(@(Get-ChildItem -LiteralPath $Root -Recurse -File -Force | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'pre-marker file readonly gate failed' }
if(@($directoriesBeforeMarker | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'pre-marker directory readonly gate failed' }

$existingItems = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force)
$maxTicks = ($existingItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
$markerTemp = Join-Path $External 'R11A_WRITE_STOPPED_STAGING.json'
if(Test-Path -LiteralPath $markerTemp) { throw 'marker staging collision' }
$markerObject = [ordered]@{
    handoff_id = 'A-R113-P067-SA2-DIRECT-BUILD-R11A-20260827'
    verdict = 'LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH'
    payload_file_count = $payload.Count
    manifest_control_file_count = 2
    seal_audit_control_file_count = 1
    write_stopped_control_file_count = 1
    control_file_count = 4
    ordinary_file_total = $payload.Count + 4
    final_root = [IO.Path]::GetFullPath($Root)
    final_write = 'THIS_MARKER_MOVE'
    post_marker_root_writes_allowed = 0
    source_sha256 = $ExpectedSourceSha
    pdf_sha256 = $ExpectedPdfSha
}
$markerObject | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $markerTemp -Encoding utf8NoBOM
$markerTargetTicks = [Math]::Max(([DateTime]::UtcNow.AddSeconds(2).Ticks),($maxTicks + 10000000))
[IO.File]::SetLastWriteTimeUtc($markerTemp,[DateTime]::new($markerTargetTicks,[DateTimeKind]::Utc))
(Get-Item -LiteralPath $markerTemp).IsReadOnly = $true
Move-Item -LiteralPath $markerTemp -Destination (Join-Path $Root 'WRITE_STOPPED.json')

$snapshot1 = @(Get-Snapshot -Base $Root)
Start-Sleep -Milliseconds 250
$snapshot2 = @(Get-Snapshot -Base $Root)
$snapshotJson1 = $snapshot1 | ConvertTo-Json -Compress -Depth 5
$snapshotJson2 = $snapshot2 | ConvertTo-Json -Compress -Depth 5
$postMarkerMutationCount = if($snapshotJson1 -ceq $snapshotJson2) { 0 } else { 1 }

$finalFiles = @(Get-ChildItem -LiteralPath $Root -Recurse -File -Force)
$finalDirectories = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Directory -Force)
$manifestCsvRows = @(Import-Csv -LiteralPath $manifestCsv)
$manifestJsonRows = @(Get-Content -LiteralPath $manifestJson -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String)
$payloadNow = @(Get-PayloadRows -Base $Root -Excluded $Controls)
$payloadMap = @{}
foreach($row in $payloadNow) { $payloadMap[$row.relative_path] = $row }
$manifestMismatch = 0
foreach($row in $manifestJsonRows) {
    if(-not $payloadMap.ContainsKey($row.relative_path)) { $manifestMismatch++; continue }
    $got = $payloadMap[$row.relative_path]
    if(([int64]$row.bytes -ne [int64]$got.bytes) -or ($row.sha256 -cne $got.sha256) -or ([string]$row.mtime_utc_ticks -cne [string]$got.mtime_utc_ticks)) { $manifestMismatch++ }
}
$csvJsonMismatch = 0
for($index=0;$index -lt $manifestJsonRows.Count;$index++) {
    $a = $manifestCsvRows[$index]
    $b = $manifestJsonRows[$index]
    if(($a.relative_path -cne $b.relative_path) -or ([int64]$a.bytes -ne [int64]$b.bytes) -or ($a.sha256 -cne $b.sha256) -or ([string]$a.mtime_utc_ticks -cne [string]$b.mtime_utc_ticks)) { $csvJsonMismatch++ }
}
$marker = Get-Item -LiteralPath (Join-Path $Root 'WRITE_STOPPED.json') -Force
$otherItems = @((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force | Where-Object { $_.FullName -ne $marker.FullName })
$latestOtherTicks = ($otherItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks }).Count
$adsCount = 0
foreach($file in $finalFiles) {
    $adsCount += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -ne ':$DATA' }).Count
}
$reparseCount = @(@((Get-Item -LiteralPath $Root -Force)) + @(Get-ChildItem -LiteralPath $Root -Recurse -Force) | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
$unreadableJson = 0
foreach($file in @($finalFiles | Where-Object Extension -eq '.json')) {
    try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding utf8 | ConvertFrom-Json -DateKind String }
    catch { $unreadableJson++ }
}
$audit = [ordered]@{
    handoff_id = 'A-R113-P067-SA2-DIRECT-BUILD-R11A-20260827'
    verdict = 'ROOT_ACCEPT_LOCAL_SA2_PASS_READY_FOR_MAIN_REVIEW_AND_ATOMIC_COMMIT_AUTH'
    payload_count = $payloadNow.Count
    control_count = 4
    ordinary_count = $finalFiles.Count
    directory_count_including_root = $finalDirectories.Count
    manifest_csv_rows = $manifestCsvRows.Count
    manifest_json_rows = $manifestJsonRows.Count
    csv_json_mismatch_count = $csvJsonMismatch
    manifest_fs_mismatch_count = $manifestMismatch
    missing_payload_count = @($manifestJsonRows | Where-Object { -not $payloadMap.ContainsKey($_.relative_path) }).Count
    extra_payload_count = @($payloadNow | Where-Object { $_.relative_path -notin @($manifestJsonRows.relative_path) }).Count
    readonly_file_count = @($finalFiles | Where-Object IsReadOnly).Count
    readonly_directory_count = @($finalDirectories | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReadOnly }).Count
    write_stopped_ticks = $marker.LastWriteTimeUtc.Ticks.ToString()
    write_stopped_margin_ticks = ($marker.LastWriteTimeUtc.Ticks - $latestOtherTicks).ToString()
    items_at_or_after_marker_excluding_marker = $atOrAfter
    postmarker_content_or_attribute_mutation_count = $postMarkerMutationCount
    ads_count = $adsCount
    unauthorized_cache_dir_count = @($finalDirectories | Where-Object { $_.Name -in @('__pycache__','.pytest_cache') }).Count
    pyc_count = @($finalFiles | Where-Object Extension -eq '.pyc').Count
    reparse_count = $reparseCount
    json_parse_failure_count = $unreadableJson
    authorized_texcache_present = (Test-Path -LiteralPath (Join-Path $Root 'texcache') -PathType Container)
    source = [ordered]@{ bytes=(Get-Item -LiteralPath $Source).Length; sha256=(Get-Sha256 $Source) }
    wrapper = [ordered]@{ bytes=(Get-Item -LiteralPath $Wrapper).Length; sha256=(Get-Sha256 $Wrapper) }
    pdf = [ordered]@{ bytes=(Get-Item -LiteralPath $Pdf).Length; sha256=(Get-Sha256 $Pdf) }
    tex_process_count = @(Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue).Count
    git_head = (& git -C $Worktree rev-parse HEAD).Trim()
    git_status_lines = @(& git -C $Worktree status --porcelain=v1)
    postmarker_zero_write = ($postMarkerMutationCount -eq 0)
}
if($audit.payload_count -ne $payload.Count -or $audit.control_count -ne 4 -or $audit.ordinary_count -ne ($payload.Count + 4)) { throw 'final count equation failed' }
if($audit.manifest_csv_rows -ne $payload.Count -or $audit.manifest_json_rows -ne $payload.Count) { throw 'manifest denominator failed' }
if($audit.csv_json_mismatch_count -ne 0 -or $audit.manifest_fs_mismatch_count -ne 0 -or $audit.missing_payload_count -ne 0 -or $audit.extra_payload_count -ne 0) { throw 'manifest identity closure failed' }
if($audit.readonly_file_count -ne $audit.ordinary_count -or $audit.readonly_directory_count -ne $audit.directory_count_including_root) { throw 'readonly closure failed' }
if([int64]$audit.write_stopped_margin_ticks -le 0 -or $audit.items_at_or_after_marker_excluding_marker -ne 0 -or -not $audit.postmarker_zero_write) { throw 'marker closure failed' }
if($audit.ads_count -ne 0 -or $audit.unauthorized_cache_dir_count -ne 0 -or $audit.pyc_count -ne 0 -or $audit.reparse_count -ne 0 -or $audit.json_parse_failure_count -ne 0) { throw 'filesystem hygiene failed' }
if($audit.source.sha256 -ne $ExpectedSourceSha -or $audit.wrapper.sha256 -ne $ExpectedWrapperSha -or $audit.pdf.sha256 -ne $ExpectedPdfSha -or $audit.tex_process_count -ne 0) { throw 'external identity/process closure failed' }
$auditPath = Join-Path $External 'POST_SEAL_AUDIT.json'
$audit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $auditPath -Encoding utf8NoBOM
Write-Output ($audit | ConvertTo-Json -Compress -Depth 8)
