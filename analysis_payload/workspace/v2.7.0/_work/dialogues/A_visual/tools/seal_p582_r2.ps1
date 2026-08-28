$ErrorActionPreference = 'Stop'

$root = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826')
$manifestCsv = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifestJson = Join-Path $root 'PAYLOAD_MANIFEST.json'
$writeStopped = Join-Path $root 'WRITE_STOPPED.json'
$excluded = @('PAYLOAD_MANIFEST.csv', 'PAYLOAD_MANIFEST.json', 'WRITE_STOPPED.json')

foreach ($path in @($manifestCsv, $manifestJson, $writeStopped)) {
  if (Test-Path -LiteralPath $path) { throw "Control already exists; one-time seal refused: $path" }
}

$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File | Where-Object {
  $relative = [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\','/')
  $relative -notin $excluded
} | Sort-Object FullName)

$rows = foreach ($file in $payloadFiles) {
  $relative = [IO.Path]::GetRelativePath($root, $file.FullName).Replace('\','/')
  [ordered]@{
    relative_path = $relative
    bytes = $file.Length
    sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
    mtime_utc_7digit = $file.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ')
  }
}

$rows | Export-Csv -LiteralPath $manifestCsv -NoTypeInformation -Encoding utf8NoBOM
$rows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $manifestJson -Encoding utf8NoBOM

$preMarkerFiles = @(Get-ChildItem -LiteralPath $root -Recurse -Force -File)
foreach ($file in $preMarkerFiles) { $file.IsReadOnly = $true }
$maxPreMarkerTicks = ($preMarkerFiles | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1).LastWriteTimeUtc.Ticks
while ([DateTime]::UtcNow.Ticks -le $maxPreMarkerTicks) { [Threading.Thread]::SpinWait(20000) }

$marker = [ordered]@{
  uid = 'FIG-P582-01'
  round = 'STRICT_R2_SA2_FONT_PATCH_R108_DIRECT_BUILD_20260826'
  status = 'LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1'
  payload_file_count = $rows.Count
  manifest_control_file_count = 2
  write_stopped_control_file_count = 1
  control_file_count = 3
  ordinary_file_total = $rows.Count + 3
  manifest_csv_sha256 = (Get-FileHash -LiteralPath $manifestCsv -Algorithm SHA256).Hash
  manifest_json_sha256 = (Get-FileHash -LiteralPath $manifestJson -Algorithm SHA256).Hash
  max_payload_or_manifest_mtime_utc_ticks = $maxPreMarkerTicks.ToString()
  created_at_utc = [DateTime]::UtcNow.ToString('o')
  post_marker_root_writes_authorized = 0
}
$marker | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $writeStopped -Encoding utf8NoBOM
(Get-Item -LiteralPath $writeStopped).IsReadOnly = $true
