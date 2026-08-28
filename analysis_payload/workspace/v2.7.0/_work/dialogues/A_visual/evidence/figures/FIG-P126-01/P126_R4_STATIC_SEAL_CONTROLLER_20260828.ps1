$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R4_SA2_STATIC_LEGEND_SEGMENT_PATCH_R115_20260828'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4_STATIC_WRITE_STOPPED_STAGE_20260828.tmp'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R4_STATIC_POSTSEAL_AUDIT_20260828.json'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$handoff = 'A-R115-P126-SA2-STATIC-LEGEND-SEGMENT-PATCH-20260828'
$expectedSourceBytes = 4356L
$expectedSourceSha = '3185834A7D4DEAC1595C244DA626FF52B5308E733AFD851E8FF508037C51ED75'
$payloadNames = @(
  'SOURCE_IDENTITY.json',
  'EXACT_AUTHORIZED_DIFF.patch',
  'STATIC_PROJECTION.json',
  'GIT_BOUNDARY.txt',
  'STATIC_REPORT.md',
  'HANDOFF.md'
)
$manifestName = 'PAYLOAD_MANIFEST.csv'
$auditName = 'SEAL_AUDIT.json'
$markerName = 'WRITE_STOPPED'
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-FileSha([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Get-RelativeForward([string]$Base, [string]$Path) {
  return ([IO.Path]::GetRelativePath($Base, $Path) -replace '\\', '/')
}

function Get-TreeSnapshot([string]$Base) {
  $rows = [Collections.Generic.List[string]]::new()
  $rootItem = Get-Item -LiteralPath $Base -Force
  $rows.Add(('D<TAB>.<TAB>{0}<TAB>{1}<TAB>{2}' -f $rootItem.CreationTimeUtc.Ticks, $rootItem.LastWriteTimeUtc.Ticks, [int]$rootItem.Attributes).Replace('<TAB>', "`t"))
  foreach ($dir in @(Get-ChildItem -LiteralPath $Base -Directory -Recurse -Force | Sort-Object FullName)) {
    $relative = Get-RelativeForward $Base $dir.FullName
    $rows.Add(('D<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}' -f $relative, $dir.CreationTimeUtc.Ticks, $dir.LastWriteTimeUtc.Ticks, [int]$dir.Attributes).Replace('<TAB>', "`t"))
  }
  foreach ($file in @(Get-ChildItem -LiteralPath $Base -File -Recurse -Force | Sort-Object FullName)) {
    $relative = Get-RelativeForward $Base $file.FullName
    $rows.Add(('F<TAB>{0}<TAB>{1}<TAB>{2}<TAB>{3}<TAB>{4}<TAB>{5}' -f $relative, $file.Length, (Get-FileSha $file.FullName), $file.CreationTimeUtc.Ticks, $file.LastWriteTimeUtc.Ticks, [int]$file.Attributes).Replace('<TAB>', "`t"))
  }
  $bytes = $utf8NoBom.GetBytes(($rows -join "`n") + "`n")
  return [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'static root missing' }
foreach ($path in @($stage, $resultPath)) {
  if (Test-Path -LiteralPath $path) { throw "external artifact already exists: $path" }
}
$sourceItem = Get-Item -LiteralPath $source
if ($sourceItem.Length -ne $expectedSourceBytes) { throw 'source bytes mismatch' }
if ((Get-FileSha $source) -cne $expectedSourceSha) { throw 'source SHA mismatch' }

$initialFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
if ($initialFiles.Count -ne 6) { throw "initial payload count mismatch: $($initialFiles.Count)" }
$initialNames = @($initialFiles | ForEach-Object { Get-RelativeForward $root $_.FullName } | Sort-Object)
$expectedNames = @($payloadNames | Sort-Object)
if (@(Compare-Object -ReferenceObject $expectedNames -DifferenceObject $initialNames -CaseSensitive).Count -ne 0) { throw 'initial payload set mismatch' }

$payloadRows = [Collections.Generic.List[object]]::new()
foreach ($name in $payloadNames) {
  $path = Join-Path $root $name
  $item = Get-Item -LiteralPath $path
  $payloadRows.Add([pscustomobject][ordered]@{
    relative_path = $name
    bytes = [long]$item.Length
    sha256 = Get-FileSha $path
    creation_time_utc_ticks = [long]$item.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [long]$item.LastWriteTimeUtc.Ticks
  })
}

$manifestPath = Join-Path $root $manifestName
$payloadRows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding utf8NoBOM
$manifestSha = Get-FileSha $manifestPath
$auditPath = Join-Path $root $auditName
$auditObject = [ordered]@{
  schema = 'P126_STATIC_LEGEND_SEGMENT_SEAL_AUDIT_V1'
  handoff_id = $handoff
  verdict = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  payload_count = 6
  control_count = 3
  ordinary_count = 9
  manifest_rows = 6
  manifest_sha256 = $manifestSha
  source_bytes = $expectedSourceBytes
  source_sha256 = $expectedSourceSha
  tex_build_count = 0
  commit_count = 0
  errors = @()
}
[IO.File]::WriteAllText($auditPath, ($auditObject | ConvertTo-Json -Depth 6) + "`n", $utf8NoBom)
$auditSha = Get-FileSha $auditPath

$premarkerFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
if ($premarkerFiles.Count -ne 8) { throw "premarker file count mismatch: $($premarkerFiles.Count)" }
$premarkerDirs = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
foreach ($file in $premarkerFiles) { $file.IsReadOnly = $true }
foreach ($dir in $premarkerDirs) { $dir.IsReadOnly = $true }
if (@(Get-ChildItem -LiteralPath $root -File -Recurse -Force | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'premarker writable file remains' }
if (@($premarkerDirs | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { throw 'premarker writable directory remains' }

$maxTicks = (@($premarkerFiles + $premarkerDirs) | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks, [long]$maxTicks + 3000000000L)
$markerLines = @(
  'SCHEMA=P126_STATIC_LEGEND_SEGMENT_WRITE_STOPPED_V1',
  "HANDOFF_ID=$handoff",
  'UID=FIG-P126-01',
  'ROLE=SA2',
  'VERDICT=STATIC_ONLY_NOT_RENDERED_NOT_PASS',
  'PAYLOAD_COUNT=6',
  'CONTROL_COUNT=3',
  'ORDINARY_COUNT=9',
  "SOURCE_BYTES=$expectedSourceBytes",
  "SOURCE_SHA256=$expectedSourceSha",
  "MANIFEST_SHA256=$manifestSha",
  "SEAL_AUDIT_SHA256=$auditSha",
  'TEX_BUILD_COUNT=0',
  'COMMIT_COUNT=0',
  'POSTMARKER_WRITES=0'
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=].*$' }).Count -ne 0) { throw 'marker syntax invalid' }
if (@($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 }).Count -ne 0) { throw 'marker duplicate key' }
[IO.File]::WriteAllText($stage, ($markerLines -join "`n") + "`n", $utf8NoBom)
$stageItem = Get-Item -LiteralPath $stage
$stageItem.LastWriteTimeUtc = [DateTime]::new($futureTicks, [DateTimeKind]::Utc)
$stageItem.IsReadOnly = $true
$markerShaBeforeMove = Get-FileSha $stage
$markerTicksBeforeMove = (Get-Item -LiteralPath $stage).LastWriteTimeUtc.Ticks
Move-Item -LiteralPath $stage -Destination (Join-Path $root $markerName) -ErrorAction Stop

$snapshot1 = Get-TreeSnapshot $root
$allFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$allDirs = @((Get-Item -LiteralPath $root -Force)) + @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
$markerPath = Join-Path $root $markerName
$markerItem = Get-Item -LiteralPath $markerPath
$nonMarkerItems = @($allFiles | Where-Object { $_.FullName -cne $markerPath }) + $allDirs
$maxNonMarkerTicks = (@($nonMarkerItems) | ForEach-Object { $_.LastWriteTimeUtc.Ticks } | Measure-Object -Maximum).Maximum
$atOrAfter = @($nonMarkerItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks }).Count
$csvFailures = 0
$jsonFailures = 0
foreach ($file in $allFiles) {
  if ($file.Extension -ieq '.csv') { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvFailures++ } }
  if ($file.Extension -ieq '.json') { try { $null = Get-Content -LiteralPath $file.FullName -Raw -Encoding utf8 | ConvertFrom-Json } catch { $jsonFailures++ } }
}
$adsCount = 0
foreach ($file in $allFiles) {
  $adsCount += @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction Stop | Where-Object { $_.Stream -ne ':$DATA' }).Count
}
$cachePycCount = @($allFiles | Where-Object { (Get-RelativeForward $root $_.FullName) -match '(?i)(^|/)(__pycache__|\.pytest_cache|\.mypy_cache)(/|$)|\.(pyc|pyo)$' }).Count
$reparseCount = @(@($allFiles + $allDirs) | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
$snapshot2 = Get-TreeSnapshot $root

$errors = [Collections.Generic.List[string]]::new()
if ($allFiles.Count -ne 9) { $errors.Add('ordinary count mismatch') }
if (@($allFiles | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { $errors.Add('writable file after marker') }
if (@($allDirs | Where-Object { -not $_.IsReadOnly }).Count -ne 0) { $errors.Add('writable directory after marker') }
if ((Get-FileSha $markerPath) -cne $markerShaBeforeMove) { $errors.Add('marker SHA changed during move') }
if ($markerItem.LastWriteTimeUtc.Ticks -ne $markerTicksBeforeMove) { $errors.Add('marker ticks changed during move') }
if ([long]$maxNonMarkerTicks -ge $markerItem.LastWriteTimeUtc.Ticks) { $errors.Add('marker not strictly latest') }
if ($atOrAfter -ne 0) { $errors.Add('at-or-after excluding marker nonzero') }
if ($snapshot1 -cne $snapshot2) { $errors.Add('postmarker content or attribute mutation') }
if ($csvFailures -ne 0 -or $jsonFailures -ne 0) { $errors.Add('CSV or JSON parse failure') }
if ($adsCount -ne 0 -or $cachePycCount -ne 0 -or $reparseCount -ne 0) { $errors.Add('hygiene failure') }

$result = [ordered]@{
  schema = 'P126_STATIC_LEGEND_SEGMENT_POSTSEAL_AUDIT_V1'
  handoff_id = $handoff
  root = $root
  verdict = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  payload_count = 6
  control_count = 3
  ordinary_count = $allFiles.Count
  directory_count_including_root = $allDirs.Count
  readonly_files = @($allFiles | Where-Object { $_.IsReadOnly }).Count
  readonly_dirs = @($allDirs | Where-Object { $_.IsReadOnly }).Count
  manifest_sha256 = $manifestSha
  seal_audit_sha256 = $auditSha
  marker_bytes = $markerItem.Length
  marker_sha256 = Get-FileSha $markerPath
  marker_physical_lines = $markerLines.Count
  marker_unique_keys = @($markerLines | ForEach-Object { ($_ -split '=', 2)[0] } | Sort-Object -Unique).Count
  marker_last_write_utc_ticks = $markerItem.LastWriteTimeUtc.Ticks
  strict_latest_margin_ticks = $markerItem.LastWriteTimeUtc.Ticks - [long]$maxNonMarkerTicks
  at_or_after_excluding_marker = $atOrAfter
  postmarker_snapshot_sha256 = $snapshot2
  postmarker_content_attribute_writes = if ($snapshot1 -ceq $snapshot2) { 0 } else { 1 }
  csv_parse_failures = $csvFailures
  json_parse_failures = $jsonFailures
  ads_count = $adsCount
  cache_pyc_count = $cachePycCount
  reparse_count = $reparseCount
  source_bytes = $sourceItem.Length
  source_sha256 = Get-FileSha $source
  tex_build_count = 0
  errors = @($errors)
  hard_gate = ($errors.Count -eq 0)
  audited_utc = [DateTime]::UtcNow.ToString('o')
}
[IO.File]::WriteAllText($resultPath, ($result | ConvertTo-Json -Depth 8) + "`n", $utf8NoBom)
(Get-Item -LiteralPath $resultPath).IsReadOnly = $true
if ($errors.Count -ne 0) { throw ($errors -join '; ') }
$result | ConvertTo-Json -Depth 8
