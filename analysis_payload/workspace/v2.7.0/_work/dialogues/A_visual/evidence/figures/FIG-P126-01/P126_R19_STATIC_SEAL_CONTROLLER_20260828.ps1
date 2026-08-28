Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_R116_20260828'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19_WRITE_STOPPED_STAGE_20260828'
$result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$handoff = 'A-R116-P126-SA2-STATIC-TEXT-CURVE-COLLISION-PATCH-20260828'
$utf8 = [Text.UTF8Encoding]::new($false)

function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Rel([string]$Path) { [IO.Path]::GetRelativePath($root,$Path).Replace('\','/') }
function Snapshot {
  $rows = [Collections.Generic.List[string]]::new()
  $rootItem = Get-Item -LiteralPath $root -Force
  $rows.Add(".<TAB>DIR<TAB>$([int64]$rootItem.CreationTimeUtc.Ticks)<TAB>$([int64]$rootItem.LastWriteTimeUtc.Ticks)<TAB>$([int]$rootItem.Attributes)".Replace('<TAB>',[char]9))
  foreach ($item in @(Get-ChildItem -LiteralPath $root -Recurse -Force | Sort-Object FullName)) {
    if ($item.PSIsContainer) {
      $rows.Add("$(Rel $item.FullName)<TAB>DIR<TAB>$([int64]$item.CreationTimeUtc.Ticks)<TAB>$([int64]$item.LastWriteTimeUtc.Ticks)<TAB>$([int]$item.Attributes)".Replace('<TAB>',[char]9))
    } else {
      $rows.Add("$(Rel $item.FullName)<TAB>$([int64]$item.Length)<TAB>$(Sha $item.FullName)<TAB>$([int64]$item.CreationTimeUtc.Ticks)<TAB>$([int64]$item.LastWriteTimeUtc.Ticks)<TAB>$([int]$item.Attributes)".Replace('<TAB>',[char]9))
    }
  }
  $bytes = $utf8.GetBytes((($rows -join "`n") + "`n"))
  $hash = [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes))
  [pscustomobject]@{ entries=$rows.Count; sha256=$hash }
}

if (-not (Test-Path -LiteralPath $root -PathType Container)) { throw 'ROOT_MISSING' }
if ((Test-Path -LiteralPath $stage) -or (Test-Path -LiteralPath $result)) { throw 'EXTERNAL_OUTPUT_EXISTS' }
if ((Test-Path -LiteralPath (Join-Path $root 'WRITE_STOPPED'))) { throw 'MARKER_EXISTS' }
$sourceItem = Get-Item -LiteralPath $source
if ($sourceItem.Length -ne 4809 -or (Sha $source) -ne '4CE06E3B00402A6C14774CC95D86348D4056B493C030CADDB9BB53DC53C6AAC2') { throw 'SOURCE_IDENTITY' }

$payload = @(Get-ChildItem -LiteralPath $root -File -Force | Where-Object { $_.Name -notin @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED') } | Sort-Object Name)
if ($payload.Count -ne 9) { throw "PAYLOAD_COUNT_$($payload.Count)" }
$manifestRows = foreach ($file in $payload) {
  [pscustomobject][ordered]@{
    relative_path = Rel $file.FullName
    bytes = [int64]$file.Length
    sha256 = Sha $file.FullName
    creation_time_utc_ticks = [int64]$file.CreationTimeUtc.Ticks
    last_write_time_utc_ticks = [int64]$file.LastWriteTimeUtc.Ticks
  }
}
$manifestPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$csv = @($manifestRows | ConvertTo-Csv -NoTypeInformation)
[IO.File]::WriteAllLines($manifestPath,$csv,$utf8)
$manifestSha = Sha $manifestPath

$auditPath = Join-Path $root 'SEAL_AUDIT.json'
$audit = [ordered]@{
  schema = 'P126_R19_STATIC_SEAL_AUDIT_V1'
  handoff_id = $handoff
  status = 'STATIC_ONLY_NOT_RENDERED_NOT_PASS'
  root = $root
  payload_count = 9
  control_count = 3
  ordinary_count = 12
  manifest_sha256 = $manifestSha
  source_bytes = 4809
  source_sha256 = '4CE06E3B00402A6C14774CC95D86348D4056B493C030CADDB9BB53DC53C6AAC2'
  reverse_sha256 = '2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405'
  tex_build_invocations = 0
  prepared_utc = [DateTime]::UtcNow.ToString('o')
}
[IO.File]::WriteAllText($auditPath,($audit | ConvertTo-Json -Depth 5),$utf8)
$auditSha = Sha $auditPath

$preFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$preChildDirs = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
$preDirs = @($preChildDirs) + @((Get-Item -LiteralPath $root -Force))
if ($preFiles.Count -ne 11) { throw "PREMARKER_FILE_COUNT_$($preFiles.Count)" }
foreach ($file in $preFiles) { [IO.File]::SetAttributes($file.FullName,$file.Attributes -bor [IO.FileAttributes]::ReadOnly) }
foreach ($dir in $preDirs) { [IO.File]::SetAttributes($dir.FullName,$dir.Attributes -bor [IO.FileAttributes]::ReadOnly) }
$roFileFail = @($preFiles | Where-Object { (((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) })
$roDirFail = @($preDirs | Where-Object { (((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) })
if ($roFileFail.Count -ne 0 -or $roDirFail.Count -ne 0) { throw 'READONLY_PREMARKER_GATE' }

$future = [DateTime]::UtcNow.AddMinutes(10)
$markerLines = @(
  'SCHEMA=P126_R19_WRITE_STOPPED_V1',
  "HANDOFF_ID=$handoff",
  'STATUS=STATIC_ONLY_NOT_RENDERED_NOT_PASS',
  "ROOT=$root",
  'PAYLOAD_COUNT=9',
  'CONTROL_COUNT=3',
  'ORDINARY_COUNT=12',
  "PAYLOAD_MANIFEST_SHA256=$manifestSha",
  "SEAL_AUDIT_SHA256=$auditSha",
  'SOURCE_BYTES=4809',
  'SOURCE_SHA256=4CE06E3B00402A6C14774CC95D86348D4056B493C030CADDB9BB53DC53C6AAC2',
  'BEFORE_SHA256=2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405',
  'REVERSE_SHA256=2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405',
  'GIT_NAME_ONLY_COUNT=1',
  'GIT_NUMSTAT=2_PLUS_2_MINUS',
  'TEX_BUILD_INVOCATIONS=0',
  'SOURCE_EDIT_INVOCATIONS=1',
  'POSTMARKER_ROOT_WRITES=0',
  "PREPARED_UTC=$([DateTime]::UtcNow.ToString('o'))",
  "MARKER_LAST_WRITE_UTC_TICKS=$([int64]$future.Ticks)"
)
if (@($markerLines | Where-Object { $_ -notmatch '^[A-Z0-9_]+=[^=].*$' -or $_.Contains("`t") }).Count -ne 0) { throw 'MARKER_SYNTAX' }
[IO.File]::WriteAllLines($stage,$markerLines,$utf8)
[IO.File]::SetLastWriteTimeUtc($stage,$future)
[IO.File]::SetAttributes($stage,[IO.File]::GetAttributes($stage) -bor [IO.FileAttributes]::ReadOnly)
if (((Get-Item -LiteralPath $stage).Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) { throw 'STAGE_NOT_READONLY' }

$markerPath = Join-Path $root 'WRITE_STOPPED'
[IO.File]::Move($stage,$markerPath)
$snapshot1 = Snapshot
Start-Sleep -Milliseconds 300
$snapshot2 = Snapshot
$allFiles = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$allChildDirs = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
$allDirs = @($allChildDirs) + @((Get-Item -LiteralPath $root -Force))
$marker = Get-Item -LiteralPath $markerPath -Force
$otherFiles = @($allFiles | Where-Object FullName -ne $marker.FullName)
$otherItems = @($otherFiles) + @($allDirs)
$atOrAfter = @($otherItems | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$allItems = @($allFiles) + @($allDirs)
$roFail = @($allItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($allFiles.Count -ne 12 -or $roFail.Count -ne 0 -or $atOrAfter.Count -ne 0 -or $snapshot1.sha256 -ne $snapshot2.sha256) { throw 'POSTMARKER_GATE' }

$out = [ordered]@{
  schema='P126_R19_STATIC_SEAL_CONTROLLER_RESULT_V1'; success=$true; handoff_id=$handoff
  invocation_count=1; retry_count=0; payload_count=9; control_count=3; ordinary_count=12
  directory_count=$allDirs.Count; readonly_failures=$roFail.Count; at_or_after_excluding_marker=$atOrAfter.Count
  marker_path=$markerPath; marker_bytes=$marker.Length; marker_sha256=Sha $markerPath; marker_lines=$markerLines.Count
  marker_ticks=[int64]$marker.LastWriteTimeUtc.Ticks; strict_margin_ticks=[int64]($marker.LastWriteTimeUtc.Ticks-($otherItems | Measure-Object LastWriteTimeUtc -Maximum).Maximum.Ticks)
  manifest_sha256=$manifestSha; seal_audit_sha256=$auditSha
  snapshot1_sha256=$snapshot1.sha256; snapshot2_sha256=$snapshot2.sha256; snapshot_entries=$snapshot1.entries
  completed_utc=[DateTime]::UtcNow.ToString('o')
}
[IO.File]::WriteAllText($result,($out | ConvertTo-Json -Depth 6),$utf8)
