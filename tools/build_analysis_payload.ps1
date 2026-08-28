param(
  [string]$WorkspaceRoot = 'D:\Users\ASUS\Desktop\机器学习',
  [string]$ProjectRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0',
  [string]$ExportRoot = 'D:\Users\ASUS\Desktop\机器学习\github_exports\v2.7.0-process-forensics-private-20260828'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$payloadRoot = Join-Path $ExportRoot 'analysis_payload\workspace'
$inventoryRoot = Join-Path $ExportRoot 'inventory'
$visualRoot = Join-Path $ExportRoot 'selected_visual_evidence'
foreach ($path in @($payloadRoot, $inventoryRoot, $visualRoot)) {
  $null = [IO.Directory]::CreateDirectory($path)
}

$textExtensions = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach ($extension in @(
  '.md','.txt','.json','.jsonl','.ndjson','.csv','.tsv','.psv',
  '.ps1','.py','.tex','.sty','.cls','.mjs','.js','.xml','.xhtml','.html',
  '.log','.aux','.toc','.idx','.ind','.ilg','.fls','.fdb_latexmk',
  '.patch','.diff','.sha256','.sample','.ledger','.marker','.stage','.gitignore'
)) { $null = $textExtensions.Add($extension) }

$cacheSegmentPattern = '(?i)(^|[\\/])(\.git|texcache|texmf-var|texmf-cache|luatex-cache|luaotfload_cache|__pycache__)([\\/]|$)'
$goalPackagePrefix = '统计学习方法讲义_v2.7.0_Codex_Goal执行包_固定工作目录与完整交付版\'

function Test-LikelyText([string]$LiteralPath) {
  $stream = [IO.File]::Open($LiteralPath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
  try {
    $length = [Math]::Min(4096, [int]$stream.Length)
    if ($length -eq 0) { return $true }
    $buffer = [byte[]]::new($length)
    $read = $stream.Read($buffer, 0, $length)
    for ($index = 0; $index -lt $read; $index++) {
      if ($buffer[$index] -eq 0) { return $false }
    }
    return $true
  } finally {
    $stream.Dispose()
  }
}

function Copy-AnalysisFile([string]$Source, [string]$Destination) {
  $parent = [IO.Path]::GetDirectoryName($Destination)
  $null = [IO.Directory]::CreateDirectory($parent)
  [IO.File]::Copy($Source, $Destination, $true)
  $attributes = [IO.File]::GetAttributes($Destination)
  if (($attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) {
    [IO.File]::SetAttributes($Destination, $attributes -band (-bnot [IO.FileAttributes]::ReadOnly))
  }
}

$inventoryRows = [Collections.Generic.List[object]]::new()
$copyFailures = [Collections.Generic.List[object]]::new()
$projectFiles = @(Get-ChildItem -LiteralPath $ProjectRoot -File -Recurse -Force -ErrorAction Stop)

foreach ($file in $projectFiles) {
  $relative = [IO.Path]::GetRelativePath($ProjectRoot, $file.FullName)
  $extension = $file.Extension.ToLowerInvariant()
  $isCache = $relative -match $cacheSegmentPattern
  $isGoalPackage = $relative.StartsWith($goalPackagePrefix, [StringComparison]::Ordinal)
  $isText = $textExtensions.Contains($extension)
  if ([string]::IsNullOrEmpty($extension) -and $file.Length -le 5MB -and -not $isCache) {
    $isText = Test-LikelyText $file.FullName
  }

  $include = $false
  $reason = ''
  if ($isGoalPackage) {
    $include = $true
    $reason = 'goal-input-package'
  } elseif ($isCache) {
    $reason = 'generated-cache-excluded-from-web-repo'
  } elseif ($isText) {
    $include = $true
    $reason = 'model-readable-process-or-source-text'
  } else {
    $reason = 'large-or-binary-listed-in-full-inventory-and-local-full-archive'
  }

  if ($include) {
    $destination = Join-Path $payloadRoot (Join-Path 'v2.7.0' $relative)
    try {
      Copy-AnalysisFile $file.FullName $destination
    } catch {
      $include = $false
      $reason = 'copy-failed-see-copy_failures.csv'
      $copyFailures.Add([pscustomobject]@{
        relative_path = $relative
        source_path = $file.FullName
        error = $_.Exception.Message
      })
    }
  }

  $inventoryRows.Add([pscustomobject][ordered]@{
    relative_path = $relative.Replace([string][char]92, [string][char]47)
    bytes = [int64]$file.Length
    last_write_utc = $file.LastWriteTimeUtc.ToString('o')
    extension = if ([string]::IsNullOrEmpty($extension)) { '[none]' } else { $extension }
    included_in_analysis_payload = $include
    classification = $reason
  })
}

$inventoryPath = Join-Path $inventoryRoot 'FULL_WORKSPACE_FILE_INVENTORY.csv'
$inventoryRows | Export-Csv -LiteralPath $inventoryPath -NoTypeInformation -Encoding utf8NoBOM
$copyFailures | Export-Csv -LiteralPath (Join-Path $inventoryRoot 'COPY_FAILURES.csv') -NoTypeInformation -Encoding utf8NoBOM

$extensionSummary = $inventoryRows |
  Group-Object extension |
  ForEach-Object {
    $measure = $_.Group | Measure-Object bytes -Sum
    [pscustomobject]@{ extension = $_.Name; files = $measure.Count; bytes = [int64]$measure.Sum }
  } |
  Sort-Object bytes -Descending
$extensionSummary | Export-Csv -LiteralPath (Join-Path $inventoryRoot 'EXTENSION_SUMMARY.csv') -NoTypeInformation -Encoding utf8NoBOM

$largest = $inventoryRows | Sort-Object bytes -Descending | Select-Object -First 500
$largest | Export-Csv -LiteralPath (Join-Path $inventoryRoot 'LARGEST_500_FILES.csv') -NoTypeInformation -Encoding utf8NoBOM

$topLevel = $inventoryRows |
  Group-Object { ($_.relative_path -split '/')[0] } |
  ForEach-Object {
    $measure = $_.Group | Measure-Object bytes -Sum
    [pscustomobject]@{ top_level = $_.Name; files = $measure.Count; bytes = [int64]$measure.Sum }
  } |
  Sort-Object bytes -Descending
$topLevel | Export-Csv -LiteralPath (Join-Path $inventoryRoot 'TOP_LEVEL_SIZE_SUMMARY.csv') -NoTypeInformation -Encoding utf8NoBOM

$runtimeFiles = @(
  'AGENTS.md','GOAL.md','PROMPT_RUNTIME_CORE.md','CONTEXT_CAPSULE.md','CURRENT_TASK.json'
)
foreach ($name in $runtimeFiles) {
  $source = Join-Path $WorkspaceRoot $name
  if (Test-Path -LiteralPath $source -PathType Leaf) {
    Copy-AnalysisFile $source (Join-Path $payloadRoot (Join-Path 'runtime_context' $name))
  }
}

$selectedRoots = [ordered]@{
  'P126_R116_SA1_FAIL' = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R18_SA1_FRESH_ISOLATED_R116_20260828'
  'P126_R19_STATIC_PATCH' = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_R116_20260828'
  'P690_R116_SA2_PASS' = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P690-01\sa2_r116_r168_readonly_adjudication_v1'
}
foreach ($entry in $selectedRoots.GetEnumerator()) {
  if (-not (Test-Path -LiteralPath $entry.Value -PathType Container)) { continue }
  foreach ($file in @(Get-ChildItem -LiteralPath $entry.Value -File -Recurse -Force)) {
    $relative = [IO.Path]::GetRelativePath($entry.Value, $file.FullName)
    if ($relative -match $cacheSegmentPattern) { continue }
    Copy-AnalysisFile $file.FullName (Join-Path $visualRoot (Join-Path $entry.Key $relative))
  }
}

$officialPdf = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r116_fullbook\main_full.pdf'
if (Test-Path -LiteralPath $officialPdf -PathType Leaf) {
  Copy-AnalysisFile $officialPdf (Join-Path $visualRoot 'OFFICIAL_R116_main_full.pdf')
}

$payloadFiles = @(Get-ChildItem -LiteralPath (Join-Path $ExportRoot 'analysis_payload') -File -Recurse -Force)
$visualFiles = @(Get-ChildItem -LiteralPath $visualRoot -File -Recurse -Force)
$summary = [ordered]@{
  schema = 'V270_PROCESS_FORENSICS_PACKAGE_BUILD_V1'
  generated_utc = [DateTime]::UtcNow.ToString('o')
  source_project_root = $ProjectRoot
  source_files = $projectFiles.Count
  source_bytes = [int64](($projectFiles | Measure-Object Length -Sum).Sum)
  analysis_payload_files = $payloadFiles.Count
  analysis_payload_bytes = [int64](($payloadFiles | Measure-Object Length -Sum).Sum)
  selected_visual_files = $visualFiles.Count
  selected_visual_bytes = [int64](($visualFiles | Measure-Object Length -Sum).Sum)
  copy_failures = $copyFailures.Count
}
[IO.File]::WriteAllText((Join-Path $inventoryRoot 'PACKAGE_BUILD_SUMMARY.json'), ($summary | ConvertTo-Json -Depth 5), [Text.UTF8Encoding]::new($false))
$summary | ConvertTo-Json -Depth 5
