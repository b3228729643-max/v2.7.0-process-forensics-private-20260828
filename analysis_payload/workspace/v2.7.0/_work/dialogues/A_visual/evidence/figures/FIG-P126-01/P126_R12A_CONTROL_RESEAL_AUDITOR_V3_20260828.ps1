Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$handoff = 'A-R115-P126-SA2-DIRECT-BUILD-R12-CONTROL-RESEAL-V3-20260828'
$operation = 'P126_R115_R12_SA2_EVIDENCE_ONLY_CONTROL_RESEAL_V3'
$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12_SA2_LABEL6_REPOSITION_R115_DIRECT_BUILD_20260828'
$destinationRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P126-01\STRICT_R12A_SA2_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$parent = [IO.Path]::GetDirectoryName($destinationRoot)
$stageMarker = Join-Path $parent 'P126_R12A_WRITE_STOPPED_STAGE_V3_20260828.tmp'
$controller = Join-Path $parent 'P126_R12A_CONTROL_RESEAL_CONTROLLER_V3_20260828.ps1'
$controllerResult = Join-Path $parent 'P126_R12A_CONTROL_RESEAL_CONTROLLER_RESULT_V3_20260828.json'
$auditorResult = Join-Path $parent 'P126_R12A_CONTROL_RESEAL_AUDITOR_RESULT_V3_20260828.json'
$report = Join-Path $parent 'P126_R12_LOCAL_SA2_REPORT_20260828.md'
$handoffFile = Join-Path $parent 'P126_R12_LOCAL_SA2_HANDOFF_20260828.md'
$auditor = $MyInvocation.MyCommand.Path
$utf8 = [Text.UTF8Encoding]::new($false)
$newControlNames = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')

function Get-Sha256([string]$Path) { (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash }

function Get-CanonicalRelative([string]$Base, [string]$Path) {
  $baseFull = [IO.Path]::GetFullPath($Base).TrimEnd('\')
  $pathFull = [IO.Path]::GetFullPath($Path)
  $relative = [IO.Path]::GetRelativePath($baseFull,$pathFull).Replace('\','/')
  $relative=[regex]::Replace($relative,'^(?:\./)+','')
  if ([string]::IsNullOrWhiteSpace($relative) -or $relative -eq '.' -or [IO.Path]::IsPathRooted($relative) -or $relative.StartsWith('/',[StringComparison]::Ordinal) -or $relative.StartsWith('../',[StringComparison]::Ordinal) -or $relative.Contains('/../',[StringComparison]::Ordinal)) { throw "unsafe relative path: $relative" }
  $segments=@($relative.Split('/'))
  if (@($segments|Where-Object{[string]::IsNullOrWhiteSpace($_) -or $_ -eq '.' -or $_ -eq '..'}).Count -ne 0) { throw "unsafe segment: $relative" }
  $resolved=[IO.Path]::GetFullPath((Join-Path $baseFull $relative.Replace('/','\')))
  if (-not ($resolved.Equals($baseFull,[StringComparison]::OrdinalIgnoreCase) -or $resolved.StartsWith($baseFull+'\',[StringComparison]::OrdinalIgnoreCase))) { throw "path escapes root: $relative" }
  $relative
}

function Test-ReadonlyAttribute([string]$Path) { (((Get-Item -LiteralPath $Path -Force).Attributes -band [IO.FileAttributes]::ReadOnly) -ne 0) }

function Get-FullTreeAdsAudit([string]$Base) {
  $rootItem=Get-Item -LiteralPath $Base -Force -ErrorAction Stop
  $childItems=@(Get-ChildItem -LiteralPath $Base -Recurse -Force -ErrorAction Stop)
  $items=@($rootItem)+$childItems
  [long]$nondefaultCount=0
  [long]$streamCount=0
  foreach($item in $items){
    $streams=@(Get-Item -LiteralPath $item.FullName -Stream * -Force -ErrorAction Stop)
    $streamCount+=$streams.Count
    $nondefaultCount+=@($streams|Where-Object{$_.Stream -ne ':$DATA'}).Count
  }
  [ordered]@{item_count=$items.Count;file_count=@($childItems|Where-Object{-not $_.PSIsContainer}).Count;child_directory_count=@($childItems|Where-Object{$_.PSIsContainer}).Count;root_count=1;stream_count=$streamCount;nondefault_ads_count=$nondefaultCount}
}

function Get-IdentityRow([string]$Base,[string]$Path) {
  $item=Get-Item -LiteralPath $Path -Force
  [ordered]@{relative_path=(Get-CanonicalRelative $Base $Path);resolved_path=[IO.Path]::GetFullPath($item.FullName);bytes=[long]$item.Length;sha256=(Get-Sha256 $item.FullName);creation_time_utc_ticks=[long]$item.CreationTimeUtc.Ticks;last_write_time_utc_ticks=[long]$item.LastWriteTimeUtc.Ticks}
}

function Get-TextSha256([string[]]$Lines) {
  $bytes=$utf8.GetBytes(($Lines -join "`n")+"`n")
  $hasher=[Security.Cryptography.SHA256]::Create()
  try { ([BitConverter]::ToString($hasher.ComputeHash($bytes))).Replace('-','') } finally { $hasher.Dispose() }
}

function Get-TreeSnapshot([string]$Base) {
  $lines=[Collections.Generic.List[string]]::new()
  $rootItem=Get-Item -LiteralPath $Base -Force
  $lines.Add(".|D|0|-|$($rootItem.CreationTimeUtc.Ticks)|$($rootItem.LastWriteTimeUtc.Ticks)|$([int]$rootItem.Attributes)")
  foreach($directory in @(Get-ChildItem -LiteralPath $Base -Recurse -Directory -Force)){
    $relative=Get-CanonicalRelative $Base $directory.FullName
    $lines.Add("$relative|D|0|-|$($directory.CreationTimeUtc.Ticks)|$($directory.LastWriteTimeUtc.Ticks)|$([int]$directory.Attributes)")
  }
  foreach($file in @(Get-ChildItem -LiteralPath $Base -Recurse -File -Force)){
    $relative=Get-CanonicalRelative $Base $file.FullName
    $lines.Add("$relative|F|$($file.Length)|$(Get-Sha256 $file.FullName)|$($file.CreationTimeUtc.Ticks)|$($file.LastWriteTimeUtc.Ticks)|$([int]$file.Attributes)")
  }
  $array=$lines.ToArray();[Array]::Sort($array,[StringComparer]::Ordinal)
  [ordered]@{entry_count=$array.Count;sha256=(Get-TextSha256 $array)}
}

foreach($required in @($sourceRoot,$destinationRoot,$controller,$controllerResult,$report,$handoffFile)){if(-not(Test-Path -LiteralPath $required)){throw "required path missing: $required"}}
if(Test-Path -LiteralPath $stageMarker){throw 'stage marker still exists'}
if(Test-Path -LiteralPath $auditorResult){throw 'auditor result preexists'}
if(-not(Test-ReadonlyAttribute $auditor)){throw 'auditor is not ReadOnly'}

$controllerData=Get-Content -LiteralPath $controllerResult -Raw|ConvertFrom-Json
if(-not $controllerData.success -or $controllerData.exit_code -ne 0 -or $controllerData.controller_invocation_count -ne 1 -or $controllerData.retry_count -ne 0 -or $controllerData.handoff_id -cne $handoff -or $controllerData.operation -cne $operation){throw 'controller result contract failure'}
if([long]$controllerData.controller.bytes -ne (Get-Item -LiteralPath $controller).Length -or [string]$controllerData.controller.sha256 -cne (Get-Sha256 $controller)){throw 'controller identity mismatch'}

$sourceSnapshot=Get-TreeSnapshot $sourceRoot
if([string]$sourceSnapshot['sha256'] -cne [string]$controllerData.source_snapshot_before.sha256 -or [string]$sourceSnapshot['sha256'] -cne [string]$controllerData.source_snapshot_after.sha256 -or [long]$sourceSnapshot['entry_count'] -ne [long]$controllerData.source_snapshot_before.entry_count){throw 'source root before/after mismatch'}
$sourceAdsAudit=Get-FullTreeAdsAudit $sourceRoot
if([long]$sourceAdsAudit['nondefault_ads_count'] -ne 0 -or [long]$sourceAdsAudit['file_count'] -ne 137 -or [long]$sourceAdsAudit['child_directory_count'] -ne 9 -or [long]$sourceAdsAudit['root_count'] -ne 1){throw 'source full-tree ADS audit failure'}
if([long]$controllerData.source_full_tree_ads.nondefault_ads_count -ne 0 -or [long]$controllerData.source_full_tree_ads.item_count -ne [long]$sourceAdsAudit['item_count']){throw 'controller source ADS binding failure'}
$sourceFiles=@(Get-ChildItem -LiteralPath $sourceRoot -Recurse -File -Force)
if($sourceFiles.Count -ne 137 -or [long](($sourceFiles|Measure-Object Length -Sum).Sum) -ne 106101530){throw 'source count/bytes failure'}
$sourceRows=@($sourceFiles|ForEach-Object{Get-IdentityRow $sourceRoot $_.FullName}|Sort-Object -Property { [string]$_['relative_path'] })
if(@($sourceRows|Group-Object -Property { [string]$_['relative_path'] }|Where-Object{$_.Count -ne 1}).Count -ne 0){throw 'source duplicate path'}
$sourceMap=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach($row in $sourceRows){if(-not $sourceMap.TryAdd([string]$row['relative_path'],$row)){throw 'source dictionary duplicate'}}

$copyPath=Join-Path $destinationRoot 'COPY_IDENTITY.csv'
$provenancePath=Join-Path $destinationRoot 'COPY_PROVENANCE.json'
$manifestPath=Join-Path $destinationRoot 'PAYLOAD_MANIFEST.csv'
$sealAuditPath=Join-Path $destinationRoot 'SEAL_AUDIT.json'
$markerPath=Join-Path $destinationRoot 'WRITE_STOPPED'
foreach($required in @($copyPath,$provenancePath,$manifestPath,$sealAuditPath,$markerPath)){if(-not(Test-Path -LiteralPath $required -PathType Leaf)){throw "control/payload missing: $required"}}
$copyRows=@(Import-Csv -LiteralPath $copyPath)
if($copyRows.Count -ne 137 -or @($copyRows|Group-Object -Property { [string]$_.relative_path }|Where-Object{$_.Count -ne 1}).Count -ne 0){throw 'copy identity row/set failure'}
$copyMap=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach($row in $copyRows){if(-not $copyMap.TryAdd([string]$row.relative_path,$row)){throw 'copy dictionary duplicate'}}
if($copyMap.Count -ne $sourceMap.Count){throw 'copy/source set count mismatch'}
foreach($key in @($sourceMap.Keys)){
  if(-not $copyMap.ContainsKey($key)){throw "copy missing source key: $key"}
  $source=$sourceMap[$key];$copy=$copyMap[$key]
  if([string]$copy.source_path -cne [string]$source['resolved_path']){throw "copy source path mismatch: $key"}
  $expectedDestination=[IO.Path]::GetFullPath((Join-Path $destinationRoot $key.Replace('/','\')))
  if([string]$copy.destination_path -cne $expectedDestination){throw "copy destination path mismatch: $key"}
  foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')){if([string]$copy.$field -cne [string]$source[$field]){throw "copy source field mismatch: $key/$field"}}
  $destination=Get-IdentityRow $destinationRoot $expectedDestination
  foreach($field in @('relative_path','bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')){if([string]$copy.$field -cne [string]$destination[$field]){throw "copy destination field mismatch: $key/$field"}}
}

$provenance=Get-Content -LiteralPath $provenancePath -Raw|ConvertFrom-Json
if($provenance.schema -cne 'P126_R12A_COPY_PROVENANCE_V3' -or $provenance.handoff_id -cne $handoff -or $provenance.operation -cne $operation -or $provenance.source_root -cne [IO.Path]::GetFullPath($sourceRoot) -or $provenance.destination_root -cne [IO.Path]::GetFullPath($destinationRoot) -or $provenance.source_snapshot_sha256 -cne [string]$sourceSnapshot['sha256'] -or $provenance.copied_material_count -ne 137 -or $provenance.old_controls_copied -ne 0 -or $provenance.added_payload_count -ne 2 -or $provenance.payload_count -ne 139 -or $provenance.preserved_verdict -cne 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE' -or $provenance.hard_defect_id -cne 'HARD-LEGEND-X2-CONTINUOUS' -or $provenance.business_evidence_rerun -ne 0){throw 'provenance semantic binding failure'}

$manifestRows=@(Import-Csv -LiteralPath $manifestPath)
if($manifestRows.Count -ne 139 -or @($manifestRows|Group-Object -Property { [string]$_.relative_path }|Where-Object{$_.Count -ne 1}).Count -ne 0){throw 'manifest row/set failure'}
$manifestMap=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach($row in $manifestRows){if(-not $manifestMap.TryAdd([string]$row.relative_path,$row)){throw 'manifest dictionary duplicate'}}
$actualPayload=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force|Where-Object{$newControlNames -cnotcontains $_.Name})
if($actualPayload.Count -ne 139){throw 'actual payload count failure'}
$actualMap=[Collections.Generic.Dictionary[string,object]]::new([StringComparer]::Ordinal)
foreach($file in $actualPayload){$row=Get-IdentityRow $destinationRoot $file.FullName;if(-not $actualMap.TryAdd([string]$row['relative_path'],$row)){throw 'actual payload duplicate'}}
if($manifestMap.Count -ne $actualMap.Count){throw 'manifest/actual set count mismatch'}
foreach($key in @($manifestMap.Keys)){
  if(-not $actualMap.ContainsKey($key)){throw "manifest actual missing: $key"}
  foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')){if([string]$manifestMap[$key].$field -cne [string]$actualMap[$key][$field]){throw "manifest actual mismatch: $key/$field"}}
}

$sealAudit=Get-Content -LiteralPath $sealAuditPath -Raw|ConvertFrom-Json
if($sealAudit.schema -cne 'P126_R12A_SEAL_AUDIT_V3' -or $sealAudit.handoff_id -cne $handoff -or $sealAudit.operation -cne $operation -or $sealAudit.source_snapshot_sha256 -cne [string]$sourceSnapshot['sha256'] -or $sealAudit.copy_identity_sha256 -cne (Get-Sha256 $copyPath) -or $sealAudit.copy_provenance_sha256 -cne (Get-Sha256 $provenancePath) -or $sealAudit.payload_manifest_sha256 -cne (Get-Sha256 $manifestPath) -or $sealAudit.copied_material_count -ne 137 -or $sealAudit.old_controls_copied -ne 0 -or $sealAudit.payload_count -ne 139 -or $sealAudit.control_count -ne 3 -or $sealAudit.ordinary_count -ne 142 -or $sealAudit.preserved_verdict -cne 'LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE' -or $sealAudit.hard_defect_id -cne 'HARD-LEGEND-X2-CONTINUOUS' -or $sealAudit.business_evidence_rerun -ne 0 -or $sealAudit.copy_identity_mismatch -ne 0 -or $sealAudit.manifest_identity_mismatch -ne 0 -or $sealAudit.source_full_tree_ads_count -ne 0 -or $sealAudit.destination_premarker_full_tree_ads_count -ne 0 -or $sealAudit.source_ads_item_count -ne [long]$sourceAdsAudit['item_count'] -or $sealAudit.destination_premarker_ads_item_count -ne 151){throw 'seal audit semantic binding failure'}

$ordinaryFiles=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Force)
$directoryPaths=@((Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force).FullName)+@($destinationRoot)
if($ordinaryFiles.Count -ne 142 -or [long]$controllerData.ordinary_count -ne 142 -or $directoryPaths.Count -ne [long]$controllerData.directory_count_including_root){throw 'ordinary/directory count failure'}
$fileReadonlyFail=@($ordinaryFiles|Where-Object{-not(Test-ReadonlyAttribute $_.FullName)}).Count
$directoryReadonlyFail=@($directoryPaths|Where-Object{-not(Test-ReadonlyAttribute $_)}).Count
if($fileReadonlyFail -ne 0 -or $directoryReadonlyFail -ne 0){throw 'tree ReadOnly failure'}

$markerBytes=[IO.File]::ReadAllBytes($markerPath)
$hasBom=($markerBytes.Length -ge 3 -and $markerBytes[0] -eq 0xEF -and $markerBytes[1] -eq 0xBB -and $markerBytes[2] -eq 0xBF)
$markerLines=@([IO.File]::ReadAllLines($markerPath,$utf8))
if($hasBom -or $markerLines.Count -ne 28 -or @($markerLines|Where-Object{$_ -notmatch '^[A-Z0-9_]+=[^\r\n]+$' -or $_.Contains("`t")}).Count -ne 0){throw 'marker syntax failure'}
$markerMap=[Collections.Generic.Dictionary[string,string]]::new([StringComparer]::Ordinal)
foreach($line in $markerLines){$parts=$line.Split('=',2);if(-not $markerMap.TryAdd($parts[0],$parts[1])){throw 'marker duplicate key'}}
$expected=[ordered]@{
  SCHEMA='P126_R12A_WRITE_STOPPED_V3';HANDOFF_ID=$handoff;OPERATION=$operation;VERDICT='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';HARD_DEFECT_ID='HARD-LEGEND-X2-CONTINUOUS';SOURCE_ROOT=$sourceRoot;DESTINATION_ROOT=$destinationRoot
  SOURCE_MATERIAL_COUNT='137';PAYLOAD_COUNT='139';CONTROL_COUNT='3';ORDINARY_COUNT='142';PAYLOAD_MANIFEST_SHA256=(Get-Sha256 $manifestPath);COPY_IDENTITY_SHA256=(Get-Sha256 $copyPath);COPY_PROVENANCE_SHA256=(Get-Sha256 $provenancePath);SEAL_AUDIT_SHA256=(Get-Sha256 $sealAuditPath);SOURCE_SNAPSHOT_SHA256=[string]$sourceSnapshot['sha256']
  CONTROLLER_INVOCATION_COUNT='1';AUDITOR_INVOCATION_BUDGET='1';RETRY_COUNT='0';BUSINESS_EVIDENCE_RERUN='0';OLD_CONTROLS_COPIED='0';SOURCE_FULL_TREE_ADS_COUNT='0';DESTINATION_PREMARKER_FULL_TREE_ADS_COUNT='0';PREMARKER_FILES_READONLY='141';PREMARKER_DIRS_READONLY=[string]$directoryPaths.Count;REPORT_SHA256='70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4';HANDOFF_SHA256='057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0'
}
if($markerMap.Count -ne 28){throw 'marker key count failure'}
foreach($binding in $expected.GetEnumerator()){if(-not $markerMap.ContainsKey($binding.Key) -or $markerMap[$binding.Key] -cne [string]$binding.Value){throw "marker binding failure: $($binding.Key)"}}
if(-not $markerMap.ContainsKey('PREPARED_UTC')){throw 'marker prepared time missing'}
[void][DateTime]::Parse($markerMap['PREPARED_UTC'],[Globalization.CultureInfo]::InvariantCulture,[Globalization.DateTimeStyles]::RoundtripKind)

$markerItem=Get-Item -LiteralPath $markerPath -Force
$otherItems=@((Get-Item -LiteralPath $destinationRoot -Force))+@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force|Where-Object{$_.FullName -cne $markerPath})
$maximumOther=[long](($otherItems|ForEach-Object{$_.LastWriteTimeUtc.Ticks}|Measure-Object -Maximum).Maximum)
$atOrAfter=@($otherItems|Where-Object{$_.LastWriteTimeUtc.Ticks -ge $markerItem.LastWriteTimeUtc.Ticks}).Count
if($markerItem.LastWriteTimeUtc.Ticks -le $maximumOther -or $atOrAfter -ne 0){throw 'marker strict-latest failure'}
$destinationSnapshot=Get-TreeSnapshot $destinationRoot
if([string]$destinationSnapshot['sha256'] -cne [string]$controllerData.destination_snapshot_s1.sha256 -or [string]$destinationSnapshot['sha256'] -cne [string]$controllerData.destination_snapshot_s2.sha256 -or [long]$destinationSnapshot['entry_count'] -ne [long]$controllerData.destination_snapshot_s1.entry_count){throw 'postmarker destination changed'}

$jsonFiles=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Filter '*.json' -Force)
$csvFiles=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Filter '*.csv' -Force)
$jsonParseFail=0;foreach($file in $jsonFiles){try{$null=Get-Content -LiteralPath $file.FullName -Raw|ConvertFrom-Json}catch{$jsonParseFail++}}
$csvParseFail=0;foreach($file in $csvFiles){try{$null=@(Import-Csv -LiteralPath $file.FullName)}catch{$csvParseFail++}}
$destinationAdsAudit=Get-FullTreeAdsAudit $destinationRoot
if([long]$destinationAdsAudit['nondefault_ads_count'] -ne 0 -or [long]$destinationAdsAudit['file_count'] -ne 142 -or [long]$destinationAdsAudit['child_directory_count'] -ne ($directoryPaths.Count-1) -or [long]$destinationAdsAudit['root_count'] -ne 1){throw 'sealed destination full-tree ADS audit failure'}
if([long]$controllerData.destination_premarker_full_tree_ads.nondefault_ads_count -ne 0 -or [long]$controllerData.destination_premarker_full_tree_ads.item_count -ne 151){throw 'controller destination ADS binding failure'}
$pycCount=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -File -Filter '*.pyc' -Force).Count
$cacheCount=@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Directory -Force|Where-Object{$_.Name -in @('__pycache__','.pytest_cache','.mypy_cache','.ruff_cache')}).Count
$allItems=@((Get-Item -LiteralPath $destinationRoot -Force))+@(Get-ChildItem -LiteralPath $destinationRoot -Recurse -Force)
$reparseCount=@($allItems|Where-Object{($_.Attributes -band [IO.FileAttributes]::ReparsePoint)-ne 0}).Count
if($jsonParseFail -ne 0 -or $csvParseFail -ne 0 -or $pycCount -ne 0 -or $cacheCount -ne 0 -or $reparseCount -ne 0){throw 'parse or hygiene failure'}
if((Get-Item -LiteralPath $report).Length -ne 2073 -or (Get-Sha256 $report) -cne '70472E2C7A2D10BBAF4A4FC540AABFE9F333AAB0239549DE28B5E8E0A9307CE4' -or -not(Test-ReadonlyAttribute $report)){throw 'external report identity failure'}
if((Get-Item -LiteralPath $handoffFile).Length -ne 1099 -or (Get-Sha256 $handoffFile) -cne '057DE9FEDE81E7A33A64B4B714A313667AA9AA6BB582692A659E8BE9FCB4F1A0' -or -not(Test-ReadonlyAttribute $handoffFile)){throw 'external handoff identity failure'}

$audit=[ordered]@{
  schema='P126_R12A_CONTROL_RESEAL_AUDITOR_RESULT_V3';handoff_id=$handoff;operation=$operation;auditor=[ordered]@{path=$auditor;bytes=(Get-Item -LiteralPath $auditor).Length;sha256=(Get-Sha256 $auditor)};auditor_invocation_count=1;retry_count=0;exit_code=0;success=$true
  copied_material_count=137;copied_material_bytes=106101530;old_controls_copied=0;payload_count=139;control_count=3;ordinary_count=142;directory_count_including_root=$directoryPaths.Count
  source_copy_identity_mismatch=0;manifest_identity_set_mismatch=0;file_readonly_fail=$fileReadonlyFail;directory_readonly_fail=$directoryReadonlyFail
  marker_path=$markerPath;marker_bytes=$markerItem.Length;marker_sha256=(Get-Sha256 $markerPath);marker_lines=$markerLines.Count;marker_keys=$markerMap.Count;marker_bad=0;marker_duplicate=0;marker_has_bom=$hasBom;marker_ticks=$markerItem.LastWriteTimeUtc.Ticks;strict_latest_margin_ticks=[long]($markerItem.LastWriteTimeUtc.Ticks-$maximumOther);at_or_after_excluding_marker=$atOrAfter
  source_snapshot=$sourceSnapshot;destination_snapshot=$destinationSnapshot;source_root_writes=0;postmarker_content_attribute_writes=0
  source_full_tree_ads=$sourceAdsAudit;destination_sealed_full_tree_ads=$destinationAdsAudit
  json_files=$jsonFiles.Count;json_parse_fail=$jsonParseFail;csv_files=$csvFiles.Count;csv_parse_fail=$csvParseFail;pyc_count=$pycCount;cache_count=$cacheCount;reparse_count=$reparseCount
  copy_identity_sha256=(Get-Sha256 $copyPath);copy_provenance_sha256=(Get-Sha256 $provenancePath);payload_manifest_sha256=(Get-Sha256 $manifestPath);seal_audit_sha256=(Get-Sha256 $sealAuditPath);report_sha256=(Get-Sha256 $report);handoff_sha256=(Get-Sha256 $handoffFile)
  preserved_verdict='LOCAL_SA2_FAIL_RETURN_TO_MAIN_SOURCE_SCOPE';hard_defect_id='HARD-LEGEND-X2-CONTINUOUS';business_evidence_rerun=0
}
[IO.File]::WriteAllText($auditorResult,($audit|ConvertTo-Json -Depth 9)+"`n",$utf8)
$resultItem=Get-Item -LiteralPath $auditorResult
[IO.File]::SetAttributes($resultItem.FullName,($resultItem.Attributes -bor [IO.FileAttributes]::ReadOnly))
$audit|ConvertTo-Json -Depth 9
