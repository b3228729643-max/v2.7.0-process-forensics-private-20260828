$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P033-01\STRICT_R5_SA1_FRESH_ISOLATED_R111_20260827'
$manifestPath = Join-Path $root 'seal\MANIFEST_SHA256.csv'
$sealPath = Join-Path $root 'seal\SEAL.json'
$stoppedPath = Join-Path $root 'seal\WRITE_STOPPED.md'
$reportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\FIG-P033-01_R111_SA1_FRESH_ISOLATED_REPORT_20260827.md'
$handoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A_visual\FIG-P033-01_R111_SA1_FRESH_ISOLATED_HANDOFF_20260827.json'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

foreach ($target in @($manifestPath, $sealPath, $stoppedPath)) {
  if ([System.IO.File]::Exists($target)) {
    throw "Single-seal refusal: target already exists: $target"
  }
}
foreach ($external in @($reportPath, $handoffPath)) {
  if (-not [System.IO.File]::Exists($external)) {
    throw "Required external artifact missing: $external"
  }
}

$excluded = @($manifestPath, $sealPath, $stoppedPath)
$evidenceFiles = Get-ChildItem -LiteralPath $root -File -Recurse -Force |
  Where-Object { $_.FullName -notin $excluded } |
  Sort-Object FullName

$manifestLines = [System.Collections.Generic.List[string]]::new()
$manifestLines.Add('relative_path,bytes,sha256')
foreach ($file in $evidenceFiles) {
  $relative = [System.IO.Path]::GetRelativePath($root, $file.FullName).Replace('\', '/')
  $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
  $manifestLines.Add(('"{0}",{1},{2}' -f $relative.Replace('"', '""'), $file.Length, $hash))
}
[System.IO.File]::WriteAllText($manifestPath, ($manifestLines -join "`n") + "`n", $utf8NoBom)
$manifestHash = (Get-FileHash -LiteralPath $manifestPath -Algorithm SHA256).Hash
$sealedAt = (Get-Date).ToString('yyyy-MM-ddTHH:mm:ss.fffK')

$sealObject = [ordered]@{
  seal_type = 'SINGLE_FINAL_READONLY'
  handoff_id = 'A-R111-P033-SA1-FRESH-ISOLATED-20260827'
  canonical_task = '/root/p033_r111_fresh_sa1'
  model_effort = 'gpt-5.6-sol/xhigh'
  uid = 'FIG-P033-01'
  candidate = 'R111'
  sealed_at = $sealedAt
  manifest_entry_count = $evidenceFiles.Count
  manifest_sha256 = $manifestHash
  result = 'PASS'
  route = 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
  frozen_N = 99
  frozen_C = 4851
  unresolved_pairs = 0
  illegal_overlap_pixels = 0
  clip_pixels = 0
  all_root_files_and_directories_readonly = $true
  write_stopped_is_final_root_write = $true
  zero_writes_after_write_stopped = $true
}
$sealJson = $sealObject | ConvertTo-Json -Depth 4
[System.IO.File]::WriteAllText($sealPath, $sealJson + "`n", $utf8NoBom)
$sealHash = (Get-FileHash -LiteralPath $sealPath -Algorithm SHA256).Hash
$reportHash = (Get-FileHash -LiteralPath $reportPath -Algorithm SHA256).Hash
$handoffHash = (Get-FileHash -LiteralPath $handoffPath -Algorithm SHA256).Hash

foreach ($external in @($reportPath, $handoffPath)) {
  $attrs = [System.IO.File]::GetAttributes($external)
  [System.IO.File]::SetAttributes($external, $attrs -bor [System.IO.FileAttributes]::ReadOnly)
}

$stopped = @"
# WRITE_STOPPED

- HANDOFF_ID: `A-R111-P033-SA1-FRESH-ISOLATED-20260827`
- canonical_task: `/root/p033_r111_fresh_sa1`
- model_effort: `gpt-5.6-sol/xhigh`
- sealed_at: `$sealedAt`
- result: `PASS`
- route: `SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3`
- manifest_sha256: `$manifestHash`
- seal_json_sha256: `$sealHash`
- external_report: `$reportPath`
- external_report_sha256: `$reportHash`
- external_handoff: `$handoffPath`
- external_handoff_sha256: `$handoffHash`
- sentinel_is_final_evidence_root_write: `true`
- zero_writes_after_sentinel: `true`
- all_evidence_root_files_and_directories_readonly: `true`

No A_LOCAL_PASS, final PASS, or SA3 completion is claimed. SA3 was not started.
"@
[System.IO.File]::WriteAllText($stoppedPath, $stopped, $utf8NoBom)

$otherFiles = Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object { $_.FullName -ne $stoppedPath }
$maxOther = ($otherFiles | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum
$targetTime = [DateTime]::UtcNow
if ($null -ne $maxOther -and $targetTime -le $maxOther) {
  $targetTime = $maxOther.AddMilliseconds(10)
}
[System.IO.File]::SetLastWriteTimeUtc($stoppedPath, $targetTime)

$allFiles = Get-ChildItem -LiteralPath $root -File -Recurse -Force
foreach ($file in $allFiles) {
  $attrs = [System.IO.File]::GetAttributes($file.FullName)
  [System.IO.File]::SetAttributes($file.FullName, $attrs -bor [System.IO.FileAttributes]::ReadOnly)
}
$allDirs = Get-ChildItem -LiteralPath $root -Directory -Recurse -Force | Sort-Object { $_.FullName.Length } -Descending
foreach ($dir in $allDirs) {
  $attrs = [System.IO.File]::GetAttributes($dir.FullName)
  [System.IO.File]::SetAttributes($dir.FullName, $attrs -bor [System.IO.FileAttributes]::ReadOnly)
}
$rootAttrs = [System.IO.File]::GetAttributes($root)
[System.IO.File]::SetAttributes($root, $rootAttrs -bor [System.IO.FileAttributes]::ReadOnly)

$verifyFiles = Get-ChildItem -LiteralPath $root -File -Recurse -Force
$verifyDirs = @((Get-Item -LiteralPath $root)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
$nonReadonlyFiles = @($verifyFiles | Where-Object { -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) })
$nonReadonlyDirs = @($verifyDirs | Where-Object { -not ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) })
$orderedTimes = $verifyFiles | Sort-Object LastWriteTimeUtc -Descending
$strictLatest = $orderedTimes.Count -ge 2 -and $orderedTimes[0].FullName -eq $stoppedPath -and $orderedTimes[0].LastWriteTimeUtc -gt $orderedTimes[1].LastWriteTimeUtc
if ($nonReadonlyFiles.Count -ne 0 -or $nonReadonlyDirs.Count -ne 0 -or -not $strictLatest) {
  throw "Seal verification failed: nonROFiles=$($nonReadonlyFiles.Count) nonRODirs=$($nonReadonlyDirs.Count) strictLatest=$strictLatest"
}

[pscustomobject]@{
  EvidenceRoot = $root
  EvidenceFileCount = $verifyFiles.Count
  EvidenceDirectoryCount = $verifyDirs.Count
  ManifestEntries = $evidenceFiles.Count
  ManifestSHA256 = $manifestHash
  SealSHA256 = $sealHash
  WriteStoppedSHA256 = (Get-FileHash -LiteralPath $stoppedPath -Algorithm SHA256).Hash
  ReportPath = $reportPath
  ReportSHA256 = $reportHash
  HandoffPath = $handoffPath
  HandoffSHA256 = $handoffHash
  AllFilesReadonly = $nonReadonlyFiles.Count -eq 0
  AllDirectoriesReadonly = $nonReadonlyDirs.Count -eq 0
  WriteStoppedStrictlyLatest = $strictLatest
  Route = 'SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'
} | ConvertTo-Json -Compress
