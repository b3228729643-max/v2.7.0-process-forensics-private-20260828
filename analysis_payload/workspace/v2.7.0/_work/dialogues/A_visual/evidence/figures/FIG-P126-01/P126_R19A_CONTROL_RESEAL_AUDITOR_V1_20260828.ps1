Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R116-P126-SA2-STATIC-TEXT-CURVE-COLLISION-PATCH-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R116_R19_STATIC_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$oldRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_R116_20260828'
$destRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19A_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_CONTROL_RESEAL_R116_20260828'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19A_WRITE_STOPPED_STAGE_V1_20260828'
$controllerResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19A_CONTROLLER_RESULT_V1_20260828.json'
$auditResult = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19A_AUDITOR_RESULT_V1_20260828.json'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$utf8 = [Text.UTF8Encoding]::new($false)

function Sha([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Canon([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { throw 'CANON_EMPTY' }
  $q = $Value.Replace([string][char]92,[string][char]47)
  $q = $q -replace '^(?:\./)+',''
  if ([IO.Path]::IsPathRooted($q) -or $q.StartsWith('/',[StringComparison]::Ordinal)) { throw 'CANON_ROOTED' }
  $parts = @($q.Split([char]47))
  if (@($parts | Where-Object { [string]::IsNullOrEmpty($_) -or $_ -eq '.' -or $_ -eq '..' }).Count -ne 0) { throw 'CANON_SEGMENT' }
  $parts -join '/'
}
function Inside([string]$Base,[string]$Relative) {
  $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd([char]92,[char]47)
  $native = $Relative.Replace([string][char]47,[string][char]92)
  $full = [IO.Path]::GetFullPath([IO.Path]::Combine($baseFull,$native))
  $prefix = $baseFull + [IO.Path]::DirectorySeparatorChar
  if (-not $full.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)) { throw 'PATH_ESCAPE' }
  $full
}
function Snapshot([string]$Base) {
  $lines = [Collections.Generic.List[string]]::new()
  $rootItem = Get-Item -LiteralPath $Base -Force
  $lines.Add((@('.','DIR',[int64]$rootItem.CreationTimeUtc.Ticks,[int64]$rootItem.LastWriteTimeUtc.Ticks,[int]$rootItem.Attributes) -join [char]9))
  foreach ($item in @(Get-ChildItem -LiteralPath $Base -Recurse -Force | Sort-Object FullName)) {
    $rel = [IO.Path]::GetRelativePath($Base,$item.FullName).Replace([string][char]92,[string][char]47)
    if ($item.PSIsContainer) { $lines.Add((@($rel,'DIR',[int64]$item.CreationTimeUtc.Ticks,[int64]$item.LastWriteTimeUtc.Ticks,[int]$item.Attributes) -join [char]9)) }
    else { $lines.Add((@($rel,[int64]$item.Length,(Sha $item.FullName),[int64]$item.CreationTimeUtc.Ticks,[int64]$item.LastWriteTimeUtc.Ticks,[int]$item.Attributes) -join [char]9)) }
  }
  $bytes = $utf8.GetBytes((($lines -join "`n") + "`n"))
  [pscustomobject]@{ entries=$lines.Count; sha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($bytes)) }
}

if (Test-Path -LiteralPath $auditResult) { throw 'AUDIT_RESULT_EXISTS' }
if (Test-Path -LiteralPath $stage) { throw 'STAGE_EXISTS' }
$cr = Get-Content -LiteralPath $controllerResult -Raw | ConvertFrom-Json
if (-not $cr.success -or $cr.handoff_id -ne $handoff -or $cr.operation -ne $operation -or $cr.verdict -ne 'STATIC_ONLY_NOT_RENDERED_NOT_PASS' -or $cr.invocation_count -ne 1 -or $cr.retry_count -ne 0 -or -not $cr.natural_exit) { throw 'CONTROLLER_RESULT' }
if ((Get-Item -LiteralPath $source).Length -ne 4809 -or (Sha $source) -ne '4CE06E3B00402A6C14774CC95D86348D4056B493C030CADDB9BB53DC53C6AAC2') { throw 'SOURCE_IDENTITY' }

$oldManifest = Join-Path $oldRoot 'PAYLOAD_MANIFEST.csv'
$oldRows = @(Import-Csv -LiteralPath $oldManifest)
$copyPath = Join-Path $destRoot 'COPY_IDENTITY.csv'
$copyRows = @(Import-Csv -LiteralPath $copyPath)
if ($oldRows.Count -ne 9 -or $copyRows.Count -ne 9) { throw 'COPY_COUNTS' }
$oldMap = @{}; foreach ($row in $oldRows) { $rel=Canon ([string]$row.relative_path); if($oldMap.ContainsKey($rel)){throw 'OLD_DUP'}; $oldMap[$rel]=$row }
$copyMap = @{}; foreach ($row in $copyRows) { $rel=Canon ([string]$row.relative_path); if($copyMap.ContainsKey($rel)){throw 'COPY_DUP'}; $copyMap[$rel]=$row }
$identityErrors = 0
foreach ($rel in $oldMap.Keys) {
  if (-not $copyMap.ContainsKey($rel)) { $identityErrors++; continue }
  $o=$oldMap[$rel]; $c=$copyMap[$rel]
  if ([string]$c.source_path -ne (Inside $oldRoot $rel) -or [string]$c.destination_path -ne (Inside $destRoot $rel) -or [int64]$c.bytes -ne [int64]$o.bytes -or [string]$c.sha256 -ne [string]$o.sha256 -or [int64]$c.creation_time_utc_ticks -ne [int64]$o.creation_time_utc_ticks -or [int64]$c.last_write_time_utc_ticks -ne [int64]$o.last_write_time_utc_ticks) { $identityErrors++ }
  foreach ($path in @([string]$c.source_path,[string]$c.destination_path)) { $f=Get-Item -LiteralPath $path -Force; if($f.Length-ne[int64]$o.bytes -or (Sha $path)-ne[string]$o.sha256 -or $f.CreationTimeUtc.Ticks-ne[int64]$o.creation_time_utc_ticks -or $f.LastWriteTimeUtc.Ticks-ne[int64]$o.last_write_time_utc_ticks){$identityErrors++} }
}
if ($identityErrors -ne 0 -or $oldMap.Count -ne $copyMap.Count) { throw 'COPY_IDENTITY' }

$provPath = Join-Path $destRoot 'COPY_PROVENANCE.json'
$prov = Get-Content -LiteralPath $provPath -Raw | ConvertFrom-Json
if ($prov.handoff_id-ne$handoff -or $prov.operation-ne$operation -or $prov.verdict-ne'STATIC_ONLY_NOT_RENDERED_NOT_PASS' -or $prov.copied_count-ne9 -or $prov.old_controls_copied-ne0 -or $prov.payload_count-ne11 -or $prov.business_evidence_rerun) { throw 'PROVENANCE' }
$manifestPath = Join-Path $destRoot 'PAYLOAD_MANIFEST.csv'
$manifest = @(Import-Csv -LiteralPath $manifestPath)
$files = @(Get-ChildItem -LiteralPath $destRoot -File -Recurse -Force)
$childDirs = @(Get-ChildItem -LiteralPath $destRoot -Directory -Recurse -Force)
$dirs = @($childDirs) + @((Get-Item -LiteralPath $destRoot -Force))
if ($files.Count -ne 14 -or $manifest.Count -ne 11) { throw 'TREE_COUNTS' }
$payload = @($files | Where-Object { $_.Name -notin @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED') })
$actual = @{}; foreach($file in $payload){$rel=[IO.Path]::GetRelativePath($destRoot,$file.FullName).Replace([string][char]92,[string][char]47);$actual[$rel]=$file}
$manifestErrors=0
foreach($row in $manifest){$rel=Canon ([string]$row.relative_path);if(-not$actual.ContainsKey($rel)){$manifestErrors++;continue};$f=$actual[$rel];if($f.Length-ne[int64]$row.bytes-or(Sha $f.FullName)-ne[string]$row.sha256-or$f.CreationTimeUtc.Ticks-ne[int64]$row.creation_time_utc_ticks-or$f.LastWriteTimeUtc.Ticks-ne[int64]$row.last_write_time_utc_ticks){$manifestErrors++}}
if($manifestErrors-ne0-or$actual.Count-ne$manifest.Count){throw 'MANIFEST_IDENTITY'}

$sealAuditPath = Join-Path $destRoot 'SEAL_AUDIT.json'
$sa = Get-Content -LiteralPath $sealAuditPath -Raw | ConvertFrom-Json
if($sa.handoff_id-ne$handoff-or$sa.operation-ne$operation-or$sa.verdict-ne'STATIC_ONLY_NOT_RENDERED_NOT_PASS'-or$sa.copied_count-ne9-or$sa.payload_count-ne11-or$sa.control_count-ne3-or$sa.ordinary_count-ne14-or$sa.business_evidence_rerun){throw 'SEAL_AUDIT'}
$allItems=@($files)+@($dirs)
$roFail=@($allItems|Where-Object{($_.Attributes-band[IO.FileAttributes]::ReadOnly)-eq0})
if($roFail.Count-ne0){throw 'READONLY'}

$marker=Get-Item -LiteralPath (Join-Path $destRoot 'WRITE_STOPPED') -Force
$markerLines=@(Get-Content -LiteralPath $marker.FullName)
$markerMap=@{};$bad=0
foreach($line in $markerLines){if($line-notmatch'^([A-Z0-9_]+)=([^=].*)$'-or$line.Contains("`t")){$bad++;continue};if($markerMap.ContainsKey($Matches[1])){$bad++}else{$markerMap[$Matches[1]]=$Matches[2]}}
$required=@('SCHEMA','HANDOFF_ID','OPERATION','VERDICT','SOURCE_ROOT','DESTINATION_ROOT','OLD_MANIFEST_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','COPIED_COUNT','OLD_CONTROLS_COPIED','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','DIRECTORY_COUNT','SOURCE_BYTES','SOURCE_SHA256','REVERSE_SHA256','BUSINESS_EVIDENCE_RERUN','CONTROLLER_INVOCATION_COUNT','CONTROLLER_RETRY_COUNT','AUDITOR_INVOCATION_BUDGET','SOURCE_SNAPSHOT_SHA256','POSTMARKER_WRITES','PREPARED_UTC','MARKER_LAST_WRITE_UTC_TICKS')
if($markerLines.Count-ne28-or$markerMap.Count-ne28-or$bad-ne0-or@($required|Where-Object{-not$markerMap.ContainsKey($_)}).Count-ne0){throw 'MARKER_SCHEMA'}
if($markerMap['HANDOFF_ID']-ne$handoff-or$markerMap['OPERATION']-ne$operation-or$markerMap['VERDICT']-ne'STATIC_ONLY_NOT_RENDERED_NOT_PASS'-or$markerMap['COPY_IDENTITY_SHA256']-ne(Sha $copyPath)-or$markerMap['COPY_PROVENANCE_SHA256']-ne(Sha $provPath)-or$markerMap['PAYLOAD_MANIFEST_SHA256']-ne(Sha $manifestPath)-or$markerMap['SEAL_AUDIT_SHA256']-ne(Sha $sealAuditPath)){throw 'MARKER_BINDING'}
$otherFiles=@($files|Where-Object FullName -ne $marker.FullName);$others=@($otherFiles)+@($dirs);$maxTicks=[int64]0
foreach($item in $others){if($item.LastWriteTimeUtc.Ticks-gt$maxTicks){$maxTicks=[int64]$item.LastWriteTimeUtc.Ticks}}
$atOrAfter=@($others|Where-Object{$_.LastWriteTimeUtc.Ticks-ge$marker.LastWriteTimeUtc.Ticks});$margin=[int64]($marker.LastWriteTimeUtc.Ticks-$maxTicks)
if($atOrAfter.Count-ne0-or$margin-le0){throw 'MARKER_ORDER'}

$jsonFail=0;foreach($file in @($files|Where-Object Extension -eq '.json')){try{$null=Get-Content -LiteralPath $file.FullName -Raw|ConvertFrom-Json}catch{$jsonFail++}}
$csvFail=0;foreach($file in @($files|Where-Object Extension -eq '.csv')){try{$null=@(Import-Csv -LiteralPath $file.FullName)}catch{$csvFail++}}
$ads=0;foreach($item in $allItems){$streams=@(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop);$ads+=@($streams|Where-Object Stream -ne ':$DATA').Count}
$cachePyc=@($files|Where-Object{$_.Name-like'*.pyc'-or$_.FullName-match'(__pycache__|[\\/]texcache[\\/])'}).Count
$reparse=@($allItems|Where-Object{($_.Attributes-band[IO.FileAttributes]::ReparsePoint)-ne0}).Count
if($jsonFail-ne0-or$csvFail-ne0-or$ads-ne0-or$cachePyc-ne0-or$reparse-ne0){throw 'HYGIENE'}

$oldNow=Snapshot $oldRoot;$s1=Snapshot $destRoot;Start-Sleep -Milliseconds 300;$s2=Snapshot $destRoot
if($oldNow.sha256-ne[string]$cr.old_source_snapshot_before_sha256-or$oldNow.sha256-ne[string]$cr.old_source_snapshot_final_sha256-or$s1.sha256-ne$s2.sha256-or$s1.sha256-ne[string]$cr.destination_snapshot1_sha256-or$s1.sha256-ne[string]$cr.destination_snapshot2_sha256){throw 'SNAPSHOT_DRIFT'}
$out=[ordered]@{schema='P126_R19A_AUDITOR_RESULT_V1';success=$true;handoff_id=$handoff;operation=$operation;verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';invocation_count=1;retry_count=0;copied_count=9;old_controls_copied=0;payload_count=11;control_count=3;ordinary_count=14;directory_count=$dirs.Count;copy_identity_errors=$identityErrors;manifest_identity_errors=$manifestErrors;readonly_failures=$roFail.Count;marker_lines=$markerLines.Count;marker_keys=$markerMap.Count;marker_bad=$bad;marker_sha256=Sha $marker.FullName;strict_margin_ticks=$margin;at_or_after_excluding_marker=$atOrAfter.Count;old_source_snapshot_sha256=$oldNow.sha256;destination_snapshot1_sha256=$s1.sha256;destination_snapshot2_sha256=$s2.sha256;postmarker_drift=0;json_parse_failures=$jsonFail;csv_parse_failures=$csvFail;ads_nondefault=$ads;cache_pyc=$cachePyc;reparse_points=$reparse;business_evidence_rerun=$false;completed_utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText($auditResult,($out|ConvertTo-Json -Depth 7),$utf8)
[IO.File]::SetAttributes($auditResult,[IO.File]::GetAttributes($auditResult)-bor[IO.FileAttributes]::ReadOnly)
