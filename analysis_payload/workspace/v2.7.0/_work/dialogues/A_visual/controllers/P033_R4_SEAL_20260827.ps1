$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R4_SA2_R3_COORDINATE_DIRECT_BUILD_R110_20260827'
$csvPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$jsonPath = Join-Path $root 'PAYLOAD_MANIFEST.json'
$wstopPath = Join-Path $root 'WRITE_STOPPED.json'
$expectedPayload = 122
$controllerSha = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash

foreach ($control in @($csvPath, $jsonPath, $wstopPath)) {
  if (Test-Path -LiteralPath $control) { throw "Control already exists: $control" }
}

$payloadFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Sort-Object FullName)
if ($payloadFiles.Count -ne $expectedPayload) { throw "Expected $expectedPayload payload files, found $($payloadFiles.Count)." }
if (@($payloadFiles | Where-Object { $_.Name -match '\.py[co]$' -or $_.Directory.Name -eq '__pycache__' }).Count -ne 0) {
  throw 'Python cache artifacts remain before seal.'
}

$payloadRows = foreach ($file in $payloadFiles) {
  [ordered]@{
    relative_path = [IO.Path]::GetRelativePath($root, $file.FullName).Replace('\', '/')
    bytes = $file.Length
    sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
  }
}

$payloadRows | Export-Csv -LiteralPath $csvPath -NoTypeInformation -Encoding utf8NoBOM
$payloadRows | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $jsonPath -Encoding utf8NoBOM

$csvRows = @(Import-Csv -LiteralPath $csvPath)
$jsonRows = @(Get-Content -LiteralPath $jsonPath -Raw | ConvertFrom-Json)
if ($csvRows.Count -ne $expectedPayload -or $jsonRows.Count -ne $expectedPayload) { throw 'Manifest row count mismatch.' }
$csvCanon = @($csvRows | ForEach-Object { $_.relative_path + '|' + $_.bytes + '|' + $_.sha256 + '|' + $_.mtime_utc_ticks })
$jsonCanon = @($jsonRows | ForEach-Object { $_.relative_path + '|' + $_.bytes + '|' + $_.sha256 + '|' + $_.mtime_utc_ticks })
if (@(Compare-Object $csvCanon $jsonCanon).Count -ne 0) { throw 'CSV and JSON manifests differ.' }

foreach ($row in $csvRows) {
  $path = Join-Path $root ($row.relative_path.Replace('/', '\'))
  $item = Get-Item -LiteralPath $path
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  if ($item.Length.ToString() -ne $row.bytes -or $hash -ne $row.sha256 -or $item.LastWriteTimeUtc.Ticks.ToString() -ne $row.mtime_utc_ticks) {
    throw "Manifest-to-filesystem mismatch: $($row.relative_path)"
  }
}

$allBeforeMarker = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
foreach ($file in $allBeforeMarker) { $file.IsReadOnly = $true }
$allDirs = @((Get-Item -LiteralPath $root)) + @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force)
foreach ($dir in $allDirs) { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
if (@(Get-ChildItem -LiteralPath $root -Recurse -File -Force | Where-Object { -not $_.IsReadOnly }).Count -ne 0) {
  throw 'A pre-marker file is not read-only.'
}

$maxTicks = (@(Get-ChildItem -LiteralPath $root -Recurse -File -Force) | Measure-Object LastWriteTimeUtc -Maximum).Maximum.Ticks
while ([DateTime]::UtcNow.Ticks -le $maxTicks) { Start-Sleep -Milliseconds 10 }
Start-Sleep -Milliseconds 100

$wstop = [ordered]@{
  round = 'STRICT_R4_SA2_R3_COORDINATE_DIRECT_BUILD_R110_20260827'
  stopped_at_utc = [DateTime]::UtcNow.ToString('o')
  payload_file_count = $expectedPayload
  manifest_control_file_count = 2
  write_stopped_control_file_count = 1
  control_file_count = 3
  ordinary_file_total = $expectedPayload + 3
  manifest_csv_sha256 = (Get-FileHash -LiteralPath $csvPath -Algorithm SHA256).Hash
  manifest_json_sha256 = (Get-FileHash -LiteralPath $jsonPath -Algorithm SHA256).Hash
  controller_path = $PSCommandPath
  controller_sha256 = $controllerSha
  terminal_status = 'LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1'
  post_marker_root_writes = 0
}
$wstop | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $wstopPath -Encoding utf8NoBOM
(Get-Item -LiteralPath $wstopPath).IsReadOnly = $true

$marker = Get-Item -LiteralPath $wstopPath
if ($marker.LastWriteTimeUtc.Ticks -le $maxTicks) { throw 'WRITE_STOPPED is not strictly latest.' }
Write-Output ("payload=$expectedPayload ordinary=$($expectedPayload + 3) margin_ticks=$($marker.LastWriteTimeUtc.Ticks - $maxTicks)")
