Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R116-P126-SA2-STATIC-TEXT-CURVE-COLLISION-PATCH-CONTROL-RESEAL-V2-20260828'
$operation = 'P126_R116_R19_STATIC_EVIDENCE_ONLY_CONTROL_RESEAL_V2'
$oldRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_R116_20260828'
$destRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R19A_SA2_STATIC_TEXT_CURVE_COLLISION_PATCH_CONTROL_RESEAL_R116_20260828'
$stage = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19A_WRITE_STOPPED_STAGE_V2_20260828'
$result = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R19A_CONTROLLER_RESULT_V2_20260828.json'
$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C08\fig_v1_c08_coordinate.tex'
$controllerPath = $MyInvocation.MyCommand.Path
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
function OrderedMap([object[]]$Rows,[string]$Field) {
  $map = [Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
  foreach ($row in @($Rows)) { $key=Canon ([string]$row.$Field); if(-not $map.TryAdd($key,$row)){throw "DUPLICATE_$key"} }
  $map
}

if (Test-Path -LiteralPath $destRoot) { throw 'DESTINATION_EXISTS' }
if ((Test-Path -LiteralPath $stage) -or (Test-Path -LiteralPath $result)) { throw 'EXTERNAL_OUTPUT_EXISTS' }
$controllerItem = Get-Item -LiteralPath $controllerPath -Force
if (($controllerItem.Attributes -band [IO.FileAttributes]::ReadOnly) -eq 0) { throw 'CONTROLLER_NOT_READONLY' }
$sourceItemBefore = Get-Item -LiteralPath $source -Force
$sourceShaBefore = Sha $source
if ($sourceItemBefore.Length -ne 4809 -or $sourceShaBefore -ne '4CE06E3B00402A6C14774CC95D86348D4056B493C030CADDB9BB53DC53C6AAC2') { throw 'SOURCE_IDENTITY' }
$oldManifest = Join-Path $oldRoot 'PAYLOAD_MANIFEST.csv'
$oldManifestSha = Sha $oldManifest
if ($oldManifestSha -ne 'E0155ECCD15A0E2BD0BC1FD270D8C913AD24C6A6577BF557867DE030D87EFF49') { throw 'OLD_MANIFEST_IDENTITY' }
$oldRows = @(Import-Csv -LiteralPath $oldManifest)
if ($oldRows.Count -ne 9) { throw 'OLD_ROW_COUNT' }
$oldMap = OrderedMap $oldRows 'relative_path'
$resolvedOld = [Collections.Generic.List[object]]::new()
foreach ($rel in $oldMap.Keys) {
  $row=$oldMap[$rel];$srcPath=Inside $oldRoot $rel;$item=Get-Item -LiteralPath $srcPath -Force
  if($item.PSIsContainer-or$item.Length-ne[int64]$row.bytes-or(Sha $srcPath)-ne[string]$row.sha256-or$item.CreationTimeUtc.Ticks-ne[int64]$row.creation_time_utc_ticks-or$item.LastWriteTimeUtc.Ticks-ne[int64]$row.last_write_time_utc_ticks){throw "OLD_IDENTITY_$rel"}
  $resolvedOld.Add([pscustomobject]@{relative_path=$rel;source_path=$srcPath;bytes=[int64]$item.Length;sha256=Sha $srcPath;creation_time_utc_ticks=[int64]$item.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$item.LastWriteTimeUtc.Ticks})
}
$oldBefore=Snapshot $oldRoot

$null=[IO.Directory]::CreateDirectory($destRoot)
$copyRows=[Collections.Generic.List[object]]::new()
foreach($row in $resolvedOld){
  $dstPath=Inside $destRoot $row.relative_path;$parent=[IO.Path]::GetDirectoryName($dstPath)
  if(-not[string]::Equals($parent,$destRoot,[StringComparison]::OrdinalIgnoreCase)){$null=[IO.Directory]::CreateDirectory($parent)}
  [IO.File]::Copy($row.source_path,$dstPath,$false)
  [IO.File]::SetCreationTimeUtc($dstPath,[DateTime]::new($row.creation_time_utc_ticks,[DateTimeKind]::Utc));[IO.File]::SetLastWriteTimeUtc($dstPath,[DateTime]::new($row.last_write_time_utc_ticks,[DateTimeKind]::Utc))
  $dst=Get-Item -LiteralPath $dstPath -Force
  if($dst.Length-ne$row.bytes-or(Sha $dstPath)-ne$row.sha256-or$dst.CreationTimeUtc.Ticks-ne$row.creation_time_utc_ticks-or$dst.LastWriteTimeUtc.Ticks-ne$row.last_write_time_utc_ticks){throw "COPY_IDENTITY_$($row.relative_path)"}
  $copyRows.Add([pscustomobject][ordered]@{relative_path=$row.relative_path;source_path=$row.source_path;destination_path=$dstPath;bytes=$row.bytes;sha256=$row.sha256;creation_time_utc_ticks=$row.creation_time_utc_ticks;last_write_time_utc_ticks=$row.last_write_time_utc_ticks})
}
$oldAfterCopy=Snapshot $oldRoot
if($oldBefore.sha256-ne$oldAfterCopy.sha256){throw 'OLD_ROOT_DRIFT_COPY'}

$copyPath=Join-Path $destRoot 'COPY_IDENTITY.csv';[IO.File]::WriteAllLines($copyPath,@($copyRows|ConvertTo-Csv -NoTypeInformation),$utf8);$copySha=Sha $copyPath
$provPath=Join-Path $destRoot 'COPY_PROVENANCE.json'
$preservedFields=@('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')
$provenance=[ordered]@{schema='P126_R19A_COPY_PROVENANCE_V2';handoff_id=$handoff;operation=$operation;verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';source_root=$oldRoot;destination_root=$destRoot;old_manifest_path=$oldManifest;old_manifest_sha256=$oldManifestSha;copy_identity_path=$copyPath;copy_identity_sha256=$copySha;copied_count=9;old_controls_copied=0;added_payload_count=2;payload_count=11;preserved_fields=$preservedFields;source_snapshot_before_sha256=$oldBefore.sha256;source_snapshot_after_copy_sha256=$oldAfterCopy.sha256;source_bytes=4809;source_sha256=$sourceShaBefore;source_last_write_utc_ticks=[int64]$sourceItemBefore.LastWriteTimeUtc.Ticks;reverse_bytes=4686;reverse_sha256='2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405';business_evidence_rerun=$false}
[IO.File]::WriteAllText($provPath,($provenance|ConvertTo-Json -Depth 7),$utf8);$provSha=Sha $provPath

$payloadFiles=@(Get-ChildItem -LiteralPath $destRoot -File -Recurse -Force|Sort-Object FullName)
if($payloadFiles.Count-ne11){throw 'PAYLOAD_COUNT'}
$manifestRows=foreach($file in $payloadFiles){[pscustomobject][ordered]@{relative_path=([IO.Path]::GetRelativePath($destRoot,$file.FullName).Replace([string][char]92,[string][char]47));bytes=[int64]$file.Length;sha256=Sha $file.FullName;creation_time_utc_ticks=[int64]$file.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[int64]$file.LastWriteTimeUtc.Ticks}}
$null=OrderedMap @($manifestRows) 'relative_path'
$manifestPath=Join-Path $destRoot 'PAYLOAD_MANIFEST.csv';[IO.File]::WriteAllLines($manifestPath,@($manifestRows|ConvertTo-Csv -NoTypeInformation),$utf8);$manifestSha=Sha $manifestPath
$sealAuditPath=Join-Path $destRoot 'SEAL_AUDIT.json'
$sealAudit=[ordered]@{schema='P126_R19A_SEAL_AUDIT_V2';handoff_id=$handoff;operation=$operation;verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';source_root=$oldRoot;destination_root=$destRoot;old_manifest_path=$oldManifest;old_manifest_sha256=$oldManifestSha;copied_count=9;old_controls_copied=0;payload_count=11;control_count=3;ordinary_count=14;directory_count=1;copy_identity_path=$copyPath;copy_identity_sha256=$copySha;copy_provenance_path=$provPath;copy_provenance_sha256=$provSha;payload_manifest_path=$manifestPath;payload_manifest_sha256=$manifestSha;source_snapshot_before_sha256=$oldBefore.sha256;source_snapshot_after_copy_sha256=$oldAfterCopy.sha256;source_bytes=4809;source_sha256=$sourceShaBefore;source_last_write_utc_ticks=[int64]$sourceItemBefore.LastWriteTimeUtc.Ticks;reverse_bytes=4686;reverse_sha256='2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405';business_evidence_rerun=$false;error_count=0}
[IO.File]::WriteAllText($sealAuditPath,($sealAudit|ConvertTo-Json -Depth 7),$utf8);$sealAuditSha=Sha $sealAuditPath

$premarkerFiles=@(Get-ChildItem -LiteralPath $destRoot -File -Recurse -Force);$premarkerChildDirs=@(Get-ChildItem -LiteralPath $destRoot -Directory -Recurse -Force);$premarkerDirs=@($premarkerChildDirs)+@((Get-Item -LiteralPath $destRoot -Force))
if($premarkerFiles.Count-ne13-or$premarkerDirs.Count-ne1){throw 'PREMARKER_COUNT'}
foreach($file in $premarkerFiles){[IO.File]::SetAttributes($file.FullName,$file.Attributes-bor[IO.FileAttributes]::ReadOnly)};foreach($dir in $premarkerDirs){[IO.File]::SetAttributes($dir.FullName,$dir.Attributes-bor[IO.FileAttributes]::ReadOnly)}
$premarkerAll=@($premarkerFiles)+@($premarkerDirs);if(@($premarkerAll|Where-Object{((Get-Item -LiteralPath $_.FullName -Force).Attributes-band[IO.FileAttributes]::ReadOnly)-eq0}).Count-ne0){throw 'PREMARKER_READONLY'}

$future=[DateTime]::UtcNow.AddMinutes(10)
$markerKeys=@('SCHEMA','HANDOFF_ID','OPERATION','VERDICT','SOURCE_ROOT','DESTINATION_ROOT','OLD_MANIFEST_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','COPIED_COUNT','OLD_CONTROLS_COPIED','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','DIRECTORY_COUNT','SOURCE_BYTES','SOURCE_SHA256','REVERSE_SHA256','BUSINESS_EVIDENCE_RERUN','CONTROLLER_INVOCATION_COUNT','CONTROLLER_RETRY_COUNT','AUDITOR_INVOCATION_BUDGET','SOURCE_SNAPSHOT_SHA256','POSTMARKER_WRITES','PREPARED_UTC','MARKER_LAST_WRITE_UTC_TICKS')
$markerValues=@('P126_R19A_WRITE_STOPPED_V2',$handoff,$operation,'STATIC_ONLY_NOT_RENDERED_NOT_PASS',$oldRoot,$destRoot,$oldManifestSha,$copySha,$provSha,$manifestSha,$sealAuditSha,'9','0','11','3','14','1','4809',$sourceShaBefore,'2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405','false','1','0','1',$oldBefore.sha256,'0',[DateTime]::UtcNow.ToString('o'),[string][int64]$future.Ticks)
$markerLines=for($i=0;$i-lt$markerKeys.Count;$i++){('{0}={1}'-f$markerKeys[$i],$markerValues[$i])}
if($markerLines.Count-ne28-or@($markerLines|Where-Object{([regex]::Matches($_,'=')).Count-ne1-or$_-notmatch'^[A-Z0-9_]+=[^=]+$'-or$_.Contains("`t")-or$_-match'PLACEHOLDER|TBD|\$\{|\{\{|<[^>]+>'}).Count-ne0){throw 'MARKER_SYNTAX'}
[IO.File]::WriteAllLines($stage,$markerLines,$utf8);[IO.File]::SetLastWriteTimeUtc($stage,$future);[IO.File]::SetAttributes($stage,[IO.File]::GetAttributes($stage)-bor[IO.FileAttributes]::ReadOnly)
$markerPath=Join-Path $destRoot 'WRITE_STOPPED';[IO.File]::Move($stage,$markerPath)

$destSnapshot1=Snapshot $destRoot;Start-Sleep -Milliseconds 300;$destSnapshot2=Snapshot $destRoot;$oldFinal=Snapshot $oldRoot
$files=@(Get-ChildItem -LiteralPath $destRoot -File -Recurse -Force);$childDirs=@(Get-ChildItem -LiteralPath $destRoot -Directory -Recurse -Force);$dirs=@($childDirs)+@((Get-Item -LiteralPath $destRoot -Force));$allItems=@($files)+@($dirs)
$marker=Get-Item -LiteralPath $markerPath -Force;$otherFiles=@($files|Where-Object FullName -ne $marker.FullName);$others=@($otherFiles)+@($dirs);$maxTicks=[int64]0
foreach($item in $others){if($item.LastWriteTimeUtc.Ticks-gt$maxTicks){$maxTicks=[int64]$item.LastWriteTimeUtc.Ticks}}
$atOrAfter=@($others|Where-Object{$_.LastWriteTimeUtc.Ticks-ge$marker.LastWriteTimeUtc.Ticks});$roFail=@($allItems|Where-Object{($_.Attributes-band[IO.FileAttributes]::ReadOnly)-eq0})
$sourceItemFinal=Get-Item -LiteralPath $source -Force;$sourceShaFinal=Sha $source
if($files.Count-ne14-or$dirs.Count-ne1-or$roFail.Count-ne0-or$atOrAfter.Count-ne0-or$destSnapshot1.entries-ne15-or$destSnapshot1.sha256-ne$destSnapshot2.sha256-or$oldBefore.sha256-ne$oldAfterCopy.sha256-or$oldBefore.sha256-ne$oldFinal.sha256-or$sourceItemFinal.Length-ne$sourceItemBefore.Length-or$sourceShaFinal-ne$sourceShaBefore-or$sourceItemFinal.LastWriteTimeUtc.Ticks-ne$sourceItemBefore.LastWriteTimeUtc.Ticks-or(Test-Path -LiteralPath $stage)){throw 'POSTMARKER_GATE'}

$out=[ordered]@{schema='P126_R19A_CONTROLLER_RESULT_V2';success=$true;handoff_id=$handoff;operation=$operation;verdict='STATIC_ONLY_NOT_RENDERED_NOT_PASS';source_root=$oldRoot;destination_root=$destRoot;old_manifest_path=$oldManifest;old_manifest_sha256=$oldManifestSha;controller_path=$controllerPath;controller_bytes=[int64]$controllerItem.Length;controller_sha256=Sha $controllerPath;controller_readonly=$true;invocation_count=1;retry_count=0;natural_exit=$true;copied_count=9;old_controls_copied=0;payload_count=11;control_count=3;ordinary_count=14;directory_count=$dirs.Count;copy_identity_path=$copyPath;copy_identity_sha256=$copySha;copy_provenance_path=$provPath;copy_provenance_sha256=$provSha;payload_manifest_path=$manifestPath;payload_manifest_sha256=$manifestSha;seal_audit_path=$sealAuditPath;seal_audit_sha256=$sealAuditSha;marker_path=$markerPath;marker_bytes=[int64]$marker.Length;marker_sha256=Sha $markerPath;marker_lines=$markerLines.Count;marker_keys=$markerKeys.Count;marker_ticks=[int64]$marker.LastWriteTimeUtc.Ticks;strict_margin_ticks=[int64]($marker.LastWriteTimeUtc.Ticks-$maxTicks);at_or_after_excluding_marker=$atOrAfter.Count;readonly_failures=$roFail.Count;source_bytes=[int64]$sourceItemFinal.Length;source_sha256=$sourceShaFinal;source_last_write_utc_ticks=[int64]$sourceItemFinal.LastWriteTimeUtc.Ticks;reverse_bytes=4686;reverse_sha256='2887758F5CC94987BE750E1EC53B555FB88CE8F71B7260CABBE0A17DDF237405';old_source_snapshot_before_sha256=$oldBefore.sha256;old_source_snapshot_after_copy_sha256=$oldAfterCopy.sha256;old_source_snapshot_final_sha256=$oldFinal.sha256;old_source_snapshot_entries=$oldBefore.entries;destination_snapshot1_sha256=$destSnapshot1.sha256;destination_snapshot2_sha256=$destSnapshot2.sha256;destination_snapshot_entries=$destSnapshot1.entries;stage_absent=(-not(Test-Path -LiteralPath $stage));postmarker_drift=0;postmarker_root_writes=0;business_evidence_rerun=$false;completed_utc=[DateTime]::UtcNow.ToString('o')}
[IO.File]::WriteAllText($result,($out|ConvertTo-Json -Depth 8),$utf8);[IO.File]::SetAttributes($result,[IO.File]::GetAttributes($result)-bor[IO.FileAttributes]::ReadOnly)
