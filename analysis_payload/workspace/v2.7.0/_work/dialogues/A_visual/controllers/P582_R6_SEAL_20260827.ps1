$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827'
$manifestCsv = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $root 'PAYLOAD_MANIFEST.json'
$writeStopped = Join-Path $root 'WRITE_STOPPED.json'
$utf8 = [Text.UTF8Encoding]::new($false)
$controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')

foreach ($control in @($manifestCsv,$manifestJson,$writeStopped)) {
  if (Test-Path -LiteralPath $control) { throw "Control already exists: $control" }
}

function Get-Sha256([string]$Path) {
  return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

function Get-ExtensionCounts($Files) {
  $counts = [ordered]@{}
  foreach ($file in $Files) {
    $extension = if ([string]::IsNullOrEmpty($file.Extension)) { '[no_extension]' } else { $file.Extension.TrimStart('.').ToLowerInvariant() }
    if (-not $counts.Contains($extension)) { $counts[$extension] = 0 }
    $counts[$extension]++
  }
  return $counts
}

function Merge-Counts($Left,$Right) {
  $merged = [ordered]@{}
  foreach ($key in @($Left.Keys)) { $merged[$key] = [int]$Left[$key] }
  foreach ($key in @($Right.Keys)) {
    if (-not $merged.Contains($key)) { $merged[$key] = 0 }
    $merged[$key] += [int]$Right[$key]
  }
  return $merged
}

$payloadFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object { $controls -notcontains $_.Name } | Sort-Object FullName)
if ($payloadFiles.Count -eq 0) { throw 'Payload denominator is empty.' }
$rows = foreach ($file in $payloadFiles) {
  $relative = [IO.Path]::GetRelativePath($root,$file.FullName).Replace('\','/')
  [ordered]@{
    relative_path = $relative
    bytes = $file.Length.ToString()
    sha256 = Get-Sha256 $file.FullName
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
    mtime_utc_7digit = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
  }
}
if (@($rows.relative_path | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'Duplicate payload relative path.' }

$csvText = ($rows | ConvertTo-Csv -NoTypeInformation) -join "`r`n"
[IO.File]::WriteAllText($manifestCsv,$csvText + "`r`n",$utf8)
$jsonText = $rows | ConvertTo-Json -Depth 4
[IO.File]::WriteAllText($manifestJson,$jsonText + "`n",$utf8)

$csvRows = @(Import-Csv -LiteralPath $manifestCsv)
$jsonRows = @(Get-Content -Raw -LiteralPath $manifestJson | ConvertFrom-Json)
if ($csvRows.Count -ne $payloadFiles.Count -or $jsonRows.Count -ne $payloadFiles.Count) { throw 'Manifest denominator mismatch.' }
$livePayload = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object { $controls -notcontains $_.Name } | Sort-Object FullName)
if ($livePayload.Count -ne $payloadFiles.Count) { throw 'Payload changed during seal preparation.' }

$csvByPath = @{}
foreach ($row in $csvRows) { $csvByPath[$row.relative_path] = $row }
$jsonByPath = @{}
foreach ($row in $jsonRows) { $jsonByPath[$row.relative_path] = $row }
foreach ($file in $livePayload) {
  $relative = [IO.Path]::GetRelativePath($root,$file.FullName).Replace('\','/')
  if (-not $csvByPath.ContainsKey($relative) -or -not $jsonByPath.ContainsKey($relative)) { throw "Manifest missing $relative" }
  $sha = Get-Sha256 $file.FullName
  $ticks = $file.LastWriteTimeUtc.Ticks.ToString()
  foreach ($row in @($csvByPath[$relative],$jsonByPath[$relative])) {
    if ($row.bytes.ToString() -ne $file.Length.ToString() -or $row.sha256 -ne $sha -or $row.mtime_utc_ticks.ToString() -ne $ticks) {
      throw "Manifest identity mismatch: $relative"
    }
  }
}

foreach ($file in @($livePayload + (Get-Item -LiteralPath $manifestCsv) + (Get-Item -LiteralPath $manifestJson))) {
  $file.IsReadOnly = $true
}

$maxOtherTicks = (@($livePayload + (Get-Item -LiteralPath $manifestCsv) + (Get-Item -LiteralPath $manifestJson)) | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
while ([DateTime]::UtcNow.Ticks -le $maxOtherTicks) { Start-Sleep -Milliseconds 1 }

$payloadExtensions = Get-ExtensionCounts $livePayload
$controlExtensions = [ordered]@{ csv = 1; json = 2 }
$ordinaryExtensions = Merge-Counts $payloadExtensions $controlExtensions
$writeStoppedRecord = [ordered]@{
  uid = 'FIG-P582-01'
  handoff_id = 'A-R109-P582-SA2-DIRECT-BUILD-R6-20260827'
  round = 'STRICT_R6_SA2_COORDINATE_PATCH_R109_DIRECT_BUILD_20260827'
  status = 'LOCAL_SA2_PASS_AWAIT_ATOMIC_COMMIT_AUTHORIZATION'
  payload_file_count = $livePayload.Count
  manifest_control_file_count = 2
  write_stopped_control_file_count = 1
  control_file_count = 3
  ordinary_file_total = $livePayload.Count + 3
  payload_extensions = $payloadExtensions
  control_extensions = $controlExtensions
  ordinary_extensions = $ordinaryExtensions
  manifest_csv_sha256 = Get-Sha256 $manifestCsv
  manifest_json_sha256 = Get-Sha256 $manifestJson
  max_payload_or_manifest_mtime_utc_ticks = $maxOtherTicks.ToString()
  sealed_at_utc = [DateTime]::UtcNow.ToString('o')
  post_write_policy = 'WRITE_STOPPED is the final root write; root-internal postseal files are forbidden.'
}
[IO.File]::WriteAllText($writeStopped,($writeStoppedRecord | ConvertTo-Json -Depth 8) + "`n",$utf8)
(Get-Item -LiteralPath $writeStopped).IsReadOnly = $true

$wstopItem = Get-Item -LiteralPath $writeStopped
if ($wstopItem.LastWriteTimeUtc.Ticks -le $maxOtherTicks) { throw 'WRITE_STOPPED is not strictly latest.' }
[pscustomobject]@{
  payload = $livePayload.Count
  controls = 3
  ordinary = $livePayload.Count + 3
  manifest_csv_sha256 = Get-Sha256 $manifestCsv
  manifest_json_sha256 = Get-Sha256 $manifestJson
  write_stopped_sha256 = Get-Sha256 $writeStopped
  write_stopped_ticks = $wstopItem.LastWriteTimeUtc.Ticks.ToString()
  max_other_ticks = $maxOtherTicks.ToString()
  margin_ticks = ($wstopItem.LastWriteTimeUtc.Ticks - $maxOtherTicks).ToString()
} | ConvertTo-Json -Depth 4
