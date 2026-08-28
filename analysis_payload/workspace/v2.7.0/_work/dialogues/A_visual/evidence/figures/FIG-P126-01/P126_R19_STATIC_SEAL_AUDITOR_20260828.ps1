Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_R116_20260828'
$controllerResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19_STATIC_SEAL_CONTROLLER_RESULT_20260828.json'
$auditResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19_STATIC_SEAL_AUDITOR_RESULT_20260828.json'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$utf8 = [Text.UTF8Encoding]::new($false)

function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Rel([string]$Path) { [IO.Path]::GetRelativePath($root,$Path).Replace('\','/') }
function Snapshot {
  $rows = [Collections.Generic.List[string]]::new()
  $rootItem = Get-Item -LiteralPath $root -Force
  $rows.Add(".<TAB>DIR<TAB>$([int64]$rootItem.CreationTimeUtc.Ticks)<TAB>$([int64]$rootItem.LastWriteTimeUtc.Ticks)<TAB>$([int]$rootItem.Attributes)".Replace('<TAB>',[char]9))
  foreach ($item in @(Get-ChildItem -LiteralPath $root -Recurse -Force | Sort-Object FullName)) {
    if ($item.PSIsContainer) { $rows.Add("$(Rel $item.FullName)<TAB>DIR<TAB>$([int64]$item.CreationTimeUtc.Ticks)<TAB>$([int64]$item.LastWriteTimeUtc.Ticks)<TAB>$([int]$item.Attributes)".Replace('<TAB>',[char]9)) }
    else { $rows.Add("$(Rel $item.FullName)<TAB>$([int64]$item.Length)<TAB>$(Sha $item.FullName)<TAB>$([int64]$item.CreationTimeUtc.Ticks)<TAB>$([int64]$item.LastWriteTimeUtc.Ticks)<TAB>$([int]$item.Attributes)".Replace('<TAB>',[char]9)) }
  }
  $bytes = $utf8.GetBytes((($rows -join "`n") + "`n"))
  [pscustomobject]@{ entries=$rows.Count; sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) }
}

if (Test-Path -LiteralPath $auditResult) { throw 'AUDIT_RESULT_EXISTS' }
$cr = Get-Content -LiteralPath $controllerResult -Raw | ConvertFrom-Json
if (-not $cr.success -or $cr.invocation_count -ne 1 -or $cr.retry_count -ne 0) { throw 'CONTROLLER_RESULT' }
$files = @(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$childDirs = @(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
$dirs = @($childDirs) + @((Get-Item -LiteralPath $root -Force))
if ($files.Count -ne 12 -or $dirs.Count -ne 1) { throw 'TREE_COUNTS' }
$allItems = @($files) + @($dirs)
$roFail = @($allItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0 })
if ($roFail.Count -ne 0) { throw 'READONLY' }

$manifestPath = Join-Path $root 'PAYLOAD_MANIFEST.csv'
$manifest = @(Import-Csv -LiteralPath $manifestPath)
if ($manifest.Count -ne 9) { throw 'MANIFEST_COUNT' }
$payload = @($files | Where-Object { $_.Name -notin @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED') })
$actual = @{}
foreach ($file in $payload) { $actual[(Rel $file.FullName)] = $file }
$identityErrors = 0
foreach ($row in $manifest) {
  $p = [string]$row.relative_path
  if (-not $actual.ContainsKey($p)) { $identityErrors++; continue }
  $f = $actual[$p]
  if ([int64]$row.bytes -ne $f.Length -or [string]$row.sha256 -ne (Sha $f.FullName) -or [int64]$row.creation_time_utc_ticks -ne $f.CreationTimeUtc.Ticks -or [int64]$row.last_write_time_utc_ticks -ne $f.LastWriteTimeUtc.Ticks) { $identityErrors++ }
}
if ($identityErrors -ne 0 -or $actual.Count -ne $manifest.Count) { throw 'MANIFEST_IDENTITY' }

$jsonFail = 0
foreach ($file in @($files | Where-Object Extension -eq '.json')) { try { $null = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json } catch { $jsonFail++ } }
$csvFail = 0
foreach ($file in @($files | Where-Object Extension -eq '.csv')) { try { $null = @(Import-Csv -LiteralPath $file.FullName) } catch { $csvFail++ } }
$adsNondefault = 0
foreach ($item in $allItems) { $streams = @(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop); $adsNondefault += @($streams | Where-Object Stream -ne ':$DATA').Count }
$cachePyc = @($files | Where-Object { $_.Name -like '*.pyc' -or $_.FullName -match '(__pycache__|[\\/]texcache[\\/])' }).Count
$reparse = @($allItems | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 }).Count
if ($jsonFail -ne 0 -or $csvFail -ne 0 -or $adsNondefault -ne 0 -or $cachePyc -ne 0 -or $reparse -ne 0) { throw 'HYGIENE' }

$marker = Get-Item -LiteralPath (Join-Path $root 'WRITE_STOPPED') -Force
$lines = @(Get-Content -LiteralPath $marker.FullName)
$map = @{}
$bad = 0
foreach ($line in $lines) { if ($line -notmatch '^([A-Z0-9_]+)=([^=].*)$' -or $line.Contains("`t")) { $bad++; continue }; if ($map.ContainsKey($Matches[1])) { $bad++ } else { $map[$Matches[1]]=$Matches[2] } }
$otherFiles = @($files | Where-Object FullName -ne $marker.FullName)
$others = @($otherFiles) + @($dirs)
$atOrAfter = @($others | Where-Object { $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$margin = [int64]($marker.LastWriteTimeUtc.Ticks-($others | Measure-Object LastWriteTimeUtc -Maximum).Maximum.Ticks)
if ($lines.Count -ne 20 -or $map.Count -ne 20 -or $bad -ne 0 -or $atOrAfter.Count -ne 0 -or $margin -le 0) { throw 'MARKER_GATE' }
if ($map['HANDOFF_ID'] -ne 'A-R116-P126-SA2-STATIC-TEXT-CURVE-COLLISION-PATCH-20260828' -or $map['STATUS'] -ne 'STATIC_ONLY_NOT_RENDERED_NOT_PASS' -or $map['PAYLOAD_MANIFEST_SHA256'] -ne (Sha $manifestPath) -or $map['SOURCE_SHA256'] -ne (Sha $source)) { throw 'MARKER_BINDING' }

$s1 = Snapshot
Start-Sleep -Milliseconds 300
$s2 = Snapshot
if ($s1.sha256 -ne $s2.sha256 -or $s1.sha256 -ne [string]$cr.snapshot1_sha256 -or $s1.sha256 -ne [string]$cr.snapshot2_sha256) { throw 'POSTMARKER_DRIFT' }
$out = [ordered]@{
  schema='P126_R19_STATIC_SEAL_AUDITOR_RESULT_V1'; success=$true; invocation_count=1; retry_count=0
  payload_count=$payload.Count; control_count=3; ordinary_count=$files.Count; directory_count=$dirs.Count
  manifest_identity_errors=$identityErrors; readonly_failures=$roFail.Count
  marker_lines=$lines.Count; marker_keys=$map.Count; marker_bad=$bad; marker_sha256=Sha $marker.FullName
  marker_ticks=[int64]$marker.LastWriteTimeUtc.Ticks; strict_margin_ticks=$margin; at_or_after_excluding_marker=$atOrAfter.Count
  snapshot1_sha256=$s1.sha256; snapshot2_sha256=$s2.sha256; snapshot_entries=$s1.entries; postmarker_drift=0
  json_parse_failures=$jsonFail; csv_parse_failures=$csvFail; ads_nondefault=$adsNondefault; cache_pyc=$cachePyc; reparse_points=$reparse
  source_bytes=(Get-Item -LiteralPath $source).Length; source_sha256=Sha $source; completed_utc=[DateTime]::UtcNow.ToString('o')
}
[IO.File]::WriteAllText($auditResult,($out | ConvertTo-Json -Depth 6),$utf8)
