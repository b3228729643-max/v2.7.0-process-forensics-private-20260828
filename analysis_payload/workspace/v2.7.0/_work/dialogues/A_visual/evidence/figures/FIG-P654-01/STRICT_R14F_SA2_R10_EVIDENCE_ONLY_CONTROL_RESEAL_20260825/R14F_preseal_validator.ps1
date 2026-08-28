# STATIC DRAFT ONLY. DO NOT EXECUTE WITHOUT A NEW EXPLICIT MAINLINE COPY/SEAL GRANT.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$SourceRoot,
  [Parameter(Mandatory=$true)][string]$TargetRoot,
  [Parameter(Mandatory=$true)][string]$CountModelPath,
  [Parameter(Mandatory=$true)][string]$ExecutionGrant
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($ExecutionGrant-ne'P654_R14F_COPY_SEAL_EXPLICITLY_GRANTED'){throw 'R14F draft execution is not authorized'}
$source=[IO.Path]::GetFullPath($SourceRoot);$target=[IO.Path]::GetFullPath($TargetRoot)
$model=Get-Content -LiteralPath $CountModelPath -Raw|ConvertFrom-Json -AsHashtable
if([IO.Path]::GetFullPath($model.future_sealed_root)-cne$target){throw 'count model target mismatch'}
$controls=@('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
$newPreReport=@('R14F_prepare.ps1','R14F_preseal_validator.ps1','R14F_seal.ps1','R14_BASE_COPY_IDENTITY.csv','R14_BASE_COPY_IDENTITY.json','R14_COPY_PROVENANCE.json')
$fields=@('source_relative_path','destination_relative_path','bytes','sha256','mtime_utc_ticks','mtime_utc_7digit')
function Get-Rel([string]$Root,[string]$FullName){[IO.Path]::GetRelativePath($Root,$FullName).Replace('/','\')}
function Get-Sha([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Get-Display([datetime]$Utc){$Utc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)}
function Normalize-Row($Row){[ordered]@{source_relative_path="$($Row.source_relative_path)";destination_relative_path="$($Row.destination_relative_path)";bytes=[int64]$Row.bytes;sha256=("$($Row.sha256)".ToLowerInvariant());mtime_utc_ticks="$($Row.mtime_utc_ticks)";mtime_utc_7digit="$($Row.mtime_utc_7digit)"}}
function Assert-Unique([object[]]$Rows,[string]$Field,[string]$Label){
  $values=@($Rows|ForEach-Object{
    $row=$_
    $found=$false
    $value=$null
    if($row-is[Collections.IDictionary]){
      if($row.Contains($Field)){$found=$true;$value=$row[$Field]}
    }else{
      $property=$row.PSObject.Properties[$Field]
      if($null-ne$property){$found=$true;$value=$property.Value}
    }
    if(-not$found-or[string]::IsNullOrWhiteSpace("$value")){throw "$Label missing or blank $Field"}
    "$value"
  })
  if(@($values|Group-Object|Where-Object { $_.Count -ne 1 }).Count-ne0){throw "$Label duplicate $Field"}
}
function Assert-Set([string[]]$Expected,[string[]]$Got,[string]$Label){if(@(Compare-Object (@($Expected|Sort-Object)) (@($Got|Sort-Object))).Count-ne0){throw "$Label path-set mismatch"}}
function Row-Key($Row){($fields|ForEach-Object{"$_=$($Row[$_])"})-join"`n"}
function Get-Ext([IO.FileInfo]$File){if([string]::IsNullOrEmpty($File.Extension)){'[none]'}else{$File.Extension.TrimStart('.').ToLowerInvariant()}}
function Get-Snapshot([object[]]$Files){$raw=@{};foreach($f in @($Files)){$k=Get-Ext $f;if(-not$raw.ContainsKey($k)){$raw[$k]=[int64]0};$raw[$k]=[int64]$raw[$k]+1};$o=[ordered]@{};foreach($k in @($raw.Keys|Sort-Object)){$o[$k]=$raw[$k]};return $o}
function Add-Ext([Collections.IDictionary]$S,[string]$K,[int64]$D){if(-not$S.Contains($K)){$S[$K]=[int64]0};$S[$K]=[int64]$S[$K]+$D}
function Merge-Snapshot([Collections.IDictionary]$A,[Collections.IDictionary]$B){$o=@{};foreach($k in @($A.Keys)+@($B.Keys)){if(-not$o.ContainsKey($k)){$o[$k]=[int64]0}};foreach($k in @($o.Keys)){$o[$k]=[int64]$(if($A.Contains($k)){$A[$k]}else{0})+[int64]$(if($B.Contains($k)){$B[$k]}else{0})};$r=[ordered]@{};foreach($k in @($o.Keys|Sort-Object)){$r[$k]=$o[$k]};return $r}
function Sum-Snapshot([Collections.IDictionary]$S){[int64](($S.Values|Measure-Object -Sum).Sum)}
function Assert-Snapshot([Collections.IDictionary]$GotSnapshot,[Collections.IDictionary]$ExpectedSnapshot,[string]$Label){$keys=@(@($GotSnapshot.Keys)+@($ExpectedSnapshot.Keys)|Sort-Object -Unique);foreach($k in $keys){$gotValue=if($GotSnapshot.Contains($k)){[int64]$GotSnapshot[$k]}else{0};$expectedValue=if($ExpectedSnapshot.Contains($k)){[int64]$ExpectedSnapshot[$k]}else{0};if($gotValue-ne$expectedValue){throw "$Label extension $k expected $expectedValue got $gotValue"}}}
function Assert-Equations([Collections.IDictionary]$PayloadSnapshot,[Collections.IDictionary]$ControlSnapshot,[Collections.IDictionary]$OrdinarySnapshot){$keys=@(@($PayloadSnapshot.Keys)+@($ControlSnapshot.Keys)+@($OrdinarySnapshot.Keys)|Sort-Object -Unique);foreach($k in $keys){$payloadValue=if($PayloadSnapshot.Contains($k)){[int64]$PayloadSnapshot[$k]}else{0};$controlValue=if($ControlSnapshot.Contains($k)){[int64]$ControlSnapshot[$k]}else{0};$ordinaryValue=if($OrdinarySnapshot.Contains($k)){[int64]$OrdinarySnapshot[$k]}else{0};if($ordinaryValue-ne$payloadValue+$controlValue){throw "ordinary != payload + control for $k"}}}

$csvRows=@(Import-Csv -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.csv')|ForEach-Object{Normalize-Row $_})
$jsonRows=@(Get-Content -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.json') -Raw|ConvertFrom-Json -DateKind String|ForEach-Object{Normalize-Row $_})
if($csvRows.Count-ne1052-or$jsonRows.Count-ne1052){throw 'identity CSV/JSON denominator mismatch'}
foreach($rows in @($csvRows,$jsonRows)){Assert-Unique $rows 'source_relative_path' 'identity';Assert-Unique $rows 'destination_relative_path' 'identity';if(@($rows|Where-Object{$_.source_relative_path-cne$_.destination_relative_path}).Count-ne0){throw 'identity source/destination relative path mismatch'}}
$csvSorted=@($csvRows|Sort-Object source_relative_path);$jsonSorted=@($jsonRows|Sort-Object source_relative_path)
for($i=0;$i-lt1052;$i++){if((Row-Key $csvSorted[$i])-cne(Row-Key $jsonSorted[$i])){throw "identity CSV/JSON full-field mismatch at $i"}}

$sourceBase=@(Get-ChildItem -LiteralPath $source -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $source $_.FullName)}|Sort-Object FullName)
if($sourceBase.Count-ne1052){throw 'R10 base denominator mismatch'}
$sourcePaths=@($sourceBase|ForEach-Object{Get-Rel $source $_.FullName});Assert-Unique (@($sourcePaths|ForEach-Object{[pscustomobject]@{path=$_}})) 'path' 'source base'
Assert-Set $sourcePaths @($csvRows.source_relative_path) 'CSV vs source';Assert-Set $sourcePaths @($jsonRows.source_relative_path) 'JSON vs source'

$targetPayload=@(Get-ChildItem -LiteralPath $target -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $target $_.FullName)})
if($targetPayload.Count-ne1058){throw 'future target pre-report payload denominator mismatch'}
$targetNew=@($targetPayload|Where-Object{$newPreReport-contains(Get-Rel $target $_.FullName)});Assert-Set $newPreReport @($targetNew|ForEach-Object{Get-Rel $target $_.FullName}) 'six pre-report additions'
$targetBase=@($targetPayload|Where-Object{$newPreReport-notcontains(Get-Rel $target $_.FullName)})
if($targetBase.Count-ne1052){throw 'future target base denominator mismatch'}
Assert-Set $sourcePaths @($targetBase|ForEach-Object{Get-Rel $target $_.FullName}) 'target base vs source'

$csvByPath=@{};$jsonByPath=@{};foreach($r in $csvRows){$csvByPath[$r.source_relative_path]=$r};foreach($r in $jsonRows){$jsonByPath[$r.source_relative_path]=$r}
foreach($srcFile in $sourceBase){
  $rel=Get-Rel $source $srcFile.FullName;$dstPath=Join-Path $target $rel;$dst=[IO.FileInfo]$dstPath
  if(-not$dst.Exists){throw "target base missing: $rel"}
  $facts=[ordered]@{source_relative_path=$rel;destination_relative_path=$rel;bytes=[int64]$srcFile.Length;sha256=(Get-Sha $srcFile.FullName);mtime_utc_ticks=$srcFile.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);mtime_utc_7digit=(Get-Display $srcFile.LastWriteTimeUtc)}
  if((Row-Key $csvByPath[$rel])-cne(Row-Key $facts)-or(Row-Key $jsonByPath[$rel])-cne(Row-Key $facts)){throw "identity table vs source mismatch: $rel"}
  if($dst.Length-ne$facts.bytes-or(Get-Sha $dstPath)-cne$facts.sha256-or$dst.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)-cne$facts.mtime_utc_ticks-or(Get-Display $dst.LastWriteTimeUtc)-cne$facts.mtime_utc_7digit){throw "target FS vs source/table mismatch: $rel"}
}

# Recheck the reviewed materialized scripts after prepare so post-gate replacement is also detected.
foreach($binding in @($model.reviewed_draft_identities)){$p=Join-Path $target $binding.future_relative_path;$f=[IO.FileInfo]$p;if(-not$f.Exists-or$f.Length-ne[int64]$binding.bytes-or(Get-Sha $p)-cne("$($binding.sha256)".ToLowerInvariant())){throw "reviewed script identity mismatch in validator: $($binding.future_relative_path)"}}
$provenance=Get-Content -LiteralPath (Join-Path $target 'R14_COPY_PROVENANCE.json') -Raw|ConvertFrom-Json
if([IO.Path]::GetFullPath($provenance.source_root)-cne$source-or[IO.Path]::GetFullPath($provenance.target_root)-cne$target-or@($provenance.psobject.Properties.Value|Where-Object{"$_".Contains('$')}).Count-ne0){throw 'provenance mismatch'}

$projectedPayload=Get-Snapshot $targetPayload;Add-Ext $projectedPayload 'json' 1
$projectedControl=[ordered]@{csv=[int64]1;json=[int64]2};$projectedOrdinary=Merge-Snapshot $projectedPayload $projectedControl
Assert-Snapshot $projectedPayload $model.final_payload_extensions 'payload';Assert-Snapshot $projectedControl $model.final_control_extensions 'control';Assert-Snapshot $projectedOrdinary $model.final_ordinary_extensions 'ordinary';Assert-Equations $projectedPayload $projectedControl $projectedOrdinary
if((Sum-Snapshot $projectedPayload)-ne1059-or(Sum-Snapshot $projectedControl)-ne3-or(Sum-Snapshot $projectedOrdinary)-ne1062-or$projectedPayload.json-ne71-or$projectedPayload.csv-ne23-or$projectedControl.json-ne2-or$projectedControl.csv-ne1-or$projectedOrdinary.json-ne73-or$projectedOrdinary.csv-ne24){throw 'projected final count model mismatch'}
$report=[ordered]@{status='PRESEAL_VALIDATED_AWAIT_SEAL';source_root=$source;target_root=$target;round='R14F';identity_csv_json_full_field_differences=0;identity_duplicate_paths=0;source_target_missing_extra=0;expected_final_payload_file_count=1059;expected_final_manifest_control_file_count=2;expected_final_write_stopped_control_file_count=1;expected_final_control_file_count=3;expected_final_ordinary_file_total=1062;expected_final_payload_extensions=$projectedPayload;expected_final_control_extensions=$projectedControl;expected_final_ordinary_extensions=$projectedOrdinary;validated_at=[datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $target 'R14_PRESEAL_VALIDATION.json') -Encoding utf8
$finalPayload=@(Get-ChildItem -LiteralPath $target -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $target $_.FullName)})
if($finalPayload.Count-ne1059){throw 'post-report payload count mismatch'};Assert-Snapshot (Get-Snapshot $finalPayload) $projectedPayload 'post-report payload'
$report|ConvertTo-Json -Depth 8 -Compress
