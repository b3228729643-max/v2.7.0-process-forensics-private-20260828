param(
  [Parameter(Mandatory = $true)][string]$EvidenceRoot,
  [Parameter(Mandatory = $true)][string]$ExternalHandoff
)

$ErrorActionPreference = 'Stop'
$expectedRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R14_SA3_FRESH_ISOLATED_R105_20260826'
$expectedExternal = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R105-P608-SA3-FRESH-ISOLATED-20260826__HANDOFF.md'
$resolvedRoot = (Resolve-Path -LiteralPath $EvidenceRoot).Path
$resolvedExternal = (Resolve-Path -LiteralPath $ExternalHandoff).Path
if ($resolvedRoot -cne $expectedRoot) { throw "Unexpected evidence root: $resolvedRoot" }
if ($resolvedExternal -cne $expectedExternal) { throw "Unexpected handoff: $resolvedExternal" }

$crosscheck = Get-Content -LiteralPath (Join-Path $resolvedRoot 'machine_crosscheck.json') -Raw | ConvertFrom-Json
if ([int]$crosscheck.integrity_error_count -ne 0) { throw 'Cannot seal evidence with cross-check errors' }

$cacheDirs = @(Get-ChildItem -LiteralPath $resolvedRoot -Directory -Force -Recurse | Where-Object { $_.Name -in @('__pycache__','.cache','.pytest_cache') })
$pycFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -File -Force -Recurse | Where-Object { $_.Extension -in @('.pyc','.pyo') })
$filesBefore = @(Get-ChildItem -LiteralPath $resolvedRoot -File -Force -Recurse)
$adsBefore = @(
  foreach ($file in $filesBefore) {
    Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue |
      Where-Object { $_.Stream -notin @(':$DATA','$DATA') }
  }
)
if ($cacheDirs.Count -ne 0) { throw "Cache directories found: $($cacheDirs.FullName -join ', ')" }
if ($pycFiles.Count -ne 0) { throw "PYC/PYO files found: $($pycFiles.FullName -join ', ')" }
if ($adsBefore.Count -ne 0) { throw "ADS found before seal: $($adsBefore.FileName -join ', ')" }

$sealAudit = [ordered]@{
  handoff_id = 'A-R105-P608-SA3-FRESH-ISOLATED-20260826'
  evidence_root = $resolvedRoot
  scan_scope = 'exact evidence root recursively'
  ordinary_file_count_before_seal = $filesBefore.Count
  cache_directory_count = $cacheDirs.Count
  pyc_pyo_file_count = $pycFiles.Count
  alternate_data_stream_count = $adsBefore.Count
  machine_crosscheck_error_count = [int]$crosscheck.integrity_error_count
}
$sealAudit | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $resolvedRoot 'SEAL_AUDIT.json') -Encoding utf8

# First freeze all material evidence and the external handoff, then prove that
# representative appends are blocked.  The check log and manifest are created
# afterward and frozen in the final step.
$materialFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -File -Force -Recurse)
foreach ($file in $materialFiles) { $file.IsReadOnly = $true }
(Get-Item -LiteralPath $resolvedExternal).IsReadOnly = $true

$probeTargets = @(
  (Join-Path $resolvedRoot 'RESULT.txt'),
  (Join-Path $resolvedRoot 'SA3_REPORT.md'),
  (Join-Path $resolvedRoot 'HANDOFF.md'),
  $resolvedExternal
)
$probeRows = @()
foreach ($target in $probeTargets) {
  $blocked = 0
  $errorType = ''
  try {
    Add-Content -LiteralPath $target -Value '__FORBIDDEN_POSTSEAL_PROBE__' -ErrorAction Stop
  } catch {
    $blocked = 1
    $errorType = $_.Exception.GetType().FullName
  }
  if ($blocked -ne 1) { throw "Post-seal append unexpectedly succeeded: $target" }
  $probeRows += [ordered]@{ target = $target; append_blocked_int = $blocked; error_type = $errorType }
}
$postsealPath = Join-Path $resolvedRoot 'POSTSEAL_WRITE_CHECKS.json'
([ordered]@{
  handoff_id = 'A-R105-P608-SA3-FRESH-ISOLATED-20260826'
  material_target_count = $probeRows.Count
  blocked_material_target_count = @($probeRows | Where-Object { $_.append_blocked_int -eq 1 }).Count
  checks = $probeRows
}) | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $postsealPath -Encoding utf8

$manifestPath = Join-Path $resolvedRoot 'SEALED_MANIFEST.csv'
$manifestRows = @(
  Get-ChildItem -LiteralPath $resolvedRoot -File -Force -Recurse |
    Where-Object { $_.FullName -cne $manifestPath } |
    Sort-Object FullName |
    ForEach-Object {
      [pscustomobject]@{
        relative_path = [System.IO.Path]::GetRelativePath($resolvedRoot, $_.FullName)
        bytes = $_.Length
        sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $_.FullName).Hash
      }
    }
)
$manifestRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8

foreach ($file in @(Get-ChildItem -LiteralPath $resolvedRoot -File -Force -Recurse)) { $file.IsReadOnly = $true }
(Get-Item -LiteralPath $resolvedExternal).IsReadOnly = $true

$finalProbeTargets = @($manifestPath, $postsealPath)
$finalProbeRows = @()
foreach ($target in $finalProbeTargets) {
  $blocked = 0
  $errorType = ''
  try {
    Add-Content -LiteralPath $target -Value '__FORBIDDEN_FINAL_POSTSEAL_PROBE__' -ErrorAction Stop
  } catch {
    $blocked = 1
    $errorType = $_.Exception.GetType().FullName
  }
  if ($blocked -ne 1) { throw "Final post-seal append unexpectedly succeeded: $target" }
  $finalProbeRows += [ordered]@{ target = $target; append_blocked_int = $blocked; error_type = $errorType }
}

$manifestCheckErrors = @()
foreach ($row in @(Import-Csv -LiteralPath $manifestPath)) {
  $path = Join-Path $resolvedRoot $row.relative_path
  if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
    $manifestCheckErrors += "missing:$($row.relative_path)"
    continue
  }
  $actualHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash
  if ($actualHash -cne $row.sha256) { $manifestCheckErrors += "hash:$($row.relative_path)" }
  if ([string](Get-Item -LiteralPath $path).Length -cne [string]$row.bytes) { $manifestCheckErrors += "bytes:$($row.relative_path)" }
}
if ($manifestCheckErrors.Count -ne 0) { throw "Manifest verification failed: $($manifestCheckErrors -join ', ')" }

$finalFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -File -Force -Recurse)
$notReadOnly = @($finalFiles | Where-Object { -not $_.IsReadOnly })
$adsAfter = @(
  foreach ($file in $finalFiles) {
    Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue |
      Where-Object { $_.Stream -notin @(':$DATA','$DATA') }
  }
)
if ($notReadOnly.Count -ne 0) { throw "Ordinary files not read-only: $($notReadOnly.FullName -join ', ')" }
if (-not (Get-Item -LiteralPath $resolvedExternal).IsReadOnly) { throw 'External handoff is not read-only' }
if ($adsAfter.Count -ne 0) { throw "ADS found after seal: $($adsAfter.FileName -join ', ')" }

$final = [ordered]@{
  handoff_id = 'A-R105-P608-SA3-FRESH-ISOLATED-20260826'
  evidence_root = $resolvedRoot
  manifest_path = $manifestPath
  manifest_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $manifestPath).Hash
  manifest_entry_count = $manifestRows.Count
  ordinary_file_count_after_seal = $finalFiles.Count
  ordinary_file_not_readonly_count = $notReadOnly.Count
  external_handoff_readonly_int = [int](Get-Item -LiteralPath $resolvedExternal).IsReadOnly
  alternate_data_stream_count_after_seal = $adsAfter.Count
  cache_directory_count_after_seal = @(Get-ChildItem -LiteralPath $resolvedRoot -Directory -Force -Recurse | Where-Object { $_.Name -in @('__pycache__','.cache','.pytest_cache') }).Count
  pyc_pyo_file_count_after_seal = @(Get-ChildItem -LiteralPath $resolvedRoot -File -Force -Recurse | Where-Object { $_.Extension -in @('.pyc','.pyo') }).Count
  manifest_verification_error_count = $manifestCheckErrors.Count
  material_append_blocked_count = @($probeRows | Where-Object { $_.append_blocked_int -eq 1 }).Count
  final_append_blocked_count = @($finalProbeRows | Where-Object { $_.append_blocked_int -eq 1 }).Count
  final_append_checks = $finalProbeRows
  report_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $resolvedRoot 'SA3_REPORT.md')).Hash
  result_txt_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $resolvedRoot 'RESULT.txt')).Hash
  result_json_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath (Join-Path $resolvedRoot 'RESULT.json')).Hash
  handoff_sha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $resolvedExternal).Hash
}
$final | ConvertTo-Json -Depth 6
