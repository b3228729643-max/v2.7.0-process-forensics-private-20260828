param(
  [Parameter(Mandatory=$true)][string]$Root
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Get-Sha256([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function Get-RelativeForward([string]$Base, [string]$Path) {
  return ([IO.Path]::GetRelativePath($Base, $Path) -replace '\\','/')
}

$resolvedRoot = [IO.Path]::GetFullPath($Root)
$controlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','PRESEAL_VALIDATION.json','WRITE_STOPPED.json')
$allFiles = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File)
$payloadFiles = @($allFiles | Where-Object { $controlNames -notcontains $_.Name } | Sort-Object FullName)
$manifestCsv = @(Import-Csv -LiteralPath ([IO.Path]::Combine($resolvedRoot,'PAYLOAD_MANIFEST.csv')) -Encoding UTF8)
$manifestJson = Get-Content -LiteralPath ([IO.Path]::Combine($resolvedRoot,'PAYLOAD_MANIFEST.json')) -Raw -Encoding UTF8 | ConvertFrom-Json
$preseal = Get-Content -LiteralPath ([IO.Path]::Combine($resolvedRoot,'PRESEAL_VALIDATION.json')) -Raw -Encoding UTF8 | ConvertFrom-Json
$markerPath = [IO.Path]::Combine($resolvedRoot,'WRITE_STOPPED.json')
$marker = Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json

$errors = [Collections.Generic.List[string]]::new()
if ($manifestCsv.Count -ne $payloadFiles.Count) { $errors.Add('csv-count') }
if ($manifestJson.rows.Count -ne $payloadFiles.Count) { $errors.Add('json-count') }
if ([int]$manifestJson.payload_count -ne $payloadFiles.Count) { $errors.Add('json-declared-count') }
if ([int]$preseal.payload_count -ne $payloadFiles.Count) { $errors.Add('preseal-count') }
if ([int]$marker.payload_count -ne $payloadFiles.Count) { $errors.Add('marker-payload-count') }
if ([int]$marker.control_count -ne 4) { $errors.Add('marker-control-count') }
if ([int]$marker.ordinary_count -ne $allFiles.Count) { $errors.Add('marker-ordinary-count') }

$duplicateCsv = @($manifestCsv | Group-Object relative_path | Where-Object { $_.Count -ne 1 })
$duplicateJson = @($manifestJson.rows | Group-Object relative_path | Where-Object { $_.Count -ne 1 })
if ($duplicateCsv.Count -ne 0) { $errors.Add('csv-duplicate') }
if ($duplicateJson.Count -ne 0) { $errors.Add('json-duplicate') }

for ($i = 0; $i -lt $payloadFiles.Count; $i++) {
  $file = $payloadFiles[$i]
  $rel = Get-RelativeForward $resolvedRoot $file.FullName
  $csv = $manifestCsv[$i]
  $json = $manifestJson.rows[$i]
  $sha = Get-Sha256 $file.FullName
  $ticks = $file.LastWriteTimeUtc.Ticks.ToString()
  if ($csv.relative_path -cne $rel -or $json.relative_path -cne $rel) { $errors.Add("path:$i") }
  if ($csv.bytes -cne $file.Length.ToString() -or $json.bytes.ToString() -cne $file.Length.ToString()) { $errors.Add("bytes:$rel") }
  if ($csv.sha256 -cne $sha -or $json.sha256 -cne $sha) { $errors.Add("sha:$rel") }
  if ($csv.mtime_utc_ticks -cne $ticks -or $json.mtime_utc_ticks -cne $ticks) { $errors.Add("ticks:$rel") }
}

$allDirs = @((Get-Item -LiteralPath $resolvedRoot -Force)) + @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -Directory)
$readonlyFileFailures = @($allFiles | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$readonlyDirFailures = @($allDirs | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
if ($readonlyFileFailures.Count -ne 0) { $errors.Add('file-readonly') }
if ($readonlyDirFailures.Count -ne 0) { $errors.Add('dir-readonly') }

$markerItem = Get-Item -LiteralPath $markerPath -Force
$othersAtOrAfter = @($allFiles | Where-Object { $_.FullName -cne $markerItem.FullName -and $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks })
if ($othersAtOrAfter.Count -ne 0) { $errors.Add('marker-not-strict-latest') }

$jsonParseFailures = [Collections.Generic.List[string]]::new()
foreach ($file in @($allFiles | Where-Object { $_.Extension -ieq '.json' })) {
  try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8 | ConvertFrom-Json }
  catch { $jsonParseFailures.Add((Get-RelativeForward $resolvedRoot $file.FullName)) }
}
if ($jsonParseFailures.Count -ne 0) { $errors.Add('json-parse') }

$ads = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File | ForEach-Object { Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue | Where-Object { $_.Stream -ne ':$DATA' } })
$reparse = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force | Where-Object { $_.Attributes -band [IO.FileAttributes]::ReparsePoint })
$unexpectedCache = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force | Where-Object {
  $rel = Get-RelativeForward $resolvedRoot $_.FullName
  $outsideAuthorizedTexcache = -not ($rel -eq 'texcache' -or $rel.StartsWith('texcache/'))
  $outsideAuthorizedTexcache -and ($_.Name -eq '__pycache__' -or $_.Extension -in @('.pyc','.pyo'))
})
if ($ads.Count -ne 0) { $errors.Add('ads') }
if ($reparse.Count -ne 0) { $errors.Add('reparse') }
if ($unexpectedCache.Count -ne 0) { $errors.Add('unexpected-cache-pyc') }

$authorizedTexcacheFiles = @(Get-ChildItem -LiteralPath ([IO.Path]::Combine($resolvedRoot,'texcache')) -Recurse -Force -File -ErrorAction SilentlyContinue)
$maxOtherTicks = ($allFiles | Where-Object { $_.FullName -cne $markerItem.FullName } | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks

[pscustomobject]@{
  status = $(if ($errors.Count -eq 0) { 'PASS' } else { 'FAIL' })
  resolved_root = $resolvedRoot
  payload_count = $payloadFiles.Count
  control_count = 4
  ordinary_count = $allFiles.Count
  manifest_csv_rows = $manifestCsv.Count
  manifest_json_rows = $manifestJson.rows.Count
  duplicate_csv_paths = $duplicateCsv.Count
  duplicate_json_paths = $duplicateJson.Count
  identity_error_count = @($errors | Where-Object { $_ -match '^(path|bytes|sha|ticks):' }).Count
  readonly_file_count = $allFiles.Count - $readonlyFileFailures.Count
  readonly_file_total = $allFiles.Count
  readonly_dir_count = $allDirs.Count - $readonlyDirFailures.Count
  readonly_dir_total = $allDirs.Count
  write_stopped_unique_count = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File -Filter 'WRITE_STOPPED.json').Count
  write_stopped_ticks = $markerItem.LastWriteTimeUtc.Ticks.ToString()
  max_other_ticks = $maxOtherTicks.ToString()
  write_stopped_margin_ticks = ($markerItem.LastWriteTimeUtc.Ticks - $maxOtherTicks).ToString()
  files_at_or_after_marker_excluding_marker = $othersAtOrAfter.Count
  postmarker_content_or_attribute_write_count = $othersAtOrAfter.Count
  json_parse_failure_count = $jsonParseFailures.Count
  ads_count = $ads.Count
  reparse_count = $reparse.Count
  unexpected_cache_or_pyc_count = $unexpectedCache.Count
  authorized_texcache_file_count = $authorizedTexcacheFiles.Count
  error_count = $errors.Count
  errors = @($errors)
} | ConvertTo-Json -Depth 7
