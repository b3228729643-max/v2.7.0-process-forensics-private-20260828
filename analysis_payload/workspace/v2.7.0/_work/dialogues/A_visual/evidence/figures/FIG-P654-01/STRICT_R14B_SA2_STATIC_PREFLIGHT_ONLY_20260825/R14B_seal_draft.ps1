# STATIC DRAFT ONLY. DO NOT EXECUTE WITHOUT A NEW EXPLICIT MAINLINE COPY/SEAL GRANT.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$TargetRoot,
  [Parameter(Mandatory=$true)][string]$CountModelPath,
  [Parameter(Mandatory=$true)][string]$ExecutionGrant
)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if($ExecutionGrant-ne'P654_R14_COPY_SEAL_EXPLICITLY_GRANTED'){throw 'R14 draft execution is not authorized'}
$target=[IO.Path]::GetFullPath($TargetRoot)
$model=Get-Content -LiteralPath $CountModelPath -Raw|ConvertFrom-Json -AsHashtable
if([IO.Path]::GetFullPath($model.future_sealed_root)-cne$target){throw 'count model target mismatch'}
$controls=@('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
function Get-Rel([string]$Root,[string]$FullName){[IO.Path]::GetRelativePath($Root,$FullName).Replace('/','\')}
function Get-Ext([IO.FileInfo]$File){if([string]::IsNullOrEmpty($File.Extension)){'[none]'}else{$File.Extension.TrimStart('.').ToLowerInvariant()}}
function Get-Snapshot([object[]]$Files){$raw=@{};foreach($f in @($Files)){$key=Get-Ext $f;if(-not$raw.ContainsKey($key)){$raw[$key]=[int64]0};$raw[$key]=[int64]$raw[$key]+1};$ordered=[ordered]@{};foreach($key in @($raw.Keys|Sort-Object)){$ordered[$key]=[int64]$raw[$key]};return $ordered}
function Add-Ext([Collections.IDictionary]$Snapshot,[string]$Key,[int64]$Delta){if(-not$Snapshot.Contains($Key)){$Snapshot[$Key]=[int64]0};$Snapshot[$Key]=[int64]$Snapshot[$Key]+$Delta}
function Merge-Snapshot([Collections.IDictionary]$A,[Collections.IDictionary]$B){$out=@{};foreach($key in @($A.Keys)+@($B.Keys)){if(-not$out.ContainsKey($key)){$out[$key]=[int64]0}};foreach($key in $out.Keys){$out[$key]=[int64]$(if($A.Contains($key)){$A[$key]}else{0})+[int64]$(if($B.Contains($key)){$B[$key]}else{0})};$ordered=[ordered]@{};foreach($key in @($out.Keys|Sort-Object)){$ordered[$key]=$out[$key]};return $ordered}
function Sum-Snapshot([Collections.IDictionary]$Snapshot){[int64](($Snapshot.Values|Measure-Object -Sum).Sum)}
function Assert-Snapshot([Collections.IDictionary]$Got,[Collections.IDictionary]$Expected,[string]$Label){$keys=@(@($Got.Keys)+@($Expected.Keys)|Sort-Object -Unique);foreach($key in $keys){$g=if($Got.Contains($key)){[int64]$Got[$key]}else{0};$e=if($Expected.Contains($key)){[int64]$Expected[$key]}else{0};if($g-ne$e){throw "$Label extension $key expected $e got $g"}}}
function Assert-Equations([Collections.IDictionary]$Payload,[Collections.IDictionary]$Control,[Collections.IDictionary]$Ordinary){$keys=@(@($Payload.Keys)+@($Control.Keys)+@($Ordinary.Keys)|Sort-Object -Unique);foreach($key in $keys){$p=if($Payload.Contains($key)){[int64]$Payload[$key]}else{0};$c=if($Control.Contains($key)){[int64]$Control[$key]}else{0};$o=if($Ordinary.Contains($key)){[int64]$Ordinary[$key]}else{0};if($o-ne$p+$c){throw "ordinary != payload + control for $key"}}}
function New-ManifestRows([object[]]$Files){@($Files|Sort-Object FullName|ForEach-Object{$f=[IO.FileInfo]$_;[ordered]@{relative_path=(Get-Rel $target $f.FullName);bytes=[int64]$f.Length;sha256=(Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLowerInvariant();mtime_utc_ticks=$f.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);mtime_utc_7digit=$f.LastWriteTimeUtc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)}})}

if(@($controls|Where-Object{Test-Path -LiteralPath (Join-Path $target $_)}).Count-ne0){throw 'seal controls already exist'}
$preseal=Get-Content -LiteralPath (Join-Path $target 'R14_PRESEAL_VALIDATION.json') -Raw|ConvertFrom-Json -AsHashtable
if($preseal.status-ne'PRESEAL_VALIDATED_AWAIT_SEAL'){throw 'preseal validator status mismatch'}
$payload=@(Get-ChildItem -LiteralPath $target -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $target $_.FullName)})
if($payload.Count-ne1059){throw 'payload count before manifests mismatch'}
$payloadExtensions=Get-Snapshot $payload
Assert-Snapshot $payloadExtensions $model.final_payload_extensions 'payload'
Assert-Snapshot $preseal.expected_final_payload_extensions $payloadExtensions 'preseal payload'

$rows=New-ManifestRows $payload
$rows|Export-Csv -LiteralPath (Join-Path $target 'PAYLOAD_MANIFEST.csv') -NoTypeInformation -Encoding utf8
$rows|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $target 'PAYLOAD_MANIFEST.json') -Encoding utf8
$manifestFiles=@([IO.FileInfo](Join-Path $target 'PAYLOAD_MANIFEST.csv'),[IO.FileInfo](Join-Path $target 'PAYLOAD_MANIFEST.json'))
$controlExtensions=Get-Snapshot $manifestFiles
Add-Ext $controlExtensions 'json' 1 # future WRITE_STOPPED.json control self
$ordinaryExtensions=Merge-Snapshot $payloadExtensions $controlExtensions
Assert-Snapshot $controlExtensions $model.final_control_extensions 'declared control'
Assert-Snapshot $ordinaryExtensions $model.final_ordinary_extensions 'declared ordinary'
Assert-Snapshot $preseal.expected_final_control_extensions $controlExtensions 'preseal control'
Assert-Snapshot $preseal.expected_final_ordinary_extensions $ordinaryExtensions 'preseal ordinary'
Assert-Equations $payloadExtensions $controlExtensions $ordinaryExtensions
if((Sum-Snapshot $payloadExtensions)-ne1059-or(Sum-Snapshot $controlExtensions)-ne3-or(Sum-Snapshot $ordinaryExtensions)-ne1062){throw 'extension snapshot sum mismatch'}
if($payloadExtensions.json-ne71-or$payloadExtensions.csv-ne23-or$controlExtensions.json-ne2-or$controlExtensions.csv-ne1-or$ordinaryExtensions.json-ne73-or$ordinaryExtensions.csv-ne24){throw 'explicit JSON/CSV equation mismatch'}

$stop=[ordered]@{
  status='WRITE_STOPPED_AWAIT_FRESH_ROOT';payload_file_count=1059;manifest_control_file_count=2;write_stopped_control_file_count=1;control_file_count=3;ordinary_file_total=1062
  declared_final_payload_extensions=$payloadExtensions;declared_final_control_extensions=$controlExtensions;declared_final_ordinary_extensions=$ordinaryExtensions
  sealed_at=[datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)
}
@($payload)+$manifestFiles|ForEach-Object{$_.IsReadOnly=$true}
$stop|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $target 'WRITE_STOPPED.json') -Encoding utf8
([IO.FileInfo](Join-Path $target 'WRITE_STOPPED.json')).IsReadOnly=$true

# Read-only post-write proof; no file under the sealed root is written from here onward.
$ordinary=@(Get-ChildItem -LiteralPath $target -Recurse -File)
$finalControls=@($ordinary|Where-Object{$controls-contains(Get-Rel $target $_.FullName)})
$finalPayload=@($ordinary|Where-Object{$controls-notcontains(Get-Rel $target $_.FullName)})
if($ordinary.Count-ne1062-or$finalPayload.Count-ne1059-or$finalControls.Count-ne3){throw 'final filesystem total mismatch'}
Assert-Snapshot (Get-Snapshot $finalPayload) $stop.declared_final_payload_extensions 'final payload filesystem'
Assert-Snapshot (Get-Snapshot $finalControls) $stop.declared_final_control_extensions 'final control filesystem'
Assert-Snapshot (Get-Snapshot $ordinary) $stop.declared_final_ordinary_extensions 'final ordinary filesystem'
if(@($ordinary|Where-Object{-not$_.IsReadOnly}).Count-ne0){throw 'sealed root contains writable files'}
$stopInfo=[IO.FileInfo](Join-Path $target 'WRITE_STOPPED.json')
if(@($ordinary|Where-Object{$_.FullName-ne$stopInfo.FullName-and$_.LastWriteTimeUtc-ge$stopInfo.LastWriteTimeUtc}).Count-ne0){throw 'WRITE_STOPPED is not uniquely latest'}
$stop|ConvertTo-Json -Depth 8 -Compress

