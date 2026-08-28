$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R7A-CONTROL-RESEAL-V1-20260828'
$operation = 'P126_R115_R7_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V1'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R7A_SA2_ABSOLUTE_LEGEND_KEY_PATCH_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$stagePath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7A_WRITE_STOPPED.stage'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7A_CONTROL_RESEAL_CONTROLLER_RESULT_20260828.json'
$auditResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7A_CONTROL_RESEAL_AUDIT_20260828.json'
$reportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7A_LOCAL_SA2_FAIL_REPORT_20260828.md'
$handoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\P126_R7A_LOCAL_SA2_FAIL_HANDOFF_20260828.md'
$verdict = 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE'
$hardDefects = @('HARD-LEGEND-X2-CONTINUOUS','HARD-LABEL6-AXIS-CONTOUR-OVERLAP','HARD-LABEL7-MARKER-ARROW-OCCLUSION')
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant() }
function Is-Readonly([IO.FileSystemInfo]$Item) { (($Item.Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) }
function Convert-CanonicalRelative([string]$Value) {
  if ([string]::IsNullOrWhiteSpace($Value)) { throw 'relative path is empty' }
  $canonical=$Value.Replace('\','/')
  $canonical=[regex]::Replace($canonical,'^(?:\./)+','')
  if([string]::IsNullOrWhiteSpace($canonical)){throw 'relative path empty after normalization'}
  if([IO.Path]::IsPathRooted($canonical)-or$canonical.StartsWith('/',[StringComparison]::Ordinal)-or$canonical-match'^[A-Za-z]:'){throw 'rooted relative path rejected'}
  $segments=@($canonical.Split('/'))
  $invalid=@($segments|Where-Object{[string]::IsNullOrEmpty([string]$_)-or[string]$_-eq'.'-or[string]$_-eq'..'-or[string]$_-match'[:*?]'})
  if($segments.Count-eq0-or$invalid.Count-ne0){throw 'unsafe relative path segment'}
  return [string]::Join('/',$segments)
}
function Resolve-Contained([string]$Base,[string]$Relative){
  $canonical=Convert-CanonicalRelative $Relative;$baseFull=[IO.Path]::GetFullPath($Base).TrimEnd('\')
  $resolved=[IO.Path]::GetFullPath((Join-Path $baseFull ($canonical.Replace('/','\'))));$prefix=$baseFull+'\'
  if(-not$resolved.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){throw 'resolved path escapes root'}
  return $resolved
}
function Get-Relative([string]$Base,[string]$Path){Convert-CanonicalRelative ([IO.Path]::GetRelativePath($Base,$Path))}
function Get-TreeSnapshot([string]$Root){
  $rows=[Collections.Generic.List[string]]::new();$items=@(@(Get-ChildItem -LiteralPath $Root -Recurse -Force)+@(Get-Item -LiteralPath $Root)|Sort-Object FullName)
  foreach($item in $items){$relative=if($item.FullName-ceq$Root){'.'}else{Get-Relative $Root $item.FullName};$kind=if($item.PSIsContainer){'D'}else{'F'};$bytes=if($item.PSIsContainer){0L}else{[long]$item.Length};$sha=if($item.PSIsContainer){''}else{Get-Sha256 $item.FullName};$rows.Add("$kind`t$relative`t$bytes`t$sha`t$($item.CreationTimeUtc.Ticks)`t$($item.LastWriteTimeUtc.Ticks)`t$([int]$item.Attributes)")}
  $text=[string]::Join("`n",$rows)+"`n";$hasher=[Security.Cryptography.SHA256]::Create();[pscustomobject]@{count=$rows.Count;sha256=[Convert]::ToHexString($hasher.ComputeHash($utf8NoBom.GetBytes($text)));rows=@($rows)}
}

foreach($path in @($auditResultPath,$reportPath,$handoffPath)){if(Test-Path -LiteralPath $path){throw "external audit output preexists: $path"}}
if(Test-Path -LiteralPath $stagePath){throw 'marker stage remains'}
$controllerResult=Get-Content -LiteralPath $controllerResultPath -Raw|ConvertFrom-Json
if($controllerResult.handoff_id-cne$handoff-or$controllerResult.operation-cne$operation-or$controllerResult.verdict-cne$verdict-or$controllerResult.controller_invocation_count-ne1-or$controllerResult.retry_count-ne0-or$controllerResult.exit_code-ne0-or-not$controllerResult.natural_exit){throw 'controller result semantic mismatch'}
$sourceSnapshotBefore=Get-TreeSnapshot $sourceRoot
if($sourceSnapshotBefore.sha256-cne$controllerResult.source_root_snapshot_before_sha256-or$controllerResult.source_root_snapshot_before_sha256-cne$controllerResult.source_root_snapshot_after_sha256){throw 'old root snapshot mismatch'}

$copyIdentityPath=Join-Path $destinationRoot 'COPY_IDENTITY.csv';$provenancePath=Join-Path $destinationRoot 'COPY_PROVENANCE.json';$manifestPath=Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv';$sealAuditPath=Join-Path $destinationRoot 'SEAL_AUDIT.json';$markerPath=Join-Path $destinationRoot 'WRITE_STOPPED'
$copyRows=@(Import-Csv -LiteralPath $copyIdentityPath);$manifestRows=@(Import-Csv -LiteralPath $manifestPath);$provenance=Get-Content -LiteralPath $provenancePath -Raw|ConvertFrom-Json;$sealAudit=Get-Content -LiteralPath $sealAuditPath -Raw|ConvertFrom-Json
if($copyRows.Count-ne188){throw 'copy identity row count'}
$copyDuplicates=@($copyRows|Group-Object -Property{[string]$_.relative_path}-CaseSensitive|Where-Object{$_.Count-ne1});if($copyDuplicates.Count-ne0){throw 'copy identity duplicates'}
$sourceFiles=@(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Force|Sort-Object{Get-Relative $sourceRoot $_.FullName});if($sourceFiles.Count-ne188){throw 'source count drift'}
$sourceMap=@{};foreach($file in $sourceFiles){$relative=Get-Relative $sourceRoot $file.FullName;if($sourceMap.ContainsKey($relative)){throw 'source duplicate'};$sourceMap[$relative]=$file}
$copyMap=@{};foreach($row in $copyRows){$relative=Convert-CanonicalRelative ([string]$row.relative_path);if($copyMap.ContainsKey($relative)){throw 'copy duplicate map'};$copyMap[$relative]=$row}
$sourceSet=@($sourceMap.Keys|Sort-Object -CaseSensitive);$copySet=@($copyMap.Keys|Sort-Object -CaseSensitive);$copySetDiff=@(Compare-Object -ReferenceObject $sourceSet -DifferenceObject $copySet -CaseSensitive)
$copyErrors=[Collections.Generic.List[string]]::new()
foreach($relative in $sourceSet){
  $src=$sourceMap[$relative];$row=$copyMap[$relative];$dst=Resolve-Contained $destinationRoot $relative
  if([string]$row.source_path-cne[IO.Path]::GetFullPath($src.FullName)-or[string]$row.destination_path-cne$dst){$copyErrors.Add("path:$relative")}
  foreach($triple in @(@('bytes',[long]$src.Length,[long]$row.bytes),@('sha',[string](Get-Sha256 $src.FullName),[string]$row.sha256),@('ctime',[long]$src.CreationTimeUtc.Ticks,[long]$row.creation_time_utc_ticks),@('mtime',[long]$src.LastWriteTimeUtc.Ticks,[long]$row.last_write_time_utc_ticks))){if($triple[1]-cne$triple[2]){$copyErrors.Add("$($triple[0]):$relative")}}
  $dstItem=Get-Item -LiteralPath $dst
  if([long]$dstItem.Length-ne[long]$row.bytes-or(Get-Sha256 $dst)-cne[string]$row.sha256-or[long]$dstItem.CreationTimeUtc.Ticks-ne[long]$row.creation_time_utc_ticks-or[long]$dstItem.LastWriteTimeUtc.Ticks-ne[long]$row.last_write_time_utc_ticks){$copyErrors.Add("destination:$relative")}
}
if($copySetDiff.Count-ne0-or$copyErrors.Count-ne0){throw 'copy identity closure failure'}

$expectedProvenance=[ordered]@{schema='P126_R7A_COPY_PROVENANCE_V1';handoff_id=$handoff;operation=$operation;source_root=[IO.Path]::GetFullPath($sourceRoot);destination_root=[IO.Path]::GetFullPath($destinationRoot);source_root_snapshot_sha256=$sourceSnapshotBefore.sha256;copied_material_count=188;added_payload_count=2;payload_count=190;control_count=3;ordinary_count=193;preserved_verdict=$verdict;business_evidence_rerun_count=0;source_controls_copied_count=0;controller_invocation_count=1;retry_count=0}
foreach($key in $expectedProvenance.Keys){if([string]$provenance.$key-cne[string]$expectedProvenance[$key]){throw "provenance binding mismatch: $key"}}
if(@($provenance.preserved_fields).Count-ne5-or[string]::Join(';',@($provenance.hard_defect_ids))-cne[string]::Join(';',$hardDefects)){throw 'provenance arrays mismatch'}
$expectedSeal=[ordered]@{schema='P126_R7A_SEAL_AUDIT_V1';handoff_id=$handoff;operation=$operation;verdict=$verdict;source_snapshot_sha256=$sourceSnapshotBefore.sha256;copied_material_count=188;source_controls_copied_count=0;payload_count=190;control_count=3;ordinary_count=193;copy_identity_rows=188;copy_set_diff_count=0;copy_identity_mismatch_count=0;payload_duplicate_count=0;business_evidence_rerun_count=0;controller_invocation_count=1;retry_count=0;auditor_invocation_budget=1}
foreach($key in $expectedSeal.Keys){if([string]$sealAudit.$key-cne[string]$expectedSeal[$key]){throw "seal audit binding mismatch: $key"}}
if([string]::Join(';',@($sealAudit.hard_defect_ids))-cne[string]::Join(';',$hardDefects)-or@( $sealAudit.errors).Count-ne0){throw 'seal audit arrays mismatch'}
if($sealAudit.copy_identity_sha256-cne(Get-Sha256 $copyIdentityPath)-or$sealAudit.copy_provenance_sha256-cne(Get-Sha256 $provenancePath)-or$sealAudit.payload_manifest_sha256-cne(Get-Sha256 $manifestPath)){throw 'seal audit hash bindings'}

$manifestDuplicates=@($manifestRows|Group-Object -Property{[string]$_.relative_path}-CaseSensitive|Where-Object{$_.Count-ne1});$controls=@('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')
$actualPayload=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force|Where-Object{(Get-Relative $destinationRoot $_.FullName)-notin$controls}|Sort-Object{Get-Relative $destinationRoot $_.FullName})
$manifestSet=@($manifestRows|ForEach-Object{Convert-CanonicalRelative ([string]$_.relative_path)}|Sort-Object -CaseSensitive);$actualSet=@($actualPayload|ForEach-Object{Get-Relative $destinationRoot $_.FullName}|Sort-Object -CaseSensitive);$manifestSetDiff=@(Compare-Object -ReferenceObject $manifestSet -DifferenceObject $actualSet -CaseSensitive)
$manifestErrors=[Collections.Generic.List[string]]::new();foreach($row in $manifestRows){$relative=Convert-CanonicalRelative ([string]$row.relative_path);$path=Resolve-Contained $destinationRoot $relative;$item=Get-Item -LiteralPath $path;if([long]$item.Length-ne[long]$row.bytes-or(Get-Sha256 $path)-cne[string]$row.sha256-or[long]$item.CreationTimeUtc.Ticks-ne[long]$row.creation_time_utc_ticks-or[long]$item.LastWriteTimeUtc.Ticks-ne[long]$row.last_write_time_utc_ticks){$manifestErrors.Add($relative)}}
if($manifestRows.Count-ne190-or$actualPayload.Count-ne190-or$manifestDuplicates.Count-ne0-or$manifestSetDiff.Count-ne0-or$manifestErrors.Count-ne0){throw 'manifest closure failure'}

$markerLines=@(Get-Content -LiteralPath $markerPath);$badMarker=@($markerLines|Where-Object{$_-notmatch'^[A-Z0-9_]+=[^\t\r\n]+$'});$markerKeys=@($markerLines|ForEach-Object{($_-split'=',2)[0]});$duplicateMarkerKeys=@($markerKeys|Group-Object -Property{[string]$_}-CaseSensitive|Where-Object{$_.Count-ne1});$markerMap=@{};foreach($line in $markerLines){$parts=$line-split'=',2;$markerMap[$parts[0]]=$parts[1]}
$expectedMarker=[ordered]@{SCHEMA='P126_R7A_WRITE_STOPPED_V1';HANDOFF_ID=$handoff;OPERATION=$operation;UID='FIG-P126-01';ROLE='SA2';VERDICT=$verdict;ROOT=$destinationRoot;SOURCE_ROOT=$sourceRoot;COPIED_MATERIAL_COUNT='188';ADDED_PAYLOAD_COUNT='2';PAYLOAD_COUNT='190';CONTROL_COUNT='3';ORDINARY_COUNT='193';SOURCE_ROOT_SNAPSHOT_SHA256=$sourceSnapshotBefore.sha256;COPY_IDENTITY_SHA256=Get-Sha256 $copyIdentityPath;COPY_PROVENANCE_SHA256=Get-Sha256 $provenancePath;PAYLOAD_MANIFEST_SHA256=Get-Sha256 $manifestPath;SEAL_AUDIT_SHA256=Get-Sha256 $sealAuditPath;BUSINESS_EVIDENCE_RERUN_COUNT='0';CONTROLLER_INVOCATION_COUNT='1';RETRY_COUNT='0';AUDITOR_INVOCATION_BUDGET='1';HARD_DEFECT_IDS=[string]::Join(';',$hardDefects)}
foreach($key in $expectedMarker.Keys){if(-not$markerMap.ContainsKey($key)-or[string]$markerMap[$key]-cne[string]$expectedMarker[$key]){throw "marker binding mismatch: $key"}}
if($markerLines.Count-ne25-or$markerKeys.Count-ne25-or$badMarker.Count-ne0-or$duplicateMarkerKeys.Count-ne0-or-not$markerMap.ContainsKey('PREPARED_UTC')-or-not$markerMap.ContainsKey('WSTOP_LAST_WRITE_UTC_TICKS')){throw 'marker syntax/exact key set failure'}

$allFiles=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force);$allDirs=@(@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force)+@(Get-Item -LiteralPath $destinationRoot));$writableFiles=@($allFiles|Where-Object{-not(Is-Readonly $_)});$writableDirs=@($allDirs|Where-Object{-not(Is-Readonly $_)});if($allFiles.Count-ne193-or$writableFiles.Count-ne0-or$writableDirs.Count-ne0){throw 'ordinary/readonly failure'}
$marker=Get-Item -LiteralPath $markerPath;$otherItems=@(@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force|Where-Object{$_.FullName-cne$markerPath})+@(Get-Item -LiteralPath $destinationRoot));$maxOtherTicks=[long](($otherItems|Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks);$atOrAfter=@($otherItems|Where-Object{$_.LastWriteTimeUtc.Ticks-ge$marker.LastWriteTimeUtc.Ticks});if($marker.LastWriteTimeUtc.Ticks-le$maxOtherTicks-or$atOrAfter.Count-ne0-or[long]$markerMap.WSTOP_LAST_WRITE_UTC_TICKS-ne[long]$marker.LastWriteTimeUtc.Ticks){throw 'marker timing failure'}
$extraStreams=[Collections.Generic.List[string]]::new();foreach($file in $allFiles){foreach($stream in @(Get-Item -LiteralPath $file.FullName -Stream * -ErrorAction SilentlyContinue)){if($stream.Stream-cne':$DATA'){$extraStreams.Add("$($file.FullName):$($stream.Stream)")}}};$pyc=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force|Where-Object{$_.Name-match'\.(pyc|pyo)$'});$badCache=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force|Where-Object{$_.Name-in@('__pycache__','.pytest_cache','.mypy_cache')});$reparse=@(@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force)+@(Get-Item -LiteralPath $destinationRoot)|Where-Object{($_.Attributes-band[IO.FileAttributes]::ReparsePoint)-ne0})
$csvFiles=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Filter'*.csv'-Force);$jsonFiles=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Filter'*.json'-Force);$parseErrors=[Collections.Generic.List[string]]::new();foreach($file in $csvFiles){try{[void]@(Import-Csv -LiteralPath $file.FullName)}catch{$parseErrors.Add($file.FullName)}};foreach($file in $jsonFiles){try{[void](Get-Content -LiteralPath $file.FullName -Raw|ConvertFrom-Json)}catch{$parseErrors.Add($file.FullName)}}
$sourceSnapshotAfter=Get-TreeSnapshot $sourceRoot;$destinationSnapshot1=Get-TreeSnapshot $destinationRoot;Start-Sleep -Milliseconds 250;$destinationSnapshot2=Get-TreeSnapshot $destinationRoot
if($sourceSnapshotAfter.sha256-cne$sourceSnapshotBefore.sha256-or$destinationSnapshot1.sha256-cne$destinationSnapshot2.sha256-or$extraStreams.Count-ne0-or$pyc.Count-ne0-or$badCache.Count-ne0-or$reparse.Count-ne0-or$parseErrors.Count-ne0){throw 'postmarker/source/hygiene/parse failure'}
if($controllerResult.destination_snapshot1_sha256-cne$controllerResult.destination_snapshot2_sha256-or$controllerResult.destination_snapshot2_sha256-cne$destinationSnapshot1.sha256-or$controllerResult.ordinary_count-ne193-or$controllerResult.payload_count-ne190-or$controllerResult.control_count-ne3){throw 'controller snapshot/count binding failure'}

$audit=[ordered]@{schema='P126_R7A_EXTERNAL_AUDIT_V1';handoff_id=$handoff;operation=$operation;verdict=$verdict;auditor_invocation_count=1;retry_count=0;exit_code=0;copied_material_count=188;payload_count=190;control_count=3;ordinary_count=$allFiles.Count;directory_count=$allDirs.Count;copy_set_diff_count=$copySetDiff.Count;copy_identity_error_count=$copyErrors.Count;manifest_set_diff_count=$manifestSetDiff.Count;manifest_identity_error_count=$manifestErrors.Count;readonly_files=@($allFiles|Where-Object{Is-Readonly $_}).Count;readonly_directories=@($allDirs|Where-Object{Is-Readonly $_}).Count;marker_line_count=$markerLines.Count;marker_unique_key_count=@($markerKeys|Sort-Object -Unique).Count;marker_bad_count=$badMarker.Count;marker_sha256=Get-Sha256 $markerPath;marker_ticks=[long]$marker.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]$marker.LastWriteTimeUtc.Ticks-$maxOtherTicks;at_or_after_excluding_marker=$atOrAfter.Count;old_root_before_sha256=$sourceSnapshotBefore.sha256;old_root_after_sha256=$sourceSnapshotAfter.sha256;destination_snapshot1_sha256=$destinationSnapshot1.sha256;destination_snapshot2_sha256=$destinationSnapshot2.sha256;postmarker_content_attribute_diff_count=0;csv_parse_count=$csvFiles.Count;json_parse_count=$jsonFiles.Count;parse_error_count=$parseErrors.Count;ads_count=$extraStreams.Count;pyc_count=$pyc.Count;bad_cache_count=$badCache.Count;reparse_count=$reparse.Count;errors=@()}
[IO.File]::WriteAllText($auditResultPath,($audit|ConvertTo-Json -Depth 7)+"`n",$utf8NoBom)
$report=@"
# P126 R7A sealed local SA2 failure report

The R7 business direction is preserved without rerun as `LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE`: N58/C1653 and three hard defects (continuous x2 legend sample, crossed label6, occluded label7). R7A is evidence-only.

R7A copied188 material, added2 provenance payload, bound payload190, controls3 and ordinary193. All files and directories including root are ReadOnly. WSTOP is unique strict-latest by $($audit.strict_latest_margin_ticks) ticks; at-or-after excluding marker0; postmarker content/attribute0; old R7 root0 change; CSV/JSON parse, ADS, cache-pyc and reparse all0.

No PDF/render/N-C/pair/manual/math/semantic rerun, source change, TeX, Git, commit, fresh role or second UID occurred. Main source-scope adjudication is requested; no patch is self-authorized.
"@
$handoffText=@"
HANDOFF_ID=$handoff
OPERATION=$operation
UID=FIG-P126-01
ROLE=SA2
VERDICT=$verdict
SEALED_ROOT=$destinationRoot
COPIED_MATERIAL_COUNT=188
PAYLOAD_COUNT=190
CONTROL_COUNT=3
ORDINARY_COUNT=193
HARD_DEFECT_IDS=$([string]::Join(';',$hardDefects))
WSTOP_SHA256=$($audit.marker_sha256)
WSTOP_STRICT_LATEST_MARGIN_TICKS=$($audit.strict_latest_margin_ticks)
AT_OR_AFTER_EXCLUDING_MARKER=0
POSTMARKER_CONTENT_ATTRIBUTE_DIFF_COUNT=0
OLD_ROOT_CHANGE_COUNT=0
NEXT_ROUTE_REQUEST=MAIN_NARROW_SINGLE_SOURCE_SCOPE
SELF_ACCEPTED=false
"@
[IO.File]::WriteAllText($reportPath,$report,$utf8NoBom);[IO.File]::WriteAllText($handoffPath,$handoffText,$utf8NoBom);(Get-Item -LiteralPath $auditResultPath).IsReadOnly=$true;(Get-Item -LiteralPath $reportPath).IsReadOnly=$true;(Get-Item -LiteralPath $handoffPath).IsReadOnly=$true
[ordered]@{audit=$audit;report=[ordered]@{path=$reportPath;bytes=(Get-Item -LiteralPath $reportPath).Length;sha256=Get-Sha256 $reportPath};handoff=[ordered]@{path=$handoffPath;bytes=(Get-Item -LiteralPath $handoffPath).Length;sha256=Get-Sha256 $handoffPath}}|ConvertTo-Json -Depth 8
