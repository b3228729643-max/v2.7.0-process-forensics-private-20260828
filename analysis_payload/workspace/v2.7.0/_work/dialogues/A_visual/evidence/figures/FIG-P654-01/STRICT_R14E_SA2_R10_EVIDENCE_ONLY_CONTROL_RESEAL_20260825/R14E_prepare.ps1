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
if($ExecutionGrant-ne'P654_R14E_COPY_SEAL_EXPLICITLY_GRANTED'){throw 'R14E draft execution is not authorized'}

$expectedSource=[IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R10_SA2_TAXONOMY_R100_DIRECT_BUILD_20260825')
$expectedTarget=[IO.Path]::GetFullPath('D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R14E_SA2_R10_EVIDENCE_ONLY_CONTROL_RESEAL_20260825')
$source=[IO.Path]::GetFullPath($SourceRoot);$target=[IO.Path]::GetFullPath($TargetRoot)
if($source-cne$expectedSource-or$target-cne$expectedTarget){throw 'resolved root mismatch'}
if($source.Contains('$')-or$target.Contains('$')){throw 'unexpanded path placeholder'}
$model=Get-Content -LiteralPath $CountModelPath -Raw|ConvertFrom-Json -AsHashtable
if([IO.Path]::GetFullPath($model.future_sealed_root)-cne$target){throw 'count model target mismatch'}

$controls=@('PAYLOAD_MANIFEST.csv','PAYLOAD_MANIFEST.json','WRITE_STOPPED.json')
function Get-Rel([string]$Root,[string]$FullName){[IO.Path]::GetRelativePath($Root,$FullName).Replace('/','\')}
function Get-Sha([string]$Path){(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()}
function Get-Display([datetime]$Utc){$Utc.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)}

# Gate 0: before any copy, bind the three materialized scripts to the main-reviewed R14E drafts by exact name, bytes and SHA-256.
$reviewed=@($model.reviewed_draft_identities)
if($reviewed.Count-ne3){throw 'reviewed draft identity denominator must be 3'}
$reviewedNames=@($reviewed|ForEach-Object{$_.future_relative_path})
if(@($reviewedNames|Group-Object|Where-Object { $_.Count -ne 1 }).Count-ne0){throw 'duplicate reviewed future script name'}
$targetBefore=@(Get-ChildItem -LiteralPath $target -Recurse -File|Sort-Object FullName)
$targetBeforeNames=@($targetBefore|ForEach-Object{Get-Rel $target $_.FullName})
if($targetBefore.Count-ne3-or@(Compare-Object $reviewedNames $targetBeforeNames).Count-ne0){throw 'future target must contain exactly the three reviewed scripts'}
foreach($binding in $reviewed){
  $path=Join-Path $target $binding.future_relative_path
  $file=[IO.FileInfo]$path
  if(-not$file.Exists-or$file.Length-ne[int64]$binding.bytes-or(Get-Sha $path)-cne("$($binding.sha256)".ToLowerInvariant())){throw "reviewed script identity mismatch before copy: $($binding.future_relative_path)"}
}

$sourceOrdinary=@(Get-ChildItem -LiteralPath $source -Recurse -File)
if($sourceOrdinary.Count-ne1055){throw 'R10 ordinary denominator mismatch'}
$sourcePayload=@($sourceOrdinary|Where-Object{$controls-notcontains(Get-Rel $source $_.FullName)}|Sort-Object FullName)
if($sourcePayload.Count-ne1052){throw 'R10 base payload denominator mismatch'}
$identity=[Collections.Generic.List[object]]::new()
foreach($file in $sourcePayload){
  $rel=Get-Rel $source $file.FullName;$dest=Join-Path $target $rel;$parent=Split-Path -Parent $dest
  if(-not(Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
  Copy-Item -LiteralPath $file.FullName -Destination $dest
  [IO.File]::SetLastWriteTimeUtc($dest,$file.LastWriteTimeUtc)
  $d=[IO.FileInfo]$dest;$sha=Get-Sha $file.FullName;$ticks=$file.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)
  if($d.Length-ne$file.Length-or(Get-Sha $dest)-cne$sha-or$d.LastWriteTimeUtc.Ticks.ToString([Globalization.CultureInfo]::InvariantCulture)-cne$ticks){throw "copy identity mismatch: $rel"}
  $identity.Add([ordered]@{source_relative_path=$rel;destination_relative_path=$rel;bytes=[int64]$file.Length;sha256=$sha;mtime_utc_ticks=$ticks;mtime_utc_7digit=(Get-Display $file.LastWriteTimeUtc)})
}
$identity|Export-Csv -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.csv') -NoTypeInformation -Encoding utf8
$identity|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $target 'R14_BASE_COPY_IDENTITY.json') -Encoding utf8
$provenance=[ordered]@{source_root=$source;target_root=$target;round='R14E';created_at=[datetime]::UtcNow.ToString('yyyy-MM-ddTHH:mm:ss.fffffffZ',[Globalization.CultureInfo]::InvariantCulture)}
if(@($provenance.Values|Where-Object{"$_".Contains('$')}).Count-ne0){throw 'provenance placeholder before write'}
$provenance|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $target 'R14_COPY_PROVENANCE.json') -Encoding utf8
$roundTrip=Get-Content -LiteralPath (Join-Path $target 'R14_COPY_PROVENANCE.json') -Raw|ConvertFrom-Json
if([IO.Path]::GetFullPath($roundTrip.source_root)-cne$source-or[IO.Path]::GetFullPath($roundTrip.target_root)-cne$target-or@($roundTrip.psobject.Properties.Value|Where-Object{"$_".Contains('$')}).Count-ne0){throw 'provenance mismatch after write'}
$prepared=@(Get-ChildItem -LiteralPath $target -Recurse -File|Where-Object{$controls-notcontains(Get-Rel $target $_.FullName)})
if($prepared.Count-ne1058){throw 'prepared pre-report payload denominator mismatch'}
[ordered]@{status='PREPARED_AWAIT_INDEPENDENT_PRESEAL_VALIDATOR';base_payload=1052;current_payload=1058;script_identity_gate='3_OF_3_BYTES_SHA_PASS'}|ConvertTo-Json -Compress
