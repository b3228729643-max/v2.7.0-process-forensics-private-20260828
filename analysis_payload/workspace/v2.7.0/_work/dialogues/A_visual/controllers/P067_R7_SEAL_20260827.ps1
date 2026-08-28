Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R7_SA2_CDF_STEP_HANDLER_R112_DIRECT_BUILD_20260827'
$auditPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\A-R112-P067-SA2-DIRECT-BUILD-R7-20260827_ROOT_AUDIT.json'
$markerTemp = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\controllers\P067_R7_WRITE_STOPPED.tmp.json'
$controlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','PRESEAL_VALIDATION.json','WRITE_STOPPED.json')

function Get-RelativePath([string]$Base, [string]$Full) {
  return [IO.Path]::GetRelativePath($Base, $Full).Replace('\','/')
}

function Get-Identity([IO.FileInfo]$File) {
  [ordered]@{
    relative_path = Get-RelativePath $root $File.FullName
    bytes = $File.Length.ToString()
    sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $File.FullName).Hash
    mtime_utc_ticks = $File.LastWriteTimeUtc.Ticks.ToString()
  }
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'R7 root absent' }
if (@(Get-ChildItem -LiteralPath $root -File -Recurse | Where-Object { $_.Name -in $controlNames }).Count -ne 0) { throw 'seal controls already present' }
if (Test-Path -LiteralPath $markerTemp) { throw 'external marker temp already exists' }

$payloadFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse | Sort-Object { Get-RelativePath $root $_.FullName })
if ($payloadFiles.Count -ne 135) { throw "payload count expected 135, got $($payloadFiles.Count)" }
$payload = @($payloadFiles | ForEach-Object { Get-Identity $_ })
$duplicate = @($payload | Group-Object -Property { $_['relative_path'] } | Where-Object { $_.Count -ne 1 })
if ($duplicate.Count -ne 0) { throw 'duplicate payload paths' }

$csvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$jsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$presealPath = Join-Path $root 'PRESEAL_VALIDATION.json'
$payload | ForEach-Object { [pscustomobject]$_ } | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8NoBOM
$payload | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $jsonPath -Encoding utf8NoBOM

$csvRows = @(Import-Csv -LiteralPath $csvPath)
$jsonRows = @(Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json)
if ($csvRows.Count -ne 135 -or $jsonRows.Count -ne 135) { throw 'manifest row count mismatch' }
$csvByPath = @{}; foreach ($row in $csvRows) { if ($csvByPath.ContainsKey($row.relative_path)) { throw 'CSV duplicate path' }; $csvByPath[$row.relative_path] = $row }
$jsonByPath = @{}; foreach ($row in $jsonRows) { if ($jsonByPath.ContainsKey($row.relative_path)) { throw 'JSON duplicate path' }; $jsonByPath[$row.relative_path] = $row }
$manifestMismatch = 0
foreach ($expected in $payload) {
  $path = [string]$expected.relative_path
  if (-not $csvByPath.ContainsKey($path) -or -not $jsonByPath.ContainsKey($path)) { $manifestMismatch++; continue }
  foreach ($field in @('bytes','sha256','mtime_utc_ticks')) {
    if ([string]$csvByPath[$path].$field -ne [string]$expected[$field]) { $manifestMismatch++ }
    if ([string]$jsonByPath[$path].$field -ne [string]$expected[$field]) { $manifestMismatch++ }
  }
}
if ($manifestMismatch -ne 0) { throw "manifest mismatch $manifestMismatch" }

$preseal = [ordered]@{
  handoff_id = 'A-R112-P067-SA2-DIRECT-BUILD-R7-20260827'
  status = 'PRESEAL_PASS'
  payload_count = 135
  premarker_control_count = 3
  projected_ordinary_count = 139
  manifest_rows_csv = $csvRows.Count
  manifest_rows_json = $jsonRows.Count
  duplicate_path_count = 0
  manifest_identity_mismatch_count = 0
  source_sha256 = '2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920'
  pdf_sha256 = '73FBE000AC977A7E270D4834A0F9B81AC24C851BAE72B38503ACCAEBC844E108'
  N = 115
  C_N_2 = 6555
  object_manual_rows = 115
  relation_manual_rows = 16
  hard_failure_count = 0
}
$preseal | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $presealPath -Encoding utf8NoBOM

$beforeMarkerFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse)
if ($beforeMarkerFiles.Count -ne 138) { throw "premarker ordinary expected 138, got $($beforeMarkerFiles.Count)" }
foreach ($file in $beforeMarkerFiles) { $file.IsReadOnly = $true }
$directories = @(Get-ChildItem -LiteralPath $root -Directory -Recurse | Sort-Object FullName -Descending)
foreach ($dir in $directories) { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
(Get-Item -LiteralPath $root).Attributes = (Get-Item -LiteralPath $root).Attributes -bor [IO.FileAttributes]::ReadOnly

$maxPremarkerTicks = ($beforeMarkerFiles | Measure-Object { $_.LastWriteTimeUtc.Ticks } -Maximum).Maximum
$targetTicks = [Math]::Max([DateTime]::UtcNow.Ticks, [int64]$maxPremarkerTicks + 1000000)
$marker = [ordered]@{
  handoff_id = 'A-R112-P067-SA2-DIRECT-BUILD-R7-20260827'
  status = 'WRITE_STOPPED'
  payload_file_count = 135
  manifest_control_file_count = 2
  preseal_control_file_count = 1
  write_stopped_control_file_count = 1
  control_file_count = 4
  ordinary_file_total = 139
  max_premarker_mtime_utc_ticks = ([int64]$maxPremarkerTicks).ToString()
  write_stopped_mtime_utc_ticks = ([int64]$targetTicks).ToString()
  root_content_writes_after_marker = 0
  root_attribute_writes_after_marker = 0
}
$marker | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $markerTemp -Encoding utf8NoBOM
(Get-Item -LiteralPath $markerTemp).LastWriteTimeUtc = [DateTime]::new([int64]$targetTicks, [DateTimeKind]::Utc)
(Get-Item -LiteralPath $markerTemp).IsReadOnly = $true
Move-Item -LiteralPath $markerTemp -Destination (Join-Path $root 'WRITE_STOPPED.json')

# Read-only external audit.  No root content or attribute mutation is allowed below.
$snapshotA = @(Get-ChildItem -LiteralPath $root -File -Recurse | Sort-Object FullName | ForEach-Object { [pscustomobject]@{ path=$_.FullName; ticks=$_.LastWriteTimeUtc.Ticks; attrs=[int]$_.Attributes; bytes=$_.Length } })
$finalFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse)
$finalDirs = @((Get-Item -LiteralPath $root)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse)
$markerFile = Get-Item -LiteralPath (Join-Path $root 'WRITE_STOPPED.json')
$otherFiles = @($finalFiles | Where-Object Name -ne 'WRITE_STOPPED.json')
$atOrAfter = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerFile.LastWriteTimeUtc.Ticks })
$readonlyFiles = @($finalFiles | Where-Object IsReadOnly).Count
$readonlyDirs = @($finalDirs | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0 }).Count
$ads = 0
foreach ($file in $finalFiles) { $ads += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object Stream -ne ':$DATA').Count }
$cache = @($finalFiles | Where-Object { $_.Extension -eq '.pyc' -or $_.Name -in @('.DS_Store','Thumbs.db') -or $_.DirectoryName -match '(__pycache__)' }).Count
$reparse = @((Get-ChildItem -LiteralPath $root -Force -Recurse) | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
$jsonParseFailures = 0
foreach ($file in @($finalFiles | Where-Object Extension -eq '.json')) { try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { $jsonParseFailures++ } }
$manifestPayload = @($finalFiles | Where-Object { $_.Name -notin $controlNames } | Sort-Object { Get-RelativePath $root $_.FullName })
$manifestNowMismatch = 0
if ($manifestPayload.Count -ne 135) { $manifestNowMismatch++ }
foreach ($file in $manifestPayload) {
  $path = Get-RelativePath $root $file.FullName
  if (-not $csvByPath.ContainsKey($path) -or -not $jsonByPath.ContainsKey($path)) { $manifestNowMismatch++; continue }
  $sha = (Get-FileHash -Algorithm SHA256 -LiteralPath $file.FullName).Hash
  foreach ($row in @($csvByPath[$path],$jsonByPath[$path])) {
    if ([string]$row.bytes -ne $file.Length.ToString()) { $manifestNowMismatch++ }
    if ([string]$row.sha256 -ne $sha) { $manifestNowMismatch++ }
    if ([string]$row.mtime_utc_ticks -ne $file.LastWriteTimeUtc.Ticks.ToString()) { $manifestNowMismatch++ }
  }
}
$snapshotB = @(Get-ChildItem -LiteralPath $root -File -Recurse | Sort-Object FullName | ForEach-Object { [pscustomobject]@{ path=$_.FullName; ticks=$_.LastWriteTimeUtc.Ticks; attrs=[int]$_.Attributes; bytes=$_.Length } })
$snapshotDiff = Compare-Object ($snapshotA | ConvertTo-Json -Compress) ($snapshotB | ConvertTo-Json -Compress)
$audit = [ordered]@{
  status = 'ROOT_ACCEPT_LOCAL_SA2_PASS'
  root = $root
  payload_count = $manifestPayload.Count
  control_count = @($finalFiles | Where-Object { $_.Name -in $controlNames }).Count
  ordinary_count = $finalFiles.Count
  manifest_csv_rows = $csvRows.Count
  manifest_json_rows = $jsonRows.Count
  manifest_fs_identity_mismatch_count = $manifestNowMismatch
  readonly_files = $readonlyFiles
  total_files = $finalFiles.Count
  readonly_directories = $readonlyDirs
  total_directories = $finalDirs.Count
  write_stopped_unique = (@($finalFiles | Where-Object Name -eq 'WRITE_STOPPED.json').Count -eq 1)
  write_stopped_strictly_latest = ($atOrAfter.Count -eq 0)
  write_stopped_margin_ticks = ($markerFile.LastWriteTimeUtc.Ticks - ($otherFiles | Measure-Object { $_.LastWriteTimeUtc.Ticks } -Maximum).Maximum)
  files_at_or_after_marker_excluding_marker = $atOrAfter.Count
  postmarker_content_or_attribute_snapshot_differences = @($snapshotDiff).Count
  json_parse_failures = $jsonParseFailures
  alternate_data_stream_count = $ads
  prohibited_cache_or_pyc_count = $cache
  reparse_point_count = $reparse
  hard_gate_pass = ($finalFiles.Count -eq 139 -and $manifestPayload.Count -eq 135 -and $manifestNowMismatch -eq 0 -and $readonlyFiles -eq $finalFiles.Count -and $readonlyDirs -eq $finalDirs.Count -and $atOrAfter.Count -eq 0 -and @($snapshotDiff).Count -eq 0 -and $jsonParseFailures -eq 0 -and $ads -eq 0 -and $cache -eq 0 -and $reparse -eq 0)
}
$audit | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $auditPath -Encoding utf8NoBOM
if (-not $audit.hard_gate_pass) { throw 'external root audit failed' }
$audit | ConvertTo-Json -Depth 8
