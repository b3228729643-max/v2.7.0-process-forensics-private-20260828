Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R8_SA2_STATIC_THREE_HARD_PATCH_R115_20260828'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R8_STATIC_WRITE_STOPPED.stage'
$resultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R8_STATIC_POSTSEAL_AUDIT_20260828.json'
$handoff = 'A-R115-P126-SA2-STATIC-THREE-HARD-PATCH-20260828'
$utf8 = [Text.UTF8Encoding]::new($false)

function Get-Sha256([string]$Path) {
  (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}
function Is-Readonly([IO.FileSystemInfo]$Item) {
  (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0)
}
function Set-Readonly([IO.FileSystemInfo]$Item) {
  $Item.Attributes = $Item.Attributes -bor [IO.FileAttributes]::ReadOnly
}
function Get-Relative([string]$Base,[string]$Path) {
  ([IO.Path]::GetRelativePath([IO.Path]::GetFullPath($Base),[IO.Path]::GetFullPath($Path))).Replace('\','/')
}
function Get-TreeSnapshot([string]$Root) {
  $rows = [Collections.Generic.List[string]]::new()
  foreach ($item in @(@(Get-ChildItem -LiteralPath $Root -Recurse -Force | Sort-Object FullName) + @(Get-Item -LiteralPath $Root))) {
    $kind = if ($item.PSIsContainer) {'D'} else {'F'}
    $bytes = if ($item.PSIsContainer) {''} else {[string]$item.Length}
    $sha = if ($item.PSIsContainer) {''} else {Get-Sha256 $item.FullName}
    $rows.Add("$(Get-Relative $Root $item.FullName)`t$kind`t$bytes`t$sha`t$($item.CreationTimeUtc.Ticks)`t$($item.LastWriteTimeUtc.Ticks)`t$([int]$item.Attributes)")
  }
  $blob = [string]::Join("`n",$rows) + "`n"
  $hash = [Security.Cryptography.SHA256]::HashData($utf8.GetBytes($blob))
  [ordered]@{rows=$rows.Count;sha256=[Convert]::ToHexString($hash)}
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'static root missing' }
foreach ($path in @($stage,$resultPath)) { if (Test-Path -LiteralPath $path) { throw "preexisting seal artifact: $path" } }
$sourceItem = Get-Item -LiteralPath $source
if ($sourceItem.Length -ne 4361 -or (Get-Sha256 $source) -cne '85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81') { throw 'source identity drift' }

$payloadNames = @('HANDLER_CAUSALITY.md','INCREMENTAL_DIFF.patch','SOURCE_IDENTITY.json','STATIC_GEOMETRY_PROJECTION.json','STATIC_HANDOFF.md','STATIC_PATCH_REPORT.md')
$actualPayload = @(Get-ChildItem -LiteralPath $root -File -Force | Sort-Object Name)
if ($actualPayload.Count -ne 6) { throw 'payload count before controls is not 6' }
$setDiff = @(Compare-Object -ReferenceObject @($payloadNames | Sort-Object -CaseSensitive) -DifferenceObject @($actualPayload.Name | Sort-Object -CaseSensitive) -CaseSensitive)
if ($setDiff.Count -ne 0) { throw 'payload set mismatch' }

$payloadRows = [Collections.Generic.List[object]]::new()
foreach ($file in $actualPayload) {
  $payloadRows.Add([pscustomobject][ordered]@{
    relative_path = Get-Relative $root $file.FullName
    bytes = [long]$file.Length
    sha256 = Get-Sha256 $file.FullName
    creation_time_utc_ticks = [long]$file.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [long]$file.LastWriteTimeUtc.Ticks
  })
}
$manifestPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$sealAuditPath = Join-Path $root 'SEAL_AUDIT.json'
$manifestText = [string]::Join("`r`n",@($payloadRows | ConvertTo-Csv -NoTypeInformation)) + "`r`n"
[IO.File]::WriteAllText($manifestPath,$manifestText,$utf8)
$sealAudit = [ordered]@{
  schema='P126_R8_STATIC_SEAL_AUDIT_V1';handoff_id=$handoff;uid='FIG-P126-01';role='SA2'
  verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';source_path=$source;source_bytes=4361
  source_sha256='85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81'
  payload_count=6;control_count=3;ordinary_count=9;manifest_rows=6;manifest_set_diff_count=0
  incremental_insertions=6;incremental_deletions=9;aggregate_insertions=29;aggregate_deletions=26
  tex_invocation_count=0;build_invocation_count=0;commit_count=0
}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit | ConvertTo-Json -Depth 5)+"`n",$utf8)

$premarkerFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
if ($premarkerFiles.Count -ne 8) { throw 'premarker ordinary count is not 8' }
$premarkerDirs = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force | Sort-Object FullName -Descending)
foreach ($file in $premarkerFiles) { Set-Readonly $file }
foreach ($dir in $premarkerDirs) { Set-Readonly $dir }
Set-Readonly (Get-Item -LiteralPath $root)
$allPremarkerDirs = @(@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force) + @(Get-Item -LiteralPath $root))
if (@($premarkerFiles | Where-Object {-not (Is-Readonly $_)}).Count -ne 0 -or @($allPremarkerDirs | Where-Object {-not (Is-Readonly $_)}).Count -ne 0) { throw 'premarker readonly gate failed' }

$premarkerItems = @(@(Get-ChildItem -LiteralPath $root -Recurse -Force) + @(Get-Item -LiteralPath $root))
$maxPremarkerTicks = [long](($premarkerItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks)
$futureTicks = [Math]::Max([DateTime]::UtcNow.AddMinutes(5).Ticks,$maxPremarkerTicks + 10000000)
$markerLines = @(
  'SCHEMA=P126_R8_STATIC_WRITE_STOPPED_V1',
  "HANDOFF_ID=$handoff",
  'UID=FIG-P126-01',
  'ROLE=SA2',
  'VERDICT=STATIC_ONLY_NOT_RENDERED_NOT_PASS',
  "ROOT=$root",
  "SOURCE_PATH=$source",
  'SOURCE_BYTES=4361',
  'SOURCE_SHA256=85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81',
  'PAYLOAD_COUNT=6',
  'CONTROL_COUNT=3',
  'ORDINARY_COUNT=9',
  "PAYLOAD_MANIFEST_SHA256=$(Get-Sha256 $manifestPath)",
  "SEAL_AUDIT_SHA256=$(Get-Sha256 $sealAuditPath)",
  'TEX_INVOCATION_COUNT=0',
  'BUILD_INVOCATION_COUNT=0',
  'COMMIT_COUNT=0',
  "WSTOP_LAST_WRITE_UTC_TICKS=$futureTicks"
)
$badMarker = @($markerLines | Where-Object {$_ -notmatch '^[A-Z0-9_]+=[^\t\r\n]+$'})
$duplicateKeys = @(($markerLines | ForEach-Object {($_ -split '=',2)[0]}) | Group-Object -CaseSensitive | Where-Object {$_.Count -ne 1})
if ($badMarker.Count -ne 0 -or $duplicateKeys.Count -ne 0) { throw 'marker syntax failure' }
[IO.File]::WriteAllText($stage,[string]::Join("`r`n",$markerLines)+"`r`n",$utf8)
$stageItem = Get-Item -LiteralPath $stage
$stageItem.LastWriteTimeUtc = [DateTime]::new($futureTicks,[DateTimeKind]::Utc)
Set-Readonly $stageItem
if (-not (Is-Readonly (Get-Item -LiteralPath $stage)) -or (Get-Item -LiteralPath $stage).LastWriteTimeUtc.Ticks -ne $futureTicks) { throw 'external marker preparation failure' }
$markerPath = Join-Path $root 'WRITE_STOPPED'
Move-Item -LiteralPath $stage -Destination $markerPath

$snapshot1 = Get-TreeSnapshot $root
Start-Sleep -Milliseconds 250
$snapshot2 = Get-TreeSnapshot $root
$allFiles = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force)
$allDirs = @(@(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force) + @(Get-Item -LiteralPath $root))
$marker = Get-Item -LiteralPath $markerPath
$otherItems = @(@(Get-ChildItem -LiteralPath $root -Recurse -Force | Where-Object {$_.FullName -cne $markerPath}) + @(Get-Item -LiteralPath $root))
$maxOtherTicks = [long](($otherItems | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks)
$atOrAfter = @($otherItems | Where-Object {$_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks})
$writableFiles = @($allFiles | Where-Object {-not (Is-Readonly $_)})
$writableDirs = @($allDirs | Where-Object {-not (Is-Readonly $_)})
$parseErrors = [Collections.Generic.List[string]]::new()
foreach ($file in @($allFiles | Where-Object {$_.Extension -ieq '.json'})) { try {[void](Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json)} catch {$parseErrors.Add($file.FullName)} }
foreach ($file in @($allFiles | Where-Object {$_.Extension -ieq '.csv'})) { try {[void]@(Import-Csv -LiteralPath $file.FullName)} catch {$parseErrors.Add($file.FullName)} }
$sourceAfter = Get-Item -LiteralPath $source
$errors = [Collections.Generic.List[string]]::new()
if ($allFiles.Count -ne 9) {$errors.Add('ordinary_count')}
if ($allDirs.Count -ne 1) {$errors.Add('directory_count')}
if ($writableFiles.Count -ne 0 -or $writableDirs.Count -ne 0) {$errors.Add('readonly')}
if ($marker.LastWriteTimeUtc.Ticks -le $maxOtherTicks -or $atOrAfter.Count -ne 0) {$errors.Add('marker_latest')}
if ($snapshot1.sha256 -cne $snapshot2.sha256) {$errors.Add('postmarker_snapshot')}
if ($parseErrors.Count -ne 0) {$errors.Add('parse')}
if ($sourceAfter.Length -ne 4361 -or (Get-Sha256 $source) -cne '85FA5D73BD816149EE77968512C708C58CEE1AB90D59EDEBBDA550F232EE0D81') {$errors.Add('source_drift')}
if ($errors.Count -ne 0) { throw "postseal audit failure: $([string]::Join(',',$errors))" }

$result = [ordered]@{
  schema='P126_R8_STATIC_POSTSEAL_AUDIT_V1';handoff_id=$handoff;verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  payload_count=6;control_count=3;ordinary_count=$allFiles.Count;directory_count=$allDirs.Count
  manifest_rows=$payloadRows.Count;readonly_files=$allFiles.Count;readonly_directories=$allDirs.Count
  marker_path=$markerPath;marker_bytes=$marker.Length;marker_sha256=Get-Sha256 $markerPath
  marker_line_count=$markerLines.Count;marker_ticks=$marker.LastWriteTimeUtc.Ticks
  strict_latest_margin_ticks=($marker.LastWriteTimeUtc.Ticks-$maxOtherTicks);at_or_after_excluding_marker=$atOrAfter.Count
  snapshot1_sha256=$snapshot1.sha256;snapshot2_sha256=$snapshot2.sha256;postmarker_diff_count=0
  parse_error_count=$parseErrors.Count;tex_invocation_count=0;build_invocation_count=0;commit_count=0;errors=@()
}
[IO.File]::WriteAllText($resultPath,($result | ConvertTo-Json -Depth 6)+"`n",$utf8)
(Get-Item -LiteralPath $resultPath).IsReadOnly = $true
$result | ConvertTo-Json -Depth 6
