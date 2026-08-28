param(
  [Parameter(Mandatory=$true)][string]$Root
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Write-Utf8NoBom([string]$Path,[string]$Text) {
  [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}
function Get-Sha256([string]$Path) {
  return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function Get-Rel([string]$Base,[string]$Path) {
  return ([IO.Path]::GetRelativePath($Base,$Path) -replace '\\','/')
}
function Csv-Escape([string]$Value) {
  return '"' + ($Value -replace '"','""') + '"'
}

$resolvedRoot = [IO.Path]::GetFullPath($Root)
if (-not [IO.Directory]::Exists($resolvedRoot)) { throw 'Static root does not exist' }
$controls = @('PAYLOAD_MANIFEST.csv','PRESEAL_AUDIT.json','WRITE_STOPPED.json')
foreach($name in $controls) {
  if([IO.File]::Exists([IO.Path]::Combine($resolvedRoot,$name))) { throw "Control already exists: $name" }
}
$payload = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File | Sort-Object FullName)
if($payload.Count -ne 4) { throw "Expected 4 static payload files, got $($payload.Count)" }
$expectedNames = @('EXACT_DIFF.patch','INTERVAL_PROOF.md','SCOPE_IDENTITY.json','STATIC_RESULT.json')
$actualNames = @($payload.Name | Sort-Object)
if(($actualNames -join '|') -cne (($expectedNames | Sort-Object) -join '|')) { throw 'Static payload name set mismatch' }

$source = 'D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\worktrees\dialogue_A_visual\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex'
if((Get-Item -LiteralPath $source).Length -ne 4014) { throw 'Source bytes mismatch' }
if((Get-Sha256 $source) -cne '2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920') { throw 'Source SHA mismatch' }
$text = Get-Content -LiteralPath $source -Raw -Encoding UTF8
if(@([regex]::Matches($text,'const plot mark left')).Count -ne 1) { throw 'New handler count mismatch' }
if(@([regex]::Matches($text,'const plot mark right')).Count -ne 0) { throw 'Old handler still present' }
if(@(Get-Process -Name latexmk,lualatex,luatex,luahbtex -ErrorAction SilentlyContinue).Count -ne 0) { throw 'TeX process count is not zero' }

$rows = @()
foreach($file in $payload) {
  $rows += [pscustomobject]@{
    relative_path = Get-Rel $resolvedRoot $file.FullName
    bytes = [int64]$file.Length
    sha256 = Get-Sha256 $file.FullName
    mtime_utc_ticks = $file.LastWriteTimeUtc.Ticks.ToString()
  }
}
$dups = @($rows | Group-Object -Property relative_path | Where-Object { $_.Count -ne 1 })
if($dups.Count -ne 0) { throw 'Duplicate payload path' }

$manifestPath = [IO.Path]::Combine($resolvedRoot,'PAYLOAD_MANIFEST.csv')
$csv = [Collections.Generic.List[string]]::new()
$csv.Add('relative_path,bytes,sha256,mtime_utc_ticks')
foreach($row in $rows) {
  $csv.Add((Csv-Escape $row.relative_path)+','+$row.bytes+','+$row.sha256+','+$row.mtime_utc_ticks)
}
Write-Utf8NoBom $manifestPath (($csv -join "`n")+"`n")
$roundtrip = @(Import-Csv -LiteralPath $manifestPath -Encoding UTF8)
if($roundtrip.Count -ne 4) { throw 'Manifest row count mismatch' }

$errors = [Collections.Generic.List[string]]::new()
for($i=0;$i -lt 4;$i++) {
  $file = $payload[$i]
  $row = $roundtrip[$i]
  $rel = Get-Rel $resolvedRoot $file.FullName
  if($row.relative_path -cne $rel) { $errors.Add("path:$i") }
  if($row.bytes -cne $file.Length.ToString()) { $errors.Add("bytes:$rel") }
  if($row.sha256 -cne (Get-Sha256 $file.FullName)) { $errors.Add("sha:$rel") }
  if($row.mtime_utc_ticks -cne $file.LastWriteTimeUtc.Ticks.ToString()) { $errors.Add("ticks:$rel") }
}
if($errors.Count -ne 0) { throw "Identity errors: $($errors.Count)" }

$presealPath = [IO.Path]::Combine($resolvedRoot,'PRESEAL_AUDIT.json')
$preseal = [ordered]@{
  schema='P067_R6_STATIC_PRESEAL_V1'
  resolved_root=$resolvedRoot
  payload_count=4
  control_count=3
  projected_ordinary_count=7
  duplicate_path_count=$dups.Count
  identity_error_count=$errors.Count
  source_bytes=4014
  source_sha256='2881377AEEF78E8C7BD7502AD8A303E19AAC395F1936475BDC6D569195900920'
  tex_process_count=0
  rendered_or_built=$false
  commit_created=$false
  status='PASS_READY_FOR_WSTOP'
}
Write-Utf8NoBom $presealPath (($preseal|ConvertTo-Json -Depth 6)+"`n")

$premarker = @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -File)
if($premarker.Count -ne 6) { throw "Premarker count must be 6, got $($premarker.Count)" }
foreach($file in $premarker) { $file.Attributes = $file.Attributes -bor [IO.FileAttributes]::ReadOnly }
$dirs = @((Get-Item -LiteralPath $resolvedRoot -Force)) + @(Get-ChildItem -LiteralPath $resolvedRoot -Recurse -Force -Directory)
foreach($dir in $dirs) { $dir.Attributes = $dir.Attributes -bor [IO.FileAttributes]::ReadOnly }
$fileReadonlyFail = @($premarker | Where-Object { -not ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) })
$dirReadonlyFail = @($dirs | Where-Object { -not ((Get-Item -LiteralPath $_.FullName -Force).Attributes -band [IO.FileAttributes]::ReadOnly) })
if($fileReadonlyFail.Count -ne 0 -or $dirReadonlyFail.Count -ne 0) { throw 'Premarker readonly failure' }

$maxTicks = ($premarker | Measure-Object -Property LastWriteTimeUtc -Maximum).Maximum.Ticks
$markerTicks = [Math]::Max([DateTime]::UtcNow.AddSeconds(5).Ticks,$maxTicks+1)
$temp = [IO.Path]::Combine([IO.Path]::GetDirectoryName($resolvedRoot),'.P067_R6_WSTOP_'+[Guid]::NewGuid().ToString('N')+'.json')
$final = [IO.Path]::Combine($resolvedRoot,'WRITE_STOPPED.json')
$marker = [ordered]@{
  schema='P067_R6_STATIC_WRITE_STOPPED_V1'
  handoff_id='A-R112-P067-SA2-STATIC-CDF-STEP-HANDLER-20260827'
  resolved_root=$resolvedRoot
  payload_count=4
  control_count=3
  ordinary_count=7
  max_premarker_ticks=$maxTicks.ToString()
  write_stopped_ticks=$markerTicks.ToString()
  postmarker_root_content_writes=0
  postmarker_root_attribute_writes=0
}
Write-Utf8NoBom $temp (($marker|ConvertTo-Json -Depth 5)+"`n")
[IO.File]::SetLastWriteTimeUtc($temp,[DateTime]::new($markerTicks,[DateTimeKind]::Utc))
$tempItem = Get-Item -LiteralPath $temp -Force
$tempItem.Attributes = $tempItem.Attributes -bor [IO.FileAttributes]::ReadOnly
Move-Item -LiteralPath $temp -Destination $final

[pscustomobject]@{
  status='SEALED'
  payload_count=4
  control_count=3
  ordinary_count=7
  manifest_sha256=Get-Sha256 $manifestPath
  preseal_sha256=Get-Sha256 $presealPath
  write_stopped_sha256=Get-Sha256 $final
  write_stopped_margin_ticks=($markerTicks-$maxTicks).ToString()
}|ConvertTo-Json -Depth 5
