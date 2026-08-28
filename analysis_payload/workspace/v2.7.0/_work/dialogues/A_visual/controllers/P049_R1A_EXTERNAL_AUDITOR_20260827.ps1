$ErrorActionPreference = 'Stop'

$sourceRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R1_SA2_R168_READONLY_R110_20260827')
$root = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R1A_SA2_R168_READONLY_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827')
$output = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P049-01_R110_R1A_CONTROL_RESEAL_EXTERNAL_AUDIT_20260827.json'
$controls = @('PAYLOAD_MANIFEST.csv', 'SEAL_AUDIT.json', 'WSTOP')

$files = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$dirs = @((Get-Item -LiteralPath $root)) + @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force)
$manifest = @(Import-Csv -LiteralPath (Join-Path $root 'PAYLOAD_MANIFEST.csv'))
$payloadFs = @($files | Where-Object { $controls -notcontains $_.Name })
$manifestMismatches = 0
foreach ($row in $manifest) {
  $path = Join-Path $root ($row.relative_path.Replace('/', '\'))
  if (-not (Test-Path -LiteralPath $path)) { $manifestMismatches++; continue }
  $item = Get-Item -LiteralPath $path
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  if ($item.Length.ToString() -ne $row.bytes -or $hash -ne $row.sha256 -or $item.LastWriteTimeUtc.Ticks.ToString() -ne $row.mtime_utc_ticks) { $manifestMismatches++ }
}
$manifestPaths = @($manifest.relative_path | Sort-Object)
$payloadPaths = @($payloadFs | ForEach-Object { [IO.Path]::GetRelativePath($root, $_.FullName).Replace('\', '/') } | Sort-Object)
$identity = @(Import-Csv -LiteralPath (Join-Path $root 'COPY_IDENTITY.csv'))
$copyMismatch = 0
foreach ($row in $identity) {
  $source = Join-Path $sourceRoot ($row.source_relative_path.Replace('/', '\'))
  $target = Join-Path $root ($row.destination_relative_path.Replace('/', '\'))
  $sourceItem = Get-Item -LiteralPath $source
  $targetItem = Get-Item -LiteralPath $target
  $sourceSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
  $targetSha = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
  if ($row.source_relative_path -ne $row.destination_relative_path -or $sourceItem.Length.ToString() -ne $row.bytes -or $targetItem.Length.ToString() -ne $row.bytes -or $sourceSha -ne $row.sha256 -or $targetSha -ne $row.sha256 -or $sourceItem.LastWriteTimeUtc.Ticks.ToString() -ne $row.mtime_utc_ticks -or $targetItem.LastWriteTimeUtc.Ticks.ToString() -ne $row.mtime_utc_ticks) { $copyMismatch++ }
}

$provenance = Get-Content -LiteralPath (Join-Path $root 'COPY_PROVENANCE.json') -Raw | ConvertFrom-Json
$provenanceMismatch = [int]($provenance.source_root -ne $sourceRoot -or $provenance.target_root -ne $root)
$jsonParseFailures = 0
foreach ($file in $files | Where-Object Extension -eq '.json') { try { Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json | Out-Null } catch { $jsonParseFailures++ } }
$csvParseFailures = 0
foreach ($file in $files | Where-Object Extension -eq '.csv') { try { @(Import-Csv -LiteralPath $file.FullName) | Out-Null } catch { $csvParseFailures++ } }
Add-Type -AssemblyName System.Drawing
$pngParseFailures = 0
foreach ($file in $files | Where-Object Extension -eq '.png') {
  try { $image = [Drawing.Image]::FromFile($file.FullName); $image.Dispose() } catch { $pngParseFailures++ }
}
$ads = 0
foreach ($file in $files) { $ads += @((Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue) | Where-Object Stream -ne ':$DATA').Count }
$reparse = @(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint }).Count
$marker = Get-Item -LiteralPath (Join-Path $root 'WSTOP')
$others = @($files | Where-Object Name -ne 'WSTOP')
$maxOther = ($others | Measure-Object LastWriteTimeUtc -Maximum).Maximum

$result = [ordered]@{
  verdict = 'ROOT_ACCEPT_R1A_SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
  source_root = $sourceRoot
  target_root = $root
  copied_payload_rows = $identity.Count
  copied_payload_identity_mismatch = $copyMismatch
  provenance_mismatch = $provenanceMismatch
  payload_manifest_rows = $manifest.Count
  payload_filesystem_count = $payloadFs.Count
  manifest_path_set_diff = @(Compare-Object $manifestPaths $payloadPaths).Count
  manifest_identity_mismatch = $manifestMismatches
  ordinary_file_count = $files.Count
  control_file_count = $files.Count - $payloadFs.Count
  read_only_files = @($files | Where-Object IsReadOnly).Count
  total_files = $files.Count
  read_only_dirs = @($dirs | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReadOnly }).Count
  total_dirs = $dirs.Count
  json_parse_failures = $jsonParseFailures
  csv_parse_failures = $csvParseFailures
  png_parse_failures = $pngParseFailures
  ads_count = $ads
  pyc_count = @($files | Where-Object { $_.Name -match '\.py[co]$' }).Count
  pycache_dir_count = @($dirs | Where-Object Name -eq '__pycache__').Count
  reparse_count = $reparse
  wstop_strictly_latest = $marker.LastWriteTimeUtc -gt $maxOther
  wstop_margin_ticks = $marker.LastWriteTimeUtc.Ticks - $maxOther.Ticks
  files_at_or_after_marker_excluding_marker = @($others | Where-Object { $_.LastWriteTimeUtc -ge $marker.LastWriteTimeUtc }).Count
  manifest_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'PAYLOAD_MANIFEST.csv') -Algorithm SHA256).Hash
  seal_audit_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'SEAL_AUDIT.json') -Algorithm SHA256).Hash
  wstop_sha256 = (Get-FileHash -LiteralPath (Join-Path $root 'WSTOP') -Algorithm SHA256).Hash
  audited_at_utc = [DateTime]::UtcNow.ToString('o')
}

$hardFailures = @(
  $result.copied_payload_identity_mismatch,
  $result.provenance_mismatch,
  $result.manifest_path_set_diff,
  $result.manifest_identity_mismatch,
  [int]($result.copied_payload_rows -ne 7),
  [int]($result.payload_manifest_rows -ne 9),
  [int]($result.payload_filesystem_count -ne 9),
  [int]($result.ordinary_file_count -ne 12),
  [int]($result.control_file_count -ne 3),
  [int]($result.read_only_files -ne $result.total_files),
  [int]($result.read_only_dirs -ne $result.total_dirs),
  $result.json_parse_failures,
  $result.csv_parse_failures,
  $result.png_parse_failures,
  $result.ads_count,
  $result.pyc_count,
  $result.pycache_dir_count,
  $result.reparse_count,
  [int](-not $result.wstop_strictly_latest),
  $result.files_at_or_after_marker_excluding_marker
  | Where-Object { $_ -ne 0 }
).Count
$result['hard_failure_count'] = $hardFailures
if ($hardFailures -ne 0) { $result.verdict = 'ROOT_REJECT_R1A' }
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $output -Encoding utf8NoBOM
Write-Output ("verdict=$($result.verdict) hard_failures=$hardFailures output=$output")
if ($hardFailures -ne 0) { exit 1 }
