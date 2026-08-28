$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$root = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828'
$controllerResultPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828_SEAL_CONTROLLER_RESULT.json'
$auditPath = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P109-01\STRICT_R3_SA2_DOMAIN_LABEL_OPAQUE_PATCH_R114_DIRECT_BUILD_20260828_ROOT_AUDIT.json'
$controlNames = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','SEAL_AUDIT.json','WRITE_STOPPED')
$controlSet = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
foreach($name in $controlNames){ $null = $controlSet.Add($name) }
$utf8NoBom = [Text.UTF8Encoding]::new($false)

function Get-RelativePath([string]$Path) { [IO.Path]::GetRelativePath($root,$Path).Replace('\','/') }
function Get-FileRow([IO.FileInfo]$File) {
  [ordered]@{
    relative_path=Get-RelativePath $File.FullName
    bytes=[int64]$File.Length
    sha256=(Get-FileHash -LiteralPath $File.FullName -Algorithm SHA256).Hash
    creation_time_utc_ticks=$File.CreationTimeUtc.Ticks.ToString()
    last_write_time_utc_ticks=$File.LastWriteTimeUtc.Ticks.ToString()
  }
}
function Get-RootSnapshotRows {
  $rows=[Collections.Generic.List[object]]::new()
  $rootItem=Get-Item -LiteralPath $root -Force
  $rows.Add([ordered]@{kind='directory';relative_path='.';bytes='';sha256='';creation_time_utc_ticks=$rootItem.CreationTimeUtc.Ticks.ToString();last_write_time_utc_ticks=$rootItem.LastWriteTimeUtc.Ticks.ToString();attributes=[int]$rootItem.Attributes})
  foreach($item in @(Get-ChildItem -LiteralPath $root -Recurse -Force | Sort-Object FullName)) {
    $relativePath=Get-RelativePath $item.FullName
    if($item.PSIsContainer){$rows.Add([ordered]@{kind='directory';relative_path=$relativePath;bytes='';sha256='';creation_time_utc_ticks=$item.CreationTimeUtc.Ticks.ToString();last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString();attributes=[int]$item.Attributes})}
    else{$rows.Add([ordered]@{kind='file';relative_path=$relativePath;bytes=[int64]$item.Length;sha256=(Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash;creation_time_utc_ticks=$item.CreationTimeUtc.Ticks.ToString();last_write_time_utc_ticks=$item.LastWriteTimeUtc.Ticks.ToString();attributes=[int]$item.Attributes})}
  }
  @($rows)
}
function Get-RowsSha([object[]]$Rows){$text=$Rows|ConvertTo-Json -Depth 6 -Compress;$sha=[Security.Cryptography.SHA256]::Create();try{([BitConverter]::ToString($sha.ComputeHash($utf8NoBom.GetBytes($text)))).Replace('-','')}finally{$sha.Dispose()}}

if(Test-Path -LiteralPath $auditPath){ throw 'AUDIT_OUTPUT_EXISTS' }
$controllerResult=Get-Content -LiteralPath $controllerResultPath -Raw|ConvertFrom-Json
if($controllerResult.status -cne 'PASS'){ throw 'CONTROLLER_RESULT_NOT_PASS' }
$csvRows=@(Import-Csv -LiteralPath (Join-Path $root 'PAYLOAD_MANIFEST.csv'))
$jsonManifest=Get-Content -LiteralPath (Join-Path $root 'PAYLOAD_MANIFEST.json') -Raw|ConvertFrom-Json
$jsonRows=@($jsonManifest.rows)
$allFiles=@(Get-ChildItem -LiteralPath $root -File -Recurse -Force)
$allDirs=@(Get-ChildItem -LiteralPath $root -Directory -Recurse -Force)
$payloadFiles = @($allFiles | Where-Object { -not $controlSet.Contains((Get-RelativePath $_.FullName)) })
$payloadRows = @($payloadFiles | Sort-Object FullName | ForEach-Object { Get-FileRow $_ })
$duplicateCsv = @($csvRows.relative_path | Group-Object | Where-Object { $_.Count -ne 1 })
$duplicateJson = @($jsonRows.relative_path | Group-Object | Where-Object { $_.Count -ne 1 })
$duplicateFs = @($payloadRows.relative_path | Group-Object | Where-Object { $_.Count -ne 1 })
$setCsvJson=@(Compare-Object -ReferenceObject @($csvRows.relative_path|Sort-Object) -DifferenceObject @($jsonRows.relative_path|Sort-Object))
$setCsvFs=@(Compare-Object -ReferenceObject @($csvRows.relative_path|Sort-Object) -DifferenceObject @($payloadRows.relative_path|Sort-Object))
$identityErrors=[Collections.Generic.List[string]]::new()
foreach($csv in $csvRows){
  $json = @($jsonRows | Where-Object { $_.relative_path -ceq $csv.relative_path })
  $fs = @($payloadRows | Where-Object { $_.relative_path -ceq $csv.relative_path })
  if($json.Count -ne 1 -or $fs.Count -ne 1){ $identityErrors.Add($csv.relative_path); continue }
  foreach($field in @('bytes','sha256','creation_time_utc_ticks','last_write_time_utc_ticks')) {
    if(([string]$csv.$field -cne [string]$json[0].$field) -or ([string]$csv.$field -cne [string]$fs[0].$field)) {
      $identityErrors.Add("$($csv.relative_path):$field"); break
    }
  }
}
$allItems=@($allFiles+$allDirs+(Get-Item -LiteralPath $root -Force))
$readonlyMissing = @($allItems | Where-Object { -not ($_.Attributes -band [IO.FileAttributes]::ReadOnly) })
$markers = @($allFiles | Where-Object { (Get-RelativePath $_.FullName) -ceq 'WRITE_STOPPED' })
if($markers.Count -ne 1){ throw 'MARKER_UNIQUENESS_FAILURE' }
$marker=$markers[0]
$atOrAfter = @($allItems | Where-Object { $_.FullName -cne $marker.FullName -and $_.LastWriteTimeUtc.Ticks -ge $marker.LastWriteTimeUtc.Ticks })
$maxOther = [int64](@($allItems | Where-Object { $_.FullName -cne $marker.FullName } | ForEach-Object { $_.LastWriteTimeUtc.Ticks }) | Measure-Object -Maximum).Maximum
$markerLines=@(Get-Content -LiteralPath $marker.FullName)
$badMarkerLines = @($markerLines | Where-Object { [string]::IsNullOrWhiteSpace($_) -or $_ -notmatch '^[^=\r\n]+=[^\r\n]+$' })
$duplicateMarkerKeys = @($markerLines | ForEach-Object { ($_ -split '=',2)[0] } | Group-Object | Where-Object { $_.Count -ne 1 })
$parseErrors=[Collections.Generic.List[string]]::new()
foreach($file in @($allFiles|Where-Object{$_.Extension-eq'.json'})){try{$null=Get-Content -LiteralPath $file.FullName -Raw|ConvertFrom-Json}catch{$parseErrors.Add((Get-RelativePath $file.FullName))}}
foreach($file in @($allFiles|Where-Object{$_.Extension-eq'.csv'})){try{$null=@(Import-Csv -LiteralPath $file.FullName)}catch{$parseErrors.Add((Get-RelativePath $file.FullName))}}
$ads=[Collections.Generic.List[string]]::new()
foreach($file in $allFiles){foreach($stream in @(Get-Item -LiteralPath $file.FullName -Stream *|Where-Object{$_.Stream-ne':$DATA'})){$ads.Add((Get-RelativePath $file.FullName)+':'+$stream.Stream)}}
$pycCache=@($allItems|Where-Object{$_.Name-match'(?i)(__pycache__|\.pyc$)'})
$reparse=@($allItems|Where-Object{$_.Attributes-band[IO.FileAttributes]::ReparsePoint})
$snapshotSha=Get-RowsSha @(Get-RootSnapshotRows)
$postmarkerMismatch = if($snapshotSha -ceq [string]$controllerResult.postmarker_snapshot_sha256_2){0}else{1}
$status = if(
  $csvRows.Count -eq $jsonRows.Count -and $csvRows.Count -eq $payloadRows.Count -and $allFiles.Count -eq ($payloadRows.Count + 4) -and
  $duplicateCsv.Count -eq 0 -and $duplicateJson.Count -eq 0 -and $duplicateFs.Count -eq 0 -and
  $setCsvJson.Count -eq 0 -and $setCsvFs.Count -eq 0 -and $identityErrors.Count -eq 0 -and
  $readonlyMissing.Count -eq 0 -and $markers.Count -eq 1 -and $atOrAfter.Count -eq 0 -and
  $markerLines.Count -eq 12 -and $badMarkerLines.Count -eq 0 -and $duplicateMarkerKeys.Count -eq 0 -and
  $parseErrors.Count -eq 0 -and $ads.Count -eq 0 -and $pycCache.Count -eq 0 -and $reparse.Count -eq 0 -and $postmarkerMismatch -eq 0
){'PASS'}else{'FAIL'}
$auditorItem=Get-Item -LiteralPath $PSCommandPath
$audit=[ordered]@{
  schema='P109_R3_ROOT_EXTERNAL_AUDIT_V1';status=$status;root=$root
  auditor_path=$PSCommandPath;auditor_bytes=[int64]$auditorItem.Length;auditor_sha256=(Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash
  payload_count=$payloadRows.Count;control_count=4;ordinary_count=$allFiles.Count;directory_count_below_root=$allDirs.Count
  manifest_csv_rows=$csvRows.Count;manifest_json_rows=$jsonRows.Count;duplicate_path_count=($duplicateCsv.Count+$duplicateJson.Count+$duplicateFs.Count)
  manifest_set_error_count=($setCsvJson.Count+$setCsvFs.Count);manifest_identity_error_count=$identityErrors.Count
  readonly_missing_count=$readonlyMissing.Count;marker_unique_count=$markers.Count;marker_physical_line_count=$markerLines.Count
  marker_bad_line_count=$badMarkerLines.Count;marker_duplicate_key_count=$duplicateMarkerKeys.Count
  marker_strict_latest_including_root=($atOrAfter.Count -eq 0);marker_margin_ticks=([int64]$marker.LastWriteTimeUtc.Ticks - $maxOther);at_or_after_excluding_marker_count=$atOrAfter.Count
  postmarker_snapshot_mismatch_count=$postmarkerMismatch;parse_error_count=$parseErrors.Count;ads_count=$ads.Count;cache_pyc_count=$pycCache.Count;reparse_count=$reparse.Count
  controller_postmarker_mutation_count=[int]$controllerResult.postmarker_content_or_attribute_mutation_count
}
[IO.File]::WriteAllText($auditPath,($audit|ConvertTo-Json -Depth 6),$utf8NoBom)
$auditItem=Get-Item -LiteralPath $auditPath;$auditItem.Attributes=$auditItem.Attributes-bor[IO.FileAttributes]::ReadOnly
if($status-cne'PASS'){throw 'ROOT_EXTERNAL_AUDIT_FAILED'}
$audit|ConvertTo-Json -Depth 6
