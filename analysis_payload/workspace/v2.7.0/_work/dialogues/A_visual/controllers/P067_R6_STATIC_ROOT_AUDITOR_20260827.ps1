param(
  [Parameter(Mandatory=$true)][string]$Root
)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
function Get-Sha256([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()}
function Get-Rel([string]$Base,[string]$Path){return ([IO.Path]::GetRelativePath($Base,$Path)-replace '\\','/')}
$resolved=[IO.Path]::GetFullPath($Root)
$manifestPath=[IO.Path]::Combine($resolved,'PAYLOAD_MANIFEST.csv')
$presealPath=[IO.Path]::Combine($resolved,'PRESEAL_AUDIT.json')
$markerPath=[IO.Path]::Combine($resolved,'WRITE_STOPPED.json')
$controls=@($manifestPath,$presealPath,$markerPath)
$all=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force -File)
$payload=@($all|Where-Object{$controls -notcontains $_.FullName}|Sort-Object FullName)
$rows=@(Import-Csv -LiteralPath $manifestPath -Encoding UTF8)
$map=@{};$dup=0
foreach($row in $rows){if($map.ContainsKey($row.relative_path)){$dup++}else{$map[$row.relative_path]=$row}}
$missing=0;$bytesMismatch=0;$shaMismatch=0;$ticksMismatch=0
foreach($file in $payload){$rel=Get-Rel $resolved $file.FullName;if(-not $map.ContainsKey($rel)){$missing++;continue};$row=$map[$rel];if([int64]$row.bytes-ne$file.Length){$bytesMismatch++};if($row.sha256-cne(Get-Sha256 $file.FullName)){$shaMismatch++};if($row.mtime_utc_ticks-cne$file.LastWriteTimeUtc.Ticks.ToString()){$ticksMismatch++};$null=$map.Remove($rel)}
$filesROFail=@($all|Where-Object{-not($_.Attributes-band[IO.FileAttributes]::ReadOnly)})
$dirs=@((Get-Item -LiteralPath $resolved -Force))+@(Get-ChildItem -LiteralPath $resolved -Recurse -Force -Directory)
$dirsROFail=@($dirs|Where-Object{-not($_.Attributes-band[IO.FileAttributes]::ReadOnly)})
$marker=Get-Item -LiteralPath $markerPath -Force
$others=@($all|Where-Object{$_.FullName-cne$marker.FullName})
$atOrAfter=@($others|Where-Object{$_.LastWriteTimeUtc.Ticks-ge$marker.LastWriteTimeUtc.Ticks})
$maxOther=($others|Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
$ads=@($all|ForEach-Object{Get-Item -LiteralPath $_.FullName -Stream * -ErrorAction SilentlyContinue|Where-Object{$_.Stream-ne':$DATA'}})
$cache=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force|Where-Object{$_.Name-eq'__pycache__'-or$_.Extension-in@('.pyc','.pyo')})
$reparse=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force|Where-Object{$_.Attributes-band[IO.FileAttributes]::ReparsePoint})
$jsonFail=@();foreach($file in @($all|Where-Object{$_.Extension-ieq'.json'})){try{$null=Get-Content -LiteralPath $file.FullName -Raw -Encoding UTF8|ConvertFrom-Json}catch{$jsonFail+=Get-Rel $resolved $file.FullName}}
[pscustomobject]@{
  status=$(if($rows.Count-eq4-and$payload.Count-eq4-and$all.Count-eq7-and$dup-eq0-and$missing-eq0-and$map.Count-eq0-and$bytesMismatch-eq0-and$shaMismatch-eq0-and$ticksMismatch-eq0-and$filesROFail.Count-eq0-and$dirsROFail.Count-eq0-and$atOrAfter.Count-eq0-and$ads.Count-eq0-and$cache.Count-eq0-and$reparse.Count-eq0-and$jsonFail.Count-eq0){'PASS'}else{'FAIL'})
  payload_count=$payload.Count;control_count=3;ordinary_count=$all.Count;manifest_rows=$rows.Count
  duplicate=$dup;missing=$missing;extra=$map.Count;bytes_mismatch=$bytesMismatch;sha_mismatch=$shaMismatch;ticks_mismatch=$ticksMismatch
  readonly_files="$($all.Count-$filesROFail.Count)/$($all.Count)";readonly_dirs="$($dirs.Count-$dirsROFail.Count)/$($dirs.Count)"
  wstop_unique=@(Get-ChildItem -LiteralPath $resolved -Recurse -Force -File -Filter 'WRITE_STOPPED.json').Count
  wstop_margin_ticks=($marker.LastWriteTimeUtc.Ticks-$maxOther).ToString();at_or_after=$atOrAfter.Count;postmarker_writes=$atOrAfter.Count
  json_parse_failures=$jsonFail.Count;ads=$ads.Count;cache_pyc=$cache.Count;reparse=$reparse.Count
  manifest_sha256=Get-Sha256 $manifestPath;preseal_sha256=Get-Sha256 $presealPath;write_stopped_sha256=Get-Sha256 $markerPath
}|ConvertTo-Json -Depth 6
