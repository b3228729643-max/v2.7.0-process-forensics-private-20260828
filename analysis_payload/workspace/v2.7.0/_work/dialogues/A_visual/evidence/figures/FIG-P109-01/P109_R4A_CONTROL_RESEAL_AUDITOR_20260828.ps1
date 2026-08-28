$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$sourceRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4_SA1_FRESH_ISOLATED_R115_20260828'
$targetRoot = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828_CONTROLLER_RESULT.json'
$externalAuditPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828_ROOT_AUDIT.json'
$externalReportPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828_REPORT.md'
$externalHandoffPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R4A_SA1_R115_EVIDENCE_ONLY_CONTROL_RESEAL_20260828_HANDOFF.md'
$expectedSourceManifestSha = '13F530C3BE817C6C50CB64420EB7CB8268E1B83025D9D460F227BC09659F0E5C'
$expectedSourceMarkerSha = '2C48561B31FD652CAA78BD460DE890D8484B458CCFC74AADD6B7D9DB29259614'
$mainSourceSnapshotSha = '161ECBDB2153C7497971F3AD2C58A88AB33F12C59B1498EFCE75F204FBE847A0'
$controlNames = @('PAYLOAD_MANIFEST.csv','SEAL_AUDIT.json','WRITE_STOPPED')
$controlSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($name in $controlNames) { $null = $controlSet.Add($name) }
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-RelativePath([string]$Root,[string]$Path) { [IO.Path]::GetRelativePath($Root,$Path).Replace('\','/') }
function Get-FileIdentity([string]$Root,[IO.FileInfo]$File) {
  [ordered]@{relative_path=Get-RelativePath $Root $File.FullName;bytes=[int64]$File.Length;sha256=(Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash;creation_time_utc_ticks=$File.CreationTimeUtc.Ticks.ToString();last_write_time_utc_ticks=$File.LastWriteTimeUtc.Ticks.ToString()}
}
function Get-RootSnapshot([string]$Root) {
  $rows=[Collections.Generic.List[object]]::new();$rootItem=Get-Item -LiteralPath $Root -Force
  $rows.Add([ordered]@{kind='directory';relative_path='.';bytes='';sha256='';creation_time_utc_ticks=$rootItem.CreationTimeUtc.Ticks.ToString();last_write_time_utc_ticks=$rootItem.LastWriteTimeUtc.Ticks.ToString();attributes=[int]$rootItem.Attributes})
  foreach($item in @(Get-ChildItem -LiteralPath $Root -Recurse -Force | Sort-Object FullName)){$relativePath=Get-RelativePath $Root $item.FullName;if($item.PSIsContainer){$rows.Add([ordered]@{kind='directory';relative_path=$relativePath;bytes='';sha256='';creation_time_utc_ticks=$item.CreationTimeUtc.Ticks.ToString();last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString();attributes=[int]$item.Attributes})}else{$rows.Add([ordered]@{kind='file';relative_path=$relativePath;bytes=[int64]$item.Length;sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash;creation_time_utc_ticks=$item.CreationTimeUtc.Ticks.ToString();last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString();attributes=[int]$item.Attributes})}}
  @($rows)
}
function Get-RowsSha([object[]]$Rows){$json=$Rows|ConvertTo-Json -Depth 7 -Compress;$sha=[Security.Cryptography.SHA256]::Create();try{([BitConverter]::ToString($sha.ComputeHash($utf8NoBom.GetBytes($json)))).Replace('-','')}finally{$sha.Dispose()}}

foreach($path in @($externalAuditPath,$externalReportPath,$externalHandoffPath)){if(Test-Path -LiteralPath $path){throw 'EXTERNAL_OUTPUT_EXISTS'}}
$controllerResult=Get-Content -LiteralPath $controllerResultPath -Raw|ConvertFrom-Json
if($controllerResult.status -cne 'PASS'){throw 'CONTROLLER_RESULT_NOT_PASS'}
$sourceSnapshotBefore=@(Get-RootSnapshot $sourceRoot);$sourceSnapshotBeforeSha=Get-RowsSha $sourceSnapshotBefore
$copyRows=@(Import-Csv -LiteralPath (Join-Path $targetRoot 'COPY_IDENTITY.csv'))
$manifestRows=@(Import-Csv -LiteralPath (Join-Path $targetRoot 'PAYLOAD_MANIFEST.csv'))
$allFiles=@(Get-ChildItem -LiteralPath $targetRoot -File -Recurse -Force);$allDirs=@(Get-ChildItem -LiteralPath $targetRoot -Directory -Recurse -Force)
$payloadFiles=@($allFiles|Where-Object{-not $controlSet.Contains((Get-RelativePath $targetRoot $_.FullName))})
$payloadRows=@($payloadFiles|Sort-Object FullName|ForEach-Object{Get-FileIdentity $targetRoot $_})
$copyDuplicates=@($copyRows.source_relative_path|Group-Object|Where-Object{$_.Count -ne 1})
$copyErrors=[Collections.Generic.List[string]]::new()
foreach($row in $copyRows){$source=@(Get-FileIdentity $sourceRoot (Get-Item -LiteralPath (Join-Path $sourceRoot ([string]$row.source_relative_path))));$destination=@(Get-FileIdentity $targetRoot (Get-Item -LiteralPath (Join-Path $targetRoot ([string]$row.destination_relative_path))));if($source.Count -ne 1 -or $destination.Count -ne 1){$copyErrors.Add([string]$row.source_relative_path);continue};if([string]$row.source_relative_path -cne [string]$row.destination_relative_path){$copyErrors.Add("$($row.source_relative_path):path");continue};foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')){if(([string]$row.$field -cne [string]$source[0].$field)-or([string]$row.$field -cne [string]$destination[0].$field)){$copyErrors.Add("$($row.source_relative_path):$field");break}}}
$manifestDuplicates=@($manifestRows.relative_path|Group-Object|Where-Object{$_.Count -ne 1})
$manifestSetDiff=@(Compare-Object -ReferenceObject @($manifestRows.relative_path|Sort-Object) -DifferenceObject @($payloadRows.relative_path|Sort-Object))
$manifestErrors=[Collections.Generic.List[string]]::new()
foreach($row in $manifestRows){$actual=@($payloadRows|Where-Object{$_.relative_path -ceq $row.relative_path});if($actual.Count -ne 1){$manifestErrors.Add([string]$row.relative_path);continue};foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')){if([string]$row.$field -cne [string]$actual[0].$field){$manifestErrors.Add("$($row.relative_path):$field");break}}}
$provenance=Get-Content -LiteralPath (Join-Path $targetRoot 'COPY_PROVENANCE.json') -Raw|ConvertFrom-Json
$provenanceErrors=@();if([string]$provenance.source_root -cne [IO.Path]::GetFullPath($sourceRoot)){$provenanceErrors+='source_root'};if([string]$provenance.target_root -cne [IO.Path]::GetFullPath($targetRoot)){$provenanceErrors+='target_root'};if([string]$provenance.source_manifest_sha256 -cne $expectedSourceManifestSha){$provenanceErrors+='source_manifest'};if([string]$provenance.source_wstop_sha256 -cne $expectedSourceMarkerSha){$provenanceErrors+='source_wstop'};if([string]$provenance.main_canonical_full_root_snapshot_sha256 -cne $mainSourceSnapshotSha){$provenanceErrors+='main_snapshot'}
$allItems=@($allFiles+$allDirs+(Get-Item -LiteralPath $targetRoot -Force));$readonlyMissing=@($allItems|Where-Object{-not($_.Attributes -band [IO.FileAttributes]::ReadOnly)})
$markers=@($allFiles|Where-Object{(Get-RelativePath $targetRoot $_.FullName) -ceq 'WRITE_STOPPED'});if($markers.Count -ne 1){throw 'MARKER_UNIQUENESS_FAILURE'};$marker=$markers[0]
$markerLines=@(Get-Content -LiteralPath $marker.FullName);$markerBad=@($markerLines|Where-Object{[string]::IsNullOrWhiteSpace($_)-or$_ -notmatch '^[^=\r\n\t]+=[^\r\n\t]+$'-or$_ -match '\$[A-Za-z_{]'});$markerKeys=@($markerLines|ForEach-Object{($_ -split '=',2)[0]});$markerDuplicates=@($markerKeys|Group-Object|Where-Object{$_.Count -ne 1})
$expectedKeyOrder=@('SCHEMA','STATUS','HANDOFF_ID','OPERATION','SOURCE_ROOT','TARGET_ROOT','SOURCE_MATERIAL_COUNT','COPIED_MATERIAL_COUNT','OLD_CONTROL_COPIED_COUNT','PAYLOAD_COUNT','CONTROL_COUNT','ORDINARY_COUNT','SOURCE_MANIFEST_SHA256','SOURCE_WSTOP_SHA256','MAIN_CANONICAL_SOURCE_SNAPSHOT_SHA256','COPY_IDENTITY_SHA256','COPY_PROVENANCE_SHA256','PAYLOAD_MANIFEST_SHA256','SEAL_AUDIT_SHA256','PREMARKER_READONLY','LAST_ROOT_OPERATION','POSTMARKER_CONTENT_WRITES','POSTMARKER_ATTRIBUTE_WRITES','CONTROLLER_INVOCATION_COUNT','RETRY_COUNT','VERDICT')
$markerOrderDiff=@(Compare-Object -ReferenceObject $expectedKeyOrder -DifferenceObject $markerKeys -SyncWindow 0)
$atOrAfter=@($allItems|Where-Object{$_.FullName -cne $marker.FullName -and $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks});$maxOther=[int64](@($allItems|Where-Object{$_.FullName -cne $marker.FullName}|ForEach-Object{$_.LastWriteTimeUtc.Ticks})|Measure-Object -Maximum).Maximum
$parseErrors=[Collections.Generic.List[string]]::new();foreach($file in @($allFiles|Where-Object{$_.Extension -eq '.json'})){try{$null=Get-Content -LiteralPath $file.FullName -Raw|ConvertFrom-Json}catch{$parseErrors.Add((Get-RelativePath $targetRoot $file.FullName))}};foreach($file in @($allFiles|Where-Object{$_.Extension -eq '.csv'})){try{$null=@(Import-Csv -LiteralPath $file.FullName)}catch{$parseErrors.Add((Get-RelativePath $targetRoot $file.FullName))}}
$ads=[Collections.Generic.List[string]]::new();foreach($file in $allFiles){foreach($stream in @(Get-Item -LiteralPath $file.FullName -Stream *|Where-Object{$_.Stream -ne ':$DATA'})){$ads.Add((Get-RelativePath $targetRoot $file.FullName)+':'+$stream.Stream)}}
$cachePyc=@($allItems|Where-Object{$_.Name -match '(?i)(__pycache__|\.pyc$|^cache$)'});$reparse=@($allItems|Where-Object{$_.Attributes -band [IO.FileAttributes]::ReparsePoint})
$targetSnapshotSha=Get-RowsSha @(Get-RootSnapshot $targetRoot);$targetPostmarkerMismatch=if($targetSnapshotSha -ceq [string]$controllerResult.target_postmarker_snapshot_sha256_2){0}else{1}
$sourceSnapshotAfter=@(Get-RootSnapshot $sourceRoot);$sourceSnapshotAfterSha=Get-RowsSha $sourceSnapshotAfter;$sourceMutationCount=if($sourceSnapshotBeforeSha -ceq $sourceSnapshotAfterSha -and $sourceSnapshotAfterSha -ceq [string]$controllerResult.source_snapshot_after_sha256){0}else{1}
$status=if($copyRows.Count -eq 37 -and $copyDuplicates.Count -eq 0 -and $copyErrors.Count -eq 0 -and $payloadRows.Count -eq 39 -and $manifestRows.Count -eq 39 -and $manifestDuplicates.Count -eq 0 -and $manifestSetDiff.Count -eq 0 -and $manifestErrors.Count -eq 0 -and $provenanceErrors.Count -eq 0 -and $allFiles.Count -eq 42 -and $allDirs.Count -eq 0 -and $readonlyMissing.Count -eq 0 -and $markerLines.Count -eq 26 -and $markerBad.Count -eq 0 -and $markerDuplicates.Count -eq 0 -and $markerOrderDiff.Count -eq 0 -and $atOrAfter.Count -eq 0 -and $parseErrors.Count -eq 0 -and $ads.Count -eq 0 -and $cachePyc.Count -eq 0 -and $reparse.Count -eq 0 -and $targetPostmarkerMismatch -eq 0 -and $sourceMutationCount -eq 0 -and [int]$controllerResult.postmarker_content_or_attribute_mutation_count -eq 0){'PASS'}else{'FAIL'}
$auditorItem=Get-Item -LiteralPath $PSCommandPath
$audit=[ordered]@{schema='P109_R4A_ROOT_EXTERNAL_AUDIT_V1';status=$status;handoff_id='A-R115-P109-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1-20260828';operation='P109_R115_SA1_EVIDENCE_ONLY_CONTROL_RESEAL_V1';auditor_path=$PSCommandPath;auditor_bytes=[int64]$auditorItem.Length;auditor_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash;auditor_invocation_count=1;retry_count=0;copy_identity_rows=$copyRows.Count;copy_identity_error_count=$copyErrors.Count;payload_count=$payloadRows.Count;control_count=3;ordinary_count=$allFiles.Count;directory_count_below_root=$allDirs.Count;manifest_rows=$manifestRows.Count;manifest_set_error_count=$manifestSetDiff.Count;manifest_identity_error_count=$manifestErrors.Count;provenance_error_count=$provenanceErrors.Count;readonly_missing_count=$readonlyMissing.Count;marker_physical_line_count=$markerLines.Count;marker_bad_line_count=$markerBad.Count;marker_duplicate_key_count=$markerDuplicates.Count;marker_order_error_count=$markerOrderDiff.Count;marker_strict_latest_including_root=($atOrAfter.Count -eq 0);marker_margin_ticks=([int64]$marker.LastWriteTimeUtc.Ticks-$maxOther);at_or_after_excluding_marker_count=$atOrAfter.Count;target_postmarker_snapshot_mismatch_count=$targetPostmarkerMismatch;source_root_mutation_count=$sourceMutationCount;parse_error_count=$parseErrors.Count;ads_count=$ads.Count;cache_pyc_count=$cachePyc.Count;reparse_count=$reparse.Count;verdict='SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3'}
[IO.File]::WriteAllText($externalAuditPath,($audit|ConvertTo-Json -Depth 7),$utf8NoBom)
$report=@"
# P109 R4A evidence-only control reseal report

- HANDOFF_ID: A-R115-P109-SA1-FRESH-ISOLATED-CONTROL-RESEAL-V1-20260828
- Result: $status
- Preserved verdict: SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3
- Copy identity: 37 rows, errors $($copyErrors.Count); old controls copied 0.
- Final model: payload $($payloadRows.Count) + controls 3 = ordinary $($allFiles.Count).
- Manifest set/identity errors: $($manifestSetDiff.Count)/$($manifestErrors.Count).
- ReadOnly missing: $($readonlyMissing.Count).
- WRITE_STOPPED: 26 lines, bad/duplicate/order $($markerBad.Count)/$($markerDuplicates.Count)/$($markerOrderDiff.Count), strict latest including root margin $([int64]$marker.LastWriteTimeUtc.Ticks-$maxOther) ticks, at-or-after $($atOrAfter.Count).
- Postmarker snapshot mismatch: $targetPostmarkerMismatch; source-root mutation: $sourceMutationCount.
- Parse/ADS/cache-pyc/reparse: $($parseErrors.Count)/$($ads.Count)/$($cachePyc.Count)/$($reparse.Count).

This operation copied and resealed evidence only. It did not rerun PDF, visual, denominator, pair, manual, text, mathematics, semantics, or page review. It does not start SA3 or write inventory.
"@
$handoff=@"
# P109 R4A immutable handoff

Evidence-only control reseal status: $status.

New root: $targetRoot

The 37 material files bound by the rejected R4 manifest were copied losslessly with relative path, bytes, SHA-256, CreationTimeUtc ticks, and LastWriteTimeUtc ticks preserved. COPY_IDENTITY and resolved COPY_PROVENANCE make payload39; PAYLOAD_MANIFEST, SEAL_AUDIT, and final WRITE_STOPPED make controls3 and ordinary42.

Preserved business direction only: SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3. Await Main acceptance; do not self-start SA3 or migrate inventory.
"@
[IO.File]::WriteAllText($externalReportPath,$report,$utf8NoBom);[IO.File]::WriteAllText($externalHandoffPath,$handoff,$utf8NoBom)
foreach($path in @($externalAuditPath,$externalReportPath,$externalHandoffPath)){$item=Get-Item -LiteralPath $path;$item.Attributes=$item.Attributes -bor [IO.FileAttributes]::ReadOnly}
if($status -cne 'PASS'){throw 'ROOT_EXTERNAL_AUDIT_FAILED'}
$audit|ConvertTo-Json -Depth 7
