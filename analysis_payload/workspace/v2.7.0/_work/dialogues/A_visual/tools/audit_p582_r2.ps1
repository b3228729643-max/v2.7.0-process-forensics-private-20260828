$ErrorActionPreference = 'Stop'

$root = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826')
$report = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P582_R108_R2_ROOT_AUDIT.json'
$manifestCsvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$writeStoppedPath = Join-Path $root 'WRITE_STOPPED.json'
$excluded = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'WRITE_STOPPED.json')

$csvRows = @(Import-Csv -LiteralPath $manifestCsvPath)
$jsonRows = @(Get-Content -LiteralPath $manifestJsonPath -Raw | ConvertFrom-Json -DateKind String)
$marker = Get-Content -LiteralPath $writeStoppedPath -Raw | ConvertFrom-Json -DateKind String
$ordinary = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File)
$payload = @($ordinary | Where-Object {
  [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\','/') -notin $excluded
})

function New-RowMap([object[]]$Rows) {
  $map = @{}
  foreach ($row in $Rows) {
    if ($map.ContainsKey([string]$row.relative_path)) { throw "duplicate manifest path: $($row.relative_path)" }
    $map[[string]$row.relative_path] = $row
  }
  return $map
}

$csvMap = New-RowMap $csvRows
$jsonMap = New-RowMap $jsonRows
$fsMap = @{}
foreach ($file in $payload) {
  $relative = [IO.Path]::GetRelativePath($root, $file.FullName).Replace('\','/')
  if ($fsMap.ContainsKey($relative)) { throw "duplicate filesystem path: $relative" }
  $fsMap[$relative] = [ordered]@{
    relative_path = $relative
    bytes = $file.Length.ToString()
    sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
    mtime_utc_7digit = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
  }
}

$allPaths = @($csvMap.Keys + $jsonMap.Keys + $fsMap.Keys | Sort-Object -Unique)
$diffs = @()
foreach ($path in $allPaths) {
  if (-not $csvMap.ContainsKey($path) -or -not $jsonMap.ContainsKey($path) -or -not $fsMap.ContainsKey($path)) {
    $diffs += [ordered]@{ path=$path; kind='path_set' }
    continue
  }
  foreach ($field in @('bytes','sha256','mtime_utc_ticks','mtime_utc_7digit')) {
    $a = [string]$csvMap[$path].$field
    $b = [string]$jsonMap[$path].$field
    $c = [string]$fsMap[$path].$field
    if ($a -cne $b -or $a -cne $c) { $diffs += [ordered]@{ path=$path; field=$field; csv=$a; json=$b; fs=$c } }
  }
}

$writeStopped = Get-Item -LiteralPath $writeStoppedPath
$otherFiles = @($ordinary | Where-Object { $_.FullName -cne $writeStopped.FullName })
$maxOtherTicks = ($otherFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc.Ticks
$filesAtOrAfter = @($otherFiles | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $writeStopped.LastWriteTimeUtc.Ticks })
$ads = @()
foreach ($file in $ordinary) {
  $streams = @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -ne ':$DATA' })
  foreach ($stream in $streams) { $ads += [ordered]@{ path=$file.FullName; stream=$stream.Stream; length=$stream.Length } }
}
$reparse = @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
$pyc = @($ordinary | Where-Object { $_.Extension -eq '.pyc' })
$pythonCacheDirs = @(Get-ChildItem -LiteralPath $root -Recurse -Force -Directory | Where-Object { $_.Name -eq '__pycache__' })
$readonly = @($ordinary | Where-Object { $_.IsReadOnly })

$checks = [ordered]@{
  payload_count_matches_marker = $payload.Count -eq [int]$marker.payload_file_count
  manifest_csv_count_matches = $csvRows.Count -eq $payload.Count
  manifest_json_count_matches = $jsonRows.Count -eq $payload.Count
  manifest_and_fs_identity_diff_zero = $diffs.Count -eq 0
  manifest_csv_sha_matches_marker = (Get-FileHash -LiteralPath $manifestCsvPath -Algorithm SHA256).Hash -eq [string]$marker.manifest_csv_sha256
  manifest_json_sha_matches_marker = (Get-FileHash -LiteralPath $manifestJsonPath -Algorithm SHA256).Hash -eq [string]$marker.manifest_json_sha256
  ordinary_count_matches_marker = $ordinary.Count -eq [int]$marker.ordinary_file_total
  ordinary_equals_payload_plus_three_controls = $ordinary.Count -eq ($payload.Count + 3)
  readonly_all = $readonly.Count -eq $ordinary.Count
  ads_zero = $ads.Count -eq 0
  pyc_zero = $pyc.Count -eq 0
  python_cache_dirs_zero = $pythonCacheDirs.Count -eq 0
  reparse_zero = $reparse.Count -eq 0
  write_stopped_strictly_latest = $writeStopped.LastWriteTimeUtc.Ticks -gt $maxOtherTicks
  files_at_or_after_write_stopped_zero = $filesAtOrAfter.Count -eq 0
}
$hardPass = @($checks.Values | Where-Object { -not $_ }).Count -eq 0
$result = [ordered]@{
  uid = 'FIG-P582-01'
  round = 'STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826'
  audited_at_utc = [DateTime]::UtcNow.ToString('o')
  root = $root
  payload_file_count = $payload.Count
  manifest_csv_rows = $csvRows.Count
  manifest_json_rows = $jsonRows.Count
  control_file_count = 3
  ordinary_file_count = $ordinary.Count
  readonly_file_count = $readonly.Count
  identity_diff_count = $diffs.Count
  identity_diffs = $diffs
  ads_count = $ads.Count
  pyc_count = $pyc.Count
  python_cache_dir_count = $pythonCacheDirs.Count
  authorized_texcache_present = Test-Path -LiteralPath (Join-Path $root 'texcache')
  reparse_count = $reparse.Count
  write_stopped_mtime_utc_ticks = $writeStopped.LastWriteTimeUtc.Ticks.ToString()
  max_other_mtime_utc_ticks = $maxOtherTicks.ToString()
  write_stopped_margin_ticks = ($writeStopped.LastWriteTimeUtc.Ticks - $maxOtherTicks).ToString()
  files_at_or_after_write_stopped = $filesAtOrAfter.Count
  checks = $checks
  hard_gate_pass = $hardPass
  status = if ($hardPass) { 'ROOT_ACCEPT_LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1' } else { 'ROOT_REJECT' }
}
$result | ConvertTo-Json -Depth 7 | Set-Content -LiteralPath $report -Encoding utf8NoBOM
Get-Content -LiteralPath $report -Raw
