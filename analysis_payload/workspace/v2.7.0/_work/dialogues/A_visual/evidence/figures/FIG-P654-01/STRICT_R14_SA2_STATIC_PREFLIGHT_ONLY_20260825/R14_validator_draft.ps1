# STATIC DRAFT ONLY. DO NOT EXECUTE WITHOUT A NEW EXPLICIT MAINLINE COPY/SEAL GRANT.
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string]$SourceRoot,
  [Parameter(Mandatory=$true)][string]$TargetRoot,
  [Parameter(Mandatory=$true)][string]$CountModelPath,
  [Parameter(Mandatory=$true)][string]$ExecutionGrant
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if ($ExecutionGrant -ne 'P654_R14_COPY_SEAL_EXPLICITLY_GRANTED') { throw 'R14 draft execution is not authorized' }

$source = [IO.Path]::GetFullPath($SourceRoot)
$target = [IO.Path]::GetFullPath($TargetRoot)
$model = Get-Content -LiteralPath $CountModelPath -Raw | ConvertFrom-Json -AsHashtable
$controls = @('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
$reportRel = 'R14_PRESEAL_VALIDATION.json'
function Get-Rel([string]$Root,[string]$FullName) { [IO.Path]::GetRelativePath($Root,$FullName).Replace('/','\') }
function Get-Ext([IO.FileInfo]$File) { if ([string]::IsNullOrEmpty($File.Extension)) {'[none]'} else {$File.Extension.TrimStart('.').ToLowerInvariant()} }
function Get-Snapshot([object[]]$Files) {
  $raw = @{}; foreach ($f in @($Files)) { $key=Get-Ext $f; if (-not $raw.ContainsKey($key)) {$raw[$key]=[int64]0}; $raw[$key]=[int64]$raw[$key]+1 }
  $ordered=[ordered]@{}; foreach($key in @($raw.Keys|Sort-Object)){$ordered[$key]=[int64]$raw[$key]}; return $ordered
}
function Add-Ext([Collections.IDictionary]$Snapshot,[string]$Key,[int64]$Delta) { if(-not $Snapshot.Contains($Key)){$Snapshot[$Key]=[int64]0};$Snapshot[$Key]=[int64]$Snapshot[$Key]+$Delta }
function Merge-Snapshot([Collections.IDictionary]$A,[Collections.IDictionary]$B) {
  $out=@{}; foreach($key in @($A.Keys)+@($B.Keys)){if(-not$out.ContainsKey($key)){$out[$key]=[int64]0}};foreach($key in $out.Keys){$out[$key]=[int64]$(if($A.Contains($key)){$A[$key]}else{0})+[int64]$(if($B.Contains($key)){$B[$key]}else{0})};$ordered=[ordered]@{};foreach($key in @($out.Keys|Sort-Object)){$ordered[$key]=$out[$key]};return $ordered
}
function Sum-Snapshot([Collections.IDictionary]$Snapshot) { [int64](($Snapshot.Values|Measure-Object -Sum).Sum) }
function Assert-Snapshot([Collections.IDictionary]$Got,[Collections.IDictionary]$Expected,[string]$Label) {
  $keys=@(@($Got.Keys)+@($Expected.Keys)|Sort-Object -Unique);foreach($key in $keys){$g=if($Got.Contains($key)){[int64]$Got[$key]}else{0};$e=if($Expected.Contains($key)){[int64]$Expected[$key]}else{0};if($g-ne$e){throw "$Label extension $key expected $e got $g"}}
}
function Assert-Equations([Collections.IDictionary]$Payload,[Collections.IDictionary]$Control,[Collections.IDictionary]$Ordinary) {
  $keys=@(@($Payload.Keys)+@($Control.Keys)+@($Ordinary.Keys)|Sort-Object -Unique);foreach($key in $keys){$p=if($Payload.Contains($key)){[int64]$Payload[$key]}else{0};$c=if($Control.Contains($key)){[int64]$Control[$key]}else{0};$o=if($Ordinary.Contains($key)){[int64]$Ordinary[$key]}else{0};if($o-ne$p+$c){throw "ordinary != payload + control for $key"}}
}

if ([IO.Path]::GetFullPath($model.future_sealed_root) -cne $target) { throw 'count model target mismatch' }
if ((Test-Path -LiteralPath (Join-Path $target $reportRel))) { throw 'preseal report already exists' }
$currentPayload=@(Get-ChildItem -LiteralPath $target -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $target $_.FullName)})
if($currentPayload.Count-ne1058){throw "pre-report payload expected 1058, got $($currentPayload.Count)"}

$identityCsv=@(Import-Csv -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.csv'))
$identityJson=@(Get-Content -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.json') -Raw|ConvertFrom-Json)
if($identityCsv.Count-ne1052-or$identityJson.Count-ne1052){throw 'identity denominator mismatch'}
$sourcePayload=@(Get-ChildItem -LiteralPath $source -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $source $_.FullName)})
if($sourcePayload.Count-ne1052){throw 'source base denominator mismatch'}
foreach($row in $identityCsv){$src=Join-Path $source $row.source_relative_path;$dst=Join-Path $target $row.destination_relative_path;if(-not(Test-Path -LiteralPath $src)-or-not(Test-Path -LiteralPath $dst)){throw "identity path missing: $($row.source_relative_path)"};$s=[IO.FileInfo]$src;$d=[IO.FileInfo]$dst;$ticks=$s.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture);if($s.Length-ne$d.Length-or$s.Length-ne[int64]$row.bytes-or(Get-FileHash -LiteralPath $src -Algorithm SHA256).Hash.ToLowerInvariant()-cne$row.sha256-or(Get-FileHash -LiteralPath $dst -Algorithm SHA256).Hash.ToLowerInvariant()-cne$row.sha256-or$ticks-cne$row.mtime_utc_ticks-or$d.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)-cne$ticks){throw "base identity mismatch: $($row.source_relative_path)"}}

$provenance=Get-Content -LiteralPath (Join-Path $target 'R14_COPY_PROVENANCE.json') -Raw|ConvertFrom-Json
if([IO.Path]::GetFullPath($provenance.source_root)-cne$source-or[IO.Path]::GetFullPath($provenance.target_root)-cne$target-or@($provenance.psobject.Properties.Value|Where-Object{"$_".Contains('$')}).Count-ne0){throw 'provenance mismatch'}

$projectedPayload=Get-Snapshot $currentPayload
Add-Ext $projectedPayload 'json' 1 # the future R14_PRESEAL_VALIDATION.json payload self
$projectedControl=[ordered]@{csv=[int64]1;json=[int64]2} # two manifests plus future WSTOP JSON self
$projectedOrdinary=Merge-Snapshot $projectedPayload $projectedControl
Assert-Snapshot $projectedPayload $model.final_payload_extensions 'payload'
Assert-Snapshot $projectedControl $model.final_control_extensions 'control'
Assert-Snapshot $projectedOrdinary $model.final_ordinary_extensions 'ordinary'
Assert-Equations $projectedPayload $projectedControl $projectedOrdinary
if((Sum-Snapshot $projectedPayload)-ne1059-or(Sum-Snapshot $projectedControl)-ne3-or(Sum-Snapshot $projectedOrdinary)-ne1062){throw 'extension snapshot sum mismatch'}
if($projectedPayload.json-ne71-or$projectedPayload.csv-ne23-or$projectedControl.json-ne2-or$projectedControl.csv-ne1-or$projectedOrdinary.json-ne73-or$projectedOrdinary.csv-ne24){throw 'explicit JSON/CSV equation mismatch'}

$report=[ordered]@{
  status='PRESEAL_VALIDATED_AWAIT_SEAL';source_root=$source;target_root=$target;round='R14'
  expected_final_payload_file_count=1059;expected_final_manifest_control_file_count=2;expected_final_write_stopped_control_file_count=1
  expected_final_control_file_count=3;expected_final_ordinary_file_total=1062
  expected_final_payload_extensions=$projectedPayload;expected_final_control_extensions=$projectedControl;expected_final_ordinary_extensions=$projectedOrdinary
  validated_at=[datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)
}
$report|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $target $reportRel) -Encoding utf8
$finalPayload=@(Get-ChildItem -LiteralPath $target -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $target $_.FullName)})
if($finalPayload.Count-ne1059){throw 'final payload count after report mismatch'}
Assert-Snapshot (Get-Snapshot $finalPayload) $projectedPayload 'post-report payload'
$report|ConvertTo-Json -Depth 8 -Compress
