$ErrorActionPreference = 'Stop'

$sourceRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R1_SA2_R168_READONLY_R110_20260827')
$targetRoot = [IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P049-01\STRICT_R1A_SA2_R168_READONLY_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827')
$sourceManifest = Join-Path $sourceRoot 'PREMARKER_MANIFEST.sha256'
$copyIdentityPath = Join-Path $targetRoot 'COPY_IDENTITY.csv'
$copyProvenancePath = Join-Path $targetRoot 'COPY_PROVENANCE.json'
$manifestPath = Join-Path $targetRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $targetRoot 'SEAL_AUDIT.json'
$wstopPath = Join-Path $targetRoot 'WSTOP'
$controllerSha = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash

if (Test-Path -LiteralPath $targetRoot) { throw 'The authorized R1A target root already exists.' }
if (-not (Test-Path -LiteralPath $sourceManifest)) { throw 'The frozen R1 manifest is missing.' }

$bound = @()
foreach ($line in Get-Content -LiteralPath $sourceManifest) {
  if ($line -match '^([A-Fa-f0-9]{64}) \*(.+)$') {
    $relative = $Matches[2]
    if (-not [IO.Path]::IsPathRooted($relative)) {
      $bound += [pscustomobject]@{ sha256 = $Matches[1].ToUpperInvariant(); relative_path = $relative }
    }
  }
}
if ($bound.Count -ne 7) { throw "Expected seven local payload bindings, found $($bound.Count)." }
if (@($bound.relative_path | Sort-Object -Unique).Count -ne 7) { throw 'Duplicate local payload path in frozen R1 manifest.' }

New-Item -ItemType Directory -Path $targetRoot | Out-Null
$identityRows = @()
foreach ($entry in $bound) {
  $source = [IO.Path]::GetFullPath((Join-Path $sourceRoot $entry.relative_path))
  $target = [IO.Path]::GetFullPath((Join-Path $targetRoot $entry.relative_path))
  if (-not $source.StartsWith($sourceRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe source path.' }
  if (-not $target.StartsWith($targetRoot + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) { throw 'Unsafe target path.' }
  $sourceItem = Get-Item -LiteralPath $source
  $sourceSha = (Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash
  if ($sourceSha -ne $entry.sha256) { throw "Frozen source payload SHA mismatch: $($entry.relative_path)" }
  $targetParent = Split-Path -Parent $target
  if (-not (Test-Path -LiteralPath $targetParent)) { New-Item -ItemType Directory -Path $targetParent -Force | Out-Null }
  Copy-Item -LiteralPath $source -Destination $target
  (Get-Item -LiteralPath $target).LastWriteTimeUtc = $sourceItem.LastWriteTimeUtc
  $targetItem = Get-Item -LiteralPath $target
  $targetSha = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
  if ($targetItem.Length -ne $sourceItem.Length -or $targetSha -ne $sourceSha -or $targetItem.LastWriteTimeUtc.Ticks -ne $sourceItem.LastWriteTimeUtc.Ticks) {
    throw "Source-to-target identity mismatch: $($entry.relative_path)"
  }
  $identityRows += [ordered]@{
    source_relative_path = $entry.relative_path.Replace('\', '/')
    destination_relative_path = $entry.relative_path.Replace('\', '/')
    bytes = $sourceItem.Length
    sha256 = $sourceSha
    mtime_utc_ticks = $sourceItem.LastWriteTimeUtc.Ticks.ToString()
  }
}
$identityRows | Export-Csv -LiteralPath $copyIdentityPath -NoTypeInformation -Encoding utf8NoBOM

$provenance = [ordered]@{
  round = 'STRICT_R1A_SA2_R168_READONLY_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827'
  handoff_id = 'A-R110-P049-SA2-R168-READONLY-R1A-CONTROL-RESEAL-20260827'
  source_root = $sourceRoot
  target_root = $targetRoot
  source_manifest = [IO.Path]::GetFullPath($sourceManifest)
  source_manifest_sha256 = (Get-FileHash -LiteralPath $sourceManifest -Algorithm SHA256).Hash
  controller_path = [IO.Path]::GetFullPath($PSCommandPath)
  controller_sha256 = $controllerSha
  invocation_count = 1
  retry_count = 0
  copied_payload_count = 7
  business_review_rerun = 0
  created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$provenance | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $copyProvenancePath -Encoding utf8NoBOM

$payloadFiles = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -File -Force | Sort-Object FullName)
if ($payloadFiles.Count -ne 9) { throw "Expected nine final payload files, found $($payloadFiles.Count)." }
$payloadRows = foreach ($file in $payloadFiles) {
  [ordered]@{
    relative_path = [IO.Path]::GetRelativePath($targetRoot, $file.FullName).Replace('\', '/')
    bytes = $file.Length
    sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
  }
}
$payloadRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8NoBOM

$manifestRows = @(Import-Csv -LiteralPath $manifestPath)
if ($manifestRows.Count -ne 9 -or @($manifestRows.relative_path | Sort-Object -Unique).Count -ne 9) { throw 'New manifest count or uniqueness failure.' }
$manifestMismatches = 0
foreach ($row in $manifestRows) {
  $path = Join-Path $targetRoot ($row.relative_path.Replace('/', '\'))
  $item = Get-Item -LiteralPath $path
  $hash = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash
  if ($item.Length.ToString() -ne $row.bytes -or $hash -ne $row.sha256 -or $item.LastWriteTimeUtc.Ticks.ToString() -ne $row.mtime_utc_ticks) { $manifestMismatches++ }
}
if ($manifestMismatches -ne 0) { throw 'New manifest-to-filesystem identity failure.' }

$sealAudit = [ordered]@{
  round = 'STRICT_R1A_SA2_R168_READONLY_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827'
  payload_file_count = 9
  copied_payload_count = 7
  added_identity_payload_count = 2
  manifest_control_file_count = 1
  seal_audit_control_file_count = 1
  write_stopped_control_file_count = 1
  control_file_count = 3
  ordinary_file_total = 12
  source_to_destination_identity_mismatch = 0
  manifest_to_filesystem_identity_mismatch = 0
  manifest_path_duplicate_count = 0
  source_manifest_sha256 = (Get-FileHash -LiteralPath $sourceManifest -Algorithm SHA256).Hash
  new_manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash
  business_review_rerun = 0
  tex_invocations = 0
  created_at_utc = [DateTime]::UtcNow.ToString('o')
}
$sealAudit | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $sealAuditPath -Encoding utf8NoBOM

$preMarkerFiles = @(Get-ChildItem -LiteralPath $targetRoot -Recurse -File -Force)
if ($preMarkerFiles.Count -ne 11) { throw "Expected eleven pre-marker files, found $($preMarkerFiles.Count)." }
foreach ($file in $preMarkerFiles) { $file.IsReadOnly = $true }
$allDirs = @((Get-Item -LiteralPath $targetRoot)) + @(Get-ChildItem -LiteralPath $targetRoot -Recurse -Directory -Force)
foreach ($dir in $allDirs) { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
if (@(Get-ChildItem -LiteralPath $targetRoot -Recurse -File -Force | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'A pre-marker file remains writable.' }
if (@($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) }).Count -ne 0) { throw 'A target directory remains writable by attribute gate.' }

$maxTicks = ($preMarkerFiles | Measure-Object LastWriteTimeUtc -Maximum).Maximum.Ticks
while ([DateTime]::UtcNow.Ticks -le $maxTicks) { Start-Sleep -Milliseconds 10 }
Start-Sleep -Milliseconds 100
$wstop = [ordered]@{
  schema = 'R168_READONLY_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
  round = 'STRICT_R1A_SA2_R168_READONLY_R110_EVIDENCE_ONLY_CONTROL_RESEAL_20260827'
  handoff_id = 'A-R110-P049-SA2-R168-READONLY-R1A-CONTROL-RESEAL-20260827'
  result = 'SA2_NO_SOURCE_CHANGE_READY_FOR_FRESH_SA1'
  payload_file_count = 9
  control_file_count = 3
  ordinary_file_total = 12
  manifest_sha256 = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash
  seal_audit_sha256 = (Get-FileHash -LiteralPath $sealAuditPath -Algorithm SHA256).Hash
  stopped_at_utc = [DateTime]::UtcNow.ToString('o')
  postmarker_root_writes = 0
}
$wstop | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $wstopPath -Encoding utf8NoBOM
(Get-Item -LiteralPath $wstopPath).IsReadOnly = $true
$marker = Get-Item -LiteralPath $wstopPath
if ($marker.LastWriteTimeUtc.Ticks -le $maxTicks) { throw 'WSTOP is not strictly latest.' }
Write-Output ("copied=7 payload=9 ordinary=12 margin_ticks=$($marker.LastWriteTimeUtc.Ticks - $maxTicks)")
